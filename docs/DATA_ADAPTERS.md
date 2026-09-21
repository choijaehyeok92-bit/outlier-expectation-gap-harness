# Data adapters — SEC and DART (Phase 3)

하네스는 숫자가 어느 규제기관에서 왔는지 몰라야 한다. 이 패키지의 존재 이유가 그것이다.
`SecEdgarProvider`와 `DartProvider`는 같은 `RegulatoryDataProvider` 인터페이스를 구현하고,
둘 다 기존 `schemas/financial_pack.schema.json`을 통과하는 문서를 만든다. Stage 0은 10-K든
사업보고서든 같은 모양을 읽는다.

> **라이브 호출은 검증되지 않았다.** 이 저장소가 만들어진 환경의 네트워크 정책이
> `www.sec.gov`·`data.sec.gov`·`opendart.fss.or.kr`를 모두 차단하고 OpenDART 키도 없다.
> 엔드포인트 경로·응답 필드명·상태코드는 공개 규격 문서를 근거로 **전부 config에 선언**했고,
> 파싱과 기간 산술은 기록 픽스처로 테스트했다. 실제 API와 어긋나면 코드가 아니라 config를 고친다.
> 모든 pack의 `ingestion.live_api_verified`는 `false`다.

---

## 계층

```
RegulatoryDataProvider          MarketDataProvider
  resolve_issuer()                resolve_security()
  list_filings(as_of_date)        get_snapshot(as_of_date)
  fetch_raw_filing()              get_price_history()
  fetch_structured_financials()   get_market_cap(as_of_date)
  fetch_share_data()
  build_financial_pack()
  list_universe()

  ├─ SecEdgarProvider (US)        ├─ UsMarketDataProvider   (CSV)
  └─ DartProvider     (KR)        └─ KrxMarketDataProvider  (KRX 호환 + CSV fallback)
```

**시장 데이터는 규제 provider와 완전히 분리한다.** `DartProvider`에는 가격 메서드가 아예 없고,
market provider에는 공시 메서드가 아예 없다. 테스트가 두 방향 모두를 검사한다. 주가는 공시가
아니며, 공시 API에서 꺼낸 가격은 어떤 거래소와도 대조할 수 없다.

**as_of 마감은 base 클래스가 강제한다.** `list_filings`는 구상 클래스의 `_all_filings`를 부른 뒤
마감일 이후를 잘라내고 무엇을 잘랐는지 함께 돌려준다. 각 provider가 기억해야 하는 규칙은 언젠가
한 쪽이 잊는다.

---

## 한국 (DART)

### corpCode 캐시
OpenDART는 모든 것을 8자리 `corp_code`로 식별한다. 매핑은 전체 법인 zip XML 한 번으로 받아
`data/dart/corp_codes.json`에 저장하고, 이후 `stock_code ↔ corp_code ↔ corp_name` 어느
방향으로든 해석한다. `stock_code`가 있으면 상장, 없으면 비상장이다.

### 시장 구분
corpCode.xml에는 KOSPI/KOSDAQ 구분이 **없다.** 세그먼트는 `company.json`·`list.json`의
`corp_cls`(Y 유가 / K 코스닥 / N 코넥스 / E 기타)에서 읽는다. `corp_cls`를 확인하지 못한 종목은
`exchange=KRX`, `requires_review=true`로 남기고 추측하지 않는다. KONEX는 config로 제외한다.

### 연결/별도 (CFS/OFS)
CFS 우선, 없으면 OFS. **한 pack 안에서 절대 섞지 않는다.** 선택은 pack 단위로 한 번 이뤄지고,
다른 기준의 fact는 경고와 함께 버려진다. 섞인 시계열은 중간에 다른 경제적 실체로 갈아타면서
존재하지 않은 성장률을 보고하는데, 하류의 어떤 단계도 그것을 볼 수 없다.

### quarter / YTD / FY / instant
가장 조용히 틀릴 수 있는 지점이라 명시적으로 처리한다.

| 상황 | 처리 |
|---|---|
| `sj_div=BS` | `instant`, period_end만 |
| 사업보고서(11011) | `fy` |
| 분기·반기보고서, 손익 두 컬럼 | `thstrm_amount` → `quarter`, `thstrm_add_amount` → `ytd`. **합치지 않는다** |
| 1분기보고서, 단일 컬럼 | `quarter` (3개월 = 누계 3개월이라 모호하지 않다) |
| 반기·3분기보고서, 단일 컬럼 | `ytd` + `requires_review`. 기간을 과소 기록하면 리뷰어에게 보이고, 과대 기록하면 성장처럼 보인다 |
| 현금흐름표 (`cumulative_only`) | **분기를 만들어내지 않는다.** 한국 공시는 현금흐름을 누계로만 내는 경우가 많아, 3분기보고서의 단일 컬럼은 9개월치다 |
| 비12월 결산 | `company.json`의 `acc_mt`로 회계연도 경계를 이동한다 (3월 결산 3분기 = 10~12월) |

`reprt_code`는 `config/dart.json`에 선언한다. 11011 사업보고서 · 11012 반기 · 11013 1분기 ·
11014 3분기.

### 계정 매핑
`config/account_mappings_kr.yaml` (버전 관리). 순서가 고정된 결정론적 체인이며 **LLM은 참여하지 않는다.**

1. `by_account_id` — XBRL element id 정확 일치 (가장 강한 신호)
2. `by_statement_label` — 재무제표 문맥 안에서의 라벨 일치
3. `by_label` — 정규화된 라벨 일치
4. `heuristics` — 순서 있는 부분문자열 규칙, 재무제표 범위 한정
5. 미일치 → `metric=other` + 원문 라벨 보존 + `requires_review=true`

