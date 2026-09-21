# Web Research Platform — Architecture

이 문서는 기존 하네스를 **재작성하지 않고** 그 위에 4계층 웹 애플리케이션을 올리기 위한 설계다.
투자 철학, scorecard, archetype, Hard Veto, valuation, planner, freeze/as_of_date, evidence
provenance는 모두 기존 하네스가 source of truth이며 여기서 새로 만들지 않는다.

---

## 1. Current architecture summary

측정한 사실(이 저장소를 읽고 실행해 확인한 것):

| 영역 | 현황 |
|---|---|
| 진입점 | `harness.py` → `harness_core/runtime.py` (1,147줄). 20개 CLI 서브커맨드 |
| 정책 엔진 | `rubric` · `conditions` · `archetypes` · `veto` · `state` · `valuation` · `planner` · `dilution` · `macro_geo` · `evidence` |
| 정책 데이터 | `config/strategy.json` (v3.3, 8개 core 도메인 + 2개 축 + 1개 진단), `calibration.json`, `workflow.json`, `intake.json`, `agents_manifest.json` (15 agents) |
| 계약 | `schemas/` 5개 (`agent_report`, `company_context`, `financial_pack`, `final_verdict`, `research_packet`) |
| 실행 단위 | `runs/<RUN_ID>/` — `company_context.json`, `sources/`, `reports/*.json`, `aggregate.json`, `final_verdict.json`, `run_manifest.json` |
| 코퍼스 | 완료된 run 25개 (US 23, KR 2 — `000660` SK하이닉스, `267260` HD현대일렉트릭) |
| 재현성 | `freeze`가 입력·소스·정책·구현 모듈까지 SHA-256으로 고정. `assert_frozen_inputs`가 stale 실행을 거부 |
| 의존성 | 런타임은 표준 라이브러리만. `jsonschema`는 dev |
| 테스트 | 159개 통과 (`harness.py selftest`) |

핵심 구조적 특징:

- **결정론적 게이트**: archetype 적합성·Hard Veto·valuation sanity·state band가 모두 config 기반으로 계산된다. IC는 배분을 줄일 수 있을 뿐 게이트를 넘어설 수 없다 (`state.reconcile_ic`).
- **Hard Veto 소유권**: `veto.py`는 owner가 아닌 에이전트의 판정을 발견으로 강등하고 `UNRESOLVED`로 올린다. 침묵은 clear가 아니다.
- **missing ≠ 0**: `conditions.number()`가 유한 숫자만 값으로 인정하고, 없으면 `None`을 반환한다.
- **as_of_date 절대 마감**: `fetch.plan()`이 cutoff 이후 공시를 내려받지 않고, `research.validate_packet`이 cutoff 이후 증거를 `excluded_post_cutoff`로 분리한다.
- **이미 US/KR 이중 구조를 전제**: `config/intake.json`의 모든 요구사항이 `us`/`kr` 설명을 함께 갖고 있고, KRX 6자리 코드 run이 이미 존재한다.
- **Research Orchestrator는 웹/LLM을 직접 호출하지 않는다** — 질문을 만들고, 제출된 패킷을 검증하고, 불변 아카이브에 넣는다 (`docs/RESEARCH_ORCHESTRATOR.md`).

**이 설계가 지켜야 할 제약**: 기존 single-company CLI와 기존 run 아티팩트를 깨뜨리지 않는다.

---

## 2. Proposed architecture

```
┌─ apps/web (Next.js, TS, Tailwind) ──────────────────────────────┐
│  /screener  /companies/[t]  /runs/[id]  /deep-dive/[id]  /reports/[id]
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS (JSON). API key는 절대 내려가지 않는다
┌─ apps/api (FastAPI + Pydantic) ─────────────────────────────────┐
│  읽기 위주. 하네스를 재계산하지 않고, LLM을 데이터 계층에 닿게 하지 않는다  │
└──┬────────────┬──────────────┬───────────────┬───────────────────┘
   │            │              │               │
┌──▼─────────┐ ┌▼────────────┐ ┌▼───────────┐ ┌▼──────────────────┐
│ packages/  │ │ packages/   │ │ packages/  │ │ packages/llm      │
│ screening  │ │ research    │ │ reporting  │ │ provider 추상화    │
│ spec·compiler│ │ plan·stages│ │ markdown   │ │ fixture/anthropic │
│ ·nl·index  │ │ ·invariants │ │            │ │ /openai           │
└──┬─────────┘ └┬────────────┘ └────────────┘ └───────────────────┘
   │            │
┌──▼────────────▼────────────────────────────────────────────────┐
│ harness_core  (변경 없음 — 정책·점수·veto·valuation의 source of truth) │
└──┬──────────────────────────────────────────────────────────────┘
   │
┌──▼─────────────────────────────────────────────────────────────┐
│ data_adapters/{sec,dart,market_us,market_kr}  (Phase 3)          │
│  RegulatoryDataProvider / MarketDataProvider — 하네스는 provider를  │
│  알지 못하고, 양쪽 모두 financial_pack.schema.json을 만족시킨다       │
└──┬─────────────────────────────────────────────────────────────┘
   │
┌──▼─────────────────────────────────────────────────────────────┐
│ PostgreSQL (Phase 2~4) + Redis/ARQ workers (Phase 3~) + S3/FS    │
└─────────────────────────────────────────────────────────────────┘
```

