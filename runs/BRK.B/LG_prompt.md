# 과제: BRK.B / 기준일 2026-09-18 / long_term_growth (LG)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/BRK.B/reports/LG.json. 그 외 파일은 수정하지 않는다.
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

## 지침 LG (domain_analyst)
# Long-Term Outlier Growth Analyst

- `agent_id`: `LG`
- `domain`: `long_term_growth`

## 임무
장기 아웃라이어 성장(`outlier_growth`) 유형의 적격 여부를 가르는 네 가지만 평가한다. 기존 도메인이 이미 측정하는 것을 다시 채점하지 않는다.

1. **5년 기회 규모** — 사업이 5년 내 대략 2배 이상으로 커질 수 있는가
2. **10년 성장 지속기간** — 그 이후에도 고부가 성장이 이어질 수 있는가
3. **조직 문화·적응력** — 반복적으로 적응·자기파괴하며 인재와 자본을 재배치할 수 있는가
4. **시장 기대오류** — 시장이 과소평가하고 있을 **구체적이고 반증 가능한** 장기 사실은 무엇인가

이 축은 **100점 핵심 점수에 합산하지 않는다**. DI와 같은 독립 평가축이며, 유형 적격 판정과 IC 해석에만 쓰인다.

경쟁우위의 현재 크기(MT), 고객가치(CP), 자본배분(MA), 생존력(FS), 가격 내재 기대(EV), 비대칭성(AS)은 각 담당 도메인이 판정한다. LG는 그 위에 **기간과 규모, 조직의 적응력, 기대차의 구체성**만 더한다.

## 관점별 질문

**Bull — 장기 규모와 지속기간**
1. 5년 기회 규모는 무엇으로 뒷받침되는가? 침투 여력, 카테고리 성장, 신제품 중 어느 것이며 각각 1차 자료가 있는가?
2. TAM을 **점유**하는 데 그치는가, **창출·확장**하는가? 후자라면 그 증거는 무엇인가?
3. 10년 뒤에도 성장이 남아 있으려면 무엇이 참이어야 하는가? 기회가 소진되지 않고 갱신되는 구조인가?
4. 조직은 과거에 스스로를 어떻게 바꿨는가? 레거시를 잠식한 사례가 있는가?
5. 현실적인 5배 경로가 매출·마진·주당 FCF·신규 가치풀 중 무엇으로 구성되는가?

**Verifier — 1차 증거**
1. 채택과 고객 행동에 대한 1차 자료(공시·감사재무제표·회사 공식 KPI)는 무엇인가? 경영진 발언은 증거가 아니다.
2. 경영진의 과거 적응은 **결과로** 확인되는가? 선언이 아니라 배치된 자본과 종료된 사업으로 확인한다.
3. 시장의 내재 기대는 무엇으로 측정했는가? reverse DCF, 컨센서스 성장 지속기간, terminal 가정 중 무엇을 썼는지 밝힌다.
4. 기대차가 **반증 가능**한가? 어떤 관측이 나오면 논지가 틀렸다고 인정하는지 먼저 쓴다.

**Skeptic — 기각 경로**
1. TAM 환상 — 총시장이 크다는 것과 회사가 가져갈 수 있다는 것은 다르다.
2. 일시적 성장의 외삽 — 공급 부족, 일회성 수요, 경기 사이클을 구조적 성장으로 오인하지 않았는가.
3. 성장의 질 — 보조금·인수·회계 인식 변경이 성장의 상당 부분을 만들고 있지 않은가.
4. 문화의 관료화 — 규모가 커지며 적응력이 실제로 떨어지고 있지 않은가.
5. 단일 의존 — 단일 제품·고객·규제 체제에 기대고 있지 않은가.
6. 숨은 Bull — Base 시나리오가 사실상 Bull을 요구하고 있지 않은가. 그렇다면 기대차가 아니라 이미 반영된 낙관이다.

## 금지 사항
- TAM이 크다는 이유만으로 `opportunity_scale_5y`에 높은 점수를 주지 않는다.
- "시장이 단기적이다"라는 일반론으로 `market_misperception` 점수를 주지 않는다. 구체적으로 **무엇을** 과소평가하는지 특정하지 못하면 50 이하다.
- 경영진의 홍보성 주장을 독립 증거로 취급하지 않는다.
- 창업자 지배를 `culture_adaptability` 고득점과 자동으로 동일시하지 않는다.
- **5배 가능성을 5배 확률로 취급하지 않는다.** 가능성은 경로의 존재이고 확률은 별개의 추정이다.
- 주가 모멘텀을 증거로 쓰지 않는다.
- 서사가 매력적이라는 이유로 점수를 만들지 않는다.

