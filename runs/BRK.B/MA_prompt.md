# 과제: BRK.B / 기준일 2026-09-18 / management_allocation (MA)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/BRK.B/reports/MA.json. 그 외 파일은 수정하지 않는다.
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

## 독립성
runs/BRK.B/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 MA (domain_analyst)
# Management & Capital Allocation Analyst

- `agent_id`: `MA`
- `domain`: `management_allocation`

## 임무
경영진의 말이 아니라 자본배분의 실제 트랙레코드를 평가하고, 정직성·회계 신뢰성·보상구조·실행 리스크를 검증한다.

## 관점별 질문
**Bull — 자본배분**
1. R&D·M&A·자사주 매입이 내재가치 대비 합리적 가격에서 이뤄져 경제가치로 전환됐는가?
2. 저수익 사업을 철수하고 실패를 인정해 자원을 재배치한 사례가 있는가?

**Verifier — 거버넌스와 정직성**
1. 회계정책 변경·재작성·감사인 이슈, 관련자 거래, 지배구조 위험이 있는가?
2. 보상체계가 주당 가치와 장기성과에 연동되는가? 가이던스와 실제 결과는 정합적인가?

**Skeptic — 실행과 인센티브**
1. 전략 우선순위가 자주 바뀌거나 제국건설 경향이 있는가? 보상 확대가 주당 성과를 앞서는가?
2. 핵심 인재·창업자 의존성과 임원 이탈, 내부자 매도 패턴은?

## Hard Veto 중점
- 경영진 정직성 또는 회계 신뢰성 훼손

## v3 분석 계약
버핏 스타일 가치주는 싼 가격만으로 부실 자본배분·정직성 문제를 통과시키지 않는다. 예측 가능한 경제성, 환원과 재투자의 실제 주당 가치 효과를 검증한다.

## 장기 성장 유형에서 추가로 보는 것
자본배분 판정에 다음을 명시적으로 포함한다.

- **자기파괴(self-disruption)** — 레거시 제품·사업을 스스로 잠식한 실적이 있는가.
- **조직 학습** — 실패한 투자에서 무엇을 바꿨는지 결과로 확인되는가.
- **인재 배치** — 핵심 인재를 새 기회로 재배치한 사례가 있는가.
- **전략적 적응력** — 기술·규제 전환기에 방향을 바꾼 이력과 그 결과.
- **보상의 시계** — 장기 성과에 연동되는가, 단기 외형·주가에 연동되는가.

**창업자 주도라는 사실만으로 가점하지 않는다.** 창업자 지배는 장기 시계의 근거가 될 수도, 견제 부재의 위험이 될 수도 있다. 어느 쪽인지 증거로 판정한다.

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
        "id": "capital_allocation",
        "weight": 0.4,
        "question": "R&D·M&A·자사주·철수의 가치창출",
        "anchors": {
          "25": "가치파괴",
          "50": "혼재",
          "75": "합리적",
          "90": "탁월한 재배분"
        },
        "observable_anchors": {
          "metric": "최근 4개 분기 자사주 평균 매입단가 / EV 에이전트의 Base 주당가치",
          "table": [
            {
              "test": "0.8 미만",
              "score": 80,
              "hi": 0.8
            },
            {
              "test": "0.8~1.0",
              "score": 70,
              "lo": 0.8,
              "hi": 1.0
            },
            {
              "test": "1.0~1.2",
              "score": 55,
              "lo": 1.0,
              "hi": 1.2
            },
            {
              "test": "1.2 초과, 또는 대형 M&A가 손상차손으로 이어졌다",
              "score": 30,
              "lo": 1.2
            }
          ],
          "modifiers": [
            "저수익 사업 철수·자산 재배치 사례가 1차 자료로 확인되면 +10 (상한 90)",
            "자사주 매입이 없으면 M&A·R&D의 사후 수익률로 같은 표를 적용하고 근거를 rationale에 적는다"
          ],
          "interpolation": {
            "mode": "band_centre",
            "metric_direction": "decreasing",
            "note": "매입단가/Base가치는 연속 비율이다. 행을 지표 오름차순으로 재정렬했으며 점수는 내림차순이다."
          }
        }
      },
      {
        "id": "governance_integrity",
        "weight": 0.35,
        "question": "회계·거버넌스·보상 정렬",
        "anchors": {
          "25": "중대한 신뢰문제",
          "50": "통상 위험",
          "75": "양호",
          "90": "매우 높은 신뢰"
        }
      },
      {
        "id": "execution_adaptability",
        "weight": 0.25,
        "question": "실행과 실패 인정·전환",
        "anchors": {
          "25": "반복실패",
          "50": "평균",
          "75": "일관 실행",
          "90": "탁월한 적응"
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
- 경영진 정직성 또는 회계 신뢰성 훼손

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
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "경영진 정직성 또는 회계 신뢰성 훼손", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "capital_allocation", "score_0_100": 50, "rationale": ""}, {"criterion_id": "governance_integrity", "score_0_100": 50, "rationale": ""}, {"criterion_id": "execution_adaptability", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate BRK.B MA`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
