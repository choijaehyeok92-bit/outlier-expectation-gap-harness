# Universe pipeline — design

StockAnalysis screen → ticker universe → Stage 0 → EV → triage → early exit or full core →
macro → ED/RT → IC → universe index → one-page record → deep report → dashboards.

**The harness decides; the universe indexes and schedules; the report explains.** Nothing in
this layer computes a score, an archetype, a veto outcome, a state, a position or a valuation.
Those come from `aggregate` / `final_verdict.json` exactly as before.

## 1. What already existed, and what this adds

| Existing (authoritative, unchanged) | Added (non-decisional) |
|---|---|
| `runs/<RUN_ID>/` — frozen inputs, agent reports, `aggregate.json`, `final_verdict.json` | `universe/` — an index over those runs |
| `plan` — the only thing that decides which agents run next | `universe run/continue` — calls `plan` and executes what it asks for |
| `aggregate` → `final_verdict.json`, `reconcile_ic` caps | `universe validate` — re-checks those caps against recorded artifacts |
| `easy_report.md`, `one_page_investment_record.md` | `deep_report.md/json` — explains the recorded verdict (Report Agent RP) |
| CI workflows that copy staged reports from `.harness_inputs/<RUN>/` | the same staging convention, used by the batch runner |

Decision code (`rubric`, `archetypes`, `veto`, `state`, `planner`, `valuation`, `macro_geo`,
`compute_aggregate`, `final_verdict`) is not modified. `runtime.main()` gains one line that
registers the `universe` sub-commands.

## 2. Conflicts found and how they were resolved

1. **The harness never calls a model.** Agent output is produced outside the harness (CI workflows
   copy `.harness_inputs/<RUN>/reports/<AID>.json`). The batch runner therefore takes agent output
   from *executors*: staged inputs (default), an optional `--agent-cmd` template for a model CLI,
   and the global macro cache. When no executor can supply a report, the runner writes the prompt
   (`runs/<RUN>/<AID>_prompt.md`, the existing convention) and marks the ticker `BLOCKED` with
   `awaiting: [...]`. It never fabricates a report.
2. **`report` already exists** (writes `easy_report.md` after a fresh aggregate). Its default
   behaviour is kept byte-for-byte; the deep report is added next to it, `--existing-run` reads
   recorded artifacts only, and `report validate T` is accepted as an optional second positional.
3. **Early exit status.** §5 of the brief records an early exit as `run_status: COMPLETE` with
   `early_exit: true`; §6 lists `EARLY_EXIT` as a status. The index stores lifecycle
   (`COMPLETE` + `early_exit`) and dashboards/CSV display `EARLY_EXIT` for those rows.
   The final state itself is `ic_state`, mirrored from `final_verdict.ic_state`
   (`EARLY_EXIT_NON_FIT` when IC was intentionally not run).
4. **Freeze hashes cover all of `harness_core/*.py` and `agents/**`.** Adding modules therefore
   requires in-flight frozen runs to re-freeze, exactly like every earlier harness change (at this
   commit every committed run is already config-stale). That contract is kept, not weakened: the
   runner never re-freezes on its own. A stale freeze makes the ticker `BLOCKED` with the reason.
   `config/universe.json` is *not* in the hash set because it holds no decision policy.
5. **Reconstructed runs.** Some committed runs were reconstructed by a connector: `final_verdict.json`
   may leave an early-exit `position_range` null, and GOOGL (on its work branch) has `aggregate.json`
   but no `final_verdict.json` and no manifest. The index copies what is recorded; a null
   non-score position is shown as the harness's own configured text for that state
   (`state_thresholds.non_score_states`, labelled `position_range_source`). A run without
   `final_verdict.json` is `BLOCKED (unfinalized)`, never `COMPLETE`.
6. **Re-running a ticker on a new date.** `run_dir(ticker)` is fixed and `init` never overwrites, and
   dated runs already exist (`NVDA-2026-09-18`). A later as-of goes to `runs/<TICKER>-<AS_OF>/`; the
   earlier frozen run is never moved or overwritten, and the index keeps `previous_runs` plus an
   append-only history.
7. **Screen names are not archetypes.** A StockAnalysis screen the investor named "compounder" is a
   provenance label (`screens`). The archetype comes only from deterministic gates.
8. **The Report Agent is not a planner agent.** Adding RP to `config/agents_manifest.json` would
   change `init`, the planner and the veto gate (every file in `reports/` is read as an agent
   report). RP has its own instructions and never writes into `reports/`.

## 3. Data model

`universe/universe.json` — `{schema_version, updated_at, tickers: {TICKER: row}}`.

