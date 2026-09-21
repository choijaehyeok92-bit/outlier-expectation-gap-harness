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
        self.assertEqual(body['backend'], 'harness_run_index')

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

    def test_parse_returns_a_spec_with_unresolved_conditions(self):
        response = CLIENT.post('/api/screen/parse', json={
            'text': '최근 3년 매출 CAGR 15% 이상인 기업', 'as_of_date': '2026-09-18'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['filters']['clauses'], [])
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

    def test_unbuilt_stages_answer_501_with_a_pointer(self):
        for path in ('/api/harness/triage', '/api/harness/full'):
            response = CLIENT.post(path)
            self.assertEqual(response.status_code, 501)
            self.assertIn('Phase', response.json()['detail'])

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
