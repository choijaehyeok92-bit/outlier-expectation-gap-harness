# Orchestration — Stage 3 triage (Phase 7) and Stage 4 full harness (Phase 8)

전체 유니버스에 Full Harness를 돌릴 수 없으니 그 앞에 triage를 둔다. 이 계층이 하는 일은
**순서 정하기**다. 어떤 기업을 다음에 볼지, 어떤 에이전트를 돌릴지, 실패한 단계를 다시 시도할지.
기업에 대한 판단은 하나도 하지 않는다 — 점수·archetype·Hard Veto·밸류에이션·포지션은 전부
하네스가 자기가 검증한 보고서로부터 계산한다.

---

## 먼저: 이 테스트가 검증하는 것과 하지 않는 것

Phase 1~4는 전부 결정론적이라 픽스처로 "옳음"을 검증할 수 있었다. **Phase 7부터는 아니다.**

| 픽스처가 검증하는 것 | 픽스처가 검증하지 **않는** 것 |
|---|---|
| 에이전트 실행 순서와 단계 전이 | 분석 품질 |
| 실패 시 재시도와 재시도 상한 | 점수의 타당성 |
| idempotency — 다시 돌려도 아무것도 새로 만들지 않음 | 증거의 진위 |
| 검증 실패 보고서가 저장소에 남지 않음 | Hard Veto 판정의 옳음 |
| freeze·Stage 0 게이트를 우회하지 않음 | IC 판정의 타당성 |
| `plan.execution_control` 존중 | Red Team이 실제로 반증을 찾았는지 |
| `plan.agents`를 따라가는 단계 루프와 종료 조건 | |
| 진전 없는 반복(stall) 감지와 단계 반복 상한 | |
| 하네스 프롬프트를 바꾸지 않고 첨부만 덧붙이는 것 | |

이 경계는 `config/triage.json`의 `verification_scope`에 선언되어 있고 **모든 배치 기록에
찍힌다.** 결과를 읽는 사람이 자기가 무엇을 들고 있는지 추측할 필요가 없게 하기 위해서다.

### 픽스처를 분석처럼 보이게 만들지 않았다

선택지가 둘 있었다. 리서치처럼 읽히는 그럴듯한 문장을 넣거나, 명백히 리서치가 아니면서도
모든 계약을 만족시키는 것을 넣거나. 후자를 택했다.

`PlaceholderAgentProvider`가 만드는 보고서는:
- thesis가 **"[PLACEHOLDER — 분석 아님] 이 보고서는 오케스트레이션 배선을 검증하기 위한
  자리표시자다"**로 시작한다
- 모든 evidence가 자리표시자 자신을 출처로 인용한다
- 모든 criterion의 uncertainty severity가 `critical`이다 (아무것도 평가하지 않았으므로 사실이다)
- **자기가 소유한 Hard Veto를 전부 `candidate`로 남긴다**

마지막 항목이 가장 중요하다. 자리표시자가 veto를 clear할 수 있으면, 아무도 들여다보지 않은
run을 초록색으로 보여주는 테스트 스위트가 만들어진다. 하네스의 게이트가 `candidate`를
UNRESOLVED로 읽으므로 자리표시자 실행은 **절대 매수 상태에 도달할 수 없고**, 테스트가 이를
고정한다.

실제로 돌려보면 이렇게 나온다:

```
status: completed | execution_control: stop_early | stage: early_exit
hard_veto_status: UNRESOLVED | mechanical_pre_ic_state: EARLY_EXIT_NON_FIT
```

하네스가 "도달 가능한 투자유형 없음"으로 종료했다. 오케스트레이터가 그걸 뒤집지 않는다.

---

## 한 기업, 한 단계

```
readiness → [EV, AS, DI, FS] → aggregate → plan → execution_control
```

각 에이전트 단계는 네 가지 성질을 지킨다.

