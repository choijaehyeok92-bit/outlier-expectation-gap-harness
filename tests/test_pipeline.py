"""Where the funnel stands, and the boundary the status exists to keep visible.

Two properties matter more than the counts. Asking for the state must not
change it — a status call that quietly ran work would make the next button
press unreadable. And the free steps must stay separable from the paid ones,
because a page that chains all eight behind one click is a page that spends
money when somebody presses "next".
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2026-09-21'

from packages import pipeline  # noqa: E402


class ShapeTests(unittest.TestCase):
    def test_the_steps_are_the_funnel_in_order(self):
        self.assertEqual([step['id'] for step in pipeline.STEPS],
                         ['universe', 'intake', 'market', 'warehouse', 'screen',
                          'triage', 'full', 'deep'])

    def test_the_free_steps_come_before_the_paid_ones(self):
        """If a paid step ever sorted before a free one, 'chain the free
        prefix' would stop being a safe thing for a page to offer."""
        costs = [step['spends_money'] for step in pipeline.STEPS]
        self.assertEqual(costs, sorted(costs), 'free steps must precede paid ones')

    def test_every_paid_step_says_what_a_company_costs(self):
        for step in pipeline.STEPS:
            if step['spends_money']:
                self.assertGreater(step['calls_per_company'], 0, step['id'])
            else:
                self.assertNotIn('calls_per_company', step, step['id'])

    def test_the_harness_stages_are_the_paid_ones(self):
        """Nothing before triage calls a model: two regulators, one bulk quote
        call and local computation."""
        paid = {step['id'] for step in pipeline.STEPS if step['spends_money']}
        self.assertEqual(paid, {'triage', 'full', 'deep'})

    def test_the_full_harness_costs_the_manifest(self):
        manifest = json.loads((ROOT / 'config' / 'agents_manifest.json').read_text(encoding='utf-8'))
        agents = manifest['agents'] if isinstance(manifest, dict) else manifest
        full = next(s for s in pipeline.STEPS if s['id'] == 'full')
        self.assertEqual(full['calls_per_company'], len(agents))

    def test_triage_costs_the_declared_triage_set(self):
        triage_config = json.loads((ROOT / 'config' / 'triage.json').read_text(encoding='utf-8'))
        step = next(s for s in pipeline.STEPS if s['id'] == 'triage')
        self.assertEqual(step['calls_per_company'], len(triage_config['triage_agents']))


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.status = pipeline.status(AS_OF)

    def test_reading_the_status_does_not_change_it(self):
        """Asking where the funnel stands must not move it."""
        before = pipeline.status(AS_OF)
        after = pipeline.status(AS_OF)
        strip = lambda s: json.dumps(s, sort_keys=True, default=str)  # noqa: E731
        self.assertEqual(strip(before), strip(after))

    def test_every_step_reports_a_state(self):
        states = {step['state'] for step in self.status['steps']}
        self.assertTrue(states <= {'done', 'partial', 'todo', 'blocked'}, states)

    def test_a_finished_step_is_never_reported_as_blocked(self):
        """A missing credential stops the next run; it does not un-produce the
        artifact a previous run already wrote."""
        self.assertEqual(pipeline._state(True, 0, 'no key'), 'done')
        self.assertEqual(pipeline._state(False, 0, 'no key'), 'blocked')
        self.assertEqual(pipeline._state(False, 3, None), 'partial')
        self.assertEqual(pipeline._state(False, 0, None), 'todo')

    def test_next_step_is_the_first_unfinished_one(self):
        nxt = self.status['next_step']
        unfinished = [s['id'] for s in self.status['steps'] if s['state'] != 'done']
        self.assertEqual(nxt, unfinished[0] if unfinished else None)

    def test_the_credential_rows_never_carry_a_value(self):
        import os
        secret = 'polygon-live-DO-NOT-LEAK-0123456789'
        previous = os.environ.get('POLYGON_API_KEY')
        os.environ['POLYGON_API_KEY'] = secret
        self.addCleanup(lambda: os.environ.__setitem__('POLYGON_API_KEY', previous)
                        if previous is not None else os.environ.pop('POLYGON_API_KEY', None))
        rendered = json.dumps(pipeline.status(AS_OF), ensure_ascii=False, default=str)
        self.assertNotIn(secret, rendered)
        self.assertNotIn(secret[:16], rendered)

    def test_the_deep_dive_gate_matches_the_declared_policy(self):
        """The page prints these names; they have to be the ones the policy
        would actually select, not a second opinion about them."""
        policy = json.loads((ROOT / 'config' / 'deep_dive.json').read_text(
            encoding='utf-8'))['selection']['automatic']
        from packages.screening import runs_index
        expected = {row['ticker'] for row in runs_index.load_rows()
                    if row.get('full_harness_complete')
                    and not row.get('early_exit')
                    and row.get('hard_veto_status') in policy['require_hard_veto_status']
                    and (row.get('core_score') or 0) >= policy['min_core_score']}
        step = next(s for s in self.status['steps'] if s['id'] == 'deep')
        self.assertEqual(set(step['eligible']), expected)


