"""`universe report`: tiered deep reports for completed runs (and, below, universe dashboards).

A run whose freeze matches the current harness gets the ordinary `report` first
(fresh deterministic verdict + easy_report.md). A run frozen under another
harness, or any run with --existing-runs, is explained from its recorded
artifacts only: no fetch, no agent, no recomputation.
"""
from __future__ import annotations

import argparse
import contextlib
import io

from . import universe as U
from .report_builder import write_deep_report
from .universe_store import RunReader, Store, sync_ticker_from_run


def _runtime():
    from . import runtime
    return runtime


def generate_reports(store, reader, tickers=None, existing_runs=False, force=False):
    h = reader.h
    rows = Store.ordered(store.load())
    results = []
    for row in rows:
        ticker = row['ticker']
        if tickers and ticker not in tickers:
            continue
        row, art, _ = sync_ticker_from_run(store, reader, ticker)
        run_id = row.get('run_id') or ticker
        if row.get('run_status') != 'COMPLETE':
            results.append({'ticker': ticker, 'status': 'SKIPPED', 'reason': f"run_status {row.get('run_status')}"})
            continue
        current = art['freeze'].get('config_current') and art['freeze'].get('inputs_current')
        mode = 'fresh' if current and not existing_runs else 'existing-run'
        try:
            if mode == 'fresh':
                with contextlib.redirect_stdout(io.StringIO()):
                    h.cmd_report(argparse.Namespace(ticker=run_id))
            result = write_deep_report(h, run_id, force=force, reader=reader)
            result.update(ticker=ticker, mode=mode)
        except (SystemExit, ValueError) as error:
            result = {'ticker': ticker, 'run_id': run_id, 'status': 'ERROR', 'mode': mode, 'reason': str(error)}
        results.append(result)
        sync_ticker_from_run(store, reader, ticker)
        if result['status'] == 'ERROR':
            store.update_row(ticker, lambda r: r.update(report_status='ERROR'))
    return results


def cmd_universe_report(args):
    h = _runtime()
    store, reader = Store(h.ROOT), RunReader(h)
    tickers = set()
    for raw in args.tickers or ():
        ticker, _, reason = U.normalize_ticker(raw, store.policy['import'])
        if reason or ticker not in store.load()['tickers']:
            raise SystemExit(f'{raw}: not in the universe')
        tickers.add(ticker)
    results = generate_reports(store, reader, tickers or None, args.existing_runs, args.force)
    for r in results:
        detail = ', '.join(r.get('paths') or []) or r.get('reason') or ''
        print(f"  {r['ticker']:<8} {r['status']:<9} {r.get('tier') or '':<8} {r.get('mode') or '':<13} {detail}"[:220])
    made = sum(1 for r in results if str(r['status']).startswith('COMPLETE'))
    print(f'universe report: {made} deep report(s) written, '
          f"{sum(1 for r in results if r['status'] == 'NONE')} not required by tier, "
          f"{sum(1 for r in results if r['status'] == 'SKIPPED')} not complete, "
          f"{sum(1 for r in results if r['status'] == 'ERROR')} error(s)")
    if any(r['status'] == 'ERROR' for r in results):
        raise SystemExit(1)


def register(us):
    p = us.add_parser('report', help='deep reports for completed runs by tier (and universe dashboards)')
    p.add_argument('tickers', nargs='*')
    p.add_argument('--existing-runs', action='store_true',
                   help='explain recorded verdicts only: no fetch, no agents, no recomputation')
    p.add_argument('--force', action='store_true', help='full deep report regardless of tier')
    p.set_defaults(func=cmd_universe_report)
