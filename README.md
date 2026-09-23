# Long Outlier Expectation Gap Harness v3.1

장기 투자 분석을 재현 가능한 자료·루브릭·결정론적 집계로 연결하는 provider-agnostic 하네스다.
핵심 100점 스코어카드와 Hard Veto 소유권을 유지하면서 네 가지 투자 유형과 조사 전처리·쉬운 최종 보고서를 제공한다.

| 투자 유형 | 경제적 의미 |
|---|---|
| `compounder` | 강한 해자, 높은 증분 ROIC, 재투자 활주로, 건전한 경영·재무와 합리적인 가격 |
| `growth` — 성장주 | 확인된 고객가치·현금창출과 빠른 확장. 컴파운더 수준의 성숙도 이전 단계에도 가격·생존·위험 조건을 요구한다 |
| `buffett_value` — 버핏 스타일 가치주 | 예측 가능한 사업·정상화 owner earnings·자본배분·재무 회복력과 안전마진. 큰 재투자 활주로는 필수가 아니다 |
| `outlier_growth` — 장기 아웃라이어 성장주 | 5~10년 이상의 성장 규모와 지속기간, 강화되는 경쟁우위, 적응력 있는 조직문화, 현실적인 5배 경로와 구체적인 시장 기대오류. 밸류에이션 관용적이되 맹목적이지 않다 |
| `moonshot` | 산업을 재편하는 혁신, 실증적인 채택곡선, 구조적 리더십, 비대칭성과 생존 여력 |

`non_fit`은 투자 유형이 아닌 관망·회피 시스템 상태다. **Expectation Gap은 모든 유형의 EV·AS·최종 판단에 남는 핵심 개념**이며 별도 투자 유형은 아니다. **Turnaround는 선택적 정상화 진단**이며 독립 투자 유형이 아니다.

문턱값의 원본은 [strategy.json](config/strategy.json)이다. [실행 정책 표](docs/POLICY.md)는 config에서 생성하며 테스트가 일치를 검증한다. Moonshot 시가총액은 기존 실행값을 유지했다. 이전 문서의 상충하는 숫자는 정책 근거로 사용하지 않는다.

### 성장 계열 세 유형의 구분
- **`growth` (성장주)** — 품질·GARP형. 검증된 고객가치와 현금창출 + 합리적인 Base 밸류에이션(price/Base ≤ 1.10)과 현재 FCF 품질을 요구한다.
- **`outlier_growth` (장기 아웃라이어 성장주)** — 지속기간 + 규모 + 조직 적응력 + 5배 경로 + 구체적 기대오류. 통상적 저가 요건과 현재 FCF 품질 요건을 **요구하지 않는 대신**, 5년 기회 규모·10년 활주로·문화·기대오류를 모두 통과해야 한다.
- **`moonshot` (문샷형)** — 초기 단계 파괴적 채택과 소형주 볼록성. 시가총액 상한이 걸린다.
- **`compounder` (컴파운더)** — 성숙한 고수익 재투자 기계.

네 범주는 서로 다른 것을 재며 겹치지 않는다. 단기 성장률이 높다는 이유만으로 `outlier_growth`가 되지 않는다.

## 분석 흐름

**Stage 0(자료 수집·전처리)** → 기업 자료 고정 → EV·AS·DI·FS triage → 도달 가능한 유형 계산 → 필요한 핵심 분석·veto reviewer·선택 TQ → 글로벌 금융·지정학 및 회사 전이 → ED·RT → 유형 적합도·Hard Veto·가치평가 게이트 → IC·포지션·모니터링 → 쉬운 한국어 보고서.

도메인 간 blind 분석과 각 보고서의 Bull/Verifier/Skeptic 구분을 유지한다. 점수 원천은 검증된 criterion별 `subscores`다. 현대 보고서는 self-confidence·unknown 개수·단일 Bull/Bear 폭으로 감점하지 않는다. 다중 보고서 간 분쟁 처리와 기존 scorecard 가중치는 유지한다.

모든 유형의 `archetype_fit`에 eligibility·fit_score·실패·누락·veto가 저장된다. 적격 유형 중 가장 높은 fit이 primary이며 동률은 config의 명시적 순서를 따른다. JSON 배열 순서가 결과를 결정하지 않는다. 누락 criterion은 누락으로 남으며 점수 0으로 판정하지 않는다. fit 설명용 합산에만 0 기여를 한다.

