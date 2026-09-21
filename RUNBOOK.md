# RUNBOOK — v3

항목당 한 에이전트가 분석한다. 매 단계의 `plan`이 실행할 항목과 조기 종료 여부를 결정한다. 투자 정책 숫자는 [config 생성 표](docs/POLICY.md)를 따른다.

## 연속 실행 원칙

운영자·에이전트는 각 단계가 끝날 때 멈추지 않고 `aggregate → digest → plan`으로 다음 상태를 계산한다. `plan`의 `execution_control`이 `continue`이면 반환된 `agents`를 계속 실행한다. 정상 종료는 `stop_early`(정책상 조기 종료) 또는 `stop_complete`(전체 워크플로 완료)뿐이다. `blocked`는 Stage 0/검증 입력을 고쳐야 한다는 뜻이며 분석 완료가 아니다.

예를 들어 EV 하나를 끝냈다면 `validate EV` 후 멈추지 말고 즉시 `aggregate`, `digest`, `plan`을 실행해 AS·DI·FS 또는 다음 단계로 진행한다. 이 반복은 코드가 명시적인 종료 신호를 낼 때까지 계속한다.

## 0. Stage 0 — 자료 수집과 재무 전처리

```bash
python harness.py init NEW_TICKER --as-of YYYY-MM-DD
python harness.py sources NEW_TICKER --pdf-dir "<공시 PDF 폴더>"
python harness.py fetch NEW_TICKER --user-agent "Name email@example.com"
python harness.py intake NEW_TICKER
python harness.py prompt NEW_TICKER FP
python harness.py validate-pack NEW_TICKER
```

`fetch`는 EDGAR 제출 색인에서 체크리스트의 `edgar_forms`에 해당하는 최신 제출물을 **as_of_date 이전 것만** 내려받고 출처를 `sources/fetch_manifest.json`에 남긴다. SEC 공정이용 정책상 연락처가 담긴 User-Agent가 필수이므로 `--user-agent` 또는 `SEC_USER_AGENT`로 직접 지정한다 — 하네스가 임의로 개인 연락처를 외부에 보내지 않는다. 요구 수량을 못 채우면 `shortfalls`로 기록하고 만들어내지 않는다. 망 정책이 sec.gov를 막는 환경에서는 실패 사유를 밝히고 수동 수집으로 안내한다.

`intake`는 `config/intake.json`의 체크리스트를 pack의 `documents[]`와 대조한다. `required`가 비면 종료코드 1이고 `freeze`가 거부한다. `near_required`(DEF 14A 등)와 `recommended`는 차단하지 않지만 비면 해당 도메인의 판단 근거가 unknowns로 남는다. 조건부 항목은 해당 여부를 사람이 판단한다.

FP는 제공된 문서만 사용하고 웹 검색을 하지 않는다. 계산·추정·일회성 판단·정상화 FCF 확정을 하지 않으며, 정상화 후보는 `adjustment_candidates`에 `requires_economic_review`로만 남긴다. 판단은 RF·FS·EV·MA가 한다. FP는 점수·Bull/Bear·Hard Veto를 만들지 않는다.

`validate-pack`은 스키마와 함께 부호 규약(capex 등은 양수), 기간과 FY/Q 모순, `metric=other`의 `metric_detail` 누락, dangling `amount_fact_id`, `documents[]`에 없는 `source_document`를 검사한다.

## 1. Intake와 고정

```bash
python harness.py freeze NEW_TICKER --provider openai --model gpt-6-astra --reasoning-effort high
```

초기화 후 freeze 전에 `company_context.json`에 current_price, net_cash_per_share, 시가총액 또는 주식수, 공통 사실과 출처를 입력한다. `sources/README.md`에 검증한 사실을 한 번 기록한다. 선택 `geo_exposure`의 지역 매출·생산 값은 0~1 비율이며, 공급자 지역·수출통제 의존성·제재 노출·해운 경로·정부 고객 노출은 문자열 목록이다. MO의 region/route/dependency 토큰과 일관된 이름을 사용한다.

정상화 진단이 필요하면 `diagnostics.turnaround_candidate=true`로 둔다. 기본값 false에서는 TQ를 실행하지 않고 누락을 coverage 결손으로 취급하지 않는다. true이면 TQ는 분석 뒤 digest와 IC에 들어가지만 유형 분류·100점에는 사용하지 않는다.

freeze는 Stage 0 상태를 먼저 확인한 뒤 입력·출처·정책·코드·지침·스키마 hash, Git commit, provider/model과 strategy/schema/decision_policy 버전을 기록하고 `stage_0` 요약을 manifest에 남긴다. 이후 변경되면 prompt가 재고정을 요구한다. 과거 run을 재초기화하지 말고 별도 ticker/run 이름을 사용한다.

## 2. Triage와 핵심 분석

```bash
python harness.py plan NEW_TICKER
python harness.py prompt NEW_TICKER EV  # AS, DI, FS도 실행
python harness.py validate NEW_TICKER
python harness.py plan NEW_TICKER
```

