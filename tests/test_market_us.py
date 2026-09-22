"""US quote ingestion: the bulk path, and the ways a price quietly goes wrong.

These run offline against recorded fixtures. The rules under test are the ones
whose failure is silent rather than loud: a ticker truncated at a dot, a
session date read off an epoch in the wrong timezone, a holiday mistaken for
"no data", a listing that disappears from a screen because nobody said its
quote was missing, and a share count invented by a vendor that has no standing
to report one.
"""
import csv
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'data_adapters' / 'fixtures' / 'market_us'
AS_OF = '2026-09-21'          # a Monday; the last session before it is Friday the 18th
ENV = {'POLYGON_API_KEY': 'test-key-not-real', 'EODHD_API_KEY': 'test-key-not-real'}

from data_adapters.base import AdapterError                          # noqa: E402
from data_adapters.market_us import bulk                             # noqa: E402
from data_adapters.market_us.provider import (UsHttpMarketDataProvider,  # noqa: E402
                                              UsMarketCsvProvider, load_config,
                                              parse_row, utc_date)
from data_adapters.testing import FixtureTransport, fixture_key      # noqa: E402


def provider(name='polygon', **kwargs):
    return UsHttpMarketDataProvider(name, transport=FixtureTransport(FIXTURES),
                                    environ=ENV, **kwargs)


class ParsingTests(unittest.TestCase):
    def test_a_dot_in_a_ticker_is_not_an_exchange_suffix(self):
        """BRK.B truncated to BRK is a different company, and nothing downstream
        would notice: the CSV would be written, the price would look sane, and
        the screen would report a class A price against class B financials."""
        rows = {row['ticker']: row for row in provider().grouped_daily('2026-09-18')}
        self.assertIn('BRK.B', rows)
        self.assertNotIn('BRK', rows)

    def test_a_declared_suffix_is_stripped(self):
        rows = {row['ticker']: row for row in provider('eodhd').grouped_daily('2026-09-18')}
        self.assertIn('MSFT', rows)
        self.assertNotIn('MSFT.US', rows)

    def test_the_session_date_comes_from_the_request_not_the_epoch_timezone(self):
        rows = provider().grouped_daily('2026-09-18')
        self.assertTrue(all(row['date'] == '2026-09-18' for row in rows))

    def test_an_epoch_becomes_a_utc_session_date(self):
        self.assertEqual(utc_date(1789704000000), '2026-09-18')
        self.assertIsNone(utc_date(None))

    def test_a_row_without_a_close_is_dropped_not_written_as_zero(self):
        fields = {'ticker': 'T', 'close': 'c', 'date': None}
        self.assertIsNone(parse_row({'T': 'AAA', 'c': None}, fields, '2026-09-18', None))
        self.assertIsNone(parse_row({'T': 'AAA', 'c': ''}, fields, '2026-09-18', None))

    def test_two_vendors_with_different_field_names_produce_the_same_shape(self):
        polygon = {r['ticker']: r['close'] for r in provider().grouped_daily('2026-09-18')}
        eodhd = {r['ticker']: r['close'] for r in provider('eodhd').grouped_daily('2026-09-18')}
        self.assertEqual(polygon, eodhd)

    def test_a_per_ticker_history_is_ordered_and_bounded(self):
        instance = provider()
        rows = instance.get_price_history(instance.resolve_security('MSFT'),
                                          '2026-09-14', '2026-09-18')
        self.assertEqual([r['date'] for r in rows], ['2026-09-14', '2026-09-18'])


class SessionTests(unittest.TestCase):
    def test_a_weekend_cutoff_walks_back_to_the_previous_session(self):
        result = bulk.session_rows(AS_OF, provider(), load_config())
        self.assertEqual(result['session_date'], '2026-09-18')
        self.assertEqual(result['sessions_tried'],
                         ['2026-09-21', '2026-09-20', '2026-09-19', '2026-09-18'])

    def test_the_walk_never_goes_forward(self):
        """A price printed after the cutoff is the retroactive use the strategy
        forbids; a lookback that could step forward would import one silently."""
        result = bulk.session_rows(AS_OF, provider(), load_config())
        self.assertTrue(all(day <= AS_OF for day in result['sessions_tried']))

    def test_an_empty_response_means_no_session_not_no_data(self):
        config = {**load_config(), 'max_session_lookback_days': 1}
        result = bulk.session_rows(AS_OF, provider(), config)
        self.assertIsNone(result['session_date'])
        self.assertEqual(result['rows'], [])