버핏 스타일 가치주는 저 P/E 필터가 아니다. RF는 유지보수 투자·운전자본·SBC·일회성을 반영한 정상화 주당 FCF를 검증한다. MT·RF·MA·FS·EV·RT는 영구 쇠퇴, 회계/정직성 문제, 숨은 부채, 부실 자본배분, 낙관적 terminal multiple 의존을 검증한다. 할인은 어느 Hard Veto도 해제하지 않는다. 확인되거나 미해소인 veto는 eligibility를 차단하며, 지정 reviewer 누락은 매수를 차단한다.

## 실행

```bash
python harness.py init NEW_TICKER --as-of YYYY-MM-DD
python harness.py fetch NEW_TICKER --user-agent "Name email@example.com"   # Stage 0: EDGAR에서 자동 수집
python harness.py intake NEW_TICKER                 # Stage 0: 필요한 원자료가 무엇이고 무엇이 비었는지
python harness.py prompt NEW_TICKER FP              # Stage 0: 재무 원자료 전처리 프롬프트
python harness.py validate-pack NEW_TICKER          # Stage 0: pack 스키마·불변식 검사
# company_context.json의 가격·순현금·출처·지역 노출을 작성한다.
python harness.py freeze NEW_TICKER --provider openai --model gpt-6-astra
python harness.py plan NEW_TICKER
python harness.py prompt NEW_TICKER EV
python harness.py validate NEW_TICKER EV
python harness.py aggregate NEW_TICKER
python harness.py digest NEW_TICKER
```

`init`은 기존 run을 덮어쓰지 않는다. `init`으로 만든 새 run은 Stage 0을 강제한다 — required 문서가 비었거나 pack 불변식이 깨지면 `freeze`가 거부하고 `plan`이 `stage: intake`를 반환한다. 기존 run의 manifest에는 이 플래그가 없어 영향을 받지 않는다. 단계별 실행은 [RUNBOOK](RUNBOOK.md)을 따른다. LLM 호출은 실행 환경에서 수행하며 하네스는 직접 모델을 호출하지 않는다.

## Stage 0 — 자료 수집과 재무 전처리

투자 판단 이전에 원자료를 먼저 세운다. [`config/intake.json`](config/intake.json)이 미국·한국 공시 기준의 문서 체크리스트(중요도·최소 개수·용도)를 정의하고, `intake`가 이를 financial pack의 `documents[]`와 대조해 차단 공백과 권고 공백을 분리해 보여준다. 조건부 항목(20-F, S-1 등)은 해당 여부를 자동 판정할 수 없으므로 gap으로 세지 않고 따로 표시한다.

전처리 규격은 [`agents/00_financial_preprocessor/AGENTS.md`](agents/00_financial_preprocessor/AGENTS.md)에 있다. FP는 공시 사실을 atomic fact로 추출하고 계정명을 canonical metric으로 매핑하며 정상화 후보만 표시한다. **계산·추정·경제적 정상화 판단을 하지 않는다.** 출력은 [`schemas/financial_pack.schema.json`](schemas/financial_pack.schema.json)을 따르고 `validate-pack`이 부호 규약, 기간과 FY/Q 모순, GAAP/non-GAAP 혼동, dangling `amount_fact_id`를 검사한다. FP는 점수를 만들지 않으며 100점 스코어와 coverage에 들어가지 않는다.

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

## Universe — 스크리너 기반 다종목 파이프라인

StockAnalysis Screener 결과(또는 스크린샷에서 추출한 ticker 목록)를 universe로 가져와 수십~수백 종목을 같은 하네스로 반복 분석한다. 설계와 충돌 해결은 [docs/UNIVERSE.md](docs/UNIVERSE.md)에 있다.

**Harness decides. Report explains.** universe 계층은 점수·유형·Hard Veto·상태·비중·밸류에이션을 계산하지 않는다. 모든 숫자는 `runs/<RUN>/final_verdict.json`(확정 전에는 `aggregate.json`)에서 출처와 함께 복사하며, `runs/` 아래 판정 산출물을 직접 쓰지 않는다. 단계 순서는 항상 `plan`이 정한다. 스크린 이름(예: "compounder")은 출처 표시일 뿐 archetype이 아니다.

