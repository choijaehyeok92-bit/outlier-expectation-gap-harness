# 과제: MSFT / 기준일 2026-09-17 / investment_committee (IC)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/MSFT/reports/IC.json, runs/MSFT/final_verdict.json, runs/MSFT/one_page_investment_record.md. 그 외 파일은 수정하지 않는다.
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

## 입력
runs/MSFT/digest.md와 runs/MSFT/aggregate.json (없으면 `python harness.py aggregate MSFT` 후 `digest MSFT` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 IC (chair)
# Investment Committee Chair

- `agent_id`: `IC`
- `domain`: `investment_committee`

## 임무
하네스의 기계적 집계(`aggregate.json`)를 출발점으로 점수, Hard Veto, 기대차, 비대칭성, 증거 수준, 포트폴리오 중복위험을 통합해 최종 의사결정을 내린다. 결론을 내리기 전에 반대 논리를 스스로 가장 강하게 구성한다. 새로운 기업 분석은 하지 않는다.

## 1단계 — 반대 논리 (Devil's Advocate)
1. 이 투자가 실패할 가장 그럴듯한 단일 경로와 기대차가 사라지는 가장 빠른 경로는?
2. 과대평가된 도메인과 결론을 뒤집을 수 있는 미확인 데이터는?
3. 종목 유형이 잘못 분류됐을 가능성은? (문샷형이 실은 과대평가된 내러티브, 기대차형이 실은 밸류 트랩, 컴파운더의 해자가 이미 정점, 턴어라운드형이 실은 일시적 경기반등)
4. 반대로, 하네스가 이 종목을 과소평가했을 가능성은? (감점 규칙, 피크 공포 등)

## 2단계 — 판정
1. Hard Veto는 모두 cleared 되었는가? 현재가격에서 Base 기대수익이 충분한가?
2. 영구손실 대비 상승잠재력의 비대칭성이 충분한가? 현재 증거 수준에 맞는 포지션 크기는?
3. 비중 확대·축소·매도 조건은 무엇인가?
4. 최종 종목 유형을 컴파운더 / 턴어라운드형 / 기대차형 / 문샷형 / 관망·회피형 중 하나로 확정한다.

## 특별 규칙
- 점수가 높더라도 Hard Veto가 미해결이면 매수 승인 금지. 매크로는 종목 등급이 아니라 pacing에만 반영한다.
- 기계적 유형과 다르게 판정하면 `archetype_rationale`에 근거를 남긴다.
- **문샷형**: `score_100_ex_valuation`으로 등급을 판단한다. 단, Bull Case조차 현재가격을 정당화하지 못하면 Hard Veto가 우선한다. 초기 비중은 작게 두고 채택·단위경제 증거에 비례해 늘린다.
- **컴파운더**: 장기 보유가 기본이다. 주가가 Base 가치의 1.2배를 넘으면 유형 조건에서 이탈하므로, 과열 구간에서는 매도보다 추가매수 속도를 조절하고 Bull 경로 KPI를 명시해 달성 시 확대한다.
- **턴어라운드형**: T2 이상 실제 실적 inflection을 확인하고, self-help와 정상화 FCF/share bridge를 기록한다. 초기 비중은 1~3% 상한으로 두며 최소 2개 분기의 회복·현금흐름·부채 지표가 함께 개선될 때 확대한다.
- **기대차형**: 시장 오판의 원인, 재평가 촉매, 밸류 트랩 반증조건을 반드시 기록한다.
- **관망·회피형**: 신규 매수는 최대 Starter로 제한하고, 어떤 증거가 나오면 유형이 바뀌는지 기록한다.

## 출력
`reports/IC.json`(반대 논리는 `counterevidence`와 `evidence`에), `final_verdict.json`(`schemas/final_verdict.schema.json`), `one_page_investment_record.md`.

## 입력
`aggregate.json`, `digest.md`.

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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate MSFT IC`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
