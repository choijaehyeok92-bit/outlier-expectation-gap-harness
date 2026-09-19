# 과제: RKLB / 기준일 2026-09-18 / turnaround_quality (TQ)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/RKLB/reports/TQ.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"RKLB","company_name":"Rocket Lab Corporation","as_of_date":"2026-09-18","currency":"USD","current_price":64.57,"shares_diluted":627650482,"market_cap_usd":40527391622.74,"enterprise_value":41170000000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded Rocket Lab FY2025 Form 10-K filed 2026-02-26","User-uploaded Rocket Lab Q1 FY2026 Form 10-Q filed 2026-05-07","User-uploaded Rocket Lab Q2 FY2026 Form 10-Q filed 2026-08-10","User-uploaded Rocket Lab Form 8-K filed 2026-09-15","Rocket Lab Q2 2026 earnings release dated 2026-08-10","Rocket Lab/Iridium transaction materials and SEC pro forma information","2026-09-18 closing price $64.57 from historical market data"],"special_questions":["Can Rocket Lab evolve from launch and space-hardware manufacturing into a vertically integrated recurring space-services platform after Iridium?","Does Neutron create a credible second growth engine without forcing structurally excessive capital consumption?","Do the 2025-2026 ATM issuances and pending Iridium stock consideration create excessive per-share dilution despite strategic asset acquisition?"],"net_cash_per_share":-1.15,"valuation_metric":"Transaction-adjusted valuation. Raw pre-close liquidity is strongly net-cash, but most September ATM proceeds are earmarked for the pending Iridium acquisition; DCF uses approximately -$1.15/share post-deal economic net cash/debt to avoid double-counting acquisition financing.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# RKLB frozen source bundle — as of 2026-09-18

## Frozen market / transaction inputs
- 2026-09-18 close: **$64.57**.
- Shares outstanding on 2026-08-05: **598.350M**.
- Completed Sep-2026 replacement ATM: **29.3M shares**, **$1.944B gross proceeds**.
- Estimated current shares after the completed ATM: **~627.65M**.
- Current market cap signal: **~$40.53B**, below the harness $50B Moonshot cap.
- Q2 cash + current/non-current marketable securities: **$2.388B**.
- Q2 debt/borrowings: about **$14.8M** before the Iridium transaction.
- Raw pre-close liquidity plus Sep ATM is strongly net-cash, but most ATM proceeds are earmarked for Iridium cash consideration.
- Transaction-adjusted economic net cash/debt used in DCF: **-$1.15/share**.
- Iridium transaction: **$54/share**, approx **$8.0B enterprise value**, expected mid-2027 close.
- Iridium consideration: **$27 cash + RKLB shares**, exchange-ratio collar $67.50-$112.50; at current price below the floor, the ratio would be 0.4000 if closing price mechanics were unchanged.
- Iridium existing **$1.775B** term loan is permitted to remain outstanding after closing; the former $3.6B bridge was terminated.
- Required return: **9%**; horizon **10 years**; terminal multiples **15x/20x/25x**.
- Owner-FCF/share paths, transaction-adjusted and post-deal diluted-economics:
  - Bear: -0.2, 0.0, 0.2, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2
  - Base: 0.0, 0.4, 0.8, 1.4, 2.2, 3.2, 4.4, 5.7, 7.0, 8.5
  - Bull: 0.2, 0.8, 1.6, 2.8, 4.5, 6.5, 8.8, 11.5, 14.5, 18.0
- Locked DCF: Bear **$17.41**, Base **$88.03**, Bull **$224.68**.
- price/Base: **~0.7335**.
- Bull/current: **~3.48x**.
- Bear/current: **~0.27x**.

## FY2025 10-K
- Revenue **$601.799M**, +38% y/y.
- Launch Services revenue **$199.042M**; Space Systems revenue **$402.757M**.
- Gross profit **$207.181M**.
- Net loss **$198.209M**.
- OCF **-$165.521M**.
- Purchases of property, equipment and software **$156.285M**.
- SBC expense **$71.099M**.
- 21 Electron launches in 2025 vs 16 in 2024.
- Government customer represented **28%** of FY2025 revenue.
- 2025 ATM proceeds **$1.146B** gross before issuance costs.
- Management concluded ICFR effective; no correction/restatement flag.

