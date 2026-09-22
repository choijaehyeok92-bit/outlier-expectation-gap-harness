# Web platform — runbook

하네스 CLI는 그대로다. 아래는 새로 추가된 스크리닝·딥다이브 계층을 실행하는 방법이다.

## 0-1. 아이콘 하나로 실행하기

```powershell
.\scripts\install-shortcut.ps1        # 바탕화면에 아이콘 생성 (한 번만)
```

이후에는 **아이콘 더블클릭**이면 끝이다. API와 웹이 함께 뜨고 브라우저가 `/pipeline`에서
열리며, 창을 닫으면 둘 다 종료된다. `-StartMenu`를 주면 시작 메뉴에도 만들고, `-Remove`로
지운다. 서비스도 레지스트리 키도 시작프로그램 등록도 하지 않는다 — 지우는 건 파일 삭제다.

터미널에서 바로 돌리려면:

| 환경 | 명령 |
|---|---|
| Windows | `.\scripts\start.cmd` (또는 `.\scripts\start.ps1`) |
| macOS | `scripts/start.command` 더블클릭, 또는 `./scripts/start.sh` |
| Linux | `./scripts/start.sh` |

런처가 대신 처리하는 것들:

- **`NEXT_PUBLIC_API_BASE`와 `WEB_ORIGINS`를 한 곳에서 맞춘다.** 앞의 것은 웹 번들에 구워지고
  뒤의 것은 API의 CORS 목록이다. 하나만 맞추면 **화면은 뜨는데 아무것도 못 불러오고**, 증거는
  브라우저 콘솔에만 남는다. 이 저장소에서 이미 한 번 겪은 일이다.
- **포트를 먼저 확인한다.** 8000·3000이 쓰이고 있으면 빈 포트를 찾아 올라간다. 한쪽이 뜬
  뒤에 충돌을 알게 되는 것보다 낫다.
- **둘을 같이 죽인다.** 런처를 껐는데 uvicorn이 8000을 붙잡고 있으면, 다음 실행이 전혀 상관없어
  보이는 이유로 실패한다.
- **Python 3.10+ / Node 18.18+ 를 확인하고** 무엇을 설치하면 되는지 말한다. `node_modules`가
  없으면 `npm ci`를 한 번 돌린다.
- **`.env`를 읽는다.** `.env.example`를 `.env`로 복사해 채우면 되고, `.env`는 커밋되지 않는다.
  값은 API 프로세스의 환경변수로만 들어가며 브라우저로 전송되지 않는다. 비워 둬도 앱은 뜬다 —
  없는 자격증명은 그 단계만 막고, 화면이 어느 변수가 비었는지 말해 준다.

아이콘은 `scripts/make_icon.py`가 표준 라이브러리만으로 그린다. 아무도 다시 만들 수 없는
바이너리는 아무도 고칠 수 없는 바이너리다.

### `.ps1` 파일 인코딩 — 건드리면 안 되는 것

**`scripts/*.ps1`은 UTF-8 BOM 있는 상태를 유지해야 한다.** Windows PowerShell 5.1은
BOM 없는 `.ps1`을 시스템 ANSI 코드페이지로 읽는다. 한국어 Windows에서는 CP949이고,
`중`의 UTF-8 세 번째 바이트 `0x91`이 CP949에서 유효한 선행 바이트라 **바로 뒤의 작은따옴표를
삼킨다.** 문자열이 닫히지 않고, 파싱은 한참 뒤의 멀쩡한 중괄호에서 실패한다:

```
위치 ...\start.ps1:61 문자:1
+ }
식 또는 문에서 예기치 않은 '}' 토큰입니다.
```

이 저장소에서 실제로 겪은 오류다. 에디터가 BOM을 떼지 못하도록 `tests/test_launcher.py`가
검사하고, `.gitattributes`가 CRLF를 고정한다. `start.cmd`는 아예 ASCII만 쓴다 — cmd.exe는
또 다른 코드페이지(OEM)로 읽기 때문이다.

증상이 다시 보이면 파일이 BOM을 잃은 것이다:

```powershell
python -c "p=open('scripts/start.ps1','rb').read(); print(p[:3] == b'\xef\xbb\xbf')"
git checkout -- scripts/start.ps1      # 되돌리는 가장 빠른 방법
```

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

## 1a. 버튼 순서 (웹: `/pipeline`)

여덟 단계가 한 화면에 있고, 각 단계가 **완료 / 일부 / 해야 함 / 막힘** 중 하나로 표시된다.
무엇이 끝났고 무엇이 다음인지는 이 화면이 디스크를 읽어 말한다 — 순서를 외우고 있을 필요가 없다.