**하네스가 받아들이기 전에는 아무것도 쓰지 않는다.** 후보 보고서는 임시 파일에 있다가 두 겹의
검증(JSON Schema → `validate_report` + `veto_element_errors`)을 모두 통과한 뒤에야 원자적으로
제자리로 옮겨진다. 거부된 문서가 `reports/`에 나타나면 `load_reports`가 집어가고 `aggregate`가
점수를 매긴다.

**정체성은 모델이 고르는 것이 아니다.** `agent_id`·`ticker`·`as_of_date`·`domain`·`role`은
manifest와 run에서 가져와 응답에 덮어쓴 뒤 검증한다. EV 프롬프트에 답하면서 자기를 FS라고
부르는 모델이 없으면 모든 검사를 통과해버린다. (테스트 있음)

**재시도는 형식을 고치지 내용을 고치지 않는다.** 재시도 프롬프트에는 **검증기가 낸 오류 문자열만**
붙는다. "score_0_100이 루브릭 가중평균과 다르다"는 문서의 결함이다. "점수가 너무 낮다"는 분석을
조종하는 것이고, 이 오케스트레이터는 그 말을 하지 않는다. 테스트가 재시도 프롬프트에 조종 문구가
없음을 검사한다.

**이미 끝난 단계는 다시 하지 않는다.** idempotency 키에 run의 frozen input snapshot이 들어간다.
re-freeze하면 이전 에이전트 작업이 올바르게 무효화되고, 바뀌지 않은 run은 그냥 건너뛴다.

### `execution_control`은 해석하지 않고 따른다

```
continue        다음 단계가 남았다. Stage 3은 제 몫을 했다
stop_early      도달 가능한 투자유형이 없다 — 진짜 결론이다
stop_complete   워크플로가 끝났다
blocked         입력이나 검증이 막혔다 — 완료가 아니며 그렇게 기록한다
```

**조기 종료는 결과이고 블록은 고쳐야 할 결함이다.** 둘을 뭉개면 배치가 "스크린 아웃됨"이라고
보고하는데 실제로는 아무도 그 회사의 공시를 읽을 수 없었던 상황이 된다.

---

## 배치

세 개의 가드가 있다.

**Idempotency는 단계의 몫**이다. 끝난 배치를 다시 돌리면 provider를 한 번도 호출하지 않는다.
(테스트: `provider.calls == []`)

**반복 실패는 배치를 멈춘다.** 연속으로 여러 기업이 실패하면 원인은 거의 그 기업들이 아니라
provider·자격증명·정책이다. 나머지를 갈아넣으면 문제 하나가 똑같은 문제 백 개가 된다.
임계값은 config이고 멈춤은 실패 묶음이 아니라 멈춤으로 기록된다.

**블록은 회로차단기를 건드리지 않는다.** 막힌 기업은 입력 문제이고 provider에 대해 아무것도
말해주지 않으므로 나머지 작업을 중단시키면 안 된다.

---

## 후보 선정

스크린 결과에서 온다. 정책은 `config/triage.json`의 `selection`이고 **티커는 나오지 않는다.**

작업할 수 없는 후보는 버리지 않고 사유와 함께 돌려준다:

```
000660     triage is already complete and valid
GHOST      no harness run; `harness.py init` and complete Stage 0 first
UNFROZEN   inputs are not frozen
NOPACK     Stage 0 incomplete — latest_annual (0/1); trailing_quarters (0/6)
```

"왜 이건 triage 안 됐지"의 답이 스크린 재실행 없이 나온다.

---

## 실행

```bash
# 무엇이 돌 것인지만 본다
python harness.py screen triage --as-of 2026-09-18 --top 20 --dry-run

# 오프라인 자리표시자로 배선을 확인한다 (분석하지 않는다)
python harness.py screen triage --as-of 2026-09-18 --top 20

# 저장된 스크린에서
python harness.py screen triage --screen-run 2026-09-18-abc123def456 --top 30

# 실제 모델. 돈을 쓰고, 사람이 리서치로 읽을 보고서를 만든다
export ANTHROPIC_API_KEY=...
python harness.py screen triage --as-of 2026-09-18 --top 10 --provider anthropic

python harness.py screen triage-runs
```