class EstimateTests(unittest.TestCase):
    def test_a_paid_estimate_multiplies_agents_by_companies(self):
        self.assertEqual(pipeline.estimate('full', 12)['calls'], 15 * 12)
        self.assertEqual(pipeline.estimate('triage', 30)['calls'], 4 * 30)

    def test_a_free_step_costs_nothing(self):
        for step in ('universe', 'intake', 'market', 'warehouse', 'screen'):
            self.assertEqual(pipeline.estimate(step, 500)['calls'], 0, step)

    def test_an_unknown_step_is_not_guessed_at(self):
        self.assertEqual(pipeline.estimate('nonexistent', 10)['calls'], 0)


class ProviderTests(unittest.TestCase):
    def test_every_paid_stage_defaults_to_something_offline(self):
        """Opening the page must not be one click away from spending money."""
        for stage, meta in pipeline.providers(environ={})['stages'].items():
            default = next(o for o in meta['options'] if o['name'] == meta['default'])
            self.assertFalse(default['spends_money'], stage)
            self.assertEqual(meta['options'][0]['name'], meta['default'],
                             'the offline option comes first')

    def test_the_deep_dive_offline_stand_in_is_not_the_agent_placeholder(self):
        """`placeholder` analyses nothing and `fixture` replays a recording.
        Offering the wrong one produces a run that looks finished and is
        empty."""
        stages = pipeline.providers(environ={})['stages']
        self.assertEqual(stages['triage']['default'], 'placeholder')
        self.assertEqual(stages['full']['default'], 'placeholder')
        self.assertEqual(stages['deep']['default'], 'fixture')

    def test_the_catalogue_says_whether_a_key_exists_and_never_what_it_is(self):
        secret = 'sk-live-DO-NOT-LEAK-abcdef0123456789'
        payload = pipeline.providers(environ={'OPENAI_API_KEY': secret})
        openai = next(o for o in payload['stages']['full']['options'] if o['name'] == 'openai')
        self.assertTrue(openai['configured'])
        self.assertEqual(openai['env_var'], 'OPENAI_API_KEY')
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(secret, rendered)
        self.assertNotIn(secret[:12], rendered, 'not even a prefix of the key')

    def test_a_blank_key_is_not_configured(self):
        payload = pipeline.providers(environ={'OPENAI_API_KEY': '   '})
        openai = next(o for o in payload['stages']['full']['options'] if o['name'] == 'openai')
        self.assertFalse(openai['configured'])

    def test_each_stage_carries_its_own_per_company_cost(self):
        stages = pipeline.providers(environ={})['stages']
        self.assertEqual(stages['triage']['calls_per_company'], 4)
        self.assertEqual(stages['full']['calls_per_company'], 15)

    def test_only_paid_stages_have_a_provider_choice(self):
        stages = pipeline.providers(environ={})['stages']
        self.assertEqual(set(stages), {'triage', 'full', 'deep'})


if __name__ == '__main__':
    unittest.main()