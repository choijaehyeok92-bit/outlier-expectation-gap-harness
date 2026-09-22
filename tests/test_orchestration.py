"""Stage 3 orchestration: sequencing, retries, idempotency and the gates.

**Scope, stated once and meant literally.** These tests use a placeholder
provider that analyses nothing. They establish that the orchestrator runs the
agents in order, retries a rejected document, skips work already done, refuses
to write anything the harness would reject, and obeys the planner. They
establish nothing about analysis quality, the soundness of a score, the
authenticity of evidence or the correctness of a Hard Veto judgement — a canned
response cannot speak to any of those, and no assertion here pretends it can.

The same boundary is recorded in `config/triage.json` and stamped onto every
batch record, so a reader of a result never has to guess which one they hold.
"""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from harness_core import runtime as h
from packages.orchestration import (agent_step, batch, contracts, fixtures, selection,
                                    store, triage)

REPO = h.ROOT
AS_OF = '2026-09-19'
TRIAGE_AGENTS = ('EV', 'AS', 'DI', 'FS')


def minimal_pack(ticker: str, as_of: str) -> dict:
    """Smallest pack that satisfies Stage 0's required rows."""
    documents = [{'document_id': 'DOC-001', 'source_document': 'annual.htm',
                  'document_type': '10-K', 'filing_date': None, 'period_end': None,
                  'is_amendment': False}]
    documents += [{'document_id': f'DOC-{index + 2:03d}', 'source_document': f'q{index}.htm',
                   'document_type': '10-Q', 'filing_date': None, 'period_end': None,
                   'is_amendment': False} for index in range(6)]
    fact = {'fact_id': 'FACT-0001', 'metric': 'revenue', 'metric_detail': None,
            'reported_label': 'Revenue', 'statement': 'income', 'gaap_status': 'gaap',
            'value_reported': 1.0, 'unit_kind': 'currency', 'currency': 'USD',
            'scale_multiplier': 1000000, 'period_kind': 'quarter', 'fiscal_year': 2026,
            'fiscal_quarter': 2, 'segment': 'consolidated', 'source_document': 'q0.htm',
            'is_amended': False, 'is_restated': False, 'requires_review': False}
    return {'schema_version': '1.0', 'ticker': ticker, 'as_of_date': as_of,
            'documents': documents, 'facts': [fact], 'adjustment_candidates': [],
            'extraction_warnings': []}


