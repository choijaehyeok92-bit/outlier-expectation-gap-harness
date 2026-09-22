"""Choosing what to ingest, and ingesting it.

The failures worth pinning here are the quiet ones. A share class spelled with
a hyphen by the regulator and a dot by the vendor drops a real company out of
the candidate list as "no quote" and re-ingests one that is already on disk. A
US quote outage, handled carelessly, hides the Korean universe that never
needed a US quote. And a liquidity rank, left undescribed, starts looking like
a quality score — which is the one thing it must never become.
"""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'data_adapters' / 'fixtures'
AS_OF = '2026-09-21'
ENV = {'POLYGON_API_KEY': 'test-key-not-real', 'SEC_USER_AGENT': 'test contact@example.com',
       'OPENDART_API_KEY': 'TEST'}

from data_adapters import candidates, credentials, universe as universe_store  # noqa: E402
from data_adapters.base import AdapterError                                    # noqa: E402
from data_adapters.market_us.provider import UsHttpMarketDataProvider          # noqa: E402
from data_adapters.testing import FixtureTransport                             # noqa: E402


class RegulatorTransport:
    """One transport over both regulators, so a sync can touch each."""

    offline = True

    def __init__(self):
        self.sec = FixtureTransport(FIXTURES / 'sec')
        self.dart = FixtureTransport(FIXTURES / 'dart',
                                     default={'status': '013', 'message': 'empty'})

    def __call__(self, url, headers):
        return (self.dart if 'opendart' in url else self.sec)(url, headers)


def quotes(**kwargs):
    return UsHttpMarketDataProvider(
        'polygon', transport=FixtureTransport(FIXTURES / 'market_us'), environ=ENV, **kwargs)


class Refusing:
    """A quote provider that cannot reach its vendor."""

    provider_name = 'polygon'

    def grouped_daily(self, session_date):
        raise AdapterError('polygon quote service unavailable: tunnel refused')


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.universe = self.root / 'universe.json'
        self.packs = self.root / 'packs'
        self.runs = self.root / 'runs'          # empty: nothing ingested yet
        # An isolated market root: the repository's own data/market must not
        # decide whether a test about a quote outage sees quotes.
        self.market = self.root / 'market'
        universe_store.sync_live(('US', 'KR'), '2026-09-18', transport=RegulatorTransport(),
                                 environ=ENV, out=self.universe)

    def rank(self, **kwargs):
        kwargs.setdefault('provider', quotes())
        return candidates.rank(AS_OF, universe_path=self.universe, packs_dir=self.packs,
                               runs_dir=self.runs, market_root=self.market, **kwargs)


class SyncTests(Base):
    def test_a_sync_records_exclusions_rather_than_dropping_them(self):
        payload = json.loads(self.universe.read_text(encoding='utf-8'))
        reasons = payload['summary']['excluded_by_reason']
        self.assertIn('ETF', reasons)
        self.assertIn('warrant', reasons)
        self.assertTrue(any(row.get('excluded_reason') for row in payload['securities']))

    def test_an_unknown_market_is_refused_rather_than_silently_skipped(self):
        with self.assertRaises(ValueError):
            universe_store.sync_live(('US', 'JP'), '2026-09-18',
                                     transport=RegulatorTransport(), environ=ENV,
                                     out=self.root / 'x.json')

    def test_enrichment_is_capped_and_the_cap_is_reported(self):
        payload = universe_store.sync_live(
            ('KR',), '2026-09-18', transport=RegulatorTransport(), environ=ENV,
            enrich_limit=9999, max_enrich=5, out=self.root / 'capped.json')
        self.assertEqual(payload['enrich_limit'], 5)
        self.assertIn('capped at 5', payload['enrich_limit_note'])

    def test_a_sync_without_a_contact_is_refused_naming_the_variable(self):
        with self.assertRaises(AdapterError) as caught:
            universe_store.sync_live(('US',), '2026-09-18', transport=RegulatorTransport(),
                                     environ={}, out=self.root / 'y.json')
        self.assertIn('SEC_USER_AGENT', str(caught.exception))