class SharesTests(unittest.TestCase):
    def test_share_counts_come_from_the_packs_not_from_the_quote_vendor(self):
        index = bulk.shares_index(AS_OF)
        self.assertIn('MSFT', index)
        self.assertGreater(index['MSFT']['shares_outstanding'], 1e9)
        self.assertLessEqual(index['MSFT']['period_end'], AS_OF)

    def test_a_share_fact_after_the_cutoff_is_not_used(self):
        pack = {'facts': [
            {'metric': 'period_end_shares', 'period_kind': 'instant',
             'value_reported': 100, 'period_end': '2026-06-30', 'scale_multiplier': 1},
            {'metric': 'period_end_shares', 'period_kind': 'instant',
             'value_reported': 999, 'period_end': '2026-12-31', 'scale_multiplier': 1}]}
        self.assertEqual(bulk._pack_shares(pack, AS_OF)['shares_outstanding'], 100)

    def test_the_scale_multiplier_is_applied(self):
        pack = {'facts': [{'metric': 'period_end_shares', 'period_kind': 'instant',
                           'value_reported': 12.5, 'period_end': '2026-06-30',
                           'scale_multiplier': 1_000_000}]}
        self.assertEqual(bulk._pack_shares(pack, AS_OF)['shares_outstanding'], 12_500_000)

    def test_a_korean_pack_does_not_supply_shares_to_a_us_listing(self):
        index = bulk.shares_index(AS_OF)
        self.assertNotIn('000660', index)


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_fetch(self, **kwargs):
        return bulk.fetch_day(AS_OF, provider=provider(), root=self.tmp.name, **kwargs)

    def test_a_listing_with_a_pack_but_no_quote_is_named_not_skipped(self):
        """The fixture has no RKLB row. A screen that silently lost it would
        report a smaller universe and give no reason."""
        result = self.run_fetch()
        self.assertIn('RKLB', result['missing_price'])
        self.assertFalse((Path(self.tmp.name) / 'US' / 'RKLB.csv').exists())

    def test_a_vendor_row_with_no_pack_is_not_written(self):
        result = self.run_fetch()
        self.assertNotIn('SPY', [row['ticker'] for row in result['written']])
        self.assertFalse((Path(self.tmp.name) / 'US' / 'SPY.csv').exists())

    def test_a_missing_share_count_leaves_the_column_empty_never_zero(self):
        self.run_fetch()
        with (Path(self.tmp.name) / 'US' / 'BRK.B.csv').open(encoding='utf-8') as handle:
            row = next(csv.DictReader(handle))
        self.assertEqual(row['close'], '498.11')
        self.assertEqual(row['shares_outstanding'], '')

    def test_a_dry_run_reports_without_writing(self):
        result = self.run_fetch(write=False)
        self.assertGreater(result['written_count'], 0)
        self.assertFalse((Path(self.tmp.name) / 'US').exists())

    def test_running_twice_leaves_the_same_file(self):
        """The worker's lease can expire and hand the job to a second worker."""
        self.run_fetch()
        first = (Path(self.tmp.name) / 'US' / 'MSFT.csv').read_text(encoding='utf-8')
        self.run_fetch()
        self.assertEqual((Path(self.tmp.name) / 'US' / 'MSFT.csv').read_text(encoding='utf-8'),
                         first)

    def test_other_dates_in_the_file_are_preserved(self):
        path = Path(self.tmp.name) / 'US' / 'MSFT.csv'
        path.parent.mkdir(parents=True)
        path.write_text('date,close,shares_outstanding\n2026-09-11,500.0,7000000000\n',
                        encoding='utf-8')
        self.run_fetch()
        with path.open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([r['date'] for r in rows], ['2026-09-11', '2026-09-18'])

    def test_a_restated_close_for_the_same_date_overwrites(self):
        path = Path(self.tmp.name) / 'US' / 'MSFT.csv'
        path.parent.mkdir(parents=True)
        path.write_text('date,close,shares_outstanding\n2026-09-18,1.23,\n', encoding='utf-8')
        self.run_fetch()
        with path.open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['close'], '511.24')

    def test_named_tickers_override_the_scope(self):
        result = self.run_fetch(tickers=['MSFT'])
        self.assertEqual([row['ticker'] for row in result['written']], ['MSFT'])

    def test_scope_all_writes_what_the_vendor_returned(self):
        result = self.run_fetch(scope='all')
        self.assertIn('SPY', [row['ticker'] for row in result['written']])
        self.assertEqual(result['missing_price'], [])

    def test_the_written_price_reaches_the_snapshot_reader(self):
        self.run_fetch()
        reader = UsMarketCsvProvider(root=self.tmp.name)
        snapshot = reader.get_snapshot(reader.resolve_security('MSFT'), AS_OF)
        self.assertEqual(snapshot.as_of_date, '2026-09-18')
        self.assertEqual(snapshot.close, 511.24)
        self.assertGreater(snapshot.shares_outstanding, 1e9)

    def test_market_cap_is_the_close_times_the_disclosed_share_count(self):
        """Neither number is authoritative alone: the vendor has no standing to
        report a share count and the regulator publishes no price."""
        from packages.screening.metrics import MetricCalculator
        import json as _json
        self.run_fetch()
        reader = UsMarketCsvProvider(root=self.tmp.name)
        snapshot = reader.get_snapshot(reader.resolve_security('MSFT'), AS_OF)
        pack = _json.loads((ROOT / 'runs' / 'MSFT' / 'sources' / 'financials'
                            / 'normalized_financials.json').read_text(encoding='utf-8'))
        computed = MetricCalculator(pack, market_snapshot=snapshot.to_dict()).compute(AS_OF)
        self.assertAlmostEqual(computed['metrics']['market_cap'],
                               snapshot.close * snapshot.shares_outstanding, places=2)
        self.assertEqual(computed['provenance']['market_cap']['method'], 'market:close*shares')

    def test_coverage_counts_against_the_packs(self):
        before = bulk.coverage(AS_OF, root=self.tmp.name)
        self.assertEqual(before['priced'], 0)
        self.assertEqual(before['packs'], len(before['unpriced']))
        self.run_fetch()
        after = bulk.coverage(AS_OF, root=self.tmp.name)
        self.assertEqual(after['priced'], after['packs'] - 1)     # RKLB has no quote
        self.assertEqual(after['unpriced'], ['RKLB'])
        self.assertEqual(after['without_shares'], ['BRK.B'])


