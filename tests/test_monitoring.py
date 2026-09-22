"""Phase 12 monitoring: thresholds, the observation log, evaluation and drift.

Unlike the orchestration suites, almost everything here is deterministic and
the tests can check that it is *right*, not merely that it runs. Three
properties carry the most weight.

**A prose threshold is refused, not interpreted.** An earlier draft of the
parser searched the text for any number and read `quantified and rising
breached for 2 consecutive periods` as `>= 2`. That is a green light nobody
checked, which is worse than no light at all, and it is pinned here against
the real corpus as well as against invented strings.

**An ambiguous observation is refused too.** A 71% margin recorded as the bare
number `71`, compared against `73% 이상` (0.73), satisfies `>= 0.73` and
reports ok for a breach. Both directions of that mistake are tested.

**Monitoring cannot decide anything.** The evaluation output is checked to
contain no score, no archetype, no Hard Veto status, no `ic_state` and no
position range, and `review_required` is checked to be raised only by a thesis
break or a triggered falsifier — never by the layer's own opinion.

**A KPI is never matched to a metric by resemblance.** The third refusal is
the same shape as the first two, and the real corpus shows why: "Microsoft
Cloud gross margin" against a company-wide `gross_margin` of 0.679 would sail
past a 66% threshold on a number that was never measured. Only exact name
equality is ever *proposed*, and accepting a proposal is a person's recorded
act.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest

import jsonschema

from packages.monitoring import (drift, evaluate, ingest, observations, store, thresholds,
                                 watchlist)

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2026-09-18'
OPERATORS = {'increasing': '>=', 'above_threshold': '>=', 'decreasing': '<=',
             'below_threshold': '<=', 'stable': None}


def snapshot_schema() -> dict:
    return json.loads((ROOT / 'schemas' / 'monitoring_snapshot.schema.json').read_text('utf-8'))


def observation_schema() -> dict:
    return json.loads((ROOT / 'schemas' / 'monitoring_observation.schema.json').read_text('utf-8'))


class ThresholdParsingTests(unittest.TestCase):
    def parse(self, text, direction='increasing'):
        return thresholds.parse(text, direction, OPERATORS)

    def test_a_number_with_a_side_becomes_a_comparison(self):
        cases = {
            '73% 이상': ('>=', 0.73, 'ratio'),
            '200% 이하': ('<=', 2.0, 'ratio'),
            '-20%p 이상': ('>=', -0.2, 'percent_point'),
            '>=1.5x': ('>=', 1.5, 'number'),
            'below 1.5x': ('<', 1.5, 'number'),
            'at least 15%': ('>=', 0.15, 'ratio'),
            '2조 이상': ('>=', 2e12, 'number'),
            '1,200억 이상': ('>=', 1.2e11, 'number'),
        }
        for text, (operator, value, unit) in cases.items():
            with self.subTest(threshold=text):
                parsed = self.parse(text)
                self.assertIsNotNone(parsed, text)
                self.assertEqual((parsed.operator, parsed.value, parsed.unit),
                                 (operator, value, unit))

    def test_prose_is_refused_rather_than_mined_for_a_number(self):
        # Each of these carries a digit somewhere, or a comparator, or both.
        # A parser that reached for either would report a checked threshold
        # where none exists.
        for text in ('전년 대비 증가', 'quantified and rising breached for 2 consecutive periods',
                     '>=revenue growth breached for 2 consecutive periods',
                     '>=20% breached for 2 consecutive periods', '>WACC', '>prior year',
                     'all decisive facts filing-backed', '최근 3년 개선'):
            with self.subTest(threshold=text):
                self.assertIsNone(self.parse(text))

    def test_a_number_with_no_side_is_not_a_comparison(self):
        # `stable` gives no operator, and a two-sided band needs a reference
        # value nobody declared.
        self.assertIsNone(self.parse('1.5', 'stable'))
        self.assertIsNone(self.parse(0.73, 'stable'))
        self.assertIsNotNone(self.parse('1.5', 'decreasing'))

    def test_the_thresholds_own_wording_outranks_the_declared_direction(self):
        parsed = self.parse('200% 이하', 'increasing')
        self.assertEqual(parsed.operator, '<=')

    def test_a_comparison_is_arithmetic_and_nothing_else(self):
        parsed = self.parse('73% 이상')
        self.assertTrue(parsed.satisfied_by(0.74))
        self.assertTrue(parsed.satisfied_by(0.73))
        self.assertFalse(parsed.satisfied_by(0.72))


class ObservationScaleTests(unittest.TestCase):
    def test_an_ambiguous_bare_number_is_refused_in_both_directions(self):
        # 71 against a 0–1 threshold: reading it as 71 passes a breach, and
        # dividing by 100 would break a legitimate ratio of 2.0.
        for value in (71, '71', 2.0):
            with self.subTest(value=value):
                number, reason = thresholds.observed_number(value, 'ratio')
                self.assertIsNone(number)
                self.assertIn('ambiguous', reason)

    def test_a_marker_or_a_declared_unit_settles_it(self):
        self.assertEqual(thresholds.observed_number('71%', 'ratio'), (0.71, None))
        self.assertEqual(thresholds.observed_number(71, 'ratio', 'percent'), (0.71, None))
        self.assertEqual(thresholds.observed_number(2.0, 'ratio', 'ratio'), (2.0, None))
        self.assertEqual(thresholds.observed_number(0.71, 'ratio'), (0.71, None))

    def test_a_plain_scale_threshold_takes_a_plain_number(self):
        self.assertEqual(thresholds.observed_number(1.8, 'number'), (1.8, None))


class LogCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def record(self, **kwargs):
        defaults = {'as_of_date': '2026-09-20', 'source': 'FY26 Q4 10-K p.40',
                    'source_type': 'filing', 'value': '71%', 'base': self.base}
        return observations.record(kwargs.pop('ticker', 'TEST'),
                                   kwargs.pop('watch_id', 'watch0000000001'),
                                   **{**defaults, **kwargs})


class ObservationLogTests(LogCase):
    def test_an_observation_needs_a_traceable_source(self):
        with self.assertRaises(observations.ObservationRejected) as caught:
            self.record(source='   ')
        self.assertIn('not evidence', str(caught.exception))

    def test_nothing_from_the_future_is_recorded(self):
        with self.assertRaises(observations.ObservationRejected) as caught:
            self.record(as_of_date='2099-01-01')
        self.assertIn('after the cutoff', str(caught.exception))

    def test_an_empty_observation_is_refused_because_unknown_is_the_default(self):
        with self.assertRaises(observations.ObservationRejected):
            self.record(value=None, triggered=None)

    def test_the_log_is_append_only_and_a_repeat_adds_nothing(self):
        first = self.record()
        again = self.record()
        self.assertEqual(first['observation_id'], again['observation_id'])
        self.assertEqual(len(observations.load('TEST', base=self.base)), 1)

    def test_a_correction_supersedes_and_the_original_stays_readable(self):
        first = self.record(value='71%')
        self.record(value='69%', supersedes=first['observation_id'],
                    note='restated in the 10-K')
        rows = observations.load('TEST', base=self.base)
        self.assertEqual(len(rows), 2, 'the original is kept, not edited')
        self.assertEqual(observations.latest(rows)['value'], '69%')

    def test_an_observation_older_than_the_analysis_is_marked_not_hidden(self):
        row = self.record(as_of_date='2026-06-30', run_as_of_date=AS_OF)
        self.assertTrue(row['pre_analysis'])
        self.assertIn(AS_OF, row['pre_analysis_note'])
        self.assertEqual(len(observations.load('TEST', base=self.base)), 1)

    def test_the_cutoff_filters_reads_as_well_as_writes(self):
        self.record(as_of_date='2026-09-20')
        self.assertEqual(observations.load('TEST', cutoff='2026-09-01', base=self.base), [])
        self.assertEqual(len(observations.load('TEST', cutoff='2026-09-30', base=self.base)), 1)

    def test_a_corrupt_line_is_reported_rather_than_swallowed(self):
        self.record()
        path = observations.log_path('TEST', self.base)
        with path.open('a', encoding='utf-8') as handle:
            handle.write('{not json\n')
        report = observations.integrity('TEST', self.base)
        self.assertEqual(report['lines'], 1)
        self.assertEqual(len(report['unreadable']), 1)

    def test_a_stored_row_matches_the_published_schema(self):
        row = self.record()
        errors = list(jsonschema.Draft202012Validator(observation_schema()).iter_errors(row))
        self.assertEqual([e.message for e in errors], [])


def agent_report(agent_id, domain, kpis, falsifiers) -> dict:
    return {'agent_id': agent_id, 'domain': domain, 'role': 'domain_analyst',
            'analysis_status': 'complete', 'key_kpis': kpis, 'falsifiers': falsifiers}


class FixtureRuns:
    """A throwaway `runs/` tree and deep-dive directory, built by hand."""

    def build(self, run_id='ACME', ticker='ACME', as_of=AS_OF, reports=None,
              policy='3.1', score=70.0, archetype='growth', ic_state='STARTER'):
        run = self.runs / run_id
        (run / 'reports').mkdir(parents=True, exist_ok=True)
        (run / 'company_context.json').write_text(json.dumps(
            {'ticker': ticker, 'as_of_date': as_of, 'currency': 'USD',
             'current_price': 100, 'company_name': f'{ticker} Inc.'}), encoding='utf-8')
        (run / 'aggregate.json').write_text(json.dumps(
            {'as_of_date': as_of, 'ticker': ticker, 'score_100': score,
             'score_100_ex_valuation': score, 'coverage_weight': 100,
             'classification': 'Starter / Watch', 'archetype': {'id': archetype},
             'hard_veto_status': 'CLEARED', 'mechanical_pre_ic_state': ic_state,
             'position_range_pre_ic': '1-2%', 'early_exit': False,
             'strategy_version': policy, 'decision_policy_version': policy,
             'domain_scores': {}, 'axis_scores': {},
             'valuation_model': {'status': 'COMPLETE', 'signals': {'price_to_base_value': 0.8}}}),
            encoding='utf-8')
        for agent_id, report in (reports or {}).items():
            (run / 'reports' / f'{agent_id}.json').write_text(
                json.dumps(report), encoding='utf-8')
        return run

    def deep_dive(self, deep_dive_id, ticker='ACME', as_of=AS_OF, kpis=None, falsifiers=None):
        directory = self.dives / deep_dive_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'deep_dive_report.json').write_text(json.dumps({
            'metadata': {'deep_dive_id': deep_dive_id, 'ticker': ticker, 'jurisdiction': 'US',
                         'as_of_date': as_of, 'created_at_utc': f'{as_of}T00:00:00+00:00',
                         'harness_run': {'run_id': ticker}},
            'monitoring_kpis': kpis or [],
            'falsifiers': falsifiers or [],
        }), encoding='utf-8')
        return directory


class WatchlistCase(unittest.TestCase, FixtureRuns):
    KPI = {'name': 'Gross margin', 'why_it_matters': 'unit economics',
           'current_value': '72%', 'direction_required': 'increasing',
           'warning_threshold': '70% 이상', 'thesis_break_threshold': '65% 이상',
           'cadence': 'quarterly', 'source': '10-Q'}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runs = Path(self.tmp.name) / 'runs'
        self.dives = Path(self.tmp.name) / 'deep_dive'
        self.runs.mkdir(parents=True)
        self.dives.mkdir(parents=True)
        self.config = watchlist.load_config()

    def watchlist_for(self, ticker='ACME', run_id=None):
        return watchlist.build(ticker, run_id, self.config, self.runs, self.dives)


class WatchlistTests(WatchlistCase):
    def test_items_are_read_back_from_reports_and_never_authored(self):
        self.build(reports={'MT': agent_report(
            'MT', 'moat_trajectory',
            [{'name': 'Gross margin', 'direction': 'up', 'threshold': '70% 이상',
              'cadence': 'quarterly'}],
            ['If retention falls below 90% the moat claim fails.'])})
        built = self.watchlist_for()
        self.assertEqual(built['summary']['kpis'], 1)
        self.assertEqual(built['summary']['falsifiers'], 1)
        kpi = next(i for i in built['items'] if i['kind'] == 'kpi')
        self.assertEqual(kpi['source_kind'], 'agent_report')
        self.assertEqual(kpi['source_ref'], 'MT')

    def test_an_agents_single_threshold_is_a_warning_and_never_a_break(self):
        # The analyst wrote one number and never said crossing it breaks the
        # thesis. Reading it as a break would manufacture an alarm.
        self.build(reports={'MT': agent_report('MT', 'moat_trajectory', [
            {'name': 'Gross margin', 'direction': 'up', 'threshold': '70% 이상',
             'cadence': 'quarterly'}], [])})
        kpi = next(i for i in self.watchlist_for()['items'] if i['kind'] == 'kpi')
        self.assertEqual(kpi['checkable_levels'], ['warning'])
        self.assertIsNone(kpi['thresholds']['thesis_break'])

    def test_a_deep_dive_declares_both_levels(self):
        self.build()
        self.deep_dive('ACME-2026-09-18-aaaaaaaaaaaa', kpis=[self.KPI])
        kpi = next(i for i in self.watchlist_for()['items'] if i['source_kind'] == 'deep_dive')
        self.assertEqual(kpi['checkable_levels'], ['warning', 'thesis_break'])

    def test_a_watch_id_survives_re_running_the_deep_dive(self):
        # The whole history of a KPI hangs off this id. If a re-run moved it,
        # re-doing the research would orphan every observation.
        self.build()
        self.deep_dive('ACME-2026-09-18-aaaaaaaaaaaa', kpis=[self.KPI])
        before = self.watchlist_for()['items']
        self.deep_dive('ACME-2026-09-18-bbbbbbbbbbbb', kpis=[self.KPI])
        after = self.watchlist_for()['items']
        before_ids = {i['watch_id'] for i in before if i['source_kind'] == 'deep_dive'}
        after_ids = {i['watch_id'] for i in after if i['source_kind'] == 'deep_dive'}
        self.assertEqual(before_ids, after_ids)

    def test_a_watch_id_survives_a_threshold_being_revised(self):
        self.build()
        self.deep_dive('ACME-2026-09-18-aaaaaaaaaaaa', kpis=[self.KPI])
        before = next(i['watch_id'] for i in self.watchlist_for()['items']
                      if i['source_kind'] == 'deep_dive')
        self.deep_dive('ACME-2026-09-18-cccccccccccc',
                       kpis=[{**self.KPI, 'warning_threshold': '75% 이상'}])
        after = next(i['watch_id'] for i in self.watchlist_for()['items']
                     if i['source_kind'] == 'deep_dive')
        self.assertEqual(before, after, 'an observation is of the world, not of the threshold')

    def test_two_agents_naming_the_same_kpi_stay_two_items(self):
        # Merging them would be a judgement about whether they mean the same
        # observable, which is not this layer's to make.
        rows = [{'name': 'Gross margin', 'direction': 'up', 'threshold': '70% 이상',
                 'cadence': 'quarterly'}]
        self.build(reports={'MT': agent_report('MT', 'moat_trajectory', rows, []),
                            'CP': agent_report('CP', 'customer_product', rows, [])})
        ids = {i['watch_id'] for i in self.watchlist_for()['items']}
        self.assertEqual(len(ids), 2)

    def test_a_falsifier_is_never_machine_checkable(self):
        self.build(reports={'MT': agent_report('MT', 'moat_trajectory', [],
                                               ['If retention falls the moat claim fails.'])})
        item = next(i for i in self.watchlist_for()['items'] if i['kind'] == 'falsifier')
        self.assertFalse(item['machine_checkable'])
        self.assertIn('evidence', item['not_machine_checkable_reason'])

    def test_a_company_with_no_run_is_an_error_not_an_empty_watchlist(self):
        with self.assertRaises(ValueError) as caught:
            self.watchlist_for('GHOST')
        self.assertIn('nothing has declared what to watch', str(caught.exception))


class EvaluationTests(WatchlistCase):
    def setUp(self):
        super().setUp()
        self.log = Path(self.tmp.name) / 'monitoring'
        self.build()
        self.deep_dive('ACME-2026-09-18-aaaaaaaaaaaa', kpis=[self.KPI], falsifiers=[
            {'statement': 'Retention falls below 90%.', 'observable': 'disclosed NRR',
             'would_break': 'the moat claim'}])

    def item(self, kind='kpi'):
        return next(i for i in self.watchlist_for()['items'] if i['kind'] == kind)

    def observe(self, **kwargs):
        defaults = {'as_of_date': '2026-09-20', 'source': '10-Q p.4', 'source_type': 'filing',
                    'base': self.log}
        return observations.record('ACME', kwargs.pop('watch_id', self.item()['watch_id']),
                                   **{**defaults, **kwargs})

    def status(self, cutoff='2026-09-25', kind='kpi'):
        result = evaluate.evaluate('ACME', cutoff, None, self.config, self.runs, self.dives,
                                   self.log)
        target = self.item(kind)['watch_id']
        return next(row for row in result['items'] if row['watch_id'] == target), result

    def test_nothing_observed_is_unknown_and_never_ok(self):
        row, _ = self.status()
        self.assertEqual(row['status'], 'unknown')
        self.assertFalse(row['review_required'])

    def test_a_value_inside_every_threshold_is_ok(self):
        self.observe(value='72%')
        row, _ = self.status()
        self.assertEqual(row['status'], 'ok')

    def test_crossing_the_warning_threshold_says_warning_and_does_not_demand_review(self):
        self.observe(value='68%')
        row, result = self.status()
        self.assertEqual(row['status'], 'warning')
        self.assertFalse(row['review_required'])
        self.assertEqual(result['summary']['review_required'], 0)

    def test_crossing_the_break_threshold_demands_review(self):
        self.observe(value='60%')
        row, result = self.status()
        self.assertEqual(row['status'], 'thesis_break')
        self.assertTrue(row['review_required'])
        self.assertEqual(result['summary']['review_required'], 1)

    def test_an_unobserved_cadence_goes_stale_rather_than_staying_green(self):
        self.observe(value='72%')
        row, _ = self.status(cutoff='2027-06-30')
        self.assertEqual(row['status'], 'stale')
        self.assertGreater(row['days_overdue'], 0)

    def test_staleness_never_quietens_a_breach(self):
        self.observe(value='60%')
        row, _ = self.status(cutoff='2027-06-30')
        self.assertEqual(row['status'], 'thesis_break')
        self.assertGreater(row['days_overdue'], 0)

    def test_an_ambiguous_observation_is_not_compared(self):
        self.observe(value=68)
        row, _ = self.status()
        self.assertEqual(row['status'], 'not_machine_checkable')
        self.assertIn('ambiguous', row['reason'])

    def test_a_declared_unit_makes_the_same_number_comparable(self):
        self.observe(value=68, unit='percent')
        row, _ = self.status()
        self.assertEqual(row['status'], 'warning')

    def test_a_falsifier_is_unchecked_until_somebody_checks_it(self):
        row, _ = self.status(kind='falsifier')
        self.assertEqual(row['status'], 'unchecked')

    def test_a_triggered_falsifier_demands_review(self):
        self.observe(watch_id=self.item('falsifier')['watch_id'], triggered=True,
                     note='NRR disclosed at 88%')
        row, result = self.status(kind='falsifier')
        self.assertEqual(row['status'], 'triggered')
        self.assertTrue(row['review_required'])
        self.assertEqual(result['review_required'][0]['status'], 'triggered')

    def test_a_falsifier_checked_and_not_met_is_recorded_as_such(self):
        self.observe(watch_id=self.item('falsifier')['watch_id'], triggered=False,
                     note='NRR disclosed at 114%')
        row, _ = self.status(kind='falsifier')
        self.assertEqual(row['status'], 'not_triggered')
        self.assertFalse(row['review_required'])

    def test_a_correction_is_what_gets_evaluated(self):
        first = self.observe(value='60%')
        self.observe(value='72%', supersedes=first['observation_id'], note='restated')
        row, _ = self.status()
        self.assertEqual(row['status'], 'ok')

    def test_monitoring_cannot_decide_anything(self):
        # The boundary, checked on the output rather than trusted in prose.
        self.observe(value='60%')
        _, result = self.status()
        serialized = json.dumps(result, ensure_ascii=False)
        for forbidden in ('"score_100"', '"hard_veto_status"', '"archetype"',
                          '"ic_state"', '"position_range"'):
            self.assertNotIn(forbidden, serialized)
        self.assertIn('ic_state나 position_range를 바꾼다', result['authority']['may_not'])

    def test_the_result_matches_the_published_schema(self):
        self.observe(value='60%')
        _, result = self.status()
        errors = list(jsonschema.Draft202012Validator(snapshot_schema()).iter_errors(result))
        self.assertEqual([f'{list(e.absolute_path)}: {e.message}' for e in errors], [])

    def test_the_portfolio_view_puts_what_needs_a_person_first(self):
        self.observe(value='60%')
        rows = evaluate.portfolio(['ACME'], '2026-09-25', self.config, self.runs, self.dives,
                                  self.log)
        self.assertEqual(rows['needing_review'], 1)
        self.assertEqual(rows['rows'][0]['ticker'], 'ACME')

    def test_an_unreadable_company_is_named_rather_than_dropped(self):
        result = evaluate.portfolio(['GHOST'], '2026-09-25', self.config, self.runs, self.dives,
                                    self.log)
        self.assertEqual(result['companies'], 0)
        self.assertEqual(result['unreadable'][0]['ticker'], 'GHOST')


WAREHOUSE = {
    'as_of_date': AS_OF,
    'rows': [{
        'ticker': 'ACME',
        'metrics': {'gross_margin': 0.62, 'revenue_growth_yoy': 0.11,
                    'current_price': 100.0, 'owner_fcf_margin': None},
        'provenance': {
            'gross_margin': {'metric_id': 'gross_margin', 'value': 0.62, 'method': 'ratio',
                             'inputs': ['FACT-1', 'FACT-2'], 'period_end': '2026-06-30'},
            'revenue_growth_yoy': {'metric_id': 'revenue_growth_yoy', 'method': 'growth:ttm',
                                   'inputs': ['FACT-3'], 'period_end': '2026-06-30'},
            'current_price': {'metric_id': 'current_price', 'method': 'market',
                              'period_end': AS_OF},
            'owner_fcf_margin': {'metric_id': 'owner_fcf_margin', 'method': 'ratio'},
        },
    }],
}


class IngestTests(WatchlistCase):
    """Linking is a person's act; everything after it is arithmetic."""

    MARGIN = {'name': 'Gross margin', 'why_it_matters': 'unit economics',
              'current_value': '65%', 'direction_required': 'increasing',
              'warning_threshold': '60% 이상', 'thesis_break_threshold': '55% 이상',
              'cadence': 'quarterly', 'source': '10-Q'}

    def setUp(self):
        super().setUp()
        self.log = Path(self.tmp.name) / 'monitoring'
        self.build()
        self.deep_dive('ACME-2026-09-18-aaaaaaaaaaaa', kpis=[self.MARGIN], falsifiers=[
            {'statement': 'Retention falls.', 'observable': 'NRR', 'would_break': 'the moat'}])

    def item(self, name='Gross margin', kind='kpi'):
        return next(i for i in self.watchlist_for()['items']
                    if i['kind'] == kind and (kind != 'kpi' or i['name'] == name))

    def suggest(self):
        return ingest.suggest('ACME', self.config, self.log,
                              runs_dir=self.runs, deep_dive_base=self.dives)

    def link(self, metric_id, watch_id=None, **kwargs):
        return ingest.link('ACME', watch_id or self.item()['watch_id'], metric_id,
                           self.config, base=self.log, runs_dir=self.runs,
                           deep_dive_base=self.dives, **kwargs)

    def ingest(self, payload=None):
        return ingest.ingest('ACME', config=self.config, base=self.log,
                             warehouse_payload=payload or WAREHOUSE,
                             runs_dir=self.runs, deep_dive_base=self.dives)

    def test_only_an_exact_name_is_proposed(self):
        payload = self.suggest()
        self.assertEqual([row['metric_id'] for row in payload['proposed']], ['gross_margin'])
        self.assertEqual(payload['proposed'][0]['name_match'], 'exact')

    def test_a_proposal_is_not_a_link(self):
        self.suggest()
        self.assertEqual(ingest.load_links('ACME', self.log), {},
                         'suggesting must not link anything by itself')
        self.assertEqual(self.ingest()['recorded'], 0)

    def test_a_metric_that_does_not_exist_is_refused(self):
        with self.assertRaises(ingest.LinkRefused) as caught:
            self.link('gross_margarine')
        self.assertIn('not a warehouse metric', str(caught.exception))

    def test_a_falsifier_cannot_be_linked_to_a_metric(self):
        with self.assertRaises(ingest.LinkRefused) as caught:
            self.link('gross_margin', watch_id=self.item(kind='falsifier')['watch_id'])
        self.assertIn('evidence, not by a metric', str(caught.exception))

    def test_a_link_records_whether_the_names_actually_matched(self):
        exact = self.link('gross_margin')
        self.assertEqual(exact['name_match'], 'exact')
        self.assertIsNone(exact['warning'])

        asserted = self.link('revenue_growth_yoy')
        self.assertEqual(asserted['name_match'], 'operator_asserted')
        self.assertIn('does not match', asserted['warning'])

    def test_an_observation_carries_the_metric_provenance(self):
        self.link('gross_margin')
        row = self.ingest()['rows'][0]
        self.assertEqual(row['value'], 0.62)
        self.assertEqual(row['unit'], 'ratio', 'the metric declares its own scale')
        self.assertEqual(row['as_of_date'], '2026-06-30',
                         'dated to the period it measures, not the build')
        stored = observations.load('ACME', row['watch_id'], base=self.log)[-1]
        self.assertIn('method=ratio', stored['source'])
        self.assertIn('FACT-1,FACT-2', stored['source'])
        self.assertEqual(stored['source_type'], 'filing')

    def test_a_market_metric_is_recorded_as_market_not_as_a_filing(self):
        self.link('current_price')
        row = self.ingest()['rows'][0]
        stored = observations.load('ACME', row['watch_id'], base=self.log)[-1]
        self.assertEqual(stored['source_type'], 'market')

    def test_re_ingesting_the_same_build_writes_nothing(self):
        self.link('gross_margin')
        first = self.ingest()
        second = self.ingest()
        self.assertEqual((first['recorded'], first['already_present']), (1, 0))
        self.assertEqual((second['recorded'], second['already_present']), (0, 1))
        self.assertEqual(len(observations.load('ACME', base=self.log)), 1)

    def test_a_metric_the_warehouse_could_not_compute_is_skipped_not_zeroed(self):
        self.link('owner_fcf_margin')
        result = self.ingest()
        self.assertEqual(result['recorded'], 0)
        self.assertIn('could not compute', result['skipped'][0]['reason'])
        self.assertEqual(observations.load('ACME', base=self.log), [])

    def test_a_metric_with_no_period_end_is_skipped(self):
        payload = {**WAREHOUSE, 'rows': [{
            **WAREHOUSE['rows'][0],
            'metrics': {'gross_margin': 0.62},
            'provenance': {'gross_margin': {'method': 'ratio', 'inputs': ['FACT-1']}}}]}
        self.link('gross_margin')
        result = self.ingest(payload)
        self.assertEqual(result['recorded'], 0)
        self.assertIn('cannot be judged stale', result['skipped'][0]['reason'])

    def test_an_asserted_link_says_so_on_every_observation_it_makes(self):
        self.link('revenue_growth_yoy', note='closest available proxy')
        row = self.ingest()['rows'][0]
        stored = observations.load('ACME', row['watch_id'], base=self.log)[-1]
        self.assertIn('operator_asserted', stored['note'])
        self.assertIn('Gross margin', stored['note'])

    def test_an_ingested_observation_is_what_the_evaluation_then_judges(self):
        self.link('gross_margin')
        self.ingest()
        result = evaluate.evaluate('ACME', '2026-09-25', None, self.config, self.runs,
                                   self.dives, self.log)
        row = next(r for r in result['items'] if r['watch_id'] == self.item()['watch_id'])
        self.assertEqual(row['status'], 'ok')
        self.assertEqual(row['observed_value'], 0.62)

    def test_an_ingested_breach_reaches_review_exactly_as_a_typed_one_would(self):
        self.link('gross_margin')
        self.ingest({**WAREHOUSE, 'rows': [{
            **WAREHOUSE['rows'][0], 'metrics': {'gross_margin': 0.50}}]})
        result = evaluate.evaluate('ACME', '2026-09-25', None, self.config, self.runs,
                                   self.dives, self.log)
        self.assertEqual(result['summary']['review_required'], 1)
        self.assertEqual(result['review_required'][0]['status'], 'thesis_break')

    def test_unlinking_keeps_the_observations_already_recorded(self):
        watch_id = self.item()['watch_id']
        self.link('gross_margin')
        self.ingest()
        ingest.unlink('ACME', watch_id, self.log)
        self.assertEqual(ingest.load_links('ACME', self.log), {})
        self.assertEqual(len(observations.load('ACME', base=self.log)), 1,
                         'the log is append-only; a changed judgement does not erase history')

    def test_ingest_with_nothing_linked_says_how_to_link(self):
        result = self.ingest()
        self.assertEqual(result['recorded'], 0)
        self.assertIn('monitor link', result['note'])

    def test_a_warehouse_that_does_not_hold_this_company_is_refused(self):
        self.link('gross_margin')
        with self.assertRaises(ingest.LinkRefused) as caught:
            self.ingest({'as_of_date': AS_OF, 'rows': []})
        self.assertIn('not in the warehouse', str(caught.exception))


