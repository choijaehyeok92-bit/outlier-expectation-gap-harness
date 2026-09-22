"""`harness.py worker …` — enqueue work, run a worker, read the queue.

Nothing here decides anything. `enqueue` writes a row, `run` works the rows,
and the rest is reading the table back. Every default leans toward doing
nothing surprising: `run` drains what is queued and exits, a daemon is
`--follow`, and the provider a job may use comes from the config rather than
from the command line.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _print(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _engine(args):
    from db.session import DatabaseNotConfigured, engine_for
    try:
        return engine_for(getattr(args, 'url', None),
                          allow_default=bool(getattr(args, 'sqlite', False)))
    except DatabaseNotConfigured as error:
        raise SystemExit(str(error)) from error


def _require_schema(engine):
    from sqlalchemy import inspect
    if 'job' not in set(inspect(engine).get_table_names()):
        raise SystemExit('no job table; run `python harness.py db upgrade` first.')


def _payload(args) -> dict:
    payload = {}
    if getattr(args, 'payload', None):
        text = args.payload
        if text.strip().startswith('@'):
            text = Path(text.strip()[1:]).read_text(encoding='utf-8')
        try:
            payload = json.loads(text)
        except ValueError as error:
            raise SystemExit(f'--payload must be JSON (or @file.json): {error}') from error
        if not isinstance(payload, dict):
            raise SystemExit('--payload must be a JSON object')
    for pair in getattr(args, 'set', None) or []:
        if '=' not in pair:
            raise SystemExit(f'--set expects KEY=VALUE, got {pair!r}')
        key, value = pair.split('=', 1)
        try:
            payload[key] = json.loads(value)
        except ValueError:
            payload[key] = value
    return payload


def cmd_worker_enqueue(args):
    from db.session import session_scope
    from workers import handlers, queue
    engine = _engine(args)
    _require_schema(engine)
    config = queue.load_config()
    payload = _payload(args)
    problem = handlers.payload_is_safe(payload)
    if problem:
        raise SystemExit(problem)
    try:
        with session_scope(engine) as session:
            job = queue.enqueue(session, args.kind, payload, config,
                                idempotency_key=args.idempotency_key,
                                priority=args.priority, max_attempts=args.max_attempts)
            row = queue.to_dict(job)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    _print(row)


def cmd_worker_run(args):
    """Work the queue. Drains and exits unless `--follow`."""
    from workers import runner
    engine = _engine(args)
    _require_schema(engine)
    kinds = [k.strip() for k in args.kinds.split(',')] if args.kinds else None
    report = runner.run(engine, kinds=kinds, once=not args.follow, max_jobs=args.max_jobs,
                        max_seconds=args.max_seconds, poll_interval=args.poll_interval)
    _print(report.to_dict() if args.full else
           {'worker_id': report.worker_id, 'kinds': report.kinds,
            'summary': report.summary, 'stopped_by': report.stopped_by,
            'processed': [{k: row.get(k) for k in ('job_id', 'kind', 'status', 'attempts',
                                                   'duration_seconds', 'error')}
                          for row in report.processed],
            'reaped': report.reaped})


def cmd_worker_status(args):
    from db.session import session_scope
    from workers import handlers, queue
    engine = _engine(args)
    _require_schema(engine)
    config = queue.load_config()
    with session_scope(engine) as session:
        payload = queue.summary(session)
    _print({**payload, 'kinds': handlers.declared_kinds(config),
            'providers_allowed': config['providers']['allowed'],
            'transport': config['transport']['kind']})


def cmd_worker_jobs(args):
    from db.session import session_scope
    from workers import queue
    engine = _engine(args)
    _require_schema(engine)
    with session_scope(engine) as session:
        if args.job_id:
            from db.models import Job
            job = session.get(Job, args.job_id)
            if job is None:
                raise SystemExit(f'no job {args.job_id}')
            _print(queue.to_dict(job))
            return
        rows = queue.recent(session, args.limit, args.status, args.kind)
    _print(rows if args.full else
           [{k: row[k] for k in ('job_id', 'kind', 'status', 'attempts', 'max_attempts',
                                 'worker_id', 'error', 'finished_at')} for row in rows])


def cmd_worker_retry(args):
    from db.session import session_scope
    from workers import queue
    engine = _engine(args)
    _require_schema(engine)
    with session_scope(engine) as session:
        job = queue.retry(session, args.job_id)
        if job is None:
            raise SystemExit(f'no job {args.job_id}')
        row = queue.to_dict(job)
    if row['status'] != 'queued':
        print(f"job {row['job_id']} is {row['status']}; only a failed or cancelled job "
              'can be requeued', file=sys.stderr)
    _print(row)


def cmd_worker_cancel(args):
    from db.session import session_scope
    from workers import queue
    engine = _engine(args)
    _require_schema(engine)
    with session_scope(engine) as session:
        job = queue.cancel(session, args.job_id)
        if job is None:
            raise SystemExit(f'no job {args.job_id}')
        _print(queue.to_dict(job))


def _moment(args):
    from datetime import datetime, timezone
    if not getattr(args, 'now', None):
        return None
    try:
        parsed = datetime.fromisoformat(args.now)
    except ValueError:
        raise SystemExit(f'--now must be an ISO timestamp, got {args.now!r}') from None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def cmd_worker_schedule(args):
    """Queue whatever is due. Safe to call as often as you like.

    This is the one line a crontab needs; the cadence lives in
    `config/workers.json`. Running it twice for the same occurrence queues
    nothing the second time, because the idempotency key names the occurrence
    rather than the moment of the call.
    """
    from workers import queue, schedule
    config = queue.load_config()
    only = [s.strip() for s in args.only.split(',')] if args.only else None

    problems = schedule.validate(config)
    if problems:
        raise SystemExit('config/workers.json schedules are not usable:\n  '
                         + '\n  '.join(problems))
    if args.dry_run:
        rows = schedule.plan(config, _moment(args))
        _print({'now': args.now or 'now', 'dry_run': True,
                'schedules': [row for row in rows
                              if not only or row['schedule_id'] in set(only)]})
        return

    from db.session import session_scope
    engine = _engine(args)
    _require_schema(engine)
    try:
        with session_scope(engine) as session:
            result = schedule.run(session, config, _moment(args), only)
    except schedule.CronError as error:
        raise SystemExit(str(error)) from error
    _print(result)


def cmd_worker_schedules(args):
    """The declared schedules, and whether they are readable."""
    from workers import queue, schedule
    config = queue.load_config()
    policy = schedule.settings(config)
    _print({'timezone': policy.get('timezone'), 'catch_up': policy.get('catch_up'),
            'lookback_hours': policy.get('lookback_hours'),
            'problems': schedule.validate(config),
            'entries': policy.get('entries') or [],
            'never_scheduled': policy.get('never_scheduled')})


def cmd_worker_locks(args):
    """Which resources are held, and what is waiting on them."""
    from db.session import session_scope
    from workers import locks, queue
    engine = _engine(args)
    _require_schema(engine)
    config = queue.load_config()
    with session_scope(engine) as session:
        _print({'held': locks.held(session),
                'blocked': queue.blocked(session, None, config),
                'policy': {'enabled': locks.enabled(config),
                           'by_kind': {k: v['namespace']
                                       for k, v in (config['locks']['by_kind']).items()}}})


def cmd_worker_reap(args):
    from db.session import session_scope
    from workers import queue
    engine = _engine(args)
    _require_schema(engine)
    with session_scope(engine) as session:
        _print({'reaped': queue.reap(session)})


def register(sub):
    parser = sub.add_parser('worker', help='queue and run background work from the job table')
    worker_sub = parser.add_subparsers(dest='worker_cmd', required=True)

    def shared(p):
        p.add_argument('--url', help='database URL; else $HARNESS_DATABASE_URL')
        p.add_argument('--sqlite', action='store_true',
                       help='use the local SQLite file instead of a configured server')
        return p

    p = shared(worker_sub.add_parser('enqueue', help='queue one job'))
    p.add_argument('kind', help='a kind declared in config/workers.json')
    p.add_argument('--payload', help='JSON object, or @path/to/file.json')
    p.add_argument('--set', action='append', metavar='KEY=VALUE',
                   help='payload field; repeatable. Values are parsed as JSON when possible')
    p.add_argument('--idempotency-key', help='else the content hash of (kind, payload)')
    p.add_argument('--priority', type=int, default=100, help='lower runs first')
    p.add_argument('--max-attempts', type=int)
    p.set_defaults(func=cmd_worker_enqueue)

    p = shared(worker_sub.add_parser('run', help='work the queue; drains and exits by default'))
    p.add_argument('--kinds', help='comma-separated; else every kind')
    p.add_argument('--follow', action='store_true', help='keep polling instead of exiting')
    p.add_argument('--max-jobs', type=int)
    p.add_argument('--max-seconds', type=float)
    p.add_argument('--poll-interval', type=float)
    p.add_argument('--full', action='store_true')
    p.set_defaults(func=cmd_worker_run)

    p = shared(worker_sub.add_parser('status', help='queue depth, by status and kind'))
    p.set_defaults(func=cmd_worker_status)

    p = shared(worker_sub.add_parser('jobs', help='recent jobs, or one by id'))
    p.add_argument('job_id', nargs='?', type=int)
    p.add_argument('--status')
    p.add_argument('--kind')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--full', action='store_true')
    p.set_defaults(func=cmd_worker_jobs)

    p = shared(worker_sub.add_parser('retry', help='requeue a failed or cancelled job'))
    p.add_argument('job_id', type=int)
    p.set_defaults(func=cmd_worker_retry)

    p = shared(worker_sub.add_parser('cancel', help='cancel a job that has not finished'))
    p.add_argument('job_id', type=int)
    p.set_defaults(func=cmd_worker_cancel)

    p = shared(worker_sub.add_parser(
        'schedule', help='queue whatever is due; the one line a crontab needs'))
    p.add_argument('--dry-run', action='store_true', help='show what would be queued')
    p.add_argument('--only', help='comma-separated schedule ids')
    p.add_argument('--now', help='evaluate as if it were this ISO time (UTC)')
    p.set_defaults(func=cmd_worker_schedule)

    p = shared(worker_sub.add_parser('schedules', help='the declared recurring work'))
    p.set_defaults(func=cmd_worker_schedules)

    p = shared(worker_sub.add_parser(
        'locks', help='resources held by running jobs, and what is waiting on them'))
    p.set_defaults(func=cmd_worker_locks)

    p = shared(worker_sub.add_parser('reap', help='return jobs with expired leases to the queue'))
    p.set_defaults(func=cmd_worker_reap)
    return parser
