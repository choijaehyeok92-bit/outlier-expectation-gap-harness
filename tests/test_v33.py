"""v3.3 decision-semantics regressions.

Three couplings v3.3 breaks, each pinned here:

* ranking an archetype by its eligibility gates, which let a detailed contract
  outvote a terse one;
* a research budget that could hide the very questions a decision waits on;
* arithmetic review signals that would otherwise be read as verdicts.
"""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))   # importable either way

from harness_core import archetypes, research, runtime as h, valuation
# Imported as a module, never by name: unittest collects every TestCase bound in
# a module's namespace, so a direct import would run that suite a second time.
import test_v3


class FitAxisTests(unittest.TestCase):
    """Eligibility says whether; fit says which. They must not borrow each other's weight."""

    def test_executable_config_ranks_on_gate_backed_fit_axes(self):
        self.assertEqual(h.ARCHETYPES['fit_policy']['method'], 'weighted_fit_axes')
        for archetype in h.ARCHETYPES['types']:
            with self.subTest(archetype=archetype['id']):
                axes = archetype['fit_axes']
                fields = [a['field'] for a in axes]
                conditions = {c['field'] for c in archetype['conditions']}
                self.assertTrue(axes)
                self.assertEqual(len(fields), len(set(fields)))
                self.assertLessEqual(set(fields), conditions)
                self.assertTrue(all(a['weight'] > 0 for a in axes))
                self.assertAlmostEqual(sum(a['weight'] for a in axes), 1.0, places=8)
                self.assertTrue(all('fit_weight' not in c for c in archetype['conditions']))

    def test_eligibility_condition_count_cannot_change_fit_score(self):
        archetype = copy.deepcopy(next(t for t in h.ARCHETYPES['types'] if t['id'] == 'compounder'))
        domains = {'moat_trajectory': {'score': 80, 'criteria': {}},
                   'reinvestment_fcf': {'score': 78, 'criteria': {'incremental_roic': 85,
                                                                  'reinvestment_runway': 75}},
                   'management_allocation': {'score': 70, 'criteria': {}}}
        before = archetypes.fit_score(archetype, domains, {})
        archetype['conditions'] += copy.deepcopy(archetype['conditions']) * 5
        self.assertEqual(before, archetypes.fit_score(archetype, domains, {}))

    def test_a_gate_absent_from_the_axes_does_not_move_the_ranking(self):
        """price_to_base_value gates compounder but does not define what a compounder is."""
        archetype = copy.deepcopy(next(t for t in h.ARCHETYPES['types'] if t['id'] == 'compounder'))
        domains = {'moat_trajectory': {'score': 80, 'criteria': {}},
                   'reinvestment_fcf': {'score': 78, 'criteria': {'incremental_roic': 85,
                                                                  'reinvestment_runway': 75}},
                   'management_allocation': {'score': 70, 'criteria': {}}}
        cheap = archetypes.fit_score(archetype, domains, {'price_to_base_value': 0.3})
        dear = archetypes.fit_score(archetype, domains, {'price_to_base_value': 1.19})
        self.assertEqual(cheap, dear)

    def test_signal_fit_axis_uses_explicit_linear_normalization(self):
        growth = copy.deepcopy(next(t for t in h.ARCHETYPES['types'] if t['id'] == 'growth'))
        axis = next(a for a in growth['fit_axes'] if a['field'] == 'signal.revenue_cagr_next_3y')
        self.assertEqual(axis['normalization']['kind'], 'linear')
        domains = {a['field'].split('.')[1]: {'score': 80, 'criteria': {}}
                   for a in growth['fit_axes'] if a['field'].startswith('domain.')}
        low = archetypes.fit_score(growth, domains, {'revenue_cagr_next_3y': axis['normalization']['min']})
        high = archetypes.fit_score(growth, domains, {'revenue_cagr_next_3y': axis['normalization']['max']})
        self.assertGreater(high, low)
        # The range is a scale, not a second gate: beyond it the axis saturates.
        beyond = archetypes.fit_score(growth, domains, {'revenue_cagr_next_3y': 5.0})
        self.assertEqual(beyond, high)

    def test_fit_axis_rows_explain_the_score_and_mark_what_is_missing(self):
        archetype = copy.deepcopy(next(t for t in h.ARCHETYPES['types'] if t['id'] == 'compounder'))
        score, rows = archetypes.fit_breakdown(archetype, {'moat_trajectory': {'score': 80, 'criteria': {}}}, {})
        self.assertEqual([r['field'] for r in rows], [a['field'] for a in archetype['fit_axes']])
        self.assertEqual(score, round(100 * 0.30 * 0.80, 8))
        self.assertEqual([r['missing'] for r in rows], [False, True, True, True])

    def test_a_legacy_config_without_fit_axes_still_ranks(self):
        legacy = copy.deepcopy(next(t for t in h.ARCHETYPES['types'] if t['id'] == 'compounder'))
        legacy.pop('fit_axes')
        for condition in legacy['conditions']:
            condition['fit_weight'] = 1.0
        score, rows = archetypes.fit_breakdown(legacy, {'moat_trajectory': {'score': 80, 'criteria': {}}}, {})
        self.assertGreater(score, 0)
        self.assertEqual(rows, [])


