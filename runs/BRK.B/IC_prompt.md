# 과제: BRK.B / 기준일 2026-09-18 / investment_committee (IC)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/BRK.B/reports/IC.json, runs/BRK.B/one_page_investment_record.md. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"BRK.B","company_name":"Berkshire Hathaway Inc.","as_of_date":"2026-09-18","currency":"USD","current_price":509.77,"shares_diluted":2155918015,"market_cap_usd":1091269818773,"enterprise_value":775369818773,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["SEC Form 10-Q for quarter ended 2026-06-30, filed 2026-08-10","SEC Q2 2026 earnings release filed 2026-08-10","SEC Form 10-Q for quarter ended 2026-03-31, filed 2026-05-04","SEC 2026 DEF 14A filed 2026-03-13","SEC Form 10-K for year ended 2025","StockAnalysis BRK.B historical close: 2026-09-18 $509.77","FinanceCharts BRK.B P/B: 1.47 vs 5Y average 1.49 on 2026-09-18"],"special_questions":["Does Berkshire's very large cash/T-bill balance signal a structural reinvestment constraint?","Can Greg Abel sustain Buffett-era capital allocation discipline after becoming CEO on 2026-01-01?","At $509.77, is the margin of safety sufficient after normalizing investment gains and insurance cash-flow noise?"],"intake_facts":["2026 H1 operating earnings $24.329B vs $20.801B in 2025 H1; Q2 operating earnings $12.983B.","2026-06-30 Insurance & Other cash/cash equivalents/U.S. Treasury Bills $359.2B; borrowings excluding BHE/BNSF $43.3B.","2026 H1 operating cash flow $21.7B; capex $10.6B.","2026 H1 repurchases about $4.8B, mostly Q2.","Insurance float about $177.5B at 2026-06-30.","OxyChem acquired 2026-01-02 for about $9.4B; Taylor Morrison acquired 2026-07-24 for about $6.8B equity value.","BRK.B 2026-09-18 close $509.77; P/B 1.47 vs 5Y average 1.49."],"net_cash_per_share":147.5679,"valuation_percentile_5y":0.5,"valuation_metric":"Price/book 1.47 on 2026-09-18 versus 5-year average 1.49; percentile set to neutral 0.50 because mean alone does not establish an exact percentile.","valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{}}

## 검증된 1차 자료 사실
# BRK.B verified source bundle — as of 2026-09-18

## Primary filings
- SEC 10-Q, quarter ended 2026-06-30, filed 2026-08-10: https://www.sec.gov/Archives/edgar/data/1067983/000119312526341032/brka-20260630.htm
  - H1 operating cash flow $21.7B; capex $10.6B.
  - Insurance & Other cash/cash equivalents/U.S. Treasury Bills $359.2B.
  - Borrowings excluding BHE/BNSF $43.3B; BNSF debt $23.5B; BHE borrowings $61.8B.
  - H1 share repurchases about $4.8B.
  - OxyChem acquired for about $9.4B; Taylor Morrison completed 2026-07-24 for about $6.8B equity value.
- SEC Q2 earnings release: https://www.sec.gov/Archives/edgar/data/1067983/000119312526344495/d159922dex991.htm
  - Q2 operating earnings $12.983B; H1 $24.329B vs $20.801B prior year.
  - H1 underwriting $3.448B; insurance investment income $5.738B; BNSF $2.935B; BHE $2.005B; manufacturing/service/retail $7.669B.
  - Insurance float about $177.5B at 2026-06-30.
- SEC 10-Q, quarter ended 2026-03-31, filed 2026-05-04: https://www.sec.gov/Archives/edgar/data/1067983/000119312526202243/brka-20260331.htm
- SEC 2025 10-K: https://www.sec.gov/Archives/edgar/data/1067983/000119312526083899/brka-20251231.htm
- SEC 2026 DEF 14A, filed 2026-03-13: https://www.sec.gov/Archives/edgar/data/1067983/000119312526106253/d882687ddef14a.htm
  - Gregory Abel became CEO 2026-01-01; Warren Buffett remained Chairman as of the cutoff.

## Market data fixed at cutoff
- StockAnalysis BRK.B history: https://stockanalysis.com/stocks/brk.b/history/
  - 2026-09-18 close $509.77.
