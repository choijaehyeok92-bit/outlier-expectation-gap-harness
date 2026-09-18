# 과제: MELI / 기준일 2026-09-17 / red_team (RT)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/MELI/reports/RT.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"MELI","company_name":"MercadoLibre, Inc.","as_of_date":"2026-09-17","currency":"USD","current_price":1825.21,"shares_diluted":50696802,"market_cap_usd":92532309978.42,"enterprise_value":98957309978.42,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded MercadoLibre FY2025 Form 10-K filed 2026-02-25","User-uploaded MercadoLibre Q1 2026 Form 10-Q filed 2026-05-08","User-uploaded MercadoLibre Q2 2026 Form 10-Q filed 2026-08-06","User-uploaded MercadoLibre Form 8-K filed 2026-09-14","MELI 2026-09-17 closing price $1,825.21 verified from historical market data"],"special_questions":["Can commerce, payments and credit growth re-accelerate owner FCF/share after the 2026 free-shipping and credit-investment margin reset?","Is Mercado Pago funding dependence normal financial working capital or a structural external-capital vulnerability?","Does credit growth remain attractive after NIMAL compression and higher past-due balances?"],"net_cash_per_share":-126.7338,"valuation_metric":"No reproducible 5-year valuation percentile frozen; current valuation is assessed through the deterministic owner-FCF/share DCF.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# MELI frozen source bundle — as of 2026-09-17

Primary company evidence comes from the four user-uploaded SEC filing documents. Only information available on or before 2026-09-17 is used.

## Source lineage
- FY2025 Form 10-K filed 2026-02-25 — SHA256 75c6936bfed518c912dd353459ecbe80f40df7363148159e558768611a8100c0
- Q1 2026 Form 10-Q filed 2026-05-08 — SHA256 d668f539e901fe36c5f6709ec0cb659f79a2a3aa93aca7fb91e11acfd4a97e49
- Q2 2026 Form 10-Q filed 2026-08-06 — SHA256 a70dab4e5ac1dc64a7863cfef8b97cb08f946f7ea11e8f8137daee0cde5b9e0b
- Form 8-K filed 2026-09-14 — SHA256 a93dae7066ae62af6585fc460d7664fab675f0521ecf571dfd387fb10e1d9a0c

## Frozen market/model inputs
- 2026-09-17 close: **$1,825.21**.
- Q2 2026 shares outstanding: **50.696802M**.
- Market capitalization at frozen price: **~$92.53B**.
- Company-defined Q2 2026 net debt: **$6.425B**.
- Frozen net_cash_per_share: **-$126.7338**.
- The 2026-09-14 $1.0B 5.85% notes issuance adds debt and cash simultaneously at closing, so it does not by itself change net debt before proceeds are deployed.
- Deterministic valuation policy: 9% required return, 10-year horizon, 15x/20x/25x Bear/Base/Bull terminal multiples.
- valuation_percentile_5y is intentionally left null because no reproducible full 5-year distribution was frozen.

## FY2025 Form 10-K
- Net revenues and financial income **$28.893B** vs $20.777B in 2024 and $15.107B in 2023.
- Gross profit **$12.858B**; income from operations **$3.201B**; net income **$1.997B**.
- CFO **$12.116B**.
- Company-defined Adjusted free cash flow **$1.481B**, versus $1.215B in 2024 and $1.439B in 2023. On ~50.7M shares this is roughly **$29.2/share** in 2025.
- Available cash, investments and digital assets at year-end **$6.710B**.
- Net debt **$4.682B**.
- Fintech MAU **78M** vs 61M in 2024; unique active buyers **121M** vs 100M.
- GMV **$65.037B** vs $51.467B; TPV **$277.823B** vs $196.660B.
- Total payment transactions **15.470B** vs 11.355B.
- NIMAL **22.4%**, down from 28.2% in 2024 and 36.2% in 2023.
- Capex **$1.327B**; product and technology development expense **$2.269B**.
- 2025 revenue mix: Brazil 52.6%, Mexico 22.4%, Argentina 20.6%, other 4.4%.
- Mercado Pago and lending are funded through receivable sales, securitizations, credit lines, local debt instruments and an $800M revolver; management treats Fintech financing liabilities as working capital in Adjusted FCF.

## Q1 2026 Form 10-Q
- Revenue **$8.845B** vs $5.935B (+49%).
- Operating income **$611M** vs $763M; net income **$417M** vs $494M.
- Adjusted FCF **-$56M** vs +$58M.
- Fintech MAU **83M** vs 64M; unique active buyers **84M** vs 67M.
- GMV **$18.951B** vs $13.330B; TPV **$87.186B** vs $58.303B.
- NIMAL **17.8%** vs 22.7%.
- Net debt **$5.748B**.

