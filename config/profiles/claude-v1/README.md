# claude-v1 — 재보정 프로필 (현재 `config/`에 **적용됨**)

이 디렉터리는 현재 `config/`에 적용된 캘리브레이션의 사본입니다.
gpt-5.6-sol이 작성한 원본은 `config/profiles/_original/`에 그대로 보존되어 있습니다.

```bash
bash config/profiles/claude-v1/revert.sh   # 원본(gpt-5.6-sol)으로 되돌리기
bash config/profiles/claude-v1/apply.sh    # 다시 claude-v1로
```

`revert.sh`로 원본을 복원하면 `harness.py selftest`는 계속 통과합니다.
반대로 원본 config는 `state_thresholds` 블록이 없으므로, 되돌린 뒤에는 `strategy.json`에
그 블록을 직접 추가해야 `aggregate`가 동작합니다. 되돌릴 때는 아래 4-1을 먼저 읽으십시오.

---

## 0. 무엇이 문제였나

"기준이 지나치게 높다"를 NVDA 실행으로 검증한 결과, 절반은 맞았고 절반은 다른 문제였습니다.

**EV 49.25는 하네스가 만든 값이 아니었습니다.** subscores 55/50/40의 고정 가중합이고 그 값은 모델 판단입니다.
하네스 기여분은 DCF 정책(9% 할인, 15/20/25x)뿐이며 그 정책은 오히려 관대한 쪽입니다.
따라서 "기준이 높다"가 성립하려면 문제가 다른 곳에 있어야 했고, 실제로 세 곳에 있었습니다.

1. **루브릭이 같은 사실을 두 번 깎았다.** `reverse_dcf_burden`의 앵커는 이미 "현재가가 Base를 요구하는가"로
   정의돼 있습니다. NVDA는 price/Base = 1.03이니 앵커상 75 구간인데, 모델이 그 위에 "그 Base 자체가
   야심적이다"를 한 번 더 적용해 55로 내렸습니다. → 두 criterion을 `price_to_base_value`에 결정론적으로 고정.
2. **AS는 메가캡에 구조적으로 닫혀 있었다.** `upside_path`가 5x/10x라는 절대 배수를 물어서 시총 수조 달러
   기업은 40점 위로 못 갑니다. → 앵커를 규모 상대 기준으로 재정의.
3. **archetype이 노이즈를 허용하지 않는 5중 AND였다.** → 임계값을 판단 노이즈만큼 하향.

---

## 1. 지시 반영 내역

### 지시 1 — 상태 임계값을 config로 이관 (코드 수정 포함)

상태 임계값과 상태별 비중이 `harness.py`에 하드코딩돼 있어 config로는 게이트를 바꿀 수 없었습니다.
`strategy.json`의 `state_thresholds`가 소유하도록 옮기고 동시에 전 구간을 낮췄습니다.

| 상태 | 기존(하드코딩) | claude-v1 | 비중 |
|---|---|---|---|
| EXCEPTIONAL_WINNER_CANDIDATE | ≥90 | **≥86** | 6-10% (IC cap) |
| CORE_WINNER_CANDIDATE | ≥85 | **≥80** | 4-8% |
| NORMAL_CANDIDATE | ≥75 | **≥70** | 2-4% |
| STARTER_OR_WATCH | ≥65 | **≥60** | 0-2% |
| REJECT | <65 | **<60** | 0% |

`harness.py` 변경: `BUY_STATES`·상태 분기·비중 dict가 모두 config를 읽습니다. selftest에
`state_thresholds` 정합성 검사(내림차순, 마지막 min=0, buy_states가 선언된 band를 가리킬 것)를 추가했고,
moonshot 시총 상한도 상수 대신 config에서 읽도록 고쳤습니다.

`classifications`도 같은 구간(86/80/70/60)으로 맞췄습니다. 라벨은 원본 그대로 둡니다 —
점수구간의 `Emerging Outlier`는 archetype과 이름만 같을 뿐 다른 개념이고, 삭제 지시는 archetype에만 해당합니다.

### 지시 2 — RUNBOOK의 허위 기술 삭제

`RUNBOOK.md`는 "도메인 점수에는 미확인·분쟁·신뢰도 패널티가 적용된다"고 적고 있었으나, v2.1 이후
루브릭 경로에서는 `harness.py`가 세 패널티를 모두 0으로 두고 있어 사실이 아니었습니다.
코드를 바꾸지 않고 문서를 사실에 맞췄습니다.