## Q2 / H1 2026
- Q2 revenue **$234.1M**, +62% y/y.
- Q2 backlog **$2.36B**, +137% y/y.
- More than **$437M** of new launch contracts across Electron, HASTE and Neutron during Q2 plus post-quarter signings; launch backlog >90 missions.
- Six-month net loss **$94.280M**.
- H1 OCF **-$134.407M**.
- H1 capex/property/equipment/software purchases **$53.112M**.
- H1 SBC **$47.677M**.
- Q2 cash **$2.129B**; current marketable securities **$172.7M**; non-current marketable securities **$85.4M**.
- Shares outstanding at June 30 **598.180M** and at Aug 5 **598.350M**.
- Pending Iridium transaction expected to require >$3B cash consideration/fees and additional Iridium debt financing/refinancing needs.

## Iridium transaction / Sep-15 financing
- Rocket Lab agreed to acquire Iridium for **$54/share**, approx **$8.0B EV**.
- Iridium 2025 revenue **$871.7M**, OEBITDA **$495.3M**, capex **$100.3M**.
- Sep 15: completed **$1.944B ATM**, issuing **29.3M shares**.
- Iridium's **$1.775B** existing term loan was amended to remain outstanding after change of control.
- Initial **$3.6B bridge facility terminated**.
- Rocket Lab stated the ATM proceeds, amended Iridium facility and available liquidity are sufficient for anticipated closing cash payments.