class SecretTests(unittest.TestCase):
    def test_a_recorded_fixture_filename_cannot_carry_a_key(self):
        """A fixture is committed and pushed. A key in its name is a key in the
        repository's history, and history is not something you can recall."""
        for secret_param in ('api_token', 'apiKey', 'crtfc_key', 'token'):
            key = fixture_key(f'https://example.com/api/bulk?{secret_param}=SUPERSECRET&fmt=json')
            self.assertNotIn('SUPERSECRET', key)

    def test_the_catalogue_says_whether_a_key_exists_and_never_what_it_is(self):
        rows = bulk.describe(environ={'POLYGON_API_KEY': 'sk-live-abcdef123456'})
        polygon = next(row for row in rows if row['name'] == 'polygon')
        self.assertTrue(polygon['configured'])
        self.assertEqual(polygon['env_var'], 'POLYGON_API_KEY')
        serialised = repr(rows)
        for fragment in ('sk-live', 'abcdef', '123456'):
            self.assertNotIn(fragment, serialised)

    def test_an_absent_key_is_a_refusal_that_names_the_variable(self):
        instance = UsHttpMarketDataProvider('polygon', transport=FixtureTransport(FIXTURES),
                                            environ={})
        with self.assertRaises(AdapterError) as caught:
            instance.grouped_daily('2026-09-18')
        self.assertIn('POLYGON_API_KEY', str(caught.exception))

    def test_a_key_is_never_taken_from_an_argument(self):
        """A key that can arrive in a call arrives in a job payload, and this
        repository serves job payloads back over HTTP."""
        import inspect
        for function in (bulk.fetch_day, UsHttpMarketDataProvider.__init__):
            names = set(inspect.signature(function).parameters)
            self.assertFalse({'api_key', 'key', 'token', 'secret'} & names)

    def test_the_bearer_key_goes_in_a_header_not_the_url(self):
        transport = FixtureTransport(FIXTURES)
        provider('polygon').grouped_daily('2026-09-18')
        instance = UsHttpMarketDataProvider('polygon', transport=transport, environ=ENV)
        instance.grouped_daily('2026-09-18')
        self.assertTrue(all('test-key-not-real' not in call for call in transport.calls))


class ConfigTests(unittest.TestCase):
    def test_an_unknown_provider_is_refused_with_the_declared_ones_named(self):
        with self.assertRaises(AdapterError) as caught:
            UsHttpMarketDataProvider('not-a-vendor', transport=FixtureTransport(FIXTURES))
        self.assertIn('polygon', str(caught.exception))

    def test_every_declared_vendor_names_its_key_variable_and_its_fields(self):
        config = load_config()
        for name in config['providers']:
            _, settings = bulk.provider_settings(config, name)
            self.assertTrue(settings.get('api_key_env'), name)
            self.assertIn('close', settings['response_fields'], name)
            self.assertIn('ticker', settings['response_fields'], name)
            self.assertIn('grouped_daily', settings['endpoints'], name)

    def test_no_vendor_claims_to_report_a_share_count(self):
        """A quote service has no authority over a disclosed share count, so no
        declared vendor is allowed to map one."""
        config = load_config()
        for name, vendor in config['providers'].items():
            self.assertIsNone(vendor['response_fields'].get('shares_outstanding'), name)

    def test_the_worker_kind_is_declared_and_costs_nothing_by_the_call(self):
        import json as _json
        workers = _json.loads((ROOT / 'config' / 'workers.json').read_text(encoding='utf-8'))
        self.assertIn('market_fetch', workers['kinds'])
        self.assertIn('market_fetch', workers['locks']['by_kind'])
        schedule = next(e for e in workers['schedules']['entries']
                        if e['id'] == 'nightly_us_prices')
        # A nightly job that fails every night on a machine with no key is noise.
        self.assertFalse(schedule['enabled'])


class ScopeTests(unittest.TestCase):
    def test_an_empty_universe_file_is_a_refusal_not_an_empty_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / 'nothing.json'
            with self.assertRaises(AdapterError) as caught:
                bulk.selection(AS_OF, None, scope='universe', universe_path=missing)
            self.assertIn('universe sync', str(caught.exception))

    def test_no_packs_is_a_refusal_that_says_what_to_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AdapterError) as caught:
                bulk.selection(AS_OF, None, scope='packs', runs_dir=tmp)
            self.assertIn('ingest', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
