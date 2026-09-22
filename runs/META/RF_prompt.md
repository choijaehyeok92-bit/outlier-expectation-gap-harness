# 과제: META / 기준일 2026-09-21 / reinvestment_fcf (RF)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/META/reports/RF.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"META","company_name":"Meta Platforms, Inc.","as_of_date":"2026-09-21","currency":"USD","current_price":741.25,"shares_diluted":2566000000,"market_cap_usd":1902047500000,"enterprise_value":1895451500000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680125000017/meta-20241231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680124000081/meta-20240930.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680125000054/meta-20250331.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828025036791/meta-20250630.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828025047240/meta-20250930.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828026028526/meta-20260331.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828026050705/meta-20260630.htm","https://finance.yahoo.com/quote/META/history/","META 2026-09-21 closing price $741.25"],"special_questions":["Separate structural AI-driven monetization upside from expectations already embedded in the 2026-09-18 price.","Stress-test the return path against sharply higher AI infrastructure capex and Reality Labs losses.","Treat the Q3 2025 OBBBA tax charge as a normalization candidate, not an automatically excluded expense."],"net_cash_per_share":2.570538,"valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"revenue_by_region":{"United States and Canada":0.392435,"Europe":0.231726,"Asia-Pacific":0.267792,"Rest of World":0.108048}}}

## 독립성
runs/META/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 RF (domain_analyst)
# Reinvestment & FCF per Share Analyst

- `agent_id`: `RF`
- `domain`: `reinvestment_fcf`

## 임무
과거 평균 ROIC가 아니라 신규 투자자본의 수익률과 재투자 활주로를 평가하고, 회사 성장이 아니라 주당 소유자경제가치(FCF/share)가 늘어나는지 검증한다.

## 관점별 질문
**Bull — 증분 ROIC와 재투자**
1. 증분 매출·영업이익·FCF 대비 증분 투자자본은? 규모가 커져도 한계수익률이 유지되는가?
2. 내부 재투자 기회는 몇 년 지속되는가? 신규 지역·제품·고객군의 ROIC는 기존 사업과 비교해 어떤가?

**Verifier — FCF per share**
1. FCF/share 3~5년 CAGR과 변동 원인은? SBC·증자·전환증권이 주당 가치를 희석하는가?
2. 운전자본·자본화 회계·투자손익이 FCF와 이익을 왜곡하는가? 정상화 FCF와 보고 FCF의 차이는?

**Skeptic — 재투자 활주로**
1. 높은 ROIC가 소규모 기반효과나 일회성 가격·공급부족에서 왔는가? 재투자 가능한 시장의 실제 규모는?
2. 성장 유지에 필요한 Capex·R&D·S&M이 과소인식됐는가? 성장이 자본집약적으로 바뀌는 변곡점은?

## Hard Veto 중점
- 증분 ROIC의 구조적 붕괴
- 장기간 지속되는 과도한 희석

## pre-FCF 기업의 주당 경제가치
사는 것은 회사 성장이 아니라 **주당 경제가치의 성장**이다. FCF가 아직 구조적으로 음수여서 FCF/share가 의미를 갖지 못하는 단계라도, 희석의 경제적 영향을 평가하지 못한 채 넘어가지 않는다. 이때는 보조 proxy를 명시적으로 골라 확인한다.

우선순위는 `veto_criteria.definitions`의 `per_share_value_proxies`를 따른다 — `owner_fcf_per_share` → `gross_profit_per_share` → `arr_per_share` → 명시적으로 정당화한 `economic_value_per_share_proxy`. 어느 것을 왜 골랐는지 rationale에 적는다.

예: 주식수 +7%에 gross profit +50%면 GP/share는 크게 증가한다. 희석은 여전히 점수 감점 사유지만 희석 Hard Veto의 주당가치 파괴 요건은 충족되지 않는다. 반대로 주식수 +10%에 gross profit +5%이거나 FCF/share가 지속 감소하면 파괴 증거가 강해진다.

**보조 proxy는 `fcf_per_share_quality`의 공식 점수를 대체하지 않는다.** 그 점수는 rubric의 관측표를 그대로 따른다. proxy는 희석 Hard Veto의 주당가치 요건 판단과 `dilution_metrics`에 쓴다.

## v3 분석 계약
v3는 incremental_roic, reinvestment_runway, fcf_per_share_quality의 검증된 subscores를 직접 읽는다. 버핏 스타일 가치주는 큰 재투자 활주로를 요구하지 않지만 유지보수 capex·운전자본·SBC·일회성을 차감한 지속 가능한 정상화 owner earnings를 요구한다.

