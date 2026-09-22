# Database layer (Phase 2)

선택 계층이다. `HARNESS_DATABASE_URL`을 설정하지 않으면 하네스도 스크리너도 딥다이브도
지금까지와 똑같이 파일로 동작한다. 설정해야만 켜진다.

> **가장 먼저 분명히 할 것**: 이 계층은 하네스 run의 source of truth가 **아니다.**
> `runs/<RUN_ID>/aggregate.json`이 source of truth이고, `harness_run` 테이블은 그 위의
> **색인**이며 `aggregate_sha256`으로 파일과 묶여 있다. 하네스가 무엇을 판정했는지 알고
> 싶으면 아티팩트를 읽는다. 그것을 빨리 찾고 싶으면 테이블을 읽는다.

검증 환경: PostgreSQL 16.13(실제 서버)과 SQLite 양쪽에서 마이그레이션 적용·되돌리기,
전체 테스트 24개 통과.

---

## 테이블 13개

```
issuer ─┬─ security ─┬─ market_snapshot        시장 데이터 (규제기관과 분리)
        │            ├─ screening_metric       계산된 지표 (Phase 4)
        │            └─ harness_run            runs/ 위의 색인
        ├─ filing ───── financial_fact         공시 사실 (CFS/OFS 포함)
screen_run    deep_dive                        실행된 스크린·딥다이브
monitoring_watch_item                          보고서가 선언한 감시 항목 (Phase 12)
monitoring_observation                         관측된 사실 (Phase 12)
job           sync_log                         작업 큐·동기화 감사
```

`db/models.py`가 정의이고 `db/migrations/versions/`의 `0001_initial_schema.py`와
`0002_monitoring.py`가 스키마다.

---

## 세 가지 규칙

### 1. 판정은 append, 계산은 replace

이 구분이 이 계층의 핵심이다.

| 종류 | 테이블 | 규칙 |
|---|---|---|
| **판정·관측** | `harness_run`, `screen_run`, `deep_dive`, `monitoring_observation` | 덮어쓰지 않는다. run을 다시 집계하면 다른 `aggregate_sha256`을 가진 **새 행**이 들어가고 이전 행은 남는다. `is_current`만 움직인다. 관측도 같다 — 정정은 `supersedes`를 채운 새 행이다 |
| **계산·파생** | `screening_metric`, `monitoring_watch_item` | upsert한다. 정의를 고쳐 다시 계산하면 값이 바뀌어야 한다 — config에 정의를 둔 이유가 그것이다. 워치아이템은 보고서에서 파생되므로 같은 규칙을 따른다 |

제자리에서 update하는 테이블은 숫자가 바뀌었다는 사실 자체를 지운다. 리뷰어가 봐야 하는
것이 정확히 그것이다.

실측:

```
MSFT current rows: [(76.0, 'ffffffff')]
MSFT all rows:     [(74.75, '3715e20c'), (76.0, 'ffffffff')]
```

### 2. NULL은 미상이고 0이 아니다

`screening_metric`은 **시도한 모든 지표**에 행을 만든다. 계산하지 못한 것도 사유와 함께.

- `value IS NULL` + `unavailable_reason` → 시도했고 거부했다
- 행 자체가 없음 → 시도한 적이 없다

이 둘은 다른 사실이고 스키마가 다르게 보관한다. 현재 코퍼스에서 336개 지표 행 중
상당수가 전자다.

### 3. 재실행은 아무것도 바꾸지 않는다

`db sync`를 두 번 돌리면 두 번째는 전부 `skipped`여야 한다. 각 로더가 안정적인 키를 쓴다:
규제기관 식별자, accession 번호, fact의 내용 해시, run의 `aggregate_sha256`.

```
run 1: inserted=0 updated=0 skipped=336
run 2: inserted=0 updated=0 skipped=336
```

**여기서 실제로 버그가 하나 나왔다.** 지표 컬럼이 `NUMERIC(38,10)`이라 float이 저장·조회를
거치며 미세하게 달라지고, 그 값을 메모리의 값과 그냥 비교하면 매 동기화마다 모든 행이
`updated`로 찍힌다. 비교와 저장 전에 컬럼의 소수 자릿수로 반올림해서 해결했다.

---

## 두 dialect

PostgreSQL이 타깃이고 스키마는 그쪽에 맞춰져 있다(JSONB, CHECK 제약). SQLite는 **두 번째
프로덕션 타깃이 아니라**, 서버 없이 단위 테스트에서 스키마·마이그레이션·동기화를 전부
돌리기 위한 것이다. 그 차이가 "매 커밋마다 검증되는 마이그레이션"과 "누가 기억할 때 검증되는
마이그레이션"의 차이다.

```bash
python -m pytest tests/test_database.py -q                       # SQLite
HARNESS_TEST_DATABASE_URL=postgresql+psycopg://... \
  python -m pytest tests/test_database.py -q                     # PostgreSQL
```

