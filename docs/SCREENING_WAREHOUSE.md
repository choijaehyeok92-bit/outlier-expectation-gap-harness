# Screening warehouse (Phase 4)

전체 유니버스에 Full Harness를 돌리는 것은 감당할 수 없다. 그래서 그 앞에 값싸고 **전적으로
기계적인** 통과 관문을 둔다. 여기서 "기계적"이 핵심이다: 이 계층의 모든 숫자는 Python이 계산하고,
LLM은 정의 파일도 계산도 건드리지 않는다. 모델에 매번 물으면 아무도 파일을 고치지 않았는데
시계열이 움직이고, 그 위에 세운 모든 임계값이 함께 움직인다.

```
US/KR universe (Phase 3)
  → SEC/DART 적재 → Stage 0 pack (Phase 3)
    → 결정론적 지표 계산 → screening warehouse   ← 이 문서
      → ScreeningSpec 필터 (Stage 1·2)
        → Harness Triage (Phase 7)  →  Full Harness (Phase 8)
```

---

## 표현식 트리와 두 개의 문맥

지표는 표현식 트리이고, 트리는 두 문맥 중 하나에서 평가된다.

- `('ttm', '2026-09-18')` — 기준일 기준 최근 12개월
- `('fy', 2025)` — 특정 회계연도

같은 트리가 두 문맥을 모두 처리하기 때문에 **주당 3년 CAGR에 별도 코드 경로가 필요 없다**.
그것은 주당 표현식을 두 회계연도에서 평가한 것일 뿐이다.

정의는 전부 `config/screening_metrics.json`에 있다. kind는
`ttm · ttm_average · instant · component · difference · sum · ratio · per_share · growth · cagr · market`.

---

## TTM: 세 가지 경로, 가장 최신 창이 이긴다

| 방법 | 성립 조건 |
|---|---|
| `four_quarters` | 연속된 분기 fact 4개. 사이가 끊기면 창 전체를 버린다 |
| `fy_ytd_bridge` | 직전 FY + 당기 누계 − 전년 동기 누계. 두 누계의 **개월수가 같아야** 한다 |
| `latest_fy` | 중간보고 이후 자료가 없을 때 최근 사업연도 |

**첫 번째로 성립하는 방법이 아니라, 창이 가장 늦게 끝나는 방법이 이긴다.** 9개월 중간보고와 그
이후의 사업보고서를 모두 가진 기업은 사업보고서 기준으로 재야 한다. 순서대로 골랐다면 3개월
묵은 창을 조용히 보고했을 것이다. 창 끝이 같으면 더 정밀한(앞선) 방법이 이긴다.

**분기와 누계는 절대 같은 합에 들어가지 않는다.** 겹치기 때문이다. Phase 3 어댑터가 둘을 별도
fact로 분리해 둔 것을 여기서 되섞으면 그 작업이 무효가 된다.

한국 현금흐름표는 누계만 공시하는 경우가 많아 `four_quarters`가 성립하지 않는다. `fy_ytd_bridge`가
존재하는 이유가 그것이다.

주식수는 **합이 아니라 평균**이다. 분기 가중평균주식수 4개를 더하면 발행주식이 네 배인 회사가 된다.

---

## 계산하지 않는 것들

각 항목은 조심하지 않은 구현이 그럴듯한 오답을 내놓는 지점이다.

| 상황 | 결과 |
|---|---|
| 세그먼트 행 | 전사 합계가 아니다. `segment`가 비었거나 연결/합계로 선언된 fact만 쓴다 |
| 마감일 이후 제출 | 쓰지 않는다. 어떤 기간을 설명하든 이 run이 갖지 못했던 정보다 |
| 필수 구성요소 누락 | 지표는 미상이다. **0이 아니다** — 부채를 공시하지 않은 것이 무차입을 뜻하지 않는다 |
| 선택 구성요소 누락 | 0으로 더하되 `assumptions`에 기록한다. 없는 줄과 0인 줄을 구분한다 |
| 분모가 0 | 계산하지 않는다. 매출 0이 마진 무한대를 뜻하지 않는다 |
| 분모가 음수 | 계산하지 않는다. 비교 방향이 뒤집힌다 |
| 기준값 ≤ 0인 증가율 | 계산하지 않는다. 적자 축소를 몇 퍼센트 성장으로 보고하면 스크린이 거짓말을 한다 |
| 끝점이 양수가 아닌 CAGR | 수학적으로 정의되지 않는다. 큰 수가 아니라 미상이다 |
| 같은 기간 서로 다른 연결 값 | 최신 제출을 쓰고 대안을 리뷰로 올린다 |
| 너무 오래된 창 | `max_staleness_days`를 넘기면 쓰지 않는다 |

### 세그먼트 규칙은 실제 사고에서 나왔다

