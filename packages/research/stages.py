"""Stage contracts for the deep dive.

Each stage gets its own JSON Schema, derived from `deep_dive_report.schema.json`
so the stage contract and the final document can never drift apart. A provider
answers one stage at a time and its answer is validated before the next stage
starts; nothing partially-valid reaches the report.

The stage split is the independence protocol in code. Research collects
evidence. The qualitative analyst forms a judgement from that evidence and is
given the harness result only for the comparison it must make afterwards. The
Red Team is a separate call with its own mandate to break the thesis. Synthesis
is the only stage that sees all of them, and it still cannot change a harness
number.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_SCHEMA_PATH = ROOT / 'schemas' / 'deep_dive_report.schema.json'

DOMAIN_KEYS = ('business_model', 'industry', 'customer_product', 'moat', 'moat_trajectory',
               'growth_runway', 'unit_economics', 'per_share_economics', 'financial_quality',
               'management', 'capital_allocation', 'technology_disruption', 'risk_analysis',
               'valuation_interpretation')
SYNTHESIS_KEYS = ('executive_summary', 'harness_comparison', 'falsifiers', 'monitoring_kpis',
                  'remaining_unknowns', 'evidence_quality', 'final_synthesis')
STAGES = ('deep_research', 'qualitative', 'red_team', 'synthesis')


def report_schema(path=None):
    return json.loads(Path(path or REPORT_SCHEMA_PATH).read_text(encoding='utf-8'))


def _subschema(master, keys):
    schema = {'$schema': master['$schema'], 'type': 'object', 'additionalProperties': False,
              'required': list(keys),
              'properties': {k: copy.deepcopy(master['properties'][k]) for k in keys},
              'definitions': copy.deepcopy(master['definitions'])}
    return schema


def stage_schema(stage, master=None):
    master = master or report_schema()
    if stage == 'deep_research':
        return _subschema(master, ('evidence',))
    if stage == 'qualitative':
        return _subschema(master, DOMAIN_KEYS + ('investment_question', 'bull_case', 'base_case', 'bear_case'))
    if stage == 'red_team':
        return _subschema(master, ('red_team',))
    if stage == 'synthesis':
        return _subschema(master, SYNTHESIS_KEYS)
    raise ValueError(f'unknown stage {stage!r}')