class RankTests(Base):
    def test_candidates_are_ordered_by_dollar_volume(self):
        ranked = self.rank()['candidates']
        volumes = [row['dollar_volume'] for row in ranked]
        self.assertEqual(volumes, sorted(volumes, reverse=True))
        self.assertEqual([row['rank'] for row in ranked], list(range(1, len(ranked) + 1)))

    def test_a_regulator_hyphen_finds_the_vendors_dot(self):
        """SEC writes BRK-B and the vendor writes BRK.B. One character, and the
        company silently becomes 'no quote'."""
        row = next(r for r in self.rank()['candidates'] if r['ticker'] == 'BRK-B')
        self.assertEqual(row['quoted_as'], 'BRK.B')
        self.assertGreater(row['dollar_volume'], 0)

    def test_the_same_rewrite_recognises_an_existing_pack(self):
        """Getting this wrong re-ingests a company that is already on disk."""
        self.packs.mkdir(parents=True)
        (self.packs / 'BRK.B.json').write_text(json.dumps(
            {'ticker': 'BRK.B', 'reporting_currency': 'USD', 'as_of_date': '2026-09-18',
             'facts': [{'metric': 'revenue'}]}), encoding='utf-8')
        tickers = [row['ticker'] for row in self.rank()['candidates']]
        self.assertNotIn('BRK-B', tickers)
        self.assertEqual(self.rank()['already_ingested'], 1)

    def test_an_already_ingested_listing_returns_only_when_asked(self):
        self.packs.mkdir(parents=True)
        (self.packs / 'MSFT.json').write_text(json.dumps(
            {'ticker': 'MSFT', 'reporting_currency': 'USD', 'as_of_date': '2026-09-18',
             'facts': [{'metric': 'revenue'}]}), encoding='utf-8')
        self.assertNotIn('MSFT', [r['ticker'] for r in self.rank()['candidates']])
        with_them = self.rank(include_ingested=True)['candidates']
        row = next(r for r in with_them if r['ticker'] == 'MSFT')
        self.assertTrue(row['already_ingested'])

    def test_korean_listings_are_unranked_with_the_reason_stated(self):
        """KRX quotes one listing per call, so there is no session to rank
        against. Ordering them by a number that does not exist would be worse
        than saying so."""
        unranked = self.rank()['unranked']
        korean = [row for row in unranked if row['jurisdiction'] == 'KR']
        self.assertTrue(korean)
        self.assertTrue(all('KRX' in row['reason_unranked'] for row in korean))
        self.assertTrue(all('dollar_volume' not in row for row in korean))

    def test_a_quote_outage_costs_the_ranking_not_the_list(self):
        """Hiding the Korean universe because a US vendor is down would be the
        same silent loss this module exists to prevent."""
        result = self.rank(provider=Refusing())
        self.assertIsNone(result['ranked_by'])
        self.assertIn('unavailable', result['quote_error'])
        self.assertEqual(result['ranked_count'], 0)
        self.assertGreater(result['unranked_count'], 0)
        self.assertTrue(any(row['jurisdiction'] == 'KR' for row in result['unranked']))

    def test_an_outage_falls_back_to_quotes_already_on_disk(self):
        """One fetch already wrote close and volume for the whole market.
        Spending a request to re-learn what the disk knows is waste; being
        unable to rank at all because the vendor is down is worse."""
        from data_adapters.market_us import bulk
        bulk.write_csv('BRK.B', {'date': '2026-09-18', 'close': 498.11,
                                 'shares_outstanding': None, 'volume': 3_900_000},
                       root=self.market)
        result = self.rank(provider=Refusing())
        self.assertEqual(result['quote_source'], 'local_csv')
        self.assertEqual(result['ranked_by'], 'dollar_volume')
        row = next(r for r in result['candidates'] if r['ticker'] == 'BRK-B')
        self.assertAlmostEqual(row['dollar_volume'], 498.11 * 3_900_000, places=2)
        # The reason the vendor was not used is still reported, not swallowed.
        self.assertIn('unavailable', result['quote_error'])

    def test_a_vendor_answer_is_labelled_as_one(self):
        self.assertEqual(self.rank()['quote_source'], 'vendor')

    def test_an_unquoted_us_listing_is_unranked_not_ranked_last(self):
        """Sorting it to the bottom would read as 'least liquid', which is a
        claim the data does not support."""
        result = self.rank()
        unquoted = [row for row in result['unranked'] if row['jurisdiction'] == 'US']
        self.assertTrue(unquoted)
        self.assertTrue(all('dollar_volume' not in row for row in unquoted))

    def test_the_limit_bounds_the_answer_not_the_universe(self):
        result = self.rank(limit=1)
        self.assertEqual(len(result['candidates']), 1)
        self.assertGreater(result['universe_size'], 1)
        self.assertGreater(result['ranked_count'], 1)

    def test_no_universe_file_is_a_refusal_that_says_what_to_run(self):
        with self.assertRaises(AdapterError) as caught:
            candidates.rank(AS_OF, provider=quotes(), universe_path=self.root / 'missing.json')
        self.assertIn('universe sync', str(caught.exception))

    def test_the_rank_declares_itself_not_evidence(self):
        """A liquidity rank that stopped saying what it is would start being
        read as a quality score."""
        result = self.rank()
        self.assertIn('거래대금', result['ranked_by_note'])
        self.assertIn('Hard Veto', result['is_not_evidence'])


