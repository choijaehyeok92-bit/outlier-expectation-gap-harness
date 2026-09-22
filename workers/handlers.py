"""What each job kind actually does.

Every handler calls a function the CLI already calls. None of them implements
analysis, computes a score or writes a verdict; they are the same entry points
with their arguments coming from a row instead of from `argparse`. If a
handler here ever does something the CLI cannot, that is a bug in the handler.

Two boundaries are enforced in this file rather than assumed.

**A payload cannot escalate a provider.** `payload['provider']` is written by
whoever enqueued the job, and a queue row that spends money because someone
typed `anthropic` into a JSON body is an obvious way to be surprised by a
bill. The worker's own config holds `providers.allowed`; anything outside it
is refused and the job fails with the reason. An operator who wants a real
model adds it to the config, on the machine, on purpose.

**Every handler is idempotent.** A lease can expire and hand the same job to a
second worker, so running twice has to be safe. It is, and not by luck:
`run_agent` skips an agent whose report is already complete and valid, the
database sync is keyed on content, the observation log ignores a byte
identical re-append, and every immutable store returns the existing path when
the content hash matches.
"""
import json
from datetime import date
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]


class HandlerRefused(RuntimeError):
    """The job was not run, and why. Not a crash — a refusal with a reason."""


def resolve_provider(payload: dict, config: dict, *, for_deep_dive: bool = False):
    """The provider this job may use, or a refusal.

    `placeholder` is the offline agent provider (analyses nothing, exists to
    exercise wiring); `fixture` is the offline deep-dive provider. Both are
    allowed by default because neither spends anything or produces a document
    a person would mistake for research.
    """
    providers = config['providers']
    name = payload.get('provider') or providers.get('default', 'placeholder')
    if name not in providers['allowed']:
        raise HandlerRefused(
            f'provider {name!r} is not in config/workers.json providers.allowed '
            f'({providers["allowed"]}). A queued row must not be able to spend money or '
            'produce research nobody asked for; add it to the config deliberately.')
    if name == 'placeholder':
        from packages.orchestration.fixtures import PlaceholderAgentProvider
        return PlaceholderAgentProvider(mode=payload.get('placeholder_mode', 'valid'))
    if name == 'fixture':
        from packages.llm import resolve_provider as resolve
        root = ROOT / 'packages' / 'research' / 'fixtures' / str(payload.get('run_id', ''))
        return resolve('fixture', payload.get('model'), root=root) if for_deep_dive \
            else resolve('fixture', payload.get('model'))
    from packages.llm import resolve_provider as resolve
    return resolve(name, payload.get('model'))


# ------------------------------------------------------------------ handlers
def db_sync(payload: dict, config: dict) -> dict:
    """Load the file artifacts into the database. Keyed on content, so repeatable."""
    from db.session import engine_for, session_scope
    from db import sync as sync_module
    from packages.screening import runs_index, store as screen_store, warehouse
    from packages.research import store as deep_store

    kinds = payload.get('kinds') or ['runs', 'warehouse', 'screens', 'deep-dives', 'monitoring']
    report = {}
    with session_scope(engine_for()) as session:
        if 'runs' in kinds:
            report['runs'] = dict(sync_module.sync_runs(session, runs_index.load_rows()))
        if 'warehouse' in kinds:
            built = warehouse.load(payload.get('as_of_date'))
            report['warehouse'] = (dict(sync_module.sync_warehouse(session, built))
                                   if built else 'no warehouse built')
        if 'screens' in kinds:
            records = [screen_store.load(row['screen_run_id'])
                       for row in screen_store.list_runs()]
            report['screens'] = dict(sync_module.sync_screen_runs(
                session, [r for r in records if r]))
        if 'deep-dives' in kinds:
            reports = [deep_store.load(row['deep_dive_id'])
                       for row in deep_store.list_reports()]
            report['deep_dives'] = dict(sync_module.sync_deep_dives(
                session, [r for r in reports if r]))
        if 'monitoring' in kinds:
            from db.cli import _sync_monitoring
            report['monitoring'] = _sync_monitoring(session, sync_module)
    return report


def screen_build(payload: dict, config: dict) -> dict:
    """Rebuild the deterministic metric warehouse. No LLM is involved at any point."""
    from packages.cli import _warehouse_entries_from_runs
    from packages.screening import warehouse
    as_of = payload.get('as_of_date') or date.today().isoformat()
    tickers = payload.get('tickers')
    entries, unreadable = _warehouse_entries_from_runs(
        tickers={t.upper() for t in tickers} if tickers else None, as_of=as_of)
    if not entries:
        raise HandlerRefused(f'no Stage 0 pack could be read for {as_of}; nothing to build')
    built = warehouse.build(entries, as_of)
    path = warehouse.save(built)
    return {'as_of_date': built['as_of_date'], 'companies': built['companies'],
            'failures': built['failures'], 'unreadable_artifacts': unreadable,
            'path': str(Path(path).relative_to(ROOT))}


