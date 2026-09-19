# Executable v3 policy

Generated from config; update with `python harness.py policy --out docs/POLICY.md`.

Strategy / schema / decision policy: 3.0 / 3.0 / 3.0.

## compounder — Compounder

| Field | Operator | Threshold | Fit weight |
|---|---|---:|---:|
| `signal.price_to_base_value` | <= | 1.2 | 1.0 |
| `domain.moat_trajectory` | >= | 76 | 1.0 |
| `domain.reinvestment_fcf` | >= | 76 | 1.0 |
| `domain.management_allocation` | >= | 72 | 1.0 |
| `domain.financial_survival` | >= | 72 | 1.0 |
| `domain.expectation_valuation` | >= | 42 | 1.0 |
| `criterion.reinvestment_fcf.incremental_roic` | >= | 75 | 1.0 |
| `criterion.reinvestment_fcf.reinvestment_runway` | >= | 70 | 1.0 |

Gate: core >= 60.

## buffett_value — Buffett-style Value

| Field | Operator | Threshold | Fit weight |
|---|---|---:|---:|
| `signal.price_to_base_value` | <= | 0.85 | 1.0 |
| `criterion.reinvestment_fcf.fcf_per_share_quality` | >= | 75 | 1.0 |
| `domain.financial_survival` | >= | 75 | 1.0 |
| `domain.management_allocation` | >= | 70 | 1.0 |
| `domain.moat_trajectory` | >= | 60 | 1.0 |
| `domain.asymmetry` | >= | 65 | 1.0 |

Gate: core >= 60.

## moonshot — Moonshot

| Field | Operator | Threshold | Fit weight |
|---|---|---:|---:|
| `signal.market_cap_usd` | <= | 50000000000 | 1.0 |
| `domain.disruptive_innovation` | >= | 78 | 1.0 |
| `domain.structural_leadership` | >= | 72 | 1.0 |
| `domain.asymmetry` | >= | 72 | 1.0 |
| `domain.financial_survival` | >= | 60 | 1.0 |

Gate: core excluding EV >= 60.

## Fit and selection

Score criteria use value/100; upper-bound signals use max(0, 1-value/(2*threshold)); missing contributes zero to fit only. Gates remain mandatory.
Tie tolerance: 1e-06; tie priority: compounder > buffett_value > moonshot.

All listed veto blockers remain binding; ownership coverage is required before buying.

Provider calibration mode: **shadow**.

## Component freshness

| Global component | TTL hours |
|---|---:|
| financial_conditions | 72 |
| credit_liquidity | 72 |
| geopolitical_events | 24 |
| structural_trade | 168 |

## State bands

| Minimum | Mechanical state | Position cap |
|---:|---|---|
| 86 | EXCEPTIONAL_WINNER_CANDIDATE | 6-10% (IC cap) |
| 80 | CORE_WINNER_CANDIDATE | 4-8% |
| 70 | NORMAL_CANDIDATE | 2-4% |
| 60 | STARTER_OR_WATCH | 0-2% |
| 0 | REJECT | 0% |
