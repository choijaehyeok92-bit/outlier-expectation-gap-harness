# Digest — NU (as of 2026-09-21)

> Reconstructed v3.3 triage output. Deterministic policy arithmetic is mirrored because the current connector environment cannot replay the repository CLI/EDGAR subprocess directly.

score **68.36** (ex-valuation **68.63**, Starter / Watch) · archetype **non_fit** · veto **PENDING_REVIEW** · state **INCOMPLETE**

signals: price/Base **0.7558x** · forward revenue CAGR **20%** · market cap **$68.81B** · reachable(raw) **['compounder']**

## Universal triage

| Agent | Domain | Score | Bear–Bull | Result |
|---|---|---:|---:|---|
| EV | Expectation / Valuation | **68.00** | 45–85 | support |
| AS | Asymmetry | **63.50** | 40–85 | neutral |
| DI | Disruptive Innovation | **86.75** | 70–95 | support |
| FS | Financial Survival | **73.75** | 55–90 | support |

## Reachability after triage

**Compounder remains reachable.** It already clears:
- price/Base **0.7558 <= 1.2**
- FS **73.75 >= 72**
- EV **68 >= 42**

It still requires MT >=76, RF >=76, MA >=72, incremental ROIC >=75 and reinvestment runway >=70.

**Growth** fails because AS **63.5 < 65**.  
**Outlier Growth** also fails AS **63.5 < 65**.  
**Buffett Value** fails FS **73.75 < 75** and AS **63.5 < 65**, despite the attractive price/Base.  
**Moonshot** fails market cap and AS gates.

## Asymmetry

Locked Bear/Base/Bull values are **$4.76 / $18.56 / $34.85** versus price **$14.03**.

- Bull/current ≈ **2.48x** -> upside_path **75**
- Bear/current ≈ **0.34x** -> permanent_loss **55**
- probability calibration **60**
- weighted AS = **63.5**

NU therefore has substantial upside but not enough risk-adjusted asymmetry to clear the 65 Growth/Outlier floor.

## Disruptive innovation

NU's 2025 monthly cost to serve was about **$0.8 per active customer** while the platform served 131M customers. By Q2 2026 customers reached roughly **139M** and activity was **83.5%**. Deposits reached **$45.3B** and the product suite now spans cards, deposits, lending, investments, SMEs and premium banking. This supports mainstream adoption and a structural digital-cost advantage. citeturn839760search0turn839760search1

## Financial survival

At June 30, Brazil CET1 was **11.9%**, Tier 1 **13.4%**, CAR **15.7%**, and excess capital margin **$1.848B**. Mexico and Colombia capital ratios were **14.9%** and **15.3%**, each above 10.5% local minimums. citeturn478742view0turn478742view1

Nu also held substantial liquid assets and funded 87% of its primary funding base through retail deposits/bank receipts. The mechanical drag is **$38.2B of unused credit limits**, roughly 1.97x estimated TTM revenue. Q2 diluted shares increased only ~0.10% YoY, so dilution itself is normal. citeturn478742view3turn631495view0turn631495view2

## Next plan

`domain_analysis`:
- **SL** — Structural Leadership
- **CP** — Customer / Product
- **MT** — Moat Trajectory
- **RF** — Reinvestment / FCF
- **MA** — Management / Allocation

For NU, RF must be interpreted through bank economics: incremental ROE, capital absorption, per-share distributable earnings, credit losses and capital requirements rather than industrial FCF.
