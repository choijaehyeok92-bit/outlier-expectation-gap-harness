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

**Two jobs do not write the same run.** The queue alone cannot promise that —
it stops two workers taking the same *row*, not two rows touching the same
`runs/<ID>/` — so a claim also takes resource locks, and the lock tests are
the ones that pin the case that motivated them: a full-harness job and a deep
dive on the same company.

**A schedule that fires twice queues once.** The idempotency key names the
occurrence rather than the moment of the call, so a doubled cron, a late
wake-up and an operator running the command by hand all collapse to one row.
The cron reader is small and its one inherited trap — day-of-month and
day-of-week being OR-ed — is pinned rather than left to be rediscovered.
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

    from db.models import Base, Job, JobLock
    from db.session import engine_for, session_scope
    from workers import handlers, locks, queue, runner, schedule
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
        # Distinct as_of dates, so the two take different warehouse locks and
        # this stays a test about ordering rather than about locking.
        low = self.enqueue(payload={'as_of_date': '2026-09-17'}, priority=200)
        high = self.enqueue(payload={'as_of_date': '2026-09-18'}, priority=10)
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


class LockTests(QueueCase):
    """The case that motivated this: two jobs, one company."""

    def claim_as(self, owner, kinds=None):
        with session_scope(self.engine) as session:
            job = queue.claim(session, kinds, self.config, owner)
            return queue.to_dict(job) if job else None

    def test_a_deep_dive_waits_for_the_harness_job_on_the_same_company(self):
        # `harness_full` rewrites runs/MSFT/aggregate.json while `deep_dive`
        # reads it to copy a harness_snapshot, and dump_json is not atomic.
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        first = self.claim_as('worker-a')
        self.assertEqual(first['kind'], 'harness_full')
        self.assertIsNone(self.claim_as('worker-b'), 'MSFT is taken')

    def test_a_different_company_is_not_blocked(self):
        # The point of per-resource locks rather than one global one.
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'NVDA'})
        self.assertEqual(self.claim_as('worker-a')['kind'], 'harness_full')
        second = self.claim_as('worker-b')
        self.assertIsNotNone(second)
        self.assertEqual(second['payload']['run_id'], 'NVDA')

    def test_a_blocked_job_is_skipped_over_not_left_at_the_head(self):
        # Priority puts the blocked job first; a queue that stopped there
        # would idle while work it could do sat behind it.
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']}, priority=1)
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'}, priority=2)
        self.enqueue(kind='deep_dive', payload={'run_id': 'NVDA'}, priority=3)
        self.claim_as('worker-a')
        skipped_to = self.claim_as('worker-b')
        self.assertEqual(skipped_to['payload']['run_id'], 'NVDA')

    def test_the_lock_is_released_when_the_job_completes(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        first = self.claim_as('worker-a')
        with session_scope(self.engine) as session:
            queue.complete(session, session.get(Job, first['job_id']), {})
        self.assertIsNotNone(self.claim_as('worker-b'))

    def test_the_lock_is_released_when_the_job_fails(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        first = self.claim_as('worker-a')
        with session_scope(self.engine) as session:
            queue.fail(session, session.get(Job, first['job_id']), 'boom', self.config)
        with session_scope(self.engine) as session:
            self.assertEqual(session.scalars(select(JobLock)).all(), [])

    def test_a_dead_worker_does_not_hold_a_company_forever(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        first = self.claim_as('ghost')
        with session_scope(self.engine) as session:
            session.get(Job, first['job_id']).lease_expires_at = now() - timedelta(hours=2)
        with session_scope(self.engine) as session:
            queue.reap(session, self.config)
        self.assertIsNotNone(self.claim_as('worker-b'),
                             'the reaped job released MSFT on its way out')

    def test_a_wildcard_and_a_named_resource_block_each_other(self):
        # `db_sync` reads every run's aggregate, so it takes the namespace.
        self.enqueue(kind='db_sync', payload={})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        self.assertEqual(self.claim_as('worker-a')['kind'], 'db_sync')
        self.assertIsNone(self.claim_as('worker-b'))

    def test_a_named_resource_blocks_a_later_wildcard(self):
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        self.assertEqual(self.claim_as('worker-a')['kind'], 'deep_dive')
        self.enqueue(kind='db_sync', payload={})
        self.assertIsNone(self.claim_as('worker-b'))

    def test_a_namespace_nobody_shares_does_not_block(self):
        # screen_build reads Stage 0 packs, which no job rewrites, so it has
        # its own namespace rather than joining the run traffic jam.
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='screen_build', payload={'as_of_date': '2026-09-18'})
        self.assertIsNotNone(self.claim_as('worker-a'))
        self.assertIsNotNone(self.claim_as('worker-b'))

    def test_a_batch_without_named_runs_takes_the_whole_namespace(self):
        # Its targets are not known until it runs its own selection, and
        # claiming too little corrupts a run while claiming too much only
        # delays one.
        self.assertEqual(locks.keys_for('harness_full', {'top': 5}, self.config),
                         [('run', '*')])
        self.assertEqual(locks.keys_for('harness_full', {'run_ids': ['msft']}, self.config),
                         [('run', 'MSFT')])

    def test_the_database_is_what_refuses_a_second_holder(self):
        # Not this package's check: the unique constraint.
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        claimed = self.claim_as('worker-a')
        with self.assertRaises(IntegrityError):
            with session_scope(self.engine) as session:
                session.add(JobLock(namespace='run', resource='MSFT',
                                    job_id=claimed['job_id']))

    def test_blocked_names_what_is_waiting_and_on_whom(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        waiting = self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        holder = self.claim_as('worker-a')
        with session_scope(self.engine) as session:
            rows = queue.blocked(session, None, self.config)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['job_id'], waiting['job_id'])
        self.assertEqual(rows[0]['needs'], ['run:MSFT'])
        self.assertEqual(rows[0]['blocked_by'][0]['job_id'], holder['job_id'])

    def test_the_summary_separates_unstarted_work_from_work_that_is_waiting(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        self.enqueue(kind='deep_dive', payload={'run_id': 'NVDA'})
        self.claim_as('worker-a')
        with session_scope(self.engine) as session:
            payload = queue.summary(session)
        self.assertEqual(payload['ready_but_locked'], 1)
        self.assertEqual(payload['claimable_now'], 1)
        self.assertEqual(len(payload['held_locks']), 1)

    def test_an_orphaned_lock_is_released(self):
        # A resource held by a job that is not running has no holder.
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        claimed = self.claim_as('worker-a')
        with session_scope(self.engine) as session:
            job = session.get(Job, claimed['job_id'])
            job.status = 'completed'                # finished without releasing
        with session_scope(self.engine) as session:
            released = locks.release_orphans(session)
        self.assertEqual(len(released), 1)
        self.assertEqual(released[0]['resource'], 'MSFT')

    def test_locking_can_be_turned_off_and_then_nothing_blocks(self):
        off = {**self.config, 'locks': {**self.config['locks'], 'enabled': False}}
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        with session_scope(self.engine) as session:
            self.assertIsNotNone(queue.claim(session, None, off, 'worker-a'))
            self.assertIsNotNone(queue.claim(session, None, off, 'worker-b'))

    def test_every_kind_declares_where_its_writes_land(self):
        # A kind with no rule takes no lock, which is silently unsafe. The
        # config has to cover all of them.
        for kind in self.config['kinds']:
            with self.subTest(kind=kind):
                self.assertIn(kind, self.config['locks']['by_kind'])
                self.assertTrue(locks.keys_for(kind, {}, self.config))
                self.assertTrue(self.config['locks']['by_kind'][kind].get('why'),
                                'a lock rule has to say what it is protecting')


class LockedRunnerTests(QueueCase):
    def test_a_worker_runs_the_job_it_can_and_leaves_the_blocked_one(self):
        # A second worker cannot be started inside one test, so MSFT is held
        # by a claim that is never completed.
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']}, priority=1)
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'}, priority=2)
        self.enqueue(kind='monitor_status', payload={'tickers': ['NVDA']}, priority=3)
        with session_scope(self.engine) as session:
            queue.claim(session, ['harness_full'], self.config, 'other-worker')
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual([row['kind'] for row in report.processed], ['monitor_status'],
                         'the blocked deep dive is passed over, not run and not failed')

    def test_a_worker_with_nothing_unblocked_reports_empty_rather_than_spinning(self):
        self.enqueue(kind='harness_full', payload={'run_ids': ['MSFT']})
        self.enqueue(kind='deep_dive', payload={'run_id': 'MSFT'})
        with session_scope(self.engine) as session:
            queue.claim(session, ['harness_full'], self.config, 'other-worker')
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.summary['claimed'], 0)
        self.assertEqual(report.stopped_by, 'queue empty')

    def test_a_completed_job_frees_the_company_for_the_next_one(self):
        self.enqueue(kind='monitor_status', payload={'tickers': ['MSFT']}, priority=1)
        self.enqueue(kind='monitor_status', payload={'tickers': ['MSFT'], 'n': 2}, priority=2)
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.summary['claimed'], 2,
                         'the second ran once the first released MSFT')
        with session_scope(self.engine) as session:
            self.assertEqual(session.scalars(select(JobLock)).all(), [])


class CronTests(unittest.TestCase):
    """The reader, before anything is scheduled with it."""

    def setUp(self):
        if not AVAILABLE:
            self.skipTest(SKIP)

    def fires(self, expression, moment):
        return schedule.matches(schedule.parse(expression), moment)

    def test_the_documented_subset_is_understood(self):
        cases = {
            '0 3 * * *': datetime(2026, 9, 22, 3, 0, tzinfo=timezone.utc),
            '*/15 * * * *': datetime(2026, 9, 22, 7, 45, tzinfo=timezone.utc),
            '0 2-4 * * *': datetime(2026, 9, 22, 3, 0, tzinfo=timezone.utc),
            '0 0 1,15 * *': datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc),
            '30 1 * * 2': datetime(2026, 9, 22, 1, 30, tzinfo=timezone.utc),   # a Tuesday
            '@daily': datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc),
            '@hourly': datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc),
            '@weekly': datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc),       # a Sunday
        }
        for expression, moment in cases.items():
            with self.subTest(cron=expression):
                self.assertTrue(self.fires(expression, moment))

    def test_a_minute_that_does_not_match_does_not_fire(self):
        self.assertFalse(self.fires('0 3 * * *',
                                    datetime(2026, 9, 22, 3, 1, tzinfo=timezone.utc)))
        self.assertFalse(self.fires('*/15 * * * *',
                                    datetime(2026, 9, 22, 7, 46, tzinfo=timezone.utc)))

    def test_seven_is_sunday_as_cron_has_always_had_it(self):
        sunday = datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(self.fires('0 0 * * 7', sunday))
        self.assertTrue(self.fires('0 0 * * 0', sunday))

    def test_day_of_month_and_day_of_week_are_or_ed_as_cron_does(self):
        # The famous trap, kept deliberate: `0 0 1 * 1` runs on the 1st AND on
        # every Monday, not only on a Monday the 1st.
        parsed = schedule.parse('0 0 1 * 1')
        first = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)        # Tuesday the 1st
        monday = datetime(2026, 9, 21, 0, 0, tzinfo=timezone.utc)      # Monday the 21st
        other = datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(schedule.matches(parsed, first))
        self.assertTrue(schedule.matches(parsed, monday))
        self.assertFalse(schedule.matches(parsed, other))

    def test_only_one_restricted_day_field_still_ands(self):
        parsed = schedule.parse('0 0 15 * *')
        self.assertTrue(schedule.matches(
            parsed, datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)))
        self.assertFalse(schedule.matches(
            parsed, datetime(2026, 9, 16, 0, 0, tzinfo=timezone.utc)))

    def test_syntax_outside_the_subset_is_refused_not_guessed(self):
        # A misread `L` that quietly means "every day" is worse than a
        # rejected config.
        for expression in ('0 0 L * *', '0 0 * * 1#2', '0 0 ? * *', '0 0 * *',
                           '0 0 * * * *', '99 * * * *', '0 0 32 * *', '0 5-2 * * *'):
            with self.subTest(cron=expression):
                with self.assertRaises(schedule.CronError):
                    schedule.parse(expression)

    def test_the_error_says_what_is_supported(self):
        with self.assertRaises(schedule.CronError) as caught:
            schedule.parse('0 0 L * *')
        self.assertIn('*/n', str(caught.exception))

    def test_the_last_occurrence_is_found_and_the_window_is_honoured(self):
        now = datetime(2026, 9, 22, 4, 45, tzinfo=timezone.utc)
        self.assertEqual(schedule.last_occurrence('0 3 * * *', now),
                         datetime(2026, 9, 22, 3, 0, tzinfo=timezone.utc))
        # Monthly, on the 1st: outside a 48h lookback on the 22nd.
        self.assertIsNone(schedule.last_occurrence('0 0 1 * *', now, lookback_hours=48))
        self.assertIsNotNone(schedule.last_occurrence('0 0 1 * *', now, lookback_hours=24 * 40))

    def test_occurrences_since_lists_every_firing_in_order(self):
        since = datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 22, 3, 30, tzinfo=timezone.utc)
        found = schedule.occurrences_since('0 * * * *', since, now)
        self.assertEqual([m.hour for m in found], [1, 2, 3])

    def test_a_naive_time_is_read_as_utc(self):
        naive = datetime(2026, 9, 22, 3, 0)
        self.assertTrue(schedule.matches(schedule.parse('0 3 * * *'), naive))
        self.assertEqual(schedule.stamp(naive), '2026-09-22T03:00Z')


