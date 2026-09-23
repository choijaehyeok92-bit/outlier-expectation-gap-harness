"""Operator-supplied Stage 0 lock fields and the generic --agent-cmd wrapper."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_core import runtime as h, universe as U, universe_context as C
from harness_core.universe_runner import BatchRunner, Options
from harness_core.universe_store import RunReader, Store

import universe_fixtures as F

POLICY = json.loads((F.REPO/'config/universe.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(F.REPO/'scripts'))
import agent_cmd  # noqa: E402


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        F.copy_harness(self.root)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def add(self, *tickers):
        accepted, _, _ = U.normalize_entries([{'raw': t} for t in tickers], POLICY['import'])
        with Store(self.root).transaction() as universe:
            U.merge_import(universe, accepted, F.AS_OF, 'test', 'now', RunReader(h).run_as_of)

    def cli(self, *args, ok=True):
        done = subprocess.run([sys.executable, 'harness.py', *args], cwd=self.root, capture_output=True,
                              text=True, encoding='utf-8')
        self.assertEqual(done.returncode == 0, ok, done.stdout + done.stderr)
        return done.stdout

    def test_parse_values(self):
        values, errors = C.parse_values({'current_price': '1,164.89', 'net_cash_per_share': '-47.1', 'currency': 'USD'})
        self.assertEqual((values, errors), ({'current_price': 1164.89, 'net_cash_per_share': -47.1, 'currency': 'USD'}, []))
        for raw, needle in (({'net_cash_per_share': '1'}, 'missing current_price'),
                            ({'current_price': '-1', 'net_cash_per_share': '0'}, 'must be positive'),
                            ({'current_price': 'n/a', 'net_cash_per_share': '0'}, 'not a number'),
                            ({'current_price': 'nan', 'net_cash_per_share': '0'}, 'not finite')):
            self.assertTrue(any(needle in e for e in C.parse_values(raw)[1]), raw)

    def test_template_then_import_reaches_freeze(self):
        F.build('complete', 'LLYX')                     # frozen, complete: never offered, never edited
        self.add('LLYX', 'NEWX', 'SPY')
        h.dump_json(self.root/'.harness_inputs/NEWX/sources/financials/normalized_financials.json', F.minimal_pack('NEWX'))
        BatchRunner(Store(self.root), RunReader(h), Options()).run()   # NEWX: init, then blocked on lock fields
        self.assertEqual(Store(self.root).load()['tickers']['NEWX']['awaiting'], ['company_context'])
        self.cli('universe', 'context', '--template', 'ctx.csv')
        lines = (self.root/'ctx.csv').read_text(encoding='utf-8').splitlines()
        self.assertEqual([l.split(',')[0] for l in lines], ['ticker', 'NEWX'])  # not LLYX (complete), not SPY (ETF)
        (self.root/'ctx.csv').write_text(lines[0] + '\nNEWX,2026-09-19,100,5,1000000000,100000000000,USD,New Co\n',
                                         encoding='utf-8')
        out = self.cli('universe', 'context', 'ctx.csv', '--source', 'broker close 2026-09-19')
        self.assertIn('WRITTEN  runs/NEWX/company_context.json', out)
        context = h.load_json(self.root/'runs/NEWX/company_context.json')
        self.assertEqual((context['current_price'], context['net_cash_per_share'], context['ticker']), (100.0, 5.0, 'NEWX'))
        self.assertIn('broker close 2026-09-19', context['known_sources'])
        BatchRunner(Store(self.root), RunReader(h), Options(only_started=True, stop_after='stage0')).run()
        self.assertTrue(h.load_json(self.root/'runs/NEWX/run_manifest.json')['frozen'])

    def test_staged_when_no_run_and_frozen_is_refused(self):
        F.build('complete', 'LLYX')
        self.add('NEWX', 'LLYX')
        self.cli('universe', 'context', '--ticker', 'NEWX', '--price', '50', '--net-cash-per-share', '0')
        staged = h.load_json(self.root/'.harness_inputs/NEWX/company_context.json')
        self.assertEqual((staged['ticker'], staged['as_of_date'], staged['current_price']), ('NEWX', F.AS_OF, 50.0))
        before = (self.root/'runs/LLYX/company_context.json').read_bytes()
        out = self.cli('universe', 'context', '--ticker', 'LLYX', '--price', '1', '--net-cash-per-share', '0', ok=False)
        self.assertIn('is frozen', out)
        self.assertEqual(before, (self.root/'runs/LLYX/company_context.json').read_bytes())
        self.cli('universe', 'context', '--ticker', 'NEWX', '--price', '-5', '--net-cash-per-share', '0', ok=False)


class AgentCmdWrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.root/'prompt.md').write_text('prompt', encoding='utf-8')

    def fake_model(self, body):
        path = self.root/'model.py'
        path.write_text(body, encoding='utf-8')
        return [sys.executable, str(path)]

    def run_wrapper(self, command):
        out = self.root/'out'/'EV.json'
        code = agent_cmd.main(['--prompt', str(self.root/'prompt.md'), '--output', str(out), '--', *command])
        return code, out

    def test_json_from_stdout_is_written_verbatim(self):
        command = self.fake_model('import sys; sys.stdin.read(); print("Done.\\n```json\\n{\\"agent_id\\": \\"EV\\", \\"x\\": 1}\\n```")')
        code, out = self.run_wrapper(command)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.read_text(encoding='utf-8')), {'agent_id': 'EV', 'x': 1})

    def test_file_written_by_model_is_kept_and_missing_json_fails(self):
        target = self.root/'out'/'EV.json'
        command = self.fake_model(f'import sys, pathlib; sys.stdin.read(); p = pathlib.Path(r"{target}"); '
                                  'p.parent.mkdir(parents=True, exist_ok=True); p.write_text("{\\"own\\": true}"); print("{\\"other\\": 1}")')
        code, out = self.run_wrapper(command)
        self.assertEqual((code, json.loads(out.read_text(encoding='utf-8'))), (0, {'own': True}))
        out.unlink()
        code, out = self.run_wrapper(self.fake_model('import sys; sys.stdin.read(); print("no report here")'))
        self.assertEqual(code, 3)
        self.assertFalse(out.exists())

    def test_runner_through_wrapper(self):
        with patch.object(h, 'ROOT', self.root):
            F.copy_harness(self.root)
            (self.root/'scripts').mkdir(exist_ok=True)
            (self.root/'scripts/agent_cmd.py').write_text((F.REPO/'scripts/agent_cmd.py').read_text(encoding='utf-8'),
                                                          encoding='utf-8')
            reports = F.reports_for('triage_exit', 'WRPX')
            (self.root/'answers').mkdir()
            for aid, r in reports.items():
                (self.root/'answers'/f'{aid}.json').write_text(json.dumps(r), encoding='utf-8')
            (self.root/'answers/FP.json').write_text(json.dumps(F.minimal_pack('WRPX')), encoding='utf-8')
            # A stand-in model CLI: reads the prompt on stdin, answers with a fenced JSON block.
            (self.root/'model.py').write_text(
                'import os, sys\nsys.stdin.read()\n'
                'print("```json\\n" + open(f"answers/{os.environ[\'HARNESS_AGENT\']}.json").read() + "\\n```")\n',
                encoding='utf-8')
            h.dump_json(self.root/'.harness_inputs/WRPX/company_context.json', F.context_for('WRPX'))
            accepted, _, _ = U.normalize_entries([{'raw': 'WRPX'}], POLICY['import'])
            with Store(self.root).transaction() as universe:
                U.merge_import(universe, accepted, F.AS_OF, 'test', 'now', RunReader(h).run_as_of)
            cmd = f'{sys.executable} scripts/agent_cmd.py --prompt {{prompt}} --output {{output}} -- {sys.executable} model.py'
            BatchRunner(Store(self.root), RunReader(h), Options(agent_cmd=cmd)).run()
            row = Store(self.root).load()['tickers']['WRPX']
            self.assertEqual((row['run_status'], row['early_exit']), ('COMPLETE', True), row.get('last_error'))


if __name__ == '__main__':
    unittest.main()
