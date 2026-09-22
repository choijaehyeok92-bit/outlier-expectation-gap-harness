# Workers — `job` 테이블을 소비한다

Phase 2가 `job` 테이블과 `idempotency_key`를 만들어 두고 소비자를 남겨 두었다. 이 계층이
그 소비자다. 워커가 하는 일은 **이미 존재하는 진입점을 부르는 것**이고, 인자는 `argparse`
대신 행에서 온다. 점수·archetype·Hard Veto·`ic_state`·비중은 여전히 하네스가 정한다.

---

## 1. 큐는 데이터베이스다 (브로커를 두지 않았다)

아키텍처 문서는 원래 Redis/ARQ를 적어 두었다. 그대로 가지 않은 이유를 먼저 적는다.

| | 브로커 | 테이블 |
|---|---|---|
| `job`에 이미 있는 것 | — | `idempotency_key`·`status`·`attempts` |
| 경쟁 소비자 분배 | 브로커가 한다 | `SELECT … FOR UPDATE SKIP LOCKED` |
| 배포 | 서비스 하나 더 | 없음 |
| **단위 테스트** | 서비스가 떠 있어야 한다 | **두 방언 모두 서비스 없이 검증된다** |

마지막 줄이 결정했다. **검증되지 않는 큐는 큐가 아니다.** 이 저장소는 Redis를 설치할 수도
없는 환경에서 돌고, 돌려볼 수 없는 의존성을 추가하는 것은 추가하지 않는 것보다 나쁘다.

핸들러 계약에는 transport가 등장하지 않는다. 나중에 브로커를 앞에 붙여도 `workers/handlers.py`는
한 줄도 바뀌지 않는다.

PostgreSQL에서는 `FOR UPDATE SKIP LOCKED`로, SQLite에서는 `UPDATE … WHERE status='queued'`의
rowcount로 claim한다. 같은 보장을 다른 경로로 얻는다.

## 2. 큐가 실제로 필요로 한 것 (migration 0003)

0001의 `job`은 작업을 **기록**할 수 있었지 **나눠 줄** 수는 없었다. 세 가지가 없었다.

| 컬럼 | 없으면 생기는 일 |
|---|---|
| `available_at` | 실패한 작업이 즉시 `queued`로 돌아가 고장난 의존성을 상대로 루프 속도만큼 재시도한다. 백오프는 sleep이 아니라 타임스탬프다 |
| `lease_expires_at` · `worker_id` | 워커가 죽으면 그 행은 영원히 `running`이다. 잃어버린 작업도 끝난 작업도 아닌, **아무도 하고 있지 않은 작업**이 된다 |
| `max_attempts` (행별) | config 기본값은 큐의 것이고, 비싼 작업 하나에 다른 상한을 주려면 행이 들고 있어야 한다 |

`started_at`·`finished_at`은 나중에 읽기 위해, `priority`는 claim 순서를 위해 있다. 인덱스는
`(status, available_at)` — claim 조건 그대로다.

## 3. lease가 만료되면 다시 돌린다 → 그래서 핸들러는 idempotent여야 한다

이게 유일한 진짜 계약이다. 죽은 워커의 작업을 되살리려면 두 번 실행될 수 있어야 하고,
두 번 실행해도 안전해야 한다. 등록된 핸들러는 전부 그렇고, **우연이 아니다**:

- `run_agent`는 완료·유효한 보고서가 있는 에이전트를 건너뛴다
- `db sync`는 전부 키(내용 해시·accession·aggregate_sha256)로 upsert한다
- 관측 로그는 같은 내용을 두 번 쓰지 않는다
- 불변 저장소는 내용이 같으면 같은 id를 돌려준다

되살리기가 무한하지 않은 이유는 `attempts`가 이미 올라가 있기 때문이다. `max_attempts`에
닿으면 `failed`로 멈춘다.

## 4. payload는 권한을 올릴 수 없다

`payload['provider']`는 큐에 넣은 쪽이 쓴 값이다. **큐에 JSON 한 줄 넣는 것만으로 돈이 나가면
안 된다.**

```json
"providers": { "allowed": ["placeholder", "fixture"], "default": "placeholder" }
```

목록 밖의 provider를 요구하는 작업은 거부되고 사유와 함께 `failed`가 된다. 실제 모델을
돌리려면 운영자가 그 기계의 config에 명시적으로 추가한다. 거부는 **재시도하지 않는다** —
다시 해도 다시 거부된다.

API 키는 payload에 넣지 않는다. `job.payload`는 저장되고 `/api/jobs`로 그대로 나간다.
`api_key`·`secret`·`token`·`password` 같은 이름이 보이면 핸들러가 보기 전에 거부한다.
(이것은 부주의에 대한 방어지 보안 경계가 아니다. 키는 환경변수에서 provider 클래스가 읽는다.)

