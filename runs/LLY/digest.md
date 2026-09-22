# Digest — LLY (as of 2026-09-21)

> Reconstructed v3.3 EV-stage output. The connected environment cannot replay the local EDGAR/CLI subprocess, so Stage 0, deterministic validation and valuation are reproduced without claiming a literal CLI run.

score **56.75** (ex-val None, Reject) · archetype **non_fit** · veto **PENDING_REVIEW** · state **INCOMPLETE**

signals: price/Base **0.9081x** · forward revenue CAGR **24%** · market cap **$1.041T** · reachable(raw) **['compounder', 'outlier_growth', 'growth']**

## Stage 0

- latest annual: PASS
- latest interim: PASS
- trailing quarters: PASS **7/6**
- historical annuals: PASS **3/3**
- proxy: PASS
- earnings release: PASS
- debt/financing event: PASS
- insider ownership: PASS
- blocking gaps: **0**
- invariant errors: **0**
- advisory gap: **investor_materials**

The pack explicitly preserves pharmaceutical reinvestment issues: acquired IPR&D is not automatically treated as economically non-recurring, and manufacturing capex is separated from acquisitions/pipeline investment.

## Frozen context

- price: **$1,164.89**
- diluted shares: **893.7M**
- market cap: **$1.041T**
- conservative net cash: **-$42.10B**
- net cash/share: **-$47.11**

Q2 2026 revenue was **$22.974B** and net income **$7.095B**. H1 OCF was **$16.023B** and capex **$5.259B**.

Mounjaro **$9.943B** + Zepbound **$4.928B** represented roughly **64.7%** of Q2 revenue, making franchise concentration a central valuation risk.

## Expectation / Valuation — 56.75

| Agent | Score | Bear–Bull | Confidence | Verdict |
|---|---:|---:|---:|---|
| EV | **56.75** | 35–80 | 0.82 | neutral |

Locked values:
- Bear **$345.26**
- Base **$1,282.74**
- Bull **$2,016.84**
- frozen price **$1,164.89**
- price/Base **0.9081x**
- Bull/current **1.73x**
- Bear/current **0.30x**

Subscores:
- reverse DCF burden: **60**
- Base return: **55**
- valuation robustness: **55**

The price-above-Bull Hard Veto is **cleared**.

## Interpretation

The current price is modestly below Base rather than deeply discounted. Base assumes owner-FCF/share rises from roughly a **$20.35 TTM proxy** toward **$113** by year 10, so the valuation still depends on a long duration of strong metabolic-franchise execution and normalization of heavy manufacturing investment.

The strongest positive is that the growth engine is broadening: orforglipron was FDA-approved for obesity and retatrutide Phase 3 obesity/type 2 diabetes trials met primary endpoints. The strongest limitation is that Mounjaro/Zepbound already dominate current economics while realized pricing is under pressure.

## Current reachability

Still reachable:
- **Compounder**
- **Growth**
- **Outlier Growth**

Already excluded:
- Buffett Value — price/Base **0.9081 > 0.85**
- Moonshot — market cap **$1.041T > $50B**

The current 56.75 is an **EV-only partial score**, not a final rejection.

## Next plan

`triage`: **AS, DI, FS**

Universal triage and Hard Veto ownership remain incomplete.