각 fact는 어느 단계에서 매칭됐는지 기록한다. 모델에 매번 물으면 아무도 파일을 고치지 않았는데
시계열이 움직인다.

**의도적으로 리뷰로 올리는 항목**: `판매비와관리비`는 스키마의 `s_and_m`/`g_and_a`로 쪼개려면
공시에 없는 배분을 만들어야 하므로 합계 그대로 `other`로 보존한다. 미국 쪽 `SellingGeneral
AndAdministrativeExpense`도 같은 이유로 같은 처리를 받는다.

### 주식수·자본변동
`stockTotqySttus`에서 발행주식총수·자기주식수·유통주식수를, `config/dart.json`의
`capital_event_endpoints`에서 유상증자·무상증자·CB·BW·EB 발행결정을 마감일 이전만 수집한다.
**기존 희석 Hard Veto는 건드리지 않는다.** 이것들은 evidence layer의 관측값이며, veto 판정은
여전히 지정 owner의 몫이다.

### Stage 0 호환
`config/intake.json`을 **한 글자도 고치지 않았다.** 기존 `source_regex`가 이미
`사업보고서`·`분기보고서|반기보고서`·`주주총회소집|임원보수`·`잠정실적|영업실적`을 담고 있어서,
문서 이름을 `분기보고서_2026-05-15_20260515000123.xml`처럼 한국 서식명으로 시작하게 만들면
기존 체크리스트가 그대로 센다. 픽스처 기준 `required` 4개가 전부 충족된다.

---

## 미국 (SEC)

문서 수집은 **기존 `harness_core/fetch.py`를 그대로 재사용한다.** 티커→CIK 해석, submissions
인덱스, 마감일 준수, 공정이용 User-Agent가 이미 거기 있다. 두 벌을 맞게 유지하는 대신 감싼다.

추가한 것은 XBRL `companyfacts`를 정규화 fact로 옮기는 부분이다.

- **기간 종류**는 `start`/`end` 간격으로 판정한다 (`config/sec.json`의 `period_spans`). 어느 구간에도
  들어가지 않으면 만들어내지 않고 `ytd` + `requires_review`로 남긴다.
- **정정(restatement)**: 같은 (tag, 기간, 단위)가 여러 제출물에 나오면 마감일 이전 가장 최근
  제출을 쓰고, 이전 제출과 값이 다르면 `is_restated=true`와 함께 **이전 값을 보존한다.** 조용히
  최신값만 남기면 회사가 숫자를 바꿨다는 사실 자체가 지워진다.
- `SEC_USER_AGENT`가 없으면 거부한다. 하네스가 임의로 연락처를 만들어 보내지 않는다.

---

## 유니버스

```bash
python harness.py universe sync --markets US,KR --as-of 2026-09-18 \
  --user-agent "your name your@email" --enrich-limit 500
python harness.py universe show --market KR --investable-only
```

- **제외는 기록한다.** ETF·워런트·SPAC·우선주·단위증권·KONEX·OTC는 파일에 이유와 함께 남는다.
  "이건 왜 내 스크린에 없지?"의 답이 재실행 없이 나온다.
- **불확실은 해소가 아니다.** 거래소나 증권 종류를 확정하지 못한 종목은 조용히 버리지 않고
  `requires_review`로 남으며, 그 개수가 요약에 들어간다.
- 한 시장이 실패해도 다른 시장은 진행한다. DART 키가 잘못됐다고 미국 유니버스까지 잃지 않는다.

`GET /api/universe/securities`로 읽는다. 이것은 규제기관 기반 유니버스이며, 완료된 run 코퍼스를
요약하는 `GET /api/universe`와 다르다.

---

## 적재

```bash
python harness.py ingest 267260 --market KR --as-of 2026-09-18 --out /tmp/pack.json
python harness.py ingest MSFT   --market US --as-of 2026-09-18 --user-agent "..."
```

`--out` 없이 실행하면 어디에 놓아야 할지만 알려준다. **적재기는 run의 sources를 덮어쓰지 않는다.**
frozen run은 frozen이다.

---

## 오프라인 실행과 픽스처 갱신

```bash
python harness.py ingest 267260 --market KR --as-of 2026-09-18 --api-key TEST --fixtures
python harness.py universe sync --markets US,KR --fixtures --user-agent "test t@e.com" --api-key TEST
```

`--fixtures`는 `data_adapters/fixtures/{sec,dart}`의 기록 응답을 재생한다. 키와 망이 생기면
`RecordingTransport`로 진짜 응답을 받아 같은 자리에 덮어쓴다:

```python
from data_adapters.testing import RecordingTransport
DartProvider(transport=RecordingTransport('data_adapters/fixtures/dart'))
```

`fixture_key`는 파일명을 만들 때 `crtfc_key`를 제거하므로 기록된 픽스처가 API 키를 저장소로
끌고 들어올 수 없다. 테스트가 이것도 검사한다.

---

## 남은 것

- 라이브 API 검증 (키와 egress 필요)
- `financial_fact` 등 Phase 2 DB 테이블로의 적재 (현재는 파일)
- 결정론적 screening metric 계산 (Phase 4) — 이게 붙으면 `screening_warehouse` 백엔드가 켜지고
  지금 `backend_unavailable`로 남는 `revenue_cagr_3y` 같은 조건이 그대로 동작한다
- KRX 세그먼트 대량 enrich (현재는 issuer당 `company.json` 1회, `--enrich-limit`로 제한)
- 워커 큐 (Phase 3 후반) — 현재 적재는 동기 실행이다
