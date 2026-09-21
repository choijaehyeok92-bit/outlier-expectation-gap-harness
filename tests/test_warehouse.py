"""The screening warehouse: deterministic metrics, and the numbers it refuses.

Every rule here is one that a careless implementation produces a plausible
wrong answer for: a nine-month cumulative summed with quarters, a segment row
read as the company total, a margin against negative revenue, a CAGR from a
loss, a missing line counted as zero.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from packages.screening import rows as row_source
from packages.screening import warehouse
from packages.screening.facts import FactIndex
from packages.screening.fields import Registry
from packages.screening.metrics import MetricCalculator, load_config

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2026-09-18'
CONFIG = load_config()


def fact(**overrides) -> dict:
    base = {'fact_id': 'FACT-0001', 'metric': 'revenue', 'statement': 'income',
            'gaap_status': 'gaap', 'value_reported': 100.0, 'unit_kind': 'currency',
            'currency': 'USD', 'scale_multiplier': 1.0, 'period_start': '2025-01-01',
            'period_end': '2025-12-31', 'period_kind': 'fy', 'fiscal_year': 2025,
            'fiscal_quarter': None, 'segment': None, 'filing_date': '2026-02-01',
            'source_document': 'doc.htm', 'is_amended': False, 'is_restated': False,
            'requires_review': False, 'review_reason': None, 'confidence': 0.9,
            'metric_detail': None, 'reported_label': None, 'source_section': None,
            'source_locator': None, 'source_page': None, 'source_quote': None}
    base.update(overrides)
    return base


def pack(facts, **overrides) -> dict:
    base = {'schema_version': '1.0', 'ticker': 'TEST', 'as_of_date': AS_OF,
            'reporting_currency': 'USD', 'consolidation_basis': 'CFS',
            'documents': [{'document_id': 'DOC-001', 'source_document': 'doc.htm',
                           'document_type': '10-K'}],
            'facts': facts}
    base.update(overrides)
    return base


def calculator(facts, market=None, **pack_overrides) -> MetricCalculator:
    return MetricCalculator(pack(facts, **pack_overrides), config=CONFIG,
                            market_snapshot=market, as_of=AS_OF)


class SegmentTests(unittest.TestCase):
    def test_segment_rows_are_not_read_as_company_totals(self):
        facts = [
            fact(fact_id='FACT-0001', value_reported=1000.0, segment='consolidated',
                 reported_label='Total revenue'),
            fact(fact_id='FACT-0002', value_reported=40.0, segment='APAC',
                 reported_label='Revenue by geography'),
        ]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 1000.0,
                         'the geography row must never stand in for the company')

    def test_segment_statement_is_excluded(self):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0),
                 fact(fact_id='FACT-0002', value_reported=7.0, statement='segment',
                      period_end='2025-12-31')]
        index = FactIndex(pack(facts), CONFIG['ttm_policy'],
                          selection=CONFIG['fact_selection'], as_of=AS_OF)
        self.assertEqual(index.excluded['statement'], 1)
        self.assertEqual(len(index.by_metric['revenue']), 1)

    def test_declared_consolidated_labels_are_kept(self):
        for label in ('consolidated', 'Total', '연결', '합계'):
            facts = [fact(segment=label, value_reported=500.0)]
            self.assertEqual(calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF)).value, 500.0)


class CutoffTests(unittest.TestCase):
    def test_a_fact_filed_after_the_cutoff_is_not_used(self):
        facts = [fact(fact_id='FACT-0001', value_reported=100.0, filing_date='2026-02-01'),
                 fact(fact_id='FACT-0002', value_reported=999.0, filing_date='2026-11-01',
                      fiscal_year=2025)]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 100.0)

    def test_a_period_ending_after_the_cutoff_is_not_used(self):
        facts = [fact(fact_id='FACT-0001', value_reported=100.0),
                 fact(fact_id='FACT-0002', value_reported=500.0, fiscal_year=2026,
                      period_start='2026-01-01', period_end='2026-12-31',
                      filing_date='2026-03-01')]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 100.0)


class TtmTests(unittest.TestCase):
    def quarters(self, values, metric='revenue'):
        ends = ['2025-12-31', '2026-03-31', '2026-06-30', '2025-09-30']
        starts = ['2025-10-01', '2026-01-01', '2026-04-01', '2025-07-01']
        return [fact(fact_id=f'FACT-{i:04d}', metric=metric, value_reported=value,
                     period_kind='quarter', fiscal_quarter=(i % 4) + 1,
                     period_start=starts[i], period_end=ends[i],
                     fiscal_year=int(ends[i][:4]), filing_date='2026-08-01')
                for i, value in enumerate(values)]

    def test_four_contiguous_quarters_are_summed(self):
        result = calculator(self.quarters([10, 20, 30, 40])).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 100)
        self.assertEqual(result.method, 'four_quarters')

    def test_a_gap_disqualifies_the_quarterly_window(self):
        facts = self.quarters([10, 20, 30, 40])
        facts.pop(3)                                    # remove 2025 Q3, leaving a hole
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertNotEqual(result.method, 'four_quarters')

    def test_quarters_and_year_to_date_are_never_added_together(self):
        facts = self.quarters([10, 20, 30, 40])
        facts.append(fact(fact_id='FACT-0099', value_reported=60, period_kind='ytd',
                          period_start='2026-01-01', period_end='2026-06-30',
                          fiscal_year=2026, filing_date='2026-08-01'))
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 100, 'the year-to-date row overlaps the quarters')

    def test_fy_ytd_bridge(self):
        facts = [
            fact(fact_id='FACT-0001', value_reported=1000.0, fiscal_year=2025),
            fact(fact_id='FACT-0002', value_reported=600.0, period_kind='ytd',
                 period_start='2026-01-01', period_end='2026-06-30', fiscal_year=2026,
                 filing_date='2026-08-14'),
            fact(fact_id='FACT-0003', value_reported=450.0, period_kind='ytd',
                 period_start='2025-01-01', period_end='2025-06-30', fiscal_year=2025,
                 filing_date='2025-08-14'),
        ]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 1000 + 600 - 450)
        self.assertEqual(result.method, 'fy_ytd_bridge')

    def test_the_bridge_needs_matching_month_spans(self):
        facts = [
            fact(fact_id='FACT-0001', value_reported=1000.0, fiscal_year=2025),
            fact(fact_id='FACT-0002', value_reported=600.0, period_kind='ytd',
                 period_start='2026-01-01', period_end='2026-06-30', fiscal_year=2026,
                 filing_date='2026-08-14'),
            fact(fact_id='FACT-0003', value_reported=200.0, period_kind='ytd',
                 period_start='2025-01-01', period_end='2025-03-31', fiscal_year=2025,
                 filing_date='2025-05-14'),
        ]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.method, 'latest_fy',
                         'a three-month prior period cannot bridge a six-month one')

    def test_the_most_recent_window_wins_over_method_order(self):
        # A nine-month interim and a later full year: the full year is current.
        facts = [
            fact(fact_id='FACT-0001', value_reported=800.0, fiscal_year=2024,
                 period_start='2024-01-01', period_end='2024-12-31', filing_date='2025-02-01'),
            fact(fact_id='FACT-0002', value_reported=1000.0, fiscal_year=2025,
                 period_start='2025-01-01', period_end='2025-12-31', filing_date='2026-02-01'),
            fact(fact_id='FACT-0003', value_reported=700.0, period_kind='ytd',
                 period_start='2025-01-01', period_end='2025-09-30', fiscal_year=2025,
                 filing_date='2025-11-14'),
            fact(fact_id='FACT-0004', value_reported=560.0, period_kind='ytd',
                 period_start='2024-01-01', period_end='2024-09-30', fiscal_year=2024,
                 filing_date='2024-11-14'),
        ]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 1000.0)
        self.assertEqual(result.period_end, '2025-12-31')

    def test_a_stale_window_is_refused(self):
        facts = [fact(fact_id='FACT-0001', value_reported=100.0, fiscal_year=2020,
                      period_start='2020-01-01', period_end='2020-12-31',
                      filing_date='2021-02-01')]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertIsNone(result.value)
        self.assertIn('older than', result.reason)

    def test_share_counts_are_averaged_not_summed(self):
        facts = self.quarters([100, 100, 100, 100], metric='diluted_weighted_average_shares')
        result = calculator(facts).evaluate('diluted_shares', ('ttm', AS_OF))
        self.assertEqual(result.value, 100, 'four quarterly averages are not four times the shares')


class RefusalTests(unittest.TestCase):
    def base(self, **extra):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0)]
        facts.extend(extra.get('facts', []))
        return facts

    def test_a_missing_required_component_is_not_zero(self):
        facts = [fact(fact_id='FACT-0001', metric='cash', value_reported=50.0,
                      period_kind='instant', period_start=None, statement='balance_sheet')]
        result = calculator(facts).evaluate('net_cash', ('ttm', AS_OF))
        self.assertIsNone(result.value, 'no debt disclosure does not mean no debt')
        self.assertIn('short_term_debt', result.reason)

    def test_an_optional_component_absence_is_recorded(self):
        facts = [
            fact(fact_id='FACT-0001', metric='cash', value_reported=50.0, period_kind='instant',
                 period_start=None, statement='balance_sheet'),
            fact(fact_id='FACT-0002', metric='short_term_debt', value_reported=10.0,
                 period_kind='instant', period_start=None, statement='balance_sheet'),
            fact(fact_id='FACT-0003', metric='long_term_debt', value_reported=15.0,
                 period_kind='instant', period_start=None, statement='balance_sheet'),
        ]
        result = calculator(facts).evaluate('net_cash', ('ttm', AS_OF))
        self.assertEqual(result.value, 25.0)
        self.assertTrue(any('short_term_investments' in note for note in result.assumptions))

    def test_a_ratio_against_zero_is_not_computed(self):
        facts = [fact(fact_id='FACT-0001', value_reported=0.0),
                 fact(fact_id='FACT-0002', metric='gross_profit', value_reported=5.0)]
        result = calculator(facts).evaluate('gross_margin', ('ttm', AS_OF))
        self.assertIsNone(result.value)
        self.assertIn('zero', result.reason)

    def test_a_ratio_against_a_negative_denominator_is_not_computed(self):
        facts = [fact(fact_id='FACT-0001', metric='operating_cash_flow', value_reported=-40.0),
                 fact(fact_id='FACT-0002', metric='capex', value_reported=10.0)]
        result = calculator(facts).evaluate('capex_to_ocf', ('ttm', AS_OF))
        self.assertIsNone(result.value)
        self.assertIn('negative', result.reason)

    def test_growth_from_a_non_positive_base_is_not_reported(self):
        facts = [fact(fact_id='FACT-0001', value_reported=-50.0, fiscal_year=2024,
                      period_start='2024-01-01', period_end='2024-12-31',
                      filing_date='2025-02-01'),
                 fact(fact_id='FACT-0002', value_reported=100.0, fiscal_year=2025)]
        calc = calculator(facts)
        result = calc.evaluate('revenue_growth_yoy', ('fy', 2025))
        self.assertIsNone(result.value)
        self.assertIn('non-positive base', result.reason)

    def test_cagr_from_a_non_positive_endpoint_is_undefined(self):
        facts = [fact(fact_id='FACT-0001', value_reported=-10.0, fiscal_year=2022,
                      period_start='2022-01-01', period_end='2022-12-31',
                      filing_date='2023-02-01'),
                 fact(fact_id='FACT-0002', value_reported=1000.0, fiscal_year=2025)]
        result = calculator(facts).evaluate('revenue_cagr_3y', ('fy', 2025))
        self.assertIsNone(result.value)
        self.assertIn('not both', result.reason)

    def test_conflicting_values_for_one_period_are_flagged(self):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0, filing_date='2026-02-01'),
                 fact(fact_id='FACT-0002', value_reported=980.0, filing_date='2026-05-01')]
        result = calculator(facts).evaluate('revenue_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 980.0, 'the newest filing wins')
        self.assertTrue(result.requires_review)
        self.assertTrue(any('other value' in note for note in result.review_reasons))

    def test_review_flags_travel_with_the_value(self):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0, requires_review=True,
                      review_reason='single ambiguous interim column')]
        result = calculator(facts).evaluate('gross_margin', ('ttm', AS_OF))
        facts.append(fact(fact_id='FACT-0002', metric='gross_profit', value_reported=300.0))
        result = calculator(facts).evaluate('gross_margin', ('ttm', AS_OF))
        self.assertTrue(result.requires_review)


class DerivationTests(unittest.TestCase):
    def test_gross_profit_falls_back_to_revenue_less_cost(self):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0),
                 fact(fact_id='FACT-0002', metric='cost_of_revenue', value_reported=400.0)]
        result = calculator(facts).evaluate('gross_profit_ttm', ('ttm', AS_OF))
        self.assertEqual(result.value, 600.0)
        self.assertIn('fallback', result.method)
        self.assertTrue(result.assumptions)

    def test_owner_fcf_is_declared_a_proxy(self):
        definition = next(row for row in CONFIG['definitions'] if row['id'] == 'owner_fcf_ttm')
        self.assertTrue(definition['is_proxy'])
        self.assertIn('하네스', definition['proxy_note'])

    def test_balance_sheet_per_share_uses_period_end_shares(self):
        facts = [
            fact(fact_id='FACT-0001', metric='cash', value_reported=100.0, period_kind='instant',
                 period_start=None, statement='balance_sheet'),
            fact(fact_id='FACT-0002', metric='short_term_debt', value_reported=10.0,
                 period_kind='instant', period_start=None, statement='balance_sheet'),
            fact(fact_id='FACT-0003', metric='long_term_debt', value_reported=10.0,
                 period_kind='instant', period_start=None, statement='balance_sheet'),
            fact(fact_id='FACT-0004', metric='period_end_shares', value_reported=40.0,
                 period_kind='instant', period_start=None, statement='shares', unit_kind='shares'),
            fact(fact_id='FACT-0005', metric='diluted_weighted_average_shares',
                 value_reported=80.0, statement='shares', unit_kind='shares'),
        ]
        result = calculator(facts).evaluate('net_cash_per_share', ('ttm', AS_OF))
        self.assertEqual(result.value, 2.0)
        self.assertIn('period_end_shares', result.method)

    def test_market_cap_is_derived_only_from_market_inputs(self):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0)]
        with_market = calculator(facts, market={'close': 10.0, 'shares_outstanding': 5.0})
        self.assertEqual(with_market.evaluate('market_cap', ('ttm', AS_OF)).value, 50.0)
        self.assertIsNone(calculator(facts).evaluate('market_cap', ('ttm', AS_OF)).value)

    def test_every_registry_warehouse_field_has_a_definition(self):
        declared = {row['id'] for row in CONFIG['definitions'] if not row.get('internal')}
        registry = Registry()
        for field in registry.data['fields']:
            if field['backends'] == ['screening_warehouse']:
                self.assertIn(field['id'], declared,
                              f'{field["id"]} is offered to screens but never computed')


class WarehouseTests(unittest.TestCase):
    def entry(self, ticker='TEST', **overrides):
        facts = [fact(fact_id='FACT-0001', value_reported=1000.0),
                 fact(fact_id='FACT-0002', metric='gross_profit', value_reported=700.0)]
        base = {'ticker': ticker, 'jurisdiction': 'US', 'currency': 'USD',
                'pack': pack(facts, ticker=ticker), 'market_snapshot': {}}
        base.update(overrides)
        return base

    def test_build_records_coverage_and_provenance(self):
        payload = warehouse.build([self.entry()], AS_OF, CONFIG)
        self.assertEqual(payload['companies'], 1)
        row = payload['rows'][0]
        self.assertEqual(row['metrics']['gross_margin'], 0.7)
        self.assertIn('revenue_ttm', row['provenance'])
        self.assertIn('market_cap', row['unavailable'])
        self.assertTrue(row['source']['pack_sha256'])

    def test_a_broken_pack_does_not_lose_the_warehouse(self):
        payload = warehouse.build([self.entry('GOOD'), {'ticker': 'BAD'}], AS_OF, CONFIG)
        self.assertEqual(payload['tickers'], ['GOOD'])
        self.assertEqual(payload['failures'][0]['ticker'], 'BAD')

    def test_one_row_per_company(self):
        payload = warehouse.build([self.entry('DUP'), self.entry('DUP')], AS_OF, CONFIG)
        self.assertEqual(payload['companies'], 1)
        self.assertIn('duplicate ticker', payload['failures'][0]['error'])

    def test_round_trip_through_disk(self):
        payload = warehouse.build([self.entry()], AS_OF, CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            warehouse.save(payload, base=tmp)
            self.assertTrue(warehouse.available(tmp))
            self.assertEqual(warehouse.load(AS_OF, base=tmp)['tickers'], ['TEST'])

    def test_backend_is_inactive_until_it_has_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(warehouse.available(tmp))


class MergeTests(unittest.TestCase):
    HARNESS = {'ticker': 'AAA', 'run_id': 'AAA', 'jurisdiction': 'US', 'currency': 'USD',
               'as_of_date': AS_OF, 'core_score': 80.0, 'net_cash_per_share': 12.0,
               'market_cap_usd': 5e10, 'domain_scores': {}, 'axis_scores': {}}
    METRICS = {'ticker': 'AAA', 'as_of_date': AS_OF, 'currency': 'USD',
               'revenue_ttm': 1000.0, 'net_cash_per_share': 9.0, 'gross_margin': 0.7}

    def test_the_harness_value_wins_where_both_have_one(self):
        row = row_source.merge_row(self.HARNESS, self.METRICS)
        self.assertEqual(row['net_cash_per_share'], 12.0)
        self.assertEqual(row['field_sources']['net_cash_per_share'], 'harness_run_index')
        self.assertEqual(row['field_sources']['gross_margin'], 'screening_warehouse')

    def test_a_company_with_no_harness_run_is_kept(self):
        row = row_source.merge_row(None, self.METRICS)
        self.assertFalse(row['has_harness_run'])
        self.assertTrue(row['has_warehouse_metrics'])
        self.assertIsNone(row.get('core_score'))

    def test_currency_conversion_needs_an_explicit_rate(self):
        korean = {'ticker': 'KKK', 'currency': 'KRW', 'market_cap': 1.38e13, 'as_of_date': AS_OF}
        without = row_source.merge_row(None, korean)
        self.assertIsNone(without.get('market_cap_usd'))
        with_rate = row_source.merge_row(None, korean, {'KRW': {'per_usd': 1380.2}})
        self.assertAlmostEqual(with_rate['market_cap_usd'], 1.38e13 / 1380.2, places=2)
        self.assertEqual(with_rate['field_sources']['market_cap_usd'], 'derived:fx(KRW)')

    def test_merged_rows_respect_the_cutoff(self):
        rows = row_source.load_rows('2026-09-17', include_warehouse=False)
        for row in rows:
            self.assertLessEqual(row.get('as_of_date') or '', '2026-09-17')


class RealCorpusTests(unittest.TestCase):
    """Against the packs completed runs actually hold, not fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.entries = []
        for run_id in ('RBRK', 'MSFT'):
            path = ROOT / 'runs' / run_id / 'sources' / 'financials' / 'normalized_financials.json'
            context = ROOT / 'runs' / run_id / 'company_context.json'
            if not path.exists():
                continue
            cls.entries.append({
                'ticker': run_id, 'jurisdiction': 'US', 'currency': 'USD',
                'pack': json.loads(path.read_text(encoding='utf-8')),
                'market_snapshot': {}})

    def test_segment_rows_do_not_corrupt_a_real_gross_margin(self):
        row = next((e for e in self.entries if e['ticker'] == 'RBRK'), None)
        if row is None:
            self.skipTest('RBRK pack is not in this checkout')
        result = warehouse.compute_row(row, AS_OF, CONFIG)
        margin = result['metrics']['gross_margin']
        self.assertIsNotNone(margin)
        self.assertLess(margin, 1.0, 'a gross margin above 100% means a segment row leaked in')
        self.assertGreater(margin, 0.5)

    def test_a_real_pack_produces_auditable_provenance(self):
        row = next((e for e in self.entries if e['ticker'] == 'MSFT'), None)
        if row is None:
            self.skipTest('MSFT pack is not in this checkout')
        result = warehouse.compute_row(row, AS_OF, CONFIG)
        revenue = result['provenance']['revenue_ttm']
        self.assertIsNotNone(revenue['value'])
        self.assertTrue(revenue['inputs'], 'every value names the facts it consumed')
        self.assertIn(revenue['method'], ('four_quarters', 'fy_ytd_bridge', 'latest_fy',
                                          'fy_ytd_bridge_full_year'))


if __name__ == '__main__':
    unittest.main()
