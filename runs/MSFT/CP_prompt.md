# 과제: MSFT / 기준일 2026-09-17 / customer_product (CP)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/MSFT/reports/CP.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"MSFT","company_name":"Microsoft Corporation","as_of_date":"2026-09-17","currency":"USD","current_price":497.75,"shares_diluted":7453000000,"market_cap_usd":3709730750000,"enterprise_value":3673181750000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded Microsoft FY2026 Form 10-K filed 2026-07-29","User-uploaded Microsoft FY2026 Q2 Form 10-Q filed 2026-01-28","User-uploaded Microsoft FY2026 Q3 Form 10-Q filed 2026-04-29","User-uploaded Microsoft Form 8-K filed 2026-09-02","MSFT 2026-09-17 closing price $497.75 verified from historical market data"],"special_questions":["Does the AI datacenter investment cycle create sufficient incremental ROIC despite owner FCF/share compression?","How should OpenAI-related revenue/RPO concentration and reciprocal economics affect customer quality, moat, and downside?","Does the FY27 Agents and Infra segment redesign strengthen evidence for a compounder classification?"],"net_cash_per_share":4.9039,"valuation_metric":"Trailing P/E about 27.7x on 2026-09-17 versus a reported 5-year average about 31.6x; percentile intentionally left null because a reproducible full distribution was not frozen.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# MSFT frozen source bundle — as of 2026-09-17

Primary evidence was extracted from the four user-uploaded SEC filing documents. Only information available on or before 2026-09-17 is used.

## Market/model inputs
- 2026-09-17 close: **$497.75**. Historical market-data pages show open $497.80, high $501.47, low $493.17.
- FY2026 diluted weighted-average shares: **7.453B**.
- FY2026 cash + cash equivalents + short-term investments: **$76.843B**.
- FY2026 current + long-term debt: **$40.294B**.
- Frozen net cash/share: **($76.843B - $40.294B) / 7.453B = $4.9039**.
- Deterministic valuation policy: 9% required return, 10 years, 15x/20x/25x terminal multiples.
- Trailing P/E on 2026-09-17: about **27.7x**; a secondary historical source reports a 5-year average near **31.6x**. No percentile is frozen.

## FY2026 Form 10-K — filed 2026-07-29
- Revenue **$331.839B**, +18% y/y; operating income **$155.237B**, +21%; net income **$133.749B**; diluted EPS **$17.95**.
- Microsoft Cloud revenue **$214.4B**, +27%; Azure and other cloud services revenue +41%; Microsoft 365 Commercial cloud +17%; M365 Commercial seats +6%.
- Commercial remaining performance obligation **$678B**, +84%, weighted-average duration about 2.3 years; about 30% expected within 12 months.
- Microsoft Cloud gross margin **66%**, down due to AI infrastructure investment and AI product usage, partly offset by efficiencies.
- OCF **$182.935B**; additions to property and equipment **$115.948B**; stock compensation **$12.405B**.
- Owner FCF definition used by harness = OCF - capex - SBC: FY2026 **$54.582B / $7.32 per diluted share**; FY2025 about **$7.99/share**; FY2024 about **$8.48/share**.
- R&D **$35.562B**. Internal reinvestment absorption (capex + R&D)/OCF ≈ **82.8%**.
- FY2026 share-repurchase program purchases: **36M shares for $16.7B**, average about **$463.89/share**; $40.6B remained authorized.
- Cash + short-term investments **$76.843B**; debt **$40.294B**. Finance lease liabilities **$66.594B** and operating lease liabilities **$21.925B** are separately disclosed.
- Construction commitments **$34.566B** and purchase commitments **$194.060B**. Future operating/finance lease payments including imputed interest total **$443.506B**.
- OpenAI: approximate **25%** as-converted equity-method interest; FY2026 commercial-arrangement revenue including revenue sharing **$24.1B** (~7.3% of total revenue); OpenAI AR **$6.0B**; total funding commitment **$13.0B**, $11.9B funded.
- Microsoft states no related-party arrangements with unconsolidated entities reasonably likely to materially affect liquidity, apart from disclosed items.
- No restatement/auditor-integrity issue was identified in the uploaded filing; internal-control and audit sections are present.