### 역할 분리 (타협 없음)

| LLM이 하는 것 | LLM이 절대 하지 않는 것 |
|---|---|
| 자연어 → ScreeningSpec | SQL 생성·실행 |
| semantic classification | 재무지표 계산 |
| qualitative research | Harness score |
| evidence synthesis | Hard Veto status |
| report drafting | archetype / valuation formula / position sizing |

모든 LLM 출력은 JSON Schema로 검증되고, 실패하면 수리하지 않고 거부한다.

### 세 개의 경계

1. **ScreeningSpec** — 이 위는 산문, 이 아래는 결정론. 모델은 spec을 제안할 수 있지만 `config/screening_fields.json` allowlist에 있는 field만 쓸 수 있다.
2. **harness_snapshot** — 딥다이브가 하네스 결과를 읽는 유일한 통로. 보고서 안에서 하네스 값이 나타날 수 있는 유일한 위치이며, 불변식이 원본과의 일치를 강제한다.
3. **untrusted source data** — 원문 공시는 데이터이지 지시가 아니다. 프롬프트 래퍼가 구분자를 무력화하고, 구조적 방어(스키마 검증·SQL 불가·점수 불가)가 실제 보호를 한다.

---

## 3. New files

### 이번 vertical slice에서 실제로 추가된 것

```
packages/__init__.py
packages/cli.py                          harness.py에 붙는 screen/deep-* 서브커맨드 (지연 import)
packages/llm/{__init__,providers}.py     LLMProvider 추상화 + Fixture/Anthropic/OpenAI
packages/screening/
  fields.py      field registry loader (allowlist)
  units.py       억/조/%/KRW/USD 파싱. 환율은 절대 추정하지 않는다
  spec.py        ScreeningSpec 검증·정규화·content-addressed id
  compiler.py    3값(Kleene) 논리 컴파일러. missing은 false도 0도 아니다
  nl.py          LexiconParser(결정론) + LLMParser(동일 검증 경로)
  runs_index.py  runs/ → 정규화 행 (읽기 전용)
  store.py       screen_runs/ 불변 저장
packages/research/
  deep_plan.py   config 기반 선정 + 도메인·질문·로컬 증거 목록
  stages.py      4단계 스키마 (report 스키마에서 파생)
  prompts.py     단계별 프롬프트 (독립성 프로토콜 포함)
  invariants.py  스키마가 표현할 수 없는 규칙
  deep_run.py    단계 실행 → 조립 → 검증 → 불변 저장
  untrusted.py   원문 인용 래핑
  store.py       deep_dive/ 불변 저장
  fixtures/{MSFT,000660}/*.json   오프라인 재생 픽스처 (생성물)
packages/reporting/render.py             markdown 렌더링
apps/api/{main,models}.py, requirements.txt
apps/web/                                Next.js 15 + TS + Tailwind 4, 6개 페이지
config/screening_fields.json             57개 field registry
config/screening_lexicon.json            한국어/영어 표현 → field 매핑
config/deep_dive.json                    선정 정책 · 14 도메인 · 10 질문 · Red Team mandate · 불변식
schemas/screening_spec.schema.json
schemas/deep_dive_plan.schema.json
schemas/deep_dive_report.schema.json
scripts/build_deep_dive_fixture.py       실제 run에서 픽스처 생성
tests/{test_screening,test_deep_dive,test_api}.py
docs/WEB_PLATFORM_ARCHITECTURE.md
```

### Phase 3에서 추가된 것

```
data_adapters/
  types.py base.py http.py         공통 엔티티·provider 인터페이스·주입 가능 transport
  pack.py                          financial_pack.schema.json 호환 pack 조립 (CFS/OFS 비혼합)
  marketdata.py                    CSV/HTTP 시장 데이터 기반 클래스
  universe.py cli.py testing.py    유니버스 동기화·CLI·오프라인 transport
  sec/{provider,xbrl}.py           SecEdgarProvider (harness_core/fetch.py 재사용) + companyfacts
  dart/{provider,corpcode,accounts,periods}.py
                                   DartProvider + corpCode 캐시 + 계정 체인 + 기간 산술
  market_us/, market_kr/           MarketDataProvider (KRX 호환)
  fixtures/{sec,dart}/             오프라인 기록 응답
config/{sec,dart,market_kr}.json   엔드포인트·보고서코드·연결기준·유니버스 필터
config/account_mappings_kr.yaml    XBRL account_id → 정규화 metric (버전 2026.09.1)
scripts/build_{sec,dart}_fixtures.py
tests/test_data_adapters.py
docs/DATA_ADAPTERS.md
```

