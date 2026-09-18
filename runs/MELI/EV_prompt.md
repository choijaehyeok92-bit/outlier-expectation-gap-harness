# 과제: MELI / 기준일 2026-09-17 / expectation_valuation (EV)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/MELI/reports/EV.json. 그 외 파일은 수정하지 않는다.
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

## 독립성
runs/MELI/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 EV (domain_analyst)
# Expectation & Valuation Analyst

- `agent_id`: `EV`
- `domain`: `expectation_valuation`

## 임무
현재가격이 요구하는 장기 기대를 역산하고(Reverse DCF), Bear/Base/Bull을 작성해 기대수익 범위와 기대차를 계산한다. 낙관적 가정·터미널가치 의존·피크 이익을 스스로 공격한다.

## 관점별 질문
**Verifier — Reverse DCF**
1. 현재 EV/시총이 정당화되려면 매출 CAGR·마진·ROIC가 얼마여야 하는가? 그 기대는 역사·경쟁·산업구조 대비 어느 수준인가?
2. WACC·영구성장률 변화에 얼마나 민감한가? 현재가격이 Bull Case 이상을 요구하는가?

**Bull — 시나리오**
1. Bear/Base/Bull 각각의 성장·마진·멀티플 가정과 5~10년 연환산 수익률은?
2. Base에서 완벽한 실행 없이도 기대수익이 충분한가? Bull은 신규 성장축을 어떻게 반영하는가?

**Skeptic — 기대차 공격**
1. Base가 사실상 Bull인가? 점유율·마진·멀티플을 동시에 낙관적으로 두었는가?
2. 기대수익의 대부분이 terminal multiple에 의존하는가? 피크 사이클 이익이나 투자손익을 정상 이익으로 쓰지 않았는가?

## 종목 유형 신호 (`archetype_signals`)
- `price_to_base_value` = 현재가 / Base 주당가치
- `valuation_percentile_5y` = 핵심 멀티플의 자기 5년 이력 대비 백분위(0=최저). 어떤 멀티플을 썼는지 `evidence`에 남긴다.
- `revenue_cagr_next_3y` = Base 3년 매출 CAGR (0.12 = 12%)

추정할 수 없으면 `null`로 둔다. `bull_score`/`bear_score`와 함께 Base·Bull·Bear 주당가치를 `evidence`에 기록한다. 저밸류에이션이 구조적 쇠퇴(밸류 트랩)에서 온 것은 아닌지 `counterevidence`에 적는다.

## Hard Veto 중점
- 현재가격이 비현실적인 Bull Case 이상을 요구