## 채점
[`config/calibration.json`](../../config/calibration.json)의 `rubrics.long_term_growth`를 따른다. 네 criterion을 정확히 한 번씩 5점 단위로 채점하고 `score_0_100`은 고정 가중평균(30/30/20/20)과 일치해야 한다.

`opportunity_scale_5y`와 `growth_duration_10y`는 관측표가 있고 `band_centre` 보간을 쓴다. 사용한 지표값(확장 배수 / 활주로 연수)과 보간 결과를 rationale에 함께 적는다. **정성 조건은 보간 대상이 아니라 상한 게이트다** — 해당 행의 정성 서술(점유율 현실성, 성장 벡터 복수성, terminal 마진 타당성, 침투율, 기회 갱신)을 충족하지 못하면 그 행을 주장할 수 없고 한 단계 아래 행으로 내린다.

`culture_adaptability`와 `market_misperception`은 형용사 앵커만 쓰며 보간하지 않는다. `anchor_policy.observed_divergence`가 기록한 대로 판단형 criterion이 프로바이더 분산의 진원지이기 때문이다. 어느 앵커 구간을 골랐고 인접 구간을 왜 배제했는지 각각 한 문장으로 적는다.

상단 게이트가 그대로 적용된다 — 85 이상은 해당 criterion을 직접 뒷받침하는 1차 자료 근거가 3개 이상이고 가장 강한 반대근거를 명시적으로 반박했을 때만 부여한다.