### Workflow A — StockAnalysis 스크린샷/스크리너

1. StockAnalysis에서 screen을 실행한다.
2. CSV로 내보내거나, 스크린샷에서 ChatGPT/Codex vision으로 ticker를 추출한다.
3. `tickers.csv`(또는 `.txt`/`.json`)로 저장한다. 예: [examples/universe_example.csv](examples/universe_example.csv)
4. universe에 import → triage만 실행 → 도달 가능한 유형이 있는 종목만 Full Run → 보고서.

```bash
python harness.py universe import stockanalysis.csv --as-of 2026-09-21      # TXT/CSV/JSON
python harness.py universe import-screen screenshot_tickers.txt --as-of 2026-09-21
python harness.py universe run --dry-run                                     # 아무것도 쓰지 않고 계획만
python harness.py universe run --triage-only --workers 4                     # Stage 0 + EV + AS/DI/FS + early exit
python harness.py universe status
python harness.py universe continue --eligible-only --workers 4              # reachable archetype이 있는 종목만
python harness.py universe report                                            # STARTER 이상 full, WATCH concise, REJECT summary
python harness.py universe export universe.csv
python harness.py universe validate
```

import는 ticker를 대문자·공백 제거·`$`/`NASDAQ:` 접두 제거·`BRK-B`→`BRK.B`로 정규화하고, 중복을 합치며, 여러 screen에 나온 ticker는 `screens[]`에 모두 남긴다. ticker 모양이 아닌 입력은 거부하고 ETF/펀드는 표시한 뒤 실행하지 않는다. TXT는 한 줄에 ticker 하나(뒤에 회사명 허용), 한 줄에 여러 개는 쉼표/세미콜론으로 구분한다.

### 에이전트 출력은 어디서 오는가

하네스는 모델을 직접 호출하지 않는다. batch runner는 `plan`이 요청한 에이전트의 보고서를 다음 순서로 얻는다.

1. `.harness_inputs/<RUN>/reports/<AID>.json` — 기존 CI workflow와 같은 staging 규칙 (ticker·기준일 일치 검사). Stage 0는 `.harness_inputs/<RUN>/company_context.json`, `sources/`, `sources/financials/normalized_financials.json`
2. MO는 해당 기준일의 신선한 전역 macro cache (`init`과 같은 재사용)
3. `--agent-cmd "codex exec ... {prompt} ... {output}"` — 프롬프트 파일을 읽어 `{output}`에 보고서를 쓰는 명령. 쓰인 보고서는 `harness.py validate`를 통과해야 한다

모델 CLI를 쓰려면 범용 래퍼를 쓴다. 모델이 파일을 직접 쓰면 그대로 두고, 아니면 stdout의 마지막 JSON을 `{output}`에 기록한다 (내용은 수정하지 않으며 하네스가 validate한다).

```bash
python harness.py universe run --triage-only --agent-cmd \
  "python scripts/agent_cmd.py --prompt {prompt} --output {output} -- claude -p"
```

Stage 0 잠금 필드(가격·순현금/주)는 운영자가 넣는다. 하네스는 가격을 조회·추정하지 않는다.

```bash
python harness.py universe context --template ctx.csv       # 대기 중인 ticker 목록
# ctx.csv에 current_price, net_cash_per_share (선택: shares_diluted, market_cap_usd, currency, company_name) 기입
python harness.py universe context ctx.csv --source "broker close 2026-09-21"
python harness.py universe context --ticker LLY --price 1164.89 --net-cash-per-share -47.11
```

run이 있고 미동결이면 `runs/<RUN>/company_context.json`을, run이 없으면 `.harness_inputs/<RUN>/company_context.json`을 쓴다. 동결된 run은 수정하지 않는다. 수동 CI 실행용 [`.github/workflows/universe-batch.yml`](.github/workflows/universe-batch.yml)(workflow_dispatch 전용)도 있다.