SQLite는 기본적으로 외래키를 무시하므로 연결 시 `PRAGMA foreign_keys=ON`을 건다. 그러지
않으면 프로덕션에 있는 제약을 테스트하지 않는 셈이 된다.

CHECK 제약은 실제로 거부한다(양쪽에서 테스트됨):

```sql
ck_fact_fy_has_no_quarter     period_kind='fy'인데 fiscal_quarter가 있으면 거부
ck_fact_quarter_has_quarter   period_kind='quarter'인데 fiscal_quarter가 없으면 거부
ck_fact_consolidation         CFS/OFS 외의 값 거부
ck_job_status                 정의되지 않은 상태 거부
```

---

## 실행

```bash
pip install -r db/requirements.txt

export HARNESS_DATABASE_URL="postgresql+psycopg://user:pass@host/harness"
python harness.py db upgrade                       # 마이그레이션
python harness.py db sync --as-of 2026-09-18       # 아티팩트 적재 (반복 안전)
python harness.py db status                        # 행 수 · 최근 동기화
python harness.py db rows --as-of 2026-09-18       # 스크린이 읽을 행
python harness.py db company MSFT                  # 한 기업의 전부

# 서버 없이 둘러보기
python harness.py db upgrade --sqlite
```

동기화 대상은 `--kinds`로 고른다: `universe,runs,packs,warehouse,screens,deep-dives`.

### 스크리너가 DB를 읽게 하기

```bash
python harness.py screen run "..." --as-of 2026-09-18              # auto
python harness.py screen run "..." --as-of 2026-09-18 --source db
python harness.py screen run "..." --as-of 2026-09-18 --source files
```

`auto`는 `HARNESS_DATABASE_URL`이 설정된 경우에만 DB를 쓴다. 설정 자체가 명시적 opt-in이므로
아무것도 조용히 DB에 의존하기 시작하지 않는다.

**두 경로는 같은 답을 내야 한다.** 색인이 파일과 다른 답을 내면 그것은 색인이 아니다.
`EquivalenceTests`가 실제 코퍼스로 이 동등성을 검사한다 — 같은 순서의 같은 종목, 같은
`core_score`·`hard_veto_status`·`archetype`·`ic_state`·`price_to_base_value`.

---

## 실제 적재 결과

```
runs        inserted=25   (완료된 하네스 run 색인)
packs       inserted=7216 (16개 pack의 공시 사실)  unreadable=1
warehouse   inserted=336  (14개 기업 × 24개 지표)
```

### 발견: `runs/MA`의 Stage 0 pack이 잘려 있다

적재 중에 `runs/MA/sources/financials/normalized_financials.json`이 **FACT-0032 중간에서
끊긴 채 커밋되어 있는 것**을 발견했다. 커밋 `c6bb660`부터 있던 상태이며 이번 작업이 만든
것이 아니다.

- 이 파일을 **고치지 않았다.** 잘린 재무 pack을 복구하려면 없는 숫자를 만들어야 한다.
- 대신 **조용히 건너뛰지 않고 보고**하도록 바꿨다. `db sync`와 `screen build` 모두
  `unreadable`에 파일과 사유를 남긴다.
- `harness.py validate-pack MA`는 현재 깔끔한 메시지 대신 JSONDecodeError 트레이스백을
  낸다. `harness_core`는 이번에도 수정하지 않았으므로 그대로 두었다.

---

## 관측의 숫자와 척도는 함께 저장된다

`monitoring_observation`은 `value_text`(쓰인 그대로)와 `(value_number, unit)`을 함께 남긴다.
**NULL인 `unit`은 의미가 있다** — 기록한 사람이 척도를 말하지 않았다는 뜻이고, 그것이 바로
평가기가 추측하기를 거부하는 경우다. `value_number`만 읽고 `unit`을 무시하는 질의는 사실의
절반만 읽는다. 71%를 `71`로 적고 0.73 임계값과 비교하면 위반이 ok로 보고되는데, 그 사고를
막는 유일한 장치가 이 한 쌍이다.

`source`가 NOT NULL인 이유도 같다. 추적할 수 없는 숫자는 증거가 아니고, 그것으로 계산한
상태는 상태가 없는 것보다 나쁘다.

---

## 남은 것

- 워커 큐가 `job` 테이블을 실제로 소비하지 않는다. 테이블과 idempotency key는 있고
  (`enqueue`가 같은 키로 중복 작업을 만들지 않는 것은 테스트됨) 소비자가 없다
- `financial_fact.supersedes_fact_id` 컬럼은 있으나 적재기가 아직 연결하지 않는다.
  정정 관계는 현재 pack의 `is_restated` 플래그와 provenance에만 있다
- 증분 동기화 없음 — `db sync`는 전체를 훑고 변경분만 쓴다. 현재 규모(7천 행)에서는
  충분하지만 유니버스 규모에서는 아니다
- 읽기 전용 복제본·커넥션 풀 튜닝 등 운영 설정 없음
- 모니터링 평가 스냅샷은 색인되지 않는다. `monitoring_runs/`의 파일로만 남고 DB에는
  워치아이템과 관측만 들어간다
