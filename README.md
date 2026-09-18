# Long Outlier Expectation Gap Multi-Agent Harness

`장기 아웃라이어 기대차 투자 전략 v2.0`을 항목별 전문 에이전트가 검증하도록 만든 provider-agnostic 하네스입니다.

## 구성
**항목 14개 = 에이전트 14개** (`config/agents_manifest.json`)

| 구분 | 에이전트 |
|---|---|
| 100점 스코어카드 8개 | SL 구조적 리더십 · CP 고객·제품 · MT 해자 추세 · RF 재투자·FCF · MA 경영진 · FS 재무생존 · EV 기대차·밸류에이션 · AS 비대칭성 |
| 독립 평가축 | DI 파괴적 혁신 · TQ 턴어라운드 품질 (100점 비합산, 유형 분류용) |
| 검증 | ED 증거 감사 · RT 레드팀 |
| 오버레이 | MO 매크로 (점수 비반영, pacing 전용) |
| 판정 | IC 투자위원회 의장 (반대 논리 포함). 점수 집계는 `harness.py aggregate`가 수행 |

JSON 스키마·워크플로·집계 CLI 포함.

## 핵심 설계
1. 도메인 간 blind 분석, 도메인 안에서는 Bull·Verifier·Skeptic 관점 분리(`bull_score`/`bear_score`)
2. 관점 간 점수차로 분쟁 탐지
3. Evidence audit + Red Team
4. Hard Veto gate
5. Weighted score + dispute detection
6. Disruptive innovation + Turnaround Quality 독립축과 종목 유형(archetype) 분류
7. IC Devil's Advocate + Chair
8. Macro pacing overlay
9. Evidence-based position sizing and monitoring

## 종목 유형 (Archetype)
평가가 끝나면 모든 종목을 다섯 유형 중 하나로 분류합니다. 판정 조건은 `config/strategy.json`의 `archetypes`에서 조정합니다.

| 유형 | 정의 | 핵심 판정 조건 (기본값) |
|---|---|---|
| 문샷형 (Moonshot) | 테슬라·팔란티어·엔비디아·구글·아마존 초기형. 파괴적 혁신성. 고밸류에이션 용인 | 시가총액 ≤ $50B, 파괴적 혁신 ≥78, 구조적 리더십 ≥72, 비대칭성 ≥72, 재무생존 ≥60. 게이트는 밸류에이션 도메인을 제외한 점수 |
| 컴파운더 (Compounder) | 장기 복리 창출 능력이 뛰어난 기업 | 주가/Base 가치 ≤1.2, Moat Trajectory ≥76, 증분 ROIC·FCF ≥76, 경영진 ≥72, 재무생존 ≥72, 밸류에이션 ≥42 |
| 턴어라운드형 (Turnaround) | 실제 실적 inflection과 self-help로 정상화 FCF/share 회복 가능성이 높은 기업 | TQ ≥72, 재무생존 ≥65, 경영진 ≥60, 기대차 ≥62, 비대칭성 ≥62. 유형 전용 게이트 점수 ≥55; 초기 1~3% 상한 |
| 기대차형 (Expectation Gap) | 적당한 성장에도 밸류에이션이 크게 낮아져 시장 오판 가능성이 있는 기업 | 주가/Base 가치 ≤0.85, 5년 밸류에이션 백분위 ≤35%, 3년 매출 CAGR 3~25%, 기대차 도메인 ≥65 |
| 관망·회피형 (Non-fit) | Hard Veto 확정, 게이트 점수(60) 미달, 또는 어느 유형에도 해당하지 않음 | 기본값. 신규 매수는 최대 Starter/Watch |

여러 유형에 동시에 해당하면 위 표 순서(문샷 → 컴파운더 → 턴어라운드 → 기대차)가 주 유형이 되고, 나머지는 `secondary`에 기록됩니다. 밸류에이션 신호는 EV 에이전트가 `archetype_signals`에 기록합니다. 문샷 시가총액은 frozen `company_context.market_cap_usd`를 우선하며, 비어 있으면 `current_price × shares_diluted`로 결정론적으로 계산합니다.

