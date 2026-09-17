# Architecture

```text
Company Intake
   │
   ├─ Phase 1: 8 scoring domains × 3 independent agents
   │      ├─ Bull analyst
   │      ├─ Verifier / specialist
   │      └─ Skeptic
   │   + Disruptive Innovation axis × 3 (점수 비합산)
   │
   ├─ Phase 2: Domain cross-examination
   │
   ├─ Phase 3A: Evidence audit × 3
   ├─ Phase 3B: Red Team × 4
   │
   ├─ Phase 4: Hard Veto Gate
   │
   ├─ Phase 5: Score → Archetype → IC
   │      ├─ 문샷형 / 컴파운더 / 이머징 아웃라이어 / 기대차형 / 관망·회피형
   │      ├─ Scorekeeper
   │      ├─ Devil's Advocate
   │      └─ Chair
   │
   ├─ Phase 6: Macro Overlay × 2  ──> pacing only
   │
   └─ Phase 7: Position / KPI / Falsifier / Sell Evidence
```

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
