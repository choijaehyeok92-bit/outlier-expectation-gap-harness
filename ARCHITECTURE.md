# Architecture and migration — v3.1

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
activated optional diagnostic. Growth is a fourth archetype, using existing domains and a forward revenue-growth estimate; its configurable initial gates do not relax the other three types.

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
and company/source inputs. Prompt generation refuses stale frozen code or inputs. Aggregate/digest/report also refuse stale snapshots before writing. Use fork-run for a new policy run; pure compute_aggregate remains available for read-only comparisons.
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
required to validate against the new schema. Research intake uses jsonschema from requirements.txt; development tests use requirements-dev.txt. Source PDF extraction still optionally needs pypdf.

## v3.1 supplemental research and reporting

research.py creates prioritized questions and validates append-only evidence intake; plain_report.py renders a fresh final decision in Korean. See docs/RESEARCH_ORCHESTRATOR.md for provenance, cutoff and conflict handling. Review-only runs explicitly frozen with --review-only may reach IC despite non-fit. They always prevent new-buy approval; completed MO may record unavailable components without forcing a fabricated fresh observation. Ordinary runs retain the original staging and macro freshness requirements.

New manifests record hash_format=sha256-lf-text-v1: JSON/Markdown/Python/text/YAML hashes normalize CRLF to LF for portable Git checkouts. Other byte changes still invalidate a snapshot. Legacy fork verification accepts matching raw or LF-normalized bytes without editing the historical files.

## v3.2 — 장기 아웃라이어 성장 유형
다섯 번째 투자 가능 유형 `outlier_growth`와 독립 평가축 `long_term_growth`(LG)를 추가했다. LG는 DI와 같이 100점 핵심 점수에 합산하지 않으며 유형 적격 판정과 IC 해석에만 쓰인다. archetype 집합과 tie-breaker는 config 주도이고 런타임은 개수를 고정하지 않는다 — 중복 없는 비어 있지 않은 집합인지, fallback이 투자 유형에 섞이지 않았는지, tie-breaker가 각 유형을 정확히 한 번 호명하는지만 검사한다. `final_verdict.schema.json`은 버전 조건부다: v3.1 산출물은 네 유형 fit만으로도 유효하고, schema_version이 3.2일 때만 다섯 유형 fit을 요구한다. 과거 run은 마이그레이션하지 않는다.

## Universe layer, batch runner and Report Agent (non-decisional)

`universe.py` (pure), `universe_store.py` (atomic JSON, lock files, history), `universe_runner.py`
(planner-driven batch execution), `universe_reports.py` (tiered deep reports, dashboards),
`report_builder.py` / `report_validator.py` (Report Agent RP) and `universe_cli.py` sit on top of the
decision modules and never replace them. They read `final_verdict.json` / `aggregate.json`, call the
existing CLI commands for every mutation (`init`, `freeze`, `prompt`, `validate`, `aggregate`, `digest`,
`cache-macro`, `report`), and never write `final_verdict.json` or a report under `runs/<RUN>/reports/`.
RP is intentionally absent from `agents_manifest.json` so that init, the planner and the veto gate are
unchanged. `config/universe.json` holds presentation/scheduling policy only and is outside the freeze
hash set; the new Python modules and `agents/16_report/` are inside it, like every other harness file,
so in-flight frozen runs must re-freeze after upgrading (the runner reports this as a stale freeze and
never re-freezes). `runtime.dump_json` now writes atomically (same bytes) and `init`'s macro-cache
reuse is exposed as `cached_macro_report` (same output). Details: [docs/UNIVERSE.md](docs/UNIVERSE.md).
