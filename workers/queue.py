"""Claiming work out of the `job` table.

The queue is the database. There is no broker, and that is a decision rather
than a shortcut: `job` already carried `idempotency_key`, `status` and
`attempts`, a Postgres `SELECT … FOR UPDATE SKIP LOCKED` is the standard way
to hand rows to competing consumers, and — the part that decided it — the
whole mechanism can be exercised by a unit test on both dialects with no
service running. A queue nobody can test is not a queue. The handler contract
does not mention the transport, so a broker can be put in front of this later
without touching a single handler.

Four things have to be true of a claim, and each is enforced here rather than
trusted.

**A claimed job goes to exactly one worker.** On PostgreSQL that is
`FOR UPDATE SKIP LOCKED`. SQLite has no such clause and no real concurrency,
so the claim is a conditional `UPDATE … WHERE status='queued'` whose row count
decides the winner — the same guarantee by a different route.

**A dead worker does not hold a job forever.** Every claim takes a lease.
Once it expires the row is claimable again, which is why every handler is
required to be idempotent: reclaiming can run one twice.

**A failure backs off.** A retry moves `available_at` forward. Returning a
failed job straight to `queued` would retry against whatever broke it as fast
as the loop spins.

**A job that is out of attempts stops.** It becomes `failed` with its error,
not `queued` forever. Silence is not a retry policy.
"""
import json
import os
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select, update

from db.models import Job

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'workers.json'
TERMINAL = ('completed', 'failed', 'cancelled')


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG).read_text(encoding='utf-8'))