## 5. 작업 종류

| kind | 하는 일 | 돈을 쓰나 | lease |
|---|---|---|---|
| `db_sync` | 파일 아티팩트를 DB로 적재 | | 15분 |
| `screen_build` | 결정론적 지표 창고 | | 30분 |
| `monitor_status` | 감시 항목 평가 + 불변 스냅샷 | | 10분 |
| `monitor_ingest` | 링크된 항목을 창고에서 적재 | | 10분 |
| `harness_triage` | Stage 3 (EV·AS·DI·FS) | ✅ | 1시간 |
| `harness_full` | Stage 4 (plan이 부르는 대로) | ✅ | 3시간 |
| `deep_dive` | 정성 딥다이브 4단계 | ✅ | 1시간 |

`spends_money: true`인 종류도 기본 provider는 `placeholder`/`fixture`다. 표시는 운영자가
allowed를 열 때 무엇이 걸려 있는지 보라는 뜻이다.

kind는 **enqueue 시점에** config와 대조한다. 오타는 큐에 넣는 사람이 바로 보아야지 한 시간 뒤
워커가 발견할 일이 아니다.

## 6. 실행

```bash
python harness.py db upgrade          # 0003까지

# 큐에 넣는다 (넣는 것과 도는 것은 다른 일이다)
python harness.py worker enqueue screen_build --set as_of_date=2026-09-18
python harness.py worker enqueue harness_triage --set top=5 --set as_of_date=2026-09-18
python harness.py worker enqueue deep_dive --set run_id=MSFT --set provider=fixture
python harness.py worker enqueue db_sync --payload '{"kinds":["runs","monitoring"]}'

# 워커. 기본은 큐를 비우고 종료한다
python harness.py worker run
python harness.py worker run --kinds screen_build,db_sync --follow   # 데몬
python harness.py worker run --max-jobs 10 --max-seconds 600

# 읽기·손보기
python harness.py worker status
python harness.py worker jobs --status failed
python harness.py worker jobs 42
python harness.py worker retry 42      # 실패한 작업을 다시 큐에
python harness.py worker cancel 43
python harness.py worker reap          # lease 만료된 작업 회수
```

`--follow`가 데몬이고 기본이 드레인인 이유: 기본값이 프로세스를 영원히 붙잡는 것은 놀라운
일이어야 한다. SIGTERM·SIGINT는 **진행 중인 작업을 끝내고** 빠져나온다. 중간에 죽여도
lease가 만료되어 회수되지만, 끝내는 편이 낫다.

API:

```
GET  /api/jobs[?status=&kind=&limit=]   최근 작업 + 큐 요약
GET  /api/jobs/{job_id}
POST /api/jobs                          {kind, payload, idempotency_key?, priority?}
```

DB가 설정되지 않았으면 501로 **그렇게 말한다.** 빈 목록을 돌려주면 한가한 큐처럼 읽힌다.

## 7. 자원 잠금 — 두 작업이 같은 run을 쓰지 않는다

큐는 **같은 행**을 두 워커가 가져가는 것만 막는다. **서로 다른 두 행**이 같은 `runs/<ID>/`를
건드리는 것은 막지 못하고, 실제로 그런 조합이 있다:

```
harness_full {run_ids:[MSFT]}   runs/MSFT/reports/*.json, aggregate.json 을 다시 쓴다
deep_dive    {run_id: MSFT}     그 aggregate.json 을 읽어 harness_snapshot 으로 복사한다
```

`harness_core.dump_json`은 `write_text` 한 줄이다 — **원자적이지 않다.** 읽는 쪽이 파일의
절반을 볼 수 있고, 그렇게 읽힌 값이 불변 기록에 사실로 들어간다.

그래서 작업은 claim 전에 자기가 건드릴 자원을 선언한다.

| kind | 잡는 것 | 이유 |
|---|---|---|
| `harness_triage` · `harness_full` | `run:<ID>` (또는 `run:*`) | `runs/<ID>/`를 쓴다 |
| `deep_dive` | `run:<ID>` | `runs/<ID>/`를 읽어 스냅샷을 복사한다 |
| `monitor_status` · `monitor_ingest` | `run:<T>` (또는 `run:*`) | 워치리스트를 만들며 `runs/<T>/reports`를 읽는다 |
| `db_sync` | `run:*` | 모든 run의 `aggregate.json`을 읽는다 |
| `screen_build` | `warehouse:<as_of>` | Stage 0 pack만 읽는다 — **어떤 작업도 그것을 다시 쓰지 않으므로** run 정체에 끼지 않는다 |

