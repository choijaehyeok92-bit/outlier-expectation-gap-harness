# Architecture and migration — v3

## Modules and decision flow

`harness.py` is the stable CLI entry point. `harness_core/runtime.py` retains file IO, CLI
orchestration, aggregate/digest composition and report validation. Pure policy logic is split
into `rubric.py`, `conditions.py`, `calibration.py`, `archetypes.py`, `veto.py`, `state.py`,
`valuation.py`, `planner.py`, `evidence.py`, `macro_geo.py` and generated policy documentation.
No new model runtime, cache service or database is required.

Frozen company inputs → universal triage → optimistic reachable archetypes → remaining
core score and veto coverage → global regime plus company transmission → ED/RT → eligible
archetype fit ranking → veto/valuation/state gates → IC within deterministic caps → monitoring.

Core weights, existing Compounder gates, Moonshot execution gates and all nine veto definitions
and ownership mappings are preserved. Compounder adds criterion refinement without replacing
its former RF domain gate. Buffett Value uses the existing FCF/share quality rubric rather
than introducing a new owner-earnings domain. DI remains independent; TQ is an explicitly
activated optional diagnostic. No fourth investable archetype exists.

## Fit, reachability and coverage

`domain.*`, `signal.*` and `criterion.<domain>.<criterion>` resolve numeric values only.
Criterion scores require complete, unique rubric IDs and finite scores on the configured step.
Invalid modern rubrics fail loudly; legacy absent rubrics leave criterion values missing.
Fit normalizes condition values with configured weights. Its exact formula and tie rule appear
in [POLICY.md](docs/POLICY.md). Missing contributes zero only to the descriptive fit calculation;
eligibility records it as missing and cannot pass. Hard conditions and core gates are mandatory.
Known unresolved vetoes block eligibility; unreported ownership blocks buy states separately.

Reachability assumes unfinished domains/criteria/signals remain attainable, checks completed
decision scores, and computes the maximum attainable weighted core gate. Known unresolved
vetoes are reviewable, so they do not prematurely terminate research; confirmed vetoes eliminate
reachability. Every positive final path still needs the entire core score and veto coverage.
Legacy field `reachable_archetypes_raw` is retained for consumers but means decision-policy
reachability in v3 (raw in shadow, adjusted in active).

Before IC, no reachable archetype produces an early_exit_record and deterministic final JSON,
including when core coverage is already complete. The last-reachable list is reconstructed in
manifest order from available observations, not represented as actual wall-clock execution history.
IC may lower deployment, but cannot override primary fit ranking, unresolved vetoes, missing
coverage or structural re-analysis. New final records retain the IC report separately.

## Global regime and company transmission

Only allowlisted `scope=global` components are cached in `runs/_macro/<date>/components.json`.
Financial conditions, credit/liquidity, geopolitical events and structural trade each have their
own observation timestamps and config TTLs. Old whole MO reports are never reused across companies.
Latest explicit invalidation prevents falling back to an older observation. Partial fresh components
can be reused; missing/stale inputs request MO refresh and a conservative configured pacing fallback.

Geopolitics is a vector, not a company-quality score. Dimension level maps to a transparent configured
pacing multiplier; the most restrictive financial/geopolitical/missing-data multiplier controls pacing.
Company transmission matches normalized exact tokens against the frozen exposure fields. Lack of
exposure data is unknown. Matching structural event IDs route to named fundamental domains; those
domains must review new company evidence before recording geo_events_reviewed. Expiry does not clear a known pending structural event in that run. No macro arithmetic
is allowed to change domain or core scores. More sophisticated geographic mapping and human audit
of the evidence behind acknowledgments remain outside this deterministic matcher.

## Reproducibility and compatibility

Run manifests and new aggregate/final outputs record strategy_version, schema_version and
decision_policy_version. Freeze hashes implementation modules, policy, prompts, schemas, templates
and company/source inputs. Prompt generation refuses stale frozen code or inputs. Aggregate remains
a read/recompute interface so historical input reports can be inspected under v3 without re-freezing.
For reproducible model comparison, freeze before research and use the same commit and input hashes.

Provider calibration is idempotent. raw_score preserves the pre-provider observable-anchored domain
score; calibrated_score and calibrated_shadow_score preserve the offset calculation; decision_score
uses raw by default. Active mode is explicit and recorded. Raw medians and criterion values are never
overwritten. Existing multi-report disagreement handling is retained, so raw_score can differ from
raw_weighted_median on a legacy/multi-report domain.

Historical reports with retired archetype strings or old provider metadata remain readable and their
artifacts are not rewritten. Recomputing under v3 intentionally applies v3 policy, never maps an old
label automatically into an investment recommendation. Missing historical criteria remain unknown;
legacy reviewer IDs may require fresh ownership review. Exact old classifications require the original
harness commit and configs, not the current schema. Archived config profiles remain available as data;
their apply/revert scripts fail safely rather than reinstall obsolete executable policy.

CLI commands remain available. `policy` is additive. `init` now refuses to overwrite an existing run.
IC writes IC.json and the one-page record; aggregate owns final_verdict.json and enforces gates.
Versioned final schema permits null scores for incomplete/early exits. No historical final JSON is
required to validate against the new schema. The runtime remains standard-library-only; development
schema tests use requirements-dev.txt. Source PDF extraction still optionally needs pypdf.
