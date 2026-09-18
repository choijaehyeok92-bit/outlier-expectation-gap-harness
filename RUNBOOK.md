# RUNBOOK

실행 단위는 **도메인 1개 = 에이전트 호출 1회**(역할 3개 동시 작성)다. 매 단계마다 `plan`이 다음에 돌릴 도메인과 조기 종료 여부를 알려준다.

```bash
python harness.py plan TICKER
```

## 1. 새 종목 초기화 (Phase 0)
```bash
python harness.py init TICKER --as-of YYYY-MM-DD
python harness.py sources TICKER --pdf-dir "<공시 PDF 폴더>"   # 선택: 공시 텍스트 추출 + 섹션 색인
```
- `runs/TICKER/company_context.json`의 `intake_facts`에 주가·주식수·최근 실적 등 공통 사실을 **한 번만** 기록한다. 모든 에이전트가 재검증 없이 사용한다.
- 공시에서 확인한 핵심 사실은 `runs/TICKER/sources/README.md`에 적는다. 프롬프트에 자동 포함된다.
- 최근 `macro_cache_days`(7일) 이내 다른 종목에서 저장한 매크로 보고서가 있으면 `init`이 재사용한다.

## 2. Phase 1a — Triage
```bash
python harness.py prompt TICKER expectation_valuation   # asymmetry, disruptive_innovation도 동일
```
출력된 프롬프트를 에이전트 1회 호출로 실행한다. 세 도메인이 끝나면 `plan`을 다시 실행한다. 감점 전 원점수와 밸류에이션 신호로도 도달 가능한 유형이 없으면 **EARLY EXIT**이다. 이 경우 `aggregate`만 실행하고 종료한다(상태 `EARLY_EXIT_NON_FIT`, 비중 0%).

## 3. Phase 1b·2 — 나머지 도메인과 교차검증
`plan`이 알려주는 나머지 6개 도메인을 병렬로 실행한다. 각 호출은 보고서 3개와 `cross_exam/<domain>.md`를 함께 작성한다. **다른 도메인의 보고서는 보여주지 않는다.**

역할별로 완전히 분리된 blind 분석이 필요하면 `python harness.py prompt TICKER AGENT_ID`로 역할마다 따로 실행한다. 토큰은 약 3배 든다.

## 4. Phase 3 — Evidence + Red Team
```bash
python harness.py digest TICKER
python harness.py prompt TICKER evidence_quality   # red_team도 동일
```
Phase 3는 원 보고서가 아니라 `digest.md`와 `cross_exam/*.md`를 입력으로 쓴다. Red Team은 종목점수에 직접 더하지 않고 Hard Veto와 IC 반론의 증거로 사용한다.

## 5. Phase 4 — Hard Veto gate
9개 veto를 `cleared / conditional / confirmed / unresolved`로 분류한다. `confirmed`는 기본 REJECT, `unresolved`는 최소 WATCH로 제한한다.

## 6. Phase 5 — 집계와 IC
```bash
python harness.py aggregate TICKER    # IC-01(Scorekeeper) 자동 생성
python harness.py digest TICKER
python harness.py prompt TICKER IC-02
python harness.py prompt TICKER IC-03
```
도메인 점수는 confidence-adjusted weighted median 기반으로 계산되고, 큰 의견차에는 dispute penalty가 적용된다. `aggregate.json`에는 다음이 함께 기록된다.
- `disruptive_innovation_score`: 파괴적 혁신 축 점수 (100점 비합산)
- `score_100_ex_valuation`: 밸류에이션 도메인을 제외한 점수 (문샷형 게이트용)
- `archetype`: 기계적 종목 유형, 판정 근거, 유형별 조건 충족·미충족·데이터 부족 내역
- `reachable_archetypes_raw`, `early_exit`: 감점 전 원점수 기준 도달 가능 유형과 조기 종료 여부

최종 Chair는 점수보다 Hard Veto를 우선하고, 종목 유형을 확정한다.

## 7. Macro overlay
MO-01~02는 `risk_budget_multiplier`만 제안한다. 종목 100점 점수는 변경하지 않는다. 종목과 무관하므로 한 번 실행한 뒤 저장해 재사용한다.
```bash
python harness.py prompt TICKER macro_overlay
python harness.py cache-macro TICKER
```

## 8. 보고서 검증
```bash
python harness.py validate TICKER [AGENT_ID ...]
```
필수 필드, Veto 문자열, 분량 상한(`config/workflow.json`의 `report_limits`)을 검사한다.

## 9. 포지션 가이드
- Starter: 1~2%
- Normal: 2~4%
- High Conviction: 4~6%
- Core Winner: 6~8%
- Exceptional Winner: 최대 약 10%

실제 비중은 기대차·영구손실·증거수준·포트폴리오 중복리스크를 반영해 Chair가 낮출 수 있다.

유형별 추가 규칙:
- 문샷형: 초기 1~3%. 채택·단위경제 증거가 늘어날 때 IC 승인으로 단계 확대
- 관망·회피형: 신규 매수 최대 Starter/Watch

## 10. 모니터링
- 분기: 핵심 KPI만
- 반기: 경쟁환경, Moat Trajectory, 고객행동, 산업구조
- 연간: 투자가설과 밸류에이션 전면 재작성
- 3~5년: 초기 가정의 사후검증