미완료 영역은 달성 가능하다고 가정한다. 이미 관측된 decision score·criterion·신호와 남은 핵심 점수의 낙관적 상한으로도 모든 유형이 불가능하면 종료한다. 가능한 경우 `plan`이 유형 조건, 모든 핵심 점수 coverage와 veto reviewer에 필요한 나머지 SL·CP·MT·RF·MA 및 활성화한 TQ를 요청한다. 다른 도메인 결론을 blind 분석에 제공하지 않는다.

점수는 검증된 subscore 고정 가중평균이다. 관측 기준표와 증거 상단/하단 게이트는 calibration config를 따른다. 분쟁·불확실성은 보고한다. Expectation Gap은 EV·AS에 계속 남아 있다.

## 3. Macro / geopolitical overlay

```bash
python harness.py prompt NEW_TICKER MO
python harness.py validate NEW_TICKER MO
python harness.py cache-macro NEW_TICKER
```

MO 프롬프트에는 회사 기준 정보·회사 출처를 넣지 않는다. `global_components`에 financial_conditions, credit_liquidity, geopolitical_events, structural_trade를 작성한다. 각 component는 `scope=global`, `as_of_utc`, 근거 evidence가 필요하다. 금융 component는 risk_budget_multiplier, 지정학 component는 각 dimension의 level·regions·routes·dependencies·structural_events를 갖는다. 정확한 차원, TTL, 배수와 라우팅은 workflow config에 있다.

관측 timestamp를 cache 복사 시각으로 바꾸지 않는다. 최신 component에 `invalidated=true`가 있으면 이전 값으로 되돌아가지 않는다. 일부만 신선하면 그 부분만 재사용하고 MO를 다시 요청한다. date-only 기준일은 UTC 자정으로 평가하므로 당일 자정 이후 자료는 다음 기준시각 전까지 사용하지 않는다. 누락/만료 component는 보수적 pacing fallback으로 표시한다.

전이는 회사 context를 읽어 매번 다시 계산한다. 빈 노출은 안전하다는 뜻이 아니라 unknown이다. 영구 수출금지·시장 접근권 상실·제재·국유화·핵심 공급자 상실은 대상 토큰이 일치할 때 관련 도메인 재분석을 요청한다. `plan`의 fundamental_reanalysis 요청에 따라 새 회사 근거를 검토한 뒤 해당 보고서 `geo_events_reviewed`에 event_id를 기록한다. 단순 확인 체크로 대체하지 않는다. 미완료 재분석은 매수를 막으며 macro 자체는 점수를 바꾸지 않는다.

## 4. ED·RT, Hard Veto와 IC

```bash
python harness.py aggregate NEW_TICKER
python harness.py digest NEW_TICKER
python harness.py prompt NEW_TICKER ED  # RT도 실행
python harness.py validate NEW_TICKER
python harness.py plan NEW_TICKER
python harness.py aggregate NEW_TICKER
python harness.py digest NEW_TICKER
python harness.py prompt NEW_TICKER IC
python harness.py aggregate NEW_TICKER
```

ED·RT는 충분한 선행 입력 후 digest를 사용한다. `evidence_concentration_flags`로 동일 경제 요인의 중복 사용을 검토한다. Hard Veto의 구성요건·cleared_if·관할 밖 라우팅과 지정 reviewer는 calibration config를 유지한다. 후보·조건부·누락은 clear가 아니며 IC가 매수로 덮어쓸 수 없다.

IC는 적격 유형의 반대 논리를 먼저 검증하고 `reports/IC.json`에 선택 `ic_state`와 근거를 기록하며 한 장 투자기록을 작성한다. primary와 secondary는 결정론적 fit 결과다. IC는 config의 state cap 안에서 신규 매수를 축소하거나 관망/거절할 수 있다. 요청이 게이트를 넘으면 final의 `ic_review_flags`에 거부 이유를 남긴다. `aggregate`가 `final_verdict.json`을 생성한다. IC가 이 파일을 손으로 덮어쓰지 않는다.

## 5. 조기 종료와 모니터링

IC 전 어느 단계에서든 유형이 모두 도달 불가능하면 `aggregate`와 `digest`로 종료한다. 전 핵심 점수가 있어도 IC를 생략할 수 있다. final의 `early_exit_record`에 단계, 마지막 도달 가능 유형의 결정론적 재구성, 실패 조건, 확인/미해소/누락 veto, 재진입 조건과 IC 의도적 미실행을 기록한다. LLM 호출이 필요 없다.

향후 재진입은 새 증거와 모든 gate 충족을 요구한다. 분기 KPI, 반기 경쟁환경·고객·해자, 연간 가설/가치평가 전면 재검토를 유지한다. 포지션 확대는 증거 증가에 비례하며 가격 하락만으로 확대하지 않는다. 포지션 범위와 macro pacing은 별도 필드다.

## 6. Calibration과 검증

```bash
python harness.py calibrate runs/RUN_A runs/RUN_B --out calibration.json
python harness.py selftest
python -m unittest discover -s tests -v
```

동일 commit·동일 input snapshot에서 provider를 비교한다. 기본 shadow에서는 보정 연구값과 decision score를 구분한다. active를 실험하려면 `provider_calibration.mode`를 명시적으로 바꾸고 별도 run을 freeze한다. 기존 manifest의 명시적인 provider_calibration_mode가 우선한다. 과거 정확한 의사결정 재현에는 해당 run의 원본 commit/config를 사용한다.
