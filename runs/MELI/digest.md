# Digest — MELI (as of 2026-09-21)

> Reconstructed v3.3 triage output. Deterministic policy arithmetic is mirrored because the current connector environment cannot replay the repository CLI directly.

score **62.93** (ex-valuation **68.50**, Starter / Watch) · archetype **non_fit** · veto **PENDING_REVIEW** · state **INCOMPLETE**

signals: price/Base **0.9197x** · forward revenue CAGR **22%** · market cap **$92.29B** · reachable(raw) **['compounder']**

## Universal triage

| Agent | Domain | Score | Bear–Bull | Result |
|---|---|---:|---:|---|
| EV | Expectation / Valuation | 55.50 | 35–80 | neutral |
| AS | Asymmetry | 58.25 | 35–85 | neutral |
| DI | Disruptive Innovation | 86.75 | 70–95 | support |
| FS | Financial Survival | 78.75 | 60–90 | support |

## What changed after triage

**Compounder remains reachable.** It already clears:
- price/Base 0.9197 <= 1.2
- FS 78.75 >= 72
- EV 55.5 >= 42

It still needs MT >=76, RF >=76, MA >=72, incremental ROIC >=75 and reinvestment runway >=70.

**Growth** is no longer reachable because AS **58.25 < 65**.  
**Outlier Growth** fails AS **58.25 < 65** and permanent_loss **25 < 50**.  
**Buffett Value** fails price/Base and AS.  
**Moonshot** fails market-cap and AS gates.

## Asymmetry

Locked DCF: Bear **$138.09**, Base **$1,979.43**, Bull **$4,719.69** versus price **$1,820.47**.

- Bull/current = **2.59x** with 3+ monetized paths -> upside_path **90**
- Bear/current = **0.076x**, no net-cash modifier -> permanent_loss **25**
- probability_calibration **60**
- weighted AS = **58.25**

MELI therefore has large upside optionality but also unusually wide permanent-value dispersion.

## Disruptive innovation

Q2 fintech MAUs reached **88M**, unique active buyers **89M**, and ecosystemic users grew **37% YoY**. Ecosystemic marketplace users generated **70% more GMV per user** than marketplace-only users. Credit exceeded **$16B** and advertising revenue grew **73% in USD**. The limiting issue is economic quality: credit-card NIMAL was **-2.5%**. citeturn663693view1turn455895search0

## Financial survival

At June 30, MELI reported **$13.176B total debt**, **$6.751B available liquidity** and **$6.425B net debt**. H1 adjusted FCF remained positive at **$158M** despite rapid credit investment. Diluted weighted-average shares were essentially unchanged YoY. citeturn651267view1turn651267view0turn335697view3

FS-owned Hard Vetoes are cleared. Dilution watch is **normal**.

## Next plan

`domain_analysis`:
- **SL** — Structural Leadership
- **CP** — Customer / Product
- **MT** — Moat Trajectory
- **RF** — Reinvestment / FCF
- **MA** — Management / Allocation

The key Compounder gate is likely to be RF: current ecosystem growth is strong, but the harness still needs evidence that incremental returns and owner FCF/share justify the current investment intensity.
