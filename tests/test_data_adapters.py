"""SEC and DART ingestion: one shape for two regulators, and the refusals.

These run entirely offline against recorded fixtures. The rules being tested
are the ones that corrupt a series quietly rather than loudly: a consolidated
and an unconsolidated figure in the same trend, a nine-month cumulative read as
a quarter, a blank cell read as zero, a filing from after the cutoff, and a
Korean account name guessed at instead of mapped.
"""
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'data_adapters' / 'fixtures'
EMPTY_DART = {'status': '013', 'message': '조회된 데이타가 없습니다.'}
AS_OF = '2026-09-18'

try:
    import yaml                                             # noqa: F401
    from data_adapters import universe
    from data_adapters.base import ConsolidationMixError    # noqa: F401
    from data_adapters.dart import DartProvider
    from data_adapters.dart.accounts import AccountResolver
    from data_adapters.dart.corpcode import CorpCodeCache, parse_corp_code_zip
    from data_adapters.dart.periods import PeriodResolver
    from data_adapters.dart.provider import parse_amount, load_config as load_dart_config
    from data_adapters.marketdata import CsvMarketDataProvider
    from data_adapters.market_kr import KrxMarketDataProvider
    from data_adapters.market_kr.provider import KrMarketCsvProvider
    from data_adapters.market_us import UsMarketDataProvider
    from data_adapters.pack import FinancialPackBuilder, choose_consolidation, validate_pack
    from data_adapters.sec import SecEdgarProvider
    from data_adapters.sec.xbrl import period_kind_for
    from data_adapters.testing import FixtureTransport, fixture_key
    from data_adapters.types import FinancialFact
    ADAPTERS = True
    SKIP = ''
except Exception as error:                                  # pragma: no cover
    ADAPTERS = False
    SKIP = f'data_adapters unavailable: {error}'


def dart_provider(extra=None, default=EMPTY_DART):
    transport = FixtureTransport(FIXTURES / 'dart', extra=extra, default=default)
    cache = CorpCodeCache(
        path='/nonexistent/corp_codes.json',
        entries=parse_corp_code_zip(transport('https://opendart.fss.or.kr/api/corpCode.xml', {})))
    return DartProvider(api_key='TEST-KEY', transport=transport, corp_codes=cache), transport


def sec_provider(extra=None):
    transport = FixtureTransport(FIXTURES / 'sec', extra=extra)
    return SecEdgarProvider(user_agent='outlier-harness test contact@example.com',
                            transport=transport), transport


@unittest.skipUnless(ADAPTERS, SKIP)
class UnitParsingTests(unittest.TestCase):
    def test_comma_formatted_amount(self):
        self.assertEqual(parse_amount('1,234,567'), 1234567.0)

    def test_parenthesised_amount_is_negative(self):
        self.assertEqual(parse_amount('(12,000)'), -12000.0)

    def test_blank_and_dash_are_not_zero(self):
        for value in ('', '-', '–', None, 'N/A'):
            self.assertIsNone(parse_amount(value), f'{value!r} must be unknown, not zero')


