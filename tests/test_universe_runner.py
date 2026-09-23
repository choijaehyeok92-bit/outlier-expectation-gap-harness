"""Batch runner: planner-driven execution, early exit, resume, failure isolation, dry run.

Tickers are synthetic and network-free; agent output is staged in `.harness_inputs/<RUN>/`
exactly as the CI workflows stage it, or produced by a tiny local `--agent-cmd` script.
Every write happens in a temporary root.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_core import runtime as h, universe as U
from harness_core.universe_runner import BatchRunner, Options
from harness_core.universe_store import RunReader, Store

import universe_fixtures as F

POLICY = json.loads((F.REPO/'config/universe.json').read_text(encoding='utf-8'))
DOMAIN_ONLY = ('SL', 'CP', 'MT', 'RF', 'MA', 'LG')


class RunnerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        F.copy_harness(self.root)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def store(self):
        return Store(self.root)

    def add(self, *tickers, as_of=F.AS_OF, raw_entries=None):
        entries = raw_entries or [{'raw': t} for t in tickers]
        accepted, _, _ = U.normalize_entries(entries, POLICY['import'])
        with self.store().transaction() as universe:
            U.merge_import(universe, accepted, as_of, 'test', 'now', RunReader(h).run_as_of)

    def batch(self, **options):
        return BatchRunner(self.store(), RunReader(h), Options(**options)).run()

    def row(self, ticker):
        return self.store().load()['tickers'][ticker]

    def statuses(self, ticker):
        run = self.root/'runs'/ticker/'reports'
        return {p.stem: h.load_json(p)['analysis_status'] for p in sorted(run.glob('*.json'))}

    def log_commands(self, ticker):
        logs = list((self.root/'runlogs/universe').glob(f'*/{ticker}.json'))
        return [c['command'] for p in logs for inv in h.load_json(p)['invocations'] for c in inv.get('commands', [])]


class BatchFlowTests(RunnerCase):
    def test_triage_only_then_eligible_only_full_run(self):
        F.staged_inputs(self.root, 'LLYS', 'complete')
        F.staged_inputs(self.root, 'NUS', 'complete', agents=[a for a in ('EV', 'AS', 'DI', 'FS', 'SL', 'CP', 'MT', 'RF',
                                                                             'MA', 'LG', 'ED', 'RT', 'IC')])  # no MO staged
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        F.staged_inputs(self.root, 'MELS', 'core_exit')
        self.add('LLYS', 'NUS', 'GOOS', 'MELS', 'SPY')

        summary = self.batch(stop_after='triage')
        self.assertEqual(self.row('SPY')['run_status'], 'BLOCKED')                         # ETF never run
        self.assertIn(('SPY', 'etf'), [(s['ticker'], s['reason']) for s in summary['skipped']])
        for ticker in ('LLYS', 'NUS', 'MELS'):
            row = self.row(ticker)
            self.assertEqual((row['run_status'], row['stage']), ('QUEUED', 'domain_analysis'), ticker)
            statuses = self.statuses(ticker)
            self.assertTrue(all(statuses[a] == 'complete' for a in ('EV', 'AS', 'DI', 'FS')))
            self.assertTrue(all(statuses[a] == 'pending' for a in DOMAIN_ONLY), 'triage-only never runs core domains')
        goos = self.row('GOOS')
        self.assertEqual((goos['run_status'], goos['early_exit'], U.display_status(goos)), ('COMPLETE', True, 'EARLY_EXIT'))

        self.batch(eligible_only=True, only_started=True, workers=2)
        lly, nu, meli = self.row('LLYS'), self.row('NUS'), self.row('MELS')
        final = h.load_json(self.root/'runs/LLYS/final_verdict.json')
        self.assertEqual((lly['run_status'], lly['ic_state'], lly['position_range']), ('COMPLETE', 'STARTER', '1-2%'))
        self.assertEqual((lly['score'], lly['archetype'], lly['hard_veto_status']),
                         (final['score_100'], final['archetype'], 'CLEARED'))
        self.assertEqual(nu['ic_state'], 'STARTER')
        # NUS had no staged MO: the runner reused LLYS's cached global components, as `init` would.
        self.assertEqual(h.load_json(self.root/'runs/NUS/reports/MO.json').get('cache_scope'), 'global_components_only')
        self.assertTrue((self.root/f'runs/_macro/{F.AS_OF}/components.json').exists())
        # MELI-like: full core, then a deterministic early exit; no macro, ED/RT or IC.
        self.assertEqual((meli['run_status'], meli['early_exit']), ('COMPLETE', True))
        self.assertEqual(h.load_json(self.root/'runs/MELS/final_verdict.json')['early_exit_record']['stage'], 'pre_ic')
        for ticker in ('GOOS', 'MELS'):
            statuses = self.statuses(ticker)
            self.assertTrue(all(statuses[a] != 'complete' for a in ('MO', 'ED', 'RT', 'IC')), ticker)
        # The index agrees with the artifacts, and the harness's own gates hold.
        store = self.store()
        for ticker in ('LLYS', 'NUS', 'GOOS', 'MELS'):
            row = store.load()['tickers'][ticker]
            errors = [m for lvl, m in U.validate_row(row, RunReader(h).artifacts(ticker), h.STATE_POLICY) if lvl == 'ERROR']
            self.assertEqual(errors, [], ticker)
        self.assertTrue((self.root/'runs/LLYS/easy_report.md').exists())
        logs = list((self.root/'runlogs/universe').glob('*/universe-run.json'))
        self.assertEqual(len(h.load_json(logs[0])['batches']), 2)

    def test_batch_early_exit(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        self.add('GOOS')
        self.batch()
        row = self.row('GOOS')
        self.assertEqual((row['run_status'], row['stage'], row['ic_state']), ('COMPLETE', 'complete', 'EARLY_EXIT_NON_FIT'))
        self.assertTrue(row['position_range'].startswith('0%'))
        statuses = self.statuses('GOOS')
        self.assertTrue(all(statuses[a] == 'pending' for a in (*DOMAIN_ONLY, 'MO', 'ED', 'RT', 'IC')))
        commands = self.log_commands('GOOS')
        self.assertFalse([c for c in commands if c.startswith('prompt GOOS') and c.split()[2] in (*DOMAIN_ONLY, 'MO', 'ED', 'RT', 'IC')])
        final = h.load_json(self.root/'runs/GOOS/final_verdict.json')
        self.assertTrue(final['early_exit_record']['ic_intentionally_not_run'])

    def test_batch_resume(self):
        F.staged_inputs(self.root, 'RESU', 'complete', agents=['EV'])
        self.add('RESU')
        self.batch()
        row = self.row('RESU')
        self.assertEqual((row['run_status'], row['stage']), ('BLOCKED', 'triage'))
        self.assertEqual(row['awaiting'], ['AS', 'DI', 'FS'])
        for aid in row['awaiting']:
            self.assertTrue((self.root/f'runs/RESU/{aid}_prompt.md').exists())
        ev_hash = (self.root/'runs/RESU/reports/EV.json').read_bytes()
        F.staged_inputs(self.root, 'RESU', 'complete', agents=['AS', 'DI', 'FS'])
        self.batch(only_started=True, stop_after='triage')
        row = self.row('RESU')
        self.assertEqual((row['run_status'], row['stage']), ('QUEUED', 'domain_analysis'))
        self.assertEqual(ev_hash, (self.root/'runs/RESU/reports/EV.json').read_bytes())
        commands = self.log_commands('RESU')
        self.assertEqual(commands.count('validate RESU EV'), 1, 'a completed stage is never re-run')
        self.assertEqual(commands.count('freeze RESU'), 1)

    def test_batch_failure_isolation(self):
        base = F.staged_inputs(self.root, 'BAD', 'complete', agents=['EV'])
        broken = h.load_json(base/'reports/EV.json'); broken['score_0_100'] = 12.0
        h.dump_json(base/'reports/EV.json', broken)
        F.staged_inputs(self.root, 'WRONG', 'complete', agents=[])
        h.dump_json(self.root/'.harness_inputs/WRONG/reports/EV.json', F.report(F.agent('EV'), 'OTHER'))
        F.staged_inputs(self.root, 'GOOD', 'triage_exit')
        self.add('BAD', 'WRONG', 'GOOD')
        summary = self.batch(workers=2)
        self.assertEqual({o['ticker']: o['outcome'] for o in summary['outcomes']},
                         {'BAD': 'failed', 'WRONG': 'failed', 'GOOD': 'complete'})
        bad = self.row('BAD')
        self.assertEqual(bad['run_status'], 'FAILED')
        error = bad['last_error']
        self.assertEqual(set(error), {'command', 'stage', 'exception_type', 'stderr', 'retryable', 'timestamp', 'summary'})
        self.assertEqual((error['command'], error['stage'], error['retryable']), ('harness.py validate BAD EV', 'ev', False))
        self.assertIn('rubric weighted score', error['stderr'])
        self.assertIn('not WRONG', self.row('WRONG')['last_error']['summary'])
        # A later run leaves FAILED tickers alone until retried.
        self.assertIn(('BAD', 'failed (use `universe retry`)'),
                      [(s['ticker'], s['reason']) for s in self.batch()['skipped']])
        F.staged_inputs(self.root, 'BAD', 'triage_exit')
        self.batch(tickers=('BAD',), include_failed=True)
        self.assertEqual((self.row('BAD')['run_status'], self.row('BAD')['early_exit']), ('COMPLETE', True))

    def test_batch_skip_completed(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        self.add('GOOS')
        self.batch()
        before = {p: p.read_bytes() for p in (self.root/'runs/GOOS').rglob('*') if p.is_file()}
        summary = self.batch()
        self.assertEqual(summary['selected'], [])
        self.assertEqual([(s['ticker'], s['reason']) for s in summary['skipped']], [('GOOS', 'complete')])
        self.assertEqual(before, {p: p.read_bytes() for p in (self.root/'runs/GOOS').rglob('*') if p.is_file()})

    def test_existing_complete_run_is_synced_not_rerun(self):
        F.build('complete', 'LLYX')
        self.add('LLYX')
        before = {p: p.read_bytes() for p in (self.root/'runs/LLYX').rglob('*') if p.is_file()}
        summary = self.batch(report=False)
        self.assertEqual(summary['outcomes'][0]['outcome'], 'complete')
        self.assertEqual(self.row('LLYX')['ic_state'], 'STARTER')
        self.assertEqual(before, {p: p.read_bytes() for p in (self.root/'runs/LLYX').rglob('*') if p.is_file()})
        self.assertFalse([c for c in self.log_commands('LLYX') if not c.startswith('report')])

    def test_dry_run_writes_nothing(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        F.build('triaged', 'TRGX'); F.build('complete', 'LLYX')
        self.add('GOOS', 'TRGX', 'LLYX', 'NEWX')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = BatchRunner(self.store(), RunReader(h), Options(dry_run=True)).dry_run()
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        counts = result['counts']
        self.assertEqual((counts['tickers'], counts['need_stage0'], counts['already_triaged'],
                          counts['eligible_for_full_core'], counts['complete']), (4, 2, 1, 1, 1))
        nxt = {item['ticker']: item['next'] for item in result['would_process']}
        # LLYX's run is already complete on disk; the runner only syncs it into the index.
        self.assertEqual(nxt, {'GOOS': 'init', 'TRGX': 'agents', 'LLYX': 'complete', 'NEWX': 'init'})

    def test_stage0_blocks_until_inputs_are_staged(self):
        self.add('NEWX')
        self.batch()
        row = self.row('NEWX')
        self.assertEqual((row['run_status'], row['stage'], row['awaiting']), ('BLOCKED', 'stage0', ['company_context']))
        self.assertFalse(h.load_json(self.root/'runs/NEWX/run_manifest.json')['frozen'])
        h.dump_json(self.root/'.harness_inputs/NEWX/company_context.json', F.context_for('NEWX'))
        self.batch(only_started=True)
        row = self.row('NEWX')
        self.assertEqual(row['awaiting'], ['FP'])
        self.assertTrue((self.root/'runs/NEWX/FP_prompt.md').exists())
        self.assertIn('financial pack missing', row['blocked_reason'])
        # A context staged for another company or date is refused, not copied.
        other = F.context_for('OTHER')
        self.add('NEWY'); h.dump_json(self.root/'.harness_inputs/NEWY/company_context.json', other)
        self.batch(tickers=('NEWY',))
        self.assertIn('not NEWY', self.row('NEWY')['blocked_reason'])

    def test_agent_command_executor(self):
        outputs = self.root/'agent_outputs'
        reports = F.reports_for('triage_exit', 'CMDX')
        for aid, r in reports.items():
            h.dump_json(outputs/f'{aid}.json', r)
        h.dump_json(outputs/'FP.json', F.minimal_pack('CMDX'))
        (self.root/'fake_agent.py').write_text(
            'import shutil, sys\nagent, output, prompt = sys.argv[1:4]\n'
            'assert open(prompt, encoding="utf-8").read()\n'
            'shutil.copyfile(f"agent_outputs/{agent}.json", output)\n', encoding='utf-8')
        h.dump_json(self.root/'.harness_inputs/CMDX/company_context.json', F.context_for('CMDX'))
        self.add('CMDX')
        self.batch(agent_cmd=f'{sys.executable} fake_agent.py {{agent}} {{output}} {{prompt}}')
        row = self.row('CMDX')
        self.assertEqual((row['run_status'], row['early_exit']), ('COMPLETE', True))
        self.assertTrue(any(c.startswith('[agent-cmd] FP') for c in self.log_commands('CMDX')))
        self.assertTrue((self.root/'runs/CMDX/sources/financials/normalized_financials.json').exists())

    def test_stale_freeze_blocks_and_runner_never_refreezes(self):
        F.staged_inputs(self.root, 'STAL', 'complete', agents=['EV', 'AS', 'DI', 'FS'])
        self.add('STAL')
        self.batch(stop_after='triage')
        manifest = (self.root/'runs/STAL/run_manifest.json').read_bytes()
        code = self.root/'harness_core/conditions.py'
        code.write_text(code.read_text(encoding='utf-8') + '\n# policy edit\n', encoding='utf-8')
        self.batch()
        row = self.row('STAL')
        self.assertEqual(row['run_status'], 'BLOCKED')
        self.assertIn('stale freeze', row['blocked_reason'])
        self.assertEqual(manifest, (self.root/'runs/STAL/run_manifest.json').read_bytes())

    def test_git_batch_mode_commits_once_and_never_pushes(self):
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'base'],
                       cwd=self.root, check=True)
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        self.add('GOOS')
        with patch.dict('os.environ', {'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                                       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}):
            self.batch(git_mode='batch')
        log = subprocess.run(['git', 'log', '--format=%s'], cwd=self.root, capture_output=True, text=True).stdout.split('\n')
        self.assertTrue(log[0].startswith('universe: complete batch'))
        files = subprocess.run(['git', 'show', '--name-only', '--format=', 'HEAD'], cwd=self.root,
                               capture_output=True, text=True).stdout
        self.assertIn('runs/GOOS/final_verdict.json', files)
        self.assertNotIn('.harness_inputs', files)
        self.assertEqual(subprocess.run(['git', 'remote'], cwd=self.root, capture_output=True, text=True).stdout, '')


class NextActionTests(unittest.TestCase):
    statuses = POLICY['statuses']

    def art(self, **kw):
        base = {'exists': True, 'final': None, 'aggregate': None, 'ic_report': None, 'hashes': {},
                'freeze': {'frozen': True, 'config_current': True, 'inputs_current': True}}
        base.update(kw)
        return base

    def insp(self, stage, agents, control='continue'):
        return {'plan': {'stage': stage, 'agents': agents, 'execution_control': control}, 'error': None}

    def act(self, art, insp=None, stop=None):
        return U.determine_next_universe_action(art, insp, self.statuses, stop, ('EV',))

    def test_planner_is_authoritative_and_lead_agent_goes_first(self):
        triage = {'expectation_valuation': 'EV', 'asymmetry': 'AS', 'disruptive_innovation': 'DI', 'financial_survival': 'FS'}
        action = self.act(self.art(), self.insp('triage', triage))
        self.assertEqual((action['kind'], action['stage'], action['agents']), ('agents', 'ev', ['EV']))
        action = self.act(self.art(), self.insp('triage', {k: v for k, v in triage.items() if v != 'EV'}))
        self.assertEqual((action['stage'], action['agents']), ('triage', ['AS', 'DI', 'FS']))
        action = self.act(self.art(), self.insp('macro', {'macro_overlay': 'MO'}))
        self.assertEqual(action['agents'], ['MO'])

    def test_stop_boundary(self):
        action = self.act(self.art(), self.insp('domain_analysis', {'structural_leadership': 'SL'}), stop='triage')
        self.assertEqual(action['kind'], 'pause')
        action = self.act(self.art(), self.insp('triage', {'asymmetry': 'AS'}), stop='triage')
        self.assertEqual(action['kind'], 'agents')
        action = self.act(self.art(), self.insp('triage', {'expectation_valuation': 'EV'}), stop='stage0')
        self.assertEqual(action['kind'], 'pause')

    def test_lifecycle_actions(self):
        self.assertEqual(self.act({'exists': False})['kind'], 'init')
        self.assertEqual(self.act(self.art(freeze={'frozen': False}))['kind'], 'stage0')
        self.assertEqual(self.act(self.art(final={'early_exit': True}))['kind'], 'complete')
        self.assertEqual(self.act(self.art(), self.insp('early_exit', {}, 'stop_early'))['kind'], 'finalize')
        stale = self.act(self.art(freeze={'frozen': True, 'config_current': False, 'inputs_current': True}),
                         self.insp('triage', {'asymmetry': 'AS'}))
        self.assertEqual(stale['kind'], 'blocked')
        ic_pending = self.act(self.art(final={'ic_verdict': None}, ic_report={'analysis_status': 'complete'}))
        self.assertEqual(ic_pending['kind'], 'finalize')


class RunnerCliTests(RunnerCase):
    def test_cli_dry_run_and_triage_only(self):
        F.staged_inputs(self.root, 'GOOS', 'triage_exit')
        (self.root/'s.txt').write_text('GOOS\nNEWX\n', encoding='utf-8')

        def cli(*args):
            done = subprocess.run([sys.executable, 'harness.py', *args], cwd=self.root, capture_output=True,
                                  text=True, encoding='utf-8')
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            return done.stdout
        cli('universe', 'import-screen', 's.txt', '--as-of', F.AS_OF)
        out = cli('universe', 'run', '--dry-run')
        self.assertIn('2 tickers\n2 need Stage 0\n0 already triaged\n0 eligible for full core', out)
        self.assertFalse((self.root/'runs/GOOS').exists())
        out = cli('universe', 'run', '--triage-only', '--workers', '2')
        self.assertIn('GOOS', out)
        rows = json.loads((self.root/'universe/universe.json').read_text(encoding='utf-8'))['tickers']
        self.assertEqual(U.display_status(rows['GOOS']), 'EARLY_EXIT')
        self.assertEqual(rows['NEWX']['run_status'], 'BLOCKED')
        self.assertEqual(rows['GOOS']['sources'], ['stockanalysis_screenshot'])
        out = cli('universe', 'status', '--status', 'EARLY_EXIT')
        self.assertIn('GOOS', out)
        cli('universe', 'validate')


if __name__ == '__main__':
    unittest.main()