class IngestRealCorpusTests(unittest.TestCase):
    """The case that decided the design, against the committed reports."""

    def test_a_segment_kpi_is_never_proposed_a_company_wide_metric(self):
        # "Microsoft Cloud gross margin" warns below 66%. Company-wide
        # gross_margin is 0.679, so an automatic match would report ok for a
        # number that was never measured.
        payload = ingest.suggest('MSFT', base=Path(tempfile.mkdtemp()))
        proposed = {row['name'] for row in payload['proposed']}
        unmatched = {row['name'] for row in payload['unmatched']}
        self.assertIn('Microsoft Cloud gross margin', unmatched)
        self.assertNotIn('Microsoft Cloud gross margin', proposed)

    def test_most_of_the_corpus_needs_a_person_and_the_summary_says_so(self):
        payload = ingest.suggest('MSFT', base=Path(tempfile.mkdtemp()))
        self.assertGreater(payload['summary']['unmatched'], payload['summary']['proposed'])
        self.assertIn('제안이지 링크가 아니다', payload['note'])

    def test_every_proposal_is_a_metric_the_warehouse_defines(self):
        definitions = ingest.metric_definitions()
        payload = ingest.suggest('MSFT', base=Path(tempfile.mkdtemp()))
        for row in payload['proposed']:
            self.assertIn(row['metric_id'], definitions)


