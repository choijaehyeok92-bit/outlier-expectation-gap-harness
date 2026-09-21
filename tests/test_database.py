"""The database layer: schema, migrations, sync and the read side.

These run against SQLite by default, so the schema and every migration are
exercised on each commit with no service running. Set
`HARNESS_TEST_DATABASE_URL` to a PostgreSQL URL to run the same suite against
the production dialect; the CHECK constraints and JSONB columns only exist
there, and this file is what proves they behave.

The property that matters most is the last one: a screen must get the same
rows from the database as from the files. If those ever diverge, the index has
stopped being an index.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2026-09-18'

try:
    from sqlalchemy import select, text
    from sqlalchemy.exc import IntegrityError

    from db import repository, sync as sync_module
    from db.models import (Base, DeepDive, FinancialFact, HarnessRun, Job, ScreenRun,
                           ScreeningMetric, Security)
    from db.session import DatabaseNotConfigured, database_url, engine_for, session_scope
    from packages.screening import rows as row_source
    from packages.screening import runs_index, warehouse
    DATABASE = True
    SKIP = ''
except Exception as error:                              # pragma: no cover
    DATABASE = False
    SKIP = f'db layer unavailable: {error}'


def migrate(url: str) -> None:
    """Apply the real migrations, not `metadata.create_all`.

    Creating tables from the models would test the models and leave the
    migrations unexercised — which is precisely the file that breaks silently.
    """
    from alembic import command
    from alembic.config import Config
    config = Config(str(ROOT / 'db' / 'alembic.ini'))
    config.set_main_option('script_location', str(ROOT / 'db' / 'migrations'))
    previous = os.environ.get('HARNESS_DATABASE_URL')
    os.environ['HARNESS_DATABASE_URL'] = url
    try:
        command.upgrade(config, 'head')
    finally:
        if previous is None:
            os.environ.pop('HARNESS_DATABASE_URL', None)
        else:
            os.environ['HARNESS_DATABASE_URL'] = previous


class DatabaseCase(unittest.TestCase):
    """A migrated, empty database per test class."""

    @classmethod
    def setUpClass(cls):
        if not DATABASE:
            raise unittest.SkipTest(SKIP)
        configured = os.environ.get('HARNESS_TEST_DATABASE_URL')
        if configured:
            cls.url = configured
            cls._tmp = None
            engine = engine_for(cls.url)
            with engine.begin() as connection:
                connection.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        else:
            cls._tmp = tempfile.TemporaryDirectory()
            cls.url = f'sqlite+pysqlite:///{Path(cls._tmp.name) / "test.sqlite3"}'
        migrate(cls.url)
        cls.engine = engine_for(cls.url)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, '_tmp', None) is not None:
            cls._tmp.cleanup()

    def setUp(self):
        with session_scope(self.engine) as session:
            for model in reversed(Base.metadata.sorted_tables):
                session.execute(model.delete())


@unittest.skipUnless(DATABASE, SKIP)
class ConfigurationTests(unittest.TestCase):
    def test_an_unset_url_is_refused_not_invented(self):
        previous = os.environ.pop('HARNESS_DATABASE_URL', None)
        try:
            with self.assertRaises(DatabaseNotConfigured):
                database_url()
            self.assertTrue(database_url(allow_default=True).startswith('sqlite'))
        finally:
            if previous is not None:
                os.environ['HARNESS_DATABASE_URL'] = previous

    def test_the_screener_does_not_use_a_database_nobody_configured(self):
        previous = os.environ.pop('HARNESS_DATABASE_URL', None)
        try:
            self.assertEqual(row_source.resolve_source('auto'), 'files')
        finally:
            if previous is not None:
                os.environ['HARNESS_DATABASE_URL'] = previous


class MigrationTests(DatabaseCase):
    def test_every_table_exists_after_upgrade(self):
        from sqlalchemy import inspect
        tables = set(inspect(self.engine).get_table_names())
        for name in Base.metadata.tables:
            self.assertIn(name, tables)

    def test_downgrade_removes_the_schema_and_upgrade_restores_it(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect
        config = Config(str(ROOT / 'db' / 'alembic.ini'))
        config.set_main_option('script_location', str(ROOT / 'db' / 'migrations'))
        previous = os.environ.get('HARNESS_DATABASE_URL')
        self.addCleanup(lambda: os.environ.__setitem__('HARNESS_DATABASE_URL', previous)
                        if previous is not None
                        else os.environ.pop('HARNESS_DATABASE_URL', None))
        os.environ['HARNESS_DATABASE_URL'] = self.url
        command.downgrade(config, 'base')
        self.assertNotIn('harness_run', set(inspect(self.engine).get_table_names()))
        command.upgrade(config, 'head')
        self.assertIn('harness_run', set(inspect(self.engine).get_table_names()))


class ConstraintTests(DatabaseCase):
    def fact(self, **overrides):
        base = {'fact_key': 'a' * 64, 'ticker': 'TEST', 'metric': 'revenue',
                'statement': 'income', 'value': 1.0, 'period_kind': 'fy',
                'fiscal_year': 2025, 'scale_multiplier': 1.0}
        base.update(overrides)
        return FinancialFact(**base)

    def test_a_full_year_may_not_carry_a_quarter(self):
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(self.fact(period_kind='fy', fiscal_quarter=3))

    def test_a_quarter_must_carry_one(self):
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(self.fact(period_kind='quarter', fiscal_quarter=None))

    def test_only_the_two_consolidation_bases_are_accepted(self):
        # Three characters, so the CHECK constraint is what rejects it rather
        # than the column width — the width would reject it on PostgreSQL and
        # let it through on SQLite, which would test nothing.
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(self.fact(consolidation_basis='XXX'))
        with session_scope(self.engine) as session:
            session.add(self.fact(fact_key='b' * 64, consolidation_basis='CFS'))

    def test_a_fact_key_cannot_be_reused(self):
        with session_scope(self.engine) as session:
            session.add(self.fact())
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(self.fact(value=999.0))

    def test_job_status_is_constrained(self):
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(Job(kind='ingest', status='probably',
                                idempotency_key='k1', payload={}))


class SyncTests(DatabaseCase):
    def run_rows(self):
        return [
            {'run_id': 'AAA', 'ticker': 'AAA', 'as_of_date': AS_OF, 'core_score': 80.0,
             'result_sha256': 'a' * 64, 'result_source': 'aggregate.json',
             'domain_scores': {'moat_trajectory': 82.0}, 'axis_scores': {},
             'hard_veto_status': 'CLEARED', 'full_harness_complete': True},
            {'run_id': 'BBB', 'ticker': 'BBB', 'as_of_date': '2026-09-19', 'core_score': 60.0,
             'result_sha256': 'b' * 64, 'result_source': 'aggregate.json',
             'domain_scores': {}, 'axis_scores': {}},
        ]

    def warehouse_payload(self):
        return {'as_of_date': AS_OF, 'companies': 1, 'rows': [{
            'ticker': 'AAA', 'currency': 'USD',
            'metrics': {'revenue_ttm': 1000.0, 'gross_margin': 0.7, 'revenue_cagr_3y': None},
            'provenance': {'revenue_ttm': {'method': 'latest_fy', 'inputs': ['FACT-0001']},
                           'gross_margin': {'method': 'ratio', 'inputs': []},
                           'revenue_cagr_3y': {'method': 'cagr:3y',
                                               'reason': 'no fiscal-year fact in FY2022'}}}]}

    def test_a_second_sync_changes_nothing(self):
        with session_scope(self.engine) as session:
            first_runs = sync_module.sync_runs(session, self.run_rows())
            first_metrics = sync_module.sync_warehouse(session, self.warehouse_payload())
        self.assertEqual(first_runs['inserted'], 2)
        self.assertEqual(first_metrics['inserted'], 3)
        with session_scope(self.engine) as session:
            again_runs = sync_module.sync_runs(session, self.run_rows())
            again_metrics = sync_module.sync_warehouse(session, self.warehouse_payload())
        self.assertEqual((again_runs['inserted'], again_runs['updated']), (0, 0))
        self.assertEqual((again_metrics['inserted'], again_metrics['updated']), (0, 0))

    def test_a_reaggregated_run_is_appended_not_overwritten(self):
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, self.run_rows())
        revised = self.run_rows()
        revised[0] = {**revised[0], 'result_sha256': 'c' * 64, 'core_score': 76.0}
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, revised)
        with session_scope(self.engine) as session:
            every = sorted((r.core_score, r.is_current) for r in
                           session.scalars(select(HarnessRun)
                                           .where(HarnessRun.run_id == 'AAA')).all())
            self.assertEqual(every, [(76.0, True), (80.0, False)])

    def test_a_recorded_refusal_is_not_the_same_as_an_absent_metric(self):
        with session_scope(self.engine) as session:
            sync_module.sync_warehouse(session, self.warehouse_payload())
        with session_scope(self.engine) as session:
            refused = session.scalar(select(ScreeningMetric).where(
                ScreeningMetric.metric == 'revenue_cagr_3y'))
            self.assertIsNotNone(refused, 'the attempt is recorded, not dropped')
            self.assertIsNone(refused.value)
            self.assertIn('FY2022', refused.unavailable_reason)
            never = session.scalar(select(ScreeningMetric).where(
                ScreeningMetric.metric == 'debt_to_ocf'))
            self.assertIsNone(never, 'a metric never attempted has no row at all')

    def test_a_metric_recomputation_updates_because_it_is_a_computation(self):
        with session_scope(self.engine) as session:
            sync_module.sync_warehouse(session, self.warehouse_payload())
        payload = self.warehouse_payload()
        payload['rows'][0]['metrics']['gross_margin'] = 0.72
        with session_scope(self.engine) as session:
            counts = sync_module.sync_warehouse(session, payload)
        self.assertEqual(counts['updated'], 1)
        with session_scope(self.engine) as session:
            row = session.scalar(select(ScreeningMetric).where(
                ScreeningMetric.metric == 'gross_margin'))
            self.assertAlmostEqual(row.value, 0.72)

    def test_facts_are_deduplicated_by_content(self):
        pack = {'ticker': 'AAA', 'reporting_currency': 'USD', 'consolidation_basis': 'CFS',
                'documents': [{'document_id': 'DOC-001', 'source_document': '10-K_2026-02-01_0001.htm',
                               'document_type': '10-K', 'filing_date': '2026-02-01'}],
                'facts': [{'fact_id': 'FACT-0001', 'metric': 'revenue', 'statement': 'income',
                           'value_reported': 100.0, 'period_kind': 'fy', 'fiscal_year': 2025,
                           'scale_multiplier': 1.0, 'source_document': '10-K_2026-02-01_0001.htm',
                           'filing_date': '2026-02-01'}]}
        with session_scope(self.engine) as session:
            self.assertEqual(sync_module.sync_pack(session, pack)['inserted'], 2)
        with session_scope(self.engine) as session:
            counts = sync_module.sync_pack(session, pack)
            self.assertEqual(counts['inserted'], 0)
        with session_scope(self.engine) as session:
            self.assertEqual(len(session.scalars(select(FinancialFact)).all()), 1)

    def test_a_long_document_name_still_produces_a_bounded_key(self):
        name = 'AVGO (Broadcom Inc.) Annual Report to Security Holders (ARS) 2026-03-02.docx'
        key = sync_module.filing_accession(name)
        self.assertLessEqual(len(key), sync_module.ACCESSION_MAX)
        self.assertEqual(key, sync_module.filing_accession(name), 'and a stable one')

    def test_screens_and_deep_dives_are_written_once(self):
        record = {'screen_run_id': 'S1', 'as_of_date': AS_OF, 'backend': 'harness_run_index',
                  'spec': {'spec_id': 'SPEC-1'}, 'summary': {'matched_count': 3},
                  'results': [], 'provenance': {'code_commit_sha': 'a' * 40}}
        report = {'metadata': {'deep_dive_id': 'D1', 'ticker': 'AAA', 'as_of_date': AS_OF,
                               'harness_run': {'run_id': 'AAA'}, 'provenance': {'stages': []}},
                  'red_team': {'overall': 'unchanged'},
                  'final_synthesis': {'agreement_with_harness': 'consistent'}}
        with session_scope(self.engine) as session:
            sync_module.sync_screen_runs(session, [record])
            sync_module.sync_deep_dives(session, [report])
        mutated = {**record, 'summary': {'matched_count': 999}}
        with session_scope(self.engine) as session:
            counts = sync_module.sync_screen_runs(session, [mutated])
            self.assertEqual(counts['skipped'], 1)
        with session_scope(self.engine) as session:
            self.assertEqual(session.get(ScreenRun, 'S1').summary['matched_count'], 3)
            self.assertEqual(session.get(DeepDive, 'D1').red_team_overall, 'unchanged')

    def test_a_job_key_cannot_queue_the_same_work_twice(self):
        with session_scope(self.engine) as session:
            first = sync_module.enqueue(session, 'ingest', {'ticker': 'AAA'})
            second = sync_module.enqueue(session, 'ingest', {'ticker': 'AAA'})
            self.assertEqual(first.job_id, second.job_id)
        with session_scope(self.engine) as session:
            self.assertEqual(len(session.scalars(select(Job)).all()), 1)

    def test_every_sync_writes_an_audit_row(self):
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, self.run_rows())
        with session_scope(self.engine) as session:
            kinds = {row['kind'] for row in repository.status(session)['recent_syncs']}
            self.assertIn('runs', kinds)


class RepositoryTests(DatabaseCase):
    def populate(self):
        with session_scope(self.engine) as session:
            sync_module.sync_universe(session, {'securities': [
                {'issuer_key': 'SEC:0000000001', 'ticker': 'AAA', 'exchange': 'Nasdaq',
                 'currency': 'USD', 'security_type': 'common', 'name': 'Alpha Inc'},
                {'issuer_key': 'SEC:0000000002', 'ticker': 'SPY', 'exchange': 'NYSE American',
                 'currency': 'USD', 'security_type': 'etf', 'name': 'An ETF',
                 'excluded_reason': 'ETF'}]})
            sync_module.sync_runs(session, [
                {'run_id': 'AAA', 'ticker': 'AAA', 'as_of_date': AS_OF, 'core_score': 80.0,
                 'result_sha256': 'a' * 64, 'result_source': 'aggregate.json',
                 'domain_scores': {'moat_trajectory': 82.0}, 'axis_scores': {}},
                {'run_id': 'LATE', 'ticker': 'LATE', 'as_of_date': '2026-12-31',
                 'core_score': 99.0, 'result_sha256': 'd' * 64,
                 'result_source': 'aggregate.json', 'domain_scores': {}, 'axis_scores': {}}])
            sync_module.sync_warehouse(session, {'as_of_date': AS_OF, 'rows': [
                {'ticker': 'AAA', 'currency': 'USD',
                 'metrics': {'revenue_ttm': 1000.0, 'gross_margin': 0.7},
                 'provenance': {}},
                {'ticker': 'ZZZ', 'currency': 'USD',
                 'metrics': {'revenue_ttm': 50.0, 'gross_margin': 0.9}, 'provenance': {}}]})

    def test_exclusions_stay_in_the_table_with_their_reason(self):
        self.populate()
        with session_scope(self.engine) as session:
            etf = session.scalar(select(Security).where(Security.ticker == 'SPY'))
            self.assertEqual(etf.excluded_reason, 'ETF')

    def test_reads_respect_the_cutoff(self):
        self.populate()
        with session_scope(self.engine) as session:
            tickers = {row['ticker'] for row in repository.harness_run_rows(session, AS_OF)}
            self.assertIn('AAA', tickers)
            self.assertNotIn('LATE', tickers)

    def test_a_company_with_metrics_and_no_run_survives_the_merge(self):
        self.populate()
        with session_scope(self.engine) as session:
            rows = {row['ticker']: row for row in repository.merged_rows(session, AS_OF)}
        self.assertTrue(rows['AAA']['has_harness_run'])
        self.assertFalse(rows['ZZZ']['has_harness_run'])
        self.assertEqual(rows['ZZZ']['revenue_ttm'], 50.0)

    def test_the_harness_value_wins_in_the_merge_here_too(self):
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, [
                {'run_id': 'AAA', 'ticker': 'AAA', 'as_of_date': AS_OF,
                 'net_cash_per_share': 12.0, 'result_sha256': 'a' * 64,
                 'result_source': 'aggregate.json', 'domain_scores': {}, 'axis_scores': {}}])
            sync_module.sync_warehouse(session, {'as_of_date': AS_OF, 'rows': [
                {'ticker': 'AAA', 'currency': 'USD',
                 'metrics': {'net_cash_per_share': 9.0}, 'provenance': {}}]})
        with session_scope(self.engine) as session:
            row = repository.merged_rows(session, AS_OF)[0]
        self.assertEqual(row['net_cash_per_share'], 12.0)
        self.assertEqual(row['field_sources']['net_cash_per_share'], 'harness_run_index')


class EquivalenceTests(DatabaseCase):
    """The index must answer what the files answer, or it is not an index."""

    def test_database_rows_match_file_rows_for_the_real_corpus(self):
        file_rows = runs_index.load_rows()
        payload = warehouse.load(AS_OF)
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, file_rows)
            if payload:
                sync_module.sync_warehouse(session, payload)
            from_db = repository.merged_rows(session, AS_OF)
        from_files = row_source.load_rows(AS_OF, warehouse_payload=payload or {}, source='files')

        self.assertEqual([row['ticker'] for row in from_db],
                         [row['ticker'] for row in from_files])
        compared = ('core_score', 'hard_veto_status', 'archetype', 'ic_state',
                    'price_to_base_value', 'has_harness_run', 'has_warehouse_metrics')
        for left, right in zip(from_db, from_files):
            for field in compared:
                self.assertEqual(left.get(field), right.get(field),
                                 f'{left["ticker"]}.{field} differs between backends')

    def test_domain_scores_survive_the_json_round_trip(self):
        file_rows = runs_index.load_rows()
        msft = next((r for r in file_rows if r['run_id'] == 'MSFT'), None)
        if msft is None:
            self.skipTest('MSFT run is not in this checkout')
        with session_scope(self.engine) as session:
            sync_module.sync_runs(session, [msft])
            stored = repository.harness_run_rows(session)[0]
        self.assertEqual(stored['domain_scores'], msft['domain_scores'])


if __name__ == '__main__':
    unittest.main()
