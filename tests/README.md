# V3 decision regression tests

Run `python harness.py selftest` or `python -m unittest discover -s tests -v`.
Install `requirements-dev.txt` for JSON Schema checks; the runtime itself uses the standard library.

The suite tests synthetic Compounder, Buffett Value, Moonshot and non-fit cases; criterion boundaries
and missingness; config-order independence and ties; value traps and veto ownership; optional TQ;
shadow/active calibration; DCF and rubric invariants; component TTL/invalidation and cache isolation;
structural geo routing without score changes; evidence concentration; historical read-only loading;
schema checks; and isolated CLI init/freeze/prompt/validate/plan/aggregate/digest workflows.
Every write is in a temporary directory. Historical runs are never rewritten for tests.

`test_screening.py`, `test_deep_dive.py` and `test_api.py` cover the web research layer: unit and
percent parsing, the ScreeningSpec contract and its field allowlist, the compiler's three-valued
logic (missing is never zero), natural-language resolution against the config lexicon, the
read-only run index, deep-dive selection and stage validation, the report invariants that keep a
deep dive from editing a harness result or returning positive-only research, and the API routes.
`test_data_adapters.py` covers SEC and DART ingestion against recorded fixtures: the account
resolution chain, fiscal period arithmetic for December and non-December year ends, the refusal to
read a nine-month cumulative as a quarter, CFS/OFS preference and the refusal to mix them, the
as-of cutoff on both filings and facts, restatement flagging, universe exclusions with their
reasons, the separation of market data from the regulators, and the rule that an API key never
reaches a fixture filename.

`test_api.py` skips itself when `apps/api/requirements.txt` is not installed and
`test_data_adapters.py` when `data_adapters/requirements.txt` is not; the rest need only
`jsonschema`.
