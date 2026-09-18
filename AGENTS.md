# AGENTS.md — Long Outlier Expectation Gap Investment Harness

## Mission
이 저장소의 모든 에이전트는 `장기 아웃라이어 기대차 투자 전략 v2.0`을 훼손하지 않고 종목을 검증한다. 목표는 높은 승률이 아니라 **영구손실을 제한하면서 소수의 장기 Outlier Winner를 식별하고 충분히 오래 보유할 수 있는 증거체계**를 만드는 것이다.

## Non-negotiable investment logic
1. 매출 성장률 자체가 아니라 **주당 FCF와 주당 경제가치의 성장**을 본다.
2. 절대적 기업 품질만으로 매수하지 않는다. **Expectation Gap = 합리적 장기 경제가치 - 현재가격 내재 기대**가 충분해야 한다.
3. 현재 해자보다 **Moat Trajectory**를 본다.
4. 높은 승률보다 **Power Law + Asymmetry**를 우선한다.
5. 가격이 아니라 **증거 변화**에 따라 판단을 바꾼다.
6. `Hard Veto`는 100점 스코어보다 우선한다.
7. Macro는 종목선정 점수에 섞지 않는다. Macro는 Risk Budget / Position Pacing 전용이다.
8. 추가매수는 `Position Increase ∝ Evidence Increase` 원칙을 따른다. 하락 자체는 추가매수 사유가 아니다.
9. **파괴적 혁신**은 100점 점수와 분리된 독립 평가축이다. 종목 유형 분류와 IC 판단에만 사용한다.
10. 모든 종목은 평가 후 **컴파운더 / 이머징 아웃라이어 / 기대차형 / 문샷형 / 관망·회피형** 중 하나로 분류한다. 문샷형의 고밸류에이션 용인은 Hard Veto를 면제하지 않는다.

## Evidence policy
- 모든 사실은 `as_of_date`, `source_type`, `source`, `period`, `value`를 남긴다.
- 1차 자료 우선순위: 규제공시/감사보고서 > 회사 IR/실적발표 > 산업 데이터 > 신뢰 가능한 2차 자료 > 기타.
- 숫자가 충돌하면 더 최신이라는 이유만으로 택하지 말고 정의·기간·회계기준 차이를 먼저 확인한다.
- 추정치와 사실을 명시적으로 구분한다.
- 모르는 것은 `unknown`으로 남긴다. 빈칸을 낙관적 추정으로 채우지 않는다.
- 분석 기준일 이후의 정보를 소급해 사용하지 않는다.

## Independence protocol
### Phase 1 — Blind analysis
각 전문 에이전트는 다른 에이전트의 결론을 보지 않고 독립 분석한다.

### Phase 2 — Domain cross-examination
같은 도메인의 Bull / Skeptic / Verifier 역할이 서로의 증거와 논리를 공격한다. 단순 다수결 금지.

### Phase 3 — Cross-domain Red Team
회계, 기술대체, 규제, 고객집중, 자금조달, 밸류에이션 과잉기대를 별도 Red Team이 검증한다.

### Phase 4 — Hard Veto gate
`hard_veto=true`가 하나라도 발생하면 IC는 자동매수할 수 없다. 반드시 `cleared`, `conditional`, `confirmed` 중 하나로 판정하고 근거를 기록한다.

### Phase 5 — Investment Committee
Scorekeeper는 점수를 집계하고, Devil's Advocate는 가장 강한 반론을 구성하며, Chair가 최종 판정을 내린다.

### Phase 6 — Position sizing
종합점수가 아니라 **증거 수준, 하방 영구손실, 기대차, 포트폴리오 중복위험**을 함께 사용한다.

## Token discipline
모든 에이전트는 [`agents/COMMON.md`](agents/COMMON.md)의 공통 규칙과 토큰 예산을 따른다. 실행은 `python harness.py prompt TICKER <domain|agent>`가 만든 프롬프트로 하며, triage 후 `plan`이 조기 종료를 판정하면 나머지 단계는 실행하지 않는다.

## Required output contract
각 에이전트는 반드시 JSON 보고서를 생성하며 `schemas/agent_report.schema.json`을 따른다. 핵심 필드:
- `agent_id`, `ticker`, `as_of_date`
- `domain`, `role`
- `score_0_100`, `confidence_0_1`
- `thesis`, `evidence`, `counterevidence`, `unknowns`
- `falsifiers`, `hard_veto_flags`
- `key_kpis`, `next_checks`
- `verdict`: `support | neutral | oppose`
- `archetype_signals` (expectation_valuation 도메인만): `price_to_base_value`, `valuation_percentile_5y`, `revenue_cagr_next_3y`

## Scoring discipline
- 에이전트의 `score_0_100`은 **자기 도메인 내부 품질 점수**다.
- 도메인 최종점수는 하네스가 다중 에이전트의 신뢰도 가중 중앙값과 분쟁패널티로 계산한다.
- 최종 100점 스코어는 `config/strategy.json`의 가중치를 사용한다.
- 신뢰도가 낮거나 핵심 데이터가 미확인인 경우 높은 점수를 주지 않는다.

## Conflict rules
- 동일 사실이 충돌하면 결론을 평균내지 않는다. 충돌 원인을 데이터 정의/기간/회계기준/출처 신뢰도 순으로 해결한다.
- 20점 이상 점수차가 나는 동일 도메인은 `domain_dispute=true`로 처리하고 IC에 강제 상신한다.
- 30점 이상 차이 또는 Hard Veto 관련 충돌은 재조사 없이는 통과할 수 없다.

## Final IC states
- `REJECT`
- `WATCH`
- `STARTER`
- `NORMAL`
- `HIGH_CONVICTION`
- `CORE_WINNER`
- `EXCEPTIONAL_WINNER`
- `HOLD_REVIEW`
- `TRIM_THESIS_RISK`
- `EXIT_THESIS_BROKEN`

## Archetypes
- `moonshot` — 문샷형
- `compounder` — 컴파운더
- `emerging_outlier` — 이머징 아웃라이어
- `expectation_gap` — 기대차형
- `non_fit` — 관망·회피형

## Forbidden shortcuts
- P/E가 낮다는 이유만으로 저평가 판정 금지.
- P/E가 높다는 이유만으로 위험 판정 금지.
- 주가 하락만으로 물타기 금지.
- 주가 상승만으로 매도 금지.
- 단기 EPS surprise를 장기 투자근거로 승격 금지.
- Macro 전망으로 기업가설 점수를 수정 금지.
- TAM만으로 구조적 성장 점수 부여 금지.
- "제2의 테슬라/엔비디아" 같은 비유만으로 파괴적 혁신 점수 부여 또는 문샷형 분류 금지.
- 경영진 발언을 검증 없이 증거로 취급 금지.
