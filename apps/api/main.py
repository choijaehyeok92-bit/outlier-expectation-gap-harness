"""Read-mostly API over the harness, the screener and the deep dive.

Three boundaries are worth naming, because they are what this service is for.

It never computes a harness result. `/api/runs` and `/api/companies` read what
the harness already wrote and hand it over unchanged; nothing in this process
recomputes a score, an archetype, a veto status or a valuation.

It never lets a model reach the data layer. `/api/screen/parse` turns text into
a ScreeningSpec and stops there. Execution happens in the deterministic
compiler, over an allowlisted field registry, and a condition the parser could
not resolve comes back in `unresolved_conditions` instead of quietly vanishing.

It never returns a secret. Provider keys are read inside the provider classes
from the environment; no route accepts one and no response echoes one.

It never runs background work in a request. `/api/jobs` writes a row; a
worker process picks it up. Which providers that worker may use is its own
configuration, so a queued payload cannot spend money by naming a model.

It never turns an observation into a decision. `/api/monitoring` compares
what was observed against thresholds somebody already declared and reports
`review_required`; no route here moves a score, an archetype, a Hard Veto
status, an `ic_state` or a position range.

It never decides the order of an analysis. `/api/harness/triage` runs the
triage set `config/workflow.json` declares, and `/api/harness/full` follows
`harness.py plan` one round at a time; neither route, and no request body,
holds a list of what the workflow is.

A stage that is not built yet answers 501 naming what is missing, rather than
returning an empty result that reads like an answer.
"""
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.models import (DeepDivePlanRequest, DeepDiveRunRequest,  # noqa: E402
                             FullHarnessRequest, JobRequest, ObservationRequest,
                             ParseRequest, ScreenRunRequest, TriageRequest)
from packages.llm import LLMError, resolve_provider  # noqa: E402
from packages.reporting import render_markdown, render_screen_markdown  # noqa: E402
from packages.research import deep_plan, deep_run  # noqa: E402
from packages.research import store as deep_store  # noqa: E402
from packages.screening import compiler, nl, runs_index  # noqa: E402
from packages.screening import rows as row_source  # noqa: E402
from packages.screening import spec as spec_module  # noqa: E402
from packages.screening import store as screen_store  # noqa: E402
from packages.screening.fields import Registry  # noqa: E402

app = FastAPI(title='Outlier Expectation Gap — Research Platform',
              version='0.1.0',
              description='US/KR screening, harness results and evidence-linked deep-dive research.')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get(
        'WEB_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if o.strip()],
    allow_methods=['GET', 'POST'],
    allow_headers=['*'])

def _fx(rates, as_of_date):
    return {code.upper(): {'per_usd': float(value), 'source': 'client-supplied', 'as_of_date': as_of_date}
            for code, value in (rates or {}).items()}


def _rows(as_of_date=None, fx_rates=None):
    """Harness runs merged with the screening warehouse, when it has been built."""
    return row_source.load_rows(as_of_date, fx_rates=fx_rates)


@app.get('/api/health')
def health():
    from packages.screening.fields import Registry
    return {'status': 'ok', 'backends': sorted(Registry().active_backends()),
            'row_source': row_source.resolve_source('auto'),
            'runs': len(runs_index.run_ids()),
            'llm_provider_default': os.environ.get('HARNESS_LLM_PROVIDER', 'fixture')}


@app.get('/api/db/status')
def database_status():
    """Row counts and recent syncs, when a database is configured.

    The index is optional; this route says so rather than pretending to one.
    """
    if row_source.resolve_source('auto') != 'db':
        raise HTTPException(501, 'no database configured; set HARNESS_DATABASE_URL and run '
                                 '`python harness.py db upgrade && python harness.py db sync`')
    from db.repository import status as database_status_rows
    from db.session import engine_for, session_scope
    with session_scope(engine_for()) as session:
        return database_status_rows(session)


@app.get('/api/universe')
def universe():
    rows = runs_index.load_rows()
    return {**runs_index.universe_summary(rows),
            'companies': sorted({(row['ticker'], row.get('company_name'), row['jurisdiction'])
                                 for row in rows})}


