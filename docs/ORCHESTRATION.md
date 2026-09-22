# Stage 3 orchestration (Phase 7)

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
| freeze·Stage 0 게이트를 우회하지 않음 | |
| `plan.execution_control` 존중 | |

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
triage_runs/<id>/triage_run.json         배치 기록 (immutable, verification_scope 포함)
```

오케스트레이션 메타데이터를 보고서 **안**이 아니라 **옆**에 둔 이유: 에이전트 보고서는 사람
분석가가 쓴 것과 정확히 같은 모양으로 남아야 한다. 어떻게 만들어졌는지는 그 옆에 둔다.

`runs/<T>/orchestration/`은 freeze 해시 대상(`company_context.json` + `sources/**`)이 아니므로
frozen run을 무효화하지 않는다.

---

## 남은 것

- **분석 품질은 이 계층의 어떤 테스트로도 확인되지 않는다.** 실제 provider와 실제 자료로만
  확인할 수 있고, 그 확인은 사람의 일이다
- `concurrency: 1` — 순차 실행이다. 같은 run에 동시에 쓰면 `aggregate`가 중간 상태를 읽는다
- `job` 테이블(Phase 2)을 아직 소비하지 않는다. 배치는 인프로세스로 돌고 재시작을 견디지 않는다
- Full Harness 오케스트레이션(Phase 8)은 아직 501이다. SL·CP·MT·RF·MA·LG·Macro·ED·RT·IC는
  triage보다 단계 의존성이 복잡하다 (`plan`이 이미 그 순서를 알고 있으므로 그것을 따르면 된다)
- Stage 0이 없는 후보를 자동으로 준비시키지 않는다. `init`·`fetch`·전처리·`freeze`는 여전히
  사람이 거치는 경로이며, 그것을 자동화하려면 공시 전처리를 자동화해야 한다