@unittest.skipUnless(ADAPTERS, SKIP)
class AccountMappingTests(unittest.TestCase):
    def setUp(self):
        self.resolver = AccountResolver()

    def test_account_id_wins(self):
        result = self.resolver.resolve('ifrs-full_Revenue', '아무이름', 'income')
        self.assertEqual((result.metric, result.stage), ('revenue', 'account_id'))

    def test_label_match_with_normalisation(self):
        result = self.resolver.resolve(None, ' 매 출 액 ', 'income')
        self.assertEqual((result.metric, result.stage), ('revenue', 'label'))

    def test_statement_context_separates_identical_labels(self):
        balance = self.resolver.resolve(None, '현금및현금성자산', 'balance_sheet')
        flow = self.resolver.resolve(None, '기말현금및현금성자산', 'cash_flow')
        self.assertEqual(balance.metric, 'cash')
        self.assertEqual(flow.metric, 'ending_cash')
        self.assertEqual(flow.stage, 'statement_label')

    def test_heuristic_is_last_before_review(self):
        # A wording no explicit map holds, but whose tokens are unambiguous.
        result = self.resolver.resolve(None, '영업활동에서 창출된 현금흐름', 'cash_flow')
        self.assertEqual((result.metric, result.stage), ('operating_cash_flow', 'heuristic'))
        self.assertIn('heuristic', result.review_reason)

    def test_unmapped_line_is_preserved_for_review_not_dropped(self):
        result = self.resolver.resolve(None, '지분법적용투자주식처분이익', 'income')
        self.assertEqual((result.metric, result.stage), ('other', 'unmapped'))
        self.assertTrue(result.requires_review)
        self.assertEqual(result.metric_detail, '지분법적용투자주식처분이익')

    def test_combined_sga_is_escalated_rather_than_split(self):
        result = self.resolver.resolve(None, '판매비와관리비', 'income')
        self.assertEqual(result.stage, 'review_required')
        self.assertTrue(result.requires_review)
        self.assertEqual(result.metric_detail, 'selling_general_and_administrative_combined')

    def test_mapping_version_is_recorded(self):
        self.assertTrue(self.resolver.version)


@unittest.skipUnless(ADAPTERS, SKIP)
class PeriodTests(unittest.TestCase):
    def setUp(self):
        self.resolver = PeriodResolver(load_dart_config())

    def test_quarter_boundaries_for_december_year_end(self):
        third = self.resolver.periods(2026, '11014', 12)
        self.assertEqual((third.quarter_start, third.quarter_end), ('2026-07-01', '2026-09-30'))
        self.assertEqual((third.ytd_start, third.ytd_end), ('2026-01-01', '2026-09-30'))
        self.assertEqual(third.ytd_months, 9)

    def test_non_december_year_end_shifts_every_quarter(self):
        third = self.resolver.periods(2026, '11014', 3)
        self.assertEqual(third.fiscal_year_start, '2025-04-01')
        self.assertEqual(third.fiscal_year_end, '2026-03-31')
        self.assertEqual((third.quarter_start, third.quarter_end), ('2025-10-01', '2025-12-31'))

    def test_quarter_and_ytd_are_separate_facts(self):
        periods = self.resolver.periods(2026, '11014', 12)
        rows = self.resolver.plan_row('IS', periods, 1000, 2800)
        kinds = {row['period_kind']: row for row in rows}
        self.assertEqual(set(kinds), {'quarter', 'ytd'})
        self.assertEqual(kinds['quarter']['amount'], 1000)
        self.assertEqual(kinds['ytd']['amount'], 2800)
        self.assertEqual(kinds['quarter']['period_start'], '2026-07-01')
        self.assertEqual(kinds['ytd']['period_start'], '2026-01-01')

    def test_cash_flow_never_yields_a_fabricated_quarter(self):
        periods = self.resolver.periods(2026, '11014', 12)
        rows = self.resolver.plan_row('CF', periods, 2800, None)
        self.assertEqual([row['period_kind'] for row in rows], ['ytd'])
        self.assertEqual(rows[0]['period_start'], '2026-01-01')

    def test_single_income_column_in_an_interim_report_is_flagged(self):
        periods = self.resolver.periods(2026, '11012', 12)
        rows = self.resolver.plan_row('IS', periods, 2000, None)
        self.assertEqual(rows[0]['period_kind'], 'ytd')
        self.assertTrue(rows[0]['requires_review'])

    def test_first_quarter_single_column_is_unambiguous(self):
        periods = self.resolver.periods(2026, '11013', 12)
        rows = self.resolver.plan_row('IS', periods, 900, None)
        self.assertEqual(rows[0]['period_kind'], 'quarter')
        self.assertFalse(rows[0]['requires_review'])

    def test_balance_sheet_is_an_instant(self):
        periods = self.resolver.periods(2026, '11012', 12)
        rows = self.resolver.plan_row('BS', periods, 50000, None)
        self.assertEqual(rows[0]['period_kind'], 'instant')
        self.assertIsNone(rows[0]['period_start'])

    def test_unknown_report_code_is_refused(self):
        with self.assertRaises(ValueError):
            self.resolver.periods(2026, '99999', 12)


