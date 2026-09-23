# V3 decision regression tests

Run `python harness.py selftest` or `python -m unittest discover -s tests -v`.
Install `requirements-dev.txt` for JSON Schema checks; the runtime itself uses the standard library.

The suite tests synthetic Compounder, Buffett Value, Moonshot and non-fit cases; criterion boundaries
and missingness; config-order independence and ties; value traps and veto ownership; optional TQ;
shadow/active calibration; DCF and rubric invariants; component TTL/invalidation and cache isolation;
structural geo routing without score changes; evidence concentration; historical read-only loading;
schema checks; and isolated CLI init/freeze/prompt/validate/plan/aggregate/digest workflows.
Every write is in a temporary directory. Historical runs are never rewritten for tests.

Universe, runner and report tests (`test_universe*.py`, `test_report.py`) build synthetic LLY/NU/GOOGL/MELI-like
runs through the harness's own commands (`universe_fixtures.py`) and stage agent output in
`.harness_inputs/<RUN>/` the way the CI workflows do. They cover import/dedupe/merge/invalid tickers,
read-only sync, gate invariants (veto, coverage, IC cap replay), CSV export, history, triage-only then
eligible-only runs, early exit, resume, failure isolation, dry run, agent-command execution, stale-freeze
blocking, git batch mode, concurrency, deep-report authority/tiering/narrative guards and dashboards.
No test uses the network.
