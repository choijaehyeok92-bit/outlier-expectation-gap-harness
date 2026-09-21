"""Dilution decision semantics: score, then watch, then Hard Veto.

The four cases below are the ones the old two-layer design got wrong. A healthy
early-stage dilution and a structural one were indistinguishable, because the
only place to put "material but not established" was the veto, where it read as
UNRESOLVED and blocked a buy.
"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness_core import dilution, runtime as h
# Imported as a module, never by name: unittest collects every TestCase bound in
# a module's namespace, so a direct import would run that suite a second time.
import test_v3

VETO = h.DILUTION_VETO
DEFINITION = h.VETO_CRITERIA['definitions'][VETO]
ELEMENTS = DEFINITION['elements']
OWNERS = h.VETO_REVIEWERS[VETO]


def flag(status, met=None, decisive=None, rationale='Fixture'):
    row = {'veto': VETO, 'status': status, 'rationale': rationale}
    if met is not None:
        row['elements_met'] = {element: met[i] for i, element in enumerate(ELEMENTS)}
    if decisive is not None:
        row['decisive_missing_evidence'] = decisive
    return row


class ConfigTests(unittest.TestCase):
    """Thresholds are declared, not spelled into Python."""

    def test_the_veto_declares_four_elements_and_its_thresholds(self):
        self.assertEqual(len(ELEMENTS), 4)
        self.assertTrue(DEFINITION['requires_element_assessment'])
        for key in ('multi_year_min_years', 'three_year_diluted_share_cagr',
                    'three_year_cumulative_dilution'):
            self.assertIn(key, DEFINITION['thresholds'])
        self.assertEqual([p['priority'] for p in DEFINITION['per_share_value_proxies']], [1, 2, 3, 4])
        self.assertEqual(DEFINITION['per_share_value_proxies'][0]['proxy'], 'owner_fcf_per_share')

    def test_no_dilution_threshold_is_hardcoded_in_python(self):
        """Every fractional threshold must live in config, not in a module.

        Integer thresholds such as multi_year_min_years are too generic to test
        for this way — a bare 2 appears in any file — so the check covers the
        fractional ones, which are distinctive enough to catch a real leak.
        """
        import ast
        declared = {float(v) for v in DEFINITION['thresholds'].values() if isinstance(v, float)}
        declared |= {float(b['min']) for b in h.CALIBRATION['dilution_policy']['bands'] if b['min']}
        self.assertTrue(declared)
        # Scanning every module for these values would keep colliding with unrelated
        # arithmetic, so the check is aimed where a leak would actually happen: the
        # module that owns the bands, and the runtime's resolution of the policy.
        source = (h.ROOT/'harness_core/dilution.py').read_text(encoding='utf-8')
        literals = {node.value for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Constant) and isinstance(node.value, float)}
        self.assertEqual(literals & declared, set())
        runtime_source = (h.ROOT/'harness_core/runtime.py').read_text(encoding='utf-8')
        self.assertIn("DILUTION_POLICY=CALIBRATION.get('dilution_policy')", runtime_source)
        self.assertIn("requires_element_assessment", runtime_source)   # the veto is resolved, not named
        self.assertNotIn(DEFINITION.get('elements', [''])[0], runtime_source)

    def test_the_watch_bands_are_not_the_veto_thresholds(self):
        bands = {b['min'] for b in h.CALIBRATION['dilution_policy']['bands']}
        self.assertNotEqual(bands, set(DEFINITION['thresholds'].values()))
        self.assertFalse(h.CALIBRATION['dilution_policy']['bands'][0].get('is_hard_veto'))


class ElementDisciplineTests(unittest.TestCase):
    """`conditional` must mean almost-confirmed, not not-yet-known."""

    def report(self, *flags):
        r = {'agent_id': OWNERS[0], 'hard_veto_flags': list(flags)}
        return r

    def errors(self, *flags):
        return h.veto_element_errors(self.report(*flags))

    def test_prose_alone_cannot_reach_conditional_or_confirmed(self):
        for status in ('conditional', 'confirmed'):
            with self.subTest(status=status):
                problems = self.errors(flag(status, rationale='SBC is large and needs monitoring'))
                self.assertTrue(problems)
                self.assertIn('elements_met', problems[0])

    def test_confirmed_requires_every_element(self):
        self.assertEqual(self.errors(flag('confirmed', met=[True]*4)), [])
        problems = self.errors(flag('confirmed', met=[True, True, False, True]))
        self.assertTrue(any('every element' in p for p in problems))

    def test_conditional_requires_exactly_one_unmet_and_names_it(self):
        self.assertEqual(self.errors(flag('conditional', met=[True, True, True, False],
                                          decisive='확정된 자금조달 계획 공시')), [])
        two_unmet = self.errors(flag('conditional', met=[True, True, False, False], decisive='x'))
        self.assertTrue(any('exactly one unmet' in p for p in two_unmet))
        none_unmet = self.errors(flag('conditional', met=[True]*4, decisive='x'))
        self.assertTrue(any('exactly one unmet' in p for p in none_unmet))
        unnamed = self.errors(flag('conditional', met=[True, True, True, False]))
        self.assertTrue(any('decisive_missing_evidence' in p for p in unnamed))

    def test_cleared_and_candidate_stay_unencumbered(self):
        for status in ('cleared', 'candidate'):
            with self.subTest(status=status):
                self.assertEqual(self.errors(flag(status)), [])

    def test_a_partial_or_mistyped_element_answer_is_rejected(self):
        partial = {'veto': VETO, 'status': 'confirmed', 'rationale': 'x',
                   'elements_met': {ELEMENTS[0]: True}}
        self.assertTrue(any('does not answer' in p for p in self.errors(partial)))
        mistyped = {'veto': VETO, 'status': 'confirmed', 'rationale': 'x',
                    'elements_met': {e: 'yes' for e in ELEMENTS}}
        self.assertTrue(any('true/false' in p for p in self.errors(mistyped)))

    def test_only_an_owner_of_an_element_gated_veto_is_held_to_it(self):
        outsider = {'agent_id': 'CP', 'hard_veto_flags': [flag('confirmed')]}
        self.assertEqual(h.veto_element_errors(outsider), [])

    def test_other_vetoes_are_untouched_by_the_rule(self):
        other = next(v for v in h.VETOES if v != VETO)
        owner = h.VETO_REVIEWERS[other][0]
        report = {'agent_id': owner, 'hard_veto_flags': [
            {'veto': other, 'status': 'conditional', 'rationale': 'no elements declared'}]}
        self.assertEqual(h.veto_element_errors(report), [])


class DilutionWatchTests(unittest.TestCase):
    POLICY = h.CALIBRATION['dilution_policy']

    def watch(self, **metrics):
        reports = [{'agent_id': OWNERS[0], 'analysis_status': 'complete', 'dilution_metrics': metrics}]
        return dilution.watch(reports, OWNERS, self.POLICY)

    def test_bands_classify_declared_dilution(self):
        for value, status in ((0.0, 'normal'), (0.029, 'normal'), (0.03, 'monitor'), (0.049, 'monitor'),
                              (0.05, 'elevated'), (0.079, 'elevated'), (0.08, 'severe'), (0.40, 'severe')):
            with self.subTest(annualized_dilution=value):
                self.assertEqual(self.watch(annualized_dilution=value)['status'], status)

    def test_a_structural_financing_need_tightens_one_band(self):
        self.assertEqual(self.watch(annualized_dilution=0.04)['status'], 'monitor')
        escalated = self.watch(annualized_dilution=0.04, structural_financing_need=True)
        self.assertEqual(escalated['status'], 'elevated')
        self.assertEqual(escalated['escalated_by'], ['structural_financing_need'])
        self.assertEqual(self.watch(annualized_dilution=0.40, structural_financing_need=True)['status'], 'severe')

    def test_a_watch_is_never_a_veto(self):
        severe = self.watch(annualized_dilution=0.2, structural_financing_need=True)
        self.assertFalse(severe['is_hard_veto'])
        self.assertNotIn('status_rule', severe)

    def test_a_run_that_declares_nothing_gets_no_watch(self):
        self.assertIsNone(dilution.watch([{'agent_id': OWNERS[0], 'analysis_status': 'complete'}],
                                         OWNERS, self.POLICY))
        self.assertIsNone(dilution.watch([], OWNERS, self.POLICY))

    def test_an_incomplete_report_does_not_declare(self):
        pending = [{'agent_id': OWNERS[0], 'analysis_status': 'pending',
                    'dilution_metrics': {'annualized_dilution': 0.2}}]
        self.assertIsNone(dilution.watch(pending, OWNERS, self.POLICY))

    def test_owner_order_decides_which_declaration_wins(self):
        reports = [{'agent_id': OWNERS[1], 'analysis_status': 'complete',
                    'dilution_metrics': {'annualized_dilution': 0.2}},
                   {'agent_id': OWNERS[0], 'analysis_status': 'complete',
                    'dilution_metrics': {'annualized_dilution': 0.01}}]
        result = dilution.watch(reports, OWNERS, self.POLICY)
        self.assertEqual(result['declared_by'], OWNERS[0])
        self.assertEqual(result['status'], 'normal')


class DecisionFlowTests(unittest.TestCase):
    """The four cases from the brief, end to end through compute_aggregate."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(h, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.tmp.cleanup)
        self.context = h.load_json(test_v3.REPO/'templates/company_context.json')
        self.context.update(ticker='SYNTH', as_of_date='2026-09-19', current_price=100,
                            net_cash_per_share=5, market_cap_usd=40e9)
        self.save_context()

    def save_context(self):
        h.dump_json(h.run_dir('SYNTH')/'company_context.json', self.context)

    fixture = test_v3.V3Tests.fixture
    outlier_price = test_v3.V3Tests.outlier_price

    def aggregate(self, reports):
        return h.compute_aggregate('SYNTH', reports)

    def moonshot(self, metrics, veto_flag=None):
        reports = self.fixture('moonshot')
        by = {r['agent_id']: r for r in reports}
        by[OWNERS[0]]['dilution_metrics'] = metrics
        if veto_flag is not None:
            flags = by[veto_flag['agent_id']]['hard_veto_flags']
            flags[:] = [f for f in flags if f['veto'] != VETO] + [veto_flag['flag']]
        return reports

    def test_case_A_healthy_moonshot_dilution_is_watched_not_vetoed(self):
        """5% dilution, GP/share strongly up, no multi-year record, runway long."""
        result = self.aggregate(self.moonshot({
            'annualized_dilution': 0.05, 'three_year_diluted_share_cagr': None,
            'consecutive_years_material_dilution': 1,
            'per_share_value_proxy': 'gross_profit_per_share', 'per_share_value_growth': 0.43,
            'structural_financing_need': False, 'rationale': 'GP +50% vs shares +5%'}))
        self.assertEqual(result['hard_veto_status'], 'CLEARED')
        self.assertEqual(result['dilution_watch']['status'], 'elevated')
        self.assertTrue(result['archetype_fit']['moonshot']['eligible'])
        self.assertEqual(result['archetype']['id'], 'moonshot')
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)
        # The watch tightened the moonshot cap instead of blocking the buy.
        self.assertEqual(result['position_range_pre_ic'], result['dilution_watch']['position_cap'])
        self.assertNotEqual(result['dilution_watch']['position_before'],
                            result['position_range_pre_ic'])

    def test_case_B_structural_dilution_confirms_the_veto(self):
        """3y share CAGR 10%, GP/share flat, short runway, further raises required."""
        result = self.aggregate(self.moonshot(
            {'annualized_dilution': 0.10, 'three_year_diluted_share_cagr': 0.10,
             'three_year_cumulative_dilution': 0.33, 'consecutive_years_material_dilution': 3,
             'per_share_value_proxy': 'gross_profit_per_share', 'per_share_value_growth': 0.01,
             'structural_financing_need': True, 'rationale': 'GP CAGR 12% vs shares 10%'},
            veto_flag={'agent_id': OWNERS[0], 'flag': flag(
                'confirmed', met=[True]*4, rationale='All four elements evidenced')}))
        self.assertEqual(result['hard_veto_status'], 'CONFIRMED')
        self.assertEqual(result['dilution_watch']['status'], 'severe')
        self.assertFalse(result['archetype_fit']['moonshot']['eligible'])
        # A confirmed veto also empties reachability, so the run may land on either
        # blocking state; what matters is that no buy state is reachable.
        self.assertNotIn(result['mechanical_pre_ic_state'], h.BUY_STATES)
        self.assertIn(result['mechanical_pre_ic_state'], ('REJECT', 'EARLY_EXIT_NON_FIT'))
        self.assertEqual(result['reachable_archetypes_raw'], [])

    def test_case_C_one_off_acquisition_financing_is_not_long_duration(self):
        """+12% in one year, low before and after, GP/share up on the acquired business."""
        result = self.aggregate(self.moonshot({
            'annualized_dilution': 0.12, 'three_year_diluted_share_cagr': 0.04,
            'three_year_cumulative_dilution': 0.13, 'consecutive_years_material_dilution': 1,
            'per_share_value_proxy': 'gross_profit_per_share', 'per_share_value_growth': 0.22,
            'structural_financing_need': False, 'rationale': 'single M&A financing'}))
        self.assertEqual(result['hard_veto_status'], 'CLEARED')
        self.assertEqual(result['dilution_watch']['status'], 'severe')      # sized for
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)      # not blocked
        self.assertEqual(result['position_range_pre_ic'], result['dilution_watch']['position_cap'])

    def test_case_D_almost_confirmed_is_conditional_and_blocks(self):
        """Two years at 9%, per-share economics worsening, runway short, one item missing."""
        assessment = flag('conditional', met=[True, True, True, False],
                          decisive='확정된 다음 자금조달 계획이 아직 공시되지 않음',
                          rationale='Three elements evidenced; financing plan outstanding')
        result = self.aggregate(self.moonshot(
            {'annualized_dilution': 0.09, 'three_year_diluted_share_cagr': 0.09,
             'consecutive_years_material_dilution': 2,
             'per_share_value_proxy': 'gross_profit_per_share', 'per_share_value_growth': -0.03,
             'structural_financing_need': True, 'rationale': 'two years at 9%'},
            veto_flag={'agent_id': OWNERS[0], 'flag': assessment}))
        self.assertEqual(result['hard_veto_status'], 'UNRESOLVED')
        self.assertNotIn(result['mechanical_pre_ic_state'], h.BUY_STATES)
        self.assertEqual(h.veto_element_errors(
            {'agent_id': OWNERS[0], 'hard_veto_flags': [assessment]}), [])

    def test_the_watch_never_removes_an_archetype_or_moves_a_score(self):
        quiet = self.aggregate(self.moonshot({'annualized_dilution': 0.0}))
        severe = self.aggregate(self.moonshot({'annualized_dilution': 0.30,
                                               'structural_financing_need': True}))
        self.assertEqual(quiet['score_100'], severe['score_100'])
        self.assertEqual(quiet['domain_scores']['financial_survival']['score'],
                         severe['domain_scores']['financial_survival']['score'])
        self.assertEqual(quiet['archetype']['id'], severe['archetype']['id'])
        self.assertTrue(severe['archetype_fit']['moonshot']['eligible'])

    def test_a_non_moonshot_keeps_its_own_cap_but_still_reports_the_watch(self):
        reports = self.fixture()                      # compounder
        by = {r['agent_id']: r for r in reports}
        by[OWNERS[0]]['dilution_metrics'] = {'annualized_dilution': 0.09}
        result = self.aggregate(reports)
        self.assertEqual(result['archetype']['id'], 'compounder')
        self.assertEqual(result['dilution_watch']['status'], 'severe')
        self.assertNotIn('position_before', result['dilution_watch'])

    def test_runs_without_dilution_metrics_still_aggregate(self):
        result = self.aggregate(self.fixture('moonshot'))
        self.assertIsNone(result['dilution_watch'])
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)


if __name__ == '__main__':
    unittest.main()
