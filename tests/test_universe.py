"""Universe index: import, merge, sync, export, history and gate invariants.

All writes happen in temporary roots; nothing touches the repository's runs/ or universe/.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_core import runtime as h, universe as U
from harness_core.universe_store import RunReader, Store, sync_ticker_from_run, atomic_dump_json

import universe_fixtures as F

POLICY = json.loads((F.REPO/'config/universe.json').read_text(encoding='utf-8'))
IMPORT = POLICY['import']


def parse(text, fmt, screens=()):
    return U.normalize_entries(U.parse_import(text, fmt, IMPORT), IMPORT, list(screens))


class ImportParsingTests(unittest.TestCase):
    def test_universe_import_txt(self):
        accepted, rejected, _ = parse('# StockAnalysis screenshot\nLLY\n nu \nCRWD - CrowdStrike Holdings\n'
                                      '$meli\nNASDAQ:SHOP\nAAPL, MSFT; NVDA\n', 'txt')
        self.assertEqual([e['ticker'] for e in accepted], ['LLY', 'NU', 'CRWD', 'MELI', 'SHOP', 'AAPL', 'MSFT', 'NVDA'])
        self.assertEqual(accepted[2]['company_name'], 'CrowdStrike Holdings')
        self.assertEqual(accepted[4]['exchange'], 'NASDAQ')
        self.assertEqual(rejected, [])

    def test_txt_name_words_never_become_tickers(self):
        accepted, _, _ = parse('LLY ELI LILLY AND CO\nLLY, Eli Lilly and Company\n', 'txt')
        self.assertEqual([e['ticker'] for e in accepted], ['LLY'])

    def test_universe_import_csv(self):
        simple, rejected, _ = parse('ticker,screen\nLLY,compounder\nNU,compounder\nCRWD,outlier_growth\n', 'csv')
        self.assertEqual([(e['ticker'], e['screens']) for e in simple],
                         [('LLY', ['compounder']), ('NU', ['compounder']), ('CRWD', ['outlier_growth'])])
        export = ('No.,Symbol,Company Name,Market Cap,Industry\n1,LLY,Eli Lilly and Company,1.04T,Drug Manufacturers\n'
                  '2,BRK-B,Berkshire Hathaway,1.0T,Insurance\n3,SPY,SPDR S&P 500 ETF Trust,600B,ETF\n')
        rows, rejected, _ = parse(export, 'csv', ['stockanalysis-compounder'])
        self.assertEqual([e['ticker'] for e in rows], ['LLY', 'BRK.B', 'SPY'])
        self.assertEqual(rows[0]['company_name'], 'Eli Lilly and Company')
        self.assertEqual(rows[0]['screener_fields']['Industry'], 'Drug Manufacturers')
        self.assertEqual(rows[2]['security_type'], 'etf')
        headerless, _, _ = parse('LLY,compounder\nMELI\n', 'csv')
        self.assertEqual([(e['ticker'], e['screens']) for e in headerless], [('LLY', ['compounder']), ('MELI', [])])

    def test_universe_import_json_shapes(self):
        for text in ('["LLY","NU"]', '{"screen":"compounder","tickers":["LLY",{"ticker":"NU"}]}',
                     '{"screens":{"compounder":["LLY","NU"]}}', '[{"symbol":"LLY"},{"ticker":"nu","screens":["x"]}]'):
            accepted, _, _ = parse(text, 'json')
            self.assertEqual([e['ticker'] for e in accepted], ['LLY', 'NU'], text)
        with self.assertRaises(U.ImportError_):
            parse('{"unexpected": 1}', 'json')

    def test_universe_deduplicate(self):
        accepted, _, duplicates = parse('LLY\nlly\n LLY \n$LLY\nBRK.B\nBRK-B\nBRK/B\n', 'txt')
        self.assertEqual([e['ticker'] for e in accepted], ['LLY', 'BRK.B'])
        self.assertEqual(len(duplicates), 5)

    def test_universe_merge_screens(self):
        accepted, _, _ = parse('ticker,screen\nMELI,compounder\nMELI,outlier_growth\nMELI,compounder\n', 'csv')
        self.assertEqual(accepted[0]['screens'], ['compounder', 'outlier_growth'])
        universe = {'tickers': {}}
        U.merge_import(universe, accepted, '2026-09-21', 'stockanalysis_screener', 't0', lambda r: None)
        again, _, _ = parse('MELI\n', 'txt', ['growth'])
        _, report = U.merge_import(universe, again, '2026-09-21', 'stockanalysis_screenshot', 't1', lambda r: None)
        row = universe['tickers']['MELI']
        self.assertEqual(report['merged'], ['MELI'])
        self.assertEqual(row['screens'], ['compounder', 'outlier_growth', 'growth'])
        self.assertEqual(row['sources'], ['stockanalysis_screener', 'stockanalysis_screenshot'])
        self.assertEqual(row['imported_at'], 't0')
        # A screen label is provenance, never an archetype.
        self.assertIsNone(row['archetype'])

    def test_universe_invalid_ticker(self):
        accepted, rejected, _ = parse('LLY\n12\nTOOLONGNAME\nFOO:BAR\n!!!\nXX:LLY\n', 'txt')
        self.assertEqual([e['ticker'] for e in accepted], ['LLY'])
        self.assertEqual(len(rejected), 5)
        self.assertTrue(all(r['reason'] for r in rejected))
        for bad in ('../etc', 'A/B/C', ''):
            self.assertIsNone(U.normalize_ticker(bad, IMPORT)[0])

    def test_korean_and_foreign_listings_are_valid(self):
        for raw, want in (('000660', '000660'), ('KRX:267260', '267260'), ('7203.T', '7203.T'), ('shop.to', 'SHOP.TO')):
            self.assertEqual(U.normalize_ticker(raw, IMPORT)[0], want)

    def test_etf_and_fund_marking(self):
        accepted, _, _ = parse('ticker,company_name,type\nQQQ,Invesco QQQ Trust,\nXYZ,Some Growth Fund,\n'
                               'NTRS,Northern Trust Corp,\nABC,Plain Co,stock\n', 'csv')
        kinds = {e['ticker']: e['security_type'] for e in accepted}
        self.assertEqual(kinds, {'QQQ': 'etf', 'XYZ': 'fund', 'NTRS': 'unknown', 'ABC': 'equity'})
        universe = {'tickers': {}}
        U.merge_import(universe, accepted, '2026-09-21', 's', 't', lambda r: None)
        self.assertEqual(universe['tickers']['QQQ']['run_status'], 'BLOCKED')
        self.assertIn('security_type=etf', universe['tickers']['QQQ']['blocked_reason'])
        self.assertEqual(universe['tickers']['NTRS']['run_status'], 'QUEUED')

    def test_new_as_of_uses_dated_run_id_and_keeps_previous(self):
        held = {'LLY': '2026-09-21'}
        universe = {'tickers': {}}
        accepted, _, _ = parse('LLY\n', 'txt')
        U.merge_import(universe, accepted, '2026-09-21', 's', 't0', held.get)
        row = universe['tickers']['LLY']
        self.assertEqual(row['run_id'], 'LLY')
        row.update(run_status='COMPLETE', started=True, score=76.66, ic_state='STARTER', last_synced_at='t0')
        _, report = U.merge_import(universe, accepted, '2026-11-01', 's', 't1', held.get)
        self.assertEqual(report['new_snapshot'], ['LLY'])
        self.assertEqual((row['run_id'], row['as_of_date'], row['run_status'], row['score']),
                         ('LLY-2026-11-01', '2026-11-01', 'QUEUED', None))
        self.assertEqual(row['previous_runs'][0]['score'], 76.66)
        # An in-progress run is never switched to another date behind the operator's back.
        row.update(run_status='BLOCKED', started=True)
        _, report = U.merge_import(universe, accepted, '2027-02-10', 's', 't2', held.get)
        self.assertEqual(report['conflicts'][0]['ticker'], 'LLY')
        self.assertEqual(row['as_of_date'], '2026-11-01')

    def test_formatting_matches_documented_csv(self):
        self.assertEqual([U.fmt(x) for x in (76.66, 82.875, 82.0, 0.5, None)], ['76.66', '82.88', '82', '0.5', ''])
        self.assertEqual(U.fmt(0.9081, 4), '0.9081')
        self.assertEqual(U.position_bounds('6-10% (IC cap)'), (6.0, 10.0))
        self.assertEqual(U.position_bounds('0% until veto cleared'), (0.0, 0.0))


class UniverseStoreTests(unittest.TestCase):
    """On-disk runs built by the harness itself, indexed read-only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        F.copy_harness(self.root)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.root)
        self.reader = RunReader(h)

    def add(self, *tickers, as_of=F.AS_OF, screens=()):
        accepted, _, _ = U.normalize_entries([{'raw': t} for t in tickers], IMPORT, list(screens))
        with self.store.transaction() as universe:
            return U.merge_import(universe, accepted, as_of, 'test', 'now', self.reader.run_as_of)[1]

    def sync(self, ticker):
        return sync_ticker_from_run(self.store, self.reader, ticker)[0]

    def runs_bytes(self):
        return {p: p.read_bytes() for p in (self.root/'runs').rglob('*') if p.is_file()}

    def test_universe_sync_from_run(self):
        F.build('complete', 'LLYX'); F.build('triage_exit', 'GOOGX'); F.build('core_exit', 'MELX')
        F.build('triaged', 'TRGX'); F.build('initialised', 'INIX')
        self.add('LLYX', 'GOOGX', 'MELX', 'TRGX', 'INIX', 'NEWX')
        before = self.runs_bytes()
        rows = {t: self.sync(t) for t in ('LLYX', 'GOOGX', 'MELX', 'TRGX', 'INIX', 'NEWX')}
        self.assertEqual(before, self.runs_bytes(), 'sync must never write inside runs/')

        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        lly = rows['LLYX']
        self.assertEqual((lly['run_status'], lly['stage'], U.display_status(lly)), ('COMPLETE', 'complete', 'COMPLETE'))
        for field, key in (('score', 'score_100'), ('score_ex_valuation', 'score_100_ex_valuation'),
                           ('archetype', 'archetype'), ('hard_veto_status', 'hard_veto_status'),
                           ('mechanical_pre_ic_state', 'mechanical_pre_ic_state'), ('ic_state', 'ic_state'),
                           ('position_range', 'position_range'), ('macro_pacing', 'macro_pacing_multiplier')):
            self.assertEqual(lly[field], final[key], field)
        self.assertEqual(lly['archetype_fit'], final['archetype_fit']['compounder']['fit_score'])
        self.assertEqual(lly['price_to_base'], final['valuation_model']['signals']['price_to_base_value'])
        self.assertEqual(lly['domain_scores']['ev'], final['domain_scores']['expectation_valuation']['score'])
        self.assertEqual(lly['source_files']['final_verdict'], 'runs/LLYX/final_verdict.json')
        self.assertEqual(lly['source_files']['ic'], 'runs/LLYX/reports/IC.json')
        self.assertTrue(lly['ic_complete'])

        for ticker, stage in (('GOOGX', 'triage'), ('MELX', 'pre_ic')):
            row = rows[ticker]
            self.assertEqual((row['run_status'], row['early_exit'], U.display_status(row)), ('COMPLETE', True, 'EARLY_EXIT'))
            self.assertEqual(row['ic_state'], 'EARLY_EXIT_NON_FIT')
            self.assertTrue(row['position_range'].startswith('0%'))
            self.assertEqual(h.load_json(self.root/f'runs/{ticker}/final_verdict.json')['early_exit_record']['stage'], stage)

        self.assertEqual((rows['TRGX']['run_status'], rows['TRGX']['stage']), ('QUEUED', 'domain_analysis'))
        self.assertIn('compounder', rows['TRGX']['reachable_archetypes'])
        self.assertEqual((rows['INIX']['run_status'], rows['INIX']['stage']), ('QUEUED', 'ev'))
        self.assertEqual((rows['NEWX']['run_status'], rows['NEWX']['stage'], rows['NEWX']['started']), ('QUEUED', 'stage0', False))

    def test_unfinalized_early_exit_is_blocked_not_complete(self):
        F.build('triage_exit', 'GOOGX')
        (self.root/'runs/GOOGX/final_verdict.json').unlink()
        manifest = h.load_json(self.root/'runs/GOOGX/run_manifest.json')
        manifest.pop('config_files'); h.dump_json(self.root/'runs/GOOGX/run_manifest.json', manifest)
        self.add('GOOGX')
        row = self.sync('GOOGX')
        self.assertEqual(row['run_status'], 'BLOCKED')
        self.assertIn('final_verdict.json is missing', row['blocked_reason'])
        self.assertEqual(row['verdict_source'], 'aggregate')

    def test_stale_freeze_blocks_and_is_never_refrozen(self):
        F.build('triaged', 'TRGX')
        self.add('TRGX')
        code = self.root/'harness_core/conditions.py'
        code.write_text(code.read_text(encoding='utf-8') + '\n# changed\n', encoding='utf-8')
        manifest_before = (self.root/'runs/TRGX/run_manifest.json').read_bytes()
        row = sync_ticker_from_run(self.store, RunReader(h), 'TRGX')[0]
        self.assertEqual(row['run_status'], 'BLOCKED')
        self.assertIn('stale freeze', row['blocked_reason'])
        self.assertEqual(manifest_before, (self.root/'runs/TRGX/run_manifest.json').read_bytes())

    def validate(self, ticker):
        row = self.store.load()['tickers'][ticker]
        return U.validate_row(row, self.reader.artifacts(row['run_id']), h.STATE_POLICY)

    def errors(self, ticker):
        return [m for lvl, m in self.validate(ticker) if lvl == 'ERROR']

    def tamper_final(self, ticker, **changes):
        path = self.root/f'runs/{ticker}/final_verdict.json'
        final = h.load_json(path); final.update(changes); h.dump_json(path, final)

    def test_clean_rows_validate(self):
        F.build('complete', 'LLYX'); F.build('core_exit', 'MELX')
        self.add('LLYX', 'MELX')
        self.sync('LLYX'); self.sync('MELX')
        self.assertEqual(self.errors('LLYX'), [])
        self.assertEqual(self.errors('MELX'), [])

    def test_universe_position_cap(self):
        F.build('complete', 'LLYX')
        self.add('LLYX'); self.sync('LLYX')
        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        # IC may not exceed the deterministic cap for the mechanical state...
        self.tamper_final('LLYX', mechanical_pre_ic_state='STARTER_OR_WATCH', ic_state='NORMAL', position_range='2-4%')
        self.sync('LLYX')
        self.assertTrue(any('exceeds the deterministic cap' in e for e in self.errors('LLYX')))
        # ...and a position that the reconciliation replay would not produce is caught too.
        self.tamper_final('LLYX', mechanical_pre_ic_state=final['mechanical_pre_ic_state'], ic_state='STARTER',
                          position_range='6-8%')
        self.sync('LLYX')
        self.assertTrue(any('replay gives position' in e for e in self.errors('LLYX')))

    def test_universe_veto_gate(self):
        F.build('complete', 'LLYX')
        self.add('LLYX')
        for changes, needle in (({'hard_veto_status': 'UNRESOLVED'}, 'Hard Veto UNRESOLVED'),
                                ({'coverage_weight': 85}, 'coverage 85'),
                                ({'macro_geo_overlay': {'pending_reanalysis_domains': ['financial_survival']}},
                                 'structural re-analysis is pending')):
            F.aggregate('LLYX')
            self.tamper_final('LLYX', **changes)
            self.sync('LLYX')
            self.assertTrue(any(needle in e for e in self.errors('LLYX')), (needle, self.errors('LLYX')))

    def test_complete_without_final_and_score_drift_are_errors(self):
        F.build('complete', 'LLYX')
        self.add('LLYX'); self.sync('LLYX')
        with self.store.transaction() as universe:
            universe['tickers']['LLYX']['score'] = 99.0
        self.assertTrue(any('universe score 99.0' in e for e in self.errors('LLYX')))
        (self.root/'runs/LLYX/final_verdict.json').unlink()
        self.assertTrue(any('COMPLETE but final_verdict.json is missing' in e for e in self.errors('LLYX')))

    def test_early_exit_with_ic_report_warns(self):
        F.build('triage_exit', 'GOOGX')
        self.add('GOOGX'); self.sync('GOOGX')
        h.dump_json(self.root/'runs/GOOGX/reports/IC.json', F.ic_report('GOOGX', 'WATCH'))
        warnings = [m for lvl, m in self.validate('GOOGX') if lvl == 'WARNING']
        self.assertTrue(any('IC' in w for w in warnings))

    def test_export_csv(self):
        F.build('complete', 'LLYX'); F.build('triage_exit', 'GOOGX')
        self.add('LLYX', 'GOOGX', 'NEWX')
        for t in ('LLYX', 'GOOGX', 'NEWX'):
            self.sync(t)
        text = U.to_csv(self.store.ordered(self.store.load()))
        lines = text.splitlines()
        self.assertEqual(lines[0], ','.join(U.CSV_COLUMNS))
        self.assertEqual(lines[0], 'ticker,score,score_ex_ev,archetype,fit,ev,as,di,fs,price_to_base,hard_veto,'
                                   'mechanical_state,ic_state,position_range,macro_pacing,status,as_of')
        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        cells = dict(zip(U.CSV_COLUMNS, lines[1].split(',')))
        self.assertEqual(cells['ticker'], 'LLYX')
        self.assertEqual(float(cells['score']), round(final['score_100'], 2))
        self.assertEqual(cells['ic_state'], final['ic_state'])
        self.assertEqual(cells['position_range'], final['position_range'])
        self.assertEqual(cells['status'], 'COMPLETE')
        self.assertTrue(lines[2].startswith('GOOGX,') and ',EARLY_EXIT,' in lines[2])
        self.assertTrue(lines[3].startswith('NEWX,') and ',QUEUED,' in lines[3])
        # The derived universe.csv next to the index is the same export.
        self.assertEqual((self.root/'universe/universe.csv').read_text(encoding='utf-8'), text)

    def test_history_snapshot(self):
        F.build('complete', 'LLYX')
        self.add('LLYX')
        self.sync('LLYX'); self.sync('LLYX')
        history = self.store.history('LLYX')
        self.assertEqual(len(history), 1, 'an unchanged re-sync adds no history')
        self.assertEqual(history[0]['snapshot']['ic_state'], 'STARTER')
        # A later snapshot goes to a new run directory; the frozen one is never touched.
        original = self.runs_bytes()
        report = self.add('LLYX', as_of='2026-11-01')
        self.assertEqual(report['new_snapshot'], ['LLYX'])
        row = self.store.load()['tickers']['LLYX']
        self.assertEqual(row['run_id'], 'LLYX-2026-11-01')
        self.assertEqual(row['previous_runs'][0]['ic_state'], 'STARTER')
        F.build('triage_exit', 'LLYX-2026-11-01', as_of='2026-11-01')
        self.sync('LLYX')
        history = self.store.history('LLYX')
        self.assertEqual(history[-1]['changes']['ic_state'], ['STARTER', 'EARLY_EXIT_NON_FIT'])
        self.assertEqual(history[-1]['changes']['as_of_date'], [F.AS_OF, '2026-11-01'])
        self.assertTrue(all(p.read_bytes() == b for p, b in original.items()))
        dest = self.store.write_snapshot('2026-11-01')
        self.assertEqual(h.load_json(dest)['tickers']['LLYX']['run_id'], 'LLYX-2026-11-01')

    def test_crashed_running_row_becomes_resumable(self):
        F.build('triaged', 'TRGX')
        self.add('TRGX')
        self.store.update_row('TRGX', lambda r: r.update(run_status='RUNNING', stage='domain_analysis'))
        self.assertEqual(self.sync('TRGX')['run_status'], 'QUEUED')      # no lock held: crashed
        with self.store.ticker_lock('TRGX'):
            self.store.update_row('TRGX', lambda r: r.update(run_status='RUNNING'))
            self.assertEqual(self.sync('TRGX')['run_status'], 'RUNNING')  # a live runner keeps it

    def test_atomic_write_leaves_no_partial_file(self):
        path = self.root/'universe/x.json'
        atomic_dump_json(path, {'a': 1})
        atomic_dump_json(path, {'a': 2})
        self.assertEqual(h.load_json(path), {'a': 2})
        self.assertEqual([p.name for p in path.parent.iterdir()], ['x.json'])


