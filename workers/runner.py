"""The loop: claim, run, record. Everything interesting is elsewhere.

A worker is deliberately dull. It takes one job at a time, calls a handler
that already existed, and writes down what happened. It holds no policy of its
own — which kinds exist, how long a lease lasts, how many attempts a job gets
and which providers may be used all come from `config/workers.json`.

Three behaviours are worth stating because their absence is what usually makes
a worker untrustworthy.

**A crash is a failure, not a silence.** Any exception a handler raises is
caught, written to the row and backed off or failed. A worker that dies
without recording why leaves a `running` row that only the reaper can explain.

**A stop is graceful.** SIGTERM and SIGINT set a flag; the job in flight
finishes and the loop exits. Killing a worker mid-handler is safe too — the
lease expires and the job comes back — but finishing is better than relying on
that.

**Every pass reaps first.** Leases expire while nobody is looking, so the
first thing a loop does is return abandoned work to the queue.
"""
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from db.models import Job
from db.session import engine_for, session_scope

from . import handlers, queue


@dataclass
class RunReport:
    worker_id: str
    kinds: Optional[list] = None
    processed: list = field(default_factory=list)
    reaped: list = field(default_factory=list)
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
    stopped_by: Optional[str] = None

    @property
    def summary(self) -> dict:
        by_status: dict = {}
        for row in self.processed:
            by_status[row['status']] = by_status.get(row['status'], 0) + 1
        return {'claimed': len(self.processed),
                'completed': by_status.get('completed', 0),
                'requeued': by_status.get('queued', 0),
                'failed': by_status.get('failed', 0),
                'reaped': len(self.reaped),
                'by_status': by_status}

    def to_dict(self) -> dict:
        return {'worker_id': self.worker_id, 'kinds': self.kinds, 'summary': self.summary,
                'started_at_utc': self.started_at_utc, 'finished_at_utc': self.finished_at_utc,
                'stopped_by': self.stopped_by, 'processed': self.processed,
                'reaped': self.reaped}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StopFlag:
    """SIGTERM/SIGINT set this; the loop finishes its job and exits."""

    def __init__(self):
        self.reason: Optional[str] = None
        self._previous: dict = {}

    def install(self) -> 'StopFlag':
        for number in (signal.SIGTERM, signal.SIGINT):
            try:
                self._previous[number] = signal.getsignal(number)
                signal.signal(number, self._handle)
            except (ValueError, OSError):
                # Not the main thread, or a platform without the signal.
                pass
        return self

    def restore(self) -> None:
        for number, previous in self._previous.items():
            try:
                signal.signal(number, previous)
            except (ValueError, OSError):
                pass
        self._previous.clear()

    def _handle(self, number, _frame):
        self.reason = signal.Signals(number).name

    def __bool__(self) -> bool:
        return self.reason is not None


def run_one(engine, kinds: Optional[list] = None, config: Optional[dict] = None,
            owner: Optional[str] = None) -> Optional[dict]:
    """Claim one job and see it through. Returns what happened, or None if idle.

    The claim, the work and the result are three separate transactions on
    purpose. Holding one open across a handler that takes an hour would pin a
    connection and block the reaper from seeing anything.
    """
    config = config or queue.load_config()
    owner = owner or queue.worker_id()

    with session_scope(engine) as session:
        job = queue.claim(session, kinds, config, owner)
        if job is None:
            return None
        claimed = queue.to_dict(job)

    job_id, kind, payload = claimed['job_id'], claimed['kind'], claimed['payload'] or {}
    started = time.monotonic()
    result, error, refused = None, None, False
    try:
        problem = handlers.payload_is_safe(payload)
        if problem:
            raise handlers.HandlerRefused(problem)
        result = handlers.resolve(kind, config)(payload, config)
    except handlers.HandlerRefused as failure:
        # A refusal is a decision, not a fault: retrying will refuse again.
        error, refused = str(failure), True
    except Exception as failure:                      # noqa: BLE001 - recorded, not swallowed
        error = f'{type(failure).__name__}: {failure}'

    with session_scope(engine) as session:
        row = session.get(Job, job_id)
        if row is None:                               # deleted underneath us
            return {**claimed, 'status': 'missing', 'error': 'the job row disappeared'}
        if error is None:
            queue.complete(session, row, result)
        else:
            queue.fail(session, row, error, config, retryable=not refused)
        final = queue.to_dict(row)
    final['duration_seconds'] = round(time.monotonic() - started, 3)
    return final


def run(engine=None, kinds: Optional[list] = None, config: Optional[dict] = None,
        once: bool = False, max_jobs: Optional[int] = None,
        max_seconds: Optional[float] = None, poll_interval: Optional[float] = None,
        owner: Optional[str] = None, install_signals: bool = True) -> RunReport:
    """Work the queue until it is empty (`once`), a limit is hit, or a signal arrives."""
    config = config or queue.load_config()
    engine = engine or engine_for()
    owner = owner or queue.worker_id()
    interval = poll_interval if poll_interval is not None \
        else float(config['execution'].get('poll_interval_seconds', 5))
    handlers.declared_kinds(config)                   # fail fast on a config/handler mismatch

    report = RunReport(worker_id=owner, kinds=kinds, started_at_utc=_now())
    stop = StopFlag()
    if install_signals:
        stop.install()
    deadline = (time.monotonic() + max_seconds) if max_seconds else None

    try:
        while True:
            if stop:
                report.stopped_by = f'signal {stop.reason}'
                break
            if deadline and time.monotonic() >= deadline:
                report.stopped_by = 'max_seconds'
                break
            if max_jobs is not None and len(report.processed) >= max_jobs:
                report.stopped_by = 'max_jobs'
                break

            if (config.get('reaper') or {}).get('enabled', True):
                with session_scope(engine) as session:
                    report.reaped.extend(queue.reap(session, config))

            outcome = run_one(engine, kinds, config, owner)
            if outcome is not None:
                report.processed.append(outcome)
                continue
            if once:
                report.stopped_by = 'queue empty'
                break
            # Sleep in slices so a signal is noticed promptly.
            waited = 0.0
            while waited < interval and not stop:
                time.sleep(min(0.25, interval - waited))
                waited += 0.25
    finally:
        if install_signals:
            stop.restore()
    report.finished_at_utc = _now()
    return report