class DriftTests(unittest.TestCase, FixtureRuns):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runs = Path(self.tmp.name) / 'runs'
        self.dives = Path(self.tmp.name) / 'deep_dive'
        self.runs.mkdir(parents=True)
        self.dives.mkdir(parents=True)
        self.config = watchlist.load_config()

    def test_a_change_under_one_policy_is_attributed_to_the_company(self):
        self.build(run_id='ACME', ticker='ACME', as_of='2026-06-30', score=62.0)
        self.build(run_id='ACME-2026-09-18', ticker='ACME', as_of='2026-09-18', score=71.0)
        result = drift.series('ACME', self.config, self.runs)
        self.assertEqual(result['runs'], 2)
        self.assertEqual(result['comparable_steps'], 1)
        change = next(c for c in result['steps'][0]['changes'] if c['field'] == 'core_score')
        self.assertEqual(change['delta'], 9.0)
        self.assertTrue(change['attributable_to_company'])

    def test_a_change_across_a_policy_boundary_is_not(self):
        self.build(run_id='ACME', ticker='ACME', as_of='2026-06-30', score=62.0, policy='3.0')
        self.build(run_id='ACME-2026-09-18', ticker='ACME', as_of='2026-09-18', score=71.0,
                   policy='3.1')
        step = drift.series('ACME', self.config, self.runs)['steps'][0]
        self.assertFalse(step['comparable'])
        self.assertIn('decision_policy_version', step['policy_changes'])
        self.assertIn('measures the policy', step['not_comparable_reason'])
        self.assertTrue(all(not c['attributable_to_company'] for c in step['changes']))

    def test_runs_are_grouped_by_the_naming_convention_and_it_is_visible(self):
        # A re-run cannot reuse a run id, so several of them carry the run id
        # as their ticker. Grouping strictly by ticker would hide the series.
        self.build(run_id='ACME', ticker='ACME', as_of='2026-06-30')
        self.build(run_id='ACME-V2-2026-09-18', ticker='ACME-V2-2026-09-18', as_of='2026-09-18')
        result = drift.series('ACME', self.config, self.runs)
        self.assertEqual(result['runs'], 2)
        self.assertEqual(result['matched_by'], ['run_id_prefix', 'ticker'])

    def test_explicit_run_ids_turn_the_inference_off(self):
        self.build(run_id='ACME', ticker='ACME', as_of='2026-06-30')
        self.build(run_id='ACME-V2-2026-09-18', ticker='ACME-V2-2026-09-18', as_of='2026-09-18')
        result = drift.series('ACME', self.config, self.runs, run_ids=['ACME'])
        self.assertEqual(result['runs'], 1)
        self.assertEqual(result['matched_by'], ['explicit_run_id'])

    def test_a_company_with_no_run_is_an_error(self):
        with self.assertRaises(ValueError):
            drift.series('GHOST', self.config, self.runs)


