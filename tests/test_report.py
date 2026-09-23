"""Report Agent (RP): the deep report explains the recorded verdict and can never change it."""
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_core import runtime as h, report_builder as B, report_validator as V
from harness_core.universe_store import RunReader

import universe_fixtures as F

POLICY = json.loads((F.REPO/'config/universe.json').read_text(encoding='utf-8'))['report_policy']


class ReportCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        F.copy_harness(self.root)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def write(self, run_id, force=False):
        return B.write_deep_report(h, run_id, force=force, reader=RunReader(h), now='2026-09-20T00:00:00+00:00')

    def load(self, run_id):
        run = self.root/'runs'/run_id
        return h.load_json(run/'deep_report.json'), (run/'deep_report.md').read_text(encoding='utf-8'), \
            h.load_json(run/'final_verdict.json')

    def findings(self, run_id, level='ERROR'):
        return [m for lvl, m in V.validate_run_report(h, run_id, RunReader(h)) if lvl == level]

    def set_ic(self, run_id, state):
        run = self.root/'runs'/run_id
        report = h.load_json(run/'reports/IC.json'); report['ic_state'] = state
        h.dump_json(run/'reports/IC.json', report)
        F.aggregate(run_id)


class ReportAuthorityTests(ReportCase):
    def test_report_authority(self):
        F.build('complete', 'LLYX')
        result = self.write('LLYX')
        self.assertEqual((result['status'], result['tier']), ('COMPLETE', 'full'))
        context, markdown, final = self.load('LLYX')
        auth = context['authority']
        self.assertEqual((auth['score_100'], auth['archetype'], auth['hard_veto_status'], auth['ic_state'],
                          auth['position_range'], auth['macro_pacing_multiplier']),
                         (final['score_100'], final['archetype'], final['hard_veto_status'], final['ic_state'],
                          final['position_range'], final['macro_pacing_multiplier']))
        self.assertEqual(auth['valuation']['base'], final['valuation_model']['scenarios']['base']['value_per_share'])
        self.assertEqual([s['id'] for s in context['sections']], [f'{i:02d}' for i in range(22)])
        self.assertEqual(B.parse_authority(markdown), json.loads(json.dumps(auth, sort_keys=True)))
        self.assertIn('| IC State | STARTER |', markdown)
        self.assertIn('This report is valid only for the frozen snapshot dated 2026-09-19', markdown)
        self.assertEqual(context['authority_sources']['final_verdict']['path'], 'runs/LLYX/final_verdict.json')
        # Every table row and every quotation carries its provenance.
        for section in context['sections']:
            for block in section['blocks']:
                if block['type'] == 'kv':
                    self.assertTrue(all(row[2] for row in block['rows']), section['id'])
                if block['type'] in ('quote', 'list', 'table'):
                    self.assertTrue(block.get('source'), (section['id'], block))
        self.assertEqual(self.findings('LLYX'), [])
        self.assertEqual(self.findings('LLYX', 'WARNING'), [])

    def test_report_cannot_raise_position(self):
        F.build('complete', 'LLYX', ic_state='EXCEPTIONAL_WINNER')          # above the mechanical cap
        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        self.assertNotEqual(final['ic_state'], 'EXCEPTIONAL_WINNER')        # the harness refused it
        self.assertTrue(final['ic_review_flags'])
        self.write('LLYX', force=True)
        context, markdown, final = self.load('LLYX')
        self.assertEqual(context['authority']['ic_state'], final['ic_state'])
        self.assertEqual(context['authority']['position_range'], final['position_range'])
        self.assertNotIn('| IC State | EXCEPTIONAL_WINNER |', markdown)
        self.assertIn('IC 요청 거부', markdown)
        # Editing the report to show a larger position is caught, in the JSON and in the markdown.
        run = self.root/'runs/LLYX'
        tampered = dict(context); tampered['authority'] = {**context['authority'], 'position_range': '6-10% (IC cap)'}
        h.dump_json(run/'deep_report.json', tampered)
        self.assertTrue(any('position_range' in e for e in self.findings('LLYX')))
        h.dump_json(run/'deep_report.json', context)
        (run/'deep_report.md').write_text(markdown.replace(f"| Position Range | {final['position_range']} |",
                                                           '| Position Range | 6-10% (IC cap) |'), encoding='utf-8')
        self.assertTrue(any('shows Position Range' in e for e in self.findings('LLYX')))
        # And a context that disagrees with the verdict is never written in the first place.
        bad = {**context, 'authority': {**context['authority'], 'ic_state': 'CORE_WINNER'}}
        errors = [m for lvl, m in V.validate_deep_report(bad, B.render_markdown(bad), final, h.STATE_POLICY) if lvl == 'ERROR']
        self.assertTrue(any('ic_state' in e for e in errors))

    def test_report_matches_final_verdict(self):
        F.build('complete', 'LLYX')
        self.write('LLYX')
        self.set_ic('LLYX', 'WATCH')                                         # the verdict changes later
        errors = self.findings('LLYX')
        self.assertTrue(any("ic_state 'STARTER' != final_verdict 'WATCH'" in e for e in errors), errors)
        self.assertTrue(any('changed after the deep report' in w for w in self.findings('LLYX', 'WARNING')))
        self.write('LLYX')                                                   # regenerating restores agreement
        self.assertEqual(self.findings('LLYX'), [])
        self.assertEqual(self.load('LLYX')[0]['tier'], 'concise')

    def test_report_tiering(self):
        F.build('triage_exit', 'GOOX')
        self.assertEqual(self.write('GOOX')['status'], 'NONE')
        self.assertFalse((self.root/'runs/GOOX/deep_report.md').exists())
        forced = self.write('GOOX', force=True)
        self.assertEqual((forced['status'], forced['tier']), ('COMPLETE', 'full'))
        context, markdown, _ = self.load('GOOX')
        self.assertTrue(context['forced'])
        self.assertIn('조기 종료 또는 미실행', markdown)                     # missing domains are not invented
        F.build('complete', 'WATX', ic_state='WATCH')
        self.assertEqual(self.write('WATX')['tier'], 'concise')
        self.assertEqual([s['id'] for s in self.load('WATX')[0]['sections']], POLICY['tier_sections']['concise'])
        F.build('complete', 'REJX', ic_state='REJECT')
        self.assertEqual(self.write('REJX')['tier'], 'summary')
        self.assertEqual([s['id'] for s in self.load('REJX')[0]['sections']], POLICY['tier_sections']['summary'])
        F.build('triaged', 'INCX')
        self.assertEqual(self.write('INCX')['reason'], 'IC report not complete')

    def test_existing_run_mode_never_recomputes(self):
        F.build('complete', 'LLYX')
        code = self.root/'harness_core/conditions.py'                        # the freeze goes stale
        code.write_text(code.read_text(encoding='utf-8') + '\n# later harness\n', encoding='utf-8')
        run = self.root/'runs/LLYX'
        before = {p: p.read_bytes() for p in run.rglob('*') if p.is_file()}
        args = argparse.Namespace(ticker='LLYX', subject=None, existing_run=False, force=False, prompt=False, out=None)
        with self.assertRaises(SystemExit) as refused:
            F.quiet(B.cmd_report_entry, args)
        self.assertIn('--existing-run', str(refused.exception))
        args.existing_run = True
        F.quiet(B.cmd_report_entry, args)
        after = {p: p.read_bytes() for p in run.rglob('*') if p.is_file()}
        self.assertEqual({p for p in after if p not in before}, {run/'deep_report.json', run/'deep_report.md'})
        self.assertTrue(all(after[p] == b for p, b in before.items()), 'no recorded artifact may change')
        context = self.load('LLYX')[0]
        self.assertFalse(context['freeze']['config_current'])
        self.assertIn('기록된 판정을 그대로 설명한다', (run/'deep_report.md').read_text(encoding='utf-8'))

    def test_financial_methodology_is_quoted_not_replaced(self):
        F.build('complete', 'BANKX')
        path = self.root/'runs/BANKX/final_verdict.json'
        final = h.load_json(path)
        final['valuation_model']['method'] = 'locked owner-FCF/share DCF using bank-specific distributable owner-earnings/share proxy'
        h.dump_json(path, final)
        self.write('BANKX')
        self.assertIn('bank-specific distributable owner-earnings/share proxy',
                      (self.root/'runs/BANKX/deep_report.md').read_text(encoding='utf-8'))