## 고정 채점 루브릭
{
  "global_bands": [
    {
      "min": 0,
      "max": 19,
      "label": "failed",
      "rule": "핵심 가설이 반증되거나 경제적 가치가 구조적으로 훼손"
    },
    {
      "min": 20,
      "max": 39,
      "label": "weak",
      "rule": "반대근거가 우세하고 장기 투자근거가 취약"
    },
    {
      "min": 40,
      "max": 59,
      "label": "mixed",
      "rule": "긍정·부정 근거가 혼재하며 우위가 입증되지 않음"
    },
    {
      "min": 60,
      "max": 74,
      "label": "adequate",
      "rule": "가설은 성립하지만 중요한 검증 공백이 존재"
    },
    {
      "min": 75,
      "max": 84,
      "label": "strong",
      "rule": "다수의 1차 자료가 장기 가설을 지지"
    },
    {
      "min": 85,
      "max": 94,
      "label": "exceptional",
      "rule": "여러 기간·지표에서 일관된 강한 증거"
    },
    {
      "min": 95,
      "max": 100,
      "label": "rare",
      "rule": "압도적이고 반증 위험이 매우 낮음; 극히 드물게 사용"
    }
  ],
  "domain": {
    "criteria": [
      {
        "id": "reverse_dcf_burden",
        "weight": 0.35,
        "question": "현재가격 내재 기대 현실성",
        "anchors": {
          "25": "Bull 이상 필요",
          "50": "강한 실행 필요",
          "75": "Base로 충분",
          "90": "보수 실행에도 충분"
        },
        "signal_map": {
          "field": "signal.price_to_base_value",
          "bands": {
            "<=0.7": 90,
            "0.7~0.9": 75,
            "0.9~1.1": 60,
            "1.1~1.3": 45,
            ">1.3": 25
          }
        }
      },
      {
        "id": "base_return",
        "weight": 0.4,
        "question": "고정 DCF 정책의 Base 기대수익",
        "anchors": {
          "25": "큰 과대평가",
          "50": "공정가치 부근",
          "75": "의미 있는 할인",
          "90": "큰 기대차"
        },
        "signal_map": {
          "field": "signal.price_to_base_value",
          "bands": {
            "<=0.7": 85,
            "0.7~0.9": 70,
            "0.9~1.1": 55,
            "1.1~1.3": 40,
            ">1.3": 25
          }
        }
      },
      {
        "id": "valuation_robustness",
        "weight": 0.25,
        "question": "terminal/피크이익 의존도",
        "anchors": {
          "25": "매우 취약",
          "50": "민감도 큼",
          "75": "여러 가정에서 유지",
          "90": "보수 민감도에서도 유지"
        }
      }
    ],
    "scoring_rule": "reverse_dcf_burden과 base_return은 하네스가 산출한 price_to_base_value의 signal_map 값을 그대로 사용한다. 모델 재량은 valuation_robustness에만 적용한다. Base 시나리오의 야심 수준은 valuation_robustness와 uncertainties에 기록하되 위 두 criterion에서 다시 감점하지 않는다."
  },
  "anchor_policy": {
    "note": "프로바이더 간 점수 차이를 줄이기 위한 채점 규율. 모든 도메인 에이전트에 적용한다.",
    "rules": [
      "observable_anchors가 있는 criterion은 그 판정표를 우선 적용한다. 표와 다른 점수를 주려면 rationale에 표의 어느 행과 왜 다른지 적는다.",
      "anchors만 있는 criterion은 어느 앵커 구간을 선택했는지와 인접 구간을 배제한 이유를 rationale에 각각 한 문장으로 적는다.",
      "상단 게이트: 85 이상은 (가) 해당 criterion을 직접 뒷받침하는 1차 자료 근거가 3개 이상이고 (나) 가장 강한 반대근거를 명시적으로 반박했을 때만 부여한다.",
      "하단 게이트: 40 미만은 1차 자료로 확인된 반증 근거를 제시했을 때만 부여한다. 근거 없이 신중해서 낮추는 것은 금지하며 그 경우 40~55 구간에 둔다.",
      "같은 사실을 두 criterion에서 중복 감점하지 않는다. 한 곳에서만 반영하고 다른 곳에는 uncertainties로 남긴다.",
      "점수는 5점 단위를 유지한다.",
      "판정표 점수와 modifier 적용 결과는 반드시 5점 단위가 되도록 반올림한다.",
      "veto는 도메인 점수에 이미 반영된 사실만으로 세우지 않는다. veto_criteria의 구성요건이 독립적으로 충족될 때만 성립한다."
    ],
    "observed_divergence": "NVDA 2026-09-17/18 동일 종가 기준 gpt-5.6-sol 대 Claude Opus 5 실행 비교: criterion 27개 평균 격차 +10.2점(sol이 높음), 27개 전부 sol >= opus. 관측 가능한 사실형 criterion은 +3.1, 위험 가중 판단형은 +13.2로 4배 차이였다. 앵커가 형용사인 criterion에서만 갈라진다는 뜻이다."
  }
}
criterion은 5점 단위로 채점한다. score_0_100은 subscores 고정 가중평균과 같아야 한다. self-confidence와 bull/bear 폭은 자동 감점하지 않는다.
anchor_policy를 반드시 지킨다. observable_anchors가 있는 criterion은 판정표가 앵커 형용사보다 우선한다. 85 이상과 40 미만에는 각각 상단·하단 게이트가 걸려 있다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 현재가격이 비현실적인 Bull Case 이상을 요구

## 결정론적 밸류에이션
{
  "policy": {
    "method": "owner_fcf_per_share_dcf",
    "horizon_years": 10,
    "required_return": 0.09,
    "terminal_multiples": {
      "bear": 15,
      "base": 20,
      "bull": 25
    },
    "rules": [
      "할인율·terminal multiple은 모델이 선택하지 않는다.",
      "회사별 override는 company_context.json에 freeze 전에 기록한다.",
      "현재가격·순현금은 frozen company_context 값만 사용한다.",
      "LLM은 Bear/Base/Bull의 연도별 owner FCF/share 경로만 추정한다."
    ]
  },
  "locked_context": {
    "current_price": 1825.21,
    "net_cash_per_share": -126.7338,
    "valuation_percentile_5y": null,
    "valuation_overrides": {
      "required_return": null,
      "terminal_multiples": {
        "bear": null,
        "base": null,
        "bull": null
      }
    }
  }
}
Bear/Base/Bull owner_fcf_per_share를 각각 정확히 10개 연도로 작성한다. 할인 계산과 price_to_base_value는 하네스가 수행한다.

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
    "현재가격이 비현실적인 Bull Case 이상을 요구": {
      "elements": [
        "현재가가 Bull 시나리오 가치를 초과할 것"
      ],
      "cleared_if": [
        "price_to_base_value가 Bull/현재가 배수 안에 있음"
      ],
      "not_covered": "Base가 야심적이라는 판단은 EV 점수가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "reverse_dcf_burden", "score_0_100": 50, "rationale": ""}, {"criterion_id": "base_return", "score_0_100": 50, "rationale": ""}, {"criterion_id": "valuation_robustness", "score_0_100": 50, "rationale": ""}], "valuation_inputs": {"valuation_percentile_5y": null, "revenue_cagr_next_3y": null, "scenarios": {"bear": {"owner_fcf_per_share": []}, "base": {"owner_fcf_per_share": []}, "bull": {"owner_fcf_per_share": []}}}, "archetype_signals": {"price_to_base_value": null, "valuation_percentile_5y": null, "revenue_cagr_next_3y": null}}
작성 후 `python harness.py validate MELI EV`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
