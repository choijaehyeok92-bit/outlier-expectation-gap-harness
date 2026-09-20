# Long Outlier Expectation Gap Harness v3.1

장기 투자 분석을 재현 가능한 자료·루브릭·결정론적 집계로 연결하는 provider-agnostic 하네스다.
핵심 100점 스코어카드와 Hard Veto 소유권을 유지하면서 네 가지 투자 유형과 조사 전처리·쉬운 최종 보고서를 제공한다.

| 투자 유형 | 경제적 의미 |
|---|---|
| `compounder` | 강한 해자, 높은 증분 ROIC, 재투자 활주로, 건전한 경영·재무와 합리적인 가격 |
| `growth` — 성장주 | 확인된 고객가치·현금창출과 빠른 확장. 컴파운더 수준의 성숙도 이전 단계에도 가격·생존·위험 조건을 요구한다 |
| `buffett_value` — 버핏 스타일 가치주 | 예측 가능한 사업·정상화 owner earnings·자본배분·재무 회복력과 안전마진. 큰 재투자 활주로는 필수가 아니다 |
| `moonshot` | 산업을 재편하는 혁신, 실증적인 채택곡선, 구조적 리더십, 비대칭성과 생존 여력 |

`non_fit`은 투자 유형이 아닌 관망·회피 시스템 상태다. **Expectation Gap은 모든 유형의 EV·AS·최종 판단에 남는 핵심 개념**이며 별도 투자 유형은 아니다. **Turnaround는 선택적 정상화 진단**이며 독립 투자 유형이 아니다.

문턱값의 원본은 [strategy.json](config/strategy.json)이다. [실행 정책 표](docs/POLICY.md)는 config에서 생성하며 테스트가 일치를 검증한다. Moonshot 시가총액은 기존 실행값을 유지했다. 이전 문서의 상충하는 숫자는 정책 근거로 사용하지 않는다.

## 분석 흐름

기업 자료 고정 → EV·AS·DI·FS triage → 도달 가능한 유형 계산 → 필요한 핵심 분석·veto reviewer·선택 TQ → 글로벌 금융·지정학 및 회사 전이 → ED·RT → 유형 적합도·Hard Veto·가치평가 게이트 → IC·포지션·모니터링 → 쉬운 한국어 보고서.

도메인 간 blind 분석과 각 보고서의 Bull/Verifier/Skeptic 구분을 유지한다. 점수 원천은 검증된 criterion별 `subscores`다. 현대 보고서는 self-confidence·unknown 개수·단일 Bull/Bear 폭으로 감점하지 않는다. 다중 보고서 간 분쟁 처리와 기존 scorecard 가중치는 유지한다.

모든 유형의 `archetype_fit`에 eligibility·fit_score·실패·누락·veto가 저장된다. 적격 유형 중 가장 높은 fit이 primary이며 동률은 config의 명시적 순서를 따른다. JSON 배열 순서가 결과를 결정하지 않는다. 누락 criterion은 누락으로 남으며 점수 0으로 판정하지 않는다. fit 설명용 합산에만 0 기여를 한다.

버핏 스타일 가치주는 저 P/E 필터가 아니다. RF는 유지보수 투자·운전자본·SBC·일회성을 반영한 정상화 주당 FCF를 검증한다. MT·RF·MA·FS·EV·RT는 영구 쇠퇴, 회계/정직성 문제, 숨은 부채, 부실 자본배분, 낙관적 terminal multiple 의존을 검증한다. 할인은 어느 Hard Veto도 해제하지 않는다. 확인되거나 미해소인 veto는 eligibility를 차단하며, 지정 reviewer 누락은 매수를 차단한다.

## 실행

```bash
python harness.py init NEW_TICKER --as-of YYYY-MM-DD
# company_context.json의 가격·순현금·출처·지역 노출을 작성한다.
python harness.py freeze NEW_TICKER --provider openai --model gpt-6-astra
python harness.py plan NEW_TICKER
python harness.py prompt NEW_TICKER EV
python harness.py validate NEW_TICKER EV
python harness.py aggregate NEW_TICKER
python harness.py digest NEW_TICKER
```

