# 과제: VRT / 기준일 2026-09-18 / structural_leadership (SL)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/VRT/reports/SL.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"VRT","company_name":"Vertiv Holdings Co","as_of_date":"2026-09-18","currency":"USD","current_price":249.39,"shares_diluted":392746991,"market_cap_usd":97947172085.49,"enterprise_value":97776372085.49,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["SEC Form 10-K FY2025 filed 2026-02-13","SEC Form 10-Q Q1 2026 filed 2026-04-22","SEC Form 10-Q Q2 2026 filed 2026-07-29","SEC 8-K filed 2026-09-02 announcing UtilityInnovation Group acquisition agreement","SEC 424B5 filed 2026-02-25","SEC Form 4 filed 2026-09-16","StockAnalysis historical close 2026-09-18: $249.39"],"special_questions":["How durable is AI-data-center power and thermal infrastructure demand once current hyperscaler capex normalizes?","Can Vertiv convert the $15B+ backlog and capacity expansion into sustained high incremental ROIC without working-capital or execution deterioration?","How should the $1.45B upfront UIG acquisition and up to $1.15B contingent consideration affect net-cash, capital-allocation and valuation risk?","Does liquid cooling, power management and behind-the-meter microgrid expansion widen Vertiv's systems-level moat or increase M&A/integration risk?"],"net_cash_per_share":0.4348855724269565,"valuation_metric":"Locked owner-FCF/share DCF. Five-year historical multiple percentile left null because Vertiv's AI-data-center growth, margin structure and capital allocation changed materially over the period.","valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"revenue_by_region":{"Americas":0.62,"Asia Pacific":0.2,"Europe, Middle East & Africa":0.18}}}

## 독립성
runs/VRT/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 SL (domain_analyst)
# Structural Leadership Analyst

- `agent_id`: `SL`
- `domain`: `structural_leadership`

## 임무
산업의 구조적 변화가 실재하며 5~10년 지속되는지, 회사가 그 변화의 단순 수혜자가 아니라 카테고리와 경쟁기준을 바꾸는 리더인지 검증한다.

## 관점별 질문
**Bull — 구조적 변화와 리더십**
1. 성장이 경기순환·기저효과가 아니라 기술·규제·비용곡선 변화에서 오는가? 가치풀이 장기적으로 커지는가?
2. 점유율과 그 변화는? 카테고리 정의·가격·표준·유통구조에 영향력을 행사하는가?
3. 경쟁사 대비 제품 로드맵과 배포능력은? 시장 확대 자체를 촉진하는가?

**Skeptic — 사이클과 TAM**
1. TAM 산정이 실제 지불의사와 연결되는가?
2. 최근 성장은 가격·믹스·재고축적·보조금 중 무엇의 영향인가? 정상화 시 매출·마진은?
3. 5~10년 후 성장률을 훼손할 포화·대체·규제 요인은? 시장 성장이 멈춰도 점유율을 얻을 수 있는가?

## Hard Veto 중점
- 고객가치 없이 마케팅·보조금에 의존하는 성장

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
        "id": "secular_durability",
        "weight": 0.4,
        "question": "구조 변화의 5~10년 지속성",
        "anchors": {
          "25": "사이클 중심",
          "50": "구조·사이클 혼재",
          "75": "장기 수요/지불의사 확인",
          "90": "비용곡선·표준·수요 재편"
        }
      },
      {
        "id": "category_leadership",
        "weight": 0.35,
        "question": "경쟁기준·표준·배포 리더십",
        "anchors": {
          "25": "추종자",
          "50": "유의미 참여자",
          "75": "리더십 입증",
          "90": "카테고리 규칙 정의"
        }
      },
      {
        "id": "durability_risks",
        "weight": 0.25,
        "question": "포화·대체·규제 이후 회복력",
        "anchors": {
          "25": "단일 취약점 지배",
          "50": "상쇄요인 혼재",
          "75": "복수 완충장치",
          "90": "여러 독립 성장축"
        },
        "observable_anchors": {
          "metric": "수요 동인이 서로 독립적인 최종시장 중 매출 10% 이상을 차지하는 것의 개수",
          "table": [
            {
              "test": "0개 — 단일 수요 동인이 매출의 80% 이상",
              "score": 45
            },
            {
              "test": "1개",
              "score": 60
            },
            {
              "test": "2개",
              "score": 75
            },
            {
              "test": "3개 이상",
              "score": 85
            }
          ],
          "modifiers": [
            "실현된 최대 단일 리스크(규제·수출통제·대형 고객 이탈)를 매출 감소 없이 흡수한 이력이 1차 자료로 확인되면 +10 (상한 90)"
          ],
          "interpolation": {
            "mode": "none",
            "reason": "최종시장 개수(이산). 개수 사이의 값은 존재하지 않는다."
          }
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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "secular_durability", "score_0_100": 50, "rationale": ""}, {"criterion_id": "category_leadership", "score_0_100": 50, "rationale": ""}, {"criterion_id": "durability_risks", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate VRT SL`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
