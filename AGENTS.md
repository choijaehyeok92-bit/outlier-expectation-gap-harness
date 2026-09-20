# AGENTS.md — Long Outlier Expectation Gap Investment Harness

## Mission
이 저장소의 모든 에이전트는 `장기 아웃라이어 기대차 투자 전략 v3.1`을 훼손하지 않고 종목을 검증한다. 목표는 높은 승률이 아니라 **영구손실을 제한하면서 소수의 장기 Outlier Winner를 식별하고 충분히 오래 보유할 수 있는 증거체계**를 만드는 것이다.

## Non-negotiable investment logic
1. 매출 성장률 자체가 아니라 **주당 FCF와 주당 경제가치의 성장**을 본다.
2. 절대적 기업 품질만으로 매수하지 않는다. **Expectation Gap = 합리적 장기 경제가치 - 현재가격 내재 기대**가 충분해야 한다.
3. 현재 해자보다 **Moat Trajectory**를 본다.
4. 높은 승률보다 **Power Law + Asymmetry**를 우선한다.
5. 가격이 아니라 **증거 변화**에 따라 판단을 바꾼다.
6. `Hard Veto`는 100점 스코어보다 우선한다.
7. Macro는 종목선정 점수에 섞지 않는다. Macro는 Risk Budget / Position Pacing 전용이다.
8. 추가매수는 `Position Increase ∝ Evidence Increase` 원칙을 따른다. 하락 자체는 추가매수 사유가 아니다.
9. **파괴적 혁신(DI)**은 독립 평가축이다. **턴어라운드 품질(TQ)**은 diagnostics.turnaround_candidate=true일 때만 실행하는 선택 진단이다. 둘 다 100점에 합산하지 않는다.
10. 모든 종목은 평가 후 **컴파운더 / 성장주 / 버핏 스타일 가치주 / 문샷형 / 관망·회피형** 중 하나로 분류한다. 문샷형의 고밸류에이션 용인이나 가치주의 할인은 Hard Veto를 면제하지 않는다. 기대차는 모든 유형의 분석 개념이며 별도 유형이 아니다.

## Evidence policy
- 모든 사실은 `as_of_date`, `source_type`, `source`, `period`, `value`를 남긴다.
- 1차 자료 우선순위: 규제공시/감사보고서 > 회사 IR/실적발표 > 산업 데이터 > 신뢰 가능한 2차 자료 > 기타.
- 숫자가 충돌하면 더 최신이라는 이유만으로 택하지 말고 정의·기간·회계기준 차이를 먼저 확인한다.
- 추정치와 사실을 명시적으로 구분한다.
- 모르는 것은 `unknown`으로 남긴다. 빈칸을 낙관적 추정으로 채우지 않는다.
- 분석 기준일 이후의 정보를 소급해 사용하지 않는다.

## Independence protocol
### Phase 0 — Raw data intake and preprocessing
`config/intake.json`의 문서 체크리스트로 필요한 원자료를 먼저 확보하고, Financial Preprocessor(FP)가 공시 사실을 atomic fact로 추출해 `sources/financials/normalized_financials.json`을 만든다. FP는 계산·추정·경제적 정상화 판단을 하지 않으며 점수·Bull/Bear·Hard Veto를 산출하지 않는다. 지침은 [`agents/00_financial_preprocessor/AGENTS.md`](agents/00_financial_preprocessor/AGENTS.md)다. 이 단계가 끝나기 전에는 freeze와 이후 분석을 시작하지 않는다.

### Phase 1 — Blind analysis
항목당 에이전트 1개가 다른 항목의 결론을 보지 않고 독립 분석한다. triage(EV·AS·DI·FS)를 먼저 실행한다.

### Phase 2 — In-report cross-examination
각 도메인 에이전트는 Bull / Verifier / Skeptic 관점을 각각 끝까지 전개하고 `bull_case`·`bear_case`, `bull_score`·`bear_score`로 남긴다. 관점을 합의에 끼워 맞추지 않는다.

### Phase 3 — Cross-domain Red Team
회계, 기술대체, 규제, 고객집중, 자금조달, 밸류에이션 과잉기대를 Red Team(RT)이 검증하고, Evidence Auditor(ED)가 출처·KPI·반증조건을 감리한다.

### Phase 4 — Hard Veto gate
`hard_veto=true`가 하나라도 발생하면 IC는 자동매수할 수 없다. 반드시 `cleared`, `conditional`, `confirmed` 중 하나로 판정하고 근거를 기록한다.
최종 `CLEARED`와 `CONFIRMED`는 `config/calibration.json`의 지정 owner만 낼 수 있다. owner가 아닌 에이전트의 `candidate`·`conditional`·`confirmed`는 판정이 아니라 발견이다. 해당 veto를 `UNRESOLVED`로 올리고 그 내용을 `non_owner_escalations`에 보존해 owner가 답하게 한다. owner 보고서나 owner 판정이 없는 상태는 어떤 경우에도 clear가 아니다.