@unittest.skipUnless(ADAPTERS, SKIP)
class ConsolidationTests(unittest.TestCase):
    def test_preference_picks_consolidated(self):
        facts = [FinancialFact('K', 'revenue', 1, 'fy', 'income', 'd.xml', consolidation_basis='OFS'),
                 FinancialFact('K', 'revenue', 2, 'fy', 'income', 'd.xml', consolidation_basis='CFS')]
        self.assertEqual(choose_consolidation(facts), 'CFS')

    def test_pack_never_mixes_the_two_bases(self):
        from data_adapters.types import Filing
        filing = Filing('K', 'DART', '사업보고서', '2026-03-17', '20260317000001')
        name = 'note'
        facts = [FinancialFact('K', 'revenue', 100, 'fy', 'income',
                               ' '.join([]) or f'사업보고서_2026-03-17_20260317000001.xml',
                               consolidation_basis=basis, period_end='2025-12-31')
                 for basis in ('CFS', 'OFS')]
        builder = FinancialPackBuilder('267260', AS_OF)
        pack = builder.build([filing], facts)
        self.assertEqual(len(pack['facts']), 1)
        self.assertEqual(pack['consolidation_basis'], 'CFS')
        self.assertTrue(any('never mixes' in w['message'] for w in pack['extraction_warnings']))
        self.assertIn(name, name)

    def test_provider_falls_back_to_unconsolidated_when_no_cfs(self):
        # Every CFS call answers "no data"; the provider must use OFS, not give up.
        extra = {}
        for year in (2023, 2024, 2025, 2026):
            for code in ('11011', '11012', '11013', '11014'):
                key = fixture_key(f'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
                                  f'?corp_code=01515323&bsns_year={year}&reprt_code={code}&fs_div=CFS')
                extra[key] = EMPTY_DART
        provider, _ = dart_provider(extra=extra)
        pack = provider.build_financial_pack('267260', AS_OF)
        self.assertEqual(pack['ingestion']['consolidation_basis'], 'OFS')
        self.assertGreater(len(pack['facts']), 0)


