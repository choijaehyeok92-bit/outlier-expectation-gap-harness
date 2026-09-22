"""Consuming the `job` table: a queue, a handler registry and a loop.

The queue is the database. There is no broker, and that is a decision: `job`
already had `idempotency_key`, `status` and `attempts`, `FOR UPDATE SKIP
LOCKED` is the standard way to hand rows to competing consumers, and the whole
mechanism is exercised by unit tests on both dialects with no service running.
A queue nobody can test is not a queue. Nothing in the handler contract
mentions the transport, so a broker can be put in front of this later.

What a worker may do is deliberately narrow. It calls entry points the CLI
already calls, with arguments from a row instead of from `argparse`. It cannot
move a score, an archetype, a Hard Veto status, an `ic_state` or a position
range, and it cannot use a provider the operator has not allowed — a payload
naming `anthropic` is refused rather than billed.
"""
from .handlers import HandlerRefused, REGISTRY, declared_kinds
from .queue import cancel, claim, complete, enqueue, fail, load_config, reap, retry
from .runner import RunReport, run, run_one

__all__ = ['enqueue', 'claim', 'complete', 'fail', 'cancel', 'retry', 'reap', 'load_config',
           'run', 'run_one', 'RunReport', 'REGISTRY', 'declared_kinds', 'HandlerRefused']
