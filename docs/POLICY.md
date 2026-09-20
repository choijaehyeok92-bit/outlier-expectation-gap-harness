# Executable v3.3 policy

Generated from config; update with `python harness.py policy --out docs/POLICY.md`.

Strategy / schema / decision policy: 3.3 / 3.3 / 3.3.

## compounder — Compounder

### Eligibility conditions

| Field | Operator | Threshold |
|---|---|---:|
| `signal.price_to_base_value` | <= | 1.2 |
| `domain.moat_trajectory` | >= | 76 |
| `domain.reinvestment_fcf` | >= | 76 |
| `domain.management_allocation` | >= | 72 |
| `domain.financial_survival` | >= | 72 |
| `domain.expectation_valuation` | >= | 42 |
| `criterion.reinvestment_fcf.incremental_roic` | >= | 75 |
| `criterion.reinvestment_fcf.reinvestment_runway` | >= | 70 |

### Fit axes

| Field | Weight | Normalization |
|---|---:|---|
| `domain.moat_trajectory` | 0.3 | `{"kind": "score_100"}` |
| `criterion.reinvestment_fcf.incremental_roic` | 0.3 | `{"kind": "score_100"}` |
| `criterion.reinvestment_fcf.reinvestment_runway` | 0.25 | `{"kind": "score_100"}` |
| `domain.management_allocation` | 0.15 | `{"kind": "score_100"}` |

Gate: core >= 60.

## outlier_growth — Long-Term Outlier Growth

### Eligibility conditions

| Field | Operator | Threshold |
|---|---|---:|
| `domain.long_term_growth` | >= | 70 |
| `criterion.long_term_growth.opportunity_scale_5y` | >= | 75 |
| `criterion.long_term_growth.growth_duration_10y` | >= | 65 |
| `criterion.long_term_growth.culture_adaptability` | >= | 65 |
| `criterion.long_term_growth.market_misperception` | >= | 65 |
| `domain.customer_product` | >= | 65 |
| `domain.moat_trajectory` | >= | 65 |
| `domain.management_allocation` | >= | 65 |
| `domain.financial_survival` | >= | 60 |
| `domain.asymmetry` | >= | 65 |
| `criterion.asymmetry.upside_path` | >= | 75 |
| `criterion.asymmetry.permanent_loss` | >= | 50 |
| `domain.expectation_valuation` | >= | 40 |

### Fit axes

| Field | Weight | Normalization |
|---|---:|---|
| `domain.long_term_growth` | 0.35 | `{"kind": "score_100"}` |
| `domain.moat_trajectory` | 0.2 | `{"kind": "score_100"}` |
| `domain.customer_product` | 0.15 | `{"kind": "score_100"}` |
| `criterion.asymmetry.upside_path` | 0.2 | `{"kind": "score_100"}` |
| `domain.management_allocation` | 0.1 | `{"kind": "score_100"}` |

Gate: core excluding EV >= 65.

## growth — Growth

### Eligibility conditions

| Field | Operator | Threshold |
|---|---|---:|
| `signal.revenue_cagr_next_3y` | >= | 0.15 |
| `signal.price_to_base_value` | <= | 1.1 |
| `domain.structural_leadership` | >= | 70 |
| `domain.customer_product` | >= | 70 |
| `domain.moat_trajectory` | >= | 65 |
| `domain.reinvestment_fcf` | >= | 65 |
| `domain.management_allocation` | >= | 65 |
| `domain.financial_survival` | >= | 70 |
| `domain.asymmetry` | >= | 65 |
| `domain.expectation_valuation` | >= | 50 |
| `criterion.reinvestment_fcf.fcf_per_share_quality` | >= | 65 |

### Fit axes

| Field | Weight | Normalization |
|---|---:|---|
| `signal.revenue_cagr_next_3y` | 0.2 | `{"direction": "higher", "kind": "linear", "max": 0.3, "min": 0.1}` |
| `domain.customer_product` | 0.25 | `{"kind": "score_100"}` |
| `domain.structural_leadership` | 0.2 | `{"kind": "score_100"}` |
| `domain.reinvestment_fcf` | 0.2 | `{"kind": "score_100"}` |
| `domain.moat_trajectory` | 0.15 | `{"kind": "score_100"}` |

Gate: core >= 65.

## buffett_value — Buffett-style Value

### Eligibility conditions

| Field | Operator | Threshold |
|---|---|---:|
| `signal.price_to_base_value` | <= | 0.85 |
| `criterion.reinvestment_fcf.fcf_per_share_quality` | >= | 75 |
| `domain.financial_survival` | >= | 75 |
| `domain.management_allocation` | >= | 70 |
| `domain.moat_trajectory` | >= | 60 |
| `domain.asymmetry` | >= | 65 |

