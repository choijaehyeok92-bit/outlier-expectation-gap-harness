# Architecture

```text
Company Intake (intake_facts + sources/README.md — 모든 에이전트가 공유, 재검색 금지)
   │
   ├─ Phase 1a: Triage — EV / AS / DI
   │      └─ plan: 감점 전 점수로도 도달 가능한 유형이 없으면 ──> EARLY_EXIT_NON_FIT (종료)
   │
   ├─ Phase 1b: SL / CP / MT / RF / MA / FS (항목당 에이전트 1개, 도메인 간 blind)
   │      └─ 각 보고서 안에서 Bull·Verifier·Skeptic 관점 분리 → bull_score / bear_score
   │
   ├─ Phase 2: 관점 간 점수차(bull − bear)로 분쟁 탐지 (20+ 분쟁, 30+ 재조사)
   │
   ├─ digest.md ── Phase 3·IC의 입력 (원 보고서 재독 금지)
   ├─ Phase 3: ED 증거 감사 / RT 레드팀(포렌식·공매도·기술대체·규제집중)
   │
   ├─ Phase 4: Hard Veto Gate
   │
   ├─ Phase 5: Score → Archetype → IC
   │      ├─ harness.py aggregate (Scorekeeper, 결정론적)
   │      ├─ 문샷형 / 컴파운더 / 이머징 아웃라이어 / 기대차형 / 관망·회피형
   │      └─ IC 의장 (반대 논리를 먼저 구성한 뒤 판정)
   │
   ├─ Phase 6: MO 매크로  ──> pacing only (7일 캐시, 종목 간 재사용)
   │
   └─ Phase 7: Position / KPI / Falsifier / Sell Evidence
```

## Token budget
토큰은 대부분 (1) 같은 사실의 중복 검색, (2) 후반 단계의 원 보고서 재독, (3) 결론이 정해진 뒤의 불필요한 단계에서 나온다. 첫 NVDA 실행(약 246만 토큰)에서 Phase 3 3개 호출이 44%를 차지했다. 하네스는 이를 다음처럼 막는다.
- **조기 종료:** 유형 조건은 결정론적이므로, triage 3개 도메인의 원점수만으로 모든 유형이 불가능하면 이후 단계는 결론을 바꿀 수 없다. 판정은 보수적이다. 감점 전 원점수를 쓰고, 미실행 도메인은 달성 가능하다고 가정한다.
- **digest:** 도메인 점수·Veto 코드·핵심 미확인 사항만 남긴 요약. Veto 문자열은 V1~V9 코드로 줄인다.
- **prompt:** 지침, 공통 규칙, Veto 목록, 기준 정보, 출력 뼈대를 하나로 묶는다. 에이전트는 저장소 문서를 따로 읽을 필요가 없다.
- **분량 상한과 `validate`:** 출력 토큰과 다음 단계의 입력 토큰을 함께 줄인다.

## Why one agent per item, with separated perspectives?
초기 설계는 도메인마다 Bull·Verifier·Skeptic 에이전트 3개를 두었지만, 호출·출력·중복 조사가 3배로 늘어나는 데 비해 역할 간 독립성의 이득은 제한적이었다(같은 1차 자료를 공유하기 때문). 지금은 항목당 에이전트 1개가 세 관점을 **각각 끝까지 전개한 뒤** 결론을 낸다.
- `bull_case` / `bear_case`: 관점별 논리를 분리해 남긴다.
- `bull_score` / `bear_score`: 각 관점이 맞을 때의 점수. 이 차이가 곧 분쟁 신호다.
- 도메인 간에는 여전히 blind다. 다른 항목의 보고서를 보지 않는다.

트레이드오프: 한 컨텍스트 안의 관점 분리는 독립 에이전트보다 편향 상쇄 효과가 약하다. 그래서 관점 간 점수차가 크면 분쟁 감점과 IC 상신으로 드러나게 했고, 교차 도메인 검증은 별도 RT·ED 에이전트가 맡는다.

## Aggregation
- 새 실행의 도메인 점수: anchored `subscores`의 고정 가중합. self-reported confidence는 점수에 반영하지 않는다.
- prose `unknowns` 개수는 새 실행에서 감점하지 않고 structured uncertainty로 추적한다.
- 단일 agent의 Bull-Bear 폭은 review flag만 만들며 자동 감점하지 않는다.
- 레거시 다중-agent 실행은 기존 confidence-weighted median과 inter-agent dispute penalty를 유지한다.
- 최종 100점: 전략 원문의 15/10/15/15/10/10/15/10 가중치
- Hard Veto: 점수와 독립된 상위 게이트
- 파괴적 혁신: 동일한 방식으로 도메인 점수를 내지만 100점에는 합산하지 않음

## Archetype classification
1. `config/strategy.json`의 `archetypes.types` 순서대로 조건을 평가한다. 조건 필드는 `domain.<도메인 id>`(도메인 점수) 또는 `signal.<이름>`(EV 에이전트의 `archetype_signals`)이다.
2. 조건을 모두 충족하고 게이트 점수(기본 65)를 넘은 첫 유형이 주 유형이 된다. 나머지 충족 유형은 `secondary`에 기록한다.
3. `valuation_tolerant` 유형(문샷형)은 `expectation_valuation`을 제외하고 재정규화한 점수를 게이트와 기계적 상태 산정에 사용하고, `position_cap`으로 초기 비중을 제한한다.
4. Hard Veto 확정, 게이트 미달, 조건 미충족은 `non_fit`(관망·회피형)이 되며 매수 후보 상태는 `STARTER_OR_WATCH`로 낮춘다. 데이터가 없어 판정하지 못한 유형은 `reason`과 `evaluations[].missing`에 표시한다.

## Human-in-the-loop 권장 지점
1. Hard Veto `candidate/conditional` 해제
2. 동일 도메인 30점 이상 점수차 (bull − bear)
3. Base와 Reverse DCF가 정반대 결론을 낼 때
4. 최종 포지션 6% 초과
5. 기존 Core Winner의 매도/축소
6. 문샷형 분류 확정 및 Chair가 기계적 유형을 변경할 때

## Provider calibration boundary
하네스가 통제하는 것은 입력 snapshot, 채점척도, 산술, Veto coverage, DCF policy다. 하네스가 통제하지 않는 것은 미래 매출/FCF 경로에 대한 실제 추론 차이다. 동일 snapshot에서도 남는 차이가 모델 간 비교의 핵심 대상이다.
