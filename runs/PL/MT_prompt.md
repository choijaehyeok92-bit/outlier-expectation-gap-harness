# 과제: PL / 기준일 2026-09-18 / moat_trajectory (MT)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/PL/reports/MT.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"PL","company_name":"Planet Labs PBC","as_of_date":"2026-09-18","currency":"USD","current_price":16.18,"shares_diluted":363847989,"market_cap_usd":5887060462.02,"enterprise_value":5481660462.02,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded Planet Labs FY2026 Form 10-K filed 2026-03-23","User-uploaded Planet Labs Q1 FY2027 Form 10-Q filed 2026-06-05","User-uploaded Planet Labs Q2 FY2027 Form 10-Q and Form 8-K filed 2026-09-03","2026-09-18 closing price $16.18 from historical market data"],"special_questions":["Does daily global imagery plus AI analytics create a durable data moat or merely a capital-intensive imagery product?","Can satellite services scale without structurally compressing gross margin or requiring repeated equity issuance?","Do RPO/backlog and sovereign-defense wins justify Moonshot status despite SBC and ATM dilution?"],"net_cash_per_share":1.1142015684,"valuation_metric":"No reproducible full 5-year valuation percentile frozen; valuation is assessed through locked owner-FCF/share DCF.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# PL frozen source bundle — as of 2026-09-18

## Source lineage
- FY2026 Form 10-K filed 2026-03-23 — SHA256 a29a790b8e2c167a3a2eea058d9bb88d3bfb807307186502ba8a19c0bf4edff8
- Q1 FY2027 Form 10-Q filed 2026-06-05 — SHA256 79f1c8a0aab6e1d3e042b269ac53ad617a756c5b50180c6d17ebe93039abffd0
- Q2 FY2027 Form 10-Q filed 2026-09-03 — SHA256 8023b8a026d982e264a59858087afa690e84408988fd8fdce191b32314af7fad
- Q2 FY2027 Form 8-K filed 2026-09-03 — SHA256 f52a0ed36c5496856e64a4171236cf2199be10b56c0e80802cb19f672920346d

## Frozen market/model inputs
- 2026-09-18 close: **$16.18**.
- Shares outstanding: Class A 340.354M + Class B 23.494M = **363.848M**.
- Market cap: **~$5.887B**.
- Q2 cash, cash equivalents and short-term investments: **$865.4M**.
- 2030 convertible notes principal: **$460.0M**.
- Frozen net cash: **$405.4M**; net_cash_per_share **$1.1142**.
- DCF policy: 9% required return, 10-year horizon, 15x/20x/25x terminal multiples.
- Bear/Base/Bull owner-FCF/share paths:
  - Bear: -0.05,0,0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40
  - Base: 0.15,0.25,0.40,0.60,0.85,1.10,1.40,1.70,2.00,2.30
  - Bull: 0.25,0.45,0.70,1.00,1.35,1.75,2.20,2.70,3.20,3.80
- Locked DCF: Bear **$4.55**, Base **$26.35**, Bull **$50.66**; price/Base **~0.614**.

## FY2026 10-K
- Revenue **$307.727M**, +26% vs FY2025 $244.352M.
- Gross profit **$172.485M**; GAAP operating loss **$95.073M**.
- Revenue by customer type: Defense & Intelligence **$180.232M**, Civil Government **$71.910M**, Commercial **$55.585M**.
- Adjusted EBITDA **+$15.495M** vs **-$10.627M** in FY2025.
- RPO **$852.435M** vs $412.829M; backlog **$900.427M** vs $503.749M.
- Operating cash flow **+$134.362M** vs -$14.374M in FY2025.
- PP&E purchases **$76.714M** and capitalized internal-use software **$4.783M**.
- Stock-based compensation **$54.995M**.
- 2030 convertible notes issued at **$460M** principal, 0.50% coupon.

## Q2 / H1 FY2027
- Q2 revenue **$116.052M**, +58% y/y; H1 revenue **$210.202M**, +51%.
- Q2 GAAP gross margin **57%**; non-GAAP **59%**.
- Q2 operating loss **$13.509M** vs $17.960M loss; adjusted EBITDA **+$13.928M**.
- H1 adjusted EBITDA **+$12.895M** vs +$7.606M.
- Q2 recurring ACV **98%**.
- RPO **$753.117M**; backlog **$814.863M**.
- Net Dollar Retention Rate **109%** vs 107%.
- H1 operating cash flow **+$68.388M**.
- YTD free cash flow **+$21.3M**; adjusted FCF **+$28.8M**.
- Cash, cash equivalents and short-term investments **$865.4M**.
- H1 stock-based compensation **$33.521M**.
- Three customers were 17%, 11%, 10% of Q2 revenue; H1 top three were 13%, 12%, 11%.
- Q2 ATM issuance: 3.782M Class A shares, gross proceeds **$122.4M**, average net sale price **$31.95/share** after expenses.
- FY2027 guidance: revenue **$430M-$441M**, non-GAAP GM **55%-57%**, adjusted EBITDA **+$3M to +$10M**, capex **$100M-$115M**.
- Q3 guidance: revenue **$101M-$105M**, adjusted EBITDA **-$6M to -$1M**.

