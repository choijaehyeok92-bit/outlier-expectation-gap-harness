# Long Outlier Expectation Gap Multi-Agent Harness

`장기 아웃라이어 기대차 투자 전략 v2.0`을 다수의 독립 전문 에이전트가 검증하도록 만든 provider-agnostic 하네스입니다.

## 구성
- **39개 전문 `AGENTS.md`**
- 8개 100점 스코어카드 도메인
- 파괴적 혁신 평가축 3개 (100점 점수와 분리된 독립 축)
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
6. Disruptive innovation axis + 종목 유형(archetype) 분류
7. IC Devil's Advocate + Chair
8. Macro pacing overlay
9. Evidence-based position sizing and monitoring

## 종목 유형 (Archetype)
평가가 끝나면 모든 종목을 다섯 유형 중 하나로 분류합니다. 판정 조건은 `config/strategy.json`의 `archetypes`에서 조정합니다.

| 유형 | 정의 | 핵심 판정 조건 (기본값) |
|---|---|---|
| 문샷형 (Moonshot) | 테슬라·팔란티어·엔비디아·구글·아마존 초기형. 파괴적 혁신성. 고밸류에이션 용인 | 파괴적 혁신 ≥80, 구조적 리더십 ≥75, 비대칭성 ≥75, 재무생존 ≥60. 게이트는 밸류에이션 도메인을 제외한 점수 |
| 컴파운더 (Compounder) | 장기 복리 창출 능력이 뛰어난 기업 | Moat Trajectory ≥80, 증분 ROIC·FCF ≥80, 경영진 ≥75, 재무생존 ≥75, 밸류에이션 ≥50 |
| 이머징 아웃라이어 (Emerging Outlier) | Base 가치 전후 가격에서 아웃라이어 성격이 강한 기업 | 주가/Base 가치 0.8~1.2, 구조적 리더십 ≥75, 비대칭성 ≥75, Moat ≥70 |
| 기대차형 (Expectation Gap) | 적당한 성장에도 밸류에이션이 크게 낮아져 시장 오판 가능성이 있는 기업 | 주가/Base 가치 ≤0.8, 5년 밸류에이션 백분위 ≤30%, 3년 매출 CAGR 3~20%, 기대차 도메인 ≥75 |
| 관망·회피형 (Non-fit) | Hard Veto 확정, 게이트 점수(65) 미달, 또는 어느 유형에도 해당하지 않음 | 기본값. 신규 매수는 최대 Starter/Watch |

여러 유형에 동시에 해당하면 위 표 순서(문샷 → 컴파운더 → 이머징 → 기대차)가 주 유형이 되고, 나머지는 `secondary`에 기록됩니다. 밸류에이션 신호는 EV 도메인 에이전트가 `archetype_signals`에 기록하며, 하네스는 그 중앙값을 사용합니다.

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