class IsolatedHarness(unittest.TestCase):
    """A throwaway repository root, so no test can touch a committed run."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('harness_core', 'config', 'templates', 'schemas', 'agents'):
            shutil.copytree(REPO / directory, self.root / directory)
        for name in ('harness.py', 'AGENTS.md'):
            shutil.copy2(REPO / name, self.root / name)
        patcher = patch.object(h, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_run(self, run_id: str, as_of: str = AS_OF, freeze: bool = True) -> Path:
        h.cmd_init(argparse.Namespace(ticker=run_id, as_of=as_of))
        run = self.root / 'runs' / run_id.upper()
        context = h.load_json(run / 'company_context.json')
        context.update(current_price=100, net_cash_per_share=5, market_cap_usd=50e9)
        h.dump_json(run / 'company_context.json', context)
        h.dump_json(run / h.FINANCIAL_PACK, minimal_pack(run_id.upper(), as_of))
        if freeze:
            h.cmd_freeze(argparse.Namespace(ticker=run_id, provider='placeholder',
                                            model='placeholder-v1', reasoning_effort=None,
                                            review_only=False))
        return run

    def reports(self, run_id: str) -> dict:
        directory = self.root / 'runs' / run_id.upper() / 'reports'
        return {path.stem: json.loads(path.read_text(encoding='utf-8'))
                for path in sorted(directory.glob('*.json'))}


class PlaceholderContractTests(unittest.TestCase):
    """The offline provider must satisfy the harness without flattering it."""

    def test_every_triage_agent_produces_an_acceptable_report(self):
        for agent_id in TRIAGE_AGENTS:
            with self.subTest(agent=agent_id):
                report = fixtures.placeholder_report(agent_id, 'TEST', AS_OF)
                self.assertEqual(contracts.validate(report), [])

    def test_a_placeholder_can_never_clear_a_hard_veto(self):
        # The whole point: a test suite must not be able to show a green run
        # that no analyst ever looked at.
        for agent_id in TRIAGE_AGENTS:
            report = fixtures.placeholder_report(agent_id, 'TEST', AS_OF)
            for flag in report['hard_veto_flags']:
                self.assertEqual(flag['status'], 'candidate')

    def test_it_says_in_the_document_that_it_is_not_analysis(self):
        report = fixtures.placeholder_report('EV', 'TEST', AS_OF)
        self.assertIn('PLACEHOLDER', report['thesis'])
        self.assertTrue(all('PLACEHOLDER' in e['claim'] for e in report['evidence']))

    def test_the_deliberately_broken_variant_is_rejected_by_the_harness(self):
        errors = contracts.validate(fixtures.placeholder_report('EV', 'TEST', AS_OF,
                                                                invalid=True))
        self.assertTrue(any('rubric weighted score' in e for e in errors))

    def test_the_agent_set_is_taken_from_the_workflow_not_restated(self):
        self.assertEqual(contracts.triage_agents(), list(TRIAGE_AGENTS))
        config = {**contracts.load_config(), 'triage_agents': ['EV', 'AS', 'DI', 'MO']}
        with self.assertRaises(ValueError):
            contracts.triage_agents(config)


class SequencingTests(IsolatedHarness):
    def test_the_four_triage_agents_run_and_the_harness_scores_them(self):
        self.make_run('SEQ')
        outcome = triage.triage_company('SEQ', fixtures.PlaceholderAgentProvider())
        self.assertEqual([step.step.agent_id for step in outcome.steps], list(TRIAGE_AGENTS))
        self.assertTrue(all(step.status == 'completed' for step in outcome.steps))
        self.assertEqual(outcome.status, 'completed')
        # The score is the harness's, computed from the reports, not written here.
        self.assertIsNotNone(outcome.harness_snapshot['score_100'])

    def test_reports_land_where_the_harness_reads_them(self):
        self.make_run('SEQ')
        triage.triage_company('SEQ', fixtures.PlaceholderAgentProvider())
        reports = self.reports('SEQ')
        for agent_id in TRIAGE_AGENTS:
            self.assertEqual(reports[agent_id]['analysis_status'], 'complete')
            self.assertEqual(contracts.validate(reports[agent_id]), [])

    def test_identity_is_stamped_from_the_manifest_not_taken_from_the_model(self):
        self.make_run('SEQ')

        class Impostor(fixtures.PlaceholderAgentProvider):
            def complete_json(self, *, stage, prompt, schema=None, context=None):
                report = super().complete_json(stage=stage, prompt=prompt, schema=schema,
                                               context=context)
                # A model answering the EV prompt while calling itself FS.
                return {**report, 'agent_id': 'FS', 'domain': 'financial_survival',
                        'ticker': 'SOMEONE_ELSE'}

        agent_step.run_agent('SEQ', 'EV', Impostor())
        report = self.reports('SEQ')['EV']
        self.assertEqual(report['agent_id'], 'EV')
        self.assertEqual(report['domain'], 'expectation_valuation')
        self.assertEqual(report['ticker'], 'SEQ')

    def test_the_planner_decides_what_happens_next(self):
        self.make_run('SEQ')
        outcome = triage.triage_company('SEQ', fixtures.PlaceholderAgentProvider())
        self.assertIn(outcome.execution_control,
                      ('continue', 'stop_early', 'stop_complete', 'blocked'))
        # A placeholder leaves every veto unevaluated, so the gate cannot clear.
        self.assertEqual(outcome.harness_snapshot['hard_veto_status'], 'UNRESOLVED')
        self.assertNotIn(outcome.harness_snapshot['mechanical_pre_ic_state'], h.BUY_STATES)

    def test_orchestration_metadata_sits_beside_the_report_not_inside_it(self):
        self.make_run('SEQ')
        agent_step.run_agent('SEQ', 'EV', fixtures.PlaceholderAgentProvider())
        self.assertNotIn('orchestration', self.reports('SEQ')['EV'])
        record = agent_step.provenance('SEQ', 'EV')
        self.assertEqual(record['provider'], 'placeholder')
        self.assertTrue(record['prompt_sha256'])


class RetryTests(IsolatedHarness):
    def test_a_transient_provider_failure_is_retried(self):
        self.make_run('RETRY')
        outcome = triage.triage_company(
            'RETRY', fixtures.PlaceholderAgentProvider(mode='flaky', fail_times=1))
        self.assertTrue(all(step.status == 'completed' for step in outcome.steps))
        self.assertTrue(all(step.attempts == 2 for step in outcome.steps))

    def test_a_rejected_document_is_retried_and_never_written(self):
        self.make_run('BROKEN')
        outcome = triage.triage_company('BROKEN',
                                        fixtures.PlaceholderAgentProvider(mode='invalid'))
        limit = contracts.load_config()['execution']['max_attempts_per_agent']
        self.assertTrue(all(step.status == 'failed' for step in outcome.steps))
        self.assertTrue(all(step.attempts == limit for step in outcome.steps))
        self.assertEqual(outcome.status, 'partial')
        for agent_id in TRIAGE_AGENTS:
            # The init skeleton is still there; the rejected document is not.
            self.assertEqual(self.reports('BROKEN')[agent_id]['analysis_status'], 'pending')

    def test_retry_feedback_is_the_validators_words_and_no_steering(self):
        self.make_run('FEEDBACK')
        seen = []

        class Recorder(fixtures.PlaceholderAgentProvider):
            def complete_json(self, *, stage, prompt, schema=None, context=None):
                seen.append(prompt)
                return super().complete_json(stage=stage, prompt=prompt, schema=schema,
                                             context=context)

        agent_step.run_agent('FEEDBACK', 'EV', Recorder(mode='flaky_invalid', fail_times=1))
        self.assertGreaterEqual(len(seen), 2)
        retry = seen[1]
        self.assertIn('rubric weighted score', retry)
        for steer in ('점수를 높', '점수를 낮', 'raise the score', 'lower the score',
                      'cleared로', 'should conclude'):
            self.assertNotIn(steer, retry)

    def test_a_total_outage_fails_the_step_rather_than_raising(self):
        self.make_run('OUTAGE')
        step = agent_step.run_agent('OUTAGE', 'EV',
                                    fixtures.PlaceholderAgentProvider(mode='error'))
        self.assertEqual(step.status, 'failed')
        self.assertTrue(any('provider' in error for error in step.errors))


class IdempotencyTests(IsolatedHarness):
    def test_a_second_run_does_no_work(self):
        self.make_run('IDEM')
        first = triage.triage_company('IDEM', fixtures.PlaceholderAgentProvider())
        self.assertTrue(all(step.status == 'completed' for step in first.steps))
        provider = fixtures.PlaceholderAgentProvider()
        second = triage.triage_company('IDEM', provider)
        self.assertTrue(all(step.status == 'skipped' for step in second.steps))
        self.assertEqual(provider.calls, [], 'a skipped step must not call the provider')

    def test_force_redoes_the_work(self):
        self.make_run('IDEM')
        triage.triage_company('IDEM', fixtures.PlaceholderAgentProvider())
        provider = fixtures.PlaceholderAgentProvider()
        again = triage.triage_company('IDEM', provider, force=True)
        self.assertTrue(all(step.status == 'completed' for step in again.steps))
        self.assertEqual(len(provider.calls), len(TRIAGE_AGENTS))

    def test_a_refreeze_invalidates_earlier_agent_work(self):
        run = self.make_run('REFREEZE')
        triage.triage_company('REFREEZE', fixtures.PlaceholderAgentProvider())
        before = agent_step.build_step('REFREEZE', 'EV').idempotency_key

        # The inputs move, and the run is frozen again on the new snapshot.
        context = h.load_json(run / 'company_context.json')
        context['current_price'] = 111
        h.dump_json(run / 'company_context.json', context)
        h.cmd_freeze(argparse.Namespace(ticker='REFREEZE', provider='placeholder',
                                        model='placeholder-v1', reasoning_effort=None,
                                        review_only=False))
        after = agent_step.build_step('REFREEZE', 'EV').idempotency_key
        self.assertNotEqual(before, after, 'a new snapshot is new work')
        self.assertIsNone(agent_step.already_done('REFREEZE', 'EV',
                                                  agent_step.build_step('REFREEZE', 'EV')))

    def test_selection_skips_a_company_whose_triage_is_already_valid(self):
        self.make_run('DONE')
        triage.triage_company('DONE', fixtures.PlaceholderAgentProvider())
        candidates = selection.select_candidates([{'run_id': 'DONE', 'ticker': 'DONE'}])
        self.assertFalse(candidates[0].eligible)
        self.assertIn('already complete', candidates[0].reason)


class GateTests(IsolatedHarness):
    def test_an_unfrozen_run_is_blocked_not_worked_on(self):
        self.make_run('UNFROZEN', freeze=False)
        outcome = triage.triage_company('UNFROZEN', fixtures.PlaceholderAgentProvider())
        self.assertEqual(outcome.status, 'blocked')
        self.assertEqual(outcome.execution_control, 'blocked')
        self.assertIn('frozen', outcome.reason)
        self.assertEqual(self.reports('UNFROZEN')['EV']['analysis_status'], 'pending')

    def test_a_missing_run_is_blocked_with_an_actionable_reason(self):
        outcome = triage.triage_company('NOSUCHRUN', fixtures.PlaceholderAgentProvider())
        self.assertEqual(outcome.status, 'blocked')
        self.assertIn('init', outcome.reason)

    def test_stage_0_gaps_block_before_any_agent_runs(self):
        h.cmd_init(argparse.Namespace(ticker='NOPACK', as_of=AS_OF))
        provider = fixtures.PlaceholderAgentProvider()
        outcome = triage.triage_company('NOPACK', provider)
        self.assertEqual(outcome.status, 'blocked')
        self.assertEqual(provider.calls, [], 'Stage 0 is not bypassed')

    def test_a_company_with_no_run_at_all_is_reported_not_dropped(self):
        candidates = selection.select_candidates([
            {'run_id': 'GHOST', 'ticker': 'GHOST', 'has_harness_run': False}])
        self.assertFalse(candidates[0].eligible)
        self.assertIn('no harness run', candidates[0].reason)


class BatchTests(IsolatedHarness):
    def candidates(self, *run_ids):
        return [selection.Candidate(run_id, run_id, rank, True)
                for rank, run_id in enumerate(run_ids, 1)]

    def test_a_batch_runs_every_eligible_candidate(self):
        for run_id in ('AAA', 'BBB'):
            self.make_run(run_id)
        result = batch.run_batch(self.candidates('AAA', 'BBB'),
                                 fixtures.PlaceholderAgentProvider(), as_of_date=AS_OF)
        self.assertEqual(result.summary['attempted'], 2)
        self.assertEqual(result.summary['completed'], 2)
        self.assertFalse(result.stopped_early)

    def test_repeated_failure_stops_the_batch(self):
        config = contracts.load_config()
        config['execution']['stop_batch_after_consecutive_failures'] = 2
        for run_id in ('AAA', 'BBB', 'CCC'):
            self.make_run(run_id)
        result = batch.run_batch(self.candidates('AAA', 'BBB', 'CCC'),
                                 fixtures.PlaceholderAgentProvider(mode='invalid'),
                                 config=config, as_of_date=AS_OF)
        self.assertTrue(result.stopped_early)
        self.assertEqual(result.summary['attempted'], 2, 'the third is not attempted')
        self.assertIn('check the provider', result.stop_reason)

    def test_a_block_does_not_trip_the_circuit_breaker(self):
        # A blocked company is an input problem; it says nothing about the
        # provider, so it must not stop work on the rest.
        config = contracts.load_config()
        config['execution']['stop_batch_after_consecutive_failures'] = 2
        self.make_run('GOOD')
        result = batch.run_batch(self.candidates('NOPE1', 'NOPE2', 'GOOD'),
                                 fixtures.PlaceholderAgentProvider(), config=config,
                                 as_of_date=AS_OF)
        self.assertFalse(result.stopped_early)
        self.assertEqual(result.summary['blocked'], 2)
        self.assertEqual(result.summary['completed'], 1)

    def test_a_rerun_of_a_finished_batch_calls_nobody(self):
        self.make_run('AAA')
        batch.run_batch(self.candidates('AAA'), fixtures.PlaceholderAgentProvider(),
                        as_of_date=AS_OF)
        provider = fixtures.PlaceholderAgentProvider()
        again = batch.run_batch(self.candidates('AAA'), provider, as_of_date=AS_OF)
        self.assertEqual(provider.calls, [])
        self.assertEqual(again.summary['steps_skipped_as_current'], len(TRIAGE_AGENTS))

    def test_ineligible_candidates_are_counted_separately(self):
        self.make_run('AAA')
        candidates = self.candidates('AAA')
        candidates.append(selection.Candidate('ZZZ', 'ZZZ', 2, False, 'no harness run'))
        result = batch.run_batch(candidates, fixtures.PlaceholderAgentProvider(),
                                 as_of_date=AS_OF)
        self.assertEqual(result.summary['attempted'], 1)
        self.assertEqual(result.summary['not_eligible'], 1)


class RecordTests(IsolatedHarness):
    def test_a_batch_record_is_written_once_and_carries_its_scope(self):
        self.make_run('AAA')
        config = contracts.load_config()
        result = batch.run_batch(self.candidates_for('AAA'),
                                 fixtures.PlaceholderAgentProvider(), as_of_date=AS_OF)
        record = store.build_record(result.to_dict(), config)
        self.assertEqual(record['verification_scope']['not_verified'],
                         config['verification_scope']['not_verified'])
        with tempfile.TemporaryDirectory() as tmp:
            path = store.save(record, base=tmp)
            original = path.read_text(encoding='utf-8')
            store.save({**record, 'summary': {'attempted': 999}}, base=tmp)
            self.assertEqual(path.read_text(encoding='utf-8'), original)
            self.assertEqual(store.load(record['triage_run_id'], base=tmp)['triage_run_id'],
                             record['triage_run_id'])

    def candidates_for(self, *run_ids):
        return [selection.Candidate(run_id, run_id, rank, True)
                for rank, run_id in enumerate(run_ids, 1)]

    def test_the_record_states_what_was_not_verified(self):
        config = contracts.load_config()
        scope = config['verification_scope']
        self.assertIn('분석 품질', scope['not_verified'])
        self.assertIn('Hard Veto 판정의 옳음', scope['not_verified'])
        self.assertIn('검증하지 않는다', scope['statement'])


if __name__ == '__main__':
    unittest.main()
