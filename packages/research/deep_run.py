"""Run the deep dive: research, qualitative, red team, synthesis.

The orchestration is deliberately boring. For each stage: build a prompt, ask
the provider, validate the answer against that stage's schema, keep it. Then
assemble the four answers into one report, copy the harness snapshot in
verbatim, validate the whole document, and run the invariants that a schema
cannot express. Anything that fails stops the run — a deep dive that half
validated is not a deep dive.

Provider and model are recorded per stage, so a reader can see which model
produced the qualitative judgement and which one attacked it.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from packages.llm import LLMError
from . import deep_plan, invariants, prompts, stages, store

ROOT = Path(__file__).resolve().parents[2]


def _prompt_sha256(text):
    import hashlib
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def run_stages(plan, provider, excerpts=None, master_schema=None):
    """Execute the four stages in order. Returns (outputs, stage_metadata)."""
    master = master_schema or stages.report_schema()
    outputs, metadata = {}, []
    evidence = None
    for stage in stages.STAGES:
        schema = stages.stage_schema(stage, master)
        prompt = prompts.build(stage, plan, schema, evidence=evidence,
                               qualitative=outputs.get('qualitative'),
                               red_team=(outputs.get('red_team') or {}).get('red_team'),
                               excerpts=excerpts)
        answer = provider.complete_json(stage=stage, prompt=prompt, schema=schema, context={'plan': plan})
        outputs[stage] = answer
        metadata.append({'stage': stage, 'provider': provider.name, 'model': provider.model,
                         'prompt_sha256': _prompt_sha256(prompt),
                         'completed_at_utc': datetime.now(timezone.utc).isoformat()})
        if stage == 'deep_research':
            evidence = answer['evidence']
    return outputs, metadata


def assemble(plan, outputs, stage_metadata, code_commit_sha):
    report = {'schema_version': '1.0'}
    report.update(outputs['deep_research'])
    report.update(outputs['qualitative'])
    report.update(outputs['red_team'])
    report.update(outputs['synthesis'])
    # Copied, not recomputed: the deep dive reads the harness result and never writes one.
    report['harness_snapshot'] = plan['harness_snapshot']

    body = {k: v for k, v in report.items()}
    digest = store.content_hash(body)
    report['metadata'] = {
        'deep_dive_id': store.deep_dive_id(plan['ticker'], plan['as_of_date'], digest),
        'ticker': plan['ticker'], 'company_name': plan.get('company_name'),
        'jurisdiction': plan['jurisdiction'], 'as_of_date': plan['as_of_date'],
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'harness_run': plan['harness_run'],
        'provenance': {'code_commit_sha': code_commit_sha, 'market_snapshot_sha256': None,
                       'stages': stage_metadata},
    }
    return report


def validate(report, plan, config=None, master_schema=None):
    import jsonschema
    master = master_schema or stages.report_schema()
    jsonschema.validate(report, master)
    errors = invariants.check(report, config or deep_plan.load_config(),
                              expected_snapshot=plan['harness_snapshot'],
                              domain_keys=stages.DOMAIN_KEYS)
    if errors:
        raise LLMError('deep dive failed its invariants:\n  - ' + '\n  - '.join(errors))
    return report


def run(run_id, provider, runs_dir=None, config=None, user_requested=False, excerpts=None,
        base=None, persist=True):
    """Plan, run the stages, validate, and (by default) persist immutably."""
    config = config or deep_plan.load_config()
    plan = deep_plan.build(run_id, runs_dir=runs_dir, config=config, user_requested=user_requested)
    if not plan['selection']['eligible']:
        raise LLMError(
            f"{run_id}: not selected for a deep dive ({plan['selection']['route']}) — "
            + '; '.join(plan['selection']['reasons'])
            + '. Re-run with an explicit request to override the automatic policy.')
    from packages.screening.store import code_commit_sha
    master = stages.report_schema()
    outputs, metadata = run_stages(plan, provider, excerpts=excerpts, master_schema=master)
    report = assemble(plan, outputs, metadata, code_commit_sha())
    validate(report, plan, config, master)
    path = store.save(report, plan, base) if persist else None
    return report, plan, path