### Fit axes

| Field | Weight | Normalization |
|---|---:|---|
| `criterion.reinvestment_fcf.fcf_per_share_quality` | 0.3 | `{"kind": "score_100"}` |
| `domain.financial_survival` | 0.25 | `{"kind": "score_100"}` |
| `domain.management_allocation` | 0.2 | `{"kind": "score_100"}` |
| `domain.moat_trajectory` | 0.15 | `{"kind": "score_100"}` |
| `domain.asymmetry` | 0.1 | `{"kind": "score_100"}` |

Gate: core >= 60.

## moonshot — Moonshot

### Eligibility conditions

| Field | Operator | Threshold |
|---|---|---:|
| `signal.market_cap_usd` | <= | 50000000000 |
| `domain.disruptive_innovation` | >= | 78 |
| `domain.structural_leadership` | >= | 72 |
| `domain.asymmetry` | >= | 72 |
| `domain.financial_survival` | >= | 60 |

### Fit axes

| Field | Weight | Normalization |
|---|---:|---|
| `domain.disruptive_innovation` | 0.4 | `{"kind": "score_100"}` |
| `domain.asymmetry` | 0.25 | `{"kind": "score_100"}` |
| `domain.structural_leadership` | 0.2 | `{"kind": "score_100"}` |
| `domain.financial_survival` | 0.15 | `{"kind": "score_100"}` |

Gate: core excluding EV >= 60.

## Fit and selection

Eligibility conditions are mandatory gates. Ranking among eligible archetypes uses fit_axes only, so the number of gates an archetype declares cannot give it extra votes. Score fields normalize as value/100; other fields declare an explicit normalization. A missing axis contributes zero to fit and never relaxes a gate.
Tie tolerance: 1e-06; tie priority: compounder > outlier_growth > growth > buffett_value > moonshot.

All listed veto blockers remain binding; ownership coverage is required before buying.

Provider calibration mode: **shadow**.

## Research budget

- Active-question cap: 24
- Monitoring cap: 12
- Optional cap: 4
- Non-blocking per-domain cap: 4
- Decision-blocking questions are never removed by these caps.

## Valuation sanity

- Yearly scenario crossing mode: review
- Terminal-value review threshold: 0.8
- Terminal-value high threshold: 0.9
- Sanity REVIEW flags do not auto-confirm a Hard Veto.

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

## Bull/bear dispersion

도메인별 bull/bear 폭의 하방 치우침을 포지션에만 반영한다. 점수·유형판정·Hard Veto에는 영향이 없다. 상방 치우침은 포지션을 넓히지 않는다 — 원칙 8(포지션 확대는 증거 증가에 비례)에 따라 축소 방향으로만 작동한다. 축소는 never_below_state에서 멈춘다 — 거부는 점수·Hard Veto의 몫이고 분산이 대신 내릴 판정이 아니다.

Metric: scored 도메인 전체에 대한 skew = (score - bear_score) - (bull_score - score) 의 평균. 양수면 하방 폭이 더 넓다는 뜻이다.

| Mean skew at least | Label | Position bands removed |
|---:|---|---:|
| 12.0 | severe_downside_skew | 2 |
| 6.0 | downside_skew | 1 |
| (any) | balanced_or_upside_skew | 0 |

The spread never changes a score, an archetype or a veto, and never widens a position.

## Observable anchor interpolation

Continuous single-metric tables interpolate between rows; counts and gated tables stay stepped.

| Criterion | Mode | Reachable scores (5-point grid) |
|---|---|---|
| `asymmetry.upside_path` | none | 30, 50, 60, 75, 90 |
| `asymmetry.permanent_loss` | band_centre | 25, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90 |
| `disruptive_innovation.optionality_incumbent_response` | none | 30, 50, 70, 85 |
| `financial_survival.dilution_offbalance` | none | 30, 55, 70, 90 |
| `long_term_growth.opportunity_scale_5y` | band_centre | 25, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90 |
| `long_term_growth.growth_duration_10y` | band_centre | 25, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90 |
| `management_allocation.capital_allocation` | band_centre | 30, 40, 45, 50, 55, 60, 65, 70, 75, 80 |
| `moat_trajectory.network_data_ecosystem` | none | 25, 55, 75, 85, 90 |
| `reinvestment_fcf.reinvestment_runway` | band_centre | 50, 60, 65, 70, 75, 80, 85, 90 |
| `structural_leadership.durability_risks` | none | 45, 60, 75, 85 |
