"""The two validation layers an agent report must pass, in order.

A model's answer is checked twice and both checks belong to the harness, not
to this package.

First the JSON Schema (`schemas/agent_report.schema.json`) decides whether the
document has the right shape. Then `harness_core.runtime.validate_report`
decides whether it obeys the policy: subscores on the configured step, a
`score_0_100` that actually equals the weighted rubric average, a bear ≤ score
≤ bull ordering, evidence within the declared count, veto strings that exist,
and — for a veto that demands it — elements answered rather than asserted.

The orchestrator adds nothing to either. It cannot loosen a rule, and when a
report fails it does not repair the content; it hands the validator's own error
strings back and asks for the document again.
"""
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AGENT_REPORT_SCHEMA = ROOT / 'schemas' / 'agent_report.schema.json'
TRIAGE_CONFIG = ROOT / 'config' / 'triage.json'


def load_config(path=None) -> dict:
    return json.loads(Path(path or TRIAGE_CONFIG).read_text(encoding='utf-8'))


def load_schema(path=None) -> dict:
    return json.loads(Path(path or AGENT_REPORT_SCHEMA).read_text(encoding='utf-8'))


def harness():
    """The harness runtime. Imported lazily so this package stays optional."""
    from harness_core import runtime
    return runtime


def triage_agents(config: Optional[dict] = None) -> list:
    """The agents Stage 3 runs, checked against the workflow's own triage set.

    `config/triage.json` lists an execution order; `config/workflow.json`
    remains the authority on which domains are triage. If they disagree, that
    is a configuration error worth failing on rather than quietly preferring
    one of them.
    """
    config = config or load_config()
    runtime = harness()
    declared = list(config['triage_agents'])
    domains = set(runtime.EXEC['triage_domains'])
    by_agent = {a['agent_id']: a['domain'] for a in runtime.MANIFEST}
    mismatched = [aid for aid in declared if by_agent.get(aid) not in domains]
    if mismatched:
        raise ValueError(
            f'config/triage.json lists {mismatched}, which workflow.json does not call triage '
            f'({sorted(domains)}). Fix the configs rather than letting the two disagree.')
    missing = domains - {by_agent.get(aid) for aid in declared}
    if missing:
        raise ValueError(f'triage domains {sorted(missing)} have no agent in config/triage.json')
    return declared


def schema_errors(report: dict, schema: Optional[dict] = None) -> list:
    import jsonschema
    validator = jsonschema.Draft202012Validator(schema or load_schema())
    return [f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
            for error in sorted(validator.iter_errors(report), key=lambda e: list(e.absolute_path))]


def policy_errors(report: dict) -> list:
    """The harness's own verdict on a report. Never relaxed here."""
    runtime = harness()
    try:
        errors = list(runtime.validate_report(report))
    except Exception as error:                       # a malformed report, not a policy failure
        return [f'validate_report raised {type(error).__name__}: {error}']
    element_errors = getattr(runtime, 'veto_element_errors', None)
    if element_errors is not None:
        try:
            errors.extend(element_errors(report))
        except Exception as error:
            errors.append(f'veto_element_errors raised {type(error).__name__}: {error}')
    return errors


def validate(report: dict, schema: Optional[dict] = None) -> list:
    """Shape first, then policy. Both must pass before anything is written."""
    errors = schema_errors(report, schema)
    if errors:
        return [f'schema: {e}' for e in errors]
    return [f'policy: {e}' for e in policy_errors(report)]