### Phase 4에서 추가된 것

```
packages/screening/
  facts.py                         pack 색인 + TTM/FY/instant 창 해석 (세그먼트·마감일 필터)
  metrics.py                       표현식 트리 계산기 (ttm/fy 두 문맥)
  warehouse.py                     지표 창고 빌드·저장·백엔드 행
  rows.py                          harness_run_index + screening_warehouse 병합
config/screening_metrics.json      24개 공개 지표 정의 + TTM·CAGR·증가율 정책
tests/test_warehouse.py
docs/SCREENING_WAREHOUSE.md
```

### 이후 Phase에서 추가될 것

```
db/migrations/                           Alembic
workers/                                 ARQ 작업: universe sync, ingestion, metric build, triage, full, deep research
```

---

## 4. Modified files

| 파일 | 변경 | 호환성 |
|---|---|---|
| `harness_core/runtime.py` | `register_application_commands(sub)` 추가, `main()`에서 1회 호출 | 기존 20개 서브커맨드 인자·동작 불변. import 실패 시 조용히 건너뛴다 |
| `.gitignore` | `node_modules/`, `.next/` 등 | — |
| `README.md` / `ARCHITECTURE.md` / `tests/README.md` | 새 계층 안내 | — |

**변경하지 않은 것**: `config/strategy.json`, `config/calibration.json`, `config/workflow.json`,
`config/intake.json`, `config/agents_manifest.json`, `schemas/` 기존 5개, `harness_core/` 나머지
20개 모듈, `runs/` 아티팩트 전부, `agents/` 전부.

`config_hashes()`가 `harness_core/*.py`를 해싱하므로 `runtime.py` 변경은 기존 frozen run의 재freeze를
요구한다 — **읽기에는 영향이 없다**(`assert_frozen_inputs`는 `require_frozen_inputs`가 켜진 쓰기 경로에서만
동작하며, 새 계층은 전부 읽기 전용이다). 이 점이 마음에 걸리면 §12의 대안을 쓴다.

---

## 5. DB schema (Phase 2~4)

vertical slice는 DB 없이 `runs/`를 읽는다. 아래는 US/KR 전체 유니버스가 들어올 때의 스키마다.