> 도메인 점수는 `subscores`의 고정 가중평균이며 **감점을 적용하지 않는다**. 미확인·분쟁·신뢰도는 점수를
> 바꾸지 않고 `review_required`·`domain_dispute`·`uncertainties` 플래그로만 기록된다.

§3의 "20 이상 분쟁, 30 이상 재조사"에도 "표시일 뿐 점수는 깎이지 않는다"를 명시했습니다.

### 지시 3 — 점수 판정 기준 전반 완화

상태 임계값(위 표) 외에 archetype 조건을 전반 하향했습니다.

| 유형 | 조건 | 기존 → claude-v1 |
|---|---|---|
| compounder | moat_trajectory / reinvestment_fcf | 80 → **76** |
| compounder | management_allocation / financial_survival | 75 → **72** |
| compounder | expectation_valuation | 50 → **42** |
| moonshot | market_cap_usd | $20B → **$50B** |
| moonshot | disruptive_innovation | 80 → **78** |
| moonshot | structural_leadership / asymmetry | 75 → **72** |
| turnaround | turnaround_quality | 75 → **72** |
| turnaround | expectation_valuation / asymmetry | 65 → **62** |
| expectation_gap | price_to_base_value | ≤0.80 → **≤0.85** |
| expectation_gap | valuation_percentile_5y | ≤0.30 → **≤0.35** |
| expectation_gap | revenue_cagr_next_3y | 3~20% → **3~25%** |
| expectation_gap | expectation_valuation | 75 → **65** |
| (공통) | min_gate_score | 65 → **60** |

### 지시 4 — 이머징 아웃라이어 삭제

컴파운더와 실질 구분이 없어 **`archetypes.types`(종목 유형 분류 기준)에서만** 제거했습니다.
`classifications`의 점수구간 라벨 `Emerging Outlier`(70~79.999)는 archetype과 별개 개념이므로 그대로 둡니다.
함께 정리한 곳:
`schemas/final_verdict.schema.json`의 enum, `config/workflow.json`의 phase 5 목록,
`README.md` 유형표, `AGENTS.md`, `ARCHITECTURE.md`, `templates/one_page_investment_record.md`,
`agents/12_investment_committee/AGENTS.md`.

### 지시 5 — 컴파운더에 price/Base ≤ 1.2 추가

삭제한 emerging_outlier의 가격 밴드 상단을 컴파운더가 이어받습니다.
아무리 좋은 기업도 Base 가치의 1.2배를 넘으면 컴파운더로 분류하지 않습니다.

**함께 조정한 이유 — 안 그러면 새 규칙이 무효가 됩니다.** EV `signal_map`에서 price/Base 1.1~1.3 구간의
EV 상한은 약 47입니다. 기존 조건 `expectation_valuation ≥ 50`을 그대로 두면 price/Base 1.1 부근에서
이미 막혀 1.2 규칙이 한 번도 구속하지 못합니다. 그래서 EV 조건을 **42**로 낮췄습니다.
price/Base > 1.3이면 EV가 42 미만이 되어 여전히 차단됩니다.

### 지시 6 — 자료 공백의 능동 보완

기존 규칙은 "확인할 수 없는 데이터는 `unknown`으로 기록한다"로 수동적이었습니다.
`config/workflow.json`에 `execution.research_policy`(mode: `active_gap_filling`)를 신설하고
`harness.py`의 `cmd_prompt`가 이를 모든 에이전트 프롬프트에 자동으로 싣도록 했습니다.
웹 검색 예산은 에이전트당 10회 → **15회**로 올렸습니다(지시하면서 예산을 그대로 두면 상충하므로).

`agents/COMMON.md`도 같은 내용으로 교체했습니다: 먼저 찾고, 못 찾은 것만 `unknowns`에 남기되
**무엇을 어디서 찾으려 했는지** 함께 적고, 2차 자료로 채운 값은 `fact_or_estimate`를
`estimate`/`interpretation`으로 표기합니다.

### 추가 — Veto 담당자 보강 (유일한 강화)

`현재가격이 비현실적인 Bull Case 이상을 요구`의 담당을 `[EV, AS]` → **`[EV, AS, RT]`**.
가격 내재 기대는 Red Team의 핵심 렌즈인데 담당에서 빠져 있었습니다.
NVDA run에 적용하자 즉시 `RT: owned veto not explicitly assessed`로 걸렸고, RT 판정을 받아 해소했습니다.

---

## 2. NVDA 2026-09-17 실행에 적용한 결과

