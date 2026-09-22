"""API contract: the routes exist, they read rather than compute, and they say no clearly.

The two things worth asserting at this layer are that the API cannot be talked
into doing the harness's job, and that the stages which do not exist yet answer
501 with a pointer rather than something that looks like an answer.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

try:
    from fastapi.testclient import TestClient
    from apps.api.main import app
    CLIENT = TestClient(app)
except Exception as error:                      # pragma: no cover - optional dependency
    CLIENT = None
    REASON = f'FastAPI test client unavailable: {error}'


@unittest.skipIf(CLIENT is None, 'apps/api requirements are not installed')
class ApiTests(unittest.TestCase):
    def test_health(self):
        body = CLIENT.get('/api/health').json()
        self.assertEqual(body['status'], 'ok')
        self.assertIn('harness_run_index', body['backends'])

    def test_universe_reports_both_markets(self):
        body = CLIENT.get('/api/universe').json()
        self.assertIn('US', body['by_jurisdiction'])
        self.assertIn('KR', body['by_jurisdiction'])

    def test_runs_match_the_harness_artifacts(self):
        body = CLIENT.get('/api/runs/MSFT').json()
        aggregate = json.loads((ROOT / 'runs' / 'MSFT' / 'aggregate.json').read_text(encoding='utf-8'))
        self.assertEqual(body['core_score'], aggregate['score_100'])
        self.assertEqual(body['hard_veto_status'], aggregate['hard_veto_status'])

    def test_unknown_run_is_404(self):
        self.assertEqual(CLIENT.get('/api/runs/NOT-A-RUN').status_code, 404)

    def test_parse_preserves_what_it_could_not_resolve(self):
        response = CLIENT.post('/api/screen/parse', json={
            'text': '경영진이 유머감각이 뛰어난 기업', 'as_of_date': '2026-09-18'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['filters']['clauses'], [])
        self.assertEqual(body['unresolved_conditions'][0]['reason'], 'unparsed_remainder')

    def test_a_warehouse_field_parses_into_a_real_filter_or_is_named(self):
        body = CLIENT.post('/api/screen/parse', json={
            'text': '최근 3년 매출 CAGR 15% 이상인 기업', 'as_of_date': '2026-09-18'}).json()
        clauses = body['filters']['clauses']
        if clauses:
            self.assertEqual(clauses[0]['field'], 'revenue_cagr_3y')
            self.assertAlmostEqual(clauses[0]['value'], 0.15)
        else:
            self.assertEqual(body['unresolved_conditions'][0]['reason'], 'backend_unavailable')

    def test_screen_run_executes_deterministically(self):
        payload = {'text': '한국과 미국에서 순현금이고 해자가 강하고 Base 가치 이하인 종목',
                   'as_of_date': '2026-09-18', 'persist': False}
        first = CLIENT.post('/api/screen/run', json=payload).json()
        second = CLIENT.post('/api/screen/run', json=payload).json()
        self.assertEqual([r['ticker'] for r in first['results']],
                         [r['ticker'] for r in second['results']])
        self.assertEqual(first['spec']['spec_id'], second['spec']['spec_id'])

    def test_screen_rejects_a_malformed_spec(self):
        response = CLIENT.post('/api/screen/run', json={
            'spec': {'schema_version': '1.0', 'as_of_date': '2026-09-18', 'universe': {},
                     'missing_policy': 'exclude',
                     'filters': {'op': 'and', 'clauses': [
                         {'field': 'price_to_base_value', 'operator': '<=', 'value': 15}]}},
            'persist': False})
        self.assertEqual(response.status_code, 422)

    def test_the_full_harness_stage_also_defaults_to_a_dry_run(self):
        # The full workflow is every agent in the manifest, per company. An
        # empty POST must not start it.
        response = CLIENT.post('/api/harness/full', json={'as_of_date': '2026-09-18'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['dry_run'])
        self.assertEqual(body['stage'], 'full')
        self.assertIn('IC 판정의 타당성', body['verification_scope']['not_verified'])

    def test_a_named_run_is_checked_for_readiness_before_anything_is_spent(self):
        response = CLIENT.post('/api/harness/full', json={'run_ids': ['NOSUCHRUN']})
        self.assertEqual(response.status_code, 200)
        readiness = response.json()['readiness'][0]
        self.assertFalse(readiness['ready'])
        self.assertIn('init', readiness['reason'])

    def test_an_unknown_full_run_id_is_a_404_not_an_empty_result(self):
        response = CLIENT.get('/api/harness/full/2026-01-01-000000000000')
        self.assertEqual(response.status_code, 404)

    def test_triage_defaults_to_a_dry_run_and_states_its_scope(self):
        # Neither spending money nor writing reports a person will read as
        # research should happen because somebody POSTed an empty body.
        response = CLIENT.post('/api/harness/triage', json={'as_of_date': '2026-09-18'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['dry_run'])
        self.assertIn('분석 품질', body['verification_scope']['not_verified'])

    def test_monitoring_reports_ignorance_rather_than_health(self):
        # No observations are committed for MSFT, so nothing may come back ok.
        response = CLIENT.get('/api/monitoring/MSFT')
        self.assertEqual(response.status_code, 200)
        summary = response.json()['summary']
        self.assertEqual(summary['by_status'].get('ok', 0), 0)
        self.assertGreater(summary['never_observed'], 0)

    def test_no_monitoring_route_returns_a_decision(self):
        body = CLIENT.get('/api/monitoring/MSFT').text
        for forbidden in ('"score_100"', '"hard_veto_status"', '"ic_state"',
                          '"position_range"'):
            self.assertNotIn(forbidden, body)

    def test_an_observation_without_a_traceable_source_is_refused(self):
        response = CLIENT.post('/api/monitoring/observations', json={
            'ticker': 'MSFT', 'watch_id': 'a' * 16, 'as_of_date': '2026-09-01',
            'source': '   ', 'source_type': 'filing', 'value': 1})
        self.assertEqual(response.status_code, 422)

    def test_an_observation_from_the_future_is_refused(self):
        response = CLIENT.post('/api/monitoring/observations', json={
            'ticker': 'MSFT', 'watch_id': 'a' * 16, 'as_of_date': '2099-01-01',
            'source': '10-K', 'source_type': 'filing', 'value': 1})
        self.assertEqual(response.status_code, 422)
        self.assertIn('after the cutoff', response.json()['detail'])

    def test_drift_says_when_a_change_is_the_policy_and_not_the_company(self):
        # Every NVDA run in the corpus sits on a different policy version.
        payload = CLIENT.get('/api/monitoring/NVDA/drift').json()
        self.assertGreater(payload['runs'], 1)
        self.assertEqual(payload['comparable_steps'], 0)
        self.assertTrue(all(not step['comparable'] for step in payload['steps']))

    def test_monitoring_a_company_with_no_run_is_a_404(self):
        self.assertEqual(CLIENT.get('/api/monitoring/GHOST').status_code, 404)

    def test_a_link_is_proposed_only_on_an_exact_name(self):
        payload = CLIENT.get('/api/monitoring/MSFT/links', params={'suggest': True}).json()
        unmatched = {row['name'] for row in payload['unmatched']}
        proposed = {row['name'] for row in payload['proposed']}
        self.assertIn('Microsoft Cloud gross margin', unmatched,
                      'a segment KPI must not be proposed the company-wide metric')
        self.assertNotIn('Microsoft Cloud gross margin', proposed)
        # Suggesting does not link: the stored set is still what it was.
        self.assertEqual(CLIENT.get('/api/monitoring/MSFT/links').json()['links'], {})

    def test_linking_to_a_metric_nobody_defined_is_refused(self):
        response = CLIENT.post('/api/monitoring/links', json={
            'ticker': 'MSFT', 'watch_id': 'a' * 16, 'metric_id': 'gross_margarine'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('not a warehouse metric', response.json()['detail'])

    def test_ingesting_with_nothing_linked_records_nothing(self):
        response = CLIENT.post('/api/monitoring/ingest', json={'ticker': 'MSFT'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['recorded'], 0)

    def test_the_job_queue_says_it_needs_a_database_rather_than_pretending(self):
        # No HARNESS_DATABASE_URL in the test environment, so the queue has
        # nowhere to live and the route says so instead of returning an empty
        # list that reads like an idle queue.
        import os
        if os.environ.get('HARNESS_DATABASE_URL'):
            self.skipTest('a database is configured; the 501 path is not exercised')
        response = CLIENT.get('/api/jobs')
        self.assertEqual(response.status_code, 501)
        self.assertIn('queue', response.json()['detail'])

    def test_the_lock_view_needs_a_database_too(self):
        import os
        if os.environ.get('HARNESS_DATABASE_URL'):
            self.skipTest('a database is configured; the 501 path is not exercised')
        self.assertEqual(CLIENT.get('/api/jobs/locks').status_code, 501)

    def test_deep_dive_plan_and_report_round_trip(self):
        plan = CLIENT.post('/api/deep-dive/plan', json={'run_id': 'MSFT'}).json()
        self.assertEqual(plan['ticker'], 'MSFT')
        run = CLIENT.post('/api/deep-dive/run', json={'run_id': 'MSFT', 'user_requested': True})
        self.assertEqual(run.status_code, 200)
        deep_dive_id = run.json()['deep_dive_id']
        report = CLIENT.get(f'/api/reports/{deep_dive_id}').json()
        self.assertEqual(report['harness_snapshot']['core_score'], plan['harness_snapshot']['core_score'])
        markdown = CLIENT.get(f'/api/reports/{deep_dive_id}', params={'fmt': 'markdown'})
        self.assertIn('Harness Snapshot', markdown.text)

    def test_deep_dive_on_an_unselected_run_is_refused(self):
        response = CLIENT.post('/api/deep-dive/run', json={'run_id': 'CRWD'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('not selected', response.json()['detail'])

    def test_no_route_echoes_a_provider_key(self):
        body = CLIENT.get('/api/health').text + CLIENT.get('/api/universe').text
        for marker in ('sk-', 'api_key', 'API_KEY', 'ANTHROPIC', 'OPENDART'):
            self.assertNotIn(marker, body)


if __name__ == '__main__':
    unittest.main()