**보장은 이 코드의 확인이 아니라 UNIQUE 제약이다.** `(namespace, resource)`가 unique이고,
두 워커가 동시에 비어 있다고 판단해도 `INSERT` 하나만 살아남는다. 진 쪽은 다음 후보로 넘어간다.

막힌 작업은 **실패하지도 지연되지도 않는다. 그냥 건너뛴다.** claim은 후보를 앞에서부터 보며
자원이 비어 있는 첫 작업을 가져간다 — 맨 앞의 막힌 작업에서 멈추면 할 수 있는 일이 뒤에 쌓인 채
워커가 논다.

```
queued:  [1] harness_full MSFT   [2] deep_dive MSFT   [3] deep_dive NVDA
worker-a -> 1 (run:MSFT 획득)
worker-b -> 3 (2는 막혔으므로 건너뛴다)
```

`resource = '*'`는 namespace 전체다. `top: N`처럼 **대상이 실행 전에 정해지지 않는 배치**가
쓴다. 너무 많이 잡으면 한 작업이 기다릴 뿐이고, 너무 적게 잡으면 run이 깨진다 — 안전한 방향은
분명하다.

잠금은 `completed`·`failed`·`cancelled`에서 풀리고, **lease가 회수될 때도 반드시 풀린다.**
죽은 워커가 기업 하나를 영원히 붙잡고 있으면 안 된다. 보유자가 없는 잠금(`running`이 아닌
작업의 행)은 매 pass의 reaper가 정리한다.

`(run, *)`와 `(run, MSFT)`는 서로 다른 행이라 UNIQUE 제약이 둘의 충돌을 판단하지 못한다.
그 경쟁만 PostgreSQL의 `pg_advisory_xact_lock`으로 닫는다 — claim 트랜잭션 동안만 잡히고
commit/rollback에서 자동으로 풀리므로 정리할 것이 없다. SQLite는 쓰기가 하나뿐이라 필요 없다.

읽기/쓰기 모드는 두지 않았다. 같은 자원을 읽기만 하는 두 작업을 직렬화하는 비용은 작고(둘 다
idempotent라 하나가 기다리면 된다), 모드 행렬은 틀리기 쉬운 곳을 하나 늘린다.

```bash
python harness.py worker locks     # 누가 무엇을 잡고 있고 무엇이 기다리는가
```

```
GET /api/jobs/locks
```

`worker status`의 `claimable_now`와 `ready_but_locked`는 다른 숫자다. **한 개의 긴 run 때문에
전부 대기 중인 큐**와 **아무도 시작하지 않은 일이 쌓인 큐**는 다른 상황이고, 합계 하나로는
구분되지 않는다.

## 8. 스케줄

되풀이되는 일의 주기를 crontab이 아니라 `config/workers.json`에 선언한다. cron은 **한 줄**만
부른다.

```cron
5 * * * *  cd /srv/harness && python harness.py worker schedule
```

무엇이 언제 도는지는 버전관리되는 파일이 안다. crontab에 파이프라인 지식이 흩어지지 않는다.

```json
{"id": "nightly_warehouse", "kind": "screen_build", "cron": "30 2 * * *",
 "payload": {"as_of_date": "{date}"}, "priority": 40}
```

기본 entries는 창고(02:30) → DB 색인(03:00) → 관측 적재(04:00) → 평가(04:30)다.
`priority`는 큐 안 순서의 힌트일 뿐 **의존성 선언이 아니다** — 창고가 실패하면 적재는 그냥
적재할 것이 없다고 보고한다. 작업 간 의존성 그래프는 두지 않았다.

### 두 번 불러도 한 번만 들어간다

이것이 핵심이다. idempotency key가 **호출 시각이 아니라 회차**를 가리킨다.

```
schedule:nightly_db_sync:2026-09-22T03:00Z
```

03:05에 부르든 03:40에 부르든 같은 회차(03:00)를 계산하므로 같은 키가 나오고, `enqueue`는
이미 있는 행을 돌려준다. cron이 두 번 발사되든, 기계가 늦게 깨든, 사람이 손으로 한 번 더
부르든 **중복이 표현 불가능하다.**

그래서 **마지막 실행 시각을 저장하지 않는다. 스케줄러의 상태는 job 테이블 자신이다.**
(테스트: 큐의 행을 지우면 다시 만기가 된다)

### 상시 프로세스를 두지 않았다

`worker schedule`은 만기인 것을 계산해 넣고 끝난다. 데몬이 하나 늘면 **그것이 살아 있는지를
다시 감시해야 한다.**

### UTC 고정

지역시간을 쓰지 않는다. DST 전환일에 같은 시각이 **두 번 오거나 아예 없고**, 그것은 멱등성을
정확히 깨뜨리는 경우다.