## 출력
`counterevidence`와 `falsifiers`를 반드시 채운다. 반증조건은 결론보다 먼저 쓴다. 확보하지 못한 관측은 `unknowns`에 남기고 0으로 처리하지 않는다.

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
        "id": "opportunity_scale_5y",
        "weight": 0.3,
        "question": "5년 내 사업이 대략 2배 이상으로 커질 수 있는가 (비상식적 점유율·마진·인수 가정 없이)",
        "anchors": {
          "25": "5년 확장 배수 1.5배 미만. 성숙·축소 시장이거나 성장이 주로 가격·인수에 의존한다.",
          "50": "1.5~2.0배가 타당. 상당한 실행력이나 점유율 확보가 필요하고 TAM은 충분하나 뚜렷이 확장 중은 아니다.",
          "75": "2배 이상이 신뢰 가능. 침투 여력·카테고리 성장·신제품이 뒷받침하며 비현실적 점유율을 요구하지 않는다.",
          "90": "3배 이상이 신뢰 가능. TAM 자체가 확장되거나 창출되고, 독립적인 성장 벡터가 복수이며, 영웅적 terminal 마진을 요구하지 않는다."
        },
        "observable_anchors": {
          "metric": "비상식적 가정 없이 타당한 5년 매출·경제가치 확장 배수",
          "period": {
            "basis": "5y_forward",
            "rationale": "기준일로부터 5년 전망 배수. 과거 실적 배수가 아니다."
          },
          "table": [
            {
              "test": "1.5배 미만",
              "score": 25,
              "hi": 1.5
            },
            {
              "test": "1.5~2.0배",
              "score": 50,
              "lo": 1.5,
              "hi": 2.0
            },
            {
              "test": "2.0~3.0배",
              "score": 75,
              "lo": 2.0,
              "hi": 3.0
            },
            {
              "test": "3.0배 이상",
              "score": 90,
              "lo": 3.0
            }
          ],
          "qualitative_gates": [
            "해당 행의 정성 조건(점유율 현실성, 성장 벡터 복수성, terminal 마진 타당성)을 충족하지 못하면 그 행을 주장할 수 없고 한 단계 아래 행으로 내린다."
          ],
          "interpolation": {
            "mode": "band_centre",
            "metric_direction": "increasing",
            "note": "확장 배수는 연속량이므로 행간 보간한다. 밴드 중앙은 표 값과 같다. 정성 조건은 보간 대상이 아니라 상한 게이트다."
          }
        }
      },
      {
        "id": "growth_duration_10y",
        "weight": 0.3,
        "question": "향후 몇 년간 고부가 성장이 지속될 수 있는가",
        "anchors": {
          "25": "활주로 3년 미만. 포화·경기민감·제품사이클 의존이 뚜렷하다.",
          "50": "3~5년 활주로는 타당하나 그 이후 지속 여부가 매우 불확실하다.",
          "75": "5~10년 활주로가 신뢰 가능. 침투율이 낮거나 중간이고 제품·지역·고객 성장 벡터가 둘 이상이다.",
          "90": "10년 초과 구조적 활주로가 타당. 낮은 침투율 + 확장하는 TAM + 반복적 혁신으로 기회가 소진되지 않고 갱신된다."
        },
        "observable_anchors": {
          "metric": "고부가 성장이 지속될 수 있는 연수",
          "period": {
            "basis": "forward_years",
            "rationale": "기준일로부터의 전망 연수."
          },
          "table": [
            {
              "test": "3년 미만",
              "score": 25,
              "hi": 3
            },
            {
              "test": "3~5년",
              "score": 50,
              "lo": 3,
              "hi": 5
            },
            {
              "test": "5~10년",
              "score": 75,
              "lo": 5,
              "hi": 10
            },
            {
              "test": "10년 초과",
              "score": 90,
              "lo": 10
            }
          ],
          "qualitative_gates": [
            "침투율·성장 벡터 개수·기회 갱신 여부가 해당 행의 서술과 맞지 않으면 한 단계 아래 행으로 내린다."
          ],
          "interpolation": {
            "mode": "band_centre",
            "metric_direction": "increasing",
            "note": "활주로 연수는 연속량이므로 행간 보간한다."
          }
        }
      },
      {
        "id": "culture_adaptability",
        "weight": 0.2,
        "question": "조직이 반복적으로 적응·자기파괴하고 장기 성장에 인재·자본을 재배치할 수 있는가",
        "anchors": {
          "25": "관료적이거나 제국 건설형 문화. 반복되는 전략 표류, 단기 외형을 좇는 보상, 제도적 깊이 없는 과도한 핵심인물 의존.",
          "50": "유능한 실행과 평범한 보상 정렬. 중대한 적응에 성공한 증거는 제한적이다.",
          "75": "자기파괴에 성공한 증거, 장기 보상 정렬, 빠른 자원 재배치, 높은 인재 밀도 또는 창업자적 주인의식.",
          "90": "주요 기술·사업 전환을 가로질러 반복적으로 재창조에 성공. 이례적으로 강한 미션 지향, 레거시 제품을 스스로 잠식한 실적, 조직이 커져도 유지되는 적응 문화."
        },
        "scoring_guardrails": [
          "창업자 지배를 높은 점수와 자동으로 동일시하지 않는다. 경영진의 자기서술은 독립 증거가 아니다."
        ]
      },
      {
        "id": "market_misperception",
        "weight": 0.2,
        "question": "시장이 과소평가하고 있을 구체적인 장기 사실은 무엇인가",
        "anchors": {
          "25": "논지가 일반적(\"AI가 성장한다\", \"TAM이 크다\"). 시장이 이미 유사하거나 더 낙관적인 가정을 반영한 것으로 보이며 반증 가능한 기대차가 없다.",
          "50": "타당한 이견은 있으나 시장의 내재 기대에 대한 증거가 약하다.",
          "75": "구체적이고 반증 가능한 기대차가 존재한다. 성장 지속기간·TAM 확장·마진 궤적·제품 옵셔널리티·경쟁우위 강화 중 무엇을 과소평가하는지 특정되고 reverse DCF 또는 컨센서스 프레이밍이 증거를 제공한다.",
          "90": "시장 내재 가정이 1차 증거가 뒷받침하는 것보다 명백히 짧거나 약한 궤적을 요구한다. 복수의 독립 출처가 불일치를 뒷받침하고, 논지가 시장의 시계가 왜 짧은지를 설명한다."
        },
        "scoring_guardrails": [
          "서사적 이견만으로는 75 이상을 줄 수 없다. 시장이 단기적이라는 일반론은 기대차의 증거가 아니다."
        ]
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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "opportunity_scale_5y", "score_0_100": 50, "rationale": ""}, {"criterion_id": "growth_duration_10y", "score_0_100": 50, "rationale": ""}, {"criterion_id": "culture_adaptability", "score_0_100": 50, "rationale": ""}, {"criterion_id": "market_misperception", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate BRK.B LG`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