## Business evidence
- August 2026 NGA Global Monitoring Service OTA award: **$8M**.
- German civil-government satellite-services tender: maximum possible **€25M over 5 years** including options.
- 7-figure one-year European defense/intelligence agreement.
- Rwanda Space Agency national data/analytics program.
- Renewal with a hyperscaler AI developer for global monitoring of data centers and semiconductor-fab construction.
- Satellite-services strategy includes sovereign capacity; Pelican tech demo launched and Tanager-2/SuperDove satellites prepared for launch.

공시 원문: runs/PL/sources/*.txt — runs/PL/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 독립성
runs/PL/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 MT (domain_analyst)
# Moat Trajectory Analyst

- `agent_id`: `MT`
- `domain`: `moat_trajectory`

## 임무
현재 해자의 크기가 아니라 5년 뒤 해자가 지금보다 넓어질지 방향을 평가한다. 네트워크·데이터·생태계 효과가 진짜 양의 피드백 루프인지, 기술대체·범용화로 해자가 축소될 경로는 없는지 함께 본다.

## 관점별 질문
**Bull — 해자 강화**
1. 점유율·가격결정력·전환비용이 강화되는가? 규모의 경제가 단위원가나 R&D 효율로 이어지는가?
2. 브랜드·데이터·유통·설치기반이 강화되고, 신제품이 기존 해자를 복리화하는가?

**Verifier — 네트워크·생태계**
1. 사용자·개발자·파트너 증가가 다른 참여자의 가치에 실제로 기여하는가? 멀티호밍은 쉬운가?
2. 데이터가 제품 개선·원가·전환비용에 누적 우위를 만드는가? 생태계를 옮길 때의 비용은?

**Skeptic — 해자 축소**
1. 고객이 더 싸고 충분히 좋은 대안으로 이동할 수 있는가? 핵심 차별화가 표준화·범용화되고 있는가?
2. 플랫폼 공급자나 핵심 파트너가 가치풀을 흡수할 수 있는가? R&D 생산성이 둔화되는가?

## Hard Veto 중점
- 해자의 지속적인 축소

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
        "id": "switching_pricing",
        "weight": 0.35,
        "question": "전환비용·가격결정력·점유율 추세",
        "anchors": {
          "25": "약화",
          "50": "정체",
          "75": "강화",
          "90": "구조적 강화"
        }
      },
      {
        "id": "network_data_ecosystem",
        "weight": 0.35,
        "question": "네트워크·데이터·생태계 피드백",
        "anchors": {
          "25": "내러티브뿐",
          "50": "일부 효과",
          "75": "측정 가능",
          "90": "복리형 방어벽"
        },
        "observable_anchors": {
          "metric": "생태계 규모·추세·전환비용을 뒷받침하는 1차 자료 수치의 개수",
          "table": [
            {
              "test": "검증 가능한 규모 수치가 없다",
              "score": 25
            },
            {
              "test": "규모 수치 1~2개, 추세·전환비용 근거 없음",
              "score": 55
            },
            {
              "test": "규모 수치 3개 이상, 같은 정의의 증가 추세는 미확인",
              "score": 75
            },
            {
              "test": "규모 수치 3개 이상 + 같은 정의의 증가 추세 확인",
              "score": 85
            },
            {
              "test": "위에 더해 전환비용이 구체 사례로 확인",
              "score": 90
            }
          ]
        }
      },
      {
        "id": "commoditization_resilience",
        "weight": 0.3,
        "question": "범용화·대체 위험 방어",
        "anchors": {
          "25": "쉽게 대체",
          "50": "혼재",
          "75": "복수 방어층",
          "90": "대체가 해자를 강화"
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
- 해자의 지속적인 축소

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
    "해자의 지속적인 축소": {
      "elements": [
        "해자 지표가 실제로 축소 중일 것",
        "그 축소가 지속적일 것"
      ],
      "cleared_if": [
        "gross margin·점유율·전환비용 등 관측 지표가 유지 또는 강화"
      ],
      "not_covered": "미래의 대체 위협은 MT 점수와 모니터링 대상이지 현재 축소의 증거가 아니다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "해자의 지속적인 축소", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "switching_pricing", "score_0_100": 50, "rationale": ""}, {"criterion_id": "network_data_ecosystem", "score_0_100": 50, "rationale": ""}, {"criterion_id": "commoditization_resilience", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate PL MT`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