class SnapshotStoreTests(unittest.TestCase):
    def test_a_snapshot_is_written_once_and_never_rewritten(self):
        record = store.build_record({'ticker': 'ACME', 'evaluated_as_of': '2026-09-25',
                                     'summary': {'items': 3, 'review_required': 1}})
        with tempfile.TemporaryDirectory() as tmp:
            path = store.save(record, base=tmp)
            original = path.read_text(encoding='utf-8')
            store.save({**record, 'summary': {'items': 999}}, base=tmp)
            self.assertEqual(path.read_text(encoding='utf-8'), original)
            rows = store.list_runs(base=tmp)
            self.assertEqual(rows[0]['monitoring_run_id'], record['monitoring_run_id'])
            self.assertEqual(rows[0]['review_required'], 1)


class RealCorpusTests(unittest.TestCase):
    """Against the committed runs, because invented thresholds are easy mode."""

    def test_the_committed_reports_parse_without_a_single_invented_comparison(self):
        built = watchlist.build('MSFT')
        self.assertGreater(built['summary']['items'], 50)
        for item in built['items']:
            if not item['machine_checkable']:
                continue
            for level in item['checkable_levels']:
                comparison = item['comparison'][level]
                self.assertIn(comparison['operator'], ('>=', '<=', '>', '<'))
                # Every parsed threshold must be a threshold, not a stray digit
                # lifted out of a sentence.
                self.assertLessEqual(len(comparison['source_text'].split()), 4,
                                     comparison['source_text'])

    def test_the_corpus_says_plainly_that_no_break_can_fire_automatically(self):
        # Every deep-dive break threshold in this corpus reads "… breached for
        # 2 consecutive periods", a persistence rule this layer does not
        # evaluate. That has to be visible, not inferred from a quiet screen.
        built = watchlist.build('MSFT')
        self.assertEqual(built['summary']['can_raise_thesis_break'], 0)
        self.assertIn('can_raise_thesis_break가 0이면', built['reading_note'])

    def test_an_unobserved_company_reports_ignorance_not_health(self):
        result = evaluate.evaluate('MSFT', '2026-09-25',
                                   base=Path(tempfile.mkdtemp()))
        self.assertEqual(result['summary']['by_status'].get('ok', 0), 0)
        self.assertEqual(result['summary']['observed'], 0)
        self.assertGreater(result['summary']['never_observed'], 0)


class ConfigTests(unittest.TestCase):
    def test_the_config_states_what_this_layer_may_not_do(self):
        config = watchlist.load_config()
        joined = ' '.join(config['authority']['may_not'])
        for forbidden in ('Hard Veto', 'archetype', 'ic_state', '점수'):
            self.assertIn(forbidden, joined)
        self.assertIn('매도 신호가 아니라', config['authority']['statement'])

    def test_only_a_break_or_a_trigger_asks_for_a_person(self):
        config = watchlist.load_config()
        self.assertEqual(sorted(config['review_required_statuses']),
                         ['thesis_break', 'triggered'])

    def test_the_monitoring_directory_can_be_moved_off_the_repository(self):
        previous = os.environ.get(observations.ENV_DIR)
        try:
            os.environ[observations.ENV_DIR] = '/tmp/elsewhere'
            self.assertEqual(observations.base_dir(), Path('/tmp/elsewhere'))
        finally:
            if previous is None:
                os.environ.pop(observations.ENV_DIR, None)
            else:
                os.environ[observations.ENV_DIR] = previous
        self.assertEqual(observations.base_dir(), observations.MONITORING_DIR)


if __name__ == '__main__':
    unittest.main()
