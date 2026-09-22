"""A stage over many candidates: retries, idempotency and a stop condition.

The same loop runs Stage 3 and Stage 4. What differs is the per-company runner
— four triage agents, or the whole planner-driven workflow — and that is a
parameter, because the guards below are about the batch and not about which
agents it happens to be running.

A batch is a loop with three guards.

**Idempotency** belongs to the step, not the batch: `run_agent` skips work that
is already complete and still valid for the current frozen snapshot, so a
re-run of a finished batch does nothing and says so.

**A repeated failure stops the batch.** If several companies in a row fail, the
cause is almost never those companies — it is the provider, the credentials or
the policy — and grinding through the rest turns one problem into a hundred
identical ones. The threshold is config, and a stop is recorded as a stop
rather than as a set of failures.

**A block is not a completion.** Candidates that could not be worked on are
counted separately from candidates the harness screened out, because those are
different answers to different questions.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from . import contracts
from .selection import Candidate
from .triage import TriageOutcome, triage_company

# Statuses that mean this company produced no usable result. A repeated run of
# them is the signal that the problem is shared rather than per-company.
FAILURE_STATUSES = ('failed', 'partial', 'stalled')


@dataclass
class BatchResult:
    as_of_date: Optional[str]
    outcomes: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    stopped_early: bool = False
    stop_reason: Optional[str] = None
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
    stage: str = 'triage'

    @property
    def summary(self) -> dict:
        by_status: dict = {}
        by_control: dict = {}
        for outcome in self.outcomes:
            by_status[outcome.status] = by_status.get(outcome.status, 0) + 1
            control = outcome.execution_control or 'unknown'
            by_control[control] = by_control.get(control, 0) + 1
        attempts = sum(step.attempts for o in self.outcomes for step in o.steps)
        retried = sum(1 for o in self.outcomes for step in o.steps if step.attempts > 1)
        return {
            'attempted': len(self.outcomes),
            'completed': by_status.get('completed', 0),
            'screened_out': by_status.get('screened_out', 0),
            'partial': by_status.get('partial', 0),
            'blocked': by_status.get('blocked', 0),
            'stalled': by_status.get('stalled', 0),
            'failed': by_status.get('failed', 0),
            'not_eligible': len(self.skipped),
            'by_status': by_status,
            'by_execution_control': by_control,
            'agent_attempts': attempts,
            'steps_needing_retry': retried,
            'steps_skipped_as_current': sum(1 for o in self.outcomes for s in o.steps
                                            if s.status == 'skipped'),
            'stopped_early': self.stopped_early,
            'stop_reason': self.stop_reason,
        }

    def to_dict(self) -> dict:
        return {'as_of_date': self.as_of_date, 'stage': self.stage, 'summary': self.summary,
                'started_at_utc': self.started_at_utc, 'finished_at_utc': self.finished_at_utc,
                'results': [outcome.to_dict() for outcome in self.outcomes],
                'not_eligible': [candidate.to_dict() for candidate in self.skipped]}


def _triage_runner(run_id, provider, config, force):
    return triage_company(run_id, provider, config=config, force=force,
                          agents=contracts.triage_agents(config))


def _full_runner(run_id, provider, config, force):
    from .full import full_harness_company
    return full_harness_company(run_id, provider, config=config, force=force)


RUNNERS = {'triage': _triage_runner, 'full': _full_runner}


def run_batch(candidates: list, provider, config: Optional[dict] = None,
              as_of_date: Optional[str] = None, force: bool = False,
              on_result: Optional[Callable[[TriageOutcome], None]] = None,
              stage: str = 'triage') -> BatchResult:
    """Run one orchestration stage across the eligible candidates, in order."""
    config = config or contracts.load_config()
    execution = config['execution']
    limit = int(execution.get('stop_batch_after_consecutive_failures', 5) or 0)
    if stage not in RUNNERS:
        raise ValueError(f'unknown batch stage {stage!r}; known: {sorted(RUNNERS)}')
    runner = RUNNERS[stage]

    result = BatchResult(as_of_date=as_of_date, stage=stage,
                         started_at_utc=datetime.now(timezone.utc).isoformat())
    result.skipped = [c for c in candidates if not c.eligible]
    consecutive = 0

    for candidate in [c for c in candidates if c.eligible]:
        outcome = runner(candidate.run_id, provider, config, force)
        result.outcomes.append(outcome)
        if on_result is not None:
            on_result(outcome)

        # A block is an input problem, not a provider problem, so it does not
        # count toward the circuit breaker. A stall does: one company that
        # cannot converge is a puzzle, five in a row is a defect.
        if outcome.status in FAILURE_STATUSES:
            consecutive += 1
        else:
            consecutive = 0
        if limit and consecutive >= limit:
            result.stopped_early = True
            result.stop_reason = (
                f'{consecutive} companies in a row produced no valid report. That is almost '
                'never the companies — check the provider, the credentials and the policy '
                'before continuing.')
            break

    result.finished_at_utc = datetime.now(timezone.utc).isoformat()
    return result