`--placeholder-mode {valid,invalid,flaky,error}`로 자리표시자가 무엇을 시뮬레이션할지 정한다.

API:

```
POST /api/harness/triage          기본값은 dry_run=true, provider=placeholder
GET  /api/harness/triage/runs
GET  /api/harness/triage/{id}
```

기본값이 dry run이고 자리표시자인 이유는, 돈을 쓰는 것과 사람이 리서치로 읽을 문서를 만드는 것
둘 다 **요청해서 일어나야지 실수로 일어나면 안 되기** 때문이다.

---

## 아티팩트

```
runs/<RUN_ID>/reports/<AID>.json         에이전트 보고서 — 사람이 쓴 것과 같은 모양
runs/<RUN_ID>/orchestration/<AID>.json   누가 언제 어떤 provider로 몇 번 시도해 만들었는지
triage_runs/<id>/triage_run.json         Stage 3 배치 기록 (immutable, verification_scope 포함)
full_harness_runs/<id>/full_run.json     Stage 4 배치 기록 (같은 규칙, 별도 디렉터리)
```

오케스트레이션 메타데이터를 보고서 **안**이 아니라 **옆**에 둔 이유: 에이전트 보고서는 사람
분석가가 쓴 것과 정확히 같은 모양으로 남아야 한다. 어떻게 만들어졌는지는 그 옆에 둔다.

`runs/<T>/orchestration/`은 freeze 해시 대상(`company_context.json` + `sources/**`)이 아니므로
frozen run을 무효화하지 않는다.

---

# Stage 4 — Full Harness (Phase 8)

Stage 3은 고정된 네 에이전트를 돌린다. **Stage 4는 목록을 갖고 있지 않다.** 매 회차
`harness.py plan`에게 다음이 무엇인지 묻고 그 답이 부르는 에이전트를 정확히 그만큼 실행한다.
단계 순서는 `packages/orchestration`이 아니라 `harness_core/planner.py`에 있다.

```
triage → (fundamental_reanalysis) → domain_analysis → macro
       → evidence_and_red_team → ic → complete
```

`packages/orchestration/full.py` 어디에도 SL·CP·MT·RF·MA·LG·MO·ED·RT·IC가 적혀 있지 않다.
manifest에 도메인을 추가하면 여기 한 줄 바뀌지 않고도 그 에이전트가 돌아간다. 테스트가 이를
고정한다 — 같은 실행에서 **LG와 TQ는 돌지 않는다.** LG는 이 기업이 도달할 수 없는 유형의
조건에만 걸려 있고 TQ는 `diagnostics.turnaround_candidate`가 켜져야 활성화되기 때문이다.
manifest를 순회하는 루프였다면 둘 다 돌았을 것이다.

## 루프가 하지 않는 세 가지

**멈출 때를 스스로 정하지 않는다.** `plan.execution_control`이 정한다.

| control | 뜻 | 기록되는 status |
|---|---|---|
| `stop_complete` | 워크플로가 끝났다 | `completed` |
| `stop_early` | 도달 가능한 유형이 없어 IC를 의도적으로 돌리지 않았다 | `screened_out` |
| `blocked` | 입력·검증이 막혔다 | `blocked` |

`screened_out`은 **결론이지 실패가 아니다.** 요약에서 `completed`와 따로 센다.

**갈아넣지 않는다.** 한 회차가 끝났는데 planner가 같은 `(stage, agents)`를 다시 부르면, 그
회차가 만든 것이 planner를 만족시키지 못한 것이다. 더 돌려도 같은 결과이므로 `stalled`로
멈추고 **어느 단계의 어떤 에이전트가 막았는지** 남긴다.

```
stalled: stage 'fundamental_reanalysis' asked for ['CP', 'FS'] a second time with nothing
changed. Those reports did not satisfy the planner, and running them again would produce
the same result. Look at what that stage still wants.
```

별도로 `max_stage_iterations`(기본 12) 상한이 있다. 워크플로의 단계 수보다 크므로 정상
실행에서는 닿지 않는다. 닿으면 완료가 아니라 `stalled`다.