class ResearchBudgetTests(unittest.TestCase):
    """A budget may shorten the queue. It may never shorten the decision."""

    POLICY = h.EXEC['research_policy']

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name)
        h.dump_json(self.run/'company_context.json', {'ticker': 'TEST', 'as_of_date': '2026-09-19'})
        h.dump_json(self.run/'run_manifest.json', {'input_snapshot_sha256': 'a'*64})

    DOMAINS = (('RF', 'reinvestment_fcf'), ('MT', 'moat_trajectory'), ('CP', 'customer_product'),
               ('FS', 'financial_survival'), ('MA', 'management_allocation'))

    def reports(self, count=20):
        return [{'agent_id': aid, 'domain': domain, 'analysis_status': 'complete',
                 'unknowns': [f'{aid} unknown {i}' for i in range(count)],
                 'next_checks': [f'{aid} optional {i}' for i in range(count)],
                 'hard_veto_flags': []} for aid, domain in self.DOMAINS]

    def build(self, aggregate, reports=None):
        return research.build_plan(self.run, reports if reports is not None else self.reports(),
                                   {'stage': 'domain_analysis'}, aggregate, h.CALIBRATION, self.POLICY)

    def test_budget_never_hides_decision_blockers(self):
        aggregate = {'archetype_fit': {'x': {'missing_conditions': [f'criterion.fake.c{i}' for i in range(30)]}},
                     'macro_geo_overlay': {'reanalysis_requests': []},
                     'valuation_model': {'status': 'COMPLETE', 'sanity': {'checks': []}}}
        plan = self.build(aggregate)
        budget = plan['research_budget']
        self.assertEqual(budget['decision_blocking_count'], 30)
        self.assertGreater(budget['active_count'], budget['configured_max_active'])
        self.assertEqual(budget['blocking_overflow'], 30 - budget['configured_max_active'])
        self.assertTrue(all(q['research_class'] != 'decision_blocking' for q in plan['deferred_questions']))
        self.assertGreater(budget['deferred_count'], 0)
        self.assertTrue(all(q['required_for_decision']
                            for q in plan['questions'] if q['research_class'] == 'decision_blocking'))

    def test_nonblocking_research_is_bounded_classified_and_visible_when_deferred(self):
        aggregate = {'archetype_fit': {}, 'macro_geo_overlay': {'reanalysis_requests': []},
                     'valuation_model': {'status': 'COMPLETE', 'sanity': {'checks': []}}}
        plan = self.build(aggregate)
        budget = plan['research_budget']
        caps = self.POLICY['question_budget']
        self.assertLessEqual(budget['active_count'], budget['configured_max_active'])
        self.assertLessEqual(budget['thesis_monitor_count'], caps['max_monitoring_questions'])
        self.assertLessEqual(budget['optional_count'], caps['max_optional_questions'])
        self.assertGreater(budget['deferred_count'], 0)
        self.assertTrue(all(q['deferred_reason'] for q in plan['deferred_questions']))
        self.assertEqual({q['research_class'] for q in plan['questions']}, {'thesis_monitor', 'optional'})
        per_domain = {}
        for q in plan['questions']:
            per_domain[q['domain']] = per_domain.get(q['domain'], 0) + 1
        self.assertLessEqual(max(per_domain.values()), caps['max_nonblocking_per_domain'])

    def test_budgeting_is_deterministic(self):
        aggregate = {'archetype_fit': {}, 'macro_geo_overlay': {'reanalysis_requests': []},
                     'valuation_model': {'status': 'COMPLETE', 'sanity': {'checks': []}}}
        first, second = self.build(aggregate), self.build(aggregate)
        self.assertEqual([q['research_question_id'] for q in first['questions']],
                         [q['research_question_id'] for q in second['questions']])
        self.assertEqual([q['research_question_id'] for q in first['deferred_questions']],
                         [q['research_question_id'] for q in second['deferred_questions']])

    def test_the_most_binding_trigger_decides_a_shared_question(self):
        text = 'Is maintenance capex disclosed?'
        reports = [{'agent_id': 'RF', 'domain': 'reinvestment_fcf', 'analysis_status': 'complete',
                    'unknowns': [text], 'next_checks': [text], 'hard_veto_flags': []}]
        # unknowns -> thesis_monitor beats next_checks -> optional.
        plan = self.build({'archetype_fit': {}, 'macro_geo_overlay': {'reanalysis_requests': []},
                           'valuation_model': {'status': 'COMPLETE', 'sanity': {'checks': []}}}, reports)
        question = next(q for q in plan['questions'] if q['question'] == text)
        self.assertEqual(sorted(question['triggers']), ['next_checks', 'unknowns'])
        self.assertEqual(question['research_class'], 'thesis_monitor')

    def test_a_blocking_sanity_failure_becomes_a_decision_blocking_question(self):
        aggregate = {'archetype_fit': {}, 'macro_geo_overlay': {'reanalysis_requests': []},
                     'valuation_model': {'status': 'COMPLETE', 'sanity': {'checks': [
                         {'id': 'scenario_value_order', 'status': 'FAIL', 'detail': 'not ordered'},
                         {'id': 'terminal_value_concentration', 'status': 'REVIEW', 'detail': 'heavy'}]}}}
        plan = self.build(aggregate)
        by_class = {q['research_class'] for q in plan['questions'] if 'scenario_value_order' in q['question']}
        self.assertEqual(by_class, {'decision_blocking'})
        review = next(q for q in plan['questions'] if 'terminal_value_concentration' in q['question'])
        self.assertEqual(review['research_class'], 'thesis_monitor')
        self.assertFalse(review['required_for_decision'])