### Phase 5 — Investment Committee
`harness.py aggregate`가 점수와 기계적 유형을 집계하고(Scorekeeper), IC 의장이 가장 강한 반론을 먼저 구성한 뒤 최종 판정을 내린다.

### Phase 6 — Position sizing
종합점수가 아니라 **증거 수준, 하방 영구손실, 기대차, 포트폴리오 중복위험**을 함께 사용한다.

## Token discipline
모든 에이전트는 [`agents/COMMON.md`](agents/COMMON.md)의 공통 규칙과 토큰 예산을 따른다. 실행은 `python harness.py prompt TICKER <AGENT_ID>`가 만든 프롬프트로 하며, triage 후 `plan`이 조기 종료를 판정하면 나머지 단계는 실행하지 않는다.

## Required output contract
각 에이전트는 반드시 JSON 보고서를 생성하며 `schemas/agent_report.schema.json`을 따른다. 핵심 필드:
- `agent_id`, `ticker`, `as_of_date`
- `domain`, `role`
- `score_0_100`, `confidence_0_1`
- 점수 도메인·독립 평가축(DI)·활성 선택 진단(TQ): `bull_score`, `bear_score`, `bull_case`, `bear_case` (`bear_score ≤ score_0_100 ≤ bull_score`)
- `thesis`, `evidence`, `counterevidence`, `unknowns`
- `falsifiers`, `hard_veto_flags`
- `key_kpis`, `next_checks`
- `verdict`: `support | neutral | oppose`
- `archetype_signals` (expectation_valuation 도메인만): `price_to_base_value`, `valuation_percentile_5y`, `revenue_cagr_next_3y`

## Scoring discipline
- 점수의 원천은 `config/calibration.json`의 criterion별 `subscores`다. 5점 단위로 채점하고 `score_0_100`은 고정 가중평균과 일치해야 한다.
- self-reported confidence, prose unknown 개수, 단일 모델의 Bull-Bear 폭은 새 실행의 숫자 점수를 직접 움직이지 않는다.
- 최종 100점 스코어는 `config/strategy.json`의 가중치를 사용한다.
- 신뢰도가 낮거나 핵심 데이터가 미확인인 경우 높은 점수를 주지 않는다.

## Conflict rules
- 동일 사실이 충돌하면 결론을 평균내지 않는다. 충돌 원인을 데이터 정의/기간/회계기준/출처 신뢰도 순으로 해결한다.
- `bull_score − bear_score`가 20점 이상인 도메인은 `domain_dispute=true`로 처리하고 IC에 강제 상신한다. 현재 1-agent 구조에서는 그 폭 자체를 자동 감점에 쓰지 않는다.
- Hard Veto는 지정 reviewer의 명시적 판정이 필요하며 미기재를 clear로 간주하지 않는다.
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
- `growth` — 성장주 (고객가치·현금창출을 확인하고 확장 중인 단계; 가격·생존·veto 게이트 유지)
- `moonshot` — 문샷형
- `compounder` — 컴파운더
- `buffett_value` — 버핏 스타일 가치주 (정상화 owner earnings + 자본배분 + 안전마진)
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
- 주가 급락·구조조정 발표·경영진의 회복 가이던스만으로 턴어라운드 점수 부여 금지.
- 경영진 발언을 검증 없이 증거로 취급 금지.

## Reproducibility contract
분석 프롬프트 전에 `freeze`로 input snapshot과 runner metadata를 고정한다. `freeze`는 `company_context.json`을 `schemas/company_context.schema.json`(Draft 2020-12 + format)으로 검증하고, terminal multiple이 bear ≤ base ≤ bull을 지키는지, 티커가 이 run을 가리키는지, 기준일이 `init` 이후 움직이지 않았는지를 확인한다. 검증은 새로 freeze할 때만 실행하며 과거 frozen run은 그대로 읽힌다. 직접적인 provider/model 비교는 동일 harness commit과 동일 input snapshot에서만 유효하다. EV 할인 계산은 LLM이 아니라 하네스가 수행한다.

## Research Orchestrator and plain reporting
Research Orchestrator는 docs/RESEARCH_ORCHESTRATOR.md를 따른다. frozen facts를 보존하고 질문·증거·충돌만 반환한다. 점수·유형·정상화·veto·비중 판정은 domain reviewer와 IC의 책임이다. 모든 추가 자료의 공개일을 cutoff와 비교한다. 최종 aggregate는 easy_report.md를 함께 생성하며 보고서가 새로운 투자판정을 만들지 않는다.
