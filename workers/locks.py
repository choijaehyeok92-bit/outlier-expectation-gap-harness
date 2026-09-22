"""Resources a running job holds, so a second job cannot touch the same run.

The queue stops two workers claiming the same row. That is not the same as
stopping two *different* rows from writing the same `runs/<ID>/`, and the
difference is not theoretical: `harness_full {run_ids: [MSFT]}` rewrites
`runs/MSFT/reports/*.json` and `aggregate.json` while `deep_dive {run_id:
MSFT}` reads them to copy a `harness_snapshot`, and `harness_core.dump_json`
is a plain `write_text`. The reader can see half a file, and what it read
becomes a fact in an immutable record.

So a job declares what it will touch before it is claimed, and a job whose
resources are already held is passed over — not failed, not queued behind a
timer, simply left for the next pass.

**The guarantee is the unique constraint, not this module's check.** Two
workers can both find a resource free; only one `INSERT` survives
`uq_job_lock_resource`, and the loser moves to the next candidate. The check
exists to avoid doing that dance for every job, not to be trusted on its own.

A resource of `*` is the whole namespace, for a batch whose targets are not
known until it runs its own selection. That is the one case the unique
constraint cannot decide by itself — `(run, *)` and `(run, MSFT)` are
different rows — so the claim transaction takes a PostgreSQL advisory lock
while it looks. SQLite has a single writer and needs nothing.
"""
from typing import Optional

from sqlalchemy import and_, delete, func, or_, select

from db.models import Job, JobLock

WILDCARD = '*'
# A constant, because the advisory lock serialises *claiming*, not a namespace.
# Two workers looking at the lock table at the same time is the whole race.
CLAIM_ADVISORY_KEY = 0x4A4F424C          # 'JOBL'


class LockUnavailable(RuntimeError):
    """Another running job already holds one of these resources."""


def policy(config: dict) -> dict:
    return config.get('locks') or {}


def enabled(config: dict) -> bool:
    return bool(policy(config).get('enabled', True))


def keys_for(kind: str, payload: Optional[dict], config: dict) -> list:
    """The `(namespace, resource)` pairs this job needs, from config not code.

    A rule that cannot find its field falls back to the wildcard, which is the
    safe direction: claiming too much delays a job, claiming too little
    corrupts a run.
    """
    rule = (policy(config).get('by_kind') or {}).get(kind)
    if rule is None:
        return []
    namespace = rule['namespace']
    payload = payload or {}
    source = rule.get('from', 'all')

    if source == 'all':
        return [(namespace, WILDCARD)]
    if source == 'field':
        value = payload.get(rule['field'])
        return [(namespace, str(value).upper() if value else WILDCARD)]
    if source == 'list_field':
        values = payload.get(rule['field'])
        if not values:
            return [(namespace, WILDCARD)]
        if isinstance(values, str):
            values = [values]
        return sorted({(namespace, str(value).upper()) for value in values})
    raise ValueError(f'config/workers.json locks.by_kind.{kind}.from is {source!r}, '
                     "which is not one of 'all', 'field', 'list_field'")


def _conflict_clause(keys: list):
    """Rows that would collide: same resource, or either side a wildcard."""
    clauses = []
    for namespace, resource in keys:
        if resource == WILDCARD:
            clauses.append(JobLock.namespace == namespace)
        else:
            clauses.append(and_(JobLock.namespace == namespace,
                                or_(JobLock.resource == resource,
                                    JobLock.resource == WILDCARD)))
    return or_(*clauses) if clauses else None


def serialize_claim(session) -> None:
    """Hold the claim critical section on PostgreSQL; a no-op on SQLite.

    `pg_advisory_xact_lock` is released by the transaction ending, so there is
    nothing to clean up and nothing to leak if a worker dies mid-claim.
    """
    if session.get_bind().dialect.name == 'postgresql':
        session.execute(select(func.pg_advisory_xact_lock(CLAIM_ADVISORY_KEY)))


def conflicts(session, keys: list, exclude_job_id: Optional[int] = None) -> list:
    """Who already holds any of these, as `{namespace, resource, job_id}`."""
    clause = _conflict_clause(keys)
    if clause is None:
        return []
    statement = select(JobLock).where(clause)
    if exclude_job_id is not None:
        statement = statement.where(JobLock.job_id != exclude_job_id)
    return [{'namespace': row.namespace, 'resource': row.resource, 'job_id': row.job_id}
            for row in session.scalars(statement).all()]


def acquire(session, job_id: int, keys: list) -> list:
    """Take every key or none. Raises `LockUnavailable` if the database refuses.

    The caller is expected to have checked `conflicts` first; this is what
    happens when that check raced somebody else.
    """
    from sqlalchemy.exc import IntegrityError
    if not keys:
        return []
    held = conflicts(session, keys, exclude_job_id=job_id)
    if held:
        raise LockUnavailable(
            'held by ' + ', '.join(f"job {row['job_id']} ({row['namespace']}:{row['resource']})"
                                   for row in held))
    try:
        with session.begin_nested():
            for namespace, resource in keys:
                session.add(JobLock(namespace=namespace, resource=resource, job_id=job_id))
            session.flush()
    except IntegrityError as error:
        raise LockUnavailable(f'another worker took one of these first: {error.orig}') from error
    return list(keys)


def release(session, job_id: int) -> int:
    """Drop everything this job held. Safe to call when it held nothing."""
    result = session.execute(delete(JobLock).where(JobLock.job_id == job_id))
    return int(result.rowcount or 0)


def release_orphans(session) -> list:
    """Locks whose job is no longer running. A held resource needs a holder."""
    rows = session.execute(
        select(JobLock, Job).outerjoin(Job, Job.job_id == JobLock.job_id)).all()
    orphans = [lock for lock, job in rows if job is None or job.status != 'running']
    for lock in orphans:
        session.delete(lock)
    return [{'namespace': lock.namespace, 'resource': lock.resource, 'job_id': lock.job_id}
            for lock in orphans]


def held(session) -> list:
    """Every lock currently taken, with the job holding it."""
    rows = session.execute(
        select(JobLock, Job).outerjoin(Job, Job.job_id == JobLock.job_id)
        .order_by(JobLock.namespace, JobLock.resource)).all()
    return [{'namespace': lock.namespace, 'resource': lock.resource, 'job_id': lock.job_id,
             'kind': job.kind if job else None,
             'worker_id': job.worker_id if job else None,
             'job_status': job.status if job else 'missing',
             'acquired_at': lock.acquired_at.isoformat() if lock.acquired_at else None}
            for lock, job in rows]
