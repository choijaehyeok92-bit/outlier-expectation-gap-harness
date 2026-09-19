# 과제: PANW / 기준일 2026-09-18 / expectation_valuation (EV)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/PANW/reports/EV.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"PANW","company_name":"Palo Alto Networks, Inc.","as_of_date":"2026-09-18","currency":"USD","current_price":363.58,"shares_diluted":818000000,"market_cap_usd":297408440000,"enterprise_value":291276440000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded Palo Alto Networks FY2026 Form 10-K filed 2026-09-10","User-uploaded Palo Alto Networks FY2026 results Form 8-K filed 2026-09-01","User-uploaded Palo Alto Networks Q3 FY2026 Form 10-Q filed 2026-06-03","User-uploaded Palo Alto Networks Q2 FY2026 Form 10-Q filed 2026-02-18","2026-09-18 closing price $363.58 from historical market data"],"special_questions":["Does platformization plus CyberArk identity expansion materially widen PANW's moat enough to justify the current valuation?","How much of reported FCF converts to owner FCF after stock-based compensation and acquisition dilution?","Does the CyberArk/Chronosphere acquisition program improve long-run per-share economics or merely accelerate enterprise scale?"],"net_cash_per_share":7.4963,"valuation_metric":"5-year valuation percentile intentionally left null because trailing P/E is heavily distorted by acquisition accounting and no consistent owner-FCF percentile series was frozen.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# PANW frozen source bundle — as of 2026-09-18

## Frozen market/model inputs
- 2026-09-18 close: **$363.58**.
- Shares outstanding reference: **818M** as of 2026-08-31.
- Market cap: **~$297.4B**.
- FY2026 cash + investments: **$7.906B**.
- FY2026 convertible senior notes: **$1.774B**.
- Frozen liquid net cash: **$6.132B**; net_cash_per_share **$7.4963**.
- Required return: **9%**.
- Horizon: **10 years**.
- Terminal multiples: **15x / 20x / 25x**.
- Owner-FCF/share paths:
  - Bear: 3.0, 3.2, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0
  - Base: 4.0, 5.0, 6.3, 7.8, 9.5, 11.3, 13.2, 15.3, 17.5, 20.0
  - Bull: 4.5, 6.0, 8.0, 10.5, 13.5, 17.0, 21.0, 25.0, 29.0, 34.0
- Locked DCF values: Bear **$80.71**, Base **$239.05**, Bull **$460.00**.
- price/Base: **~1.521**.
- Bull/current: **~1.265**.
- Bear/current: **~0.222**.

## FY2026 10-K
- Revenue **$11.480B** vs $9.221B FY2025 and $8.027B FY2024.
- Subscription and support revenue **$9.200B**.
- GAAP operating income **$695M**.
- GAAP net income **$307M**.
- FY2026 operating cash flow **$4.553B**.
- Purchases of property, equipment and other assets **$440M**.
- Company-defined free cash flow **$4.113B**.
- Total share-based compensation **$1.815B**.
- Owner-style FCF proxy (OCF - capex - SBC): **$2.298B**.
- Weighted-average diluted shares FY2026 **764M**; shares outstanding at 2026-08-31 **818M**.
- Cash and equivalents **$2.514B**; investments **$5.392B**.
- Long-term convertible senior notes **$1.774B**.
- FY2026 common-stock repurchases **$1.000B**.
- Goodwill **$22.010B** and intangible assets **$7.017B**, materially increased by acquisitions.
- CyberArk completed 2026-02-11 for total purchase consideration **$21.1B**; CyberArk holders received $45 cash + 2.2005 PANW shares per CyberArk share.
- CyberArk included $1.25B principal 0% convertible notes due 2030.
- Management disclosed ongoing integration risk for CyberArk and Chronosphere.

## FY2026 Q4 / FY2027 outlook from 2026-09-01 8-K
- Q4 revenue **$3.41B**, +34% y/y.
- Q4 NGS ARR **$9.10B**, +63% y/y.
- RPO **$21.2B**, +34% y/y.
- Q4 GAAP operating income **$172M**; non-GAAP operating income **$1.0B**.
- Q4 GAAP net loss **$282M**; non-GAAP net income **$853M**.
- Q4 OCF **$1.4B**; adjusted FCF **$1.3B**.
- FY2026 adjusted FCF margin **38.4%**.
- FY2027 revenue guidance **$14.10B-$14.20B**, +23%-24%.
- FY2027 NGS ARR guidance **$11.075B-$11.175B**, +22%-23%.
- FY2027 RPO guidance **$25.2B-$25.4B**, +19%-20%.
- FY2027 non-GAAP operating margin **29.5%**.
- FY2027 adjusted FCF margin guidance **38.0%**.
- Management targets **40% adjusted FCF margin in FY2028** and **$20B FY2030 NGS ARR**.
- Console acquisition adds an AI-native agentic workflow platform to Cortex.

## Valuation context
- Trailing P/E is distorted by acquisition accounting and large amortization/fair-value effects.
- FinanceCharts showed price/FCF around **74.5x** on 2026-09-17 versus a 5Y average around **45.5x**.
- Because a reproducible owner-FCF 5Y percentile was not frozen, valuation_percentile_5y remains null.

공시 원문: runs/PANW/sources/*.txt — runs/PANW/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 독립성
runs/PANW/reports/의 다른 에이전트 보고서는 읽지 않는다.

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
    "current_price": 363.58,
    "net_cash_per_share": 7.4963,
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
작성 후 `python harness.py validate PANW EV`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
