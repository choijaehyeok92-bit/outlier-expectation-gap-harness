"""Build a DeepDivePlan from a completed harness run.

The plan is deterministic. It reads the run, applies the config-driven
selection policy, lists the qualitative domains to cover, inventories the
frozen local evidence that must be read before any search, and carries over the
harness's own research questions where the run has them. It states no answer
and no judgement.

Selection never names a ticker. A run reaches `automatic` by satisfying the
policy in `config/deep_dive.json`; anything else is `optional` (a person asked
for it) or `early_exit` (the planner had already stopped), and the route is
recorded in the report so a reader knows why the deep dive exists.
"""
import hashlib
import json
from pathlib import Path

from packages.screening import runs_index

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'config' / 'deep_dive.json'
SCHEMA_PATH = ROOT / 'schemas' / 'deep_dive_plan.schema.json'
LOCAL_EVIDENCE = ('company_context.json', 'run_manifest.json', 'sources/README.md',
                  'sources/financials/normalized_financials.json', 'digest.md', 'aggregate.json',
                  'final_verdict.json')

SNAPSHOT_FIELDS = ('ticker', 'as_of_date', 'core_score', 'ex_valuation_score', 'classification',
                   'archetype', 'hard_veto_status', 'ic_state', 'position_range',
                   'price_to_base_value', 'domain_scores', 'axis_scores', 'dilution_watch_status')


def load_config(path=None):
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


def load_schema(path=None):
    return json.loads(Path(path or SCHEMA_PATH).read_text(encoding='utf-8'))


def harness_snapshot(row):
    """The harness result, copied. Nothing here is recomputed or reinterpreted."""
    return {field: row.get(field) for field in SNAPSHOT_FIELDS}


def snapshot_sha256(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def select(row, config, user_requested=False):
    """Route and reasons. A user request can add a route; it can never claim the automatic one."""
    policy = config['selection']
    automatic = policy['automatic']
    reasons = []

    if automatic.get('require_full_harness_complete') and not row.get('full_harness_complete'):
        reasons.append('full harness coverage is incomplete')
    veto_required = automatic.get('require_hard_veto_status') or []
    if veto_required and row.get('hard_veto_status') not in veto_required:
        reasons.append(f"hard veto status is {row.get('hard_veto_status')}, not one of {veto_required}")
    minimum = automatic.get('min_core_score')
    score = row.get('core_score')
    if minimum is not None:
        if score is None:
            reasons.append('core score is missing')
        elif score < minimum:
            reasons.append(f'core score {score} is below the deep-dive threshold {minimum}')
    if automatic.get('exclude_early_exit') and row.get('early_exit'):
        reasons.append('the planner recorded an early exit for this run')

    if not reasons:
        return {'eligible': True, 'route': 'automatic',
                'reasons': ['meets the configured automatic deep-dive policy']}
    if row.get('early_exit'):
        route = 'early_exit'
    elif user_requested:
        route = 'optional'
    else:
        route = 'blocked'
    # An explicit request is the only thing that makes a non-automatic run eligible.
    return {'eligible': bool(user_requested), 'route': route, 'reasons': reasons}


def local_evidence(run_dir):
    rows = []
    for name in LOCAL_EVIDENCE:
        path = Path(run_dir) / name
        rows.append({'path': name, 'exists': path.is_file(),
                     'sha256': hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                     if path.is_file() else None})
    return rows


def harness_questions(run_dir):
    """Open research questions the harness itself raised, when the run can produce them."""
    run_dir = Path(run_dir)
    try:
        from harness_core import runtime as harness
        from harness_core import research as harness_research
    except Exception:
        return []
    if not (run_dir / 'reports').exists() or not (run_dir / 'run_manifest.json').exists():
        return []
    try:
        reports = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((run_dir / 'reports').glob('*.json'))]
        aggregate_path = run_dir / 'aggregate.json'
        aggregate = json.loads(aggregate_path.read_text(encoding='utf-8')) if aggregate_path.exists() else {}
        plan = harness_research.build_plan(run_dir, reports, {'stage': 'deep_dive'}, aggregate,
                                           harness.CALIBRATION, harness.EXEC.get('research_policy', {}))
    except Exception:
        # A historical run written under an older policy may not replay cleanly.
        # That is not a reason to block the deep dive; it just contributes no
        # carried-over questions, and the deep-dive domains still stand.
        return []
    return [{'question_id': q['research_question_id'], 'question': q['question'],
             'domain': q.get('domain'), 'origin': 'harness_research_plan',
             'research_class': q.get('research_class'),
             'required_for_decision': bool(q.get('required_for_decision'))}
            for q in plan.get('questions', [])]


def build(run_id, runs_dir=None, config=None, user_requested=False):
    config = config or load_config()
    row = runs_index.load_row(run_id, runs_dir)
    if row is None:
        raise ValueError(f'{run_id}: no readable harness run')
    run_dir = Path(runs_dir or runs_index.RUNS_DIR) / run_id
    snapshot = harness_snapshot(row)

    questions = [{'question_id': item['id'], 'question': item['question'], 'domain': None,
                  'origin': 'investment_question', 'research_class': 'decision_blocking',
                  'required_for_decision': True}
                 for item in config['investment_questions']]
    questions += [{'question_id': f"DD-{domain['id'].upper()}", 'question': domain['prompt_focus'],
                   'domain': domain['id'], 'origin': 'deep_dive_domain',
                   'research_class': 'thesis_monitor', 'required_for_decision': False}
                  for domain in config['domains']]
    questions += harness_questions(run_dir)

    plan = {
        'schema_version': '1.0',
        'ticker': row['ticker'],
        'company_name': row.get('company_name'),
        'jurisdiction': row['jurisdiction'] if row['jurisdiction'] in ('US', 'KR') else 'US',
        'as_of_date': row['as_of_date'],
        'harness_run': {'run_id': run_id, 'aggregate_sha256': row.get('result_sha256') or '',
                        'input_snapshot_sha256': row.get('input_snapshot_sha256'),
                        'strategy_version': row.get('strategy_version'),
                        'decision_policy_version': row.get('decision_policy_version')},
        'selection': select(row, config, user_requested),
        'harness_snapshot': snapshot,
        'domains': [{'id': d['id'], 'title': d['title'], 'prompt_focus': d['prompt_focus'],
                     'harness_reference': {'domain': d.get('harness_domain'),
                                           'score': (row.get('domain_scores') or {}).get(d.get('harness_domain'))
                                           if d.get('harness_domain') in (row.get('domain_scores') or {})
                                           else (row.get('axis_scores') or {}).get(d.get('harness_domain'))}}
                    for d in config['domains']],
        'local_evidence': local_evidence(run_dir),
        'questions': questions,
        'red_team_mandate': config['red_team_mandate'],
    }
    import jsonschema
    jsonschema.validate(plan, load_schema())
    return plan
