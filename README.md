# Long Outlier Expectation Gap Multi-Agent Harness

`장기 아웃라이어 기대차 투자 전략 v2.0`을 다수의 독립 전문 에이전트가 검증하도록 만든 provider-agnostic 하네스입니다.

## 구성
- **36개 전문 `AGENTS.md`**
- 8개 100점 스코어카드 도메인
- Evidence Audit 3개
- Red Team 4개
- Macro Overlay 2개
- Investment Committee 3개
- JSON 스키마·워크플로·집계 CLI 포함

## 핵심 설계
1. Blind independent analysis
2. Domain cross-examination
3. Evidence audit + Red Team
4. Hard Veto gate
5. Weighted score + dispute detection
6. IC Devil's Advocate + Chair
7. Macro pacing overlay
8. Evidence-based position sizing and monitoring

## 빠른 시작
```bash
python harness.py init NVDA --as-of 2026-09-15
# 각 agent가 runs/NVDA/reports/<agent_id>.json 작성
python harness.py aggregate NVDA
```

## 디렉터리 철학
각 에이전트 디렉터리마다 `AGENTS.md`를 둬 역할·질문·Hard Veto 초점을 격리했습니다. 루트 `AGENTS.md`는 공통 헌법 역할을 합니다.

## 주의
`harness.py`는 **오케스트레이션의 결정론적 집계 계층**입니다. 실제 LLM 호출은 사용 환경(Codex, Claude Code, OpenAI API, 자체 agent framework)에 맞춰 어댑터를 연결하십시오. 모델이 바뀌어도 점수·veto·보고서 형식은 유지되도록 설계했습니다.
