# Digest — AVGO (as of 2026-09-18)
score 64.25 (ex-val None, Starter / Watch) · DI None · TQ None · archetype non_fit — No eligible archetype: see failed/missing conditions and vetoes · veto PENDING_REVIEW · state INCOMPLETE
signals {'price_to_base_value': 0.8841, 'valuation_percentile_5y': None, 'revenue_cagr_next_3y': 0.4381, 'market_cap_usd': 1707097776022.65} · reachable(raw) ['compounder', 'growth']
veto codes: V1 경영진 정직성 또는 회계 신뢰성 훼손 / V2 구조적으로 과도한 외부자본 조달 의존 / V3 장기간 지속되는 과도한 희석 / V4 고객가치 없이 마케팅·보조금에 의존하는 성장 / V5 증분 ROIC의 구조적 붕괴 / V6 해자의 지속적인 축소 / V7 현재가격이 비현실적인 Bull Case 이상을 요구 / V8 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성 / V9 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## expectation_valuation — 64.25 (raw 64.25, spread 60.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| EV | 64.25 (25–85) | 0.78 | neutral | V7=cleared | At the frozen $357.61 close, the locked-policy DCF produces Bear/Base/Bull values of about $137/$404/$798. Price/Base is 0.884, so current price does not requi… |
bull: AI custom accelerators, networking and VMware cash flows scale together. Bull owner FCF/share rises from $9.5 to $57 over ten years; locked 25x terminal gives … / bear: AI accelerator demand normalizes after the current buildout, large customers internalize more silicon, and customer/TSMC concentration reduces bargaining power…
unknowns: Individual revenue shares, contract economics and cancellation/volume-flex terms for the … · How much of the $179.2B RPO is custom AI silicon versus software, and its recognition/mar…

## Archetype fit
{"buffett_value": {"eligible": false, "fit_score": 7.99901961, "failed_conditions": ["signal.price_to_base_value"], "missing_conditions": ["criterion.reinvestment_fcf.fcf_per_share_quality", "domain.financial_survival", "domain.management_allocation", "domain.moat_trajectory", "domain.asymmetry"], "blocking_vetoes": []}, "compounder": {"eligible": false, "fit_score": 15.9265625, "failed_conditions": [], "missing_conditions": ["domain.moat_trajectory", "domain.reinvestment_fcf", "domain.management_allocation", "domain.financial_survival", "criterion.reinvestment_fcf.incremental_roic", "criterion.reinvestment_fcf.reinvestment_runway"], "blocking_vetoes": []}, "growth": {"eligible": false, "fit_score": 20.36942149, "failed_conditions": ["gate_score"], "missing_conditions": ["domain.structural_leadership", "domain.customer_product", "domain.moat_trajectory", "domain.reinvestment_fcf", "domain.management_allocation", "domain.financial_survival", "domain.asymmetry", "criterion.reinvestment_fcf.fcf_per_share_quality"], "blocking_vetoes": []}, "moonshot": {"eligible": false, "fit_score": 0.0, "failed_conditions": ["signal.market_cap_usd"], "missing_conditions": ["domain.disruptive_innovation", "domain.structural_leadership", "domain.asymmetry", "domain.financial_survival", "gate_score"], "blocking_vetoes": []}}
## Provider calibration
{"mode": "shadow", "applied": true, "decision_effect": false, "family": "openai", "base_offset": 5.0, "max_abs_offset": 5.0, "per_domain_offset": {"expectation_valuation": -1.67}, "basis": {"sample": "NVDA 2026-09-17/18, 동일 종가 $219.34, criterion 27개 대조", "n": 27, "measured_mean_gap": 10.2, "measured_sd": 6.9, "direction": "27개 전부 gpt-5.6-sol >= Claude Opus 5. 노이즈가 아니라 계통 편향.", "caveat": "표본은 종목 1개다. 다른 종목의 쌍 실행이 쌓이면 base_offset을 재추정해야 한다. harness.py calibrate로 측정한다."}, "reason": null}
## Evidence concentration (review only)
[]
## Macro / geopolitical transmission
{"financial_regime": {}, "geopolitical_regime": {}, "company_transmission": {}, "missing_or_stale_components": ["credit_liquidity", "financial_conditions", "geopolitical_events", "structural_trade"], "reanalysis_requests": [], "pending_reanalysis_domains": [], "risk_budget_multiplier": 0.5, "purchase_pacing_multiplier": 0.5, "monitoring_urgency": "high", "fundamental_score_effect": 0}