@app.get('/api/universe/securities')
def universe_securities(market: str | None = None, investable_only: bool = True,
                        limit: int = Query(200, ge=1, le=5000)):
    """The listed US/KR universe built by `harness.py universe sync`.

    This is the regulator-derived universe, not the completed-run corpus that
    `/api/universe` summarises. Rows excluded as ETFs, warrants, SPAC shells or
    off-market listings stay in the file with the reason, so the answer to
    "why is this missing" does not require a re-sync.
    """
    try:
        from data_adapters import universe as universe_store
    except Exception as error:
        raise HTTPException(501, f'data adapters are not installed: {error}') from error
    payload = universe_store.load()
    if payload is None:
        raise HTTPException(404, 'no universe file yet; run '
                                 '`python harness.py universe sync --markets US,KR`')
    rows = universe_store.investable(payload) if investable_only else payload['securities']
    if market:
        currency = 'KRW' if market.upper() == 'KR' else 'USD'
        rows = [row for row in rows if row.get('currency') == currency]
    return {'synced_at_utc': payload['synced_at_utc'], 'as_of_date': payload.get('as_of_date'),
            'summary': payload['summary'], 'markets': payload.get('markets', {}),
            'count': len(rows), 'securities': rows[:limit]}


@app.get('/api/warehouse')
def warehouse_summary(as_of_date: str | None = None):
    """The deterministic metric warehouse: what it covers and what it could not compute."""
    from packages.screening import warehouse as warehouse_store
    payload = warehouse_store.load(as_of_date)
    if payload is None:
        raise HTTPException(404, 'the screening warehouse has not been built; run '
                                 '`python harness.py screen build --as-of <DATE> --from-runs`')
    return {k: v for k, v in payload.items() if k != 'rows'}


@app.get('/api/warehouse/{ticker}')
def warehouse_company(ticker: str, as_of_date: str | None = None):
    """One company's metrics with the provenance behind every number."""
    from packages.screening import warehouse as warehouse_store
    payload = warehouse_store.load(as_of_date)
    if payload is None:
        raise HTTPException(404, 'the screening warehouse has not been built')
    row = next((r for r in payload['rows'] if r['ticker'].upper() == ticker.upper()), None)
    if row is None:
        raise HTTPException(404, f'{ticker}: not in the warehouse at {payload["as_of_date"]}')
    return row


@app.get('/api/screen/fields')
def screen_fields(available_only: bool = False):
    rows = Registry().describe()
    return [row for row in rows if row['available']] if available_only else rows


@app.get('/api/runs')
def list_runs():
    return [{k: row[k] for k in ('run_id', 'ticker', 'company_name', 'jurisdiction', 'exchange',
                                 'currency', 'as_of_date', 'market_cap_usd', 'core_score',
                                 'ex_valuation_score', 'classification', 'archetype',
                                 'hard_veto_status', 'ic_state', 'position_range',
                                 'price_to_base_value', 'early_exit', 'full_harness_complete')}
            for row in sorted(_rows(), key=lambda r: -(r.get('core_score') or 0))]


@app.get('/api/runs/{run_id}')
def get_run(run_id: str):
    row = runs_index.load_row(run_id)
    if row is None:
        raise HTTPException(404, f'{run_id}: no readable harness run')
    return row


@app.get('/api/companies/{ticker}')
def get_company(ticker: str):
    rows = [row for row in _rows() if row['ticker'].upper() == ticker.upper()]
    if not rows:
        raise HTTPException(404, f'{ticker}: no harness run')
    rows.sort(key=lambda r: r['as_of_date'] or '', reverse=True)
    deep_dives = [row for row in deep_store.list_reports() if row['ticker'].upper() == ticker.upper()]
    return {'ticker': rows[0]['ticker'], 'company_name': rows[0].get('company_name'),
            'jurisdiction': rows[0]['jurisdiction'], 'currency': rows[0].get('currency'),
            'latest': rows[0], 'harness_history': rows, 'deep_dives': deep_dives}


@app.post('/api/screen/parse')
def screen_parse(request: ParseRequest):
    provider = (resolve_provider(request.provider, request.model)
                if request.provider != 'lexicon' else None)
    try:
        return nl.parse(request.text, request.as_of_date, provider=provider,
                        fx_rates=_fx(request.fx_rates, request.as_of_date))
    except (LLMError, spec_module.SpecError) as error:
        raise HTTPException(422, str(error)) from error


