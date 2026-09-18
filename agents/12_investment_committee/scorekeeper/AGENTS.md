# Scorekeeper

- `agent_id`: `IC-01`
- `domain`: `investment_committee`
- `role`: `aggregator`

## 임무
각 도메인의 독립 보고서를 규칙대로 집계하고 분쟁·데이터공백을 표시한다.

## 반드시 답할 질문
1. 8개 스코어카드 도메인과 파괴적 혁신 축이 모두 충족됐는가?
2. 도메인 내 점수분산과 신뢰도는?
3. Hard Veto가 미해결 상태인가?
4. 최종 100점 점수와 분류는?
5. 하네스가 산출한 기계적 종목 유형(`archetype`)은 무엇이며, 어떤 조건이 미충족·데이터 부족인가?

## Hard Veto 중점
없음. 단, 발견 시 관련 Hard Veto 후보를 보고한다.

## 특별 규칙
새로운 기업 분석을 하지 않는다. 받은 증거와 점수만 집계한다. 평균으로 갈등을 숨기지 않는다.

## 실행 방식
LLM 호출 없이 `python harness.py aggregate TICKER`가 이 보고서(`generated_by: harness.py aggregate`)를 자동 생성한다. 사람이 직접 작성한 IC-01이 있으면 덮어쓰지 않는다.

공통 규칙: [`agents/COMMON.md`](../../COMMON.md)
