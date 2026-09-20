# Research Orchestrator 계약

하네스는 질문을 지정하고, Research Orchestrator는 자료를 수집한다. 검증 입력은 고정하며 도메인 reviewer가 추론하고 하네스가 결정한다.

## 실행 경계

이 모듈은 웹이나 LLM을 직접 호출하지 않는다. 현재 실행 환경의 연구자/에이전트가 research-prompt를 받아 실제 검색을 수행하고 JSON을 제출한다. 검색을 실행하지 않았는데 실행했다고 기록해서는 안 된다. 검색 실패·접근 불가·자료 부재는 각각 명시한다.

1. company_context.json의 as_of_date를 절대 마감일로 사용한다.
2. run_manifest.json, sources/README.md, financials의 normalized_financials, derived_metrics, adjustment_candidates, qa_report를 먼저 확인한다.
3. 현재 plan, 완료된 report, digest, aggregate를 확인한다. research-plan은 존재 여부·해시를 기록한다. 누락 파일을 만들어진 것으로 간주하지 않는다.
4. 완료된 report의 unknowns·next_checks·veto 후보/조건부, 누락 관측값·valuation 입력·구조적 지정학 재분석만 질문으로 만든다. 같은 질문의 ID는 안정적으로 유지된다.
5. veto 질문을 최우선 처리한다. 지지/반박 1차 증거를 별도로 찾는다. 검색만으로 cleared/confirmed를 판정하지 않는다.

## 자료 순서와 종료

먼저 로컬 원본·재무팩·README·기존 증거에서 답을 찾는다. 이미 답이 있으면 웹 검색을 하지 않는다.
공백에 한해 Tier 1(규제·법적 공시), Tier 2(회사 공식 IR·콜), Tier 3(정부·산업 공식자료), Tier 4(신뢰 가능한 2차 자료), Tier 5(보조 미디어) 순서로 검색한다.
핵심 수치는 가능한 Tier 1/2로 확보한다. 동일 보도자료의 재인용은 source_origin을 동일하게 유지한다.
충분한 답을 얻으면 멈추고, 합리적 검색 후 없으면 searched_but_not_found 또는 inaccessible과 remaining_unknowns를 남긴다.

resolved는 질문을 답하는 적격 증거가 있고 핵심 unknown이 없는 경우다. partial은 일부 증거가 있고 unknown이 남은 경우다. unresolved는 신뢰 가능한 답을 확보하지 못한 경우다. 미제출 질문도 요약에서 unresolved로 계산한다. veto 양측 중 한쪽 근거를 확보하지 못하면 partial/unresolved로 남긴다.

## 입력 계약

schemas/research_packet.schema.json이 실행 계약이다. 최상위 필드는 schema_version=1.0, ticker, as_of_date, input_snapshot_sha256, questions다.
질문에는 research_question_id, question, status, evidence, remaining_unknowns, excluded_post_cutoff, search_log를 넣는다.
각 evidence에는 사용자가 지정한 출처·공개일·대상기간·cutoff 적격성·fact/estimate/interpretation·economic_driver·충돌·refreeze·confidence를 모두 넣는다.
추가 필수 provenance는 source_origin과 verified_fact_refs다. refs가 없으면 빈 배열로 표현한다.

- normalized:FACT-0001은 QA 파일이 존재하고 requires_review=false인 cutoff 내 1차 수치만 참조한다. 비교값은 원본 value_reported 단위로 표시한다. 단위 변환이 필요하면 comparison_value에 변환값을 명시하고 계산을 claim에 설명한다.
- context:key는 고정된 context 값이다. readme:원문 구절은 README의 정확한 인용 구절이다.
- 새 숫자가 참조 수치와 다르면 verified_value/new_value/possible_reason 및 conflict_with_verified_fact=true를 기록한다.
- 수정공시·재작성은 is_amendment/is_restatement=true다. 수용기는 requires_refreeze=true로 강제 분리한다.
- publication_date는 공개일이며 period와 다르다. cutoff 이후 자료는 excluded_post_cutoff로만 남는다.
- 동일 사실을 재사용할 때 evidence_id와 economic_driver를 유지한다. 다른 매체에 실려도 원천 source_origin은 동일하다.
- 경제적 조정은 possible_adjustment다. normalized_out은 금지한다. maintenance capex·경제적 ROIC·정상화 owner FCF는 직접 공시된 1차 수치가 아니면 estimate/interpretation이다.
- Hard Veto 질문은 evidence_supporting_veto/evidence_against_veto에 evidence ID를 기재한다. reviewer가 판정을 내린다.
- fact는 원문 직접 확인, estimate는 계산·추정, interpretation은 연결 판단이다. 한 claim 안에 섞지 않는다.

수용기는 형식·동일성·cutoff·명시된 수치 참조·증거 ID를 검사한다. 출처의 실제 진위나 자연어 의미까지 검증했다고 주장하지 않는다. 연구자와 Evidence Auditor는 누락된 참조, 단위/기간/정의 차이, 출처 오표기, fact와 해석 혼합을 별도로 확인해야 한다.

## 불변성과 전달

research-ingest는 research/result-{내용해시}.json을 추가한다. 원본 context/sources, domain reports, score, veto, valuation은 수정하지 않는다.
conflict/refreeze 및 cutoff 이후 자료는 후보 증거에서 제외한다. 다음 prompt에는 동일 snapshot의 적격·비충돌 증거만 제공한다. 도메인 프롬프트는 해당 질문의 증거만 받고 ED·RT·IC는 전체 후보를 검토한다. 결과 파일 내용이 바뀌면 로딩을 거부한다.
새 독립 증거 수는 evidence_id 기준으로 중복 제거하고 source_independence_groups를 별도로 제공한다. 같은 ID를 재제출하면 새 증거 수를 늘리지 않는다.
recommended_harness_reruns는 새로운 적격 증거를 받은 질문의 담당자만 포함한다. 자동으로 보고서를 완료하거나 점수를 수정하지 않는다.

## 정책 변경과 재현

과거 run은 기존 정책 snapshot으로 보존한다. fork-run은 입력을 바이트 그대로 복사하고 출처 manifest와 재사용 보고서 해시를 남긴다. 새 정책 아래 보고서는 다시 검토하며 새 run을 freeze한다.
freeze는 company_context.json을 스키마·시나리오 순서·티커·기준일 기준으로 검증한다. fork-run이 입력을 그대로 복사하므로 lineage.source_run이 기록된 fork는 원본 티커를 유지해도 통과한다. 검증은 freeze 시점에만 걸리며 이미 frozen된 run의 읽기에는 관여하지 않는다.
성장주 추가는 v3.1 정책 변경이다. 기존 핵심 점수와 컴파운더·가치주·문샷 게이트를 유지한다. 성장률 .15는 15%이며 15가 아니다. 임계값은 초기 정책이며 수익률 검증 결과가 아니다.
쉬운 보고서는 최종 집계가 만드는 설명이다. 새 투자 결론이나 주가 예측을 생성하지 않는다.


New manifests record hash_format=sha256-lf-text-v1: JSON/Markdown/Python/text/YAML hashes normalize CRLF to LF for portable Git checkouts. Other byte changes still invalidate a snapshot. Legacy fork verification accepts matching raw or LF-normalized bytes without editing the historical files.
