# Digest — RBRK (as of 2026-09-18)
score 68.46 (ex-val 66.0, Starter / Watch) · DI 70.0 · TQ None · archetype non_fit — No eligible archetype: see failed/missing conditions and vetoes · veto PENDING_REVIEW · state INCOMPLETE
signals {'price_to_base_value': 0.6304, 'valuation_percentile_5y': None, 'revenue_cagr_next_3y': 0.26, 'market_cap_usd': 22121456045.43} · reachable(raw) ['outlier_growth']
veto codes: V1 경영진 정직성 또는 회계 신뢰성 훼손 / V2 구조적으로 과도한 외부자본 조달 의존 / V3 장기간 지속되는 과도한 희석 / V4 고객가치 없이 마케팅·보조금에 의존하는 성장 / V5 증분 ROIC의 구조적 붕괴 / V6 해자의 지속적인 축소 / V7 현재가격이 비현실적인 Bull Case 이상을 요구 / V8 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성 / V9 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## financial_survival — 65.75 (raw 65.75, spread 45.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| FS | 65.75 (35–80) | 0.92 | support | V2=cleared, V3=cleared, V9=cleared | Liquidity is strong and refinancing risk is distant, but dilution materially lowers financial-survival quality. Cash plus short-term investments exceed convert… |
bull: RBRK has about $1.75B of cash and short-term investments, positive OCF/FCF, and 0% converts maturing in 2030. Near-term external financing is not required, lea… / bear: Dilution is the main financial risk. Outstanding shares rose about 5% y/y, H1 SBC was $174M, and convertibles add potential dilution. A valuation drawdown plus…
unknowns: Fully diluted economic share count after all RSUs, options, ESPP and convertible-note eff… · Normalized annual SBC after post-IPO award timing effects.

## expectation_valuation — 71.75 (raw 71.75, spread 70.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| EV | 71.75 (20–90) | 0.78 | support | V7=cleared | At the frozen $106.71 close, locked-policy DCF gives Bear/Base/Bull values near $31.58/$169.29/$563.05. Price/Base is 0.6304, but Base is fragile: roughly 81% … |
bull: Bull assumes cyber-resilience plus Agent Cloud create multiple durable growth vectors and owner FCF/share reaches $45 in year 10. Under the locked 25x terminal… / bear: Bear assumes ARR growth decelerates sharply, SBC remains economically heavy and operating leverage improves slowly. Owner FCF/share reaches only $3.50 in year …
unknowns: Normalized long-run SBC as a percent of revenue and the resulting diluted share count. · Agent Cloud revenue, margins, retention and customer-payback evidence are not separately …

## asymmetry — 66.25 (raw 66.25, spread 45.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| AS | 66.25 (40–85) | 0.82 | support | V7=cleared, V9=cleared | RBRK has genuine power-law upside but also severe valuation downside. Locked Bull/current is about 5.28x, while Bear/current is about 0.30x. Core cyber resilie… |
bull: A 5x path exists if core cyber-resilience ARR compounds, identity/cloud workloads broaden, Agent Cloud becomes a second platform, and SBC-adjusted owner FCF/sh… / bear: Bear value is only about 30% of price. Growth mean-reversion, heavy SBC/dilution, weaker Agent Cloud monetization or margin delay could destroy most of the val…
unknowns: Agent Cloud standalone ARR, gross margin and customer retention. · Normalized SBC/share dilution once post-IPO grants mature.

## disruptive_innovation — 70.0 (raw 70.0, spread 32.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| DI | 70 (50–82) | 0.84 | support | – | Rubrik shows real adoption and product expansion, but the evidence supports meaningful structural innovation rather than a proven 10x disruption. ARR, large-cu… |
bull: Rubrik is moving cyber recovery from backup administration toward autonomous data, identity and AI-agent resilience. Strong ARR expansion, >119% NRR and new Ag… / bear: The core product may remain a premium but sustaining cyber-resilience platform rather than a new value-chain standard. Agent Cloud adoption and economics are n…
unknowns: Standalone Agent Cloud ARR, customer count and gross margin. · Independent recovery-time/TCO benchmarks versus Cohesity, Veeam, hyperscaler-native tools…

## Archetype fit
{"buffett_value": {"eligible": false, "fit_score": 32.48627451, "failed_conditions": ["domain.financial_survival"], "missing_conditions": ["criterion.reinvestment_fcf.fcf_per_share_quality", "domain.management_allocation", "domain.moat_trajectory"], "blocking_vetoes": []}, "compounder": {"eligible": false, "fit_score": 26.40416667, "failed_conditions": ["domain.financial_survival"], "missing_conditions": ["domain.moat_trajectory", "domain.reinvestment_fcf", "domain.management_allocation", "criterion.reinvestment_fcf.incremental_roic", "criterion.reinvestment_fcf.reinvestment_runway"], "blocking_vetoes": []}, "growth": {"eligible": false, "fit_score": 32.88746556, "failed_conditions": ["domain.financial_survival"], "missing_conditions": ["domain.structural_leadership", "domain.customer_product", "domain.moat_trajectory", "domain.reinvestment_fcf", "domain.management_allocation", "criterion.reinvestment_fcf.fcf_per_share_quality"], "blocking_vetoes": []}, "moonshot": {"eligible": false, "fit_score": 55.97570879, "failed_conditions": ["domain.disruptive_innovation", "domain.asymmetry"], "missing_conditions": ["domain.structural_leadership"], "blocking_vetoes": []}, "outlier_growth": {"eligible": false, "fit_score": 25.28846154, "failed_conditions": [], "missing_conditions": ["domain.long_term_growth", "criterion.long_term_growth.opportunity_scale_5y", "criterion.long_term_growth.growth_duration_10y", "criterion.long_term_growth.culture_adaptability", "criterion.long_term_growth.market_misperception", "domain.customer_product", "domain.moat_trajectory", "domain.management_allocation"], "blocking_vetoes": []}}
## Provider calibration
{"mode": "shadow", "applied": true, "decision_effect": false, "family": "openai", "base_offset": 5.0, "max_abs_offset": 5.0, "per_domain_offset": {"financial_survival": -3.33, "expectation_valuation": -1.67, "asymmetry": -1.67, "disruptive_innovation": -3.33}, "basis": {"sample": "NVDA 2026-09-17/18, 동일 종가 $219.34, criterion 27개 대조", "n": 27, "measured_mean_gap": 10.2, "measured_sd": 6.9, "direction": "27개 전부 gpt-5.6-sol >= Claude Opus 5. 노이즈가 아니라 계통 편향.", "caveat": "표본은 종목 1개다. 다른 종목의 쌍 실행이 쌓이면 base_offset을 재추정해야 한다. harness.py calibrate로 측정한다."}, "reason": null}
## Evidence concentration (review only)
[]
## Macro / geopolitical transmission
{"financial_regime": {}, "geopolitical_regime": {}, "company_transmission": {}, "missing_or_stale_components": ["credit_liquidity", "financial_conditions", "geopolitical_events", "structural_trade"], "reanalysis_requests": [], "pending_reanalysis_domains": [], "risk_budget_multiplier": 0.5, "purchase_pacing_multiplier": 0.5, "monitoring_urgency": "high", "fundamental_score_effect": 0}