## Q2 / H1 2026 Form 10-Q
- H1 revenue **$19.014B** vs $12.725B (+49.4%); Q2 revenue **$10.169B** vs $6.790B (~+49.8%).
- H1 net income **$883M** vs $1.017B; H1 operating margin **6.8%** vs 12.5%. Q2 operating margin **6.7%** vs 12.2%.
- Margin compression is attributed mainly to the lower free-shipping threshold in Brazil, higher shipping costs, cost of goods and higher doubtful-account provisions from credit-card expansion.
- H1 CFO **$5.737B** vs $3.948B.
- H1 Adjusted FCF **$158M** vs $512M.
- Q2 Fintech MAU **88M** vs 68M; Q2 unique active buyers **89M** vs 71M.
- H1 GMV **$40.877B** vs $28.588B; Q2 GMV **$21.926B** vs $15.258B.
- H1 TPV **$188.138B** vs $122.905B; Q2 TPV **$100.952B** vs $64.602B.
- H1 payment transactions **9.821B** vs 6.951B.
- H1 NIMAL **19.4%** vs 22.8%; Q2 NIMAL **20.7%** vs 23.0%.
- Gross loans receivable **$16.375B**; allowance **$4.379B**; total past due **$4.638B**. At 2025 year-end gross loans were $12.508B and total past due $3.295B.
- Off-balance-sheet unused credit-card commitments **$14.047B** vs $9.001B at 2025 year-end.
- No single customer represented more than 5% of revenue.
- Total debt **$13.176B**; company-defined liquid assets for net-debt calculation **$6.751B**; net debt **$6.425B**.
- New uncommenced warehouse leases total **$2.254B**; remaining Gol logistics-service commitment **$272M**.
- Shares outstanding **50.696802M**, essentially unchanged year over year.

## Form 8-K filed 2026-09-14
- MercadoLibre closed a **$1.0B** underwritten public offering of **5.850% Notes due 2036**.
- The notes are guaranteed by major operating subsidiaries across Argentina, Brazil, Mexico, Chile and Colombia.

공시 원문: runs/MELI/sources/*.txt — runs/MELI/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 입력
runs/MELI/digest.md (없으면 `python harness.py aggregate MELI` 후 `digest MELI` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 RT (red_team)
# Red Team

- `agent_id`: `RT`
- `domain`: `red_team`

## 임무
Bull case의 가장 약한 고리를 네 가지 렌즈로 공격하고, 하나의 일관된 공매도 논리로 묶는다. Red Team 결과는 점수에 더하지 않고 Hard Veto와 IC 반론의 증거로만 쓴다.

## 렌즈별 질문
**포렌식 회계**
1. 현금흐름과 손익의 괴리는? 조정 이익·FCF가 경제적 비용을 제외하는가?
2. 매출인식·자본화·충당금·투자손익에 공격적 가정이 있는가? 감사·내부통제·재작성 이슈는?

**공매도 논리**
3. 시장이 낙관적으로 오해하는 핵심과 가장 취약한 가정(TAM·점유율·마진)은? 주가 60~80% 하락을 설명할 현실적 시나리오는?

**기술 대체**
4. 대체기술의 비용곡선은 얼마나 빨리 개선되며, 고객 전환비용이 기술전환 앞에서 실제 방어벽이 되는가? 기존 수익원이 자기잠식될 위험은?

**규제·집중**
5. 매출·이익·공급자·지역의 집중도와 단일 이벤트 리스크(규제승인·수출통제·반독점)는? 대체경로와 완충장치가 있는가?

마지막으로 공매도 논리를 반증할 증거를 적는다.

## 입력
`digest.md`와 공시 원문(색인 기준 부분 읽기).

## Hard Veto 중점
- 경영진 정직성 또는 회계 신뢰성 훼손
- 해자의 지속적인 축소
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 그 밖에 증거가 확인한 모든 Veto

`confirmed`는 증거가 결정적일 때만 쓴다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성

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
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "경영진 정직성 또는 회계 신뢰성 훼손", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "구조적으로 과도한 외부자본 조달 의존", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "고객가치 없이 마케팅·보조금에 의존하는 성장", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "증분 ROIC의 구조적 붕괴", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "해자의 지속적인 축소", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate MELI RT`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