class ValuationSanityTests(unittest.TestCase):
    """Only a contradiction blocks. A review signal is a question, not a verdict."""

    CTX = {'current_price': 100, 'net_cash_per_share': 5}

    def value(self, **paths):
        n = h.VAL_POLICY['horizon_years']
        report = {'analysis_status': 'complete', 'valuation_inputs': {'scenarios': {
            case: {'owner_fcf_per_share': path} for case, path in paths.items()}}}
        return valuation.deterministic_valuation(report, self.CTX, h.VAL_POLICY)

    def flat(self, bear=8, base=10, bull=12):
        n = h.VAL_POLICY['horizon_years']
        return {'bear': [bear]*n, 'base': [base]*n, 'bull': [bull]*n}

    def check(self, result, check_id):
        return next(row for row in result['sanity']['checks'] if row['id'] == check_id)

    def test_an_ordered_valuation_passes_every_check(self):
        result = self.value(**self.flat())
        self.assertEqual(result['sanity']['status'], 'PASS')
        self.assertFalse(result['sanity']['blocking'])
        self.assertEqual({row['status'] for row in result['sanity']['checks']}, {'PASS'})

    def test_yearly_path_crossing_is_review_not_automatic_block(self):
        crossed = self.flat()
        crossed['bear'][0] = 20
        result = self.value(**crossed)
        row = self.check(result, 'yearly_scenario_order')
        self.assertEqual(row['status'], 'REVIEW')
        self.assertFalse(row['blocking'])
        self.assertFalse(result['sanity']['blocking'])
        self.assertEqual(result['sanity']['status'], 'REVIEW')

    def test_intrinsic_value_ordering_contradiction_blocks(self):
        result = self.value(**self.flat(bear=20))
        self.assertEqual(result['sanity']['status'], 'FAIL')
        self.assertTrue(result['sanity']['blocking'])
        self.assertTrue(self.check(result, 'scenario_value_order')['blocking'])

    def test_terminal_concentration_is_review_not_automatic_reject(self):
        n = h.VAL_POLICY['horizon_years']
        path = [1]*(n-1)+[100]
        result = self.value(bear=path, base=path, bull=path)
        self.assertEqual(result['sanity']['status'], 'REVIEW')
        self.assertFalse(result['sanity']['blocking'])
        self.assertEqual(self.check(result, 'terminal_value_concentration')['status'], 'REVIEW')

    def test_the_executable_config_declares_the_sanity_policy(self):
        policy = h.VAL_POLICY['sanity_policy']
        self.assertEqual(policy['yearly_scenario_crossing'], 'review')
        self.assertLess(policy['terminal_fraction_review'], policy['terminal_fraction_high'])
        self.assertTrue(policy['price_above_bull_review'])

    def test_the_thresholds_come_from_config_not_from_the_code(self):
        crossed = self.flat()
        crossed['bear'][0] = 20
        result = self.value(**crossed)
        strict = valuation.valuation_sanity(
            {k: [float(x) for x in v] for k, v in crossed.items()}, result['scenarios'], 100,
            {**h.VAL_POLICY['sanity_policy'], 'yearly_scenario_crossing': 'block'})
        self.assertTrue(strict['blocking'])
        self.assertEqual(strict['status'], 'FAIL')
        loose = valuation.valuation_sanity(
            {k: [float(x) for x in v] for k, v in self.flat().items()}, result['scenarios'], 100,
            {**h.VAL_POLICY['sanity_policy'], 'terminal_fraction_review': 0.01})
        self.assertEqual(self.check({'sanity': loose}, 'terminal_value_concentration')['status'], 'REVIEW')

    def test_price_above_bull_is_routed_for_review_not_auto_vetoed(self):
        n = h.VAL_POLICY['horizon_years']
        report = {'analysis_status': 'complete', 'valuation_inputs': {'scenarios': {
            case: {'owner_fcf_per_share': [value]*n} for case, value in
            (('bear', 0.08), ('base', 0.10), ('bull', 0.12))}}}
        result = valuation.deterministic_valuation(report, {'current_price': 100, 'net_cash_per_share': 0},
                                                   h.VAL_POLICY)
        row = self.check(result, 'price_above_bull_value')
        self.assertEqual(row['status'], 'REVIEW')
        self.assertFalse(row['blocking'])
        self.assertFalse(result['sanity']['blocking'])


