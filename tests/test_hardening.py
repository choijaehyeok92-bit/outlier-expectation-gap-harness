"""v3.2.1 hardening invariants.

Three failure modes that all read as "approved" unless something pins them down:
a veto cleared or confirmed by an agent who does not own it, a fact whose age
cannot be established slipping into the verified catalog, and a company context
frozen with a price, cutoff or scenario spread that the later stages cannot
mean anything sensible with.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from harness_core import runtime as h, context, research
from harness_core.veto import veto_gate

REPO = h.ROOT
VETO = h.VETOES[0]
OWNERS = h.VETO_REVIEWERS[VETO]


def flag(veto, status, rationale='Fixture'):
    return {'veto': veto, 'status': status, 'rationale': rationale}


def stranger(veto):
    """An agent that is not an owner of this veto but does own another one."""
    return next(aid for aid, owned in
                ((a['agent_id'], [v for v, ids in h.VETO_REVIEWERS.items() if a['agent_id'] in ids])
                 for a in h.MANIFEST)
                if owned and aid not in h.VETO_REVIEWERS[veto])


class HardVetoOwnershipTests(unittest.TestCase):
    """Only an owner ends the question; everyone else can only raise it."""

    def setUp(self):
        self.reports = {}
        for veto, owners in h.VETO_REVIEWERS.items():
            for aid in owners:
                report = self.reports.setdefault(aid, {'agent_id': aid, 'analysis_status': 'complete',
                                                       'hard_veto_flags': []})
                report['hard_veto_flags'].append(flag(veto, 'cleared'))
        self.outsider = stranger(VETO)

    def gate(self, reports=None):
        return veto_gate(list((reports if reports is not None else self.reports).values()), h.VETOES,
                         h.VETO_REVIEWERS)

    def item(self, result, veto=VETO):
        return next(row for row in result['items'] if row['veto'] == veto)

    def add(self, agent_id, status, veto=VETO, rationale='Fixture'):
        reports = copy.deepcopy(self.reports)
        reports.setdefault(agent_id, {'agent_id': agent_id, 'analysis_status': 'complete',
                                      'hard_veto_flags': []})
        reports[agent_id]['hard_veto_flags'].append(flag(veto, status, rationale))
        return reports

    def test_every_owner_clearing_is_the_only_route_to_cleared(self):
        result = self.gate()
        self.assertEqual(result['overall'], 'CLEARED')
        self.assertEqual(self.item(result)['status'], 'CLEARED')
        self.assertEqual(result['non_owner_escalations'], [])

    def test_a_non_owner_never_confirms_but_always_escalates(self):
        for status in ('candidate', 'conditional', 'confirmed'):
            with self.subTest(status=status):
                result = self.gate(self.add(self.outsider, status))
                row = self.item(result)
                self.assertEqual(row['status'], 'UNRESOLVED')
                self.assertEqual(result['overall'], 'UNRESOLVED')
                self.assertEqual(result['confirmed'], [])
                self.assertIn(row, result['unresolved'])

    def test_the_non_owner_finding_is_preserved_not_discarded(self):
        result = self.gate(self.add(self.outsider, 'confirmed', rationale='Restatement in the 10-K/A'))
        row = self.item(result)
        self.assertEqual([x['agent_id'] for x in row['non_owner_escalations']], [self.outsider])
        self.assertEqual(row['non_owner_escalations'][0]['rationale'], 'Restatement in the 10-K/A')
        self.assertEqual([x['veto'] for x in result['non_owner_escalations']], [VETO])
        self.assertEqual(result['non_owner_escalations'][0]['status'], 'confirmed')

    def test_a_non_owner_clearing_is_not_an_escalation_and_cannot_clear(self):
        reports = self.add(self.outsider, 'cleared')
        reports[OWNERS[0]]['hard_veto_flags'] = [f for f in reports[OWNERS[0]]['hard_veto_flags']
                                                 if f['veto'] != VETO]
        result = self.gate(reports)
        row = self.item(result)
        self.assertEqual(row['status'], 'UNRESOLVED')
        self.assertEqual(row['non_owner_escalations'], [])
        self.assertEqual(row['missing_assessments'], [OWNERS[0]])

    def test_an_owner_confirming_still_confirms_and_outranks_an_escalation(self):
        for extra in ((), (self.outsider,)):
            with self.subTest(also_flagged_by=extra):
                reports = self.add(extra[0], 'candidate') if extra else copy.deepcopy(self.reports)
                owner_flag = next(f for f in reports[OWNERS[0]]['hard_veto_flags'] if f['veto'] == VETO)
                owner_flag['status'] = 'confirmed'
                result = self.gate(reports)
                self.assertEqual(result['overall'], 'CONFIRMED')
                self.assertEqual(self.item(result)['status'], 'CONFIRMED')
                self.assertIn(self.item(result), result['confirmed'])

    def test_silence_from_an_owner_is_never_clearance(self):
        absent = copy.deepcopy(self.reports)
        del absent[OWNERS[0]]
        row = self.item(self.gate(absent))
        self.assertEqual(row['status'], 'PENDING_REVIEW')
        self.assertEqual(row['missing_reports'], [OWNERS[0]])

        unfinished = copy.deepcopy(self.reports)
        unfinished[OWNERS[0]]['analysis_status'] = 'pending'
        self.assertEqual(self.item(self.gate(unfinished))['missing_reports'], [OWNERS[0]])

        silent = copy.deepcopy(self.reports)
        silent[OWNERS[0]]['hard_veto_flags'] = [f for f in silent[OWNERS[0]]['hard_veto_flags']
                                                if f['veto'] != VETO]
        self.assertEqual(self.item(self.gate(silent))['status'], 'UNRESOLVED')

    def test_an_escalation_on_one_veto_leaves_the_others_alone(self):
        result = self.gate(self.add(self.outsider, 'confirmed'))
        others = [row['status'] for row in result['items'] if row['veto'] != VETO]
        self.assertEqual(set(others), {'CLEARED'})


class VerifiedCatalogDateTests(unittest.TestCase):
    """A fact whose age cannot be established is not a verified fact."""

    CUTOFF = '2026-09-19'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name)
        h.dump_json(self.run/'company_context.json', {'ticker': 'TEST', 'as_of_date': self.CUTOFF})
        h.dump_json(self.run/'sources/financials/qa_report.json', {})

    def catalog(self, fact_date, document_date='2026-08-01', source_document='annual.htm'):
        pack = {'documents': [{'document_id': 'DOC-001', 'source_document': 'annual.htm',
                              'document_type': '10-K', 'filing_date': document_date}],
                'facts': [{'fact_id': 'FACT-0001', 'value_reported': 42, 'requires_review': False,
                           'filing_date': fact_date, 'source_document': source_document}]}
        h.dump_json(self.run/h.FINANCIAL_PACK, pack)
        return research.verified_catalog(self.run)

    def test_a_null_filing_date_falls_back_to_the_document(self):
        self.assertEqual(self.catalog(None)['normalized:FACT-0001'], 42)

    def test_an_absent_filing_date_falls_back_to_the_document(self):
        pack = {'documents': [{'document_id': 'DOC-001', 'source_document': 'annual.htm',
                              'filing_date': '2026-08-01'}],
                'facts': [{'fact_id': 'FACT-0001', 'value_reported': 42, 'requires_review': False,
                           'source_document': 'annual.htm'}]}
        h.dump_json(self.run/h.FINANCIAL_PACK, pack)
        self.assertIn('normalized:FACT-0001', research.verified_catalog(self.run))

    def test_the_fallback_still_obeys_the_cutoff(self):
        self.assertNotIn('normalized:FACT-0001', self.catalog(None, document_date='2026-09-20'))

    def test_a_fact_with_no_usable_date_anywhere_is_excluded_not_dated(self):
        for case in ({'fact_date': None, 'document_date': None},
                     {'fact_date': None, 'source_document': 'unlisted.htm'},
                     {'fact_date': None, 'document_date': 'not-a-date'}):
            with self.subTest(**case):
                self.assertNotIn('normalized:FACT-0001', self.catalog(**case))

    def test_a_malformed_fact_date_is_excluded_rather_than_papered_over(self):
        for bad in ('2026-13-45', '20260801', '', 'unknown'):
            with self.subTest(filing_date=bad):
                self.assertNotIn('normalized:FACT-0001', self.catalog(bad))

    def test_a_document_match_by_document_id_also_works(self):
        self.assertIn('normalized:FACT-0001', self.catalog(None, source_document='DOC-001'))

    def test_the_context_half_of_the_catalog_is_unaffected(self):
        self.assertEqual(self.catalog(None)['context:ticker'], 'TEST')


class FreezeContextValidationTests(unittest.TestCase):
    """The context is checked once, where it is locked."""

    SCHEMA = h.load_json(REPO/'schemas/company_context.schema.json')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('schemas', 'templates'):
            shutil.copytree(REPO/directory, self.root/directory)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start(); self.addCleanup(patcher.stop)
        self.context = {'ticker': 'HARDEN', 'as_of_date': '2026-09-19', 'currency': 'USD',
                        'current_price': 100, 'net_cash_per_share': 5, 'market_cap_usd': 100e9}
        self.manifest = {'ticker': 'HARDEN', 'as_of_date': '2026-09-19'}

    def errors(self, **overrides):
        ctx = {**copy.deepcopy(self.context), **overrides}
        return context.validate(ctx, 'HARDEN', self.manifest, self.SCHEMA, h.VAL_POLICY)

    def assertRejects(self, needle, **overrides):
        problems = self.errors(**overrides)
        self.assertTrue(problems, f'{overrides} was accepted')
        self.assertTrue(any(needle in p for p in problems), problems)

    def test_a_locked_context_passes(self):
        self.assertEqual(self.errors(), [])

    def test_the_price_must_be_a_real_positive_price(self):
        for price in (0, -1, None, '100'):
            with self.subTest(current_price=price):
                self.assertRejects('current_price', current_price=price)
        del self.context['current_price']
        self.assertRejects('current_price')

    def test_the_cutoff_must_be_a_real_calendar_date(self):
        for value in ('2026-02-30', '2026-13-01', '20260919', '2026-9-19', 'yesterday'):
            with self.subTest(as_of_date=value):
                self.manifest['as_of_date'] = value       # isolate the format error from the drift check
                self.assertRejects('as_of_date', as_of_date=value)

    def test_the_required_return_must_discount(self):
        for rate in (0, -0.08, 1.5, 'high'):
            with self.subTest(required_return=rate):
                self.assertRejects('required_return',
                                   valuation_overrides={'required_return': rate, 'terminal_multiples': {}})
        self.assertEqual(self.errors(valuation_overrides={'required_return': 0.09,
                                                          'terminal_multiples': {}}), [])

    def test_terminal_multiples_are_non_negative(self):
        self.assertRejects('terminal_multiples',
                           valuation_overrides={'terminal_multiples': {'bear': -1, 'base': 20, 'bull': 30}})

    def test_scenario_multiples_must_not_invert(self):
        for spread in ({'bear': 25, 'base': 20, 'bull': 30}, {'bear': 10, 'base': 40, 'bull': 30}):
            with self.subTest(**spread):
                self.assertRejects('must not invert',
                                   valuation_overrides={'terminal_multiples': spread})
        self.assertEqual(self.errors(valuation_overrides={'terminal_multiples':
                                                          {'bear': 10, 'base': 20, 'bull': 30}}), [])

    def test_a_partial_override_is_checked_against_the_policy_it_merges_into(self):
        policy_base = h.VAL_POLICY['terminal_multiples']['base']
        self.assertRejects('must not invert', valuation_overrides={
            'terminal_multiples': {'bear': policy_base + 5, 'base': None, 'bull': None}})

    def test_the_context_must_name_this_run(self):
        self.assertRejects('ticker', ticker='NVDA')

    def test_a_forked_run_may_still_carry_its_source_ticker(self):
        """fork-run copies inputs byte for byte on purpose, so the snapshot stays comparable."""
        forked = context.validate({**self.context, 'ticker': 'SOURCE'}, 'HARDEN',
                                  {**self.manifest, 'lineage': {'source_run': 'SOURCE'}},
                                  self.SCHEMA, h.VAL_POLICY)
        self.assertEqual(forked, [])
        self.assertTrue(context.validate({**self.context, 'ticker': 'OTHER'}, 'HARDEN',
                                         {**self.manifest, 'lineage': {'source_run': 'SOURCE'}},
                                         self.SCHEMA, h.VAL_POLICY))

    def test_the_cutoff_cannot_move_after_init(self):
        self.assertRejects('cannot move', as_of_date='2026-09-20')

    # --- end to end ---------------------------------------------------------

    def freeze(self, run_id='HARDEN', ctx=None):
        h.cmd_init(SimpleNamespace(ticker=run_id, as_of='2026-09-19'))
        run = h.run_dir(run_id)
        manifest = h.load_json(run/'run_manifest.json')
        manifest['financial_pack_required'] = False           # stage 0 is not what is under test here
        h.dump_json(run/'run_manifest.json', manifest)
        locked = h.load_json(run/'company_context.json')
        locked.update({'current_price': 100, 'net_cash_per_share': 5, **(ctx or {})})
        h.dump_json(run/'company_context.json', locked)
        h.cmd_freeze(SimpleNamespace(ticker=run_id, provider='openai', model='m', reasoning_effort=None))
        return run

    def test_freeze_accepts_a_sound_context_and_refuses_an_unsound_one(self):
        with patch('sys.stdout'):
            run = self.freeze()
        self.assertTrue(h.load_json(run/'run_manifest.json')['frozen'])
        for label, bad in (('price', {'current_price': 0}),
                           ('cutoff', {'as_of_date': '2026-10-01'}),
                           ('ticker', {'ticker': 'NVDA'}),
                           ('spread', {'valuation_overrides': {'required_return': None,
                                       'terminal_multiples': {'bear': 30, 'base': 20, 'bull': 40}}})):
            with self.subTest(label), patch('sys.stdout'):
                with self.assertRaises(SystemExit) as caught:
                    self.freeze(f'HARDEN{label.upper()}', bad)
                self.assertIn('not fit to freeze', str(caught.exception))
                self.assertFalse(h.load_json(h.run_dir(f'HARDEN{label.upper()}')/'run_manifest.json')['frozen'])

    def test_an_already_frozen_run_stays_readable_when_its_context_would_now_be_refused(self):
        with patch('sys.stdout'):
            run = self.freeze()
        legacy = h.load_json(run/'company_context.json')
        legacy['ticker'] = 'RENAMED_LONG_AGO'          # a shape today's freeze would reject
        h.dump_json(run/'company_context.json', legacy)
        self.assertEqual(h.load_json(run/'company_context.json')['ticker'], 'RENAMED_LONG_AGO')
        self.assertEqual(research.verified_catalog(run)['context:ticker'], 'RENAMED_LONG_AGO')
        self.assertFalse(h.intake_status('HARDEN')['blocking'])
        with patch.object(context, 'validate', side_effect=AssertionError('read paths must not validate')):
            self.assertTrue(h.load_reports('HARDEN'))
            research.verified_catalog(run)


if __name__ == '__main__':
    unittest.main()
