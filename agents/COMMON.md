# 공통 수행 규칙 (모든 에이전트)

## 분석
- 기준일을 먼저 선언한다. 기준일 이후 정보는 사용하지 않는다.
- 최소 3개의 독립 근거를 확보하고, 가능한 한 1차 자료를 우선한다.
- 근거와 반대근거를 모두 제시한다.
- `사실 / 추정 / 해석`을 구분한다.
- 확인할 수 없는 데이터는 `unknown`으로 기록한다.
- 결론보다 먼저 반증조건을 작성한다.
- 다른 에이전트의 점수에 맞추기 위한 조정은 금지한다.

## 토큰 예산
- `company_context.json`의 기준 정보와 `sources/README.md`의 검증된 사실은 다시 검색하지 않는다. 오류를 발견했을 때만 근거와 함께 지적한다.
- 웹 검색·페치는 `config/workflow.json`의 `research_budget` 이내로 쓴다(기본: 역할당 6회, 도메인 묶음 12회).
- 공시 원문(.txt)은 통째로 읽지 않는다. `sources/INDEX.md`의 줄번호로 grep하거나 부분만 읽는다.
- Phase 3·IC 에이전트는 다른 에이전트의 원 보고서 대신 `digest.md`와 `cross_exam/*.md`를 읽는다. 원 보고서는 특정 주장을 검증할 때만 그 파일 하나를 연다.
- 보고서 분량은 `report_limits`를 지킨다(thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개, falsifiers·key_kpis·next_checks 각 3개). `unknowns`에는 핵심 가설에 직결되는 것만 쓴다.
- `hard_veto_flags`에는 상태가 none이 아닌 항목만 쓴다.
- 작성 후 `python harness.py validate <TICKER> <AGENT_ID...>`로 검증한다. 스키마 파일을 직접 읽지 않아도 된다.