| | 원본 | claude-v1 |
|---|---|---|
| EV | 49.25 | **53.00** |
| AS | 52.75 | **61.50** |
| 종합점수 | 68.92 | **70.36** |
| classification | Starter / Watch | **Emerging Outlier** (70~79.999 구간) |
| compounder 미달 | 4개 조건 | **2개** — MT 73.75(<76), MA 71.75(<72) |
| archetype | non_fit | **non_fit** |
| 상태 / 비중 | WATCH / 0% | **WATCH / 0%** |

**임계값을 전 구간 낮추고 이중 감점까지 제거했는데 판정이 바뀌지 않았습니다.**
구속 조건이 점수 임계값이 아니라 Hard Veto 게이트(UNRESOLVED)이기 때문입니다.
미해소 3건은 모두 "NVIDIA가 지분투자·보증한 주체의 매출 비중"이라는 단일 미공시 수치에 걸려 있고,
어떤 숫자를 조정해도 풀리지 않습니다.

MA는 임계값 72에 **0.25점** 모자라 탈락했습니다. 5중 AND가 경계에서 여전히 취약하다는 뜻이며,
`final_verdict.archetype_rationale`에 경계 판정으로 기록해 두었습니다.

---

## 3. 이제 config가 소유하는 것 / 여전히 코드에 있는 것

| | 위치 |
|---|---|
| 상태 임계값·상태별 비중·buy_states | ✅ `strategy.json.state_thresholds` |
| archetype 조건·게이트 점수 | ✅ `strategy.json.archetypes` |
| 점수구간 라벨 | ✅ `strategy.json.classifications` |
| 루브릭 criterion·가중치·앵커·signal_map | ✅ `calibration.json.rubrics` |
| 밸류에이션 정책(할인율·terminal·horizon) | ✅ `calibration.json.valuation` |
| Veto 담당자 | ✅ `calibration.json.veto_reviewers` |
| 조사 예산·능동 보완 정책 | ✅ `workflow.json.execution` |
| 스코어카드 가중치 | ✅ `strategy.json.scorecard` |
| 분쟁 임계(20/30)와 패널티 계수 | ❌ `harness.py:223-230` — 단, 루브릭 경로에서는 전부 0이라 무의미 |

---

## 4. 검토했으나 적용하지 않은 권고 (의견 차이)

**terminal multiples 15/20/25는 그대로 두었습니다.** 할인율 9%에서 이 배수들의 내재 영구성장률은
각각 **2.3% / 4.0% / 5.0%**입니다. Bull의 5.0%는 장기 명목 GDP를 영구히 상회한다는 뜻이라
이론적으로 성립하지 않습니다. 정합적인 값은 대략 **14 / 18 / 22**(내재 g 1.9% / 3.4% / 4.4%)입니다.

적용하지 않은 이유는 이것이 **가치를 낮추는 강화 방향**이고 요청하신 완화 방향과 반대이기 때문입니다.
NVDA에 적용하면 Base 주당가치가 $212.86 → 약 $199로 내려가 price/Base가 1.10을 넘고,
signal_map 밴드가 한 칸 내려가 EV가 53.00 → 41.75가 됩니다. 그러면 새로 넣은 컴파운더
`EV ≥ 42` 조건에도 걸립니다. 적용하시려면 `calibration.json`의
`valuation.terminal_multiples` 세 값만 고치면 됩니다.

### 4-1. 되돌릴 때 주의

`revert.sh`는 원본 3종을 그대로 복사합니다. 원본 `strategy.json`에는 `state_thresholds` 블록이 없으므로,
되돌린 직후 `aggregate`는 `KeyError: 'state_thresholds'`로 실패합니다. 원본으로 완전히 돌아가시려면
`harness.py`도 이 커밋 이전으로 함께 되돌리거나, 원본 `strategy.json`에 `state_thresholds` 블록만
복사해 넣으십시오. 같은 이유로 원본 `workflow.json`에는 `research_policy`가 없어 `prompt`도 실패합니다.

---

## 5. 파일

```
config/profiles/claude-v1/   # 현재 config/와 동일한 사본
  strategy.json  calibration.json  workflow.json
  CHANGES.json   # 46건 기계 판독용 변경 목록
  README.md  apply.sh  revert.sh
config/profiles/_original/   # gpt-5.6-sol 원본 3종
runs/NVDA/aggregate.claude-v1.json   # 중간 검증용 (지시 1~6 반영 전)
```
