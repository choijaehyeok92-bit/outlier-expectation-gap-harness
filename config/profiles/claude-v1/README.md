# claude-v1 — 재보정 프로필

`config/`의 원본(gpt-5.6-sol 작성)을 대체하는 드롭인 프로필입니다. 원본은 `config/profiles/_original/`에
그대로 보존되어 있습니다.

```bash
bash config/profiles/claude-v1/apply.sh    # 적용
bash config/profiles/claude-v1/revert.sh   # 원복
```

적용하면 `config_files` 해시가 바뀝니다. 다른 프로필에서 채점된 run과 점수를 비교하려면
반드시 `freeze`를 다시 실행하고, `run_manifest.json`의 `config_files`가 같은지 먼저 확인하십시오.

---

## 0. 먼저 — 무엇이 실제로 문제였는가

지적하신 "기준이 지나치게 높다"를 NVDA 실행 결과로 검증했습니다. 절반은 맞고 절반은 다릅니다.

**EV 49.25는 하네스가 만든 값이 아닙니다.** subscores 55/50/40의 고정 가중합이고, 그 55/50/40은 모델의 판단입니다.
하네스가 기여한 건 DCF 정책(9% 할인, 15/20/25x)뿐이며 그 정책은 오히려 관대한 쪽입니다.
그래서 "기준이 높다"가 성립하려면 문제는 두 곳에 있어야 했고, 확인해 보니 실제로 두 곳에 있었습니다.

1. **루브릭이 같은 사실을 두 번 깎게 되어 있었다.** `reverse_dcf_burden`의 앵커는 이미 "현재가가 Base를
   요구하는가"로 정의돼 있습니다. NVDA는 price/Base = 1.03이므로 앵커상 75("Base로 충분") 구간입니다.
   그런데 모델이 그 위에 "그 Base 자체가 야심적이다"를 한 번 더 적용해 55로 내렸습니다. 같은 사실에 대한
   이중 감점입니다. → 두 criterion을 하네스가 계산한 `price_to_base_value`에 **결정론적으로 고정**했습니다.
2. **archetype 조건이 노이즈를 허용하지 않는 5중 AND였다.** 도메인 점수에는 ±3점 수준의 판단 편차가 있는데,
   컴파운더는 5개 조건을 전부 동시에 넘어야 합니다. → 임계값을 노이즈 허용폭만큼 낮췄습니다.
3. **AS는 메가캡에 대해 구조적으로 도달 불가였다.** `upside_path`가 5x/10x라는 **절대 배수**를 물어서,
   시총 수조 달러 기업은 아무리 좋아도 40점 위로 못 갑니다. `emerging_outlier`의 AS≥75가 메가캡에게
   영원히 닫혀 있던 진짜 이유입니다. → 앵커를 **규모 상대** 기준으로 재정의했습니다.

---

## 1. 변경 내역 (23건)

전체 기계 판독용 목록은 `CHANGES.json`에 있습니다.

### 1-1. 루브릭 — 이중 감점 제거 (완화)

`expectation_valuation`의 두 criterion을 하네스 산출 신호에 고정합니다. 모델 재량은
`valuation_robustness`(가중 0.25)에만 남습니다.

| price_to_base_value | reverse_dcf_burden | base_return |
|---|---|---|
| ≤ 0.70 | 90 | 85 |
| 0.70 ~ 0.90 | 75 | 70 |
| 0.90 ~ 1.10 | **60** | **55** |
| 1.10 ~ 1.30 | 45 | 40 |
| > 1.30 | 25 | 25 |

`scoring_rule`에 "Base 시나리오의 야심 수준은 `valuation_robustness`와 `uncertainties`에 기록하되
위 두 criterion에서 다시 감점하지 않는다"를 명시했습니다. 프로바이더가 바뀌어도 이 두 값은 흔들리지 않습니다.

### 1-2. 루브릭 — AS의 메가캡 천장 제거 (완화)

`asymmetry.upside_path`의 질문을 "5~10년 큰 상승 경로"에서
**"시가총액 규모를 감안한 5~10년 위험조정 상승 배수와 경로의 복수성"**으로 바꾸고 앵커를 재정의했습니다.