class IngestTests(Base):
    def provider(self):
        from data_adapters.sec import SecEdgarProvider
        return SecEdgarProvider(user_agent=ENV['SEC_USER_AGENT'],
                                transport=FixtureTransport(FIXTURES / 'sec'))

    def test_a_pack_is_written_where_screen_build_reads_it(self):
        result = candidates.ingest_one('MSFT', 'US', '2026-09-18', out_dir=self.packs,
                                       provider=self.provider())
        self.assertEqual(result['ticker'], 'MSFT')
        self.assertGreater(result['facts'], 0)
        self.assertTrue((self.packs / 'MSFT.json').exists())
        from data_adapters.market_us import bulk
        self.assertIn('MSFT', bulk.pack_tickers('2026-09-18', packs_dir=self.packs,
                                                runs_dir=self.runs))

    def test_an_existing_pack_is_not_silently_rebuilt(self):
        """Re-ingesting would replace facts a frozen run may already cite."""
        candidates.ingest_one('MSFT', 'US', '2026-09-18', out_dir=self.packs,
                              provider=self.provider())
        before = (self.packs / 'MSFT.json').read_text(encoding='utf-8')
        again = candidates.ingest_one('MSFT', 'US', '2026-09-18', out_dir=self.packs,
                                      provider=self.provider())
        self.assertEqual(again['status'], 'exists')
        self.assertEqual((self.packs / 'MSFT.json').read_text(encoding='utf-8'), before)

    def test_force_rebuilds_it(self):
        candidates.ingest_one('MSFT', 'US', '2026-09-18', out_dir=self.packs,
                              provider=self.provider())
        again = candidates.ingest_one('MSFT', 'US', '2026-09-18', out_dir=self.packs,
                                      force=True, provider=self.provider())
        self.assertIn(again['status'], ('ok', 'validation_errors'))

    def test_one_bad_ticker_does_not_fail_the_batch(self):
        """A regulator times out on one issuer often enough that an
        all-or-nothing batch would rarely finish."""
        result = candidates.ingest_batch(['MSFT', 'NOT-A-TICKER'], 'US', '2026-09-18',
                                         out_dir=self.packs, environ=ENV,
                                         transport=FixtureTransport(FIXTURES / 'sec'))
        self.assertEqual(result['requested'], 2)
        self.assertEqual(result['failed'], 1)
        by_ticker = {row['ticker']: row for row in result['results']}
        self.assertIn(by_ticker['MSFT']['status'], ('ok', 'validation_errors'))
        self.assertEqual(by_ticker['NOT-A-TICKER']['status'], 'failed')
        self.assertIn('error', by_ticker['NOT-A-TICKER'])

    def test_a_batch_over_the_cap_is_refused_pointing_at_the_queue(self):
        with self.assertRaises(AdapterError) as caught:
            candidates.ingest_batch([f'T{n}' for n in range(11)], 'US', '2026-09-18',
                                    out_dir=self.packs, max_companies=10, environ=ENV,
                                    transport=FixtureTransport(FIXTURES / 'sec'))
        self.assertIn('ingest_pack', str(caught.exception))

    def test_an_empty_batch_is_refused(self):
        with self.assertRaises(AdapterError):
            candidates.ingest_batch([], 'US', '2026-09-18', environ=ENV)


