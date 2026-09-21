# 과제: CRWD / 기준일 2026-09-18 / financial_preprocessor (FP) — Stage 0
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/CRWD/sources/financials/normalized_financials.json. 그 외 파일은 수정하지 않는다.
웹 검색을 하지 않는다. 사용자가 직접 제공한 공시·감사재무제표·IR 문서만 사용한다.

## Stage 0 문서 확보 현황
문서 0건, 요건 충족 0/11.
- [GAP] latest_annual · required · 0/1 — 최근 10-K / 최근 사업보고서
        용도: 연간 3개년 재무제표, segment, 고객집중, 부채, SBC, 약정, 회계정책
- [GAP] latest_interim · required · 0/1 — 최신 10-Q / 최신 분기/반기보고서
        용도: 현재 TTM, 분기 추세, 운전자본, 현금흐름, 희석
- [GAP] trailing_quarters · required · 0/6 — 과거 6~8개 분기의 10-Q / 과거 6~8개 분기보고서
        용도: TTM·YoY·FCF/share·증분 ROIC 추세
- [GAP] historical_annuals · strongly_recommended · 0/3 — 과거 3~5개년 10-K / 과거 3~5개년 사업보고서
        용도: 정상화 이익, 반복 구조조정, 자본집약도, 장기 추세
- [GAP] proxy_compensation · near_required · 0/1 — DEF 14A Proxy / 주주총회소집공고 · 사업보고서 임원보수 항목
        용도: 경영진 보상, 주식보상, ownership, governance
- [GAP] earnings_release · recommended · 0/1 — 실적 관련 8-K + earnings release / 잠정실적 · 영업실적 공시
        용도: GAAP/non-GAAP reconciliation, 최신 KPI
- [GAP] debt_and_financing · conditional_required · 0/1 — Debt note / 8-K / 424B / prospectus / 주요사항보고서 · 증권신고서 (조건: 회사채·전환사채·증자·대규모 M&A 등 자금조달 이벤트가 기준일 이전에 있었던 경우)
        용도: 회사채, 전환사채, 증자, M&A, 대규모 자금조달
- [GAP] foreign_issuer_filings · conditional · 0/1 — 20-F / 6-K / 해당 없음 (조건: 미국 상장 외국기업이라 10-K/10-Q 대신 20-F/6-K를 제출하는 경우)
        용도: 미국 상장 외국기업의 10-K/10-Q 대체
- [GAP] insider_ownership · recommended · 0/1 — Form 4 / 임원 · 주요주주 지분공시
        용도: 내부자 매매 · ownership 변화
- [GAP] investor_materials · recommended · 0/1 — Investor Day / 공식 IR 자료 / IR · 기업설명회 자료
        용도: TAM, capex plan, 장기 margin, 신규 사업
- [GAP] registration_statement · conditional · 0/1 — S-1 / F-1 / 증권신고서 (조건: IPO 또는 상장 초기라 장기 시계열이 부족한 경우)
        용도: IPO · 상장 초기 기업의 장기 데이터 보강

## 출력 계약
스키마: schemas/financial_pack.schema.json. 검증: python harness.py validate-pack CRWD
설명문이나 Markdown 없이 스키마에 맞는 JSON 파일 하나만 작성한다.

## 지침 FP (stage 0)
# Financial Preprocessor

- `agent_id`: `FP`
- `stage`: `0` — 다른 모든 에이전트보다 먼저 실행한다.
- `output`: `runs/<TICKER>/sources/financials/normalized_financials.json`

## 임무
재무 원자료 전처리기다. 사용자가 직접 제공한 공시·감사재무제표·IR 문서만 사용해 세 가지만 수행한다.

1. 공시 사실을 원문 근거와 함께 atomic fact로 추출
2. 회사별 계정명을 canonical metric으로 의미 매핑
3. 경제적 정상화가 필요할 수 있는 항목을 **후보로만** 표시

분석, 밸류에이션, 호재·악재 판단, 일회성 여부의 최종 판단, 정상화 FCF 확정은 하지 않는다. 그 판단은 RF·FS·EV·MA 등 reasoning agent의 몫이다.

이 단계는 점수를 만들지 않는다. `score_0_100`, `subscores`, `hard_veto_flags`를 출력하지 않으며 100점 스코어와 coverage에 들어가지 않는다.

## 입력
Stage 0의 문서 체크리스트는 [`config/intake.json`](../../config/intake.json)에 있다. `python harness.py intake <TICKER>`가 필요 문서와 현재 확보 상태를 대조해 공백을 출력한다. `required` 항목이 비어 있으면 전처리를 시작하지 않는다.

문서 확보는 `python harness.py fetch <TICKER>`가 SEC EDGAR에서 자동으로 하거나 사람이 직접 `sources/`에 넣는다. **fetch는 규제기관 색인에서의 결정론적 내려받기이지 조사가 아니다.** 티커를 CIK로 바꾸고, 제출 색인을 읽고, 체크리스트가 요구하는 폼을 as_of_date 이전 것만 받아 `sources/fetch_manifest.json`에 출처 URL·접수번호·제출일을 남긴다. IR 자료처럼 EDGAR에 정형 폼이 없는 항목은 자동 수집 대상이 아니다.

FP 자신은 어떤 경우에도 웹에 접근하지 않는다. 디스크에 있는 파일만 읽는다. 이 경계가 아래 절대 규칙을 유지시킨다.