| Field group | Fields |
|---|---|
| identity | `ticker`, `run_id`, `company_name`, `exchange`, `security_type` (`equity`/`etf`/`fund`/`unknown`) + `security_type_source` |
| provenance | `source`, `sources[]`, `screen_name` (first), `screens[]`, `screener_fields{}`, `imported_at`, `last_imported_at`, `queue_seq` |
| lifecycle | `as_of_date`, `run_status` (`QUEUED/RUNNING/FAILED/BLOCKED/COMPLETE`), `stage` (`stage0/ev/triage/domain_analysis/macro/evidence_and_red_team/ic/complete`), `started`, `blocked_reason`, `awaiting[]`, `last_error{}`, `attempts` |
| copied decision fields | `score`, `score_ex_valuation`, `coverage_weight`, `archetype`, `archetype_fit`, `secondary_archetypes`, `reachable_archetypes`, `domain_scores{ev,as,di,fs,...}`, `hard_veto_status`, `mechanical_pre_ic_state`, `ic_state`, `ic_complete`, `position_range` (+`_source`), `position_range_pre_ic`, `macro_pacing`, `price_to_base`, `current_price`, `valuation{bear,base,bull}`, `early_exit`, `review_only`, `reconstructed`, `decision_policy_version`, `verdict_source` |
| traceability | `source_files{final_verdict, aggregate, ic, digest, one_page, deep_report, ...}`, `source_hashes{...}` (sha256 at sync time) |
| reports | `report_status`, `report_tier` |

Derived files, rewritten on every save: `universe/universe.csv` (the export format) and
`universe/queue.json` (processing order and pending/blocked/failed/complete lists).
`universe/history/<T>.jsonl` is append-only; `universe/snapshots/<label>.json` copies the index.

A sync reads `runs/<RUN_ID>/` and never writes there. Numbers come from `final_verdict.json`,
or from `aggregate.json` before a run is finalized. `COMPLETE` requires `final_verdict.json` and
either an early exit or an IC report the verdict already includes.

## 4. Import

`universe import FILE --as-of D` (`.txt`, `.csv`/`.tsv`, `.json`) and `universe import-screen FILE`
(same, source `stockanalysis_screenshot`, for vision-extracted lists).

* Uppercase, trim, drop `$`, split `NASDAQ:` style prefixes, write share classes with a dot
  (`BRK-B`, `BRK/B` → `BRK.B`, matching `runs/BRK.B`).
* Reject anything that is not a listed-ticker shape (row numbers, words, unknown prefixes).
* De-duplicate within a file; a ticker in several screens keeps every screen in `screens[]`.
* Merge into existing rows (screens and sources are unioned; first `imported_at` is kept).
* Mark ETFs/funds only on explicit evidence (a type column, a small known-fund list, or a fund
  word in the name) and leave them `BLOCKED`: the harness analyzes operating companies.
* TXT: one ticker per line with an optional name (`LLY - Eli Lilly`); several tickers per line only
  when comma/semicolon separated. CSV: header aliases include StockAnalysis exports
  (`Symbol`, `Company Name`); headerless `ticker,screen` also works. JSON: a list, `{"tickers":[...]}`
  or `{"screens":{name:[...]}}`.

## 5. Batch runner (planner-driven)

For each ticker, sequentially: `plan → execute requested agents → validate → aggregate → digest → plan`,
until the planner returns `stop_early` / `stop_complete`, or the requested stop boundary is reached.
The runner never orders stages itself. `lead_agents` (EV) only runs EV ahead of the rest of the same
planner step so an invalid EV stops a ticker before AS/DI/FS are spent.

Stage 0 is `init` → staged `company_context.json`/sources/pack or `fetch` (with an SEC user agent)
→ FP via an executor → `validate-pack` → `freeze`. Missing locked context fields or Stage 0 gaps are
`BLOCKED`, never guessed. `--triage-only` stops once triage is done; `continue --eligible-only` then
advances only tickers with a reachable archetype. Early-exit tickers are finalized and never get
core, macro, ED/RT or IC work.

Failure isolation: each ticker runs under its own lock; an exception is recorded
(`command`, `stage`, `exception_type`, `stderr`, `retryable`, `timestamp`) and the batch moves on.
`retry` re-queues failed tickers; completed stages are never re-run because the planner only asks
for incomplete agents.

## 6. Report tiers

`EARLY_EXIT_NON_FIT` → no deep report · `REJECT` → summary · `WATCH` (and hold/trim/exit review states)
→ concise · `STARTER` and above → full. `--force` overrides the tier, never the content.

## 7. Invariants (`universe validate`, `report validate`)

COMPLETE without `final_verdict.json`; a buy state with Hard Veto ≠ CLEARED, coverage ≠ 100, a pending
structural re-analysis, `non_fit` or review-only; an IC state above the deterministic cap for the
mechanical state; an IC-reconciliation replay (`state.reconcile_ic` over `aggregate.json` + `IC.json`)
that disagrees with the recorded state/position; an early exit with a completed IC report (warning);
a universe score that differs from the verdict; a deep report whose state/position differs from
`final_verdict.json`.

## 8. Implementation status

| Phase | Scope | Status |
|---|---|---|
| 1 | design, data model | this document, `config/universe.json`, `harness_core/universe.py` |
| 2 | import / export / status / sync / validate | `universe_store.py`, `universe_cli.py`, `tests/test_universe.py` |
| 3 | batch runner, early exit, resume/retry, dry run | pending |
| 4 | Report Agent, deep report, report validation | pending |
| 5 | universe dashboards, history CLI, parallel workers, docs | pending |