## Structural geopolitical re-analysis
When reviewing a routed structural event, add its event_id to geo_events_reviewed only after citing new company-level evidence.

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
        "id": "incremental_roic",
        "weight": 0.4,
        "question": "증분 투자자본 수익률",
        "anchors": {
          "25": "자본비용 미달",
          "50": "측정 불확실",
          "75": "우수",
          "90": "대규모에서도 매우 높음"
        }
      },
      {
        "id": "reinvestment_runway",
        "weight": 0.3,
        "question": "고수익 재투자 활주로",
        "anchors": {
          "25": "짧음",
          "50": "수년",
          "75": "장기 복수경로",
          "90": "대규모 장기 복리"
        },
        "observable_anchors": {
          "metric": "내부 재투자 흡수율 = (capex + R&D) / 영업현금흐름. 측정 기간은 최근 12개월(TTM)이다.",
          "table": [
            {
              "test": "15% 미만 — 창출 자본이 내부에 흡수되지 않고 자사주·외부투자로 나간다",
              "score": 50,
              "hi": 0.15
            },
            {
              "test": "15~35%",
              "score": 65,
              "lo": 0.15,
              "hi": 0.35
            },
            {
              "test": "35~60%",
              "score": 80,
              "lo": 0.35,
              "hi": 0.6
            },
            {
              "test": "60% 초과 + 증분 ROIC가 자본비용의 2배 이상",
              "score": 90,
              "lo": 0.6
            }
          ],
          "interpolation": {
            "mode": "band_centre",
            "metric_direction": "increasing",
            "note": "흡수율은 연속 비율이므로 행간 보간한다. 밴드 중앙에서는 표 값과 동일하다."
          },
          "period": {
            "basis": "TTM",
            "rationale": "분기 단독치는 운전자본 타이밍에 따라 크게 흔들리고(NVDA Q1 FY27 OCF $50,344M vs Q2 $24,077M), 누적 YTD는 회계연도 중 실행 시점에 따라 기간 길이가 달라져 run 간 비교가 불가능하다. TTM은 두 문제를 모두 피하고 이 하네스가 valuation에서 이미 쓰는 기준과 일치한다.",
            "fallback": [
              "latest_full_fiscal_year",
              "latest_reported_ytd"
            ],
            "fallback_rule": "TTM 산출이 불가능하면 위 순서로 대체하고 rationale에 실제 사용한 기간을 명시한다."
          }
        }
      },
      {
        "id": "fcf_per_share_quality",
        "weight": 0.3,
        "question": "SBC·Capex 후 FCF/share",
        "anchors": {
          "25": "감소",
          "50": "왜곡 큼",
          "75": "정상화 성장",
          "90": "강한 복리"
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
      "veto는 도메인 점수에 이미 반영된 사실만으로 세우지 않는다. veto_criteria의 구성요건이 독립적으로 충족될 때만 성립한다.",
      "observable_anchors에 interpolation.mode=band_centre가 있으면 행 사이를 보간한다. 밴드 중앙은 표 값과 같고 경계에서는 이웃 밴드와의 중간값이 되며, 결과는 5점 단위로 반올림한다. rationale에 사용한 지표값과 보간 결과를 함께 적는다.",
      "interpolation.mode=none인 관측표와 형용사 앵커만 있는 criterion은 보간하지 않는다. 계수형 지표를 보간하면 확보하지 못한 관측치를 있는 것처럼 만들고, 형용사 앵커는 observed_divergence가 기록한 프로바이더 분산의 진원지이므로 표 값에 고정한다.",
      "observable_anchors에 period가 있으면 그 기간으로만 지표를 산출한다. 다른 기간을 쓰면 rationale에 이유와 사용 기간을 적는다."
    ],
    "observed_divergence": "NVDA 2026-09-17/18 동일 종가 기준 gpt-5.6-sol 대 Claude Opus 5 실행 비교: criterion 27개 평균 격차 +10.2점(sol이 높음), 27개 전부 sol >= opus. 관측 가능한 사실형 criterion은 +3.1, 위험 가중 판단형은 +13.2로 4배 차이였다. 앵커가 형용사인 criterion에서만 갈라진다는 뜻이다."
  }
}
criterion은 5점 단위로 채점한다. score_0_100은 subscores 고정 가중평균과 같아야 한다. self-confidence와 bull/bear 폭은 자동 감점하지 않는다.
anchor_policy를 반드시 지킨다. observable_anchors가 있는 criterion은 판정표가 앵커 형용사보다 우선한다. 85 이상과 40 미만에는 각각 상단·하단 게이트가 걸려 있다.
interpolation.mode=band_centre인 관측표는 행 사이를 보간한다. 밴드 안 위치 p=(x-lo)/(hi-lo)에 대해 p<0.5면 S-(0.5-p)(S-S_prev), p>=0.5면 S+(p-0.5)(S_next-S)이고 결과를 5점 단위로 반올림한다. 밴드 중앙은 표 값과 같다. rationale에 사용한 지표값 x와 보간 결과를 함께 적는다.
interpolation.mode=none인 표와 형용사 앵커 criterion은 보간하지 않고 표 값을 그대로 쓴다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 장기간 지속되는 과도한 희석
- 증분 ROIC의 구조적 붕괴

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
- **`conditional`은 정보 부족 상태가 아니다.** 구성요건이 거의 모두 1차 자료로 확인되었고 결정적 자료 하나만 미확보인 "거의 confirmed" 상태다. 자료가 없어 판단할 수 없으면 `conditional`이 아니라, 구성요건이 반증되었으면 `cleared`, 평가 자체를 못 했으면 `candidate`다. "아직 장기 이력이 없다", "앞으로 나빠질 수 있다"는 `conditional`의 사유가 될 수 없다. 그런 우려는 점수·`uncertainties`·`key_kpis`로 보낸다.
- `requires_element_assessment`가 선언된 veto에 `confirmed`·`conditional`을 쓰려면 `elements_met`에 구성요건 전부를 참/거짓으로 답해야 한다. `confirmed`는 전부 참, `conditional`은 정확히 하나만 거짓이며 `decisive_missing_evidence`에 그 자료와 해소 조건을 적는다. `validate`가 이를 검사한다.
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
    "장기간 지속되는 과도한 희석": {
      "requires_element_assessment": true,
      "elements": [
        "희석이 장기간 지속될 것",
        "그 폭이 과도할 것",
        "희석을 감안한 주당 경제가치가 충분히 증가하지 않을 것",
        "향후에도 반복될 구조적 자금조달 또는 SBC 원인이 있을 것"
      ],
      "element_tests": {
        "희석이 장기간 지속될 것": "다음 중 하나가 1차 자료로 확인될 때만 충족: (1) multi_year_min_years 이상 연속 회계연도에서 의미 있는 순희석 반복, (2) 최근 3년 희석주식수 CAGR ≥ three_year_diluted_share_cagr, (3) 최근 3년 누적 희석 ≥ three_year_cumulative_dilution. 한 분기 또는 한 번의 ATM·M&A 자금조달은 이 요건을 충족하지 못한다. 상장 이력이 짧아 장기 자료가 없는 것은 '충족되지 않음'이지 '미확인'이 아니다.",
        "그 폭이 과도할 것": "희석률 자체가 아니라 아래 주당 경제가치 요건과 함께 판단한다. 단일 연도 희석률이 높다는 사실만으로는 충족하지 않는다.",
        "희석을 감안한 주당 경제가치가 충분히 증가하지 않을 것": "per_share_value_proxies의 우선순위에 따라 선택한 proxy가 희석 기간 동안 정체·감소해야 충족된다. 주식수 +7%에 gross profit +50%처럼 주당 proxy가 크게 증가하면 이 요건은 반증되고 veto는 cleared다.",
        "향후에도 반복될 구조적 자금조달 또는 SBC 원인이 있을 것": "사업 유지에 반복 ATM이 필요하거나, runway가 짧아 FCF breakeven 전 추가 증자가 불가피하거나, SBC가 장기간 매출·GP 성장보다 빠르게 증가하거나, 자본계획상 반복 equity issuance가 불가피할 때 충족된다. 일회성 M&A·일시적 증자이고 현재 runway가 충분하면 충족되지 않는다."
      },
      "thresholds": {
        "multi_year_min_years": 2,
        "three_year_diluted_share_cagr": 0.08,
        "three_year_cumulative_dilution": 0.25
      },
      "per_share_value_proxies": [
        {
          "priority": 1,
          "proxy": "owner_fcf_per_share",
          "use_when": "기본. FCF가 구조적으로 의미 있는 단계"
        },
        {
          "priority": 2,
          "proxy": "gross_profit_per_share",
          "use_when": "FCF가 아직 구조적으로 음수인 초기 성장기업"
        },
        {
          "priority": 3,
          "proxy": "arr_per_share",
          "use_when": "SaaS 등 ARR이 검증 가능하게 공시되는 경우"
        },
        {
          "priority": 4,
          "proxy": "economic_value_per_share_proxy",
          "use_when": "위 셋이 부적절한 사업. 선택 이유를 명시한다"
        }
      ],
      "cleared_if": [
        "희석주식수가 보합 또는 감소",
        "자사주 매입이 SBC를 상쇄",
        "희석 기간 동안 선택한 주당 경제가치 proxy가 충분히 증가",
        "장기간 지속 요건의 세 가지 임계값 중 어느 것도 충족되지 않음 (상장 이력이 짧아 자료가 없는 경우 포함)",
        "희석 원인이 일회성이고 현재 runway로 추가 증자 필요성이 확인되지 않음"
      ],
      "watch_triggers": [
        "연환산 희석률이 dilution_policy의 monitor 밴드 이상",
        "SBC가 매출 또는 gross profit 성장보다 빠르게 증가",
        "전환증권·ATM 잔여 한도가 유의미"
      ],
      "not_covered": "SBC 존재 자체는 요건이 아니다. 단일 연도의 높은 희석, 상장 이력이 짧아 장기 자료가 없는 것, 장래 희석 가능성에 대한 우려도 요건이 아니다. 이들은 FS·RF 점수와 dilution_watch로 보낸다."
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
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "장기간 지속되는 과도한 희석", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "증분 ROIC의 구조적 붕괴", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "incremental_roic", "score_0_100": 50, "rationale": ""}, {"criterion_id": "reinvestment_runway", "score_0_100": 50, "rationale": ""}, {"criterion_id": "fcf_per_share_quality", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate META RF`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
