# Web platform — runbook

하네스 CLI는 그대로다. 아래는 새로 추가된 스크리닝·딥다이브 계층을 실행하는 방법이다.

## 0. 의존성

```bash
pip install -r requirements-dev.txt          # jsonschema (하네스 + 스크리닝 패키지)
pip install -r apps/api/requirements.txt     # FastAPI, uvicorn, pydantic  (API를 띄울 때만)
(cd apps/web && npm install)                 # Next.js  (UI를 띄울 때만)
```

`packages/screening`·`packages/research`·`packages/reporting`은 표준 라이브러리와 `jsonschema`만 쓴다.
FastAPI와 Pydantic은 `apps/api`에만 있다.

## 1. CLI만으로

```bash
# 어떤 field를 쓸 수 있는가
python harness.py screen fields --available-only

# 자연어 → ScreeningSpec (실행하지 않고 해석만)
python harness.py screen nl \
  "미국과 한국에서 시총 1조 이상, 순현금이고 해자가 강하고 Base 가치 이하인 종목" \
  --as-of 2026-09-18 --fx KRW=1380.2 --out /tmp/spec.json

# 실행 + 불변 저장
python harness.py screen run \
  "미국과 한국에서 시총 1조 이상, 순현금이고 해자가 강하고 Base 가치 이하인 종목" \
  --as-of 2026-09-18 --fx KRW=1380.2 --markdown /tmp/screen.md

# 딥다이브 계획 → 실행 → 보고서
python harness.py deep-plan MSFT
python harness.py deep-run  MSFT --markdown /tmp/MSFT.md
python harness.py deep-list
```

환율은 조회되지 않는다. `--fx KRW=1380.2`를 주지 않으면 원화 임계값 조건은 적용되지 않고
`unresolved_conditions`에 `missing_fx_rate`로 남는다.

## 1b. SEC / DART 적재 (Phase 3)

```bash
pip install -r data_adapters/requirements.txt     # PyYAML (한국 계정 맵)

# 오프라인: 기록 픽스처로 전체 경로를 실행한다
python harness.py ingest 267260 --market KR --as-of 2026-09-18 --api-key TEST --fixtures
python harness.py ingest MSFT   --market US --as-of 2026-09-18 \
  --user-agent "test t@example.com" --fixtures
python harness.py universe sync --markets US,KR --as-of 2026-09-18 \
  --user-agent "test t@example.com" --api-key TEST --fixtures

# 라이브: 키와 연락처가 필요하다. 둘 다 백엔드 secret이며 프론트엔드로 가지 않는다
export OPENDART_API_KEY=...
export SEC_USER_AGENT="your name your@email"
python harness.py universe sync --markets US,KR --as-of 2026-09-18 --enrich-limit 500
python harness.py universe show --market KR --investable-only
python harness.py ingest 267260 --market KR --as-of 2026-09-18 --out /tmp/pack.json
```

`--out` 없이 실행하면 pack을 어디에 놓아야 할지만 알려준다. 적재기는 run의 sources를 덮어쓰지
않는다. 자세한 계약과 한국 특유의 처리는 [DATA_ADAPTERS.md](DATA_ADAPTERS.md)에 있다.

## 2. API

```bash
uvicorn apps.api.main:app --reload --port 8000
curl -s localhost:8000/api/health
curl -s localhost:8000/api/universe
curl -s -X POST localhost:8000/api/screen/run \
  -H 'content-type: application/json' \
  -d '{"text":"한국과 미국에서 순현금이고 해자가 강한 종목","as_of_date":"2026-09-18","persist":false}'
```

OpenAPI 문서는 `http://localhost:8000/docs`.

## 3. UI

```bash
cd apps/web
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE
npm run dev                       # http://localhost:3000
```

CORS 허용 오리진은 백엔드의 `WEB_ORIGINS` 환경변수로 정한다
(기본값 `http://localhost:3000,http://127.0.0.1:3000`).

## 4. LLM provider

기본값은 오프라인 `fixture`다. 실제 모델을 쓰려면:

```bash
export HARNESS_LLM_PROVIDER=anthropic     # 또는 openai
export HARNESS_LLM_MODEL=claude-opus-5
export ANTHROPIC_API_KEY=…                # 백엔드에만 둔다. 프론트엔드로 내려가지 않는다
python harness.py screen nl "…" --as-of 2026-09-18 --provider anthropic
```

모든 모델 출력은 JSON Schema로 검증되며, 실패하면 수리하지 않고 거부된다.

## 5. 픽스처 재생성

```bash
python scripts/build_deep_dive_fixture.py MSFT
python scripts/build_deep_dive_fixture.py 000660
```

픽스처는 해당 run의 실제 기록(에이전트 evidence·counterevidence·unknowns·falsifiers·KPI)에서
생성된다. 손으로 쓴 가짜 증거가 아니지만 **독립 리서치도 아니다** — 보고서 provenance에
`provider: fixture`가 남고, markdown과 UI 모두 경고 배너를 띄운다.

## 6. 테스트

```bash
python harness.py selftest                      # 전체 (하네스 + 신규 계층)
python -m pytest tests/test_screening.py -q
python -m pytest tests/test_deep_dive.py -q
python -m pytest tests/test_api.py -q           # FastAPI 미설치 시 자동 skip
python -m pytest tests/test_data_adapters.py -q # PyYAML 미설치 시 자동 skip
(cd apps/web && npm run build)                  # 타입 체크 포함
```