`init`은 기존 run을 덮어쓰지 않는다. 단계별 실행은 [RUNBOOK](RUNBOOK.md)을 따른다. LLM 호출은 실행 환경에서 수행하며 하네스는 직접 모델을 호출하지 않는다.

## Calibration·증거·Macro

Provider calibration 기본값은 `shadow`다. 각 도메인에 `raw_score`, `calibrated_score`/`calibrated_shadow_score`, `decision_score`를 함께 남긴다. shadow에서는 raw observable-anchored 점수가 결정 점수이며 provider offset은 분류를 움직이지 않는다. `active`는 명시적으로 선택하고 freeze에 기록할 수 있다. criterion 값 자체는 어느 모드에서도 provider 보정하지 않는다.

`evidence_id`와 선택 `economic_driver`로 같은 사실에 의존하는 긍정 도메인들을 표시한다. `evidence_concentration_flags`는 ED·RT·IC 검토용이며 자동 감점하지 않는다.

MO는 글로벌 금융 여건·신용/유동성과 군사분쟁·무역분절·수출통제·제재·에너지·해운·주권/정책 불안정의 벡터를 출력한다. 전역 cache는 timestamp를 가진 글로벌 component만 저장한다. 회사별 `geo_exposure`와의 전이는 매 run에서 다시 계산한다. 금융·지정학은 위험예산·매수속도·모니터링만 바꾼다. 영구적인 구조적 사건은 SL·CP·FS·MT 등의 재분석을 요청하며 **기업 점수에 임의의 macro 가감점을 넣지 않는다**.

## 검증과 호환성

```bash
python -m pip install -r requirements-dev.txt
python harness.py selftest
python -m unittest discover -s tests -v
python harness.py policy --out docs/POLICY.md
```

[아키텍처 및 마이그레이션](ARCHITECTURE.md)에 모듈, 캐시 계약, 과거 보고서 호환성과 의도적인 제한을 정리했다. 과거 `runs/`는 변경하지 않는다. 새 최종 JSON은 v3 schema를 따르며, 기존 archetype 문자열을 새 primary로 재출력하지 않는다.

## 조사 전처리와 쉬운 보고서

[Research Orchestrator 계약](docs/RESEARCH_ORCHESTRATOR.md)에 따라 research-plan → research-prompt → research-ingest를 실행한다. 하네스가 질문을 만들고 외부 실행 환경의 연구자가 실제 검색을 수행한다. 수용된 증거는 다음 도메인 프롬프트에 공급되며 원본이나 점수는 자동 변경하지 않는다.

```bash
python harness.py research-plan NEW_TICKER
python harness.py research-prompt NEW_TICKER --out research_prompt.md
# 실제로 조회한 자료만 schemas/research_packet.schema.json에 맞춰 packet.json 작성
python harness.py research-ingest NEW_TICKER packet.json
python harness.py report NEW_TICKER
```

aggregate와 report는 최신 계산에서 easy_report.md를 생성한다. IC 미완료/조기 종료 상태도 명시한다. 성장주 임계값은 초기 정책값이며 수익률 검증을 마친 기준이 아니다. 기존 유형의 기준과 점수 가중치는 유지한다.

과거 실행을 새 정책으로 검토하려면 `python harness.py fork-run OLD_RUN NEW_RUN --carry-domain-reports` 후 새 run을 freeze한다. 원본 입력은 바이트 그대로 보존하고, 재사용한 도메인 보고서의 출처를 기록하며 ED·RT·MO·IC는 새로 수행한다. 재사용 점수도 현재 루브릭으로 검토해야 한다. 과거 run 자체를 새 정책으로 재고정하지 않는다.

IC 검토를 명시적으로 요청받았지만 유형 조건을 충족하지 못한 경우 새 실행을 freeze --review-only로 고정할 수 있다. 이 실행은 매수 승인을 차단하며 미확인 macro를 그대로 표시한다. 기본 분석의 조기 종료·위험 게이트는 유지된다.
