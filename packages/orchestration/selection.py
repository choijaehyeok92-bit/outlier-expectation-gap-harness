"""Which companies an orchestration stage runs, and why the others did not.

Selection reads a screen's leaderboard and the config, and never a ticker. A
candidate that cannot be worked on is not dropped: it comes back with the
reason, because "why was this not triaged" should not require re-running the
screen to answer.

`stage` chooses which policy applies. Triage skips a company whose four triage
reports are already valid; the full harness does not, because its loop starts
wherever the planner says and may legitimately begin at triage. What the full
stage skips instead is a company the planner already screened out and one whose
IC report is already written.
"""
from dataclasses import dataclass, field
from typing import Optional

from . import contracts
from .agent_step import readiness, run_directory


@dataclass
class Candidate:
    run_id: str
    ticker: str
    rank: int
    eligible: bool
    reason: Optional[str] = None
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {'run_id': self.run_id, 'ticker': self.ticker, 'rank': self.rank,
                'eligible': self.eligible, 'reason': self.reason, **self.detail}


def _triage_complete(run_id: str, agents: list) -> bool:
    """Every triage agent already has a complete report the harness accepts."""
    from .agent_step import existing_report
    for agent_id in agents:
        report = existing_report(run_id, agent_id)
        if report is None or report.get('analysis_status') != 'complete':
            return False
        if contracts.validate(report):
            return False
    return True


def _ic_complete(run_id: str) -> bool:
    """The IC chair's report exists and the harness still accepts it."""
    from .agent_step import existing_report
    runtime = contracts.harness()
    agent_id = next((a['agent_id'] for a in runtime.MANIFEST
                     if a['domain'] == runtime.IC_DOMAIN), 'IC')
    report = existing_report(run_id, agent_id)
    return bool(report and report.get('analysis_status') == 'complete'
                and not contracts.validate(report))


def selection_policy(config: Optional[dict] = None, stage: str = 'triage') -> dict:
    config = config or contracts.load_config()
    if stage == 'full':
        return (config.get('full_harness') or {}).get('selection') or config['selection']
    return config['selection']


def select_candidates(rows: list, config: Optional[dict] = None, top_n: Optional[int] = None,
                      agents: Optional[list] = None, stage: str = 'triage') -> list:
    """Screen rows to an ordered candidate list, each marked eligible or not."""
    config = config or contracts.load_config()
    policy = selection_policy(config, stage)
    agents = agents or contracts.triage_agents(config)
    limit = top_n if top_n is not None else int(policy.get('top_n', 30))

    candidates = []
    for rank, row in enumerate(rows, 1):
        run_id = row.get('run_id') or row.get('ticker')
        ticker = (row.get('ticker') or run_id or '').upper()
        if not run_id:
            continue
        detail = {'core_score': row.get('core_score'),
                  'hard_veto_status': row.get('hard_veto_status'),
                  'has_harness_run': row.get('has_harness_run')}

        if not (run_directory(run_id) / 'company_context.json').exists():
            # A screen can surface a company the warehouse knows and the harness
            # has never seen. That is the funnel working, not an error.
            candidates.append(Candidate(run_id, ticker, rank, False,
                                        'no harness run; `harness.py init` and complete Stage 0 first',
                                        detail))
            continue
        if policy.get('skip_when_early_exit', True) and row.get('early_exit'):
            candidates.append(Candidate(run_id, ticker, rank, False,
                                        'the planner already recorded an early exit', detail))
            continue
        if policy.get('skip_when_triage_complete', False) and _triage_complete(run_id, agents):
            candidates.append(Candidate(run_id, ticker, rank, False,
                                        'triage is already complete and valid', detail))
            continue
        if policy.get('skip_when_ic_complete', False) and _ic_complete(run_id):
            candidates.append(Candidate(run_id, ticker, rank, False,
                                        'the IC report is already written and valid', detail))
            continue
        if policy.get('require_frozen_run', True):
            gate = readiness(run_id)
            if not gate['ready']:
                candidates.append(Candidate(run_id, ticker, rank, False, gate['reason'], detail))
                continue
        candidates.append(Candidate(run_id, ticker, rank, True, None, detail))

    eligible = [c for c in candidates if c.eligible][:limit]
    chosen = {c.run_id for c in eligible}
    for candidate in candidates:
        if candidate.eligible and candidate.run_id not in chosen:
            candidate.eligible = False
            candidate.reason = f'beyond the configured top {limit}'
    return candidates
