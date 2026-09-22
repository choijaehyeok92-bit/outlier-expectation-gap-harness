"""Run one agent against one frozen run.

The shape of a step is: ask the harness for the prompt, ask the provider for a
report, let the harness judge it, and only then write. Four properties hold it
together.

**Nothing is written until the harness accepts it.** A candidate report lives
in a temp file until both validation layers pass, then moves into place
atomically. A half-written or rejected report must never appear under
`reports/`, because `load_reports` would pick it up and `aggregate` would score
it.

**Identity is not the model's to choose.** `agent_id`, `ticker`, `as_of_date`,
`domain` and `role` come from the manifest and the run, and are overwritten on
the response before validation. A model that renames itself FS while answering
the EV prompt would otherwise pass every check.

**Retries repair format, never content.** The retry prompt carries the
validator's own error strings and nothing else. "score_0_100 does not equal the
rubric weighted score" is a defect in the document; "your score is too low"
would be steering the analysis, and this orchestrator never says it.

**A step already done is not redone.** The idempotency key includes the run's
frozen input snapshot, so re-freezing correctly invalidates earlier agent work
while an unchanged run is simply skipped.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import contracts

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_FIELDS = ('agent_id', 'ticker', 'as_of_date', 'domain', 'role')
RETRY_PREFACE = (
    '\n\n## 직전 제출물이 검증을 통과하지 못했다\n'
    '아래는 하네스 검증기가 낸 오류다. 형식과 규칙을 고쳐 문서를 다시 제출한다.\n'
    '어떤 판정을 내릴지는 지시하지 않는다 — 점수·verdict·Veto 상태는 네 분석의 결과여야 한다.\n')


@dataclass(frozen=True)
class AgentStep:
    run_id: str
    agent_id: str
    as_of_date: Optional[str]
    input_snapshot_sha256: Optional[str]
    policy_version: Optional[str]

    @property
    def idempotency_key(self) -> str:
        return hashlib.sha256('|'.join([
            self.run_id, self.agent_id, self.input_snapshot_sha256 or '-',
            self.policy_version or '-']).encode('utf-8')).hexdigest()

    def to_dict(self) -> dict:
        return {**self.__dict__, 'idempotency_key': self.idempotency_key}


@dataclass
class StepOutcome:
    step: AgentStep
    status: str                       # completed | skipped | failed | blocked
    attempts: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None
    errors: list = field(default_factory=list)
    reason: Optional[str] = None
    report_path: Optional[str] = None
    finished_at_utc: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status in ('completed', 'skipped')

    def to_dict(self) -> dict:
        return {'run_id': self.step.run_id, 'agent_id': self.step.agent_id,
                'status': self.status, 'attempts': self.attempts,
                'provider': self.provider, 'model': self.model,
                'errors': self.errors[:6], 'reason': self.reason,
                'report_path': self.report_path,
                'idempotency_key': self.step.idempotency_key,
                'finished_at_utc': self.finished_at_utc}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_directory(run_id: str) -> Path:
    """Where the harness says this run lives.

    Deliberately `runtime.run_dir` rather than a path built here: it applies
    the harness's own identifier check, and it follows `runtime.ROOT`, so a
    test that isolates the harness isolates the orchestrator with it.
    """
    return contracts.harness().run_dir(run_id)


def repo_root() -> Path:
    return contracts.harness().ROOT


def build_step(run_id: str, agent_id: str) -> AgentStep:
    runtime = contracts.harness()
    manifest = runtime.load_manifest(run_id)
    return AgentStep(run_id=run_id, agent_id=agent_id,
                     as_of_date=manifest.get('as_of_date'),
                     input_snapshot_sha256=manifest.get('input_snapshot_sha256'),
                     policy_version=manifest.get('decision_policy_version'))


def readiness(run_id: str) -> dict:
    """Whether this run may be worked on at all. Stage 0 is not bypassed."""
    runtime = contracts.harness()
    run = run_directory(run_id)
    if not (run / 'company_context.json').exists():
        return {'ready': False, 'reason': f'{run_id}: no run directory; `harness.py init` first'}
    manifest = runtime.load_manifest(run_id)
    if not manifest.get('frozen'):
        return {'ready': False, 'reason': f'{run_id}: inputs are not frozen'}
    try:
        runtime.assert_frozen_inputs(run_id)
    except SystemExit as error:
        return {'ready': False, 'reason': str(error)}
    status = runtime.intake_status(run_id)
    if status['blocking']:
        gaps = [f"{g['id']} ({g['found']}/{g['needed']})"
                for g in (status['coverage'] or {}).get('blocking_gaps', [])]
        return {'ready': False,
                'reason': f'{run_id}: Stage 0 incomplete — ' + '; '.join(gaps + status['invariant_errors'][:2])}
    return {'ready': True, 'reason': None}


def existing_report(run_id: str, agent_id: str) -> Optional[dict]:
    path = run_directory(run_id) / 'reports' / f'{agent_id}.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return None


def already_done(run_id: str, agent_id: str, step: AgentStep) -> Optional[str]:
    """Why this step needs no work, or None if it does.

    A complete report that still validates is done. A complete report produced
    against a different frozen snapshot is not: the inputs moved underneath it.
    """
    report = existing_report(run_id, agent_id)
    if report is None or report.get('analysis_status') != 'complete':
        return None
    if contracts.validate(report):
        return None
    record = provenance(run_id, agent_id)
    if record and record.get('idempotency_key') not in (None, step.idempotency_key):
        return None
    return 'a complete, valid report already exists for this frozen snapshot'


def provenance_path(run_id: str, agent_id: str) -> Path:
    return run_directory(run_id) / 'orchestration' / f'{agent_id}.json'


def provenance(run_id: str, agent_id: str) -> Optional[dict]:
    path = provenance_path(run_id, agent_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return None


def write_provenance(outcome: StepOutcome, prompt_sha256: str) -> Path:
    """Orchestration metadata, beside the report rather than inside it.

    The agent report keeps exactly the shape a human analyst would write. Who
    ran it, with which provider, after how many attempts, belongs next to it.
    """
    path = provenance_path(outcome.step.run_id, outcome.step.agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        **outcome.step.to_dict(), 'status': outcome.status, 'attempts': outcome.attempts,
        'provider': outcome.provider, 'model': outcome.model,
        'prompt_sha256': prompt_sha256, 'validation_errors': outcome.errors[:6],
        'finished_at_utc': outcome.finished_at_utc,
        'note': 'Orchestration metadata. The harness scored the report; this records how it '
                'was produced, and nothing about whether its analysis is right.',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def build_prompt(run_id: str, agent_id: str) -> str:
    """The harness's own prompt for this agent. Not reworded here.

    `cmd_prompt` is a CLI command and announces itself on stdout; a library
    call should not. Its output is captured rather than its behaviour changed,
    so the prompt the orchestrator sends is byte-for-byte the one a person
    would get from `harness.py prompt`.
    """
    runtime = contracts.harness()
    with tempfile.NamedTemporaryFile('r+', suffix='.md', delete=False, encoding='utf-8') as handle:
        target = handle.name
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            runtime.cmd_prompt(argparse.Namespace(ticker=run_id, target=agent_id, out=target))
        return Path(target).read_text(encoding='utf-8')
    finally:
        os.unlink(target)


def _stamp_identity(report: dict, run_id: str, agent_id: str, as_of_date: Optional[str]) -> dict:
    runtime = contracts.harness()
    agent = next((a for a in runtime.MANIFEST if a['agent_id'] == agent_id), None)
    if agent is None:
        raise ValueError(f'unknown agent {agent_id}')
    context = runtime.load_json(run_directory(run_id) / 'company_context.json')
    return {**report, 'agent_id': agent_id, 'domain': agent['domain'], 'role': agent['role'],
            'ticker': context.get('ticker') or run_id,
            'as_of_date': as_of_date or context.get('as_of_date')}


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile('w', dir=path.parent, suffix='.tmp', delete=False,
                                         encoding='utf-8')
    try:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()
        os.replace(handle.name, path)
    except Exception:
        handle.close()
        Path(handle.name).unlink(missing_ok=True)
        raise


def run_agent(run_id: str, agent_id: str, provider, config: Optional[dict] = None,
              force: bool = False, schema: Optional[dict] = None) -> StepOutcome:
    """One agent, end to end. Returns an outcome rather than raising."""
    config = config or contracts.load_config()
    schema = schema or contracts.load_schema()
    execution = config['execution']
    step = build_step(run_id, agent_id)
    outcome = StepOutcome(step=step, status='failed',
                          provider=getattr(provider, 'name', None),
                          model=getattr(provider, 'model', None))

    gate = readiness(run_id)
    if not gate['ready']:
        outcome.status, outcome.reason = 'blocked', gate['reason']
        outcome.finished_at_utc = _now()
        return outcome

    if not force:
        done = already_done(run_id, agent_id, step)
        if done:
            outcome.status, outcome.reason = 'skipped', done
            outcome.finished_at_utc = _now()
            outcome.report_path = str((run_directory(run_id) / 'reports' / f'{agent_id}.json')
                                      .relative_to(repo_root()))
            return outcome

    try:
        prompt = build_prompt(run_id, agent_id)
    except SystemExit as error:
        outcome.status, outcome.reason = 'blocked', str(error)
        outcome.finished_at_utc = _now()
        return outcome
    prompt_sha = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    attempts = int(execution.get('max_attempts_per_agent', 3))
    message = prompt
    for attempt in range(1, attempts + 1):
        outcome.attempts = attempt
        try:
            candidate = provider.complete_json(stage=f'agent:{agent_id}', prompt=message,
                                               schema=schema,
                                               context={'run_id': run_id, 'agent_id': agent_id})
        except Exception as error:
            outcome.errors = [f'provider: {type(error).__name__}: {error}']
            message = prompt + RETRY_PREFACE + '\n'.join(f'- {e}' for e in outcome.errors)
            continue

        try:
            candidate = _stamp_identity(dict(candidate), run_id, agent_id, step.as_of_date)
        except Exception as error:
            outcome.errors = [f'identity: {error}']
            break

        errors = contracts.validate(candidate, schema)
        if not errors:
            path = run_directory(run_id) / 'reports' / f'{agent_id}.json'
            _atomic_write(path, candidate)
            outcome.status = 'completed'
            outcome.errors = []
            outcome.report_path = str(path.relative_to(repo_root()))
            outcome.finished_at_utc = _now()
            write_provenance(outcome, prompt_sha)
            return outcome

        outcome.errors = errors
        # Only the validator's own words go back. Never a hint about the verdict.
        message = prompt + RETRY_PREFACE + '\n'.join(f'- {e}' for e in errors[:12])

    outcome.status = 'failed'
    outcome.reason = f'did not pass validation in {outcome.attempts} attempt(s)'
    outcome.finished_at_utc = _now()
    write_provenance(outcome, prompt_sha)
    return outcome
