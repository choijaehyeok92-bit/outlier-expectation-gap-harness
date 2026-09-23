"""Universe dashboards, concurrency safety and history."""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_core import runtime as h, universe as U
from harness_core.universe_reports import build_universe_summary, write_dashboards
from harness_core.universe_runner import BatchRunner, Options
from harness_core.universe_store import RunReader, Store, sync_ticker_from_run

import universe_fixtures as F

CONFIG = json.loads((F.REPO/'config/universe.json').read_text(encoding='utf-8'))


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        F.copy_harness(self.root)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.root)

    def add(self, *tickers, as_of=F.AS_OF):
        accepted, _, _ = U.normalize_entries([{'raw': t} for t in tickers], CONFIG['import'])
        with self.store.transaction() as universe:
            U.merge_import(universe, accepted, as_of, 'test', 'now', RunReader(h).run_as_of)


class DashboardTests(Case):
    def test_universe_dashboards(self):
        F.build('complete', 'LLYX'); F.build('complete', 'WATX', ic_state='WATCH')
        F.build('triage_exit', 'GOOX'); F.build('core_exit', 'MELX')
        self.add('LLYX', 'WATX', 'GOOX', 'MELX', 'NEWX')
        reader = RunReader(h)
        for ticker in ('LLYX', 'WATX', 'GOOX', 'MELX', 'NEWX'):
            sync_ticker_from_run(self.store, reader, ticker)
        written = write_dashboards(self.store)
        self.assertEqual(sorted(Path(p).name for p in written),
                         sorted(['universe_summary.md', 'compounders.md', 'growth.md', 'outlier_growth.md',
                                 'buffett_value.md', 'moonshots.md', 'watchlist.md', 'early_exit.md']))
        summary = (self.root/'reports/universe/universe_summary.md').read_text(encoding='utf-8')
        header = next(l for l in summary.splitlines() if l.startswith('| Ticker | Score'))
        for column in ('Ticker', 'Score', 'Ex-EV', 'Archetype', 'Fit', 'EV', 'AS', 'DI', 'FS', 'Price/Base', 'Hard Veto',
                       'Mechanical State', 'IC State', 'Position Range', 'Macro Pacing', 'Status', 'As-of'):
            self.assertIn(f'| {column} |', header + '|')
        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        lly = next(l for l in summary.splitlines() if l.startswith('| LLYX |'))
        self.assertIn(f"| {U.fmt(final['score_100'])} |", lly)
        self.assertIn(f"| {final['ic_state']} | {final['position_range']} |", lly)
        self.assertNotRegex(summary.lower(), r'top pick|best stock|추천')
        compounders = (self.root/'reports/universe/compounders.md').read_text(encoding='utf-8')
        self.assertIn('| LLYX |', compounders)
        self.assertIn('| WATX |', (self.root/'reports/universe/watchlist.md').read_text(encoding='utf-8'))
        early = (self.root/'reports/universe/early_exit.md').read_text(encoding='utf-8')
        self.assertRegex(early, r'\| GOOX \| EARLY_EXIT \| triage \|')
        recorded = h.load_json(self.root/'runs/MELX/final_verdict.json')['early_exit_record']['last_reachable_archetypes']
        self.assertIn(f"| MELX | EARLY_EXIT | pre_ic | {', '.join(recorded)} |", early)
        self.assertNotIn('| LLYX |', early)

    def test_builder_is_pure_and_link_is_relative(self):
        row = {**U.ROW_DEFAULTS, 'ticker': 'LLY', 'run_id': 'LLY', 'run_status': 'COMPLETE', 'archetype': 'compounder',
               'archetype_fit': 82.875, 'ic_state': 'STARTER', 'position_range': '1-2%', 'report_tier': 'full',
               'source_files': {'deep_report_md': 'runs/LLY/deep_report.md'}, 'queue_seq': 1}
        files = build_universe_summary([row], CONFIG, 'T')
        self.assertIn('[full](../../runs/LLY/deep_report.md)', files['universe_summary.md'])
        self.assertIn('| LLY | — | — | 82.88 |', files['compounders.md'])
        self.assertEqual(files, build_universe_summary([row], CONFIG, 'T'))

    def test_dashboards_follow_a_batch(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        self.add('GOOS')
        summary = BatchRunner(self.store, RunReader(h), Options()).run()
        self.assertIn('reports/universe/early_exit.md', summary['dashboards'])
        self.assertIn('| GOOS | EARLY_EXIT |', (self.root/'reports/universe/early_exit.md').read_text(encoding='utf-8'))
        snapshots = list((self.root/'universe/snapshots').glob('*.json'))
        self.assertEqual(len(snapshots), 1)


class ConcurrencyTests(Case):
    def test_parallel_transactions_do_not_lose_updates(self):
        self.add('BASE')
        threads = [threading.Thread(target=self.add, args=(f'T{i}',)) for i in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        script = ('import sys; sys.path.insert(0, ".")\n'
                  'from harness_core import universe as U\nfrom harness_core.universe_store import Store\n'
                  'store = Store(".")\n'
                  'accepted, _, _ = U.normalize_entries([{"raw": sys.argv[1]}], store.policy["import"])\n'
                  'with store.transaction() as u:\n    U.merge_import(u, accepted, "2026-09-19", "p", "t", lambda r: None)\n')
        (self.root/'add_one.py').write_text(script, encoding='utf-8')
        processes = [subprocess.Popen([sys.executable, 'add_one.py', f'P{i}'], cwd=self.root) for i in range(6)]
        self.assertEqual([p.wait() for p in processes], [0] * 6)
        tickers = set(self.store.load()['tickers'])
        self.assertEqual(tickers, {'BASE', *(f'T{i}' for i in range(12)), *(f'P{i}' for i in range(6))})
        self.assertEqual(len({r['queue_seq'] for r in self.store.load()['tickers'].values()}), 19)
        self.assertFalse(list((self.root/'universe').glob('.*.tmp')))

    def test_same_ticker_never_runs_twice(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        self.add('GOOS')
        with self.store.ticker_lock('GOOS'):
            self.store.update_row('GOOS', lambda r: r.update(run_status='RUNNING'))
            summary = BatchRunner(self.store, RunReader(h), Options()).run()
            self.assertEqual(summary['selected'], [])
            self.assertIn(('GOOS', 'running elsewhere'), [(s['ticker'], s['reason']) for s in summary['skipped']])
            from harness_core.universe_runner import TickerJob
            runner = BatchRunner(self.store, RunReader(h), Options())
            self.assertEqual(TickerJob(runner, 'GOOS').process()['outcome'], 'skipped_locked')
        self.assertFalse((self.root/'runs/GOOS').exists())


class HistoryCliTests(Case):
    def test_history_cli(self):
        F.build('complete', 'LLYX')
        self.add('LLYX')
        sync_ticker_from_run(self.store, RunReader(h), 'LLYX')
        done = subprocess.run([sys.executable, 'harness.py', 'universe', 'history', 'LLYX'], cwd=self.root,
                              capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('ic_state: ∅ → STARTER', done.stdout)
        done = subprocess.run([sys.executable, 'harness.py', 'universe', 'history', 'LLYX', '--json'], cwd=self.root,
                              capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(json.loads(done.stdout)[0]['snapshot']['ic_state'], 'STARTER')


if __name__ == '__main__':
    unittest.main()
