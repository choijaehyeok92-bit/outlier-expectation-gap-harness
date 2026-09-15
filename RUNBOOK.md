# RUNBOOK

## 1. 새 종목 초기화
```bash
python harness.py init TICKER --as-of YYYY-MM-DD
```
`runs/TICKER/`에 입력·보고서 디렉터리가 생성된다.

## 2. Phase 1 — Blind domain analysis
`config/agents_manifest.json`에 등록된 8개 점수 도메인의 에이전트를 병렬 실행한다. **이 단계에서는 서로의 보고서를 보여주지 않는다.**

## 3. Phase 2 — Domain cross-examination
각 도메인에서 Bull/Skeptic/Verifier가 Phase 1 결과를 읽고, 사실충돌·논리충돌·데이터 공백을 명시한다. 원본 보고서는 수정하지 말고 `cross_exam/`에 후속 보고서를 남긴다.

## 4. Phase 3 — Evidence + Red Team
ED-01~03과 RT-01~04를 실행한다. Red Team은 종목점수에 직접 더하지 않고 Hard Veto 및 IC 반론의 증거로 사용한다.

## 5. Phase 4 — Hard Veto gate
9개 veto를 `cleared / conditional / confirmed / unresolved`로 분류한다. `confirmed`는 기본 REJECT, `unresolved`는 최소 WATCH로 제한한다.

## 6. Phase 5 — 집계
```bash
python harness.py aggregate TICKER
```
도메인 점수는 confidence-adjusted weighted median 기반으로 계산되고, 큰 의견차에는 dispute penalty가 적용된다.

## 7. Phase 6 — IC
IC-01 → IC-02 → IC-03 순으로 실행한다. 최종 Chair는 점수보다 Hard Veto를 우선한다.

## 8. Phase 7 — Macro overlay
MO-01~02는 `risk_budget_multiplier`만 제안한다. 종목 100점 점수는 변경하지 않는다.

## 9. 포지션 가이드
- Starter: 1~2%
- Normal: 2~4%
- High Conviction: 4~6%
- Core Winner: 6~8%
- Exceptional Winner: 최대 약 10%

실제 비중은 기대차·영구손실·증거수준·포트폴리오 중복리스크를 반영해 Chair가 낮출 수 있다.

## 10. 모니터링
- 분기: 핵심 KPI만
- 반기: 경쟁환경, Moat Trajectory, 고객행동, 산업구조
- 연간: 투자가설과 밸류에이션 전면 재작성
- 3~5년: 초기 가정의 사후검증