class SchedulePlanTests(unittest.TestCase):
    def setUp(self):
        if not AVAILABLE:
            self.skipTest(SKIP)
        self.config = queue.load_config()

    def test_the_shipped_schedules_are_readable_and_point_at_real_kinds(self):
        self.assertEqual(schedule.validate(self.config), [])

    def test_no_money_spending_kind_is_scheduled_by_default(self):
        # Queueing a nightly harness_full because a config shipped that way is
        # exactly the surprise the provider allowlist exists to prevent.
        spends = {kind for kind, row in self.config['kinds'].items()
                  if row.get('spends_money')}
        scheduled = {entry['kind'] for entry in schedule.entries(self.config)}
        self.assertEqual(spends & scheduled, set())
        self.assertTrue(set(self.config['schedules']['never_scheduled']) <= spends)

    def test_validate_catches_a_duplicate_id(self):
        entry = dict(self.config['schedules']['entries'][0])
        broken = {**self.config, 'schedules': {**self.config['schedules'],
                                               'entries': [entry, dict(entry)]}}
        problems = schedule.validate(broken)
        self.assertTrue(any('duplicate schedule id' in p for p in problems))

    def test_validate_catches_a_kind_nobody_declared(self):
        broken = {**self.config, 'schedules': {**self.config['schedules'], 'entries': [
            {'id': 'x', 'kind': 'screan_build', 'cron': '@daily'}]}}
        self.assertTrue(any('not declared' in p for p in schedule.validate(broken)))

    def test_validate_catches_a_payload_carrying_a_credential(self):
        broken = {**self.config, 'schedules': {**self.config['schedules'], 'entries': [
            {'id': 'x', 'kind': 'db_sync', 'cron': '@daily',
             'payload': {'api_key': 'sk-x'}}]}}
        self.assertTrue(any('payload carries' in p for p in schedule.validate(broken)))

    def test_only_two_placeholders_are_substituted(self):
        moment = datetime(2026, 9, 22, 3, 0, tzinfo=timezone.utc)
        rendered = schedule.render_payload(
            {'as_of_date': '{date}', 'tag': 'run-{occurrence}',
             'nested': {'when': '{date}'}, 'list': ['{date}'],
             'left_alone': '{today}', 'number': 5}, moment)
        self.assertEqual(rendered['as_of_date'], '2026-09-22')
        self.assertEqual(rendered['tag'], 'run-2026-09-22T03:00Z')
        self.assertEqual(rendered['nested']['when'], '2026-09-22')
        self.assertEqual(rendered['list'], ['2026-09-22'])
        self.assertEqual(rendered['left_alone'], '{today}',
                         'an unknown placeholder is left alone, not evaluated')
        self.assertEqual(rendered['number'], 5)

    def test_the_key_names_the_occurrence_not_the_moment_of_the_call(self):
        moment = datetime(2026, 9, 22, 3, 0, tzinfo=timezone.utc)
        self.assertEqual(schedule.idempotency_key('nightly_db_sync', moment, self.config),
                         'schedule:nightly_db_sync:2026-09-22T03:00Z')

    def test_a_missed_window_is_reported_rather_than_back_filled(self):
        config = {**self.config, 'schedules': {
            **self.config['schedules'], 'lookback_hours': 2,
            'entries': [{'id': 'monthly', 'kind': 'db_sync', 'cron': '0 0 1 * *'}]}}
        row = schedule.plan(config, datetime(2026, 9, 22, 4, 0, tzinfo=timezone.utc))[0]
        self.assertFalse(row['due'])
        self.assertIn('not', row['reason'])

    def test_a_disabled_entry_is_not_planned(self):
        config = {**self.config, 'schedules': {**self.config['schedules'], 'entries': [
            {'id': 'off', 'kind': 'db_sync', 'cron': '@daily', 'enabled': False}]}}
        self.assertEqual(schedule.plan(config), [])