이 창고를 실제 run 데이터에 처음 돌렸을 때 RBRK의 매출총이익률이 **2037%**로 나왔다. 원인은
`Revenue by geography — APAC` 행이 같은 기간의 마지막 행이라는 이유만으로 전사 매출로 읽힌
것이었다. 세그먼트 필터를 넣은 뒤 0.801이 됐다. 테스트가 이 사례를 그대로 고정한다.

---

## owner FCF는 대용치다

`owner_fcf_ttm = ocf_ttm − capex_ttm`.

이것은 **스크리닝용 기계적 대용치**이며, 하네스 EV 에이전트가 쓰는 정상화 owner FCF와 다른
수치다. 후자는 유지보수 capex와 일회성 항목에 대한 경제적 판단이 들어간 값이다. 정의에
`is_proxy: true`가 붙어 있고, 이 값이 하네스의 판단을 대신하지 않는다.

같은 이유로 `판매비와관리비` / `SellingGeneralAndAdministrativeExpense`는 `s_and_m`과
`g_and_a`로 쪼개지 않는다. 쪼개려면 공시에 없는 배분을 만들어야 한다.

---

## 두 백엔드의 병합

| 백엔드 | 담는 것 |
|---|---|
| `harness_run_index` | 하네스가 실제로 분석한 기업. 고정된 입력, 검토된 숫자, 소유자가 있는 Hard Veto |
| `screening_warehouse` | 적재된 모든 기업의 기계적 지표. 아직 아무도 보지 않은 기업 포함 |

**둘 다 값을 가진 필드는 하네스가 이긴다.** 하네스 값은 freeze되고 검토된 것이고, 창고 값은 pack에
대한 계산이다. 각 행이 `field_sources`에 필드별 출처를 기록하므로 검토된 수치와 계산된 수치를
구분할 수 있다.

**하네스 run이 없는 기업은 버리지 않고 남긴다.** 그것이 값싼 사전 스크린의 존재 이유다. 그런 행의
하네스 필드는 단순히 없으므로, 그 위의 필터는 미상으로 평가되고 기본 `missing_policy`가 랭킹에서
제외하며 spec의 `requires_harness_run` 플래그가 이유를 말한다. UI는 이들을 `정량만`으로 표시하고
별도 섹션에 모은다.

환율은 여기서도 조회하지 않는다. 원화 시총을 달러 임계값과 비교하려면 호출자가 기준일 환율을
명시해야 하고, 없으면 `market_cap_usd`는 미상으로 남는다.

---

## 조건부 백엔드

`config/screening_fields.json`에서 `screening_warehouse`는 `status: conditional`이다. 선언된
데이터 경로에 파일이 있을 때만 켜진다.

- **빌드 전**: `revenue_cagr_3y` 같은 조건은 조용히 사라지지 않고 `backend_unavailable`
  미해석 조건으로 남는다.
- **빌드 후**: 같은 문장이 그대로 컴파일된다. ScreeningSpec 형식은 바뀌지 않는다.

Phase 1에서 registry에 백엔드 구분을 넣어 둔 이유가 이것이다.

---

## 실행

```bash
# 완료된 run들이 이미 갖고 있는 Stage 0 pack으로 창고를 만든다
python harness.py screen build --as-of 2026-09-18 --from-runs

# 어댑터가 만든 pack으로 (Phase 3의 ingest --out 결과)
python harness.py ingest 267260 --market KR --as-of 2026-09-18 --out packs/267260.json
python harness.py screen build --as-of 2026-09-18 --packs packs/ --market-data data/market

# 이제 정량 조건이 실제 필터가 된다
python harness.py screen run "매출총이익률 70% 이상이고 영업이익률 10% 이상" --as-of 2026-09-18
```

시세는 `--market-data`의 `MarketDataProvider`에서만 온다. 규제기관은 가격을 공시하지 않는다.

읽기:

```
GET /api/warehouse              커버리지와 계산하지 못한 항목
GET /api/warehouse/{ticker}     한 기업의 지표 + 숫자별 provenance
```

---

## Provenance

모든 값이 감사 가능하다.

```json
{"metric_id": "revenue_ttm", "value": 5476000000000.0,
 "method": "fy_ytd_bridge",
 "inputs": ["FACT-0415", "FACT-0476", "FACT-0535"],
 "period_end": "2026-06-30",
 "requires_review": false}
```

어느 방법이 만들었는지, 어떤 fact를 소비했는지, 그 fact 중 하나라도 리뷰 대상이었는지
(예: 한국 중간 손익계산서의 단일 모호 컬럼) 함께 남는다. 숫자는 쓸 수 있고, 플래그는 따라다닌다.

---

## 남은 것

- Phase 2 DB(`screening_metric` 테이블)로의 적재 — 현재는 파일
- 워커 큐에서의 증분 재계산 — 현재는 전체 재빌드
- 산업·섹터 상대 지표 (현재 지표는 전부 절대값)
- 실제 유니버스 규모에서의 성능 (현재 16개 기업, 전량 메모리)