class UniverseCliTests(unittest.TestCase):
    def test_cli_import_status_export_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            F.copy_harness(root)
            with patch.object(h, 'ROOT', root):
                F.build('complete', 'LLYX')

            def cli(*args, ok=True):
                done = subprocess.run([sys.executable, 'harness.py', *args], cwd=root, capture_output=True,
                                      text=True, encoding='utf-8')
                if ok:
                    self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                else:
                    self.assertNotEqual(done.returncode, 0, done.stdout)
                return done.stdout
            (root/'screen.csv').write_text('ticker,screen\nLLYX,compounder\nNEWX,outlier_growth\nNEWX,compounder\n12,x\n',
                                           encoding='utf-8')
            out = cli('universe', 'import', 'screen.csv', '--as-of', F.AS_OF)
            self.assertIn('2 ticker(s) accepted, 1 rejected', out)
            cli('universe', 'import', 'screen.csv', ok=False)                       # --as-of is required
            out = cli('universe', 'status', '--archetype', 'compounder', '--veto', 'CLEARED', '--min-score', '70')
            self.assertIn('LLYX', out); self.assertNotIn('NEWX  ', out)
            cli('universe', 'export', 'out/universe.csv')
            self.assertTrue((root/'out/universe.csv').read_text(encoding='utf-8').startswith('ticker,score,score_ex_ev'))
            cli('universe', 'export', 'out/universe.json')
            self.assertEqual(len(json.loads((root/'out/universe.json').read_text(encoding='utf-8'))['rows']), 2)
            cli('universe', 'validate')
            shown = json.loads(cli('universe', 'show', 'NEWX'))
            self.assertEqual(shown['row']['screens'], ['outlier_growth', 'compounder'])
            cli('universe', 'history', 'LLYX')
            cli('universe', 'remove', 'NEWX')
            self.assertNotIn('NEWX', json.loads((root/'universe/universe.json').read_text(encoding='utf-8'))['tickers'])
            cli('universe', 'show', 'NEWX', ok=False)


if __name__ == '__main__':
    unittest.main()
