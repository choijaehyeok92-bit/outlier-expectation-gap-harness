"""Stage 4 for one company: the whole harness workflow, driven by the planner.

Stage 3 ran a fixed list of four agents. Stage 4 runs no list at all. Each
round it asks `harness.py plan` what comes next and executes exactly the agents
that answer names, so the order of the workflow — triage, then any structural
re-analysis, then the remaining scored domains, the macro overlay, the evidence
audit and Red Team, and finally the IC chair — stays where it already was, in
`harness_core.planner`. Adding a domain to the manifest changes what this loop
runs without a line changing here.

Three things the loop refuses to do.

**It does not decide when to stop.** `plan.execution_control` does. `stop_early`
means no investable archetype is reachable and the IC was intentionally not
run; that is a conclusion and the run is recorded as `screened_out`, not as a
failure. `stop_complete` means the workflow finished. `blocked` means the
inputs are stuck, which is never either of those.

**It does not grind.** If a round leaves the planner asking for the same stage
and the same agents, nothing that round produced satisfied it, and repeating
will produce the same nothing. The run stops as `stalled` and says which agents
in which stage were the ones that did not move it. A separate iteration cap
catches anything this misses.

**It does not finish the analysis for anybody.** At a terminal stage it runs
the harness's own `digest` and `report`, which write `digest.md`,
`aggregate.json`, `final_verdict.json` and `easy_report.md`. It never runs
`cache-macro` — that cache is reused by every later `init`, so one run's macro
view would silently spread to other companies — and it never writes
`one_page_investment_record.md`, which is the IC chair's own document.
"""
import argparse
import contextlib
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from . import attachments, contracts
from .agent_step import StepOutcome, readiness, run_agent, run_directory
from .triage import persist_harness_view, refresh_harness_view

TERMINAL_CONTROLS = ('stop_early', 'stop_complete')
STATUS_BY_CONTROL = {'stop_complete': 'completed', 'stop_early': 'screened_out'}


@dataclass
class StageRound:
    index: int
    stage: str
    agents: dict                     # domain -> agent_id, exactly as the planner gave it
    steps: list = field(default_factory=list)
    forced: bool = False
    digest_refreshed: bool = False

    def to_dict(self) -> dict:
        return {'round': self.index, 'stage': self.stage, 'agents': self.agents,
                'forced_rerun': self.forced, 'digest_refreshed': self.digest_refreshed,
                'steps': [step.to_dict() for step in self.steps]}