```sql
-- 발행인: 관할과 규제기관 식별자를 함께 보유한다
CREATE TABLE issuer (
  issuer_id            BIGSERIAL PRIMARY KEY,
  jurisdiction         TEXT NOT NULL CHECK (jurisdiction IN ('US','KR')),
  regulator            TEXT NOT NULL CHECK (regulator IN ('SEC','DART')),
  regulator_issuer_id  TEXT NOT NULL,              -- CIK / corp_code
  legal_name           TEXT NOT NULL,
  industry             TEXT, sector TEXT,
  UNIQUE (regulator, regulator_issuer_id)
);

CREATE TABLE security (
  security_id   BIGSERIAL PRIMARY KEY,
  issuer_id     BIGINT NOT NULL REFERENCES issuer,
  ticker        TEXT NOT NULL,
  exchange      TEXT NOT NULL,                     -- NASDAQ/NYSE/NYSE American/KOSPI/KOSDAQ
  currency      CHAR(3) NOT NULL,
  security_type TEXT NOT NULL,                     -- common/etf/cef/preferred/warrant/spac/...
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (exchange, ticker)
);

-- 시장 데이터는 규제 provider와 완전히 분리된다
CREATE TABLE market_snapshot (
  security_id        BIGINT NOT NULL REFERENCES security,
  as_of_date         DATE NOT NULL,
  close              NUMERIC(20,6),
  market_cap         NUMERIC(24,2),
  shares_outstanding NUMERIC(20,4),
  source             TEXT NOT NULL,
  PRIMARY KEY (security_id, as_of_date)
);

CREATE TABLE financial_fact (
  fact_id             BIGSERIAL PRIMARY KEY,
  issuer_id           BIGINT NOT NULL REFERENCES issuer,
  metric              TEXT NOT NULL,               -- financial_pack.schema.json의 metric enum
  metric_detail       TEXT,
  value               NUMERIC(28,6),
  currency            CHAR(3),
  period_start        DATE, period_end DATE,
  period_kind         TEXT NOT NULL CHECK (period_kind IN ('instant','quarter','ytd','fy')),
  fiscal_year         INT, fiscal_quarter INT,
  filing_date         DATE NOT NULL,
  source              TEXT NOT NULL,               -- accession / rcept_no
  consolidation_basis TEXT NOT NULL CHECK (consolidation_basis IN ('CFS','OFS')),
  confidence          NUMERIC(4,3),
  requires_review     BOOLEAN NOT NULL DEFAULT FALSE,
  is_amendment        BOOLEAN NOT NULL DEFAULT FALSE,
  supersedes_fact_id  BIGINT REFERENCES financial_fact,
  CHECK (period_kind <> 'fy'      OR fiscal_quarter IS NULL),
  CHECK (period_kind <> 'quarter' OR fiscal_quarter IS NOT NULL)
);
-- 한 발행인·한 기간 안에서 CFS와 OFS를 섞지 않기 위한 제약의 근거가 되는 인덱스
CREATE INDEX financial_fact_lookup
  ON financial_fact (issuer_id, metric, period_kind, period_end, consolidation_basis, filing_date DESC);

-- 정정공시는 원본을 덮어쓰지 않는다: 둘 다 보존하고 supersedes로 잇는다
CREATE TABLE filing (
  filing_id    BIGSERIAL PRIMARY KEY,
  issuer_id    BIGINT NOT NULL REFERENCES issuer,
  regulator    TEXT NOT NULL,
  form_type    TEXT NOT NULL,                      -- 10-K/10-Q/사업보고서/분기보고서/...
  reprt_code   TEXT,                               -- DART: 11011/11012/11013/11014
  filing_date  DATE NOT NULL,
  period_end   DATE,
  is_amendment BOOLEAN NOT NULL DEFAULT FALSE,
  raw_uri      TEXT NOT NULL,                      -- S3 또는 로컬 경로
  raw_sha256   CHAR(64) NOT NULL,
  UNIQUE (regulator, raw_sha256)
);

-- 결정론적으로 계산된 스크리닝 지표. LLM은 이 표를 쓰지 않는다
CREATE TABLE screening_metric (
  security_id   BIGINT NOT NULL REFERENCES security,
  as_of_date    DATE NOT NULL,
  metric        TEXT NOT NULL,                     -- config/screening_fields.json의 field id
  value         NUMERIC(28,8),                     -- NULL은 미상이며 0이 아니다
  currency      CHAR(3),
  inputs_sha256 CHAR(64) NOT NULL,                 -- 재현용
  computed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (security_id, as_of_date, metric)
);

-- 하네스 실행 인덱스. 권위는 runs/ 아티팩트에 있고 이 표는 색인이다
CREATE TABLE harness_run (
  run_id                 TEXT PRIMARY KEY,
  security_id            BIGINT REFERENCES security,
  as_of_date             DATE NOT NULL,
  stage                  TEXT NOT NULL,            -- triage / full / complete / early_exit
  core_score             NUMERIC(6,2),
  ex_valuation_score     NUMERIC(6,2),
  classification         TEXT, archetype TEXT,
  hard_veto_status       TEXT, ic_state TEXT, position_range TEXT,
  price_to_base_value    NUMERIC(12,6),
  domain_scores          JSONB NOT NULL DEFAULT '{}',
  strategy_version       TEXT, decision_policy_version TEXT,
  code_commit_sha        CHAR(40),
  input_snapshot_sha256  CHAR(64),
  aggregate_sha256       CHAR(64) NOT NULL,
  artifact_uri           TEXT NOT NULL
);

CREATE TABLE screen_run (
  screen_run_id   TEXT PRIMARY KEY,
  as_of_date      DATE NOT NULL,
  spec            JSONB NOT NULL,
  spec_id         TEXT NOT NULL,
  backend         TEXT NOT NULL,
  summary         JSONB NOT NULL,
  results         JSONB NOT NULL,
  content_sha256  CHAR(64) NOT NULL,
  code_commit_sha CHAR(40) NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE deep_dive (
  deep_dive_id          TEXT PRIMARY KEY,
  run_id                TEXT NOT NULL REFERENCES harness_run,
  as_of_date            DATE NOT NULL,
  route                 TEXT NOT NULL,             -- automatic / optional / early_exit
  report                JSONB NOT NULL,
  red_team_overall      TEXT NOT NULL,
  agreement_with_harness TEXT NOT NULL,
  content_sha256        CHAR(64) NOT NULL,
  provider_metadata     JSONB NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE job (
  job_id       BIGSERIAL PRIMARY KEY,
  kind         TEXT NOT NULL,   -- universe_sync / ingest / metric_build / triage / full / deep_research / report
  status       TEXT NOT NULL CHECK (status IN ('queued','running','completed','failed','cancelled')),
  idempotency_key TEXT NOT NULL UNIQUE,            -- 재시도가 중복 작업을 만들지 않게 한다
  payload      JSONB NOT NULL,
  error        TEXT,
  attempts     INT NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**불변 규칙**: 과거 run을 새 데이터로 덮어쓰지 않는다. `harness_run`·`screen_run`·`deep_dive`는
append-only이며, 재실행은 새 행을 만든다. `value IS NULL`은 미상이고 0이 아니다.

---

## 6. ScreeningSpec schema

전체 정의는 `schemas/screening_spec.schema.json`. 요지:

```jsonc
{
  "schema_version": "1.0",
  "spec_id": "SPEC-…",              // 질문의 내용 해시 (파서 타임스탬프는 제외)
  "source": {"kind": "natural_language", "text": "…",
             "parser": {"provider": "lexicon|anthropic|openai", "model": null,
                        "parsed_at_utc": "…", "lexicon_sha256": "…"}},
  "as_of_date": "2026-09-18",       // 절대 마감일
  "universe": {"jurisdictions": ["US","KR"], "exchanges": [], "industries": [],
               "sectors": [], "tickers": [], "exclude_security_types": []},
  "filters": {"op": "and", "clauses": [                 // AND/OR 중첩 가능
    {"field": "net_cash_per_share", "operator": ">", "value": 0,
     "unit": "local_currency", "origin_text": "순현금",
     "rationale": "…"},
    {"op": "or", "clauses": [ /* … */ ]}
  ]},
  "fx_rates": {"KRW": {"per_usd": 1380.2, "source": "…", "as_of_date": "…"}},
  "sort": [{"field": "core_score", "direction": "desc"}],
  "limit": 50,
  "missing_policy": "exclude",      // exclude | require_review | include
  "requires_harness_run": true,
  "unresolved_conditions": [
    {"text": "최근 3년 매출 CAGR 15% 이상", "reason": "backend_unavailable",
     "suggested_field": "revenue_cagr_3y", "detail": "…"}
  ]
}
```

**연산자**: `=` `==` `!=` `<` `<=` `>` `>=` `in` `not_in` `between`.
(요구 목록에 `>`/`>=`가 빠져 있었으나 "15% 이상", "순현금"이 이를 요구하므로 대칭 집합으로 지원한다.)

**결정론적 규칙**

1. `field`는 `config/screening_fields.json`에 선언된 57개 식별자만 허용한다. 그 밖은 `no_mapped_field`.
2. 백엔드가 아직 없는 field는 `backend_unavailable`로 남는다. 조용히 사라지지 않는다.
3. `unit: ratio`는 소수다. 1.5를 넘는 값은 퍼센트 오기로 보고 **거부**한다(0으로 바꾸지 않는다).
4. 통화 임계값은 명시된 `fx_rates` 없이는 변환하지 않는다 → `missing_fx_rate`.
5. 해석 불가 조건은 전부 `unresolved_conditions`에 원문으로 보존한다.
6. **missing은 0이 아니다.** 컴파일러는 3값 논리(참/거짓/미상)로 평가하고, `missing_policy`가
   미상 행의 운명을 마지막에 결정한다. `!=`도 미상 값에 대해서는 미상이다.

**의미 매핑은 config에만 있다** (`config/screening_lexicon.json`):

| 표현 | 매핑 | 비고 |
|---|---|---|
| 순현금 | `net_cash_per_share > 0` | frozen context |
| Base 가치 이하 | `price_to_base_value <= 1.0` | 하네스 DCF |
| 해자가 강함 | `domain.moat_trajectory >= 75` | **하네스 run이 없으면 해자를 추정하지 않고 `requires_harness_run`** |
| 희석이 적음 | `dilution_watch_status in [none, clean, low]` | 희석 Hard Veto는 건드리지 않는다 |
| 3년 매출 CAGR | `revenue_cagr_3y` | Phase 4 전까지 `backend_unavailable` |

`revenue_cagr_next_3y`(EV 에이전트의 **전망치**)를 과거 CAGR 대용으로 쓰지 않는다. 레지스트리에 그 경고가 명시되어 있다.

---

## 7. DeepDive schema

`schemas/deep_dive_plan.schema.json` (요청) · `schemas/deep_dive_report.schema.json` (결과).

보고서 최상위 구조:

```
metadata            deep_dive_id, ticker, jurisdiction, as_of_date,
                    harness_run{run_id, aggregate_sha256, policy versions},
                    provenance{code_commit_sha, stages[{stage, provider, model, prompt_sha256}]}