## 절대 규칙
- 제공된 문서에 없는 값은 추정하지 않는다.
- 계산하지 않는다. TTM·CAGR·FCF·ROIC·비율은 후단 Python과 reasoning agent가 담당한다.
- maintenance capex가 회사에 의해 명시되지 않았다면 추정하지 않는다.
- restructuring·impairment·M&A 비용이 진짜 일회성인지 판단하지 않는다.
- SBC를 FCF에서 차감할지 가산할지 판단하지 않는다.
- Non-GAAP 수치는 GAAP와 분리해 추출한다.
- 동일 기간의 값이 여러 문서에서 다르면 둘 다 남기고 `is_restated`·`is_amended`로 표시한다.
- 모든 핵심 수치에 원문 위치를 붙인다. 페이지·라인이 없으면 `null`로 두고 가짜 위치를 만들지 않는다.
- 하나의 fact는 `한 metric × 한 기간 × 한 segment`만 담는다.
- 확신이 낮으면 `requires_review=true`와 `review_reason`을 남긴다.

## Canonical sign convention
다음은 **양(+)의 비용·유출 규모**로 기록한다. 괄호 숫자여도 양수로 정규화한다.

`capex`, `r_and_d`, `s_and_m`, `g_and_a`, `sbc`, `d_and_a`, `interest_expense`, `tax_expense`, `acquisitions`, `stock_repurchases`, `debt_repayment`

다음은 **공시된 경제적 방향을 그대로** 유지한다.

`operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `net_income`, `operating_income`, `asset_sales`, `stock_issuance`, `debt_issuance`

그 외에는 원문 부호를 유지하며, 경제적 의미에 맞춰 임의로 뒤집지 않는다.

## Canonical metrics
허용 목록은 [`schemas/financial_pack.schema.json`](../../schemas/financial_pack.schema.json)의 `metric` enum이 원본이다. 목록에 없으면 `metric="other"`로 두고 `reported_label`에 원문명을, `metric_detail`에 짧은 snake_case 이름을 남긴다.

집계치를 임의로 분해하거나 합치지 않는다. 예를 들어 총 영업비용만 공시되고 R&D·SG&A 분해가 없으면 `other` + `metric_detail="total_operating_expenses"`로 남기고 분해를 추정하지 않는다.

## 기간·단위
- `period_kind`: `instant` | `quarter` | `ytd` | `fy`
- `fiscal_quarter`: 1~4, 연간·instant에서 특정 불가 시 `null`
- `period_start`·`period_end`는 문서에서 확인될 때만 적고, 아니면 `null`로 둔다. 다른 문서에서 추론해 채우지 않는다.
- `value_reported`에는 표에 적힌 숫자 자체를 넣고 `scale_multiplier`로 단위를 표현한다. 후단이 곱한다.
- percent는 12.5%를 `value_reported=0.125`, `scale_multiplier=1`로 기록한다.

## adjustment candidates
다음을 발견하면 `adjustment_candidates`에 기록하되 recurring/non-recurring 최종 판정은 하지 않는다. 항상 `judgment_status="requires_economic_review"`다.

`restructuring`, `impairment`, `litigation`, `acquisition_cost`, `integration_cost`, `severance`, `asset_sale_gain_loss`, `unusual_tax`, `sbc`, `acquisition_amortization`, `working_capital_swing`, `subsidy`, `insurance_proceeds`, `capitalized_development`, `other`

반복 이력이 문서에서 확인되면 `recurrence_history`에 사실만 기록한다. 출력은 `possible_adjustment`이지 `normalized_out`이 아니다.

## 추출 우선순위
1. 최근 FY + 최근 8개 분기 revenue / operating income / net income
2. CFO / capex / SBC / R&D
3. basic·diluted weighted-average shares
4. cash / short-term investments / debt / lease liabilities
5. assets / liabilities / equity
6. stock repurchases / issuance / acquisitions
7. commitments / guarantees / converts
8. segment revenue 및 segment operating profit
9. adjustment candidates
10. restatement, KPI 정의 변경, 회계정책 변경

문서에 값이 없으면 만들지 않는다. 확보하지 못한 항목은 `extraction_warnings`에 무엇을 어디서 찾으려 했는지와 함께 남긴다.

## 금지 사항
- 투자 판단·등급·포지션 결정
- 경제적 정상화를 사실처럼 확정
- 출처 없는 수치 생성
- 2차 자료를 1차 자료처럼 표기
- 기준일 이후 자료 사용
- 자료가 없는 것을 0으로 처리
- 이미 전처리된 수치의 임의 재계산

## 검증
```bash
python harness.py intake <TICKER>          # Stage 0 문서 공백
python harness.py prompt <TICKER> FP       # 이 지침이 포함된 전처리 프롬프트
python harness.py validate-pack <TICKER>   # 스키마 + 불변식 검사
```
`validate-pack`은 fact_id·adjustment_id 중복, canonical metric 위반, 부호 규약 위반, 기간과 FY/Q 모순, GAAP/non-GAAP 혼동, dangling `amount_fact_id`를 검사한다.

공통 규칙: [`agents/COMMON.md`](../COMMON.md) — 단, 이 단계는 점수·Bull/Bear·Hard Veto를 산출하지 않으므로 해당 절은 적용되지 않는다.
