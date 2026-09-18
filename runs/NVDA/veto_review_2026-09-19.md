# NVDA Hard Veto re-adjudication — 2026-09-19

## Scope

This is a post-run Hard Veto adjudication by **OpenAI GPT-5.6 Sol (reasoning effort: high)** over the frozen NVDA evidence set dated 2026-09-17.

The base run remains the existing Claude-Opus-5 run. This review **does not rerun or replace domain scores, DCF paths, frozen inputs, or provider calibration**. It changes only Hard Veto statuses and the derived veto gate / mechanical state.

Decision rule: a Hard Veto is triggered only when the literal veto condition is supported, not merely because the underlying risk is material. Risks already reflected in domain scores should not be double-counted as a veto without evidence that the veto wording itself is satisfied.

## Changes

### V4 — 고객가치 없이 마케팅·보조금에 의존하는 성장
**conditional → cleared**

The predicate "고객가치 없이" is not supported by the frozen evidence. Q2 FY27 gross margin was 75.0%, SG&A was 1.4% of revenue, H1 customer advances were $15.6B, and Hyperscale / ACIE revenue grew +102% / +138% y/y. Equity investments and guarantees remain a material demand-quality risk, but they do not establish that aggregate growth is subsidy-dependent.

Re-open if supported customers become a dominant revenue source or if removing NVIDIA support causes customer unit economics / demand to collapse.

### V8 — 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
**conditional → cleared**

Concentration is high, but the "치명적" threshold is not met. The largest direct customer represented 16% of Q2 revenue and the top three represented 44% of H1 revenue. More importantly, NVIDIA effectively lost China's data-center compute market to export controls while Q2 revenue still grew +105.9% y/y. The observed stress does not show fatal dependence on one customer or one regulation.

Re-open if a single customer exceeds 25% with poor substitutability, or a second major jurisdiction restriction causes sustained revenue / owner-FCF impairment.

### V9 — 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음
**conditional → cleared**

Net cash of about $23.2B, TTM operating cash flow of about $134.4B, and only about $1.0B due within one year make insolvency / forced financing a weak current path. The Bear value near $75 represents a severe valuation and owner-FCF reset while the business remains cash-generative, not business extinction.

Expected-return unattractiveness and drawdown risk are already captured in EV and AS. Re-blocking the same price risk as a Hard Veto would double-count it.

Re-open if survival requires external capital or a stress case implies structural disappearance of owner FCF rather than valuation compression.

## Result

- Confirmed vetoes: 0
- Unresolved vetoes: 0
- Hard Veto gate: **CLEARED**
- Aggregate score: **73.94** (unchanged)
- Archetype: **Compounder** (unchanged, provisional due provider calibration)
- Mechanical pre-IC state: **NORMAL_CANDIDATE**
- Mechanical position band: **2–4%**
- Macro pacing multiplier: **0.7** (unchanged)

The remaining concerns — ecosystem financing, concentration, custom silicon, off-balance commitments, and weak expectation gap at price/Base ≈ 1.03 — remain active scoring and monitoring risks rather than Hard Vetoes.