@unittest.skipUnless(ADAPTERS, SKIP)
class DartIngestionTests(unittest.TestCase):
    def setUp(self):
        self.provider, self.transport = dart_provider()
        self.pack = self.provider.build_financial_pack('267260', AS_OF)

    def test_corp_code_cache_resolves_in_both_directions(self):
        cache = self.provider.corp_codes
        entry = cache.by_stock_code('267260')
        self.assertEqual(cache.by_corp_code(entry.corp_code).corp_name, entry.corp_name)
        self.assertEqual(cache.resolve(entry.corp_name).stock_code, '267260')
        self.assertTrue(all(e.listed for e in cache.listed))

    def test_issuer_carries_the_market_segment_and_fiscal_calendar(self):
        issuer = self.provider.resolve_issuer('267260')
        self.assertEqual(issuer.extra['corp_cls'], 'Y')
        self.assertEqual(self.provider.fiscal_year_end_month(issuer), 12)
        self.assertFalse(issuer.extra['fiscal_year_end_assumed'])

    def test_pack_is_schema_and_invariant_clean(self):
        self.assertEqual(validate_pack(self.pack), [])

    def test_pack_satisfies_stage_0_without_touching_intake_config(self):
        from harness_core import intake
        policy = json.loads((ROOT / 'config' / 'intake.json').read_text(encoding='utf-8'))
        coverage = intake.coverage(self.pack, policy)
        self.assertEqual(coverage['blocking_gaps'], [],
                         'Korean form names in the existing source_regex must satisfy Stage 0')
        self.assertEqual(intake.pack_invariants(self.pack), [])

    def test_cutoff_excludes_a_later_filing(self):
        self.assertEqual(self.pack['ingestion']['excluded_post_cutoff'], 1)
        for document in self.pack['documents']:
            self.assertLessEqual(document['filing_date'] or '', AS_OF)

    def test_interim_report_yields_both_a_quarter_and_a_year_to_date(self):
        rows = [f for f in self.pack['facts']
                if f['metric'] == 'revenue' and (f['period_end'] or '').startswith('2026-06')]
        kinds = {row['period_kind']: row['value_reported'] for row in rows}
        self.assertEqual(set(kinds), {'quarter', 'ytd'})
        self.assertLess(kinds['quarter'], kinds['ytd'])

    def test_interim_cash_flow_is_year_to_date_only(self):
        rows = [f for f in self.pack['facts'] if f['metric'] == 'operating_cash_flow'
                and (f['period_end'] or '').startswith('2026-06')]
        self.assertTrue(rows)
        self.assertEqual({row['period_kind'] for row in rows}, {'ytd'})

    def test_cost_metrics_are_positive_magnitudes(self):
        for fact in self.pack['facts']:
            if fact['metric'] == 'capex' and fact['value_reported'] is not None:
                self.assertGreaterEqual(fact['value_reported'], 0)

    def test_share_counts_are_collected(self):
        shares = [f for f in self.pack['facts'] if f['statement'] == 'shares']
        self.assertTrue(shares)
        self.assertEqual({f['unit_kind'] for f in shares}, {'shares'})
        self.assertIn('period_end_shares', {f['metric'] for f in shares})

    def test_capital_events_are_recorded_without_touching_the_veto(self):
        events = self.pack['ingestion']['capital_events']
        self.assertTrue(any(e['kind'] == 'convertible' for e in events))
        for event in events:
            self.assertLessEqual(event['filing_date'], AS_OF)
            self.assertNotIn('hard_veto', json.dumps(event, ensure_ascii=False))

    def test_empty_status_is_not_an_error(self):
        result = self.provider.call('bonus_issue', corp_code='01515323')
        self.assertTrue(result['empty'])
        self.assertEqual(result['rows'], [])

    def test_account_map_version_is_in_the_pack_provenance(self):
        self.assertEqual(self.pack['ingestion']['account_map_version'],
                         AccountResolver().version)

    def test_missing_api_key_is_refused_not_guessed(self):
        provider, _ = dart_provider()
        provider.api_key = None
        with self.assertRaises(Exception) as caught:
            provider.call('filing_search', corp_code='01515323')
        self.assertIn('OPENDART_API_KEY', str(caught.exception))

    def test_provider_exposes_no_price_method(self):
        for attribute in ('get_snapshot', 'get_price_history', 'get_market_cap'):
            self.assertFalse(hasattr(self.provider, attribute),
                             'a regulator must not serve prices')


