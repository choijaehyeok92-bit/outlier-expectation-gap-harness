# Digest — NU (as of 2026-09-21)

> Reconstructed v3.3 full-core output. The bank-specific RF adaptation is explicit because the industrial capex/OCF observable is not economically valid for a regulated bank.

score **78.69** (ex-valuation **80.57**, Emerging Outlier) · archetype **compounder** · veto **PENDING_REVIEW** · state **WATCH**

position pre-IC: **0% until veto cleared**

## Core scorecard

| Domain | Score |
|---|---:|
| SL — Structural Leadership | **86.25** |
| CP — Customer / Product | **88.75** |
| MT — Moat Trajectory | **85.00** |
| RF — Reinvestment / FCF | **82.00** |
| MA — Management / Allocation | **79.00** |
| FS — Financial Survival | **73.75** |
| EV — Expectation / Valuation | **68.00** |
| AS — Asymmetry | **63.50** |
| DI — Disruptive Innovation | **86.75** |

## Archetype result

**Compounder is eligible** and is the only reachable archetype.

It clears:
- price/Base **0.7558 <= 1.2**
- MT **85 >= 76**
- RF **82 >= 76**
- MA **79 >= 72**
- FS **73.75 >= 72**
- EV **68 >= 42**
- incremental ROIC **85 >= 75**
- reinvestment runway **75 >= 70**

Compounder deterministic fit score: **81.6**.

Growth and Outlier Growth remain excluded because AS is **63.5 < 65**. Buffett Value misses FS/AS despite the attractive valuation.

## Why RF passes

For a bank, industrial FCF is not a valid owner-economics measure. The RF report therefore uses regulatory-equity economics:

- Q2 net income **$1.061B** and ROE **33%**, versus **$637M / 28%** in Q2 2025.
- Q2 equity increased from roughly **$9.575B to $13.252B** YoY.
- A rough annualized incremental-earnings / incremental-equity proxy is about **46%**.
- H1 net income was about **$1.933B** and buybacks **$500.4M**, leaving roughly **74%** of earnings retained before OCI/SBC effects.
- Q2 net-income-per-diluted-share proxy rose from about **$0.13 to $0.216** with negligible share dilution.

Because the standard capex+R&D/OCF runway formula is invalid for a bank, reinvestment runway is conservatively scored **75**, not mechanically 90.

## Management and capital allocation

Nu repurchased **40.66M shares for $500.4M**, or about **$12.31/share**. That is roughly **0.663x** the frozen Base value of $18.56, mapping capital allocation to **80**.

Governance is deliberately discounted: the dual-class structure gives founder David Vélez dominant voting control, so governance_integrity is only **70** despite strong execution and long-term equity compensation.

## Why state is still WATCH

The Compounder gates are satisfied, but the Hard Veto gate is still **PENDING_REVIEW** because RT has not performed its independent co-owner review. The global macro overlay is also missing/stale.

Therefore the deterministic state remains:

`WATCH — 0% until veto cleared`

## Next plan

`macro`: **MO**

After MO: **ED + RT**, then **IC** if no blocking issue emerges.
