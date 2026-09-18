# RUNBOOK

실행 단위는 **항목 1개 = 에이전트 1개 = 호출 1회**다(총 13개). 매 단계마다 `plan`이 다음에 돌릴 에이전트와 조기 종료 여부를 알려준다.

```bash
python harness.py plan TICKER
```

## 1. 새 종목 초기화 (Phase 0)
```bash
python harness.py init TICKER --as-of YYYY-MM-DD
python harness.py sources TICKER --pdf-dir "<공시 PDF 폴더>"   # 선택: 공시 텍스트 추출 + 섹션 색인
# company_context.json에 current_price / net_cash_per_share를 입력한 뒤
python harness.py freeze TICKER --provider <provider> --model <model> --reasoning-effort <effort>
```
- `runs/TICKER/company_context.json`의 `intake_facts`에 주가·주식수·최근 실적 등 공통 사실을 **한 번만** 기록한다. 모든 에이전트가 재검증 없이 사용한다.
- 공시에서 확인한 핵심 사실은 `runs/TICKER/sources/README.md`에 적는다. 프롬프트에 자동 포함된다.
- 최근 `macro_cache_days`(7일) 이내 다른 종목에서 저장한 매크로 보고서가 있으면 `init`이 재사용한다.

## 2. Phase 1a — Triage
```bash
python harness.py prompt TICKER EV   # AS, DI도 동일
```
출력된 프롬프트를 에이전트 1회 호출로 실행한다. 세 에이전트가 끝나면 `plan`을 다시 실행한다. 감점 전 점수와 밸류에이션 신호로도 도달 가능한 유형이 없으면 **EARLY EXIT**이다. 이 경우 `aggregate`만 실행하고 종료한다(상태 `EARLY_EXIT_NON_FIT`, 비중 0%).

## 3. Phase 1b·2 — 나머지 도메인
`plan`이 알려주는 SL·CP·MT·RF·MA·FS를 병렬로 실행한다. **다른 항목의 보고서는 보여주지 않는다.** 각 에이전트는 Bull·Verifier·Skeptic 관점을 보고서 안에서 분리하고 `bull_score`/`bear_score`를 남긴다. 두 점수 차이가 20 이상이면 분쟁, 30 이상이면 재조사 대상이다.

## 4. Phase 3 — Evidence + Red Team
```bash
python harness.py digest TICKER
python harness.py prompt TICKER ED   # RT도 동일
```
Phase 3는 원 보고서가 아니라 `digest.md`를 입력으로 쓴다. Red Team은 종목점수에 직접 더하지 않고 Hard Veto와 IC 반론의 증거로 사용한다.

## 5. Phase 4 — Hard Veto gate
9개 veto를 `cleared / conditional / confirmed / unresolved`로 분류한다. `confirmed`는 기본 REJECT, `unresolved`는 최소 WATCH로 제한한다.

## 6. Phase 5 — 집계와 IC
```bash
python harness.py aggregate TICKER    # Scorekeeper (결정론적)
python harness.py digest TICKER
python harness.py prompt TICKER IC    # 반대 논리 → 판정 → final_verdict.json, 한 장 투자기록
```
도메인 점수에는 미확인·분쟁(bull − bear)·신뢰도 패널티가 적용된다. `aggregate.json`에는 다음이 함께 기록된다.
- `disruptive_innovation_score`: 파괴적 혁신 축 점수 (100점 비합산)
- `score_100_ex_valuation`: 밸류에이션 도메인을 제외한 점수 (문샷형 게이트용)
- `archetype`: 기계적 종목 유형, 판정 근거, 유형별 조건 충족·미충족·데이터 부족 내역
- `reachable_archetypes_raw`, `early_exit`: 감점 전 원점수 기준 도달 가능 유형과 조기 종료 여부

최종 Chair는 점수보다 Hard Veto를 우선하고, 종목 유형을 확정한다.

## 7. Macro overlay
MO는 `risk_budget_multiplier`만 제안한다. 종목 100점 점수는 변경하지 않는다. 종목과 무관하므로 한 번 실행한 뒤 저장해 재사용한다.
```bash
python harness.py prompt TICKER MO
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

## 11. 모델 A/B 비교
동일 commit, 동일 `company_context.json`, 동일 `sources/`로 각각 freeze한다. 두 `run_manifest.json`의 `input_snapshot_sha256`가 다르면 점수 차이를 모델 차이로 해석하지 않는다. 비교 순서는 `subscores → valuation_inputs → uncertainties → veto assessments → aggregate`다.
