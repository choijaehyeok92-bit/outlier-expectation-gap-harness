# NVDA filing-first rerun — 2026-09-18

This run re-executed the harness using the user-provided NVIDIA SEC filings as the primary company evidence source:

- FY2026 Form 10-K filed 2026-02-25
- Q2 FY2027 Form 10-Q filed 2026-08-26
- Form 8-K filed 2026-09-03 (Hugging Face acquisition)

## Frozen comparison inputs

- Reference price: $219.34
- net_cash_per_share: $0.9635
- 5-year valuation percentile signal: 0.05
- Macro pacing multiplier: 0.9
- DCF policy: 9% required return, 10-year horizon, 15x / 20x / 25x terminal multiples

These were held consistent with the prior same-date run to isolate the effect of filing evidence.

## Final result

- Core score: **75.56**
- Ex-valuation score: **79.01**
- Coverage: **100%**
- DI: **85.0**
- Archetype: **Compounder**
- Hard Veto: **CLEARED**
- IC state: **NORMAL_CANDIDATE**
- Mechanical position band: **2–4%**
- IC initial sizing: **1.5–2%**, staged at **0.9x** macro pacing

## Domain scores

| Domain | Score |
|---|---:|
| Structural Leadership | 86.25 |
| Customer / Product | 78.25 |
| Moat Trajectory | 82.00 |
| Reinvestment / FCF | 82.00 |
| Management / Allocation | 78.50 |
| Financial Survival | 76.00 |
| Expectation / Valuation | 56.00 |
| Asymmetry | 63.50 |
| Disruptive Innovation | 85.00 |

## Deterministic valuation

- Bear: ~$92.7
- Base: ~$233.5
- Bull: ~$445.9
- Price / Base: ~0.939

## Main filing-driven changes vs prior run

The rerun kept structural leadership strong but lowered valuation, asymmetry, financial-survival and reinvestment scores after explicitly incorporating:

- $366B total future commitments
- $279B supply/capacity commitments
- $108.5B maximum gross guarantee exposure
- concentrated accounts receivable and extended customer payment terms
- $36B AI-cloud commitments
- higher ecosystem capital-allocation complexity
- the proposed ~$11.9B Hugging Face acquisition plus retention program
- explicit custom-silicon competition and China export-control risk

The counterweight is still exceptional current cash generation, high gross margins, a broad developer ecosystem, and effective disclosure/internal controls.

## Falsifiers

1. FCF conversion weakens while AR, commitments and guarantees keep rising.
2. Custom silicon materially erodes platform economics.
3. Owner FCF/share misses the revised Base path for two fiscal years.

## Reproducibility

Workflow: `.github/workflows/nvda-filings-rerun.yml`

Successful GitHub Actions run: 35327284480

Runner metadata:
- provider: OpenAI
- model: GPT-5.6 Sol
- reasoning effort: high

The complete generated run was also preserved as a GitHub Actions artifact named:
`NVDA-harness-filing-first-rerun-2026-09-18`.