공시 원문: runs/RKLB/sources/*.txt — runs/RKLB/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 독립성
runs/RKLB/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 TQ (domain_analyst)
# Turnaround Quality Analyst

- `agent_id`: `TQ`
- `domain`: `turnaround_quality`

## 임무
저점 실적 기업의 회복이 단순한 주가 반등·가이던스·경기순환이 아니라 **검증 가능한 운영 턴어라운드**인지 판정한다. 이 축은 100점 핵심 점수에 합산하지 않고 Turnaround archetype 분류와 IC 판단에 사용한다.

## 핵심 질문

### Bull 관점
1. 매출, gross/operating margin, FCF, 수주, 재고, 고객 유지율 등 핵심 KPI 중 최소 2개가 실제 분기 실적에서 저점 대비 개선되는가?
2. 비용 구조조정, 가격, 제품믹스, 공급망, 자산매각, 부채축소, 비핵심사업 철수 등 경영진이 통제 가능한 self-help가 회복의 주된 원인인가?
3. 정상화 실적은 과거 피크마진이 아니라 보수적 매출·마진 가정으로 설명되는가?
4. 6~24개월 내 확인 가능한 촉매와 KPI, 책임자, 일정이 있는가?

### Skeptic 관점
1. 회복이 원자재 가격, 금리, 환율, 재고 재축적, 산업 공급감소 등 외생적 사이클에 지나치게 의존하는가?
2. EPS는 개선되지만 FCF, 운전자본, 순부채, 주식수는 악화되는가?
3. 구조조정 비용 절감이 성장투자 축소나 미래 경쟁력 훼손의 대가인가?
4. “정상화”가 과거 피크 수익성 회귀를 암묵적으로 가정하는가?
5. 자산매각·증자·리파이낸싱 없이는 회복 기간을 버틸 수 없는가?

## 판정 원칙
- **가이던스보다 실제 분기 실적을 우선**한다.
- 한 분기 반등만으로 75점 이상을 주지 않는다. 원칙적으로 서로 다른 2개 이상 KPI에서 2개 분기 이상의 개선 증거가 필요하다.
- 단순 업황 반등은 turnaround로 보지 않는다. self-help가 회복의 독립적 동력이어야 한다.
- 정상화 bridge는 매출, 마진, capex, 운전자본, SBC, 이자비용을 포함해 FCF/share로 연결한다.
- 비용 절감은 매출·고객·제품 경쟁력 훼손 여부를 함께 본다.
- 높은 부채 기업은 `financial_survival`과 충돌하지 않도록 만기·이자·유동성 runway를 명시한다.
- Turnaround 점수 75 이상이어도 Hard Veto가 있으면 IC에서 매수 승인할 수 없다.

## 턴어라운드 단계
보고서 thesis에 현재 단계를 다음 중 하나로 명시한다.
- **T0 Deteriorating**: 악화 지속
- **T1 Stabilizing**: 하락 멈춤, 아직 회복 미확인
- **T2 Inflecting**: 2개 이상 KPI가 실제 실적에서 개선
- **T3 Recovering**: FCF/마진/부채가 함께 개선, 정상화 bridge 가시화
- **T4 Re-rated**: 정상화가 상당 부분 실현되어 더 이상 턴어라운드 기대차가 핵심이 아님

## 특별 경고
다음은 높은 점수를 주기 위한 근거가 아니다.
- 주가가 많이 하락했다.
- 컨센서스가 낮다.
- 경영진이 “하반기 회복”을 말했다.
- 구조조정 발표만 했다.
- 업황이 좋아질 것이라는 매크로 전망만 있다.

## 출력 해석
- 85+: T3에 가까운 검증된 회복. 여러 KPI와 FCF/share가 동시 개선.
- 75~84: T2 이상. 실제 inflection + self-help + 정상화 bridge가 충분.
- 60~74: 회복 가능성은 있으나 T1/T2 경계. 핵심 증거 미완성.
- <60: 서사적 턴어라운드 또는 외부 사이클 의존.

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
        "id": "operating_inflection",
        "weight": 0.35,
        "question": "매출·마진·FCF·재고·수주 등 핵심 지표가 저점 대비 실제로 개선되고 있는가?",
        "anchors": {
          "25": "가이던스뿐이거나 악화 지속",
          "50": "한두 지표의 초기 안정화",
          "75": "2개 이상 핵심 지표의 2개 분기 개선",
          "90": "광범위한 실적 회복과 현금흐름 전환 확인"
        }
      },
      {
        "id": "self_help_quality",
        "weight": 0.3,
        "question": "회복이 경영진이 통제 가능한 비용·가격·제품믹스·자산매각·부채축소·운영개선에서 오는가?",
        "anchors": {
          "25": "외부 경기·원자재·금리 반등 의존",
          "50": "외부환경과 self-help 혼재",
          "75": "측정 가능한 self-help가 주요 동력",
          "90": "구조개선이 단위경제·자본효율을 재설계"
        }
      },
      {
        "id": "normalized_earnings_bridge",
        "weight": 0.2,
        "question": "저점 실적에서 정상화 FCF/share·마진으로 가는 수치적 bridge가 보수적 가정으로 설명되는가?",
        "anchors": {
          "25": "피크마진·낙관 매출 없이는 성립 불가",
          "50": "정상화 경로가 있으나 핵심 가정 다수",
          "75": "보수 매출·마진으로 정상화 가치 설명",
          "90": "이미 상당 부분 실현되고 추가 개선이 확인 가능"
        }
      },
      {
        "id": "catalyst_accountability",
        "weight": 0.15,
        "question": "6~24개월 내 재평가 촉매와 경영진의 공개 KPI·마감기한·보상 정렬이 있는가?",
        "anchors": {
          "25": "촉매·책임주체 불명확",
          "50": "계획은 있으나 일정/지표 약함",
          "75": "구체 KPI·일정·책임자 존재",
          "90": "분기별 이행 실적과 강한 이해관계 정렬"
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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "operating_inflection", "score_0_100": 50, "rationale": ""}, {"criterion_id": "self_help_quality", "score_0_100": 50, "rationale": ""}, {"criterion_id": "normalized_earnings_bridge", "score_0_100": 50, "rationale": ""}, {"criterion_id": "catalyst_accountability", "score_0_100": 50, "rationale": ""}]}
작성 후 `python harness.py validate RKLB TQ`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