@unittest.skipUnless(ADAPTERS, SKIP)
class SecIngestionTests(unittest.TestCase):
    def setUp(self):
        self.provider, self.transport = sec_provider()
        self.pack = self.provider.build_financial_pack('MSFT', AS_OF)

    def test_pack_is_schema_and_invariant_clean(self):
        self.assertEqual(validate_pack(self.pack), [])

    def test_same_shape_as_the_korean_pack(self):
        korean, _ = dart_provider()
        other = korean.build_financial_pack('267260', AS_OF)
        self.assertEqual(set(self.pack) - {'ingestion'}, set(other) - {'ingestion'})

    def test_cutoff_excludes_later_filings_and_later_facts(self):
        self.assertEqual(self.pack['ingestion']['excluded_post_cutoff'], 1)
        for fact in self.pack['facts']:
            self.assertLessEqual(fact['filing_date'] or '', AS_OF)

    def test_period_kinds_come_from_declared_spans(self):
        policy = self.provider.config['period_spans']
        self.assertEqual(period_kind_for(None, '2026-06-30', policy)[0], 'instant')
        self.assertEqual(period_kind_for('2025-07-01', '2026-06-30', policy)[0], 'fy')
        self.assertEqual(period_kind_for('2026-04-01', '2026-06-30', policy)[0], 'quarter')
        kind, review, _ = period_kind_for('2020-01-01', '2026-06-30', policy)
        self.assertTrue(review, 'an unrecognised span must be flagged, not assigned')

    def test_restatement_is_flagged_and_the_superseded_value_kept(self):
        restated = [f for f in self.pack['facts'] if f['is_restated']]
        self.assertTrue(restated)
        self.assertIn('superseded', restated[0]['review_reason'])

    def test_combined_sga_is_escalated_rather_than_split(self):
        rows = [f for f in self.pack['facts']
                if f['reported_label'] == 'SellingGeneralAndAdministrativeExpense']
        self.assertTrue(rows)
        self.assertEqual(rows[0]['metric'], 'other')
        self.assertTrue(rows[0]['requires_review'])

    def test_download_plan_reuses_the_existing_intake_checklist(self):
        plan = self.pack['ingestion']['download_plan']
        self.assertIn('download', plan)
        self.assertTrue(any(row.get('requirement') == 'latest_annual' for row in plan['download']))

    def test_missing_user_agent_is_refused(self):
        provider = SecEdgarProvider(user_agent=None,
                                    transport=FixtureTransport(FIXTURES / 'sec'))
        with self.assertRaises(Exception) as caught:
            provider.resolve_issuer('MSFT')
        self.assertIn('SEC_USER_AGENT', str(caught.exception))

    def test_provider_exposes_no_price_method(self):
        for attribute in ('get_snapshot', 'get_price_history'):
            self.assertFalse(hasattr(self.provider, attribute))


@unittest.skipUnless(ADAPTERS, SKIP)
class UniverseTests(unittest.TestCase):
    def test_us_exclusions_are_recorded_with_a_reason(self):
        provider, _ = sec_provider()
        rows = {s.ticker: s for s in provider.list_universe()}
        self.assertIsNone(rows['MSFT'].excluded_reason)
        self.assertEqual(rows['SPY'].security_type, 'etf')
        self.assertEqual(rows['AJAX'].security_type, 'spac')
        self.assertEqual(rows['AJAX-W'].security_type, 'warrant')
        self.assertTrue(rows['SOMEC'].excluded_reason)

    def test_korean_universe_uses_corp_cls_for_the_market_segment(self):
        provider, _ = dart_provider()
        rows = {s.ticker: s for s in provider.list_universe(enrich_limit=10)}
        self.assertEqual(rows['005930'].exchange, 'KOSPI')
        self.assertEqual(rows['247540'].exchange, 'KOSDAQ')
        self.assertTrue(rows['900999'].excluded_reason, 'KONEX is excluded by config')
        self.assertEqual(rows['456780'].security_type, 'spac')

    def test_unenriched_korean_rows_say_they_are_unsure(self):
        provider, _ = dart_provider()
        rows = provider.list_universe(enrich_limit=0)
        self.assertTrue(all(s.requires_review and s.exchange == 'KRX' for s in rows),
                        'without corp_cls the market segment must not be guessed')

    def test_unlisted_corporations_are_not_in_the_universe(self):
        provider, _ = dart_provider()
        tickers = {s.ticker for s in provider.list_universe(enrich_limit=10)}
        self.assertNotIn(None, tickers)
        self.assertEqual(len([t for t in tickers if t]), len(tickers))

    def test_sync_survives_one_market_failing(self):
        provider, _ = dart_provider()
        broken = SecEdgarProvider(user_agent=None, transport=FixtureTransport(FIXTURES / 'sec'))
        payload = universe.sync({'US': broken, 'KR': provider}, as_of_date=AS_OF,
                                KR={'enrich_limit': 10})
        self.assertIn('US', payload['errors'])
        self.assertIn('KR', payload['markets'])
        self.assertTrue(universe.investable(payload))

    def test_round_trip_through_disk(self):
        provider, _ = dart_provider()
        payload = universe.sync({'KR': provider}, as_of_date=AS_OF, KR={'enrich_limit': 10})
        with tempfile.TemporaryDirectory() as tmp:
            path = universe.save(payload, Path(tmp) / 'securities.json')
            self.assertEqual(universe.load(path)['summary'], payload['summary'])