@app.post('/api/screen/run')
def screen_run(request: ScreenRunRequest):
    try:
        if request.spec is not None:
            spec = spec_module.normalise(request.spec)
        elif request.text:
            if not request.as_of_date:
                raise HTTPException(422, 'as_of_date is required when screening from text')
            provider = (resolve_provider(request.provider, request.model)
                        if request.provider != 'lexicon' else None)
            spec = nl.parse(request.text, request.as_of_date, provider=provider,
                            fx_rates=_fx(request.fx_rates, request.as_of_date))
        else:
            raise HTTPException(422, 'either spec or text is required')
    except (LLMError, spec_module.SpecError) as error:
        raise HTTPException(422, str(error)) from error

    rows = _rows(spec.get('as_of_date'), spec.get('fx_rates'))
    result = compiler.run(spec, rows)
    record = screen_store.build_record(spec, result, rows_sha256=screen_store.content_hash(
        [{k: v for k, v in row.items() if k != 'match_explain'} for row in rows]))
    record['backends'] = row_source.backend_summary(rows)
    if request.persist:
        screen_store.save(record)
    return record


@app.get('/api/screen/runs')
def screen_runs():
    return screen_store.list_runs()


@app.get('/api/screen/runs/{screen_run_id}')
def screen_run_detail(screen_run_id: str):
    record = screen_store.load(screen_run_id)
    if record is None:
        raise HTTPException(404, f'{screen_run_id}: no such screen run')
    return record


@app.get('/api/screen/runs/{screen_run_id}/markdown', response_class=PlainTextResponse)
def screen_run_markdown(screen_run_id: str):
    record = screen_store.load(screen_run_id)
    if record is None:
        raise HTTPException(404, f'{screen_run_id}: no such screen run')
    return render_screen_markdown(record)


@app.post('/api/harness/triage')
def harness_triage(request: TriageRequest):
    """Stage 3: the triage agents over the selected candidates.

    Defaults to a dry run and to the offline placeholder provider, because
    both alternatives — spending money and writing reports a person will read
    as research — should be asked for rather than stumbled into.
    """
    from packages.orchestration import batch, contracts, selection
    from packages.orchestration import store as triage_store
    config = contracts.load_config()

    if request.screen_run_id:
        record = screen_store.load(request.screen_run_id)
        if record is None:
            raise HTTPException(404, f'{request.screen_run_id}: no such screen run')
        rows, as_of = record['results'], record.get('as_of_date')
    else:
        as_of = request.as_of_date
        rows = _rows(as_of)

    candidates = selection.select_candidates(rows, config=config, top_n=request.top,
                                             stage='triage')
    eligible = [c for c in candidates if c.eligible]
    if request.dry_run:
        return {'as_of_date': as_of, 'dry_run': True,
                'eligible': [c.to_dict() for c in eligible],
                'not_eligible': [c.to_dict() for c in candidates if not c.eligible],
                'verification_scope': config['verification_scope']}

    if request.provider == 'placeholder':
        from packages.orchestration.fixtures import PlaceholderAgentProvider
        provider = PlaceholderAgentProvider()
    else:
        provider = resolve_provider(request.provider, request.model)

    result = batch.run_batch(candidates, provider, config=config, as_of_date=as_of,
                             force=request.force, stage='triage')
    record = triage_store.build_record(result.to_dict(), config, stage='triage')
    if request.persist:
        triage_store.save(record)
    return record


@app.get('/api/harness/triage/runs')
def harness_triage_runs():
    from packages.orchestration import store as triage_store
    return triage_store.list_runs(stage='triage')


@app.get('/api/harness/triage/{triage_run_id}')
def harness_triage_run(triage_run_id: str):
    from packages.orchestration import store as triage_store
    record = triage_store.load(triage_run_id, stage='triage')
    if record is None:
        raise HTTPException(404, f'{triage_run_id}: no such triage run')
    return record


def _orchestration_provider(request):
    """Offline placeholder unless a real model was asked for by name."""
    if request.provider == 'placeholder':
        from packages.orchestration.fixtures import PlaceholderAgentProvider
        return PlaceholderAgentProvider()
    return resolve_provider(request.provider, request.model)