| | 기존 | claude-v1 |
|---|---|---|
| 25 | 비현실 | 상승 경로가 비현실적이거나 단일 낙관가정에 의존 |
| 50 | 단일 낙관가정 | 요구수익률을 겨우 넘는 경로 하나 |
| 75 | 복수 경로 | 요구수익률을 뚜렷이 상회하는 복수 경로 |
| 90 | 강한 power-law | 규모 대비 예외적 상승 배수(소형주 10x급, 대형주 3x급)와 복수 경로 |

### 1-3. archetype 임계값 (완화)

| 유형 | 조건 | 기존 → claude-v1 |
|---|---|---|
| compounder | moat_trajectory | 80 → **76** |
| compounder | reinvestment_fcf | 80 → **76** |
| compounder | management_allocation | 75 → **72** |
| compounder | financial_survival | 75 → **72** |
| compounder | expectation_valuation | 50 → 50 (유지) |
| moonshot | market_cap_usd | $20B → **$50B** |
| moonshot | disruptive_innovation | 80 → **78** |
| moonshot | structural_leadership / asymmetry | 75 → **72** |
| emerging_outlier | structural_leadership / asymmetry | 75 → **72** |
| turnaround | turnaround_quality | 75 → **72** |
| turnaround | expectation_valuation / asymmetry | 65 → **62** |
| expectation_gap | price_to_base_value | ≤0.80 → **≤0.85** |
| expectation_gap | valuation_percentile_5y | ≤0.30 → **≤0.35** |
| expectation_gap | revenue_cagr_next_3y | 3~20% → **3~25%** |
| expectation_gap | expectation_valuation | 75 → **72** |
| (공통) | min_gate_score | 65 → **63** |

`compounder`의 `expectation_valuation ≥ 50`만 유지했습니다. 이 전략의 정의가 "좋은 기업이 아니라 기대차가
큰 기업을 산다"이므로, 공정가치 아래라는 최소 요건까지 풀면 전략의 이름이 남지 않습니다.

`moonshot` 시총 상한을 $50B로 올린 근거: $20B는 테슬라(2013년 약 $20~30B)와 팔란티어(상장 시 약 $20B)
같은 이 유형의 준거 사례조차 경계에 걸립니다.

### 1-4. Veto 담당자 (강화 — 유일하게 조인 항목)

`현재가격이 비현실적인 Bull Case 이상을 요구`의 담당을 `[EV, AS]` → **`[EV, AS, RT]`**.
가격 내재 기대는 Red Team의 핵심 렌즈인데 담당에서 빠져 있어, 이 항목만 RT 검증 없이 clear될 수 있었습니다.

---

## 2. NVDA 2026-09-17 실행에 적용한 결과

| | 원본 | claude-v1 (config만) | claude-v1 (+루브릭 재채점) |
|---|---|---|---|
| EV | 49.25 | 49.25 | **53.00** |
| AS | 52.75 | 52.75 | **61.50** |
| 종합점수 | 68.92 | 68.92 | **70.36** |
| compounder 미달 조건 | 4개 | 3개 | **2개** (MT 73.75<76, MA 71.75<72) |
| emerging_outlier 미달 | 1개 (AS) | 1개 (AS) | 1개 (AS 61.50<72) |
| archetype | non_fit | non_fit | **non_fit** |
| 상태 | WATCH | WATCH | **WATCH** |
| 비중 | 0% | 0% | **0%** |

결과 파일: `runs/NVDA/aggregate.claude-v1.json`

**가장 중요한 결과는 판정이 바뀌지 않았다는 것입니다.** 임계값을 전부 낮추고 이중 감점까지 제거했는데도
NVDA는 여전히 WATCH·0%입니다. **구속 조건이 점수 임계값이 아니라 Hard Veto 게이트(UNRESOLVED)이기
때문입니다.** 미해소 3건은 모두 "NVIDIA가 지분투자·보증한 주체의 매출 비중"이라는 단일 미공시 수치에
걸려 있고, 이건 어떤 숫자를 조정해도 풀리지 않습니다. 공시가 나오거나 DSO가 정상화되어야 풀립니다.

---

## 3. config로는 바꿀 수 없는 수치 (중요)

프로필을 아무리 고쳐도 아래는 **harness.py에 하드코딩**되어 있어 움직이지 않습니다.
게이트를 실제로 완화하시려면 여기를 고쳐야 합니다.