class ScheduleRunTests(QueueCase):
    NOW = datetime(2026, 9, 22, 4, 45, tzinfo=timezone.utc)

    def fire(self, now=None, only=None, config=None):
        with session_scope(self.engine) as session:
            return schedule.run(session, config or self.config, now or self.NOW, only)

    def test_the_due_schedules_are_queued(self):
        result = self.fire()
        self.assertEqual(result['summary']['queued'], len(schedule.entries(self.config)))
        with session_scope(self.engine) as session:
            self.assertEqual(len(session.scalars(select(Job)).all()),
                             result['summary']['queued'])

    def test_firing_twice_for_the_same_occurrence_queues_nothing_extra(self):
        # A doubled cron, a retried command, an operator being thorough.
        first = self.fire()
        second = self.fire()
        self.assertEqual(second['summary']['queued'], 0)
        self.assertEqual(second['summary']['already_queued'], first['summary']['queued'])
        with session_scope(self.engine) as session:
            self.assertEqual(len(session.scalars(select(Job)).all()),
                             first['summary']['queued'])

    def test_a_later_call_in_the_same_window_is_still_the_same_occurrence(self):
        self.fire(self.NOW)
        later = self.fire(self.NOW + timedelta(minutes=40))
        self.assertEqual(later['summary']['queued'], 0)

    def test_the_next_day_is_new_work(self):
        self.fire(self.NOW)
        tomorrow = self.fire(self.NOW + timedelta(days=1))
        self.assertEqual(tomorrow['summary']['queued'], len(schedule.entries(self.config)))

    def test_the_queue_is_the_only_state_the_scheduler_keeps(self):
        # Nothing on disk, no extra table: deleting the jobs makes it due again.
        self.fire()
        with session_scope(self.engine) as session:
            for job in session.scalars(select(Job)).all():
                session.delete(job)
        self.assertEqual(self.fire()['summary']['queued'],
                         len(schedule.entries(self.config)))

    def test_only_narrows_what_is_queued(self):
        result = self.fire(only=['nightly_db_sync'])
        self.assertEqual(result['summary']['queued'], 1)
        self.assertEqual(result['queued'][0]['schedule_id'], 'nightly_db_sync')

    def test_a_broken_schedule_stops_the_run_rather_than_queuing_half_of_it(self):
        broken = {**self.config, 'schedules': {**self.config['schedules'], 'entries': [
            {'id': 'good', 'kind': 'db_sync', 'cron': '@daily'},
            {'id': 'bad', 'kind': 'db_sync', 'cron': '0 0 L * *'}]}}
        with self.assertRaises(schedule.CronError):
            self.fire(config=broken)
        with session_scope(self.engine) as session:
            self.assertEqual(session.scalars(select(Job)).all(), [])

    def test_the_payload_reaches_the_job_with_its_date_filled_in(self):
        self.fire(only=['nightly_warehouse'])
        with session_scope(self.engine) as session:
            job = session.scalars(select(Job)).one()
            self.assertEqual(job.payload, {'as_of_date': '2026-09-22'})
            self.assertEqual(job.priority, 40)

    def test_a_scheduled_job_is_an_ordinary_job_a_worker_then_runs(self):
        self.fire(only=['nightly_monitor_status'])
        report = runner.run(self.engine, once=True, install_signals=False)
        self.assertEqual(report.summary['completed'], 1)
        self.assertEqual(report.processed[0]['kind'], 'monitor_status')


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