### 밀린 것을 밀어 넣지 않는다

스케줄러가 사흘 쉬었다고 사흘치가 들어가지 않는다. `db_sync`에 필요한 것은 최신 상태 하나지
백로그 세 개가 아니다. `lookback_hours`(기본 48) 안의 **가장 최근 회차 하나**만 넣고, 그보다
오래된 것은 `not_due`로 사유와 함께 보고한다.

### cron 리더

라이브러리를 넣지 않고 작게 직접 썼다. **순수 matcher + 분 단위 역방향 스캔**이다. "다음 발사
시각"을 닫힌 형태로 계산하는 것이 cron 구현이 틀리는 지점이고, "이 분이 맞나?"를 2,880번
묻는 것은 지루하고 정확하다.

지원: `*` `n` `a-b` `a,b` `*/n` `a-b/n`, 그리고 `@hourly` `@daily` `@weekly` `@monthly`.
`L` `W` `#` `?` 같은 문법은 **해석하지 않고 거부한다** — 잘못 읽어서 조용히 매일 도는 것보다
설정이 틀렸다고 말하는 편이 낫다.

**day-of-month와 day-of-week가 둘 다 `*`가 아니면 OR로 친다.** cron의 유명한 함정이고,
`0 0 1 * 1`은 1일 **그리고** 매주 월요일에 돈다. 운영자가 cron이 cron처럼 굴기를 기대하므로
남겼고, 의도된 것임을 테스트로 고정했다.

### 돈 쓰는 종류는 기본 schedule에 없다

`harness_triage`·`harness_full`·`deep_dive`는 `never_scheduled`에 사유와 함께 적혀 있다.
넣을 수는 있지만 **운영자가 이 파일에 명시적으로 적는 결정**이어야 한다. (테스트가
`spends_money`인 종류가 기본 entries에 없음을 고정한다)

```bash
python harness.py worker schedules                     # 선언된 것과 문법 검사 결과
python harness.py worker schedule --dry-run            # 지금 무엇이 만기인가
python harness.py worker schedule                      # 넣는다
python harness.py worker schedule --only nightly_db_sync
python harness.py worker schedule --now 2026-09-22T04:45:00Z --dry-run
```

```
GET  /api/jobs/schedules[?now=]    선언 + 현재 만기 (읽기 전용 — 넣지 않는다)
POST /api/jobs/schedules/run       만기인 것을 넣는다
```

## 9. 병렬성

워커 프로세스 하나가 한 번에 작업 하나를 처리한다. 병렬이 필요하면 **프로세스를 늘린다** —
`SKIP LOCKED`가 같은 행을 두 번 주지 않고, 자원 잠금이 같은 기업을 두 번 주지 않는다. 한
프로세스 안의 스레드 풀은 그 보장을 스스로 다시 구현해야 하므로 두지 않았다.

## 10. 남은 것

- **잠금 단위가 run이지 파일이 아니다.** 같은 기업에 대한 작업은 서로 다른 파일을 건드려도
  직렬화된다. 더 잘게 쪼갤 수는 있지만 경계를 틀리면 조용히 깨지므로, 지금은 거친 쪽을 택했다
- **읽기 잠금이 없다.** `deep_dive`와 `monitor_status`는 run을 읽기만 하는데도 서로를 막는다.
  비용은 대기시간뿐이다
- **`screen_build`가 창고 파일을 잡지 run pack을 잡지 않는다.** Stage 0 pack을 다시 쓰는 작업이
  생기면 이 가정이 깨지고, 그때는 `by_kind` 규칙을 고쳐야 한다
- **heartbeat를 핸들러가 부르지 않는다.** 함수는 있지만 긴 작업이 중간에 lease를 갱신하지
  않는다. `harness_full`의 lease를 3시간으로 잡아 둔 것이 현재의 대응이다
- **작업 간 의존성 그래프가 없다.** 스케줄은 시각으로 순서를 암시할 뿐, 창고가 실패했을 때
  적재를 미루지 않는다. 적재는 적재할 것이 없다고 보고하고 끝난다
- **catch-up 모드가 구현되어 있지 않다.** `catch_up: false`만 동작하며, true로 두어도
  가장 최근 회차 하나만 들어간다. `occurrences_since`는 있으니 붙일 수는 있다
- **스케줄 자체의 실행 이력이 없다.** 어떤 회차가 큐에 들어갔는지는 `job.idempotency_key`로
  알 수 있지만, 스케줄러가 언제 돌았는지는 남지 않는다
- **완료된 작업을 지우지 않는다.** 무엇이 언제 돌았는지가 감사 기록이다. 정리는 명시적으로 한다
- 워커가 돌린 결과를 `sync_log`에 넣지 않는다. `job.result`에만 남는다