harness_snapshot    하네스에서 그대로 복사. 이 문서에서 하네스 수치가 나타날 수 있는 유일한 위치
investment_question 10개 필수 질문 + 답 + 근거 + 확신도
evidence            evidence_id, claim, source, source_origin, source_tier(0~5),
                    publication_date, period, as_of_date, fact_or_estimate,
                    economic_driver, confidence, verified_fact_refs
executive_summary
business_model / industry / customer_product / moat / moat_trajectory /
growth_runway / unit_economics / per_share_economics / financial_quality /
management / capital_allocation / technology_disruption / risk_analysis /
valuation_interpretation                      ← 14개 정성 섹션 (아래 형식)
bull_case / base_case / bear_case
red_team            overall, supporting_harness, contradicting_harness,
                    domains_with_material_disagreement, reason, attack_paths[11개 벡터 중]
harness_comparison  가장 강한 지지/반박 증거, 과대평가 가능 지점, 놓친 지점,
                    해소되지 않은 모순, by_domain 일치도
falsifiers          statement / observable / would_break
monitoring_kpis     name, why_it_matters, current_value, direction_required,
                    warning_threshold, thesis_break_threshold, cadence, source
remaining_unknowns / evidence_quality / final_synthesis
```

정성 섹션 형식(숫자 점수를 새로 만들지 않는다):

```json
{"assessment": "strong|favorable|mixed|weak|critical",
 "direction": "strengthening|stable|weakening|unclear",
 "confidence": 0.0, "thesis": "",
 "supporting_evidence": [], "contradicting_evidence": [],
 "unknowns": [], "falsifiers": []}