@app.post('/api/harness/full')
def harness_full(request: FullHarnessRequest):
    """Stage 4: the whole harness workflow, one round of `plan` at a time.

    The agent order is not set here or in the request. Each round asks
    `harness.py plan` what comes next and runs exactly that, so the stage
    machine stays in `harness_core.planner`. `screened_out` in a result means
    the planner reached an early exit — a conclusion, not an error.
    """
    from packages.orchestration import batch, contracts, full as full_stage, selection
    from packages.orchestration import store as batch_store
    config = contracts.load_config()

    if request.run_ids:
        if request.dry_run:
            return {'stage': 'full', 'dry_run': True, 'run_ids': request.run_ids,
                    'readiness': [{'run_id': run_id, **full_stage.readiness(run_id)}
                                  for run_id in request.run_ids],
                    'verification_scope': config['verification_scope']}
        provider = _orchestration_provider(request)
        outcomes = [full_stage.full_harness_company(run_id, provider, config=config,
                                                    force=request.force,
                                                    max_iterations=request.max_rounds)
                    for run_id in request.run_ids]
        return {'stage': 'full', 'verification_scope': config['verification_scope'],
                'results': [outcome.to_dict() for outcome in outcomes]}

    if request.screen_run_id:
        record = screen_store.load(request.screen_run_id)
        if record is None:
            raise HTTPException(404, f'{request.screen_run_id}: no such screen run')
        rows, as_of = record['results'], record.get('as_of_date')
    else:
        as_of = request.as_of_date
        rows = _rows(as_of)

    candidates = selection.select_candidates(rows, config=config, top_n=request.top,
                                             stage='full')
    eligible = [c for c in candidates if c.eligible]
    if request.dry_run:
        return {'as_of_date': as_of, 'stage': 'full', 'dry_run': True,
                'eligible': [c.to_dict() for c in eligible],
                'not_eligible': [c.to_dict() for c in candidates if not c.eligible],
                'verification_scope': config['verification_scope']}

    result = batch.run_batch(candidates, _orchestration_provider(request), config=config,
                             as_of_date=as_of, force=request.force, stage='full')
    record = batch_store.build_record(result.to_dict(), config, stage='full')
    if request.persist:
        batch_store.save(record)
    return record


@app.get('/api/harness/full/runs')
def harness_full_runs():
    from packages.orchestration import store as batch_store
    return batch_store.list_runs(stage='full')


@app.get('/api/harness/full/{full_run_id}')
def harness_full_run(full_run_id: str):
    from packages.orchestration import store as batch_store
    record = batch_store.load(full_run_id, stage='full')
    if record is None:
        raise HTTPException(404, f'{full_run_id}: no such full-harness run')
    return record


@app.get('/api/harness/runs/{run_id}')
def harness_run(run_id: str):
    return get_run(run_id)


@app.get('/api/monitoring')
def monitoring_portfolio(tickers: str | None = None, as_of_date: str | None = None):
    """One row per monitored company: what needs a person, and what nobody is watching.

    With no `tickers`, the companies someone has actually recorded an
    observation for. Asking for a company with no observations is allowed and
    useful — the answer is how much of its watchlist has never been looked at.
    """
    from packages.monitoring import evaluate as monitor_evaluate
    from packages.monitoring import observations as observation_log
    names = [t.strip() for t in tickers.split(',')] if tickers else observation_log.tickers()
    if not names:
        return {'companies': 0, 'rows': [], 'unreadable': [],
                'note': 'no observations recorded yet; pass ?tickers= to see what is unwatched'}
    return monitor_evaluate.portfolio([n for n in names if n], as_of_date)


@app.get('/api/monitoring/{ticker}')
def monitoring_company(ticker: str, as_of_date: str | None = None,
                       run_id: str | None = None):
    """Every declared KPI and falsifier for one company, with its current status."""
    from packages.monitoring import evaluate as monitor_evaluate
    try:
        return monitor_evaluate.evaluate(ticker, as_of_date, run_id)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.get('/api/monitoring/{ticker}/watchlist')
def monitoring_watchlist(ticker: str, run_id: str | None = None):
    """What was declared, before any observation is applied to it."""
    from packages.monitoring import watchlist as watchlist_builder
    try:
        return watchlist_builder.build(ticker, run_id)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.get('/api/monitoring/{ticker}/drift')
def monitoring_drift(ticker: str, run_ids: str | None = None):
    """What changed between this company's harness runs, and whether that is the company."""
    from packages.monitoring import drift
    names = [r.strip() for r in run_ids.split(',')] if run_ids else None
    try:
        return drift.series(ticker, run_ids=names)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.post('/api/monitoring/observations')
def monitoring_observe(request: ObservationRequest):
    """Append one observation. Nothing is edited; a correction sets `supersedes`."""
    from packages.monitoring import observations as observation_log
    from packages.monitoring import watchlist as watchlist_builder
    run_as_of = None
    try:
        run_as_of = watchlist_builder.build(request.ticker)['as_of_date']
    except ValueError:
        pass
    try:
        return observation_log.record(
            request.ticker, request.watch_id, as_of_date=request.as_of_date,
            source=request.source, source_type=request.source_type, value=request.value,
            unit=request.unit, triggered=request.triggered, period=request.period,
            fact_or_estimate=request.fact_or_estimate, note=request.note,
            supersedes=request.supersedes, run_as_of_date=run_as_of)
    except observation_log.ObservationRejected as error:
        raise HTTPException(422, str(error)) from error


