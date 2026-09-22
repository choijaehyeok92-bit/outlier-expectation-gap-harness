"""Phase 12 monitoring: observations over time against thresholds already declared.

The layer answers three questions and refuses a fourth.

    What are we watching?      `watchlist` — read back from the agent reports
                               and the deep dive, never authored here
    What has been observed?    `observations` — an append-only log, every row
                               carrying a source and a date
    What needs a person?       `evaluate` — arithmetic against the declared
                               thresholds, plus staleness
    What should we do?         not this layer's question

That last line is the whole design. A `thesis_break` is a request that the
domain reviewer, the veto owner and the IC look again; it is not a sell, and
nothing here can move a score, an archetype, a Hard Veto status, an `ic_state`
or a position range. `drift` is the same discipline applied across runs: it
reports what changed between two harness results and says plainly when the
change measures the policy rather than the company.

A threshold written in prose is reported as `not_machine_checkable` with its
wording intact. Guessing at one would produce a green status nobody checked,
which is worse than no status at all.
"""
# Re-exported under names that do not shadow the submodules they come from:
# `from packages.monitoring import evaluate` must keep meaning the module.
from .drift import series as drift_series
from .evaluate import evaluate as evaluate_company
from .evaluate import portfolio as evaluate_portfolio
from .observations import ObservationRejected, record as record_observation
from .watchlist import build as build_watchlist

__all__ = ['build_watchlist', 'record_observation', 'ObservationRejected',
           'evaluate_company', 'evaluate_portfolio', 'drift_series']