class DecisionSemanticsTests(unittest.TestCase):
    """What the sanity result is allowed to do to a decision, end to end."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(h, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.tmp.cleanup)
        self.context = h.load_json(test_v3.REPO/'templates/company_context.json')
        self.context.update(ticker='SYNTH', as_of_date='2026-09-19', current_price=100,
                            net_cash_per_share=5, market_cap_usd=100e9)
        self.save_context()

    def save_context(self):
        h.dump_json(h.run_dir('SYNTH')/'company_context.json', self.context)

    # V3Tests owns the fixture builders; reuse them rather than duplicating.
    fixture = test_v3.V3Tests.fixture
    outlier_price = test_v3.V3Tests.outlier_price

    def aggregate(self, reports):
        return h.compute_aggregate('SYNTH', reports)

    def scenarios(self, reports):
        return next(r for r in reports if r['agent_id'] == 'EV')['valuation_inputs']['scenarios']

    def test_an_ordered_valuation_leaves_the_buy_state_alone(self):
        result = self.aggregate(self.fixture())
        self.assertEqual(result['valuation_model']['sanity']['status'], 'PASS')
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)

    def test_yearly_crossing_alone_does_not_force_watch(self):
        reports = self.fixture()
        self.scenarios(reports)['bear']['owner_fcf_per_share'][0] = 20
        result = self.aggregate(reports)
        self.assertEqual(result['valuation_model']['sanity']['status'], 'REVIEW')
        self.assertFalse(result['valuation_model']['sanity']['blocking'])
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)

    def test_an_ordering_contradiction_forces_watch(self):
        reports = self.fixture()
        n = h.VAL_POLICY['horizon_years']
        self.scenarios(reports)['bear']['owner_fcf_per_share'] = [20]*n
        result = self.aggregate(reports)
        self.assertTrue(result['valuation_model']['sanity']['blocking'])
        self.assertEqual(result['mechanical_pre_ic_state'], 'WATCH')

    def test_v31_and_v32_verdicts_still_validate_under_the_v33_schema(self):
        """Adding a version must not strand the artifacts written under the old ones."""
        import jsonschema
        schema = h.load_json(test_v3.REPO/'schemas/final_verdict.schema.json')
        reports = self.fixture()
        verdict = h.final_verdict(self.aggregate(reports), reports)
        self.assertEqual(verdict['schema_version'], '3.3')
        self.assertIn('fit_axes', verdict['archetype_fit']['compounder'])
        jsonschema.validate(verdict, schema)
        for version in ('3.1', '3.2', '3.3'):
            with self.subTest(schema_version=version):
                legacy = copy.deepcopy(verdict)
                for field in ('strategy_version', 'schema_version', 'decision_policy_version'):
                    legacy[field] = version
                if version == '3.1':
                    # v3.1 predates outlier_growth and is never rewritten to add it.
                    legacy['archetype_fit'].pop('outlier_growth')
                jsonschema.validate(legacy, schema)
        stranded = copy.deepcopy(verdict)
        stranded['archetype_fit'].pop('outlier_growth')
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(stranded, schema)     # v3.3 still owes all five

    def test_a_sanity_review_never_confirms_the_valuation_hard_veto(self):
        veto = '현재가격이 비현실적인 Bull Case 이상을 요구'
        reports = self.fixture()
        n = h.VAL_POLICY['horizon_years']
        # Terminal-heavy but still ordered: only the concentration check fires.
        for case, tail in (('bear', 80), ('base', 100), ('bull', 120)):
            self.scenarios(reports)[case]['owner_fcf_per_share'] = [1]*(n-1)+[tail]
        result = self.aggregate(reports)
        self.assertEqual(result['valuation_model']['sanity']['status'], 'REVIEW')
        self.assertEqual(result['hard_veto_status'], 'CLEARED')
        self.assertEqual(result['confirmed_vetoes'], [])
        row = next(x for x in result['veto_gate']['items'] if x['veto'] == veto)
        self.assertEqual(row['status'], 'CLEARED')


if __name__ == '__main__':
    unittest.main()