**남의 분석을 대신 끝내주지 않는다.** 종료 단계에서 하네스 자신의 `digest`와 `report`를 불러
`aggregate.json`·`final_verdict.json`·`digest.md`·`easy_report.md`를 만든다. 다음 둘은
**절대 만들지 않는다**:

- `cache-macro` — `runs/_macro`는 이후 모든 `init`이 재사용하는 전역 캐시다. 자동 실행하면
  한 run의 macro 판단이 다른 기업으로 조용히 퍼진다. 사람이 명시적으로 부를 때만 캐시된다
- `one_page_investment_record.md` — IC 프롬프트가 지정하는 사람 손 산출물이다. JSON만 돌려주는
  provider는 쓸 수 없고 오케스트레이터가 대신 지어내지 않는다

`stalled`·`blocked`로 끝난 run에는 `easy_report.md`를 쓰지 않는다. 끝나지 않은 분석에 읽을
판정문을 붙이지 않기 위해서다.

## 재분석 단계만 강제로 다시 돌린다

planner가 구조적 지정학 이벤트 때문에 특정 도메인의 재분석을 요구하면(`fundamental_reanalysis`)
그 보고서들은 **이미 존재한다.** idempotency가 건너뛰면 영원히 진전이 없다. 그래서 이 단계만
`force_rerun_stages`에 들어 있고 강제로 다시 실행한다. 재실행된 에이전트가 그래도
`geo_events_reviewed`에 이벤트를 기록하지 않으면 위의 stall 감지가 한 회차 뒤에 멈춘다.

## 하네스 프롬프트는 한 글자도 바꾸지 않는다

`harness.py prompt ED`는 "`runs/T/digest.md`를 읽으라"로 끝난다. 사람은 파일을 연다.
HTTP 너머의 provider는 열 수 없다 — 문자열을 받아 문자열을 돌려줄 뿐이다. 그 상태로 보내면
ED·RT·IC는 **아무것도 없는 상태로 감리하고 공격하고 판정하며, 조용히 그렇게 한다.**

그래서 지정된 파일을 뒤에 붙인다. 세 가지 규칙이 이것을 "두 번째 프롬프트"가 되지 않게 한다.

1. **하네스 본문은 건드리지 않는다.** 첨부는 그 뒤의 별도 블록이고 자체 제목을 단다.
   provenance에 `harness_prompt_sha256`과 실제 전송분의 `prompt_sha256`을 **둘 다** 남겨
   언제든 비교할 수 있다
2. **내용은 데이터이지 지시가 아니다.** `digest.md`는 다른 에이전트 보고서에서 만들어지며
   그것은 모델 출력이다. 그 안의 한 문장이 명령 모양일 수 있으므로, 원문 공시에 쓰는 것과
   같은 구분자·무력화 블록(`packages/research/untrusted.py`)으로 감싼다
3. **자르지 않는다.** 상한을 넘으면 절반이 도착하는 대신 그 단계가 `blocked`가 된다.
   digest의 4분의 3으로 내린 IC 판정은 전부로 내린 것과 겉보기에 똑같다

| 에이전트 | 첨부 |
|---|---|
| EV·AS·DI·FS·SL·CP·MT·RF·MA·LG·TQ·MO | 없음 (프롬프트가 파일을 지정하지 않는다) |
| ED·RT | `digest.md` |
| IC | `digest.md`, `aggregate.json` |

`evidence_and_red_team`·`ic` 단계 직전에 하네스의 `digest`를 다시 만들어 최신 보고서를
반영한다.

## 자리표시자의 천장 — MO와 IC

Stage 3에서 자리표시자가 매수에 닿을 수 없었던 이유는 소유한 veto를 전부 `candidate`로
남기기 때문이었다. Stage 4는 그 천장을 혼자 무너뜨릴 수 있는 두 에이전트를 돌린다.

- **IC는 상태를 요청하지 않는다.** `ic_state`는 보고서가 매수를 요청할 수 있는 스키마상
  유일한 필드다. 자리표시자는 그 필드를 **비운다.** `reconcile_ic`는 기계적 상태를 그대로
  돌려준다