class NarrativeTests(ReportCase):
    def narrative(self, run_id, text, sources=None, **extra):
        payload = {'ticker': run_id, 'as_of_date': F.AS_OF,
                   'sections': {'02': {'text': text, 'sources': sources or [f'runs/{run_id}/reports/SL.json#thesis']}}}
        payload.update(extra)
        h.dump_json(self.root/'runs'/run_id/'deep_report_narrative.json', payload)

    def test_valid_narrative_is_merged_and_invented_numbers_rejected(self):
        F.build('complete', 'LLYX')
        final = h.load_json(self.root/'runs/LLYX/final_verdict.json')
        self.narrative('LLYX', f"SL thesis explains the structural shift; the recorded score is {final['score_100']} in 2026.")
        result = self.write('LLYX')
        self.assertEqual(result['status'], 'COMPLETE')
        context, markdown, _ = self.load('LLYX')
        self.assertEqual(context['narrative']['status'], 'merged')
        self.assertIn('RP 서술', markdown)
        self.assertEqual(self.findings('LLYX'), [])
        for text, needle in (('A fair value of 4,321.5 per share is likely.', 'does not appear'),
                             ('Our target price is well above Base.', 'forbidden phrase'),
                             ('This is a Top Pick for the portfolio.', 'forbidden phrase')):
            self.narrative('LLYX', text)
            result = self.write('LLYX')
            self.assertEqual(result['status'], 'COMPLETE_NARRATIVE_REJECTED')
            self.assertTrue(any(needle in e for e in result['narrative_errors']), (text, result['narrative_errors']))
            self.assertEqual(self.load('LLYX')[0]['narrative']['status'], 'rejected')
            self.assertNotIn(text, (self.root/'runs/LLYX/deep_report.md').read_text(encoding='utf-8').split('RP narrative was rejected')[0])

    def test_narrative_cannot_carry_decision_fields_or_foreign_sources(self):
        F.build('complete', 'LLYX')
        bundle = B.load_bundle(h, 'LLYX')
        context = {'ticker': 'LLYX', 'run_id': 'LLYX', 'as_of_date': F.AS_OF, 'derived': {}}
        bad = {'ticker': 'LLYX', 'as_of_date': F.AS_OF, 'ic_state': 'CORE_WINNER',
               'sections': {'19': {'text': 'Position explained.', 'sources': ['runs/OTHER/final_verdict.json'],
                                   'position_range': '6-8%'}}}
        errors = V.validate_narrative(bad, bundle, context, POLICY['narrative'])
        self.assertTrue(any('unexpected top-level keys' in e for e in errors))
        self.assertTrue(any('decision fields are not narrative' in e for e in errors))
        self.assertTrue(any('not a recorded artifact' in e for e in errors))

    def test_rp_prompt(self):
        F.build('complete', 'LLYX')
        text = B.rp_prompt(h, 'LLYX')
        self.assertIn('deep_research_report (RP)', text)
        self.assertIn('runs/LLYX/deep_report_narrative.json', text)
        self.assertIn('절대 변경하지 않는 것', text)