| # | 단계 | 비용 | 하는 일 |
|---|---|---|---|
| 0 | 명단 | 무료 | 상장 명단. 재무는 없다 |
| 1 | Stage 0 적재 | 무료 | 재무 사실(pack). SEC 3회 / DART 36회 per 기업 |
| 2 | 시세 | 무료 | 한 세션 종가, 일괄 호출 1회 |
| 3 | 지표 창고 | 무료 | 결정론적 지표. LLM 0 |
| 4 | 정량 스크리닝 | 무료 | 조건 통과분만. 점수·archetype 아직 없음 |
| 5 | Stage 3 triage | **유료** | 15개 중 4개 에이전트. 기업당 **4콜** |
| 6 | Stage 4 full harness | **유료** | 점수·archetype·Hard Veto·IC. 기업당 **15콜** |
| 7 | 심층 보고서 | **유료** | CLEARED · core ≥ 70 · early_exit 아님 |

**「무료 구간 한 번에」 버튼은 0·2·3·4만 묶는다.**

- 5단계부터 묶지 않는 이유: 한 번에 다 도는 버튼은 사람이 "다음"을 누를 때 돈이 나가는
  버튼이다. 유료 단계는 각각 **dry run이 먼저**이고, 대상 수와 예상 호출 수를 보여준 뒤
  **두 번째 클릭**에서야 실제로 돈다. 요청 본문의 기본값도 `dry_run: true`,
  `provider: placeholder`다.
- 1단계(적재)를 묶지 않는 이유: 어느 기업을 적재할지는 사람이 고르는 결정이다. `/universe`로
  보낸다.
- 한 단계가 실패하면 **거기서 멈춘다.** 시세를 못 받았는데 창고를 계속 만들면 운영자가
  갱신하라고 한 세션이 아니라 디스크에 우연히 있던 가격으로 짓는 것이고, 그런 조용한 대체는
  하지 않는다. 남은 단계는 개별 버튼으로 돌릴 수 있다고 알려준다.

`GET /api/pipeline/status`는 **읽기 전용**이다. 상태를 묻는 것이 상태를 바꾸면 다음 버튼
클릭을 아무도 해석할 수 없다.

### 유료 단계에서 실제 모델 고르기

각 유료 단계마다 **공급자 드롭다운**이 있다. 기본값은 그 단계의 오프라인 스텁이라 화면을 여는
것만으로는 과금되지 않는다.

| 단계 | 오프라인 기본값 | 하는 일 |
|---|---|---|
| triage · full harness | `placeholder` | 아무것도 분석하지 않고 배선만 확인한다 |
| 심층 보고서 | `fixture` | 저장된 응답을 재생한다 |

**두 오프라인 스텁은 같은 것이 아니다.** 단계에 맞지 않는 쪽을 쓰면 끝난 것처럼 보이지만
내용이 비어 있는 run이 나온다. 그래서 드롭다운이 단계별로 따로 있다.

`anthropic` / `openai`를 고르면 **모델 입력칸**이 나타난다. 비우면 기본값, 채우면 그 문자열이
**검증 없이 그대로 전달**된다 — 없는 이름이면 공급자가 돌려준 오류가 화면에 그대로 보인다.
과금 경고가 기업당 호출 수(triage 4, full 15, 심층 4)와 함께 표시된다.

```powershell
setx OPENAI_API_KEY "sk-..."       # 새 창을 열고 API를 재시작
setx ANTHROPIC_API_KEY "sk-ant-..."
```

키가 없는 공급자는 `· 키 없음`으로 표시되고, 고르면 **어느 환경변수가 비었는지** 알려준다
(422). 서버는 키가 있는지 여부만 브라우저에 알려주며 **키 자체나 그 앞자리는 절대 보내지
않는다** — `GET /api/pipeline/providers`, 테스트로 고정.

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

## 1b-1. 적재 대상 고르기 (웹: `/universe`)

```powershell
setx SEC_USER_AGENT "Your Name you@example.com"    # SEC는 키가 아니라 연락처를 요구한다
setx OPENDART_API_KEY "..."
```

`/universe` 화면이 세 단계다: ① 유니버스 동기화 ② 후보 순위 ③ 선택한 종목 적재.