def worker_id() -> str:
    return f'{socket.gethostname()}:{os.getpid()}'


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    """SQLite hands back naive datetimes; comparing them to aware ones raises."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def kind_settings(kind: str, config: dict) -> dict:
    settings = (config.get('kinds') or {}).get(kind)
    if settings is None:
        raise ValueError(
            f'unknown job kind {kind!r}; config/workers.json declares '
            f'{sorted((config.get("kinds") or {}))}')
    return settings


def lease_seconds(kind: str, config: dict) -> int:
    execution = config['execution']
    try:
        return int(kind_settings(kind, config).get('lease_seconds')
                   or execution['lease_seconds'])
    except ValueError:
        return int(execution['lease_seconds'])


def backoff_for(attempts: int, config: dict) -> int:
    schedule = config['execution'].get('backoff_seconds') or [30]
    return int(schedule[min(max(attempts, 1) - 1, len(schedule) - 1)])


def enqueue(session, kind: str, payload: dict, config: Optional[dict] = None,
            idempotency_key: Optional[str] = None, priority: int = 100,
            available_at: Optional[datetime] = None,
            max_attempts: Optional[int] = None) -> Job:
    """Queue one job. The same key twice returns the same row, never a second one.

    The kind is checked against the config here rather than at claim time: a
    typo should be refused by whoever enqueues it, not discovered by a worker
    an hour later.
    """
    from db.sync import content_hash
    config = config or load_config()
    kind_settings(kind, config)
    key = idempotency_key or content_hash([kind, payload])
    existing = session.scalar(select(Job).where(Job.idempotency_key == key))
    if existing is not None:
        return existing
    job = Job(kind=kind, status='queued', idempotency_key=key, payload=payload,
              priority=priority, available_at=available_at or _now(),
              max_attempts=int(max_attempts or config['execution']['max_attempts']))
    session.add(job)
    session.flush()
    return job


def _claimable(kinds: Optional[list]):
    condition = (Job.status == 'queued') & (Job.available_at <= _now())
    if kinds:
        condition = condition & Job.kind.in_(kinds)
    return condition


def claim(session, kinds: Optional[list] = None, config: Optional[dict] = None,
          owner: Optional[str] = None) -> Optional[Job]:
    """Take one queued job, or None. Never hands the same row to two workers."""
    config = config or load_config()
    owner = owner or worker_id()
    dialect = session.get_bind().dialect.name

    statement = (select(Job).where(_claimable(kinds))
                 .order_by(Job.priority.asc(), Job.available_at.asc(), Job.job_id.asc())
                 .limit(1))
    if dialect == 'postgresql':
        statement = statement.with_for_update(skip_locked=True)

    job = session.scalar(statement)
    if job is None:
        return None

    lease = lease_seconds(job.kind, config)
    values = {'status': 'running', 'attempts': Job.attempts + 1, 'worker_id': owner,
              'started_at': _now(), 'finished_at': None, 'error': None,
              'lease_expires_at': _now() + timedelta(seconds=lease)}
    # The `status == 'queued'` predicate is the claim on SQLite, where there is
    # no SKIP LOCKED: whoever's UPDATE matches a row has it, and a second
    # worker's UPDATE matches nothing.
    result = session.execute(update(Job).where(Job.job_id == job.job_id,
                                               Job.status == 'queued').values(**values))
    if result.rowcount != 1:
        return None
    session.flush()
    session.refresh(job)
    return job


def heartbeat(session, job: Job, config: Optional[dict] = None) -> None:
    """Extend the lease of a job still being worked on."""
    config = config or load_config()
    job.lease_expires_at = _now() + timedelta(seconds=lease_seconds(job.kind, config))
    session.flush()


def complete(session, job: Job, result: Optional[dict] = None) -> Job:
    job.status = 'completed'
    job.result = result
    job.error = None
    job.finished_at = _now()
    job.lease_expires_at = None
    session.flush()
    return job


def fail(session, job: Job, error: str, config: Optional[dict] = None,
         retryable: bool = True) -> Job:
    """Back off and retry, or stop and say why. Never a silent requeue."""
    config = config or load_config()
    job.error = str(error)[:4000]
    job.lease_expires_at = None
    if retryable and job.attempts < job.max_attempts:
        job.status = 'queued'
        job.available_at = _now() + timedelta(seconds=backoff_for(job.attempts, config))
        job.worker_id = None
    else:
        job.status = 'failed'
        job.finished_at = _now()
    session.flush()
    return job


def cancel(session, job_id: int) -> Optional[Job]:
    """Cancel a job that has not finished. A finished job is left as it is."""
    job = session.get(Job, job_id)
    if job is None or job.status in TERMINAL:
        return job
    job.status = 'cancelled'
    job.finished_at = _now()
    job.lease_expires_at = None
    session.flush()
    return job


def retry(session, job_id: int, config: Optional[dict] = None) -> Optional[Job]:
    """Put a failed job back in the queue, raising its cap by one attempt.

    Without the cap moving, requeueing a job that already spent its attempts
    would be claimed once and fail again immediately, which looks like the
    retry did nothing.
    """
    config = config or load_config()
    job = session.get(Job, job_id)
    if job is None or job.status not in ('failed', 'cancelled'):
        return job
    job.status = 'queued'
    job.available_at = _now()
    job.lease_expires_at = None
    job.worker_id = None
    job.finished_at = None
    job.max_attempts = max(int(job.max_attempts), int(job.attempts) + 1)
    session.flush()
    return job


def reap(session, config: Optional[dict] = None) -> list:
    """Return jobs whose lease expired to the queue, or fail them if spent.

    A worker that was killed leaves `running` rows behind. They are not lost
    work and they are not finished work; they are work nobody is doing.
    """
    config = config or load_config()
    grace = int((config.get('reaper') or {}).get('stuck_after_lease_grace_seconds', 60))
    cutoff = _now() - timedelta(seconds=grace)
    stuck = session.scalars(select(Job).where(Job.status == 'running')).all()
    reaped = []
    for job in stuck:
        expires = _aware(job.lease_expires_at)
        if expires is None or expires > cutoff:
            continue
        reaped.append({'job_id': job.job_id, 'kind': job.kind, 'attempts': job.attempts,
                       'worker_id': job.worker_id,
                       'lease_expired_at': expires.isoformat()})
        fail(session, job, 'lease expired; the worker holding this job stopped reporting',
             config)
    return reaped


def to_dict(job: Job) -> dict:
    def stamp(value):
        value = _aware(value)
        return value.isoformat() if value else None
    return {'job_id': job.job_id, 'kind': job.kind, 'status': job.status,
            'idempotency_key': job.idempotency_key, 'attempts': job.attempts,
            'max_attempts': job.max_attempts, 'priority': job.priority,
            'payload': job.payload, 'result': job.result, 'error': job.error,
            'worker_id': job.worker_id, 'available_at': stamp(job.available_at),
            'lease_expires_at': stamp(job.lease_expires_at),
            'started_at': stamp(job.started_at), 'finished_at': stamp(job.finished_at),
            'created_at': stamp(job.created_at), 'updated_at': stamp(job.updated_at)}


def summary(session) -> dict:
    """Counts by status and kind, plus what is overdue — for `worker status`."""
    rows = session.execute(
        select(Job.status, Job.kind, func.count()).group_by(Job.status, Job.kind)).all()
    by_status: dict = {}
    by_kind: dict = {}
    for status, kind, count in rows:
        by_status[status] = by_status.get(status, 0) + count
        by_kind.setdefault(kind, {})[status] = count
    overdue = session.scalars(select(Job).where(Job.status == 'running')).all()
    expired = [job.job_id for job in overdue
               if _aware(job.lease_expires_at) and _aware(job.lease_expires_at) < _now()]
    return {'by_status': by_status, 'by_kind': by_kind,
            'claimable_now': session.scalar(
                select(func.count()).select_from(Job).where(_claimable(None))) or 0,
            'leases_expired': expired}


def recent(session, limit: int = 20, status: Optional[str] = None,
           kind: Optional[str] = None) -> list:
    statement = select(Job).order_by(Job.job_id.desc()).limit(limit)
    if status:
        statement = statement.where(Job.status == status)
    if kind:
        statement = statement.where(Job.kind == kind)
    return [to_dict(job) for job in session.scalars(statement).all()]
