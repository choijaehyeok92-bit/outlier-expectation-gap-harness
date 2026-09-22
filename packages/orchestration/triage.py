"""Stage 3 for one company: the four triage agents, then the harness's verdict.

The order is the harness's (`config/workflow.json` names the triage domains;
`config/triage.json` only sequences them), and the verdict is the harness's
too. After the agents have written their reports this module runs `aggregate`
and `plan` exactly as a person would, and then does what the planner says.

`plan.execution_control` is obeyed, not interpreted:

    continue        more stages remain; Stage 3 has done its part
    stop_early      no investable archetype is reachable — a real conclusion
    stop_complete   the workflow is finished
    blocked         inputs or validation are stuck; NOT done, and recorded as such

An early exit is a result. A block is a defect to fix. Collapsing the two would
let a batch report a company as "screened out" when in truth nobody could read
its filings.
"""
import argparse
import contextlib
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from . import contracts
from .agent_step import StepOutcome, readiness, run_agent, run_directory

SNAPSHOT_FIELDS = ('score_100', 'score_100_ex_valuation', 'classification', 'hard_veto_status',
                   'mechanical_pre_ic_state', 'early_exit', 'coverage_weight')


@dataclass
class TriageOutcome:
    run_id: str
    ticker: str
    status: str                      # completed | partial | blocked | failed
    steps: list = field(default_factory=list)
    execution_control: Optional[str] = None
    stage: Optional[str] = None
    next_agents: dict = field(default_factory=dict)
    harness_snapshot: dict = field(default_factory=dict)
    reason: Optional[str] = None
    finished_at_utc: Optional[str] = None

    @property
    def triage_complete(self) -> bool:
        return all(step.ok for step in self.steps) and bool(self.steps)

    def to_dict(self) -> dict:
        return {'run_id': self.run_id, 'ticker': self.ticker, 'status': self.status,
                'execution_control': self.execution_control, 'stage': self.stage,
                'next_agents': self.next_agents, 'harness_snapshot': self.harness_snapshot,
                'reason': self.reason, 'finished_at_utc': self.finished_at_utc,
                'steps': [step.to_dict() for step in self.steps]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def refresh_harness_view(run_id: str) -> dict:
    """Run aggregate and plan, as a person would, and read back what they said.

    `aggregate` is the harness writing its own artifacts; this module does not
    compute or store a score of its own.
    """
    runtime = contracts.harness()
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        runtime.cmd_aggregate(argparse.Namespace(ticker=run_id))
    reports = runtime.load_reports(run_id)
    result = runtime.compute_aggregate(run_id, reports)
    step = runtime.plan(run_id, reports, result)
    archetype = result.get('archetype') or {}
    snapshot = {field: result.get(field) for field in SNAPSHOT_FIELDS}
    snapshot['archetype'] = archetype.get('id')
    return {'plan': step, 'snapshot': snapshot}


def triage_company(run_id: str, provider, config: Optional[dict] = None,
                   force: bool = False, agents: Optional[list] = None) -> TriageOutcome:
    """Run the triage agents for one company and report what the harness then said."""
    config = config or contracts.load_config()
    runtime = contracts.harness()
    agents = agents or contracts.triage_agents(config)
    context_path = run_directory(run_id) / 'company_context.json'
    ticker = run_id
    if context_path.exists():
        ticker = runtime.load_json(context_path).get('ticker') or run_id

    outcome = TriageOutcome(run_id=run_id, ticker=ticker, status='failed')
    gate = readiness(run_id)
    if not gate['ready']:
        outcome.status, outcome.reason = 'blocked', gate['reason']
        outcome.execution_control = 'blocked'
        outcome.finished_at_utc = _now()
        return outcome

    for agent_id in agents:
        step = run_agent(run_id, agent_id, provider, config=config, force=force)
        outcome.steps.append(step)
        if step.status == 'blocked':
            outcome.status, outcome.reason = 'blocked', step.reason
            outcome.execution_control = 'blocked'
            outcome.finished_at_utc = _now()
            return outcome

    try:
        view = refresh_harness_view(run_id)
    except SystemExit as error:
        outcome.status, outcome.reason = 'blocked', str(error)
        outcome.execution_control = 'blocked'
        outcome.finished_at_utc = _now()
        return outcome

    outcome.execution_control = view['plan'].get('execution_control')
    outcome.stage = view['plan'].get('stage')
    outcome.next_agents = view['plan'].get('agents') or {}
    outcome.harness_snapshot = view['snapshot']
    failed = [step for step in outcome.steps if not step.ok]
    if failed:
        outcome.status = 'partial'
        outcome.reason = f'{len(failed)} agent(s) did not produce a valid report'
    elif outcome.execution_control == 'blocked':
        outcome.status, outcome.reason = 'blocked', view['plan'].get('statement')
    else:
        outcome.status = 'completed'
    outcome.finished_at_utc = _now()
    return outcome