def _job_engine():
    """The queue is a table, so no database means no queue — said, not guessed."""
    from db.session import DatabaseNotConfigured, engine_for
    try:
        engine = engine_for()
    except DatabaseNotConfigured as error:
        raise HTTPException(501, f'{error} The job queue lives in that database.') from error
    from sqlalchemy import inspect
    if 'job' not in set(inspect(engine).get_table_names()):
        raise HTTPException(501, 'no job table; run `python harness.py db upgrade` first')
    return engine


@app.get('/api/jobs')
def jobs_list(status: str | None = None, kind: str | None = None,
              limit: int = Query(20, ge=1, le=200)):
    """Recent jobs, newest first, with the queue's own summary."""
    from db.session import session_scope
    from workers import queue as job_queue
    with session_scope(_job_engine()) as session:
        return {'summary': job_queue.summary(session),
                'jobs': job_queue.recent(session, limit, status, kind)}


@app.get('/api/jobs/locks')
def jobs_locks():
    """Resources held by running jobs, and the queued jobs waiting on them.

    A queue that looks busy because everything is waiting on one long run is a
    different situation from a queue with work nobody has started, and the
    summary alone cannot tell them apart.
    """
    from db.session import session_scope
    from workers import locks as job_locks
    from workers import queue as job_queue
    config = job_queue.load_config()
    with session_scope(_job_engine()) as session:
        return {'held': job_locks.held(session),
                'blocked': job_queue.blocked(session, None, config),
                'enabled': job_locks.enabled(config)}


@app.get('/api/jobs/{job_id}')
def jobs_get(job_id: int):
    from db.models import Job
    from db.session import session_scope
    from workers import queue as job_queue
    with session_scope(_job_engine()) as session:
        job = session.get(Job, job_id)
        if job is None:
            raise HTTPException(404, f'no job {job_id}')
        return job_queue.to_dict(job)


@app.post('/api/jobs')
def jobs_enqueue(request: JobRequest):
    """Queue work. Enqueueing is not running: a worker has to pick it up.

    The same `idempotency_key` twice returns the row that already exists, so a
    client retrying a timed-out POST does not queue the work twice.
    """
    from db.session import session_scope
    from workers import handlers, queue as job_queue
    config = job_queue.load_config()
    problem = handlers.payload_is_safe(request.payload)
    if problem:
        raise HTTPException(422, problem)
    with session_scope(_job_engine()) as session:
        try:
            job = job_queue.enqueue(session, request.kind, request.payload, config,
                                    idempotency_key=request.idempotency_key,
                                    priority=request.priority,
                                    max_attempts=request.max_attempts)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        return job_queue.to_dict(job)


@app.post('/api/deep-dive/plan')
def deep_dive_plan(request: DeepDivePlanRequest):
    try:
        return deep_plan.build(request.run_id, user_requested=request.user_requested)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.post('/api/deep-dive/run')
def deep_dive_run(request: DeepDiveRunRequest):
    fixtures = ROOT / 'packages' / 'research' / 'fixtures' / request.run_id
    provider_kwargs = {'root': fixtures} if request.provider == 'fixture' else {}
    try:
        provider = resolve_provider(request.provider, request.model, **provider_kwargs)
        report, plan, _path = deep_run.run(request.run_id, provider,
                                           user_requested=request.user_requested)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
    except LLMError as error:
        raise HTTPException(422, str(error)) from error
    return {'deep_dive_id': report['metadata']['deep_dive_id'], 'plan': plan, 'report': report}


@app.get('/api/deep-dive')
def deep_dive_list():
    return deep_store.list_reports()


@app.get('/api/deep-dive/{deep_dive_id}')
def deep_dive_detail(deep_dive_id: str):
    report = deep_store.load(deep_dive_id)
    if report is None:
        raise HTTPException(404, f'{deep_dive_id}: no such deep dive')
    return {'report': report, 'plan': deep_store.load_plan(deep_dive_id)}


@app.get('/api/reports/{deep_dive_id}')
def report_detail(deep_dive_id: str, fmt: str = Query('json', pattern='^(json|markdown)$')):
    report = deep_store.load(deep_dive_id)
    if report is None:
        raise HTTPException(404, f'{deep_dive_id}: no such report')
    if fmt == 'markdown':
        return PlainTextResponse(render_markdown(report))
    return report
