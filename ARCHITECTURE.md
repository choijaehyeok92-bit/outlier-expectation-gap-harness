# Architecture

```text
Company Intake (intake_facts + sources/README.md — 모든 에이전트가 공유, 재검색 금지)
   │
   ├─ Phase 1a: Triage — expectation_valuation / asymmetry / disruptive_innovation
   │      └─ plan: 원점수로도 도달 가능한 유형이 없으면 ──> EARLY_EXIT_NON_FIT (종료)
   │
   ├─ Phase 1b: 나머지 6개 scoring domain (도메인당 1회 호출, 역할 3개)
   │      ├─ Bull analyst
   │      ├─ Verifier / specialist
   │      └─ Skeptic
   │
   ├─ Phase 2: Domain cross-examination (Phase 1과 같은 호출에서 작성)
   │
   ├─ digest.md ── Phase 3·IC의 입력 (원 보고서 재독 금지)
   ├─ Phase 3A: Evidence audit × 3
   ├─ Phase 3B: Red Team × 4
   │
   ├─ Phase 4: Hard Veto Gate
   │
   ├─ Phase 5: Score → Archetype → IC
   │      ├─ 문샷형 / 컴파운더 / 이머징 아웃라이어 / 기대차형 / 관망·회피형
   │      ├─ Scorekeeper (harness 자동 생성)
   │      ├─ Devil's Advocate
   │      └─ Chair
   │
   ├─ Phase 6: Macro Overlay × 2  ──> pacing only (7일 캐시, 종목 간 재사용)
   │
   └─ Phase 7: Position / KPI / Falsifier / Sell Evidence
```

## Token budget
토큰은 대부분 (1) 같은 사실의 중복 검색, (2) 후반 단계의 원 보고서 재독, (3) 결론이 정해진 뒤의 불필요한 단계에서 나온다. 첫 NVDA 실행(약 246만 토큰)에서 Phase 3 3개 호출이 44%를 차지했다. 하네스는 이를 다음처럼 막는다.
- **조기 종료:** 유형 조건은 결정론적이므로, triage 3개 도메인의 원점수만으로 모든 유형이 불가능하면 이후 단계는 결론을 바꿀 수 없다. 판정은 보수적이다. 감점 전 원점수를 쓰고, 미실행 도메인은 달성 가능하다고 가정한다.
- **digest:** 도메인 점수·Veto 코드·핵심 미확인 사항만 남긴 요약. Veto 문자열은 V1~V9 코드로 줄인다.
- **prompt:** 역할 지침, 공통 규칙, Veto 목록, 기준 정보, 출력 뼈대를 하나로 묶는다. 에이전트는 저장소 문서를 따로 읽을 필요가 없다.
- **분량 상한과 `validate`:** 출력 토큰과 다음 단계의 입력 토큰을 함께 줄인다.

트레이드오프: 도메인 단위 실행은 같은 도메인의 세 역할이 한 컨텍스트에서 작성되므로 역할 간 blind 독립성이 약해진다. 필요하면 `prompt TICKER AGENT_ID`로 역할별 실행을 선택할 수 있다.

## Why three agents per scoring domain?
단일 LLM의 일관된 편향을 줄이기 위해 역할을 비대칭으로 둔다. Bull은 장기 복리 경로를 최대한 정교하게 만들고, Skeptic은 실패 경로를 찾으며, Verifier는 데이터와 정의를 고정한다. 합의 자체가 목적이 아니라 **논점의 해상도**가 목적이다.

## Aggregation
- 각 도메인 내부 점수: confidence-weighted median
- unknown penalty: 핵심 미확인 데이터에 패널티
- dispute penalty: 20점 이상 의견차부터 적용
- 최종 100점: 전략 원문의 15/10/15/15/10/10/15/10 가중치
- Hard Veto: 점수와 독립된 상위 게이트
- 파괴적 혁신: 동일한 방식으로 도메인 점수를 내지만 100점에는 합산하지 않음

## Archetype classification
1. `config/strategy.json`의 `archetypes.types` 순서대로 조건을 평가한다. 조건 필드는 `domain.<도메인 id>`(도메인 점수) 또는 `signal.<이름>`(EV 에이전트 `archetype_signals`의 중앙값)이다.
2. 조건을 모두 충족하고 게이트 점수(기본 65)를 넘은 첫 유형이 주 유형이 된다. 나머지 충족 유형은 `secondary`에 기록한다.
3. `valuation_tolerant` 유형(문샷형)은 `expectation_valuation`을 제외하고 재정규화한 점수를 게이트와 기계적 상태 산정에 사용하고, `position_cap`으로 초기 비중을 제한한다.
4. Hard Veto 확정, 게이트 미달, 조건 미충족은 `non_fit`(관망·회피형)이 되며 매수 후보 상태는 `STARTER_OR_WATCH`로 낮춘다. 데이터가 없어 판정하지 못한 유형은 `reason`과 `evaluations[].missing`에 표시한다.

## Human-in-the-loop 권장 지점
1. Hard Veto `candidate/conditional` 해제
2. 동일 도메인 30점 이상 점수차
3. Base와 Reverse DCF가 정반대 결론을 낼 때
4. 최종 포지션 6% 초과
5. 기존 Core Winner의 매도/축소
6. 문샷형 분류 확정 및 Chair가 기계적 유형을 변경할 때