어느 것도 없으면 `runs/<RUN>/<AID>_prompt.md`를 쓰고 그 종목을 `BLOCKED (awaiting ...)`로 둔다. 보고서를 만들어 내지 않는다. `--user-agent`(또는 `SEC_USER_AGENT`)를 주면 Stage 0에서 EDGAR fetch도 실행한다.

### 상태, 재개, 실패 격리

| run_status | 의미 |
|---|---|
| `QUEUED` | 대기 또는 `--triage-only` 등으로 멈춤 (`stage`가 다음 단계) |
| `RUNNING` | 이 ticker의 lock을 가진 runner가 실행 중 |
| `BLOCKED` | 입력 대기(보고서·company_context·FP), stale freeze, 확정되지 않은 run 등 — `blocked_reason` |
| `FAILED` | 명령 실패 — `last_error{command, stage, exception_type, stderr, retryable, timestamp}` |
| `COMPLETE` | `final_verdict.json` 확정. 조기 종료면 `early_exit=true`, 화면에는 `EARLY_EXIT` |

`stage`: `stage0 → ev → triage → domain_analysis → macro → evidence_and_red_team → ic → complete`. 한 종목이 실패해도 batch는 계속된다. `universe continue`는 시작된 종목을 재개하고, `universe retry XYZ`는 실패 종목을 다시 큐에 넣어 실행한다. 이미 끝난 단계는 planner가 요청하지 않으므로 다시 실행되지 않는다. stale freeze는 자동으로 재고정하지 않는다.

기타: `universe add LLY NU --as-of D`, `universe remove XYZ`, `universe reset XYZ`, `universe show LLY`, `universe sync`, `universe history LLY`, `universe snapshot`, `universe dashboard`. `--git none|per-ticker|batch`(기본 none, push하지 않음), `--stage stage0|triage|...`, `--workers N`(같은 ticker의 단계는 항상 순차), `--no-report`.

### 조회와 내보내기 (설명용 정렬만)

```bash
python harness.py universe status --archetype compounder --min-fit 80 --max-price-base 0.9 --veto CLEARED
python harness.py universe status --state STARTER --sort score --desc
python harness.py universe export universe.json
```

CSV 열: `ticker,score,score_ex_ev,archetype,fit,ev,as,di,fs,price_to_base,hard_veto,mechanical_state,ic_state,position_range,macro_pacing,status,as_of`. "Top Pick" 같은 새 순위는 만들지 않는다.

`reports/universe/`에 `universe_summary.md`, `compounders.md`, `growth.md`, `outlier_growth.md`, `buffett_value.md`, `moonshots.md`, `watchlist.md`, `early_exit.md`가 batch·report 뒤에 자동 갱신된다. 로그는 `runlogs/universe/<날짜>/universe-run.json`과 `<TICKER>.json`/`<TICKER>.log`.

### Deep Research Report (Report Agent RP)

```bash
python harness.py report LLY                  # 기존 easy_report.md 갱신 + tier에 따른 deep report
python harness.py report LLY --existing-run   # 재계산·fetch·에이전트 없이 기록된 판정만 설명
python harness.py report XYZ --force          # tier 무시 (내용은 그대로)
python harness.py report validate LLY
```

`runs/<RUN>/deep_report.md`·`deep_report.json`은 00 Executive Summary부터 21 Final Conclusion까지 22개 섹션이며, 모든 판정 값은 `final_verdict.json`에서 복사되고 각 문단에 출처 경로가 붙는다. 보고서는 새 목표주가·밸류에이션·점수·유형·비중·IC 판정을 만들지 않고, 판정과 다르면 쓰이지 않는다. `one_page_investment_record.md`는 빠른 IC 기록, `deep_report.md`는 심층 리서치로 역할을 나눈다. 보고서는 동결 기준일에만 유효하며 새 실적이 나오면 새 기준일로 import → refreeze → rerun → 새 보고서를 만든다 (이전 run은 `runs/<TICKER>`에 그대로 두고 새 run은 `runs/<TICKER>-<AS_OF>`).

### Workflow B — 단일 종목

기존 단일 종목 CLI(`init`·`fetch`·`intake`·`freeze`·`plan`·`prompt`·`validate`·`aggregate`·`digest`·`report`)는 그대로 동작한다. universe는 선택 사항이다.