def monitor_status(payload: dict, config: dict) -> dict:
    """Evaluate watchlists against observations and persist an immutable snapshot."""
    from packages.monitoring import evaluate as monitor_evaluate
    from packages.monitoring import observations as observation_log
    from packages.monitoring import store as monitoring_store

    tickers = payload.get('tickers') or observation_log.tickers()
    if not tickers:
        return {'companies': 0, 'note': 'no observations recorded yet; nothing to evaluate'}
    cutoff = payload.get('as_of_date')
    saved, review = [], 0
    for ticker in tickers:
        try:
            result = monitor_evaluate.evaluate(ticker, cutoff)
        except ValueError as error:
            saved.append({'ticker': ticker, 'error': str(error)})
            continue
        review += result['summary']['review_required']
        record = monitoring_store.build_record(result)
        saved.append({'ticker': ticker, 'monitoring_run_id': record['monitoring_run_id'],
                      'review_required': result['summary']['review_required'],
                      'path': str(Path(monitoring_store.save(record)).relative_to(ROOT))})
    return {'companies': len(tickers), 'review_required': review, 'results': saved}


def _batch(stage: str, payload: dict, config: dict) -> dict:
    from packages.orchestration import batch, contracts, selection
    from packages.orchestration import store as batch_store
    from packages.screening import rows as row_source

    orchestration = contracts.load_config()
    provider = resolve_provider(payload, config)
    as_of = payload.get('as_of_date')
    if payload.get('run_ids'):
        rows = [{'run_id': run_id, 'ticker': run_id} for run_id in payload['run_ids']]
    else:
        rows = row_source.load_rows(as_of, source=payload.get('source', 'auto'))
    candidates = selection.select_candidates(rows, config=orchestration,
                                             top_n=payload.get('top'), stage=stage)
    eligible = [c for c in candidates if c.eligible]
    if not eligible:
        return {'stage': stage, 'attempted': 0,
                'not_eligible': [c.to_dict() for c in candidates][:20],
                'note': 'nothing to run; every candidate is already complete or blocked'}
    result = batch.run_batch(candidates, provider, config=orchestration, as_of_date=as_of,
                             force=bool(payload.get('force')), stage=stage)
    record = batch_store.build_record(result.to_dict(), orchestration, stage=stage)
    path = batch_store.save(record)
    spec = batch_store.stage_spec(stage)
    return {'stage': stage, spec['id_field']: record[spec['id_field']],
            'summary': record['summary'],
            'verification_scope': record['verification_scope'],
            'path': str(Path(path).relative_to(ROOT))}


def harness_triage(payload: dict, config: dict) -> dict:
    """Stage 3 over the selected candidates. The harness scores; this only sequences."""
    return _batch('triage', payload, config)


def harness_full(payload: dict, config: dict) -> dict:
    """Stage 4 — the planner decides the order, round by round, not this handler."""
    return _batch('full', payload, config)


def deep_dive(payload: dict, config: dict) -> dict:
    """The four qualitative stages for one run. Refuses a run the policy did not select."""
    from packages.llm import LLMError
    from packages.research import deep_run

    run_id = payload.get('run_id')
    if not run_id:
        raise HandlerRefused('deep_dive needs a run_id in its payload')
    provider = resolve_provider(payload, config, for_deep_dive=True)
    try:
        report, _plan, path = deep_run.run(run_id, provider,
                                           user_requested=bool(payload.get('user_requested')))
    except LLMError as error:
        raise HandlerRefused(str(error)) from error
    return {'deep_dive_id': report['metadata']['deep_dive_id'], 'run_id': run_id,
            'red_team_overall': (report.get('red_team') or {}).get('overall'),
            'path': str(Path(path).relative_to(ROOT))}


REGISTRY: dict = {
    'db_sync': db_sync,
    'screen_build': screen_build,
    'monitor_status': monitor_status,
    'harness_triage': harness_triage,
    'harness_full': harness_full,
    'deep_dive': deep_dive,
}


def resolve(kind: str, config: dict) -> Callable:
    """The handler for a kind, checked against the config rather than guessed."""
    from .queue import kind_settings
    name = kind_settings(kind, config).get('handler') or kind
    handler = REGISTRY.get(name)
    if handler is None:
        raise HandlerRefused(
            f'config/workers.json maps {kind!r} to handler {name!r}, which is not registered '
            f'({sorted(REGISTRY)}). Fix the config rather than letting a worker guess.')
    return handler


def declared_kinds(config: Optional[dict] = None) -> list:
    """Kinds the config declares, cross-checked against what is implemented."""
    from .queue import load_config
    config = config or load_config()
    kinds = sorted((config.get('kinds') or {}))
    missing = [k for k in kinds if (config['kinds'][k].get('handler') or k) not in REGISTRY]
    if missing:
        raise ValueError(f'config/workers.json declares kinds with no handler: {missing}')
    return kinds


def payload_is_safe(payload: dict) -> Optional[str]:
    """A payload must not carry a secret. `job.payload` is readable over the API.

    This is a guard against a careless enqueue, not a security boundary: keys
    belong in the environment, where the provider classes read them.
    """
    suspicious = [key for key in (payload or {})
                  if any(token in key.lower()
                         for token in ('api_key', 'apikey', 'secret', 'token', 'password'))]
    if suspicious:
        return (f'payload carries {suspicious}, and job payloads are stored and served over '
                'the API. Provider credentials are read from the environment; do not queue them.')
    try:
        json.dumps(payload)
    except (TypeError, ValueError) as error:
        return f'payload is not JSON-serialisable: {error}'
    return None
