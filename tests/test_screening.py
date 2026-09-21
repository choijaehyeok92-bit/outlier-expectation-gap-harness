"""Screening: units, the spec contract, the compiler's three-valued logic, the parser.

The rules being tested are the ones that would silently corrupt a screen rather
than break it: a percent read as a whole number, a missing value read as zero, a
threshold in the wrong currency, a condition the parser could not handle
disappearing instead of being reported.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from packages.screening import compiler, nl, runs_index, store, units
from packages.screening import spec as spec_module
from packages.screening.fields import Registry, load_lexicon

ROOT = Path(__file__).resolve().parents[1]
LEXICON = load_lexicon()
AS_OF = '2026-09-18'


def rows():
    return [
        {'run_id': 'AAA', 'ticker': 'AAA', 'jurisdiction': 'US', 'as_of_date': AS_OF,
         'core_score': 80.0, 'market_cap_usd': 5e10, 'net_cash_per_share': 10.0,
         'price_to_base_value': 0.8, 'hard_veto_status': 'CLEARED',
         'domain_scores': {'moat_trajectory': 82.0}, 'axis_scores': {}},
        {'run_id': 'BBB', 'ticker': 'BBB', 'jurisdiction': 'KR', 'as_of_date': AS_OF,
         'core_score': 60.0, 'market_cap_usd': 1e9, 'net_cash_per_share': -2.0,
         'price_to_base_value': 1.4, 'hard_veto_status': 'UNRESOLVED',
         'domain_scores': {'moat_trajectory': 55.0}, 'axis_scores': {}},
        {'run_id': 'CCC', 'ticker': 'CCC', 'jurisdiction': 'US', 'as_of_date': AS_OF,
         'core_score': 75.0, 'market_cap_usd': 2e10, 'net_cash_per_share': None,
         'price_to_base_value': None, 'hard_veto_status': 'CLEARED',
         'domain_scores': {}, 'axis_scores': {}},
        {'run_id': 'FUTURE', 'ticker': 'FUT', 'jurisdiction': 'US', 'as_of_date': '2026-09-30',
         'core_score': 99.0, 'market_cap_usd': 9e11, 'net_cash_per_share': 5.0,
         'price_to_base_value': 0.1, 'hard_veto_status': 'CLEARED',
         'domain_scores': {'moat_trajectory': 99.0}, 'axis_scores': {}},
    ]


def spec_with(clauses, **overrides):
    base = spec_module.empty(AS_OF)
    base['filters'] = {'op': 'and', 'clauses': clauses}
    base.update(overrides)
    return spec_module.normalise(base)


class UnitTests(unittest.TestCase):
    def test_percent_is_a_decimal_fraction(self):
        self.assertAlmostEqual(units.parse_percent('15%'), 0.15)
        self.assertAlmostEqual(units.parse_percent('0.15'), 0.15)

    def test_percent_prefers_the_marked_number(self):
        # "3년" must not be mistaken for the threshold.
        self.assertAlmostEqual(units.parse_percent('최근 3년 매출 CAGR 15% 이상'), 0.15)

    def test_bare_number_above_one_is_rejected_not_divided(self):
        with self.assertRaises(units.UnitError):
            units.parse_percent('15')

    def test_korean_scale_words(self):
        self.assertEqual(units.parse_currency_amount('1조', LEXICON), (1e12, 'KRW'))
        self.assertEqual(units.parse_currency_amount('5억', LEXICON), (5e8, 'KRW'))
        self.assertEqual(units.parse_currency_amount('10 billion dollars', LEXICON), (1e10, 'USD'))

    def test_conversion_requires_an_explicit_rate(self):
        with self.assertRaises(units.UnitError):
            units.convert(1e12, 'KRW', 'USD', {})
        self.assertAlmostEqual(units.convert(1380.2, 'KRW', 'USD', {'KRW': {'per_usd': 1380.2}}), 1.0)


class SpecTests(unittest.TestCase):
    def test_ratio_field_rejects_a_percent_shaped_value(self):
        with self.assertRaises(spec_module.SpecError):
            spec_with([{'field': 'price_to_base_value', 'operator': '<=', 'value': 15}])

    def test_unknown_field_becomes_an_unresolved_condition(self):
        result = spec_with([{'field': 'made_up_metric', 'operator': '>=', 'value': 1}])
        self.assertEqual(result['filters']['clauses'], [])
        self.assertEqual(result['unresolved_conditions'][0]['reason'], 'no_mapped_field')

    def test_inactive_backend_is_reported_not_dropped(self):
        result = spec_with([{'field': 'revenue_cagr_3y', 'operator': '>=', 'value': 0.15}])
        self.assertEqual(result['filters']['clauses'], [])
        self.assertEqual(result['unresolved_conditions'][0]['reason'], 'backend_unavailable')

    def test_cross_currency_without_a_rate_is_unresolved(self):
        result = spec_with([{'field': 'market_cap_usd', 'operator': '>=', 'value': 1e12,
                             'currency': 'KRW'}])
        self.assertEqual(result['filters']['clauses'], [])
        self.assertEqual(result['unresolved_conditions'][0]['reason'], 'missing_fx_rate')

    def test_cross_currency_with_an_explicit_rate_converts(self):
        result = spec_with([{'field': 'market_cap_usd', 'operator': '>=', 'value': 1e12,
                             'currency': 'KRW'}],
                           fx_rates={'KRW': {'per_usd': 1380.2, 'source': 'test'}})
        clause = result['filters']['clauses'][0]
        self.assertEqual(clause['converted_from'], 'KRW')
        self.assertAlmostEqual(clause['value'], 1e12 / 1380.2, places=2)

    def test_harness_dependent_field_sets_requires_harness_run(self):
        result = spec_with([{'field': 'domain.moat_trajectory', 'operator': '>=', 'value': 75}])
        self.assertTrue(result['requires_harness_run'])

    def test_spec_id_ignores_parser_timestamps(self):
        first = nl.parse('순현금 기업', AS_OF)
        second = nl.parse('순현금 기업', AS_OF)
        self.assertNotEqual(first['source']['parser']['parsed_at_utc'],
                            second['source']['parser']['parsed_at_utc'])
        self.assertEqual(first['spec_id'], second['spec_id'])

    def test_spec_id_is_content_addressed(self):
        first = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 70}])
        second = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 70}])
        third = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 71}])
        self.assertEqual(first['spec_id'], second['spec_id'])
        self.assertNotEqual(first['spec_id'], third['spec_id'])

    def test_set_operator_requires_a_list(self):
        with self.assertRaises(spec_module.SpecError):
            spec_with([{'field': 'hard_veto_status', 'operator': 'in', 'value': 'CLEARED'}])

    def test_malformed_spec_is_rejected_by_schema(self):
        import jsonschema
        with self.assertRaises(jsonschema.ValidationError):
            spec_module.normalise({'schema_version': '1.0', 'as_of_date': AS_OF,
                                   'universe': {}, 'missing_policy': 'exclude',
                                   'filters': {'op': 'xor', 'clauses': []}})


class CompilerTests(unittest.TestCase):
    def test_missing_value_is_unknown_not_zero(self):
        spec = spec_with([{'field': 'net_cash_per_share', 'operator': '>', 'value': 0}])
        result = compiler.run(spec, rows())
        self.assertEqual([r['ticker'] for r in result['results']], ['AAA'])
        # CCC has no net cash figure: it is excluded, not treated as zero and failed.
        self.assertIn('CCC', [r['ticker'] for r in result['excluded_missing_data']])

    def test_missing_policy_require_review_separates_the_row(self):
        spec = spec_with([{'field': 'net_cash_per_share', 'operator': '>', 'value': 0}],
                         missing_policy='require_review')
        result = compiler.run(spec, rows())
        self.assertEqual([r['ticker'] for r in result['needs_review']], ['CCC'])
        self.assertEqual([r['ticker'] for r in result['results']], ['AAA'])

    def test_missing_policy_include_is_explicit_and_marked(self):
        spec = spec_with([{'field': 'net_cash_per_share', 'operator': '>', 'value': 0}],
                         missing_policy='include')
        result = compiler.run(spec, rows())
        included = [r for r in result['results'] if r.get('included_on_missing_data')]
        self.assertEqual([r['ticker'] for r in included], ['CCC'])

    def test_not_equal_on_a_missing_value_is_unknown(self):
        spec = spec_with([{'field': 'price_to_base_value', 'operator': '!=', 'value': 1.0}])
        result = compiler.run(spec, rows())
        self.assertIn('CCC', [r['ticker'] for r in result['excluded_missing_data']])

    def test_or_group_passes_on_one_true_even_with_an_unknown(self):
        spec = spec_with([{'op': 'or', 'clauses': [
            {'field': 'core_score', 'operator': '>=', 'value': 70},
            {'field': 'net_cash_per_share', 'operator': '>', 'value': 0}]}])
        result = compiler.run(spec, rows())
        self.assertIn('CCC', [r['ticker'] for r in result['results']])

    def test_as_of_date_is_an_absolute_cutoff(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 50}])
        result = compiler.run(spec, rows())
        self.assertEqual([r['run_id'] for r in result['excluded_post_cutoff']], ['FUTURE'])
        self.assertNotIn('FUT', [r['ticker'] for r in result['results']])

    def test_universe_filters_by_jurisdiction(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 0}],
                         universe={'jurisdictions': ['KR']})
        result = compiler.run(spec, rows())
        self.assertEqual([r['ticker'] for r in result['results']], ['BBB'])

    def test_nested_domain_field_resolves(self):
        spec = spec_with([{'field': 'domain.moat_trajectory', 'operator': '>=', 'value': 75}])
        result = compiler.run(spec, rows())
        self.assertEqual([r['ticker'] for r in result['results']], ['AAA'])

    def test_sort_places_missing_last(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 0}],
                         sort=[{'field': 'price_to_base_value', 'direction': 'asc'}],
                         missing_policy='include')
        result = compiler.run(spec, rows())
        self.assertEqual(result['results'][-1]['ticker'], 'CCC')

    def test_explain_reports_each_clause(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 70},
                          {'field': 'net_cash_per_share', 'operator': '>', 'value': 0}])
        result = compiler.run(spec, rows())
        explain = result['results'][0]['match_explain']
        self.assertEqual({row['field'] for row in explain},
                         {'core_score', 'net_cash_per_share'})


class NaturalLanguageTests(unittest.TestCase):
    def test_korean_query_resolves_declared_phrases_only(self):
        spec = nl.parse('미국과 한국에서 시총 1조 이상, 순현금이고 최근 3년 매출 CAGR 15% 이상이며 '
                        '희석이 적은 기업 중, 해자가 강하고 Base 가치 이하인 종목 찾아줘.', AS_OF,
                        fx_rates={'KRW': {'per_usd': 1380.2, 'source': 'test'}})
        fields = {c['field'] for c in spec_module.iter_filters(spec)}
        self.assertEqual(fields, {'market_cap_usd', 'net_cash_per_share', 'dilution_watch_status',
                                  'domain.moat_trajectory', 'price_to_base_value'})
        self.assertEqual(spec['universe']['jurisdictions'], ['US', 'KR'])
        # The only thing it could not answer is named, not dropped.
        self.assertEqual([u['suggested_field'] for u in spec['unresolved_conditions']],
                         ['revenue_cagr_3y'])

    def test_moat_is_never_estimated_without_a_harness_run(self):
        spec = nl.parse('해자가 강한 기업', AS_OF)
        clause = spec_module.iter_filters(spec)[0]
        self.assertEqual(clause['field'], 'domain.moat_trajectory')
        self.assertTrue(spec['requires_harness_run'])

    def test_unmapped_phrase_is_preserved_as_unresolved(self):
        spec = nl.parse('경영진이 유머감각이 뛰어난 기업', AS_OF)
        self.assertEqual(spec_module.iter_filters(spec), [])
        self.assertEqual(spec['unresolved_conditions'][0]['reason'], 'unparsed_remainder')

    def test_parser_metadata_is_recorded(self):
        spec = nl.parse('순현금 기업', AS_OF)
        self.assertEqual(spec['source']['parser']['provider'], 'lexicon')
        self.assertTrue(spec['source']['parser']['lexicon_sha256'])

    def test_llm_parser_output_is_validated_not_trusted(self):
        from packages.llm import FixtureProvider, LLMError
        bad = FixtureProvider(responses={'screening_spec': {
            'schema_version': '1.0', 'as_of_date': AS_OF, 'universe': {},
            'missing_policy': 'exclude',
            'filters': {'op': 'and', 'clauses': [{'field': 'core_score', 'operator': 'LIKE', 'value': 1}]}}})
        with self.assertRaises(LLMError):
            nl.parse('anything', AS_OF, provider=bad)

    def test_llm_parser_field_allowlist_is_enforced_after_validation(self):
        from packages.llm import FixtureProvider
        provider = FixtureProvider(responses={'screening_spec': {
            'schema_version': '1.0', 'as_of_date': AS_OF, 'universe': {},
            'missing_policy': 'exclude',
            'filters': {'op': 'and', 'clauses': [
                {'field': 'secret_alpha_signal', 'operator': '>=', 'value': 1}]}}})
        spec = nl.parse('anything', AS_OF, provider=provider)
        self.assertEqual(spec_module.iter_filters(spec), [])
        self.assertEqual(spec['unresolved_conditions'][0]['reason'], 'no_mapped_field')


class RunsIndexTests(unittest.TestCase):
    def test_real_corpus_loads_and_covers_both_markets(self):
        loaded = runs_index.load_rows()
        self.assertGreater(len(loaded), 0)
        summary = runs_index.universe_summary(loaded)
        self.assertIn('US', summary['by_jurisdiction'])
        self.assertIn('KR', summary['by_jurisdiction'])

    def test_korean_run_is_detected_by_currency(self):
        row = runs_index.load_row('000660')
        self.assertEqual(row['jurisdiction'], 'KR')
        self.assertEqual(row['currency'], 'KRW')

    def test_scores_are_copied_from_the_harness_not_recomputed(self):
        row = runs_index.load_row('MSFT')
        aggregate = json.loads((ROOT / 'runs' / 'MSFT' / 'aggregate.json').read_text(encoding='utf-8'))
        self.assertEqual(row['core_score'], aggregate['score_100'])
        self.assertEqual(row['hard_veto_status'], aggregate['hard_veto_status'])
        self.assertEqual(row['archetype'], aggregate['archetype']['id'])

    def test_reading_the_index_never_writes(self):
        before = {p: p.stat().st_mtime_ns for p in (ROOT / 'runs' / 'MSFT').rglob('*') if p.is_file()}
        runs_index.load_rows()
        after = {p: p.stat().st_mtime_ns for p in (ROOT / 'runs' / 'MSFT').rglob('*') if p.is_file()}
        self.assertEqual(before, after)


class StoreTests(unittest.TestCase):
    def test_screen_run_is_written_once_and_content_addressed(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 70}])
        result = compiler.run(spec, rows())
        record = store.build_record(spec, result)
        with tempfile.TemporaryDirectory() as tmp:
            first = store.save(record, tmp)
            original = first.read_text(encoding='utf-8')
            mutated = copy.deepcopy(record)
            mutated['summary']['matched_count'] = 999
            store.save(mutated, tmp)          # same id, must not overwrite
            self.assertEqual(first.read_text(encoding='utf-8'), original)
            self.assertEqual(store.load(record['screen_run_id'], tmp)['summary']['matched_count'],
                             record['summary']['matched_count'])

    def test_record_carries_reproduction_metadata(self):
        spec = spec_with([{'field': 'core_score', 'operator': '>=', 'value': 70}])
        record = store.build_record(spec, compiler.run(spec, rows()))
        self.assertTrue(record['provenance']['code_commit_sha'])
        self.assertEqual(record['as_of_date'], AS_OF)
        self.assertEqual(record['spec']['spec_id'], spec['spec_id'])


class RegistryTests(unittest.TestCase):
    def test_every_lexicon_field_exists_in_the_registry(self):
        registry = Registry()
        for phrase in LEXICON['qualitative_phrases']:
            for row in phrase['filters']:
                self.assertIn(row['field'], registry, f"{phrase['id']} names an unknown field")
        for phrase in LEXICON['metric_phrases']:
            self.assertIn(phrase['field'], registry, f"{phrase['id']} names an unknown field")
        for phrase in LEXICON['sort_phrases']:
            self.assertIn(phrase['field'], registry)

    def test_registry_units_match_the_declared_unit_table(self):
        registry = Registry()
        declared = set(registry.data['units'])
        for field in registry.data['fields']:
            self.assertIn(field['unit'], declared)


if __name__ == '__main__':
    unittest.main()