- FinanceCharts P/B: https://www.financecharts.com/stocks/BRK.B/value/price-to-book-value-averages
  - P/B 1.47; 5-year average P/B 1.49.

## Frozen modeling conventions
- Current B-equivalent share count from 2026 Q2 filing cover (2026-07-29): 488,450 A + 1,408,035,161 B = 2,140,710,161 B-equivalent.
- market_cap_usd = $509.77 × 2,140,710,161 ≈ $1.0913T.
- net_cash_per_share = (Insurance & Other cash/T-bills $359.2B - Insurance & Other borrowings $43.3B) / 2,140,710,161 ≈ $147.57.
- Equity securities and BNSF/BHE operating debt are excluded from net_cash_per_share; their economics remain in operating/owner earnings.
- EV owner-FCF paths use normalized operating earnings as a proxy, explicitly flagged as model uncertainty.

## 입력
runs/BRK.B/digest.md와 runs/BRK.B/aggregate.json (없으면 `python harness.py aggregate BRK.B` 후 `digest BRK.B` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 IC (chair)
# Investment Committee Chair — v3

- `agent_id`: `IC`
- `domain`: `investment_committee`

## 임무와 입력
aggregate.json과 digest.md의 증거·유형별 fit·veto·가치평가·지정학 전이를 검토한다.
새 기업 분석이나 숫자 덮어쓰기를 하지 않는다. 선택할 투자 유형은 compounder,
growth(성장주), outlier_growth(장기 아웃라이어 성장주), buffett_value(버핏 스타일 가치주), moonshot뿐이다. non_fit은 관망/거절 시스템 상태다.
Expectation Gap은 모든 유형의 가치평가 개념이다. TQ는 활성화되었을 때 정상화 진단이다.

## Devil's Advocate
- Compounder: 해자 정체/축소, 증분 ROIC 악화, 재투자 활주로 고갈, 과도한 매수가.
- Buffett Value: 가치 함정, 과대 정상화 이익, 영구 쇠퇴, 숨은 레버리지, 회계/정직성,
  부실 자본배분, terminal multiple에 기대는 가짜 할인. 낮은 배수만으로 통과시키지 않는다.
- Growth: 성장 둔화, 주당 현금창출 부재, 취약한 고객가치, 성숙한 해자로의 발전 실패, 높은 가격.
- Moonshot: 채택 실패, 취약한 단위경제, 증거를 대신하는 TAM/서사, 희석, Bull+를 요구하는 가격.
- evidence_concentration_flags가 독립 근거처럼 보이는 하나의 경제 요인을 드러내는지 검토한다.

## 판정
primary는 적격 유형의 결정론적 최고 fit이며 secondary는 별도 기록한다. config 조건·동률 규칙을 따른다.
미해소/확정 Hard Veto, 누락 reviewer, 미완료 핵심 coverage나 구조적 재분석을 매수로 넘기지 않는다.
어느 유형도 도달 가능하지 않으면 IC를 실행하지 않고 deterministic early_exit_record로 종료한다.
금융·지정학은 위험예산·속도·모니터링이며 회사 점수 조정 근거가 아니다.

## 출력
reports/IC.json에 선택 ic_state와 가장 강한 반론·근거를 기록한다. 새 매수 상태는
STARTER/NORMAL/HIGH_CONVICTION/CORE_WINNER/EXCEPTIONAL_WINNER 중 config cap 이하만 가능하다.
WATCH/REJECT 또는 기존 포지션 검토 상태로 보수적으로 낮출 수 있다. 요청이 게이트를 넘으면
하네스가 거부하고 ic_review_flags를 남긴다. 유형별 비중 상한도 유지한다.
one_page_investment_record.md를 작성한 뒤 aggregate를 다시 실행하여 final_verdict.json을 생성한다.
final_verdict.json을 직접 편집해 게이트를 우회하지 않는다.

## 장기 아웃라이어 성장(outlier_growth) Devil's Advocate
이 유형이 primary 또는 secondary로 올라오면 다음 반론을 **먼저** 구성한 뒤 판정한다.

1. 5년 기회 규모가 과장됐다 — 배수의 근거가 점유율 가정에 기대고 있지 않은가.
2. 10년 지속기간이 증거가 아니라 서사다 — 무엇이 관측됐고 무엇이 희망인가.
3. 문화가 규모를 견디지 못한다 — 적응력의 증거가 소규모 시절의 것 아닌가.
4. 고객가치가 일시적이다 — 보조금·전환기 수요·일회성 계약이 아닌가.
5. 5배 경로가 영웅적 마진·점유율을 요구한다 — 분해했을 때 무엇이 비현실적인가.
6. 기대오류가 실제 오류가 아니다 — 시장이 이미 같은 것을 반영하고 있지 않은가.
7. 현재 가격이 이미 장기 지속기간 논지를 반영하고 있다.
8. **누락 위험(omission risk)** 은 고려하되 Hard Veto를 무효화할 수 없다.

결론에 **"비싸지만 지속기간이 과소평가됨"** 과 **"Bull+가 이미 반영돼 비쌈"** 중 어느 쪽인지 명시한다.

포지션은 영구 소액 상한을 두지 않는다. 신규 진입은 보통 STARTER 또는 NORMAL이며, 확대는 검증된 기회 규모·해자 강화·고객가치 증거·수익률 궤적·경영진 실행에 비례한다. **주가 상승 자체는 증거가 아니다.** 전역 IC state 밴드와 최대 ~10% 상한은 그대로 구속한다.


## 쉬운 최종 보고서
plain_language에 business, opportunity, risk, decision_reason을 각각 쉬운 한국어 1~3문장으로 작성한다. 원보고서의 근거만 사용하고 사실·추정·판단을 구분한다. 숫자를 새로 생성하지 않는다. 영어 약어를 풀어 쓰고 초보 독자에게 회사의 사업, 기회, 손실 가능성, 현재 결론의 이유를 설명한다. 최종 결과와 계산표는 하네스가 easy_report.md에 자동 반영한다.

## Executable v3 archetype policy
{"min_gate_score": 60, "fallback": "non_fit", "buy_state_cap_for_fallback": "STARTER_OR_WATCH", "types": [{"id": "compounder", "label": "컴파운더", "label_en": "Compounder", "description": "넓어지는 해자, 높은 증분 ROIC와 재투자 여력으로 장기 복리를 창출하는 능력이 뛰어난 기업.", "valuation_tolerant": false, "conditions": [{"field": "signal.price_to_base_value", "op": "<=", "value": 1.2}, {"field": "domain.moat_trajectory", "op": ">=", "value": 76}, {"field": "domain.reinvestment_fcf", "op": ">=", "value": 76}, {"field": "domain.management_allocation", "op": ">=", "value": 72}, {"field": "domain.financial_survival", "op": ">=", "value": 72}, {"field": "domain.expectation_valuation", "op": ">=", "value": 42}, {"field": "criterion.reinvestment_fcf.incremental_roic", "op": ">=", "value": 75}, {"field": "criterion.reinvestment_fcf.reinvestment_runway", "op": ">=", "value": 70, "note": "관측표가 band_centre 보간을 쓰므로 70은 도달 가능한 값이다(흡수율 약 31.67% 이상). 보간 도입 전에는 표 격자가 [50,65,80,90]뿐이라 70이 존재하지 않았고 실질 기준이 80(흡수율 35%)이었다."}], "position_guidance": "장기 보유가 기본이다. 밸류에이션 과열 시 매도보다 추가매수 속도를 조절한다.", "blocked_vetoes": ["경영진 정직성 또는 회계 신뢰성 훼손", "구조적으로 과도한 외부자본 조달 의존", "장기간 지속되는 과도한 희석", "고객가치 없이 마케팅·보조금에 의존하는 성장", "증분 ROIC의 구조적 붕괴", "해자의 지속적인 축소", "현재가격이 비현실적인 Bull Case 이상을 요구", "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음"], "fit_axes": [{"field": "domain.moat_trajectory", "weight": 0.3}, {"field": "criterion.reinvestment_fcf.incremental_roic", "weight": 0.3}, {"field": "criterion.reinvestment_fcf.reinvestment_runway", "weight": 0.25}, {"field": "domain.management_allocation", "weight": 0.15}]}, {"id": "outlier_growth", "label": "장기 아웃라이어 성장주", "label_en": "Long-Term Outlier Growth", "description": "5~10년 이상의 장기 성장 규모와 지속기간, 강화되는 경쟁우위, 적응력 있는 조직문화, 현실적인 5배 가치 경로와 구체적인 시장 기대오류를 중심으로 평가하는 장기 아웃라이어 성장형 기업. 단기 성장률이 높다는 이유만으로는 적격이 아니며, 밸류에이션 관용적이되 맹목적이지 않다 — 결정론적 가치평가 완료, EV 최소 품질, Bear/Base/Bull 분석과 Bull 초과 가격 Hard Veto가 모두 유지된다.", "valuation_tolerant": true, "min_gate_score": 65, "position_cap": null, "position_guidance": "영구 소액 상한을 두지 않는다. 신규 진입은 보통 STARTER 또는 NORMAL에서 시작하고, 확대는 증거 증가에 비례한다 — 검증된 기회 규모, 해자 강화, 고객가치 증거, 수익률 궤적, 경영진 실행이 그 증거다. 주가 상승 자체는 증거가 아니다. 전역 IC state 밴드와 최대 ~10% 상한은 그대로 구속한다.", "blocked_vetoes": ["경영진 정직성 또는 회계 신뢰성 훼손", "구조적으로 과도한 외부자본 조달 의존", "장기간 지속되는 과도한 희석", "고객가치 없이 마케팅·보조금에 의존하는 성장", "증분 ROIC의 구조적 붕괴", "해자의 지속적인 축소", "현재가격이 비현실적인 Bull Case 이상을 요구", "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음"], "conditions": [{"field": "domain.long_term_growth", "op": ">=", "value": 70}, {"field": "criterion.long_term_growth.opportunity_scale_5y", "op": ">=", "value": 75}, {"field": "criterion.long_term_growth.growth_duration_10y", "op": ">=", "value": 65}, {"field": "criterion.long_term_growth.culture_adaptability", "op": ">=", "value": 65}, {"field": "criterion.long_term_growth.market_misperception", "op": ">=", "value": 65}, {"field": "domain.customer_product", "op": ">=", "value": 65}, {"field": "domain.moat_trajectory", "op": ">=", "value": 65}, {"field": "domain.management_allocation", "op": ">=", "value": 65}, {"field": "domain.financial_survival", "op": ">=", "value": 60}, {"field": "domain.asymmetry", "op": ">=", "value": 65}, {"field": "criterion.asymmetry.upside_path", "op": ">=", "value": 75}, {"field": "criterion.asymmetry.permanent_loss", "op": ">=", "value": 50}, {"field": "domain.expectation_valuation", "op": ">=", "value": 40}], "fit_axes": [{"field": "domain.long_term_growth", "weight": 0.35}, {"field": "domain.moat_trajectory", "weight": 0.2}, {"field": "domain.customer_product", "weight": 0.15}, {"field": "criterion.asymmetry.upside_path", "weight": 0.2}, {"field": "domain.management_allocation", "weight": 0.1}]}, {"id": "growth", "label": "성장주", "label_en": "Growth", "description": "고객가치와 현금창출이 확인되고 빠른 확장을 이어가는 기업. 컴파운더 수준의 재투자·해자 성숙도에 도달하기 전 단계도 평가한다. 성장률만으로 적격 판정을 내리지 않는다.", "valuation_tolerant": false, "min_gate_score": 65, "conditions": [{"field": "signal.revenue_cagr_next_3y", "op": ">=", "value": 0.15}, {"field": "signal.price_to_base_value", "op": "<=", "value": 1.1}, {"field": "domain.structural_leadership", "op": ">=", "value": 70}, {"field": "domain.customer_product", "op": ">=", "value": 70}, {"field": "domain.moat_trajectory", "op": ">=", "value": 65}, {"field": "domain.reinvestment_fcf", "op": ">=", "value": 65}, {"field": "domain.management_allocation", "op": ">=", "value": 65}, {"field": "domain.financial_survival", "op": ">=", "value": 70}, {"field": "domain.asymmetry", "op": ">=", "value": 65}, {"field": "domain.expectation_valuation", "op": ">=", "value": 50}, {"field": "criterion.reinvestment_fcf.fcf_per_share_quality", "op": ">=", "value": 65}], "position_cap": "1-3% (성장주 초기 상한)", "position_guidance": "추정 매출 성장의 실현, 주당 현금창출과 해자 강화를 분기마다 검증한다. 가격·Hard Veto 게이트를 면제하지 않는다.", "blocked_vetoes": ["경영진 정직성 또는 회계 신뢰성 훼손", "구조적으로 과도한 외부자본 조달 의존", "장기간 지속되는 과도한 희석", "고객가치 없이 마케팅·보조금에 의존하는 성장", "증분 ROIC의 구조적 붕괴", "해자의 지속적인 축소", "현재가격이 비현실적인 Bull Case 이상을 요구", "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음"], "calibration_status": "초기 정책값. 특정 기업에 맞춘 보정이나 사후 수익률 검증을 거친 기준이 아니며 별도 백테스트가 필요하다.", "fit_axes": [{"field": "signal.revenue_cagr_next_3y", "weight": 0.2, "normalization": {"kind": "linear", "min": 0.1, "max": 0.3, "direction": "higher"}}, {"field": "domain.customer_product", "weight": 0.25}, {"field": "domain.structural_leadership", "weight": 0.2}, {"field": "domain.reinvestment_fcf", "weight": 0.2}, {"field": "domain.moat_trajectory", "weight": 0.15}]}, {"id": "buffett_value", "label": "버핏 스타일 가치주", "label_en": "Buffett-style Value", "valuation_tolerant": false, "description": "예측 가능한 경제성, 정상화 owner earnings, 보수적 재무, 합리적 자본배분과 안전마진. 낮은 멀티플만으로는 적합하지 않다.", "conditions": [{"field": "signal.price_to_base_value", "op": "<=", "value": 0.85}, {"field": "criterion.reinvestment_fcf.fcf_per_share_quality", "op": ">=", "value": 75}, {"field": "domain.financial_survival", "op": ">=", "value": 75}, {"field": "domain.management_allocation", "op": ">=", "value": 70}, {"field": "domain.moat_trajectory", "op": ">=", "value": 60}, {"field": "domain.asymmetry", "op": ">=", "value": 65}], "position_guidance": "정상화 FCF, 유지보수 투자, 회계 신뢰성, 숨은 레버리지, 자본배분과 영구 쇠퇴를 검증한다. 큰 재투자 활주로는 요구하지 않는다.", "blocked_vetoes": ["경영진 정직성 또는 회계 신뢰성 훼손", "구조적으로 과도한 외부자본 조달 의존", "장기간 지속되는 과도한 희석", "고객가치 없이 마케팅·보조금에 의존하는 성장", "증분 ROIC의 구조적 붕괴", "해자의 지속적인 축소", "현재가격이 비현실적인 Bull Case 이상을 요구", "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음"], "fit_axes": [{"field": "criterion.reinvestment_fcf.fcf_per_share_quality", "weight": 0.3}, {"field": "domain.financial_survival", "weight": 0.25}, {"field": "domain.management_allocation", "weight": 0.2}, {"field": "domain.moat_trajectory", "weight": 0.15}, {"field": "domain.asymmetry", "weight": 0.1}]}, {"id": "moonshot", "label": "문샷형", "label_en": "Moonshot", "description": "산업을 재편하는 파괴적 혁신과 검증 가능한 채택곡선. 시가총액 상한은 conditions의 실행값을 따른다.", "valuation_tolerant": true, "conditions": [{"field": "signal.market_cap_usd", "op": "<=", "value": 50000000000}, {"field": "domain.disruptive_innovation", "op": ">=", "value": 78}, {"field": "domain.structural_leadership", "op": ">=", "value": 72}, {"field": "domain.asymmetry", "op": ">=", "value": 72}, {"field": "domain.financial_survival", "op": ">=", "value": 60}], "position_cap": "1-3% (문샷 초기 상한 — 채택·단위경제 증거 증가 시 IC 승인으로 단계 확대)", "position_guidance": "시가총액 상한은 conditions 참조. 고밸류에이션은 용인하되 Bull+ Hard Veto는 면제하지 않는다. 채택·단위경제 증거에 비례해 확대한다.", "blocked_vetoes": ["경영진 정직성 또는 회계 신뢰성 훼손", "구조적으로 과도한 외부자본 조달 의존", "장기간 지속되는 과도한 희석", "고객가치 없이 마케팅·보조금에 의존하는 성장", "증분 ROIC의 구조적 붕괴", "해자의 지속적인 축소", "현재가격이 비현실적인 Bull Case 이상을 요구", "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음"], "fit_axes": [{"field": "domain.disruptive_innovation", "weight": 0.4}, {"field": "domain.asymmetry", "weight": 0.25}, {"field": "domain.structural_leadership", "weight": 0.2}, {"field": "domain.financial_survival", "weight": 0.15}]}], "fallback_metadata": {"id": "non_fit", "label": "관망·회피형", "label_en": "Non-fit / Avoid", "description": "Hard Veto, 게이트 미달 또는 네 투자 유형에 부적합한 시스템 상태.", "conditions": [], "position_guidance": "유형 적합성이 확인되기 전까지 신규 비중 확대 금지."}, "fit_policy": {"method": "weighted_fit_axes", "tie_tolerance": 1e-06, "tie_breaker": ["compounder", "outlier_growth", "growth", "buffett_value", "moonshot"], "note": "Eligibility conditions are mandatory gates. Ranking among eligible archetypes uses fit_axes only, so the number of gates an archetype declares cannot give it extra votes. Score fields normalize as value/100; other fields declare an explicit normalization. A missing axis contributes zero to fit and never relaxes a gate."}}
aggregate generates final_verdict.json deterministically. Write IC.json and then rerun aggregate; never override missing veto ownership or noneligible archetypes.

## 공통 규칙
## 분석
- 기준일을 먼저 선언한다. 기준일 이후 정보는 사용하지 않는다.
- 최소 3개의 독립 근거를 확보하고, 가능한 한 1차 자료를 우선한다.
- 근거와 반대근거를 모두 제시한다.
- `사실 / 추정 / 해석`을 구분한다.
- 자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면, 예산 내에서 웹 검색·IR 자료·신뢰 가능한 2차 자료로 **먼저 보완을 시도한다**.
- 보완 시도 후에도 확보하지 못한 것만 `unknowns`에 남기고, 무엇을 어디서 찾으려 했는지 함께 적는다.
- 2차 자료로 채운 값은 `fact_or_estimate`를 `estimate` 또는 `interpretation`으로 표기하고 `EVIDENCE_POLICY.md`의 출처 위계를 지킨다.
- 결론보다 먼저 반증조건을 작성한다.

## 관점 분리 (점수 도메인과 독립 평가축)
에이전트는 항목당 하나지만, 지침의 Bull·Verifier·Skeptic 관점을 **각각 끝까지 밀어붙인 뒤** 결론을 낸다. 합의를 먼저 정하고 관점을 끼워 맞추지 않는다.
- `bull_case` / `bear_case`: Bull 논리와 Skeptic 논리를 각각 300자 이내로 쓴다.
- `bull_score` / `bear_score`: 각 논리가 맞을 때의 도메인 점수. `bear_score ≤ score_0_100 ≤ bull_score`.
- `subscores`: `config/calibration.json`의 criterion을 정확히 한 번씩 5점 단위로 채점한다. 이 값이 점수의 원천이다.
- `score_0_100`: subscores의 고정 가중평균과 같아야 하며 하네스가 검증한다.
- `bull_score` / `bear_score`: 시나리오 범위와 논쟁 폭을 보여주는 메타데이터다. 단일 모델의 자체 범위가 넓다는 이유만으로 자동 감점하지 않는다.
- `bull_score - bear_score`가 20 이상이면 재검토 표시를 남기되 수치 점수와 분리한다.

## 토큰 예산
- `company_context.json`의 기준 정보와 `sources/README.md`의 검증된 사실은 다시 검색하지 않는다. 오류를 발견했을 때만 근거와 함께 지적한다.
- 웹 검색·페치는 `config/workflow.json`의 `research_budget` 이내로 쓴다(기본 에이전트당 15회). 예산은 위 공백 보완에 우선 배정한다.
- 공시 원문(.txt)은 통째로 읽지 않는다. `sources/INDEX.md`의 줄번호로 grep하거나 부분만 읽는다.
- Phase 3·IC 에이전트는 다른 에이전트의 원 보고서 대신 `digest.md`를 읽는다. 원 보고서는 특정 주장을 검증할 때만 그 파일 하나를 연다.
- 보고서 분량은 `report_limits`를 지킨다(thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개, falsifiers·key_kpis·next_checks 각 3개). `unknowns`에는 핵심 가설에 직결되는 것만 쓴다.
- `config/calibration.json`에서 자신에게 배정된 Hard Veto는 반드시 `cleared / conditional / confirmed` 중 하나로 명시한다. 미기재는 clear가 아니다.
- 작성 후 `python harness.py validate <TICKER> <AGENT_ID>`로 검증한다. 스키마 파일을 직접 읽지 않아도 된다.

## 재현성
- agent 실행 전 `python harness.py freeze TICKER --provider ... --model ...`로 company_context와 sources를 해시 고정한다.
- freeze 이후 입력이 바뀌면 prompt 생성을 중단한다. 모델 비교는 동일 `input_snapshot_sha256`에서만 유효하다.
- EV는 고정된 할인율·terminal multiple·현재가격·순현금을 사용하며 LLM은 연도별 owner FCF/share 경로만 제안한다.

## v3 분석 계약
새 evidence에는 가능하면 안정적인 evidence_id와 공유 economic_driver를 기록한다. 동일 사실을 여러 긍정 도메인에 재사용한 evidence_concentration_flags는 ED/RT/IC 검토용이며 자동 감점하지 않는다. Macro/지정학은 점수를 바꾸지 않고 pacing·위험예산·모니터링 또는 회사 근거를 통한 재분석 요청만 만든다.

## Hard Veto (정확한 문자열 사용)
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 장기간 지속되는 과도한 희석
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## Hard Veto 판정 기준
Hard Veto는 "중대한 리스크"가 아니라 "이 문장이 실제로 성립하는가"로 판정한다. 문구의 모든 구성요건이 충족될 때만 성립하며, 하나라도 반증되면 cleared다. 우려는 스코어·uncertainties·모니터링으로 보내고 veto로 올리지 않는다.
도메인 점수에 이미 온전히 반영된 사실만으로는 veto를 세우지 않는다. veto는 그 자체의 구성요건이 독립적으로 충족될 때만 성립한다(anchor_policy의 중복 감점 금지를 veto 층에 확장).
{
  "status_rule": {
    "confirmed": "구성요건 전부가 1차 자료로 확인됨",
    "conditional": "구성요건 전부가 충족될 가능성이 높으나 결정적 자료 1개가 미확보. 해소 조건을 반드시 명시한다",
    "candidate": "평가하지 않았거나 판단 근거가 전혀 없음",
    "cleared": "구성요건 중 최소 하나가 증거로 반증됨"
  },
  "definitions": {
    "경영진 정직성 또는 회계 신뢰성 훼손": {
      "elements": [
        "정직성 또는 회계 신뢰성이 훼손된 사건이 발생했을 것"
      ],
      "cleared_if": [
        "재작성·감사인 이견/교체·내부통제 중대결함·미공시 관련자거래가 모두 부재"
      ],
      "not_covered": "공격적이지만 GAAP을 준수하는 평가(Level 3 등)는 감시항목이지 훼손의 증거가 아니다. 이익 품질은 RF·EV 점수가 반영한다."
    },
    "구조적으로 과도한 외부자본 조달 의존": {
      "elements": [
        "영업활동이 자체적으로 자금을 조달하지 못할 것",
        "그 결과 외부자본 조달이 구조적으로 반복될 것"
      ],
      "cleared_if": [
        "영업현금흐름이 필수지출을 상회",
        "조달이 생존용이 아니라 재량적 자본배분(자사주·투자)을 위한 것"
      ],
      "not_covered": "차입 자체가 아니라 차입 없이 사업이 성립하지 않는 구조가 요건이다."
    },
    "장기간 지속되는 과도한 희석": {
      "elements": [
        "희석이 장기간 지속될 것",
        "그 폭이 과도할 것"
      ],
      "cleared_if": [
        "희석주식수가 보합 또는 감소",
        "자사주 매입이 SBC를 상쇄"
      ],
      "not_covered": "SBC 존재 자체는 요건이 아니다."
    },
    "고객가치 없이 마케팅·보조금에 의존하는 성장": {
      "elements": [
        "고객가치가 부재할 것(필수 요건)",
        "성장이 마케팅·보조금에 의존할 것"
      ],
      "cleared_if": [
        "높은 gross margin과 낮은 판관비 비율이 동시에 관측되어 고객이 프로모션 없이 지불함을 보임",
        "고객 선수금·대기 수요 등 지불의사의 직접 증거"
      ],
      "not_covered": "벤더 금융(공급자가 고객의 구매자금을 지분투자·대출·보증으로 대는 구조)은 이 문구가 포괄하지 않는다. 고객가치 부재라는 필수 요건과 별개 사안이므로 veto가 아니라 CP unit_economics·FS dilution_offbalance·AS permanent_loss 점수와 key_kpis·uncertainties로 처리한다. out_of_scope_concerns 참조."
    },
    "증분 ROIC의 구조적 붕괴": {
      "elements": [
        "증분 ROIC가 자본비용 아래로 내려갔을 것",
        "그것이 일시적이 아니라 구조적일 것"
      ],
      "cleared_if": [
        "증분 ROIC가 자본비용을 크게 상회"
      ],
      "not_covered": "높은 수준에서의 하락(체감)은 붕괴가 아니다."
    },
    "해자의 지속적인 축소": {
      "elements": [
        "해자 지표가 실제로 축소 중일 것",
        "그 축소가 지속적일 것"
      ],
      "cleared_if": [
        "gross margin·점유율·전환비용 등 관측 지표가 유지 또는 강화"
      ],
      "not_covered": "미래의 대체 위협은 MT 점수와 모니터링 대상이지 현재 축소의 증거가 아니다."
    },
    "현재가격이 비현실적인 Bull Case 이상을 요구": {
      "elements": [
        "현재가가 Bull 시나리오 가치를 초과할 것"
      ],
      "cleared_if": [
        "price_to_base_value가 Bull/현재가 배수 안에 있음"
      ],
      "not_covered": "Base가 야심적이라는 판단은 EV 점수가 반영한다."
    },
    "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성": {
      "elements": [
        "단일 제품·고객·규제에 대한 종속이 있을 것",
        "그 종속이 치명적일 것 — 해당 요인 상실 시 사업 경제성이 회복 불가하게 훼손될 것"
      ],
      "cleared_if": [
        "해당 리스크가 실제로 현실화됐음에도 매출·이익이 유지되거나 성장한 이력"
      ],
      "watch_trigger": [
        "단일 고객이 매출의 25%를 초과",
        "제2의 관할에서 판매 제한이 발생",
        "아직 스트레스 테스트되지 않은 종속 축(고객 집중 등)은 cleared로 두되 이 임계값을 모니터링한다"
      ],
      "not_covered": "높은 집중도 자체는 요건이 아니다. SL의 durability_risks가 반영한다."
    },
    "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음": {
      "elements": [
        "파산 또는 사업가치의 영구적 소멸 확률이 유의미할 것",
        "그 확률이 기대수익에 비해 과도할 것"
      ],
      "definition": "여기서 영구손실은 사업가치의 영구적 소멸을 뜻하며, 매수가 대비 가격 하락(valuation drawdown)은 포함하지 않는다. 가격 위험은 EV와 AS 점수가 이미 온전히 반영하므로 여기서 다시 세우면 중복이다.",
      "cleared_if": [
        "순현금이고 영업현금흐름이 차입을 상회하여 파산 확률이 사실상 0",
        "Bear 시나리오에서도 사업이 유의미한 owner FCF를 창출"
      ],
      "not_covered": "Bear 주당가치가 현재가를 크게 밑도는 것은 가격 위험이며 AS의 permanent_loss 점수가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "ic_state": "WATCH"}
작성 후 `python harness.py validate BRK.B IC`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