**시가총액으로 자르지 않는다.** 시총은 종가 × 주식수이고 주식수는 공시에서 오므로, 적재 전에
시총으로 자르려면 아끼려던 적재를 먼저 해야 한다. 순위는 한 번의 bulk 호출로 얻는
**거래대금**이며, 이것은 다음 호출을 어디에 쓸지만 정한다 — 점수·archetype·Hard Veto·
밸류에이션 어디에도 들어가지 않는다.

한국 상장은 순위 없이 나열된다(KRX는 종목별 조회라 대조할 세션이 없다). 미국 시세 공급자가
죽어도 목록은 그대로 나오고, 이미 받아 둔 `data/market/US/*.csv`가 있으면 그것으로 순위를
매긴 뒤 출처를 밝힌다.

적재는 한 요청에 10개까지다 — 기업마다 규제기관 요청이 여러 번이라 더 넣으면 요청이
타임아웃되고 반쯤 쓰인 디렉터리가 남는다. 더 큰 배치는 워커 큐의 `ingest_pack`에 넣는다.
이미 있는 pack은 덮어쓰지 않는다.

```bash
# 같은 일을 CLI로
python harness.py universe sync --markets US,KR --as-of 2026-09-21 --enrich-limit 200
python harness.py ingest MSFT --market US --as-of 2026-09-21 --out data/packs/MSFT.json
```

## 1c. 스크리닝 창고 (Phase 4)

```bash
# 완료된 run들의 Stage 0 pack으로 지표 창고를 만든다
python harness.py screen build --as-of 2026-09-18 --from-runs

# 어댑터가 만든 pack + 시세 CSV로
python harness.py screen build --as-of 2026-09-18 \
  --packs /tmp/packs --from-runs --market-data data/market

# 창고가 생기면 정량 조건이 미해석 조건이 아니라 실제 필터가 된다
python harness.py screen run "매출총이익률 70% 이상이고 영업이익률 10% 이상" --as-of 2026-09-18
```

시세 CSV는 `data/market/<US|KR>/<TICKER>.csv` (`date,close,shares_outstanding[,market_cap]`).
가격은 `MarketDataProvider`에서만 오고 규제기관에서 오지 않는다. 미국 CSV를 손으로 만들지 않고
채우는 방법은 바로 아래 1c-1에 있다.
지표 정의와 계산하지 않는 경우는 [SCREENING_WAREHOUSE.md](SCREENING_WAREHOUSE.md)에 있다.

## 1c-1. 미국 시세 채우기

`market_cap`·`current_price`·`price_to_owner_fcf`는 시장 지표이고 `missing_policy: exclude`는
판정할 수 없는 조건을 가진 기업을 버린다. **디스크에 미국 종가가 없으면 시총이나 밸류에이션을
언급하는 스크린에서 미국 종목이 전부 빠진다.** 조건에 걸려서가 아니라 조건을 판정할 수 없어서다.

```powershell
setx POLYGON_API_KEY "..."        # 새 창을 열고 API를 재시작
```
```bash
python scripts/fetch_us_prices.py --as-of 2026-09-21 --dry-run   # 먼저 확인
python scripts/fetch_us_prices.py --as-of 2026-09-21
python harness.py screen build --as-of 2026-09-21 --packs <dir> --market-data data/market
```

한 세션 전 종목이 **호출 1회**로 온다. 무료 티어로도 기준일 하나는 충분하다(분당 5콜).
기준일이 휴장이면 직전 거래일까지 **뒤로만** 거슬러 올라간다. 기본 범위는 Stage 0 pack이 있는
종목이며 `--scope universe` / `--scope all` / `--tickers`로 넓힌다.

주식수는 시세 공급자가 아니라 Stage 0 pack(`dei:EntityCommonStockSharesOutstanding`)에서 온다.
둘 중 하나라도 없으면 시가총액은 미상이고 0으로 채우지 않는다.

웹에서는 `/market` 화면에서 같은 일을 한다 — 공급자·기준일·범위를 고르고, 먼저 「받아보기」로
확인한 뒤 쓴다. 커버리지(Stage 0 pack 대비 가격 보유 수, 가격 없는 종목 이름)를 함께 보여준다.
야간 자동화는 `market_fetch` 작업 종류이고 `nightly_us_prices` 스케줄은 **기본이 꺼짐**이다 —
키가 없는 기계에서 매일 밤 실패하는 작업을 만들지 않는다.

공급자 선택과 그 이유, 쓰지 않기로 한 공급자는 [DATA_ADAPTERS.md](DATA_ADAPTERS.md)에 있다.

## 1d. 데이터베이스 (Phase 2, 선택)

