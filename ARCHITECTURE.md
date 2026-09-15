# Architecture

```text
Company Intake
   │
   ├─ Phase 1: 8 scoring domains × 3 independent agents
   │      ├─ Bull analyst
   │      ├─ Verifier / specialist
   │      └─ Skeptic
   │
   ├─ Phase 2: Domain cross-examination
   │
   ├─ Phase 3A: Evidence audit × 3
   ├─ Phase 3B: Red Team × 4
   │
   ├─ Phase 4: Hard Veto Gate
   │
   ├─ Phase 5: IC
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

## Human-in-the-loop 권장 지점
1. Hard Veto `candidate/conditional` 해제
2. 동일 도메인 30점 이상 점수차
3. Base와 Reverse DCF가 정반대 결론을 낼 때
4. 최종 포지션 6% 초과
5. 기존 Core Winner의 매도/축소
