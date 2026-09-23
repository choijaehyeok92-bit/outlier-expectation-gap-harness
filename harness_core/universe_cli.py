"""`harness.py universe ...` commands. Thin wiring over universe/universe_store (and the runner)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import universe as U
from . import universe_runner
from .universe_store import RunReader, Store, load_policy, sync_ticker_from_run, utcnow


def _runtime():
    from . import runtime
    return runtime


def _store():
    h = _runtime()
    return Store(h.ROOT), RunReader(h)


def _tickers(store, names):
    universe = store.load()
    out = []
    for raw in names:
        ticker, _, reason = U.normalize_ticker(raw, store.policy['import'])
        if reason or ticker not in universe['tickers']:
            raise SystemExit(f'{raw}: not in the universe' + (f' ({reason})' if reason else ''))
        out.append(ticker)
    return out


def _require_as_of(value):
    if not value or not U.valid_as_of(value):
        raise SystemExit(f'--as-of must be a calendar date YYYY-MM-DD (got {value!r})')
    return value


# ------------------------------------------------------------------ import / add / remove

def cmd_import(args, source=None):
    store, reader = _store()
    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f'{path}: not found')
    as_of = _require_as_of(args.as_of)
    fmt = args.format or path.suffix.lstrip('.') or 'txt'
    policy = store.policy['import']
    try:
        entries = U.parse_import(path.read_text(encoding='utf-8-sig'), fmt, policy)
    except U.ImportError_ as error:
        raise SystemExit(f'{path}: {error}')
    accepted, rejected, duplicates = U.normalize_entries(entries, policy, [args.screen] if args.screen else [])
    source = source or args.source or policy['default_source']
    with store.transaction() as universe:
        _, report = U.merge_import(universe, accepted, as_of, source, utcnow(), reader.run_as_of,
                                   getattr(args, 'run_id', None))
    _print_import(path, accepted, rejected, duplicates, report)
    if not accepted:
        raise SystemExit(1)


def cmd_import_screen(args):
    return cmd_import(args, source=_store()[0].policy['import']['screenshot_source'])


def cmd_add(args):
    store, reader = _store()
    as_of = _require_as_of(args.as_of)
    policy = store.policy['import']
    entries = [{'raw': t, 'screens': []} for t in args.tickers]
    accepted, rejected, duplicates = U.normalize_entries(entries, policy, [args.screen] if args.screen else [])
    if args.run_id and len(accepted) != 1:
        raise SystemExit('--run-id applies to exactly one ticker')
    with store.transaction() as universe:
        _, report = U.merge_import(universe, accepted, as_of, args.source or 'manual', utcnow(),
                                   reader.run_as_of, args.run_id)
    _print_import('command line', accepted, rejected, duplicates, report)
    if not accepted:
        raise SystemExit(1)


def _print_import(label, accepted, rejected, duplicates, report):
    print(f'{label}: {len(accepted)} ticker(s) accepted, {len(rejected)} rejected, '
          f'{len(set(duplicates))} duplicate(s) folded')
    for key, title in (('added', 'added'), ('merged', 'merged (screens/sources updated)'),
                       ('new_snapshot', 'new as-of snapshot queued (previous run kept in history)'),
                       ('funds', 'ETF/fund — imported but not run by the batch runner')):
        if report[key]:
            print(f'  {title}: {", ".join(report[key])}')
    for item in rejected:
        where = f" (line {item['line']})" if item.get('line') else ''
        print(f"  rejected{where}: {item['reason']}")
    for item in report['conflicts']:
        print(f"  conflict {item['ticker']}: {item['reason']}")


def cmd_remove(args):
    store, _ = _store()
    tickers = _tickers(store, args.tickers)
    with store.transaction() as universe:
        for ticker in tickers:
            if store.lock_held(ticker):
                raise SystemExit(f'{ticker}: a runner holds this ticker; wait for it to finish')
            row = universe['tickers'].pop(ticker)
            store.append_history(ticker, {'ticker': ticker, 'recorded_at': utcnow(), 'event': 'removed',
                                          'snapshot': U.snapshot_summary(row)})
    print(f"removed {', '.join(tickers)} from the universe index (runs/ left untouched)")


def cmd_reset(args):
    store, _ = _store()
    tickers = _tickers(store, args.tickers)
    for ticker in tickers:
        if store.lock_held(ticker):
            raise SystemExit(f'{ticker}: a runner holds this ticker; wait for it to finish')
        store.update_row(ticker, lambda row: row.update(run_status='QUEUED', blocked_reason=None, awaiting=[],
                                                        last_error=None, attempts=0))
    print(f"reset {', '.join(tickers)} to QUEUED; the next sync or run re-derives the stage from runs/")


# ------------------------------------------------------------------ sync / show / status / export

def refresh(store, reader, tickers=None):
    universe = store.load()
    names = tickers or list(universe['tickers'])
    rows = []
    for ticker in names:
        row, _, _ = sync_ticker_from_run(store, reader, ticker)
        rows.append(row)
    return rows


def cmd_sync(args):
    store, reader = _store()
    tickers = _tickers(store, args.tickers) if args.tickers else None
    rows = refresh(store, reader, tickers)
    print(f'synced {len(rows)} row(s) from runs/')
    _table(rows, store)


def cmd_show(args):
    store, reader = _store()
    ticker = _tickers(store, [args.ticker])[0]
    row, art, inspection = sync_ticker_from_run(store, reader, ticker) if not args.no_sync else \
        (store.load()['tickers'][ticker], None, None)
    payload = {'row': row, 'display_status': U.display_status(row), 'history_entries': len(store.history(ticker))}
    if inspection:
        payload['planner'] = inspection.get('plan')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def status_filters(args):
    return {k: getattr(args, k, None) for k in ('archetype', 'state', 'mechanical_state', 'veto', 'status', 'stage',
                                                   'screen', 'min_score', 'min_fit', 'max_price_base', 'min_ex_ev')}


def cmd_status(args):
    store, reader = _store()
    rows = list(store.load()['tickers'].values()) if args.no_sync else refresh(store, reader)
    h = _runtime()
    rows = U.sort_rows(U.filter_rows(rows, status_filters(args)), args.sort, args.desc, h.STATE_POLICY)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    _counts(store.load())
    _table(rows, store)


def _counts(universe):
    rows = list(universe['tickers'].values())
    counts = {}
    for row in rows:
        counts[U.display_status(row)] = counts.get(U.display_status(row), 0) + 1
    print(f"{len(rows)} ticker(s): " + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))


COLUMNS = [('Ticker', lambda r: r['ticker']), ('Status', U.display_status), ('Stage', lambda r: r.get('stage')),
           ('Score', lambda r: U.fmt(r.get('score'))), ('Ex-EV', lambda r: U.fmt(r.get('score_ex_valuation'))),
           ('Archetype', lambda r: r.get('archetype')), ('Fit', lambda r: U.fmt(r.get('archetype_fit'))),
           ('P/Base', lambda r: U.fmt(r.get('price_to_base'), 4)), ('Veto', lambda r: r.get('hard_veto_status')),
           ('Mechanical', lambda r: r.get('mechanical_pre_ic_state')), ('IC', lambda r: r.get('ic_state')),
           ('Position', lambda r: (r.get('position_range') or '')[:24]), ('Pacing', lambda r: U.fmt(r.get('macro_pacing'))),
           ('As-of', lambda r: r.get('as_of_date'))]


def _table(rows, store):
    if not rows:
        print('(no rows)')
        return
    cells = [[str(fn(r) or '') for _, fn in COLUMNS] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, (h, _) in enumerate(COLUMNS)]
    print('  '.join(h.ljust(w) for (h, _), w in zip(COLUMNS, widths)))
    for c in cells:
        print('  '.join(v.ljust(w) for v, w in zip(c, widths)))
    notes = [(r['ticker'], r.get('blocked_reason') or (r.get('last_error') or {}).get('summary'))
             for r in rows if r.get('blocked_reason') or r.get('last_error')]
    for ticker, note in notes:
        print(f'  {ticker}: {note}')


def cmd_export(args):
    store, reader = _store()
    rows = store.ordered(store.load()) if args.no_sync else refresh(store, reader)
    rows = sorted(rows, key=lambda r: (r.get('queue_seq') or 0, r['ticker']))
    dest = Path(args.path)
    fmt = (args.format or dest.suffix.lstrip('.')).lower()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if fmt == 'csv':
        dest.write_text(U.to_csv(rows), encoding='utf-8')
    elif fmt == 'json':
        dest.write_text(json.dumps({'exported_at': utcnow(), 'authority': 'runs/<RUN_ID>/final_verdict.json',
                                    'rows': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        raise SystemExit('export format must be csv or json')
    print(f'{dest}: {len(rows)} row(s) ({fmt})')


def cmd_validate(args):
    store, reader = _store()
    h = _runtime()
    tickers = _tickers(store, args.tickers) if args.tickers else list(store.load()['tickers'])
    findings = []
    for ticker in tickers:
        row = store.load()['tickers'][ticker]
        art = reader.artifacts(row.get('run_id') or ticker)
        findings += U.validate_row(row, art, h.STATE_POLICY)
    errors = [m for lvl, m in findings if lvl == 'ERROR']
    warnings = [m for lvl, m in findings if lvl == 'WARNING']
    for lvl, message in findings:
        if lvl != 'INFO' or args.verbose:
            print(f'{lvl}: {message}')
    print(f'universe validate: {len(tickers)} ticker(s), {len(errors)} error(s), {len(warnings)} warning(s)')
    sys.exit(1 if errors else 0)


def cmd_history(args):
    store, _ = _store()
    ticker = _tickers(store, [args.ticker])[0]
    entries = store.history(ticker)
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return
    if not entries:
        print(f'{ticker}: no history yet (history is written when a sync records decision fields)')
        return
    for e in entries:
        if e.get('event') == 'removed':
            print(f"{e['recorded_at']}  removed from universe")
            continue
        s = e['snapshot']
        digits = lambda k: 4 if k == 'price_to_base' else 2
        changes = ', '.join(f'{k}: {U.fmt(v[0], digits(k)) or "∅"} → {U.fmt(v[1], digits(k)) or "∅"}'
                            for k, v in e['changes'].items()
                            if k not in ('as_of_date', 'run_id'))
        print(f"{e['recorded_at']}  as_of {s.get('as_of_date')}  run {e.get('run_id')}  "
              f"[{e.get('verdict_source')}]  {changes or 'no field change'}")


def cmd_snapshot(args):
    store, _ = _store()
    print(store.write_snapshot(args.label))


# ------------------------------------------------------------------ argparse

def _add_filters(p):
    p.add_argument('--archetype'); p.add_argument('--state', help='final IC state, e.g. STARTER')
    p.add_argument('--mechanical-state'); p.add_argument('--veto', help='CLEARED / UNRESOLVED / ...')
    p.add_argument('--status', help='QUEUED/RUNNING/FAILED/BLOCKED/COMPLETE/EARLY_EXIT')
    p.add_argument('--stage'); p.add_argument('--screen')
    p.add_argument('--min-score', type=float); p.add_argument('--min-ex-ev', type=float)
    p.add_argument('--min-fit', type=float); p.add_argument('--max-price-base', type=float)
    p.add_argument('--sort', choices=sorted(U.SORT_KEYS), default='queue',
                   help='descriptive ordering only; there is no merit ranking')
    p.add_argument('--desc', action='store_true')


def register(sub):
    top = sub.add_parser('universe', help='screen-driven multi-ticker index, batch runner and dashboards')
    us = top.add_subparsers(dest='universe_cmd', required=True)
    for name, func, text in (('import', cmd_import, 'import a TXT/CSV/JSON ticker list (StockAnalysis screener export)'),
                             ('import-screen', cmd_import_screen, 'import a vision-extracted screenshot ticker list')):
        p = us.add_parser(name, help=text)
        p.add_argument('file'); p.add_argument('--as-of', required=True)
        p.add_argument('--screen', help='screen label for rows that do not carry one (provenance only)')
        p.add_argument('--source'); p.add_argument('--format', choices=['txt', 'csv', 'tsv', 'json'])
        p.set_defaults(func=func)
    p = us.add_parser('add', help='add tickers by hand'); p.add_argument('tickers', nargs='+')
    p.add_argument('--as-of', required=True); p.add_argument('--screen'); p.add_argument('--source')
    p.add_argument('--run-id', help='attach an existing run directory (single ticker)'); p.set_defaults(func=cmd_add)
    p = us.add_parser('remove', help='drop tickers from the index (runs/ untouched)'); p.add_argument('tickers', nargs='+'); p.set_defaults(func=cmd_remove)
    p = us.add_parser('reset', help='clear a row\'s lifecycle status back to QUEUED'); p.add_argument('tickers', nargs='+'); p.set_defaults(func=cmd_reset)
    p = us.add_parser('sync', help='refresh rows from runs/ (read-only on runs)'); p.add_argument('tickers', nargs='*'); p.set_defaults(func=cmd_sync)
    p = us.add_parser('show', help='one row with provenance'); p.add_argument('ticker'); p.add_argument('--no-sync', action='store_true'); p.set_defaults(func=cmd_show)
    p = us.add_parser('status', help='filterable descriptive table'); _add_filters(p)
    p.add_argument('--json', action='store_true'); p.add_argument('--no-sync', action='store_true'); p.set_defaults(func=cmd_status)
    p = us.add_parser('export', help='write universe.csv / universe.json'); p.add_argument('path')
    p.add_argument('--format', choices=['csv', 'json']); p.add_argument('--no-sync', action='store_true'); p.set_defaults(func=cmd_export)
    p = us.add_parser('validate', help='check universe rows against run artifacts and gate invariants')
    p.add_argument('tickers', nargs='*'); p.add_argument('--verbose', action='store_true'); p.set_defaults(func=cmd_validate)
    p = us.add_parser('history', help='decision-field changes across snapshots'); p.add_argument('ticker')
    p.add_argument('--json', action='store_true'); p.set_defaults(func=cmd_history)
    p = us.add_parser('snapshot', help='copy the index to universe/snapshots/'); p.add_argument('--label'); p.set_defaults(func=cmd_snapshot)
    universe_runner.register(us, load_policy(_runtime().ROOT)['statuses']['stages'])
    return top
