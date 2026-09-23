"""`universe report`: tiered deep reports for completed runs, and the universe dashboards.

A run whose freeze matches the current harness gets the ordinary `report` first
(fresh deterministic verdict + easy_report.md). A run frozen under another
harness, or any run with --existing-runs, is explained from its recorded
artifacts only: no fetch, no agent, no recomputation.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path

from . import universe as U
from .report_builder import write_deep_report
from .universe_store import RunReader, Store, atomic_write_text, sync_many, utcnow


def _runtime():
    from . import runtime
    return runtime


def generate_reports(store, reader, tickers=None, existing_runs=False, force=False):
    h = reader.h
    wanted = [r['ticker'] for r in Store.ordered(store.load()) if not tickers or r['ticker'] in tickers]
    rows = {r['ticker']: r for r in sync_many(store, reader, wanted)}
    results, touched, failed = [], [], []
    for ticker in wanted:
        row = rows.get(ticker)
        if row is None:
            continue
        run_id = row.get('run_id') or ticker
        if row.get('run_status') != 'COMPLETE':
            results.append({'ticker': ticker, 'status': 'SKIPPED', 'reason': f"run_status {row.get('run_status')}"})
            continue
        freeze = reader.artifacts(run_id)['freeze']
        mode = 'fresh' if freeze.get('config_current') and freeze.get('inputs_current') and not existing_runs \
            else 'existing-run'
        try:
            if mode == 'fresh':
                with contextlib.redirect_stdout(io.StringIO()):
                    h.cmd_report(argparse.Namespace(ticker=run_id))
            result = write_deep_report(h, run_id, force=force, reader=reader)
            result.update(ticker=ticker, mode=mode)
        except (SystemExit, ValueError) as error:
            result = {'ticker': ticker, 'run_id': run_id, 'status': 'ERROR', 'mode': mode, 'reason': str(error)}
            failed.append(ticker)
        results.append(result)
        touched.append(ticker)
    if touched:
        sync_many(store, reader, touched)
    for ticker in failed:
        store.update_row(ticker, lambda r: r.update(report_status='ERROR'))
    return results


# ------------------------------------------------------------------ dashboards (pure builder + writer)

SUMMARY_COLUMNS = ['Ticker', 'Score', 'Ex-EV', 'Archetype', 'Fit', 'EV', 'AS', 'DI', 'FS', 'Price/Base', 'Hard Veto',
                   'Mechanical State', 'IC State', 'Position Range', 'Macro Pacing', 'Status', 'As-of', 'Deep report']


def _cell(value):
    return str(value if value not in (None, '') else '—').replace('|', '\\|').replace('\n', ' ')


def _link(row, reports_dir):
    path = (row.get('source_files') or {}).get('deep_report_md')
    if not path:
        return '—'
    return f"[{row.get('report_tier') or 'report'}]({Path(os.path.relpath(path, reports_dir)).as_posix()})"


def _summary_cells(row, reports_dir):
    ds = row.get('domain_scores') or {}
    return [row['ticker'], U.fmt(row.get('score')), U.fmt(row.get('score_ex_valuation')), row.get('archetype'),
            U.fmt(row.get('archetype_fit')), U.fmt(ds.get('ev')), U.fmt(ds.get('as')), U.fmt(ds.get('di')),
            U.fmt(ds.get('fs')), U.fmt(row.get('price_to_base'), 4), row.get('hard_veto_status'),
            row.get('mechanical_pre_ic_state'), row.get('ic_state'), row.get('position_range'),
            U.fmt(row.get('macro_pacing')), U.display_status(row), row.get('as_of_date'), _link(row, reports_dir)]


def _table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(_cell(c) for c in r) + ' |' for r in rows]
    return out if rows else ['_(해당 없음)_']


def _preamble(title, generated_at, note):
    return [f'# {title}', '', f'generated {generated_at} · source `universe/universe.json` '
            '(each row copies `runs/<RUN>/final_verdict.json`, or `aggregate.json` before finalization)', '',
            f'> {note}', '']


def build_universe_summary(rows, config, generated_at, reports_dir='reports/universe'):
    """{filename: markdown}. Pure; nothing here ranks by merit or changes a number."""
    note = config['dashboards']['note']
    files = {}
    counts = {}
    for r in rows:
        counts[U.display_status(r)] = counts.get(U.display_status(r), 0) + 1
    arch_counts = {}
    for r in rows:
        if r.get('archetype'):
            arch_counts[r['archetype']] = arch_counts.get(r['archetype'], 0) + 1
    lines = _preamble('Universe summary', generated_at, note)
    lines += [f"{len(rows)} ticker(s): " + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())), '',
              'Archetypes (recorded): ' + (', '.join(f'{k} {v}' for k, v in sorted(arch_counts.items())) or '—'), '',
              '정렬: import 순서. Price/Base·Fit·Score는 하네스가 기록한 값이며 순위가 아니다.', '']
    lines += _table(SUMMARY_COLUMNS, [_summary_cells(r, reports_dir) for r in rows])
    blocked = [r for r in rows if r.get('run_status') in ('BLOCKED', 'FAILED')]
    if blocked:
        lines += ['', '## Blocked / failed', '']
        lines += _table(['Ticker', 'Status', 'Stage', 'Reason'],
                        [[r['ticker'], r['run_status'], r.get('stage'),
                          r.get('blocked_reason') or (r.get('last_error') or {}).get('summary')] for r in blocked])
    lines += ['', '## Provenance', '']
    lines += _table(['Ticker', 'Run', 'Verdict source', 'final_verdict sha256'],
                    [[r['ticker'], r.get('run_id'), r.get('verdict_source'),
                      ((r.get('source_hashes') or {}).get('final_verdict') or '')[:12]] for r in rows])
    files['universe_summary.md'] = '\n'.join(lines) + '\n'

    by_fit = lambda r: (-(r.get('archetype_fit') or 0), r['ticker'])
    arch_header = ['Ticker', 'Score', 'Ex-EV', 'Fit', 'Price/Base', 'Hard Veto', 'IC State', 'Position Range',
                   'Macro Pacing', 'Status', 'As-of', 'Deep report']

    def arch_cells(r):
        return [r['ticker'], U.fmt(r.get('score')), U.fmt(r.get('score_ex_valuation')), U.fmt(r.get('archetype_fit')),
                U.fmt(r.get('price_to_base'), 4), r.get('hard_veto_status'), r.get('ic_state'), r.get('position_range'),
                U.fmt(r.get('macro_pacing')), U.display_status(r), r.get('as_of_date'), _link(r, reports_dir)]
    for filename, archetype in config['dashboards']['archetype_files'].items():
        primary = sorted([r for r in rows if r.get('archetype') == archetype], key=by_fit)
        secondary = sorted([r for r in rows if archetype in (r.get('secondary_archetypes') or [])], key=lambda r: r['ticker'])
        lines = _preamble(f'Archetype: {archetype}', generated_at, note)
        lines += [f'정렬: 기록된 {archetype} fit (설명용; 투자 우열 순위가 아니다).', '', '## Primary archetype', '']
        lines += _table(arch_header, [arch_cells(r) for r in primary])
        lines += ['', '## Secondary archetype (deterministic ranking below the primary)', '']
        lines += _table(['Ticker', 'Primary', 'Secondary', 'IC State', 'Status'],
                        [[r['ticker'], r.get('archetype'), ', '.join(r.get('secondary_archetypes') or []),
                          r.get('ic_state'), U.display_status(r)] for r in secondary])
        files[filename] = '\n'.join(lines) + '\n'

    watch_states = set(config['dashboards']['watch_states'])
    watch = [r for r in rows if r.get('run_status') == 'COMPLETE' and not r.get('early_exit')
             and (r.get('ic_state') in watch_states)]
    lines = _preamble('Watchlist', generated_at, note)
    lines += ['완료된 run 중 신규 매수 승인이 없는 관찰·재검토 상태. 가격 변화가 아니라 새 증거와 재동결·재분석이 상태를 바꾼다.', '']
    lines += _table(['Ticker', 'IC State', 'Mechanical State', 'Hard Veto', 'Archetype', 'Score', 'Price/Base',
                     'Position Range', 'As-of', 'Deep report'],
                    [[r['ticker'], r.get('ic_state'), r.get('mechanical_pre_ic_state'), r.get('hard_veto_status'),
                      r.get('archetype'), U.fmt(r.get('score')), U.fmt(r.get('price_to_base'), 4),
                      r.get('position_range'), r.get('as_of_date'), _link(r, reports_dir)] for r in sorted(watch, key=lambda r: r['ticker'])])
    files['watchlist.md'] = '\n'.join(lines) + '\n'

    exits = [r for r in rows if r.get('early_exit')]
    lines = _preamble('Early exit', generated_at, note)
    lines += ['도달 가능한 투자 유형이 없어 IC 없이 종료된 run. Full Core·Macro·RT·IC는 의도적으로 실행되지 않았다. '
              '`BLOCKED`는 aggregate.json에 조기 종료가 기록됐지만 final_verdict.json으로 확정되지 않은 run이다.', '']
    lines += _table(['Ticker', 'Status', 'Exit stage', 'Last reachable', 'Score', 'Ex-EV', 'EV', 'AS', 'DI', 'FS',
                     'Price/Base', 'As-of'],
                    [[r['ticker'], U.display_status(r), r.get('early_exit_stage'),
                      ', '.join(r.get('last_reachable_archetypes') or []), U.fmt(r.get('score')),
                      U.fmt(r.get('score_ex_valuation')), U.fmt((r.get('domain_scores') or {}).get('ev')),
                      U.fmt((r.get('domain_scores') or {}).get('as')), U.fmt((r.get('domain_scores') or {}).get('di')),
                      U.fmt((r.get('domain_scores') or {}).get('fs')), U.fmt(r.get('price_to_base'), 4),
                      r.get('as_of_date')] for r in sorted(exits, key=lambda r: r['ticker'])])
    files['early_exit.md'] = '\n'.join(lines) + '\n'
    return files


def write_dashboards(store):
    rows = Store.ordered(store.load())
    reports_dir = store.policy['paths']['reports_dir']
    files = build_universe_summary(rows, store.policy, utcnow(), reports_dir)
    for name, text in files.items():
        atomic_write_text(store.root/reports_dir/name, text)
    return [f'{reports_dir}/{name}' for name in files]


def cmd_dashboard(args):
    h = _runtime()
    store, reader = Store(h.ROOT), RunReader(h)
    if not args.no_sync:
        sync_many(store, reader)
    for path in write_dashboards(store):
        print(path)


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
    for path in write_dashboards(store):
        print(f'  dashboard: {path}')
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
    p = us.add_parser('dashboard', help='rewrite reports/universe/*.md from the index')
    p.add_argument('--no-sync', action='store_true')
    p.set_defaults(func=cmd_dashboard)