```bash
pip install -r db/requirements.txt
export HARNESS_DATABASE_URL="postgresql+psycopg://user:pass@host/harness"
python harness.py db upgrade
python harness.py db sync --as-of 2026-09-18       # 반복 실행 안전
python harness.py db status
python harness.py screen run "..." --as-of 2026-09-18 --source db

# 서버 없이 둘러보기
python harness.py db upgrade --sqlite
```

`HARNESS_DATABASE_URL`이 없으면 모든 것이 지금까지처럼 파일로 동작한다.
계약과 발견 사항은 [DATABASE.md](DATABASE.md)에 있다.

## 1e. Stage 3 triage (Phase 7)

```bash
# 무엇이 돌 것인지만 본다
python harness.py screen triage --as-of 2026-09-18 --top 20 --dry-run

# 오프라인 자리표시자 — 배선만 확인하고 분석하지 않는다
python harness.py screen triage --as-of 2026-09-18 --top 20

# 실제 모델: 돈을 쓰고 사람이 리서치로 읽을 보고서를 만든다
export ANTHROPIC_API_KEY=...
python harness.py screen triage --as-of 2026-09-18 --top 10 --provider anthropic

python harness.py screen triage-runs
```

자리표시자 provider는 분석하지 않으며 Hard Veto를 절대 clear하지 않는다. 무엇이 검증되고
무엇이 검증되지 않는지는 [ORCHESTRATION.md](ORCHESTRATION.md)에 있다.

## 1f. Stage 4 full harness (Phase 8)

```bash
# 무엇이 돌 것인지만 본다
python harness.py screen full --as-of 2026-09-18 --top 5 --dry-run

# 한 기업 (스크린 선정을 건너뛴다)
python harness.py screen full --run-id MSFT

# 실제 모델: 기업당 에이전트 호출이 13회 이상이다
export ANTHROPIC_API_KEY=...
python harness.py screen full --as-of 2026-09-18 --top 3 --provider anthropic

python harness.py screen full-runs
```

Stage 4는 에이전트 목록을 갖고 있지 않다. 매 회차 `harness.py plan`에게 다음 단계를 묻고
그 답을 실행하며, `stop_early`(조기 종료 = `screened_out`)나 `stop_complete`에서 멈춘다.
진전 없이 같은 단계가 반복되면 `stalled`로 멈추고 어느 단계가 막았는지 남긴다.

종료 시 하네스의 `digest`·`report`를 불러 `digest.md`·`easy_report.md`를 만든다.
`cache-macro`와 `one_page_investment_record.md`는 자동으로 만들지 않는다 — 전자는 전역 캐시를
오염시키고 후자는 IC 의장이 손으로 쓰는 문서다.

**저장된 run이 `blocked: frozen policy or harness changed`로 나오면** 그 run은 마지막 freeze
이후 `harness_core`/`harness.py`가 움직인 것이다. 오케스트레이터는 게이트를 우회하지 않으므로
사람이 검토 후 `python harness.py freeze <TICKER>`를 다시 해야 한다.

## 1g. Monitoring (Phase 12)

```bash
# 무엇을 보고 있는지 — 기계 판정 가능 여부까지
python harness.py monitor watchlist MSFT

# 관측 기록. 출처와 날짜가 없으면 거부된다
python harness.py monitor observe MSFT --match "Microsoft Cloud gross margin" \
  --value "64%" --as-of 2026-09-20 --source "FY26 Q4 10-K p.40" --source-type filing

# 지표와 잇기 — 제안은 정확히 일치할 때만 나오고, 거는 것은 사람이다
python harness.py monitor suggest MSFT
python harness.py monitor link MSFT --match "capex/OCF" --all-matches --metric capex_to_ocf
python harness.py monitor ingest MSFT --as-of 2026-09-18

# 평가와 포트폴리오
python harness.py monitor status MSFT
python harness.py monitor status --tickers MSFT,NVDA
python harness.py monitor drift NVDA
```

이름이 비슷하다는 이유로 자동 연결하지 않는다 — "Microsoft Cloud gross margin"에 전사
`gross_margin`을 붙이면 재지 않은 숫자가 임계값을 통과해 ok로 보고된다. 사람이 그래도 맞다고
판단하면 `operator_asserted`로 기록되고 그 사실이 모든 관측에 실린다.

`71`처럼 척도가 모호한 값은 비교하지 않고 거부한다. `"71%"`로 쓰거나 `--unit percent`를 준다.
`thesis_break`는 매도 신호가 아니라 재검토 요청이며, 이 계층은 점수·archetype·Hard Veto·
`ic_state`·비중을 바꾸지 않는다. 자세한 것은 [MONITORING.md](MONITORING.md).

