"""Stage 3 orchestration: running the harness over many candidates.

What this package does is sequencing. It decides which company to look at next
and which agent to run, it retries a step that failed, and it refuses to write
anything the harness would reject. It does not decide anything about a company:
scores, archetypes, Hard Veto statuses, valuations and position ranges are the
harness's, computed from agent reports it validated.

**What the tests here verify, and what they do not.** The fixtures exercise
sequencing, retry behaviour, idempotency, and the refusal to bypass a gate.
They do not verify analysis quality, the soundness of a score, the authenticity
of evidence or the correctness of a Hard Veto judgement — none of which a
canned response can establish. That boundary is recorded in
`config/triage.json` under `verification_scope` and stamped onto every batch
record, so a reader of a result never has to guess which one they are holding.
"""
from .agent_step import AgentStep, StepOutcome, run_agent
from .batch import BatchResult, run_batch
from .selection import Candidate, select_candidates
from .triage import TriageOutcome, triage_company

__all__ = ['AgentStep', 'StepOutcome', 'run_agent', 'BatchResult', 'run_batch',
           'Candidate', 'select_candidates', 'TriageOutcome', 'triage_company']