@dataclass
class FullRunOutcome:
    run_id: str
    ticker: str
    status: str          # completed | screened_out | partial | blocked | stalled | failed
    rounds: list = field(default_factory=list)
    execution_control: Optional[str] = None
    stage: Optional[str] = None
    next_agents: dict = field(default_factory=dict)
    harness_snapshot: dict = field(default_factory=dict)
    artifacts: list = field(default_factory=list)
    reason: Optional[str] = None
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None

    @property
    def steps(self) -> list:
        """Every agent step across every round, so a batch can count them."""
        return [step for round_ in self.rounds for step in round_.steps]

    @property
    def reached_terminal(self) -> bool:
        return self.execution_control in TERMINAL_CONTROLS

    def to_dict(self) -> dict:
        return {'run_id': self.run_id, 'ticker': self.ticker, 'status': self.status,
                'execution_control': self.execution_control, 'stage': self.stage,
                'next_agents': self.next_agents, 'harness_snapshot': self.harness_snapshot,
                'artifacts': self.artifacts, 'reason': self.reason,
                'started_at_utc': self.started_at_utc, 'finished_at_utc': self.finished_at_utc,
                'stages_run': [round_.stage for round_ in self.rounds],
                'rounds': [round_.to_dict() for round_ in self.rounds]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def settings(config: Optional[dict] = None) -> dict:
    config = config or contracts.load_config()
    return config.get('full_harness') or {}


FINAL_ARTIFACTS = ('aggregate.json', 'final_verdict.json', 'digest.md', 'easy_report.md')


def existing_artifacts(run_id: str) -> list:
    run = run_directory(run_id)
    return [f'runs/{run.name}/{name}' for name in FINAL_ARTIFACTS if (run / name).exists()]


def finalize(run_id: str, config: Optional[dict] = None) -> list:
    """Write the harness's own end-of-run artifacts. Names them; writes none itself."""
    runtime = contracts.harness()
    written = []
    digest = attachments.digest_policy(config)
    with contextlib.redirect_stdout(io.StringIO()):
        runtime.cmd_digest(argparse.Namespace(
            ticker=run_id, thesis_chars=int(digest.get('thesis_chars', 160)),
            unknowns=int(digest.get('unknowns', 2))))
        # `report` recomputes the verdict and rewrites aggregate.json and
        # final_verdict.json beside easy_report.md, so nothing here is stale.
        runtime.cmd_report(argparse.Namespace(ticker=run_id))
    written = existing_artifacts(run_id)
    return written


def _ticker(run_id: str) -> str:
    runtime = contracts.harness()
    path = run_directory(run_id) / 'company_context.json'
    if not path.exists():
        return run_id
    return runtime.load_json(path).get('ticker') or run_id


def _signature(stage: str, agents: dict) -> tuple:
    return (stage, tuple(agents.values()))


def full_harness_company(run_id: str, provider, config: Optional[dict] = None,
                         force: bool = False, max_iterations: Optional[int] = None,
                         on_round=None) -> FullRunOutcome:
    """Run one company all the way to whatever the planner calls the end."""
    config = config or contracts.load_config()
    policy = settings(config)
    cap = int(max_iterations if max_iterations is not None
              else policy.get('max_stage_iterations', 12))
    force_stages = set(policy.get('force_rerun_stages') or [])

    outcome = FullRunOutcome(run_id=run_id, ticker=_ticker(run_id), status='failed',
                             started_at_utc=_now())
    gate = readiness(run_id)
    if not gate['ready']:
        outcome.status, outcome.execution_control = 'blocked', 'blocked'
        outcome.reason = gate['reason']
        outcome.finished_at_utc = _now()
        return outcome

    previous = None
    for index in range(1, cap + 1):
        try:
            # Read-only: a round that turns out to have nothing to do must
            # leave the run byte-for-byte as it found it.
            view = refresh_harness_view(run_id, write=False)
        except SystemExit as error:
            outcome.status, outcome.execution_control = 'blocked', 'blocked'
            outcome.reason = str(error)
            break

        step = view['plan']
        outcome.stage = step.get('stage')
        outcome.execution_control = step.get('execution_control')
        outcome.next_agents = step.get('agents') or {}
        outcome.harness_snapshot = view['snapshot']

        if outcome.execution_control in TERMINAL_CONTROLS:
            break
        if outcome.execution_control == 'blocked':
            outcome.status = 'blocked'
            outcome.reason = step.get('statement') or 'the planner reports the run is blocked'
            break

        agents = dict(outcome.next_agents)
        if not agents:
            # `continue` with nothing to run is a contradiction, not a finish.
            outcome.status = 'stalled'
            outcome.reason = (f'the planner says continue at stage {outcome.stage!r} but names no '
                              'agent. Nothing was run and nothing would change on a retry.')
            break

        signature = _signature(outcome.stage, agents)
        if policy.get('stop_when_plan_repeats', True) and signature == previous:
            outcome.status = 'stalled'
            outcome.reason = (
                f'stage {outcome.stage!r} asked for {sorted(agents.values())} a second time with '
                'nothing changed. Those reports did not satisfy the planner, and running them '
                'again would produce the same result. Look at what that stage still wants.')
            break
        previous = signature

        round_ = StageRound(index=index, stage=outcome.stage, agents=agents,
                            forced=force or outcome.stage in force_stages)
        # Work is about to happen, so the harness's own artifacts are brought
        # up to date first: an agent in this round may read aggregate.json.
        persist_harness_view(run_id)
        if attachments.needs_digest(outcome.stage, config):
            # ED, RT and IC are told to read digest.md. Make it current first.
            attachments.refresh_digest(run_id, config)
            round_.digest_refreshed = True
        outcome.rounds.append(round_)

        blocked = None
        for agent_id in agents.values():
            result = run_agent(run_id, agent_id, provider, config=config, force=round_.forced)
            round_.steps.append(result)
            if result.status == 'blocked':
                blocked = result
                break
        if on_round is not None:
            on_round(round_)
        if blocked is not None:
            outcome.status, outcome.execution_control = 'blocked', 'blocked'
            outcome.reason = blocked.reason
            break
    else:
        # The cap was spent. Ask once more before calling it a stall: the last
        # round may well have been the one that finished the workflow.
        try:
            view = refresh_harness_view(run_id, write=False)
            outcome.stage = view['plan'].get('stage')
            outcome.execution_control = view['plan'].get('execution_control')
            outcome.next_agents = view['plan'].get('agents') or {}
            outcome.harness_snapshot = view['snapshot']
        except SystemExit as error:
            outcome.status, outcome.execution_control = 'blocked', 'blocked'
            outcome.reason = str(error)
        if not outcome.reached_terminal and outcome.status != 'blocked':
            outcome.status = 'stalled'
            outcome.reason = (f'the planner still wanted work after {cap} stage rounds '
                              '(full_harness.max_stage_iterations). That is more rounds than '
                              'the workflow has stages, so something is not converging.')

    if outcome.reached_terminal:
        failed = [step for step in outcome.steps if not step.ok]
        outcome.status = STATUS_BY_CONTROL[outcome.execution_control]
        if failed:
            # The planner stopped, but part of the evidence behind that stop is
            # missing. Not a finished analysis, whatever the stage says.
            outcome.status = 'partial'
            outcome.reason = f'{len(failed)} agent(s) did not produce a valid report'

    if outcome.reached_terminal and outcome.stage in (policy.get('finalize') or {}).get(
            'on_terminal_stages', ['early_exit', 'complete']):
        outcome.artifacts = existing_artifacts(run_id)
        # A run that was already finished is left alone. Rewriting four
        # artifacts that nothing changed would make "this re-run did nothing"
        # false in the only place a person checks it — the file system.
        if outcome.rounds or len(outcome.artifacts) < len(FINAL_ARTIFACTS):
            try:
                outcome.artifacts = finalize(run_id, config)
            except SystemExit as error:
                outcome.reason = f'{outcome.reason or ""} (finalize failed: {error})'.strip()

    outcome.finished_at_utc = _now()
    return outcome