class ReportCliTests(ReportCase):
    def cli(self, *args, ok=True):
        done = subprocess.run([sys.executable, 'harness.py', *args], cwd=self.root, capture_output=True,
                              text=True, encoding='utf-8')
        if ok:
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        else:
            self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout + done.stderr

    def test_report_cli_and_universe_report(self):
        F.build('complete', 'LLYX'); F.build('triage_exit', 'GOOX')
        out = self.cli('report', 'LLYX')                                     # legacy + deep report
        self.assertTrue((self.root/'runs/LLYX/easy_report.md').exists())
        self.assertIn('deep report (full)', out)
        self.assertIn('0 error(s)', self.cli('report', 'validate', 'LLYX'))
        md = self.root/'runs/LLYX/deep_report.md'
        md.write_text(md.read_text(encoding='utf-8').replace('| IC State | STARTER |', '| IC State | NORMAL |'), encoding='utf-8')
        self.assertIn('shows IC State', self.cli('report', 'validate', 'LLYX', ok=False))
        self.cli('report', 'LLYX', '--prompt')
        self.assertTrue((self.root/'runs/LLYX/RP_prompt.md').exists())
        self.assertIn('none (early exit', self.cli('report', 'GOOX'))
        (self.root/'s.txt').write_text('LLYX\nGOOX\nNEWX\n', encoding='utf-8')
        self.cli('universe', 'import', 's.txt', '--as-of', F.AS_OF)
        out = self.cli('universe', 'report', '--existing-runs')
        self.assertIn('1 deep report(s) written, 1 not required by tier, 1 not complete', out)
        rows = json.loads((self.root/'universe/universe.json').read_text(encoding='utf-8'))['tickers']
        self.assertEqual((rows['LLYX']['report_status'], rows['LLYX']['report_tier']), ('COMPLETE', 'full'))
        self.assertEqual(rows['GOOX']['report_status'], 'NONE')
        self.cli('universe', 'validate')
        md.write_text(md.read_text(encoding='utf-8').replace('| IC State | STARTER |', '| IC State | NORMAL |'), encoding='utf-8')
        self.assertIn('shows IC State', self.cli('universe', 'validate', ok=False))


if __name__ == '__main__':
    unittest.main()