- **MO는 모든 구성요소를 unknown으로 선언한다.** 형식은 유효해야 한다(아니면 planner가 MO를
  영원히 다시 부른다). 그러나 모든 지정학 severity는 `unknown`이고 모든 risk budget
  multiplier는 정책 자신의 `missing_component_multiplier`다. 둘 다 pacing을 **조이지
  풀지 않는다**

테스트가 둘 다 고정한다. 자리표시자로 `stop_complete`까지 완주해도 결과는 이렇다:

```
ic_state: WATCH | position_range: 0% until veto cleared
hard_veto_status: UNRESOLVED | macro_pacing_multiplier: 0.5
```

## 실행

```bash
# 무엇이 돌 것인지만 본다
python harness.py screen full --as-of 2026-09-18 --top 5 --dry-run

# 한 기업 (스크린 선정을 건너뛴다)
python harness.py screen full --run-id MSFT

# 오프라인 자리표시자로 배선을 확인한다 (분석하지 않는다)
python harness.py screen full --screen-run 2026-09-18-abc123def456 --top 5

# 실제 모델. 기업당 에이전트 호출이 13회 이상이다
export ANTHROPIC_API_KEY=...
python harness.py screen full --as-of 2026-09-18 --top 3 --provider anthropic

python harness.py screen full-runs
```

API:

```
POST /api/harness/full            기본값은 dry_run=true, provider=placeholder
                                  run_ids: [...] 로 지정 실행, 아니면 스크린 상위 N
GET  /api/harness/full/runs
GET  /api/harness/full/{id}
```

## 후보 선정이 triage와 다른 점

| | triage | full |
|---|---|---|
| 기본 `top_n` | 30 | 10 |
| triage가 끝난 기업 | 건너뛴다 | **건너뛰지 않는다** (그게 다음 단계다) |
| planner가 조기 종료한 기업 | 건너뛴다 | 건너뛴다 |
| IC 보고서가 이미 있는 기업 | — | 건너뛴다 |

full은 "triage가 끝났는지"를 조건으로 걸지 않는다. 루프가 planner를 따르므로 필요하면
triage부터 돈다 — 그리고 통과하지 못하면 planner가 `stop_early`를 내서 4개 에이전트만 쓰고
멈춘다. 그 판단은 config가 아니라 하네스의 것이다.

---

## 남은 것

- **분석 품질은 이 계층의 어떤 테스트로도 확인되지 않는다.** 실제 provider와 실제 자료로만
  확인할 수 있고, 그 확인은 사람의 일이다
- `concurrency: 1` — 순차 실행이다. 같은 run에 동시에 쓰면 `aggregate`가 중간 상태를 읽는다
- `job` 테이블(Phase 2)을 아직 소비하지 않는다. 배치는 인프로세스로 돌고 재시작을 견디지 않는다
- **저장된 run들은 현재 stale-frozen이다.** `config_hashes()`가 `harness_core/*.py`와
  `harness.py`를 포함하므로, 그 파일들이 마지막 freeze 이후 움직인 run은 `assert_frozen_inputs`가
  거부한다. Phase 8 이전부터 그랬고 오케스트레이터는 이를 우회하지 않고 `blocked`로 보고한다.
  다시 돌리려면 사람이 검토 후 `freeze`를 다시 해야 한다
- `stalled`는 사람이 봐야 하는 상태다. 어느 단계가 왜 멈췄는지는 남기지만, 무엇을 고쳐야
  하는지는 판정하지 않는다
- Stage 4를 실제 모델로 돌린 결과는 이 저장소에 없다. 위의 표가 말하는 대로, 자리표시자로
  확인한 것은 배선뿐이다
- Stage 0이 없는 후보를 자동으로 준비시키지 않는다. `init`·`fetch`·전처리·`freeze`는 여전히
  사람이 거치는 경로이며, 그것을 자동화하려면 공시 전처리를 자동화해야 한다