```

`additionalProperties: false`라서 `"ai_score": 91` 같은 필드는 스키마 단계에서 거부된다.

### 스키마가 표현할 수 없어 코드로 강제하는 불변식 (`packages/research/invariants.py`)

1. 모든 evidence 참조는 실재해야 한다.
2. 모든 evidence의 `publication_date <= as_of_date`.
3. `harness_snapshot`은 원본 run과 정확히 일치해야 한다 → **딥다이브가 점수·veto·포지션을 바꿀 수 없다**.
4. **positive-only 연구 거부**: 각 정성 섹션은 반박 증거 또는 선언된 unknown 중 하나를 반드시 가져야 한다.
   반대 증거를 못 찾았다면 그 사실을 unknown으로 적는다.
5. Red Team 필수, 서로 다른 공격 벡터 최소 3개.
6. `harness_comparison`에서 발견된 material disagreement는 `red_team`에 반드시 살아남아야 한다.
7. falsifier 필수, monitoring KPI 필수(각 KPI에 `thesis_break_threshold` 필수).
8. 10개 투자질문 전부 답변.

### 독립성 순서

`deep_research` → `qualitative` → `red_team` → `synthesis`. 각각 별도 provider 호출이며 단계별로 검증된다.
정성 단계 프롬프트는 순서를 명시한다: **증거 → 독립 판단 → 그 다음에만 하네스와 비교**.
금지 예시("Harness MT=90이므로 moat가 강하다")가 프롬프트에 그대로 들어간다.

---

## 8. API routes

| Method | Route | 상태 |
|---|---|---|
| GET | `/api/health` | ✅ |
| GET | `/api/universe` | ✅ (현재는 완료된 run 인덱스) |
| GET | `/api/universe/securities` | ✅ SEC/DART 기반 상장 유니버스 |
| GET | `/api/warehouse`, `/api/warehouse/{ticker}` | ✅ 지표 커버리지 · 기업별 provenance |
| GET | `/api/screen/fields` | ✅ field registry |
| GET | `/api/runs`, `/api/runs/{run_id}` | ✅ 읽기 전용 |
| GET | `/api/companies/{ticker}` | ✅ 기본정보 + 하네스 이력 + 딥다이브 목록 |
| POST | `/api/screen/parse` | ✅ 자연어 → ScreeningSpec (+ unresolved) |
| POST | `/api/screen/run` | ✅ spec 또는 text 실행 + 불변 저장 |
| GET | `/api/screen/runs`, `/api/screen/runs/{id}`, `…/markdown` | ✅ |
| POST | `/api/harness/triage` | ⏸ 501 (Phase 7) |
| POST | `/api/harness/full` | ⏸ 501 (Phase 8) |
| GET | `/api/harness/runs/{id}` | ✅ |
| POST | `/api/deep-dive/plan` | ✅ |
| POST | `/api/deep-dive/run` | ✅ |
| GET | `/api/deep-dive`, `/api/deep-dive/{id}` | ✅ |
| GET | `/api/reports/{id}?fmt=json\|markdown` | ✅ |

미구현 단계는 그럴듯한 답을 만들지 않고 501과 해당 Phase를 반환한다.

---

## 9. CLI additions

기존 20개 서브커맨드는 인자·동작 모두 그대로다. 추가된 것:

```bash
python harness.py screen fields [--available-only]
python harness.py screen nl "미국과 한국에서 시총 1조 이상, 순현금이고 해자가 강한 종목" \
       --as-of 2026-09-18 --fx KRW=1380.2 [--provider lexicon|anthropic|openai] [--out spec.json]
