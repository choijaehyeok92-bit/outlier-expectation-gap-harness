# Digest — LLY (as of 2026-09-21)

> Reconstructed v3.3 triage output. Deterministic policy arithmetic is mirrored because the current connector environment cannot replay the repository CLI/EDGAR subprocess directly.

score **64.46** (ex-valuation **70.25**, Starter / Watch) · archetype **non_fit** · veto **PENDING_REVIEW** · state **INCOMPLETE**

signals: price/Base **0.9081x** · forward revenue CAGR **24%** · market cap **$1.041T** · reachable(raw) **['compounder']**

## Universal triage

| Agent | Domain | Score | Bear–Bull | Result |
|---|---|---:|---:|---|
| EV | Expectation / Valuation | **56.75** | 35–80 | neutral |
| AS | Asymmetry | **61.75** | 40–80 | neutral |
| DI | Disruptive Innovation | **82.00** | 65–95 | support |
| FS | Financial Survival | **78.75** | 60–90 | support |

## Reachability after triage

**Compounder remains reachable.**

It already clears:
- price/Base **0.9081 <= 1.2**
- FS **78.75 >= 72**
- EV **56.75 >= 42**

It still requires MT >=76, RF >=76, MA >=72, incremental ROIC >=75 and reinvestment runway >=70.

**Growth** fails because AS **61.75 < 65**.  
**Outlier Growth** also fails AS **61.75 < 65**.  
**Buffett Value** fails price/Base **0.9081 > 0.85** and AS **61.75 < 65**.  
**Moonshot** fails market cap and AS gates.

## Asymmetry

Locked Bear/Base/Bull values are **$345.26 / $1,282.74 / $2,016.84** versus price **$1,164.89**.

- Bull/current ≈ **1.73x** -> upside_path **75**
- Bear/current ≈ **0.30x** -> permanent_loss **50**
- probability calibration **60**
- weighted AS = **61.75**

The business has several growth paths, but the starting market capitalization and low Bear/current ratio keep risk-adjusted asymmetry below the Growth/Outlier threshold.

## Disruptive innovation

The metabolic franchise is already at mainstream scale. Q2 Mounjaro and Zepbound revenue totaled **$14.871B**. Orforglipron was FDA-approved and launched for obesity, while retatrutide Phase 3 obesity and type 2 diabetes trials met primary endpoints.

DI scores **82.0**: the clinical/adoption shift is substantial, but competing pharmaceutical companies are well capitalized and reimbursement can constrain value capture.

## Financial survival

At June 30, Lilly had **$8.95B cash + $3.856B investments**, **$54.908B total debt**, and **$10.1B unused committed bank facilities**.

Estimated TTM operating cash flow is about **$28.08B**. H1 OCF was **$16.023B** against **$5.259B capex**.

Q2 diluted shares fell about **0.68% YoY**, and H1 repurchases were about **$4.0B**. Identified off-balance commitments are well below 0.5x estimated TTM revenue.

## Next plan

`domain_analysis`
- **SL** — Structural Leadership
- **CP** — Customer / Product
- **MT** — Moat Trajectory
- **RF** — Reinvestment / FCF
- **MA** — Management / Allocation

For LLY, RF is likely to be the binding domain: manufacturing capex, recurring acquired IPR&D, acquisitions and owner-FCF/share normalization must be evaluated together rather than treating pipeline investment as one-time noise.
