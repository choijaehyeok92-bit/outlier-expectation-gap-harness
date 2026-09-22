"""The job queue: claiming, leases, backoff, refusals and the handler contract.

The queue is a table, which is why this file exists at all: the whole
mechanism runs against SQLite in a unit test with no service, and against
PostgreSQL by setting `HARNESS_TEST_DATABASE_URL`. A queue nobody can test is
not a queue.

Four properties carry the design and each is asserted rather than described.

**A job is claimed once.** Two workers racing get one job each at most, and
the second gets nothing rather than the same row.

**A dead worker does not hold work forever.** An expired lease returns the job
to the queue — which is also why every handler must be idempotent, since
reclaiming can run one twice.

**A failure backs off and then stops.** `available_at` moves forward, and at
`max_attempts` the job becomes `failed` with its error rather than cycling.

**A payload cannot escalate.** A row naming a paid provider is refused, not
billed, and a row carrying something that looks like a credential is refused
before any handler sees it.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

try:
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    from db.models import Base, Job
    from db.session import engine_for, session_scope
    from workers import handlers, queue, runner
    AVAILABLE = True
    SKIP = ''
except Exception as error:                              # pragma: no cover
    AVAILABLE = False
    SKIP = f'worker layer unavailable: {error}'


def migrate(url: str) -> None:
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


def now() -> datetime:
    return datetime.now(timezone.utc)


class QueueCase(unittest.TestCase):
    """A migrated, empty queue per test."""

    @classmethod
    def setUpClass(cls):
        if not AVAILABLE:
            raise unittest.SkipTest(SKIP)
        configured = os.environ.get('HARNESS_TEST_DATABASE_URL')
        if configured:
            cls.url, cls._tmp = configured, None
            from sqlalchemy import text
            with engine_for(cls.url).begin() as connection:
                connection.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        else:
            cls._tmp = tempfile.TemporaryDirectory()
            cls.url = f'sqlite+pysqlite:///{Path(cls._tmp.name) / "queue.sqlite3"}'
        migrate(cls.url)
        cls.engine = engine_for(cls.url)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, '_tmp', None) is not None:
            cls._tmp.cleanup()

    def setUp(self):
        with session_scope(self.engine) as session:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
        self.config = queue.load_config()

    def enqueue(self, kind='screen_build', payload=None, **kwargs):
        with session_scope(self.engine) as session:
            job = queue.enqueue(session, kind, payload or {}, self.config, **kwargs)
            return queue.to_dict(job)

    def job(self, job_id):
        with session_scope(self.engine) as session:
            return queue.to_dict(session.get(Job, job_id))


class EnqueueTests(QueueCase):
    def test_the_same_work_queued_twice_is_one_row(self):
        first = self.enqueue(payload={'as_of_date': '2026-09-18'})
        second = self.enqueue(payload={'as_of_date': '2026-09-18'})
        self.assertEqual(first['job_id'], second['job_id'])
        with session_scope(self.engine) as session:
            self.assertEqual(len(session.scalars(select(Job)).all()), 1)

    def test_different_payloads_are_different_work(self):
        first = self.enqueue(payload={'as_of_date': '2026-09-18'})
        second = self.enqueue(payload={'as_of_date': '2026-09-19'})
        self.assertNotEqual(first['job_id'], second['job_id'])

    def test_a_kind_nobody_declared_is_refused_at_enqueue_time(self):
        # A typo should be caught by whoever queues it, not discovered by a
        # worker an hour later.
        with self.assertRaises(ValueError) as caught:
            self.enqueue(kind='screan_build')
        self.assertIn('config/workers.json declares', str(caught.exception))

    def test_the_idempotency_key_is_unique_in_the_database_too(self):
        self.enqueue(idempotency_key='k1')
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(Job(kind='db_sync', status='queued', idempotency_key='k1',
                                payload={}))


class ClaimTests(QueueCase):
    def test_a_claimed_job_is_running_and_leased(self):
        queued = self.enqueue()
        with session_scope(self.engine) as session:
            job = queue.claim(session, None, self.config, 'worker-a')
            self.assertEqual(job.job_id, queued['job_id'])
            self.assertEqual(job.status, 'running')
            self.assertEqual(job.attempts, 1)
            self.assertEqual(job.worker_id, 'worker-a')
            self.assertIsNotNone(job.lease_expires_at)

    def test_two_workers_never_get_the_same_job(self):
        self.enqueue(payload={'n': 1})
        with session_scope(self.engine) as session:
            first = queue.claim(session, None, self.config, 'worker-a')
            second = queue.claim(session, None, self.config, 'worker-b')
        self.assertIsNotNone(first)
        self.assertIsNone(second, 'the only queued job was already claimed')

    def test_an_empty_queue_returns_nothing_rather_than_waiting(self):
        with session_scope(self.engine) as session:
            self.assertIsNone(queue.claim(session, None, self.config))

    def test_a_job_scheduled_for_later_is_not_claimable_yet(self):
        self.enqueue(available_at=now() + timedelta(hours=1))
        with session_scope(self.engine) as session:
            self.assertIsNone(queue.claim(session, None, self.config))

    def test_kinds_filter_what_a_worker_picks_up(self):
        self.enqueue(kind='db_sync')
        with session_scope(self.engine) as session:
            self.assertIsNone(queue.claim(session, ['screen_build'], self.config))
            self.assertIsNotNone(queue.claim(session, ['db_sync'], self.config))

    def test_priority_then_age_decides_the_order(self):
        low = self.enqueue(payload={'n': 1}, priority=200)
        high = self.enqueue(payload={'n': 2}, priority=10)
        with session_scope(self.engine) as session:
            self.assertEqual(queue.claim(session, None, self.config).job_id, high['job_id'])
            self.assertEqual(queue.claim(session, None, self.config).job_id, low['job_id'])


class LifecycleTests(QueueCase):
    def claimed(self, **kwargs):
        row = self.enqueue(**kwargs)
        with session_scope(self.engine) as session:
            queue.claim(session, None, self.config, 'worker-a')
        return row

    def test_completing_records_the_result_and_drops_the_lease(self):
        row = self.claimed()
        with session_scope(self.engine) as session:
            queue.complete(session, session.get(Job, row['job_id']), {'companies': 3})
        final = self.job(row['job_id'])
        self.assertEqual(final['status'], 'completed')
        self.assertEqual(final['result'], {'companies': 3})
        self.assertIsNone(final['lease_expires_at'])
        self.assertIsNotNone(final['finished_at'])

    def test_a_failure_backs_off_rather_than_retrying_immediately(self):
        row = self.claimed()
        with session_scope(self.engine) as session:
            queue.fail(session, session.get(Job, row['job_id']), 'boom', self.config)
        final = self.job(row['job_id'])
        self.assertEqual(final['status'], 'queued')
        self.assertEqual(final['error'], 'boom')
        self.assertGreater(final['available_at'], now().isoformat())
        with session_scope(self.engine) as session:
            self.assertIsNone(queue.claim(session, None, self.config),
                              'the backoff has to actually hold it back')

    def test_a_job_out_of_attempts_stops_and_says_why(self):
        row = self.enqueue(max_attempts=1)
        with session_scope(self.engine) as session:
            job = queue.claim(session, None, self.config, 'worker-a')
            queue.fail(session, job, 'boom', self.config)
        final = self.job(row['job_id'])
        self.assertEqual(final['status'], 'failed')
        self.assertEqual(final['error'], 'boom')
        self.assertIsNotNone(final['finished_at'])

    def test_a_refusal_is_not_retried(self):
        row = self.claimed()
        with session_scope(self.engine) as session:
            queue.fail(session, session.get(Job, row['job_id']), 'refused', self.config,
                       retryable=False)
        self.assertEqual(self.job(row['job_id'])['status'], 'failed')

    def test_an_expired_lease_returns_the_job_to_the_queue(self):
        row = self.claimed()
        with session_scope(self.engine) as session:
            session.get(Job, row['job_id']).lease_expires_at = now() - timedelta(hours=2)
        with session_scope(self.engine) as session:
            reaped = queue.reap(session, self.config)
        self.assertEqual(len(reaped), 1)
        self.assertEqual(reaped[0]['job_id'], row['job_id'])
        final = self.job(row['job_id'])
        self.assertEqual(final['status'], 'queued')
        self.assertIn('lease expired', final['error'])
        self.assertEqual(final['attempts'], 1, 'the spent attempt still counts')

    def test_a_live_lease_is_left_alone(self):
        self.claimed()
        with session_scope(self.engine) as session:
            self.assertEqual(queue.reap(session, self.config), [])

    def test_reaping_cannot_resurrect_a_job_forever(self):
        row = self.enqueue(max_attempts=1)
        with session_scope(self.engine) as session:
            job = queue.claim(session, None, self.config, 'worker-a')
            job.lease_expires_at = now() - timedelta(hours=2)
        with session_scope(self.engine) as session:
            queue.reap(session, self.config)
        self.assertEqual(self.job(row['job_id'])['status'], 'failed')

    def test_a_heartbeat_extends_a_lease(self):
        row = self.claimed()
        with session_scope(self.engine) as session:
            job = session.get(Job, row['job_id'])
            job.lease_expires_at = now() + timedelta(seconds=1)
            queue.heartbeat(session, job, self.config)
            self.assertGreater(job.lease_expires_at, now() + timedelta(seconds=60))

    def test_cancelling_stops_an_unfinished_job_and_leaves_a_finished_one(self):
        row = self.enqueue()
        with session_scope(self.engine) as session:
            queue.cancel(session, row['job_id'])
        self.assertEqual(self.job(row['job_id'])['status'], 'cancelled')

        done = self.claimed(payload={'n': 2})
        with session_scope(self.engine) as session:
            queue.complete(session, session.get(Job, done['job_id']), {})
            queue.cancel(session, done['job_id'])
        self.assertEqual(self.job(done['job_id'])['status'], 'completed')

    def test_retrying_a_spent_job_raises_its_cap_so_it_can_actually_run(self):
        row = self.enqueue(max_attempts=1)
        with session_scope(self.engine) as session:
            queue.fail(session, queue.claim(session, None, self.config, 'w'), 'boom',
                       self.config)
        with session_scope(self.engine) as session:
            queue.retry(session, row['job_id'], self.config)
        final = self.job(row['job_id'])
        self.assertEqual(final['status'], 'queued')
        self.assertGreater(final['max_attempts'], final['attempts'])
        with session_scope(self.engine) as session:
            self.assertIsNotNone(queue.claim(session, None, self.config))


class HandlerContractTests(unittest.TestCase):
    def setUp(self):
        if not AVAILABLE:
            self.skipTest(SKIP)
        self.config = queue.load_config()

    def test_every_declared_kind_has_a_handler(self):
        self.assertEqual(handlers.declared_kinds(self.config),
                         sorted(self.config['kinds']))

    def test_a_config_pointing_at_a_missing_handler_fails_loudly(self):
        broken = {**self.config,
                  'kinds': {**self.config['kinds'], 'ghost': {'handler': 'nope'}}}
        with self.assertRaises(ValueError):
            handlers.declared_kinds(broken)

    def test_a_payload_cannot_name_a_provider_the_operator_did_not_allow(self):
        # The whole point: queueing a row must not be able to spend money.
        with self.assertRaises(handlers.HandlerRefused) as caught:
            handlers.resolve_provider({'provider': 'anthropic'}, self.config)
        self.assertIn('providers.allowed', str(caught.exception))

    def test_the_default_provider_is_the_offline_one(self):
        self.assertEqual(handlers.resolve_provider({}, self.config).name, 'placeholder')

    def test_an_operator_can_allow_a_real_provider_deliberately(self):
        opened = {**self.config,
                  'providers': {**self.config['providers'],
                                'allowed': ['placeholder', 'anthropic']}}
        provider = handlers.resolve_provider({'provider': 'anthropic'}, opened)
        self.assertEqual(provider.name, 'anthropic')

    def test_a_payload_carrying_a_credential_is_refused(self):
        for key in ('api_key', 'ANTHROPIC_API_KEY', 'secret', 'auth_token', 'password'):
            with self.subTest(key=key):
                self.assertIsNotNone(handlers.payload_is_safe({key: 'x'}))
        self.assertIsNone(handlers.payload_is_safe({'run_id': 'MSFT', 'top': 3}))

    def test_a_payload_that_is_not_serialisable_is_refused(self):
        self.assertIsNotNone(handlers.payload_is_safe({'when': object()}))

    def test_the_config_writes_down_that_handlers_must_be_idempotent(self):
        contract = self.config['handler_contract']
        self.assertTrue(contract['must_be_idempotent'])
        joined = ' '.join(contract['may_not'])
        for forbidden in ('Hard Veto', 'ic_state', 'allowed_providers', 'Stage 0'):
            self.assertIn(forbidden, joined)


class RunnerTests(QueueCase):
    def test_a_worker_drains_the_queue_and_says_what_it_did(self):
        self.enqueue(kind='monitor_status', payload={'tickers': []})
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.summary['claimed'], 1)
        self.assertEqual(report.summary['completed'], 1)
        self.assertEqual(report.stopped_by, 'queue empty')

    def test_a_handler_refusal_fails_the_job_without_retrying_it(self):
        row = self.enqueue(kind='deep_dive', payload={})       # no run_id
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.processed[0]['status'], 'failed')
        self.assertIn('run_id', report.processed[0]['error'])
        self.assertEqual(self.job(row['job_id'])['attempts'], 1,
                         'a refusal will refuse again; one attempt is enough')

    def test_a_crashing_handler_is_recorded_not_swallowed(self):
        original = handlers.REGISTRY['db_sync']

        def explode(payload, config):
            raise RuntimeError('the database went away')

        handlers.REGISTRY['db_sync'] = explode
        self.addCleanup(handlers.REGISTRY.__setitem__, 'db_sync', original)
        row = self.enqueue(kind='db_sync')
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.processed[0]['status'], 'queued', 'a crash is retryable')
        self.assertIn('the database went away', self.job(row['job_id'])['error'])

    def test_a_worker_only_takes_the_kinds_it_was_started_for(self):
        self.enqueue(kind='db_sync')
        report = runner.run(self.engine, kinds=['screen_build'], once=True,
                            install_signals=False)
        self.assertEqual(report.summary['claimed'], 0)

    def test_max_jobs_stops_the_loop(self):
        for index in range(3):
            self.enqueue(kind='monitor_status', payload={'tickers': [], 'n': index})
        report = runner.run(self.engine, once=True, max_jobs=2, install_signals=False)
        self.assertEqual(report.summary['claimed'], 2)
        self.assertEqual(report.stopped_by, 'max_jobs')

    def test_a_worker_reaps_before_it_claims(self):
        row = self.enqueue(kind='monitor_status', payload={'tickers': []})
        with session_scope(self.engine) as session:
            job = queue.claim(session, None, self.config, 'ghost')
            job.lease_expires_at = now() - timedelta(hours=2)
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(len(report.reaped), 1)
        self.assertEqual(self.job(row['job_id'])['status'], 'queued',
                         'reaped, then held back by the backoff')

    def test_running_the_same_job_twice_is_safe(self):
        # The contract every handler signs: a reclaimed lease runs it again.
        self.enqueue(kind='screen_build', payload={'as_of_date': '2026-09-18'})
        first = runner.run(self.engine, once=True, install_signals=False)
        with session_scope(self.engine) as session:
            job = session.scalars(select(Job)).one()
            job.status, job.available_at, job.lease_expires_at = 'queued', now(), None
        second = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(first.processed[0]['result']['companies'],
                         second.processed[0]['result']['companies'])

    def test_the_summary_counts_what_is_waiting(self):
        self.enqueue(kind='db_sync')
        with session_scope(self.engine) as session:
            payload = queue.summary(session)
        self.assertEqual(payload['by_status'], {'queued': 1})
        self.assertEqual(payload['claimable_now'], 1)


class RealWorkTests(QueueCase):
    """One job of each cheap kind, end to end, against the committed corpus."""

    def test_screen_build_produces_a_warehouse_through_the_queue(self):
        self.enqueue(kind='screen_build', payload={'as_of_date': '2026-09-18'})
        report = runner.run(self.engine, once=True, install_signals=False)
        result = report.processed[0]['result']
        self.assertEqual(report.processed[0]['status'], 'completed')
        self.assertGreater(result['companies'], 0)
        self.assertEqual(result['as_of_date'], '2026-09-18')

    def test_monitor_status_says_so_when_nothing_is_being_watched(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.environ.get('HARNESS_MONITORING_DIR')
            os.environ['HARNESS_MONITORING_DIR'] = tmp
            self.addCleanup(
                lambda: os.environ.__setitem__('HARNESS_MONITORING_DIR', previous)
                if previous is not None else os.environ.pop('HARNESS_MONITORING_DIR', None))
            self.enqueue(kind='monitor_status', payload={})
            report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.processed[0]['status'], 'completed')
        self.assertEqual(report.processed[0]['result']['companies'], 0)

    def test_a_triage_job_reports_the_selections_reason_rather_than_a_result(self):
        # MSFT's triage reports are already complete and valid, so the honest
        # answer is that there is nothing to run — and the reason travels with
        # it. A handler that returned an empty success here would look exactly
        # like one that had done the work.
        self.enqueue(kind='harness_triage', payload={'run_ids': ['MSFT']})
        report = runner.run(self.engine, once=True, install_signals=False)
        result = report.processed[0]['result']
        self.assertEqual(report.processed[0]['status'], 'completed')
        self.assertEqual(result['attempted'], 0)
        reasons = [row['reason'] for row in result['not_eligible']]
        self.assertTrue(all(reasons), 'every skipped candidate has to say why')
        self.assertIn('already complete', ' '.join(reasons))


if __name__ == '__main__':
    unittest.main()