관측 로그는 `monitoring/<TICKER>/observations.jsonl`이고 `HARNESS_MONITORING_DIR`로 저장소 밖에
둘 수 있다. **재생성이 불가능한 유일한 산출물이므로 gitignore하지 않았다.**

## 1h. Workers

```bash
python harness.py db upgrade                 # 0003까지 (job 테이블에 lease·백오프)

python harness.py worker enqueue screen_build --set as_of_date=2026-09-18
python harness.py worker run                 # 큐를 비우고 종료
python harness.py worker run --follow        # 데몬. SIGTERM은 진행 중 작업을 끝내고 나간다
python harness.py worker status
python harness.py worker jobs --status failed
python harness.py worker locks               # 누가 어느 기업을 잡고 있는가

# 되풀이되는 일 — crontab에는 이 한 줄만 둔다
python harness.py worker schedules           # 선언된 주기와 문법 검사
python harness.py worker schedule --dry-run  # 지금 무엇이 만기인가
python harness.py worker schedule            # 넣는다. 두 번 불러도 한 번만 들어간다
```

```cron
5 * * * *  cd /srv/harness && python harness.py worker schedule
* * * * *  cd /srv/harness && python harness.py worker run --max-seconds 55
```

큐는 `job` 테이블이다. 브로커가 없고 Redis도 필요 없다. **payload에 API 키를 넣지 않는다** —
`job.payload`는 저장되고 `/api/jobs`로 나간다. payload가 `provider: anthropic`을 요구해도
`config/workers.json`의 `providers.allowed`에 없으면 거부된다.

같은 기업을 건드리는 두 작업은 자원 잠금으로 직렬화된다 — `harness_full {run_ids:[MSFT]}`가
도는 동안 `deep_dive {run_id: MSFT}`는 claim되지 않고 **건너뛰어진다**(실패가 아니다). 워커를
여러 개 띄워도 안전하다. `worker status`의 `ready_but_locked`가 0이 아니면 긴 작업 뒤에서
기다리는 일이 있다는 뜻이다. 자세한 것은 [WORKERS.md](WORKERS.md).

## 1i. 스크리너에서 해석기·모델 고르기

웹 `/screener` 화면의 **해석기(parser)** 드롭다운에서 고른다. 기본값은 `lexicon`(결정론적,
오프라인)이라 **화면을 여는 것만으로 돈이 나가지 않는다.**

| 선택지 | 하는 일 |
|---|---|
| `lexicon` | `config/screening_lexicon.json` 어휘로 파싱. 모델 호출 없음 |
| `fixture` | 저장된 응답 재생 |
| `anthropic` · `openai` | 실제 모델. **호출마다 과금** |

`anthropic`/`openai`를 고르면 **모델 입력칸**이 나타난다. 비우면 기본값, 채우면 그 문자열이
**검증 없이 그대로 공급자에게 전달**된다 — 이 저장소는 모델 목록을 들고 있지 않으므로, 없는
이름이면 공급자가 돌려준 오류가 화면에 그대로 보인다.

키는 **API 프로세스의 환경변수**에 둔다:

```powershell
setx OPENAI_API_KEY "sk-..."      # 새 창을 열고 API를 재시작
setx ANTHROPIC_API_KEY "sk-ant-..."
```

키가 없는 해석기는 드롭다운에 `· 키 없음`으로 표시되고, 고르면 **어느 환경변수가 비었는지**
알려준다. 서버는 키가 있는지 여부만 브라우저에 알려주며 **키 자체나 그 앞자리는 절대 보내지
않는다**(`GET /api/screen/providers`, 테스트로 고정).

모델을 바꿔도 **판정 계층은 영향받지 않는다.** 모델이 하는 일은 문장을 ScreeningSpec으로
옮기는 것뿐이고, 점수·archetype·Hard Veto·밸류에이션은 하네스가 계산한다. 해석하지 못한
조건은 지어내지 않고 `unresolved_conditions`로 남는다.

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
python -m pytest tests/test_warehouse.py -q     # 창고 유무와 무관하게 통과해야 한다
python -m pytest tests/test_orchestration.py -q # 순서·재시도·idempotency (분석 품질 아님)
python -m pytest tests/test_database.py -q      # SQLite
HARNESS_TEST_DATABASE_URL=postgresql+psycopg://user@host/db \
  python -m pytest tests/test_database.py -q    # PostgreSQL
(cd apps/web && npm run build)                  # 타입 체크 포함
```