## FY2026 Q2 Form 10-Q — filed 2026-01-28
- Quarterly revenue +17% y/y; Microsoft Cloud revenue **$51.5B**, +26%.
- Azure and other cloud services +39%; M365 Commercial cloud +17%; M365 Commercial seats +6%.
- Commercial RPO **$625B**, +110%.
- Six-month OCF **$80.815B**; six-month additions to PP&E **$49.270B**.

## FY2026 Q3 Form 10-Q — filed 2026-04-29
- Microsoft Cloud revenue **$54.5B**, +29%.
- Azure and other cloud services +40%; M365 Commercial cloud +19%; M365 seats +6%.
- Commercial RPO **$627B**, +99%.
- Nine-month OCF **$127.494B**; additions to PP&E **$80.146B**.

## Form 8-K — filed 2026-09-02
- FY27 reporting changes to two segments: **Agents and Infra** and **Devices and Consumer**.
- Restated FY2026 Agents and Infra revenue **$268.127B** and operating income **$136.365B**; Devices and Consumer revenue **$63.712B**, operating income **$18.872B**.
- Updated Azure definition becomes more purely consumption infrastructure; GitHub cloud and Security Copilot move into Microsoft 365 commercial cloud.
- FY27 Q1 total revenue outlook **$89.85B-$90.95B**.
- Azure revenue growth outlook approximately **45% constant currency**.
- FY27 Q1 capex expected **over $50B**, including component-pricing effects.

## Secondary market facts frozen only for context
- 2026-09-17 MSFT close $497.75.
- Trailing P/E about 27.7x; 5-year average P/E about 31.6x.

공시 원문: runs/MSFT/sources/*.txt — runs/MSFT/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 독립성
runs/MSFT/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 CP (domain_analyst)
# Customer & Product Analyst

- `agent_id`: `CP`
- `domain`: `customer_product`

## 임무
고객이 제품을 선택하는 경제적 이유와 지불의사를 확인하고, 유지율·사용량 데이터로 제품력을 검증하며, 성장이 할인·보조금·마케팅으로 인위적으로 만들어졌는지 가려낸다.

## 관점별 질문
**Bull — 고객가치**
1. 제품이 고객 비용을 얼마나 줄이거나 매출·생산성을 얼마나 높이는가? 대체재 대비 ROI와 payback은?
2. 가격 인상 후에도 고객가치가 유지되는가? 제품 제거 시 고객 손실은 얼마나 큰가?

**Verifier — 유지율과 사용량**
1. NRR/GRR/churn/renewal/usage 추세와 신규 코호트 품질은?
2. 고객당 사용량 또는 wallet share가 증가하는가? 상위 고객 의존도와 집중도는?

**Skeptic — 보조금과 마케팅**
1. CAC·payback 추세와 판매·마케팅비 증가율 대비 질적 성장은?
2. 프로모션·보조금·벤더 금융을 제거해도 수요가 유지되는가? 단위경제가 성장과 함께 개선되는가?

## Hard Veto 중점
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성

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
        "id": "customer_roi",
        "weight": 0.4,
        "question": "고객 ROI·지불의사",
        "anchors": {
          "25": "보조금/프로모션 의존",
          "50": "정량 근거 부족",
          "75": "ROI·가격결정력 확인",
          "90": "미션크리티컬"
        }
      },
      {
        "id": "retention_usage",
        "weight": 0.35,
        "question": "유지율·사용량·wallet share",
        "anchors": {
          "25": "이탈/사용감소",
          "50": "안정적",
          "75": "코호트 개선",
          "90": "지속 확장"
        }
      },
      {
        "id": "unit_economics",
        "weight": 0.25,
        "question": "CAC/payback/단위경제",
        "anchors": {
          "25": "성장할수록 악화",
          "50": "혼재",
          "75": "규모경제 확인",
          "90": "강한 운영레버리지"
        }
      }
    ]
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
- 고객가치 없이 마케팅·보조금에 의존하는 성장
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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "고객가치 없이 마케팅·보조금에 의존하는 성장", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "customer_roi", "score_0_100": 50, "rationale": ""}, {"criterion_id": "retention_usage", "score_0_100": 50, "rationale": ""}, {"criterion_id": "unit_economics", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate MSFT CP`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
