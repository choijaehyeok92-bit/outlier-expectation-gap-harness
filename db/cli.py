"""`db` subcommands: upgrade, sync, status, rows.

Everything here is opt-in. `HARNESS_DATABASE_URL` names the database, or
`--sqlite` uses a local file for a look around. Nothing else in the platform
starts reading the database because these exist.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = Path(__file__).resolve().parent / 'alembic.ini'


def _print(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _url(args) -> str:
    """The configured database, or a message saying how to name one."""
    from .session import DatabaseNotConfigured, database_url
    try:
        return database_url(getattr(args, 'url', None),
                            allow_default=bool(getattr(args, 'sqlite', False)))
    except DatabaseNotConfigured as error:
        raise SystemExit(str(error)) from error


def _engine(args):
    from .session import engine_for
    return engine_for(_url(args), allow_default=bool(getattr(args, 'sqlite', False)))


def cmd_db_upgrade(args):
    from alembic import command
    from alembic.config import Config
    config = Config(str(ALEMBIC_INI))
    config.cmd_opts = None
    config.set_main_option('script_location', str(ALEMBIC_INI.parent / 'migrations'))
    config.attributes['configure_logger'] = False
    import os
    os.environ['HARNESS_DATABASE_URL'] = _url(args)
    command.upgrade(config, args.revision)
    print(f'{args.revision} applied to {_url(args).split("@")[-1]}', file=sys.stderr)
    cmd_db_status(args)



def _require_schema(engine, url: str) -> None:
    """Say what to do, rather than showing an UndefinedTable traceback."""
    from sqlalchemy import inspect
    if 'harness_run' not in set(inspect(engine).get_table_names()):
        raise SystemExit(f'{url.split("@")[-1]}: the schema is not applied. '
                         'Run `python harness.py db upgrade` first.')


def cmd_db_status(args):
    from .repository import status
    from .session import session_scope
    engine = _engine(args)
    _require_schema(engine, _url(args))
    with session_scope(engine) as session:
        _print({'url': _url(args).split('@')[-1], **status(session)})


def cmd_db_sync(args):
    """Load the file artifacts. Safe to run repeatedly; nothing is overwritten."""
    from . import sync as sync_module
    from .session import session_scope
    from packages.screening import runs_index, store as screen_store, warehouse
    from packages.research import store as deep_store

    kinds = {k.strip() for k in (args.kinds or
                                 'universe,runs,warehouse,screens,deep-dives,packs,'
                                 'monitoring').split(',')}
    report = {}
    engine = _engine(args)
    _require_schema(engine, _url(args))
    with session_scope(engine) as session:
        if 'universe' in kinds:
            try:
                from data_adapters import universe as universe_store
                payload = universe_store.load(args.universe)
            except Exception:
                payload = None
            report['universe'] = (dict(sync_module.sync_universe(session, payload))
                                  if payload else 'no universe file')
        if 'runs' in kinds:
            report['runs'] = dict(sync_module.sync_runs(session, runs_index.load_rows()))
        if 'packs' in kinds:
            counts = sync_module.Counts()
            entries, problems = _pack_entries(args)
            for entry in entries:
                part = sync_module.sync_pack(session, entry['pack'], ticker=entry['ticker'])
                for key in ('inserted', 'updated', 'skipped'):
                    counts.bump(key, part[key])
            report['packs'] = {**counts, 'packs_read': len(entries),
                               'unreadable': problems}
        if 'warehouse' in kinds:
            payload = warehouse.load(args.as_of)
            report['warehouse'] = (dict(sync_module.sync_warehouse(session, payload))
                                   if payload else 'no warehouse built')
        if 'screens' in kinds:
            records = [screen_store.load(row['screen_run_id']) for row in screen_store.list_runs()]
            report['screens'] = dict(sync_module.sync_screen_runs(
                session, [r for r in records if r]))
        if 'deep-dives' in kinds:
            reports = [deep_store.load(row['deep_dive_id']) for row in deep_store.list_reports()]
            report['deep_dives'] = dict(sync_module.sync_deep_dives(
                session, [r for r in reports if r]))
        if 'monitoring' in kinds:
            report['monitoring'] = _sync_monitoring(session, sync_module)
    _print(report)


def _sync_monitoring(session, sync_module) -> dict:
    """Watch items for every company with observations, and the observations themselves.

    Only companies someone has actually recorded an observation for. Building
    a watchlist for all twenty-five runs would fill the table with rows nobody
    is watching, which is the opposite of what a monitoring table is for.
    """
    from packages.monitoring import observations as observation_log
    from packages.monitoring import watchlist as watchlist_builder

    items, rows, unreadable = sync_module.Counts(), sync_module.Counts(), []
    for ticker in observation_log.tickers():
        try:
            watchlist = watchlist_builder.build(ticker)
        except ValueError as error:
            unreadable.append({'ticker': ticker, 'reason': str(error)})
        else:
            part = sync_module.sync_watchlist(session, watchlist)
            for key in ('inserted', 'updated', 'skipped'):
                items.bump(key, part[key])
        part = sync_module.sync_observations(session, observation_log.load(ticker))
        for key in ('inserted', 'updated', 'skipped'):
            rows.bump(key, part[key])
    return {'watch_items': dict(items), 'observations': dict(rows),
            'tickers': observation_log.tickers(), 'unreadable': unreadable}


def _read_pack(path):
    """A pack, or None with the reason. A corrupt file is reported, not hidden."""
    try:
        pack = json.loads(Path(path).read_text(encoding='utf-8'))
    except ValueError as error:
        return None, f'{Path(path).name}: unreadable JSON ({error})'
    if not pack.get('facts'):
        return None, f'{Path(path).name}: no facts'
    return pack, None


def _pack_entries(args):
    """Stage 0 packs from a directory, or from the runs that already hold one.

    Returns (entries, problems). One unreadable artifact must not cost the sync
    every other one, and it must not disappear either.
    """
    entries, problems = [], []
    if args.packs:
        for path in sorted(Path(args.packs).glob('*.json')):
            pack, problem = _read_pack(path)
            if problem:
                problems.append(problem)
                continue
            entries.append({'ticker': (pack.get('ticker') or path.stem).upper(), 'pack': pack})
        return entries, problems

    from packages.screening import runs_index
    for run_id in runs_index.run_ids():
        path = ROOT / 'runs' / run_id / 'sources' / 'financials' / 'normalized_financials.json'
        if not path.exists():
            continue
        pack, problem = _read_pack(path)
        if problem:
            problems.append(f'{run_id}/{problem}')
            continue
        entries.append({'ticker': (pack.get('ticker') or run_id).upper(), 'pack': pack})
    return entries, problems


def cmd_db_rows(args):
    """What a screen would read out of the database."""
    from .repository import merged_rows
    from .session import session_scope
    fx = {}
    for pair in args.fx or []:
        code, _, rate = pair.partition('=')
        fx[code.strip().upper()] = {'per_usd': float(rate), 'source': 'operator (--fx)'}
    engine = _engine(args)
    _require_schema(engine, _url(args))
    with session_scope(engine) as session:
        rows = merged_rows(session, args.as_of, fx)
    _print({'rows': len(rows),
            'with_harness_run': sum(1 for r in rows if r.get('has_harness_run')),
            'warehouse_only': sum(1 for r in rows if r.get('has_warehouse_metrics')
                                  and not r.get('has_harness_run')),
            'sample': [{k: r.get(k) for k in ('ticker', 'core_score', 'revenue_ttm',
                                              'gross_margin', 'has_harness_run')}
                       for r in rows[:args.limit]]})


def cmd_db_company(args):
    from .repository import company
    from .session import session_scope
    engine = _engine(args)
    _require_schema(engine, _url(args))
    with session_scope(engine) as session:
        _print(company(session, args.ticker))


def register(sub):
    parser = sub.add_parser('db', help='optional PostgreSQL index over the run artifacts')
    db_sub = parser.add_subparsers(dest='db_cmd', required=True)

    def shared(p):
        p.add_argument('--url', help='database URL; else $HARNESS_DATABASE_URL')
        p.add_argument('--sqlite', action='store_true',
                       help='use the local SQLite file instead of a configured server')
        return p

    p = shared(db_sub.add_parser('upgrade', help='apply migrations'))
    p.add_argument('revision', nargs='?', default='head')
    p.set_defaults(func=cmd_db_upgrade)

    p = shared(db_sub.add_parser('status', help='row counts and recent syncs'))
    p.set_defaults(func=cmd_db_status)

    p = shared(db_sub.add_parser('sync', help='load the file artifacts; safe to repeat'))
    p.add_argument('--kinds',
                   help='universe,runs,packs,warehouse,screens,deep-dives,monitoring')
    p.add_argument('--as-of', help='warehouse date to load')
    p.add_argument('--packs', help='directory of Stage 0 packs')
    p.add_argument('--universe', help='universe file path')
    p.set_defaults(func=cmd_db_sync)

    p = shared(db_sub.add_parser('rows', help='what a screen would read from the database'))
    p.add_argument('--as-of')
    p.add_argument('--fx', action='append', metavar='CODE=PER_USD')
    p.add_argument('--limit', type=int, default=10)
    p.set_defaults(func=cmd_db_rows)

    p = shared(db_sub.add_parser('company', help='everything the database holds on one company'))
    p.add_argument('ticker')
    p.set_defaults(func=cmd_db_company)
    return sub