## 빠른 시작
```bash
python harness.py init NVDA --as-of 2026-09-15
# company_context.json의 current_price / net_cash_per_share를 채운 뒤
python harness.py freeze NVDA --provider openai --model gpt-5.6-sol --reasoning-effort high
python harness.py plan NVDA           # 다음에 실행할 에이전트 또는 조기 종료 안내
python harness.py prompt NVDA EV      # 에이전트 1회 호출용 프롬프트
python harness.py validate NVDA EV
python harness.py digest NVDA         # Phase 3·IC 입력용 요약
python harness.py aggregate NVDA
```
자세한 단계는 [RUNBOOK.md](RUNBOOK.md)를 보세요.

## 토큰 절약 설계
| 장치 | 효과 |
|---|---|
| 항목당 에이전트 1개 | 39개 → 14개. 한 에이전트가 Bull·Verifier·Skeptic 관점을 보고서 안에서 분리해 기록 |
| Triage + 조기 종료 | EV·AS·DI·TQ를 먼저 실행하고, 감점 전 점수로도 도달 가능한 유형이 없으면 나머지 10개 에이전트를 생략 |
| `digest` | Phase 3·IC가 원 보고서 대신 압축 요약을 읽음 (첫 NVDA 실행: 403K자 → 16K자) |
| `prompt` | 공통 문서를 따로 읽는 대신 필요한 내용만 담은 프롬프트 1개(기본 약 4K자 + 종목 기준 정보·공시 사실) |
| 공통 기준 정보 | `intake_facts`·`sources/README.md`의 사실은 재검색 금지. 웹 검색 예산 에이전트당 15회(공백 능동 보완용) |
| 보고서 분량 상한 | thesis 600자, bull/bear_case 300자, evidence 3~6개 등 (`report_limits`) |
| LLM 호출 제거 | 점수 집계는 `aggregate`가 수행, 매크로 보고서는 7일간 종목 간 재사용 |

## 디렉터리 철학
항목마다 `agents/<NN_domain>/AGENTS.md` 하나에 임무·관점별 질문·Hard Veto 초점을 담았습니다. 공통 규칙은 `agents/COMMON.md`, 헌법은 루트 `AGENTS.md`입니다.

## 주의
`harness.py`는 **오케스트레이션의 결정론적 집계 계층**입니다. 실제 LLM 호출은 사용 환경(Codex, Claude Code, OpenAI API, 자체 agent framework)에 맞춰 어댑터를 연결하십시오. 모델이 바뀌어도 점수·veto·보고서 형식은 유지되도록 설계했습니다.

## v2.1 — Provider calibration
- **Anchored rubric:** 8개 핵심 도메인과 DI·TQ를 criterion별 5점 단위 subscore로 평가하고 Python이 고정 가중합한다.
- **Confidence 비가중:** self-reported confidence는 새 실행의 숫자 점수를 바꾸지 않는다.
- **Single-agent spread 비감점:** 한 모델의 Bull/Bear 폭은 review flag만 만들고 자동 -4/-8점은 적용하지 않는다.
- **Structured uncertainty:** prose `unknowns` 개수로 새 실행을 감점하지 않는다.
- **Explicit Veto coverage:** 지정 reviewer가 Veto를 생략하면 clear가 아니라 미검증이다.
- **Deterministic valuation:** 할인율·terminal multiple·현재가격·순현금을 고정하고, LLM은 owner-FCF/share 경로만 제안한다.
- **Frozen run manifest:** commit/config/input SHA-256과 provider/model/reasoning metadata를 기록한다.

기존 39-agent 및 구버전 JSON은 `legacy_declared_score` 방식으로 계속 집계할 수 있다.