@unittest.skipUnless(ADAPTERS, SKIP)
class MarketDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for market, ticker in (('KR', '267260'), ('US', 'MSFT')):
            directory = Path(self.tmp.name) / market
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f'{ticker}.csv').write_text(
                'date,close,shares_outstanding\n'
                '2026-09-16,100,1000\n2026-09-18,110,1000\n2026-09-30,900,1000\n',
                encoding='utf-8')

    def test_snapshot_never_returns_an_observation_after_the_cutoff(self):
        provider = KrMarketCsvProvider(root=self.tmp.name)
        security = provider.resolve_security('267260')
        self.assertEqual(provider.get_snapshot(security, AS_OF).as_of_date, '2026-09-18')
        self.assertEqual(provider.get_snapshot(security, '2026-09-17').as_of_date, '2026-09-16')

    def test_market_cap_is_derived_only_from_disclosed_inputs(self):
        provider = UsMarketDataProvider(root=self.tmp.name)
        security = provider.resolve_security('MSFT')
        self.assertEqual(provider.get_market_cap(security, AS_OF), 110 * 1000)
        self.assertIsNone(provider.get_market_cap(provider.resolve_security('NOPE'), AS_OF))

    def test_price_history_respects_the_window(self):
        provider = KrMarketCsvProvider(root=self.tmp.name)
        rows = provider.get_price_history(provider.resolve_security('267260'),
                                          '2026-09-17', '2026-09-30')
        self.assertEqual([r['date'] for r in rows], ['2026-09-18', '2026-09-30'])

    def test_krx_provider_parses_a_krx_shaped_response(self):
        payload = json.dumps({'output': [
            {'TRD_DD': '2026/09/18', 'TDD_CLSPRC': '418,500', 'MKTCAP': '15,066,000,000,000',
             'LIST_SHRS': '36,000,000'}]}).encode('utf-8')
        provider = KrxMarketDataProvider(transport=lambda url, headers: payload)
        snapshot = provider.get_snapshot(provider.resolve_security('267260'), AS_OF)
        self.assertEqual(snapshot.as_of_date, '2026-09-18')
        self.assertEqual(snapshot.close, 418500.0)
        self.assertEqual(snapshot.currency, 'KRW')

    def test_krx_provider_falls_back_when_the_venue_is_unreachable(self):
        def broken(url, headers):
            raise RuntimeError('blocked')
        provider = KrxMarketDataProvider(transport=broken,
                                         fallback=KrMarketCsvProvider(root=self.tmp.name))
        snapshot = provider.get_snapshot(provider.resolve_security('267260'), AS_OF)
        self.assertEqual(snapshot.as_of_date, '2026-09-18')

    def test_market_provider_exposes_no_filing_method(self):
        provider = KrMarketCsvProvider(root=self.tmp.name)
        for attribute in ('list_filings', 'fetch_structured_financials', 'build_financial_pack'):
            self.assertFalse(hasattr(provider, attribute))


@unittest.skipUnless(ADAPTERS, SKIP)
class SecretHygieneTests(unittest.TestCase):
    def test_api_key_never_reaches_a_fixture_filename(self):
        key = fixture_key('https://opendart.fss.or.kr/api/list.json'
                          '?crtfc_key=SUPERSECRET&corp_code=01515323')
        self.assertNotIn('SUPERSECRET', key)
        self.assertIn('corp_code=01515323', key)

    def test_no_committed_fixture_carries_a_key(self):
        for path in FIXTURES.rglob('*.json'):
            body = path.read_text(encoding='utf-8')
            self.assertNotIn('crtfc_key', body, f'{path} leaks an API key')


if __name__ == '__main__':
    unittest.main()