| 위치 | 내용 | 비고 |
|---|---|---|
| `harness.py:386-389` | 상태 임계값 `>=90 / >=85 / >=75 / >=65` | `config/strategy.json`의 `classifications`는 **라벨만** 바꿉니다. 실제 게이트는 여기입니다. |
| `harness.py:394` 직전 dict | 상태별 비중 `6-10% / 4-8% / 2-4% / 0-2%` | config에 없음 |
| `harness.py:20` | `BUY_STATES` 목록 | config에 없음 |
| `harness.py:223,227` | 분쟁 임계 `spread>=20 → -4`, `>=30 → -8` | **modern(루브릭) 경로에서는 0으로 무력화** |
| `harness.py:229-230` | `unknown_penalty`, `confidence_penalty` | **modern 경로에서 0** |

마지막 두 항목은 반대 방향의 문제입니다. RUNBOOK은 "도메인 점수에 미확인·분쟁·신뢰도 패널티가 적용된다"고
적혀 있지만 v2.1 이후 루브릭 경로에서는 **어떤 감점도 적용되지 않습니다**. NVDA 실행에서 10개 도메인 전부
`review_required=True`(스프레드 20 이상 또는 critical 불확실성)였는데 점수에 미친 영향은 0점이었습니다.
하네스가 문제를 탐지한 뒤 무시하고 있습니다. 이건 이번 프로필 범위 밖이라 손대지 않았고, 사실만 보고합니다.

---

## 4. 검토했으나 적용하지 않은 권고 (의견 차이)

**terminal multiples 15/20/25는 그대로 두었습니다.** 다만 기록은 남깁니다.
할인율 9%에서 이 배수들이 내재하는 영구성장률은 각각 **2.3% / 4.0% / 5.0%**입니다. Bull의 5.0%는
장기 명목 GDP를 영구히 상회한다는 뜻이라 이론적으로 성립하지 않습니다. 정합적인 값은 대략 **14 / 18 / 22**
(내재 g 1.9% / 3.4% / 4.4%)입니다.

적용하지 않은 이유는 이것이 **가치를 낮추는 강화 방향**이고, 요청하신 방향과 반대이기 때문입니다.
NVDA에 적용하면 Base 주당가치가 $212.86 → 약 $199로 내려가 price/Base가 1.10을 넘고, signal_map 밴드가
한 칸 내려가 EV가 53.00 → 41.75가 됩니다. 판단은 사용자 몫이므로 숫자만 제시합니다.
적용하시려면 `calibration.json`의 `valuation.terminal_multiples` 세 값만 고치면 됩니다.

---

## 4-1. 알려진 제약 — selftest

이 프로필을 적용하면 `python harness.py selftest`가 **실패합니다.**

```
AssertionError: moonshot market-cap gate should exclude >$20B
```

원인은 프로필이 아니라 selftest입니다. `harness.py:684-689`가 config가 소유한 값인 $20B를
테스트 코드에 하드코딩해 두었습니다. 경계 동작(≤ 포함)을 검증하려던 테스트인데 업무 상수까지 같이 고정해서,
config를 정당하게 바꾸면 무관한 테스트가 깨집니다.

동봉한 `selftest-config-driven.patch`(21줄)가 그 값을 config에서 읽도록 바꿉니다. 검증했습니다 —
패치 적용 + claude-v1 프로필 조합에서 selftest는 통과합니다.

```bash
git apply config/profiles/claude-v1/selftest-config-driven.patch
```

**이 패치는 저장소에 적용하지 않았습니다.** `harness.py`는 `run_manifest.config_files`에 해시로 기록되므로,
지금 고치면 이미 커밋된 NVDA run의 manifest가 무효가 됩니다. 적용 여부는 사용자가 판단하십시오.
패치를 쓰지 않으시려면 `strategy.json`의 moonshot `market_cap_usd`를 `20000000000`으로 되돌리면
프로필이 완전한 드롭인이 됩니다.

---

## 5. 파일

```
config/profiles/claude-v1/
  strategy.json      # archetype 임계값 재보정
  calibration.json   # 루브릭 앵커·signal_map·veto 담당
  workflow.json      # 원본과 동일 (변경 없음)
  CHANGES.json       # 23건 기계 판독용 변경 목록
  README.md          # 이 문서
  apply.sh / revert.sh
  selftest-config-driven.patch   # selftest가 moonshot 상한을 config에서 읽도록 (미적용)
config/profiles/_original/   # 원본 3종 보존
runs/NVDA/aggregate.claude-v1.json   # 프로필 적용 재집계 결과
```