class RequestCostTests(unittest.TestCase):
    """The declared per-company request counts, re-measured.

    A page that is about to queue two hundred companies shows these numbers, so
    they cannot be a comment that drifted. Each test counts what a fixture
    transport actually receives and fails if the adapter's shape changes.
    """

    def test_a_us_pack_costs_what_the_catalogue_says(self):
        from data_adapters.sec import SecEdgarProvider
        transport = FixtureTransport(FIXTURES / 'sec')
        provider = SecEdgarProvider(user_agent=ENV['SEC_USER_AGENT'], transport=transport)
        provider.build_financial_pack('MSFT', '2026-09-18')
        self.assertEqual(len(transport.calls),
                         credentials.REQUESTS_PER_COMPANY['US']['requests'])

    def test_a_kr_pack_costs_what_the_catalogue_says(self):
        import tempfile
        from data_adapters.dart import DartProvider
        from data_adapters.dart.corpcode import CorpCodeCache
        transport = FixtureTransport(FIXTURES / 'dart',
                                     default={'status': '013', 'message': 'empty'})
        with tempfile.TemporaryDirectory() as tmp:
            provider = DartProvider(api_key='TEST', transport=transport,
                                    corp_codes=CorpCodeCache(path=Path(tmp) / 'cc.json'))
            provider.corp_codes.refresh(provider.client.get(
                provider._url('corp_code'), {'crtfc_key': 'TEST'}))
            before = len(transport.calls)          # corpCode is fetched once, not per company
            provider.build_financial_pack('267260', '2026-09-18')
        self.assertEqual(len(transport.calls) - before,
                         credentials.REQUESTS_PER_COMPANY['KR']['requests'])

    def test_the_korean_cost_scales_with_the_years_requested(self):
        """The note says 8 requests per extra year; a caller trimming years to
        stay inside a daily quota is relying on that being true."""
        import tempfile
        from data_adapters.dart import DartProvider
        from data_adapters.dart.corpcode import CorpCodeCache
        counted = {}
        for years in (2, 3, 4):
            transport = FixtureTransport(FIXTURES / 'dart',
                                         default={'status': '013', 'message': 'empty'})
            with tempfile.TemporaryDirectory() as tmp:
                provider = DartProvider(api_key='TEST', transport=transport,
                                        corp_codes=CorpCodeCache(path=Path(tmp) / 'cc.json'))
                provider.corp_codes.refresh(provider.client.get(
                    provider._url('corp_code'), {'crtfc_key': 'TEST'}))
                before = len(transport.calls)
                provider.build_financial_pack('267260', '2026-09-18', years=years)
                counted[years] = len(transport.calls) - before
        self.assertEqual(counted[3] - counted[2], 8)
        self.assertEqual(counted[4] - counted[3], 8)

    def test_the_counts_reach_the_credential_description(self):
        for row in credentials.describe(environ={}):
            self.assertGreater(row['requests'], 0, row['market'])
            self.assertTrue(row['requests_note'], row['market'])
            self.assertNotEqual(row['note'], row['requests_note'],
                                'the credential note and the cost note are different sentences')


class CredentialTests(unittest.TestCase):
    def test_the_description_says_whether_each_exists_and_never_what_it_is(self):
        secret = 'dart-live-DO-NOT-LEAK-0123456789'
        rows = credentials.describe(environ={'OPENDART_API_KEY': secret})
        dart = next(row for row in rows if row['regulator'] == 'DART')
        self.assertTrue(dart['configured'])
        self.assertEqual(dart['env_var'], 'OPENDART_API_KEY')
        self.assertNotIn(secret, repr(rows))
        self.assertNotIn(secret[:12], repr(rows))

    def test_blank_is_not_configured(self):
        rows = credentials.describe(environ={'SEC_USER_AGENT': '   '})
        self.assertFalse(next(r for r in rows if r['regulator'] == 'SEC')['configured'])

    def test_no_credential_arrives_as_an_argument(self):
        import inspect
        for function in (credentials.regulator_provider, universe_store.sync_live,
                         candidates.rank, candidates.ingest_batch):
            names = set(inspect.signature(function).parameters)
            self.assertFalse({'api_key', 'key', 'token', 'user_agent', 'secret'} & names,
                             function.__name__)

    def test_the_worker_kinds_are_declared_with_locks(self):
        workers = json.loads((ROOT / 'config' / 'workers.json').read_text(encoding='utf-8'))
        for kind in ('universe_sync', 'ingest_pack'):
            self.assertIn(kind, workers['kinds'])
            self.assertIn(kind, workers['locks']['by_kind'])
            self.assertFalse(workers['kinds'][kind]['spends_money'])


if __name__ == '__main__':
    unittest.main()
