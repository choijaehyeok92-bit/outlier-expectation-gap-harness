# Digest — NU (as of 2026-09-21)

> Reconstructed v3.3 EV-stage output. The current connected execution environment cannot replay the local EDGAR/CLI subprocess, so deterministic Stage 0, validation and valuation arithmetic are reproduced without claiming a literal CLI run.

score **68.0** (ex-val None, Starter / Watch) · archetype **non_fit** · veto **PENDING_REVIEW** · state **INCOMPLETE**

signals: price/Base **0.7558x** · forward revenue CAGR **20%** · market cap **$68.81B** · reachable(raw) **['buffett_value', 'compounder', 'growth', 'outlier_growth']**

## Stage 0

NU is a foreign private issuer, so the pack uses 20-F annual reports and quarter/YTD-bearing 6-K interim statements.

- latest annual: PASS
- latest interim: PASS
- trailing interim series: PASS **7/6**
- historical annuals: PASS **3/3**
- foreign-issuer filing coverage: PASS
- earnings release / investor materials: PASS
- pack invariant errors: **0**
- advisory gaps: proxy compensation, insider ownership

## Bank-specific valuation convention

Conventional industrial-company net cash is not used. Customer deposits, securities, cash and wholesale funding are operating balance-sheet items for a bank, so frozen **net_cash_per_share = $0.00**.

The locked `owner_fcf_per_share` field is interpreted as a **distributable owner-earnings/share proxy after required capital retention**, not literal industrial FCF.

## Expectation / Valuation — 68.0

| Agent | Score | Bear–Bull | Confidence | Verdict |
|---|---:|---:|---:|---|
| EV | **68.0** | 45–85 | 0.80 | support |

Locked valuation at the frozen **$14.03** price:

- Bear: **$4.76**
- Base: **$18.56**
- Bull: **$34.85**
- Price/Base: **0.7558x**

Subscores:
- reverse DCF burden: **75**
- Base return: **70**
- valuation robustness: **55**

The price-above-Bull Hard Veto is **cleared**.

## Current operating picture

Q2 2026 shows strong scale and profitability: roughly **139M customers**, accounting revenue of **$5.51B**, net income of **$1.06B**, and **33% ROE**. The credit portfolio was **$39.4B** against **$45.3B deposits**. The main valuation uncertainty is not demand growth but how much of high reported earnings can ultimately be distributed after retaining capital for growth and credit risk.

## Next plan

`triage`: **AS, DI, FS**

The 68.0 score is an EV-only partial score, not a final investment state. Universal triage and Hard Veto ownership remain incomplete.