python harness.py screen query --spec spec.json [--save] [--markdown out.md] [--full]
python harness.py screen run "…" --as-of 2026-09-18 --fx KRW=1380.2 [--markdown out.md]
python harness.py screen runs
python harness.py deep-plan MSFT [--force] [--out plan.json]
python harness.py deep-run  MSFT [--provider fixture|anthropic|openai] [--markdown report.md] [--force]
python harness.py deep-report <deep_dive_id> [--out report.md]
python harness.py deep-list
```

이후 Phase에서 추가될 것: `universe sync --markets US,KR`, `screen build --as-of …`,
`screen triage --input results.json --top 100`, `screen full --input triage.json --top 30`,
`screen deep-dive --input leaderboard.json --top 10`.

**지연 import**: 새 커맨드의 구현은 핸들러 안에서 import된다. `harness.py aggregate`는 스크리닝
스택을 로드하지 않으며, `packages/`가 없는 체크아웃에서도 기존 CLI가 전부 동작한다.

---

## 10. Implementation phases

| Phase | 내용 | 상태 |
|---|---|---|
| 1 | 기존 하네스 read-only API | ✅ 완료 |
| 2 | DB + run index (PostgreSQL, Alembic) | ⏳ 현재는 파일시스템 인덱스 |
| 3 | US/KR universe + SEC/DART ingestion | ✅ 어댑터·유니버스·적재 완료 (라이브 API 미검증) |
| 4 | screening warehouse (결정론적 지표 계산) | ✅ 24개 지표·provenance·조건부 백엔드 완료 |
| 5 | ScreeningSpec | ✅ 완료 |
| 6 | NL screener | ✅ 완료 (lexicon + LLM 양쪽) |
| 7 | Harness triage orchestration | ⏸ 501 |
| 8 | Full Harness orchestration | ⏸ 501 |
| 9 | Deep-Dive Research | ✅ 완료 (fixture provider로 검증) |
| 10 | Red Team + synthesis | ✅ 완료 |
| 11 | Report UI | ✅ 완료 |
| 12 | Monitoring | ⏳ KPI 스키마·표시는 완료, 시계열 추적은 미구현 |

Phase 5·6·9·10·11이 먼저 완성된 것은 vertical slice를 먼저 관통시켰기 때문이다.
Phase 4가 붙으면서 `screening_warehouse` 백엔드가 조건부로 활성화됐고, `backend_unavailable`로
남던 조건들이 창고를 빌드한 뒤에는 그대로 컴파일된다 — spec 형식은 바뀌지 않았다.
남은 것은 Phase 2(DB), Phase 7·8(오케스트레이션), Phase 12(모니터링 시계열)다.

---

## 11. Major risks

| # | 위험 | 왜 위험한가 | 완화 |
|---|---|---|---|
| 1 | **CFS/OFS 혼합** | 연결/별도를 섞은 시계열은 성장률과 마진을 조용히 왜곡한다 | `financial_fact.consolidation_basis` 필수. CFS 우선, 없으면 OFS, 한 시계열 안에서 혼합 금지를 적재 단계에서 검증 |
| 2 | **한국 계정 매핑** | 계정명이 회사·연도별로 다르고 LLM 추론은 재현되지 않는다 | XBRL `account_id` → 버전 관리되는 alias map → statement context → 결정론적 휴리스틱 → `requires_review`. LLM은 매핑에 쓰지 않는다 |
| 3 | **quarter / YTD 혼동** | DART는 누적 기준 공시가 많다. Q3 누적을 분기로 읽으면 성장률이 무너진다 | `period_kind` 필수 + 하네스 `intake.pack_invariants`의 기존 검증 재사용 |
| 4 | **환율** | 조용한 환산은 시총 필터를 통째로 어긋나게 한다 | 환율을 절대 조회하지 않는다. 명시 없으면 `missing_fx_rate`로 조건을 적용하지 않는다 |
| 5 | **미래 데이터 누출** | 과거 run에 미래 정보가 섞이면 전체 코퍼스의 신뢰가 무너진다 | `as_of_date` 절대 마감. 컴파일러가 cutoff 이후 run을 `excluded_post_cutoff`로 분리, 딥다이브 불변식이 cutoff 이후 증거를 거부 |
| 6 | **LLM 월권** | 모델이 점수·veto·SQL을 만들면 결정론이 사라진다 | 모든 출력이 JSON Schema 검증. field allowlist. SQL 경로 없음. `harness_snapshot` 일치 강제 |
| 7 | **프롬프트 인젝션** | 공시 원문에 지시문이 들어올 수 있다 | 원문을 구분자로 감싸고 구분자를 무력화. 구조적 방어(모델이 도달할 수 있는 것이 스키마 검증된 JSON뿐)가 실질 보호 |
| 8 | **positive-only research** | 하네스를 정당화하는 보고서는 아무 정보가 없다 | 반박 증거 또는 선언된 unknown 필수. Red Team 별도 단계. 최소 3개 공격 벡터 |
| 9 | **비용 폭주** | 전체 유니버스에 Full Harness/딥다이브를 돌리면 비용이 통제 불능 | 4단계 깔때기(universe → cheap quant → triage → full). cheap quant 구간에 LLM 사용 금지. 딥다이브는 config 기반 상위 후보만 |
| 10 | **missing을 0으로** | 조용한 잘못된 답이 나온다 | 3값 논리 + `missing_policy`. 테스트가 `!=`·`or`·정렬까지 검증 |
| 11 | **레거시 run 호환** | 코퍼스가 여러 정책 버전을 가로지른다 | 읽기 층이 `aggregate.json` 우선, `final_verdict.json` 대체. 은퇴한 archetype 문자열과 구 IC state를 그대로 표시하고 다시 쓰지 않는다 |
| 12 | **fixture를 리서치로 오독** | 데모 보고서가 실제 조사로 보이면 위험하다 | provenance에 `provider: fixture` 기록. markdown과 UI 양쪽에 경고 배너 |

---

## 12. Migration / backward compatibility plan

### 지금 보장된 것 (측정)

- `python harness.py selftest` — **241개 테스트 통과** (기존 159 + 신규 82).
- 기존 20개 서브커맨드의 파서·인자·동작 불변. `plan` / `aggregate` / `digest` / `report` 출력 동일.
- `runs/` 아티팩트 단 하나도 수정하지 않았다. 읽기 층은 mtime 불변을 테스트로 검증한다.
- `config/` 기존 5개 파일과 `schemas/` 기존 5개 파일 무수정.
- `harness_core/` 20개 모듈 중 `runtime.py` 하나만, `main()`에 한 줄과 헬퍼 하나를 추가했다.

### 유일하게 주의할 지점

`config_hashes()`는 `harness_core/*.py`를 포함하므로 `runtime.py` 변경은 **frozen run의 정책 해시를
바꾼다**. 영향 범위:

- **읽기**: 영향 없음. `assert_frozen_inputs`는 `aggregate`/`digest`/`prompt`/`report` 같은 쓰기 경로에서만
  호출되고, 새 계층은 전부 읽기 전용이다.
- **기존 run에 대한 재실행**: `freeze`를 다시 해야 한다. 이는 정책 변경 시 기존에도 동일하게 요구되던
  절차이며(`docs/RESEARCH_ORCHESTRATOR.md`의 "정책 변경과 재현"), `fork-run`이 입력을 바이트 그대로
  복사하는 경로를 그대로 쓴다.
- **실측**: 변경 전 커밋과 변경 후를 각각 체크아웃해 25개 run 전부에 `harness.py digest`를 돌려
  pass/fail 집합을 비교했다. **완전히 동일하다.** 코퍼스의 모든 run이 이미 더 오래된 harness
  커밋으로 freeze되어 있어 이 변경으로 상태가 바뀐 run은 하나도 없다. 위 위험은 이론적으로는
  맞지만 이번 변경에서 관측된 영향은 없다.
- **이것도 피하고 싶다면**: `packages/cli.py`를 별도 진입점(`screener.py`)으로 두고 `runtime.py`를
  전혀 건드리지 않는 선택지가 있다. 비용은 `python harness.py screen …` 형태를 포기하는 것이다.
  요청이 그 형태를 명시했으므로 현재는 `runtime.py`에 한 줄을 넣는 쪽을 택했다.

### 데이터 이행 (Phase 2~3)

1. `runs/`를 권위 있는 아티팩트로 유지한다. DB의 `harness_run`은 **색인**이며 원본이 아니다.
2. 최초 적재는 `runs/`를 읽어 `harness_run`을 채운다 — 점수를 재계산하지 않고 `aggregate_sha256`으로
   원본과 묶는다.
3. SEC/DART 적재는 새 issuer/security/filing/financial_fact를 만든다. 기존 run의 `sources/`는 건드리지 않는다.
4. `financial_pack.schema.json` 호환 출력을 두 provider 모두가 만들어, 하네스는 provider 종류를 모른 채
   동작한다.
5. 과거 run을 새 데이터로 덮어쓰지 않는다. 새 as_of_date는 새 run이다.

### 롤백

새 계층 전체를 지워도 하네스는 그대로 동작한다. 남는 것은 `runtime.py`의 헬퍼 한 개이며,
`packages/` import 실패 시 조용히 건너뛰도록 되어 있어 그 자체로 안전하다.
