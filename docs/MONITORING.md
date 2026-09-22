# Monitoring (Phase 12)

보고서는 "무엇을 보면 내가 틀린 줄 알 수 있는가"를 이미 적어 두었다. 에이전트 보고서의
`key_kpis`와 `falsifiers`, 딥다이브의 `monitoring_kpis`와 `falsifiers`가 그것이다. Phase 12는
그 선언을 **다시 쓰지 않고 읽어서**, 관측을 기록하고, 이미 선언된 임계값과 결정론적으로
비교한다.

이 계층이 답하는 질문은 셋이고, 넷째는 답하지 않는다.

| 질문 | 모듈 |
|---|---|
| 무엇을 보고 있는가 | `watchlist` — 보고서에서 읽어 온다. 여기서 만들지 않는다 |
| 무엇이 관측되었는가 | `observations` — append-only 로그, 모든 행에 출처와 날짜 |
| 무엇이 사람을 필요로 하는가 | `evaluate` — 선언된 임계값과의 산술, 그리고 staleness |
| **무엇을 해야 하는가** | **이 계층의 질문이 아니다** |

`thesis_break`는 **매도 신호가 아니다.** 도메인 reviewer·veto owner·IC가 다시 보라는 요청이다.
이 패키지의 어떤 것도 점수·archetype·Hard Veto 상태·`ic_state`·`position_range`를 바꿀 수 없고,
평가 결과에 그런 필드가 아예 존재하지 않는다는 것을 테스트가 고정한다.

---

## 1. 산문 임계값은 해석하지 않는다

이 모듈의 초안은 틀렸고, 어떻게 틀렸는지가 설계의 핵심이다.

에이전트는 임계값을 산문으로 쓴다: `73% 이상`, `전년 대비 증가`, `>WACC`. 딥다이브도 마찬가지로
`>=20% breached for 2 consecutive periods` 같은 문장을 쓴다. 초안 파서는 **텍스트에서 아무 숫자나**
찾았고, 그 결과:

```
'quantified and rising breached for 2 consecutive periods'  ->  >= 2      ← 말이 안 된다
'>=revenue growth breached for 2 consecutive periods'       ->  >= 2      ← 말이 안 된다
```

아무도 확인하지 않은 초록불이 만들어졌다. **확인이 없는 것보다 나쁘다.**

지금은 전체 문자열이 엄격하게 일치해야 한다. 비교어를 **제거**한 나머지가 숫자와 허용된 단위
**뿐**이어야 하고, 단어가 하나라도 남으면 거부한다.

| 문구 | 결과 |
|---|---|
| `73% 이상` · `>=1.5x` · `at least 15%` · `2조 이상` | `>= 0.73` · `>= 1.5` · `>= 0.15` · `>= 2e12` |
| `-20%p 이상` | `>= -0.2` (percent_point) |
| `전년 대비 증가` · `>WACC` · `>prior year` | **거부** — 숫자가 없거나 다른 계열과의 비교다 |
| `>=20% breached for 2 consecutive periods` | **거부** — 지속성 규칙은 이 비교가 평가하지 않는다 |

거부된 항목은 감시에서 빠지지 않는다. `not_machine_checkable`로 **원문 그대로** 남고 사람이
읽는다. 스크리너가 `unresolved_conditions`를 숨기지 않는 것과 같은 규칙이다.

### 저장소 현황이 말해 주는 것

MSFT 워치리스트 95개 항목 중 기계 판정 가능한 것은 25개다. 그리고:

```
"can_raise_warning": 25,
"can_raise_thesis_break": 0
```

이 저장소의 딥다이브 `thesis_break_threshold`는 전부 `… breached for 2 consecutive periods`로
끝난다. 즉 **어떤 관측도 자동으로 가설 파기를 띄울 수 없다.** 조용한 화면이 가설이 멀쩡하다는
증거가 아니라는 뜻이고, 그래서 이 숫자를 요약에 항상 띄운다.

## 2. 모호한 관측도 비교하지 않는다

반대 방향의 같은 위험이다. 71%인 매출총이익률을 `71`이라고 기록하고 `73% 이상`(0.73)과
비교하면 `71 >= 0.73`이 참이 되어 **위반이 ok로 보고된다.** 그렇다고 100으로 나누면 부채비율
2.0 같은 정상적인 1 초과 비율이 망가진다.

그래서 추측하지 않는다. 0–1 척도 임계값에 1을 넘는 맨숫자가 오면 거부하고, 무엇을 뜻했는지
말하게 한다.

```bash
# 거부: 71이 0.71인지 71%인지 알 수 없다
harness.py monitor observe ACME --match "Gross margin" --value 71 ...
# 둘 중 하나로 말한다
harness.py monitor observe ACME --match "Gross margin" --value "71%" ...
harness.py monitor observe ACME --match "Gross margin" --value 71 --unit percent ...
```

## 3. 관측은 사실이므로 사실의 규칙을 따른다

```
필수: as_of_date · source · source_type · value 또는 triggered
거부: 출처 없음 · 기준일 이후 날짜 · 빈 관측
```

- **append-only.** 한 번 쓰면 고치지 않는다. 정정은 `supersedes`를 채운 새 관측이고 원본은
  남는다. "3월에 우리는 무엇을 믿었고 왜 그랬나"에 답할 수 있어야 한다.
- **미래 정보 없음.** 기준일 이후 날짜는 읽을 때 거르는 게 아니라 **쓸 때 거부한다.** 조용히
  사라지는 오타는 아무도 고치지 않는다.
- **분석보다 오래된 관측은 숨기지 않고 표시한다.** `pre_analysis: true`가 붙는다. 추세 맥락으로
  기록할 만하지만 새 소식으로 읽히면 안 된다.
- 로그는 `monitoring/<TICKER>/observations.jsonl`. `HARNESS_MONITORING_DIR`로 저장소 밖으로
  옮길 수 있다. **이것만 재생성이 불가능한 산출물이므로 `.gitignore`에 넣지 않았다.**
  평가 스냅샷(`monitoring_runs/`)은 관측과 보고서로부터 다시 만들 수 있으므로 ignore한다.

## 4. 상태

| 상태 | 뜻 | 재검토 요청 |
|---|---|---|
| `ok` | 선언된 모든 임계값 안 | |
| `warning` | 경고 임계값을 넘음 | |
| `thesis_break` | 가설 파기 임계값을 넘음 | ✅ |
| `triggered` | falsifier가 발동했다고 사람이 기록 | ✅ |
| `not_triggered` | 확인했고 발동하지 않음 | |
| `stale` | cadence 안에 관측 없음 | |
| `unknown` / `unchecked` | 한 번도 관측·확인되지 않음 | |
| `not_machine_checkable` | 임계값이 산문 — 사람이 읽는다 | |

두 가지는 UI에서 절대 초록색이 아니다.

- **`stale`은 괜찮다는 뜻이 아니라 아무도 보고 있지 않다는 뜻이다.** 1년째 갱신되지 않은
  숫자가 주는 all-clear는 all-clear가 아니다. 그래서 staleness는 `ok`를 덮어쓰고,
  **위반은 덮지 않는다** — 위반이 이미 더 큰 소리다.
- **`not_machine_checkable`은 비교 자체가 없었다는 뜻이다.**

`warning`은 재검토를 강제하지 않는다. 경고와 파기를 같은 무게로 올리면 둘 다 무시된다.

## 5. watch_id는 재생성을 견뎌야 한다

관측은 `watch_id`에 붙는다. 딥다이브를 다시 돌릴 때마다 id가 바뀌면 그 기업의 과거 관측이
전부 고아가 된다. 그래서 id는 `ticker + kind + source_kind + 정규화된 이름`으로 만들고:

- **agent_report는 `agent_id`를 포함한다** — 재실행해도 같다
- **deep_dive는 `deep_dive_id`를 포함하지 않는다** — 재실행마다 바뀐다
- **임계값은 어느 쪽에도 넣지 않는다** — 관측은 세상에 대한 것이지 임계값에 대한 것이 아니다

세 에이전트가 같은 이름의 KPI를 선언하면 **세 항목으로 남는다.** 같은 관측물인지 판단하는 건
이 계층의 몫이 아니다. CLI는 모호하면 거부하고 후보를 보여주며, 정말 같다면
`--all-matches`로 사람이 그렇게 말한다.

## 6. Drift — 기업이 변한 것인가 정책이 변한 것인가

점수가 62에서 71로 움직인 것은 두 가지 전혀 다른 뜻일 수 있다. 사업이 변했거나, 루브릭·정책
버전·하네스가 변했거나. 후자면 두 숫자는 애초에 같은 것을 재고 있지 않았다.

재현성 계약이 provider 비교에 대해 말하는 것과 같은 문제다. 그래서 모든 연속 쌍에 라벨이
붙는다. `strategy_version`이나 `decision_policy_version`이 다르면 차이는 보여주되
`comparable=false`, `attributable_to_company=false`다.

저장소의 NVDA가 그 예다:

```
NVDA                  2026-09-17  73.94  STARTER              policy None
NVDA-2026-09-18       2026-09-18  70.19  STARTER              policy 3.2
NVDA-V3-2026-09-19    2026-09-19  70.06  EARLY_EXIT_NON_FIT   policy 3.0
NVDA-V31-2026-09-19   2026-09-19  70.19  STARTER              policy 3.1

comparable_steps: 0
archetype: compounder -> growth -> non_fit -> growth   (전부 attributable_to_company=false)
```

archetype이 세 번 바뀌었지만 **기업에 대해서는 아무것도 말하지 않는다.** 정책 버전이 매번
달랐다.

### 시리즈를 모으는 방법

`init`은 기존 run을 덮지 않으므로 한 기업의 재실행은 반드시 새 run_id를 갖고, 그중 몇은
run_id를 ticker로 갖는다. ticker로만 묶으면 네 번 돌린 기업이 1점짜리 "시리즈"가 된다. 그래서
ticker **또는** 저장소의 `<TICKER>-…` 명명 관행으로 묶고, 각 point에 `matched_by`를 남긴다.
명시적인 `--run-ids`를 주면 추론하지 않는다.

## 7. 실행

```bash
# 무엇을 보고 있는지 (기계 판정 가능 여부 포함)
python harness.py monitor watchlist MSFT
python harness.py monitor watchlist MSFT --full        # 임계값과 파싱 결과까지

# 관측 기록 — 출처와 날짜가 필수다
python harness.py monitor observe MSFT --match "Microsoft Cloud gross margin" \
  --value "64%" --as-of 2026-09-20 --source "FY26 Q4 10-K p.40" --source-type filing \
  --period FY26Q4
# 여러 에이전트가 같은 이름을 선언했다면 거부되고 후보가 나온다. 같은 것이라면:
#   --all-matches
# falsifier는 값이 아니라 발동 여부다:
#   --match "…" --triggered true --note "NRR 88%로 공시"
# 정정은 수정이 아니라 새 관측이다:
#   --supersedes <observation_id> --note "10-K에서 재작성됨"

# 평가
python harness.py monitor status MSFT                  # 요약
python harness.py monitor status MSFT --full --save    # 전체 + 불변 스냅샷
python harness.py monitor status --tickers MSFT,NVDA   # 포트폴리오
python harness.py monitor drift NVDA
python harness.py monitor runs
```

API:

```
GET  /api/monitoring[?tickers=A,B]          포트폴리오 — 재검토 필요 순
GET  /api/monitoring/{ticker}               항목별 상태
GET  /api/monitoring/{ticker}/watchlist     관측 적용 전 선언 그대로
GET  /api/monitoring/{ticker}/drift         run 간 변화와 comparable 여부
POST /api/monitoring/observations           관측 1건 append
```

웹: `/monitoring`(포트폴리오), `/monitoring/[ticker]`(항목별 + drift). 항목은 출처가 아니라
**읽는 사람에게 무엇을 요구하는지**로 묶는다.

## 8. DB

`db upgrade`가 `0002_monitoring`으로 테이블 둘을 만든다. 수명주기가 의도적으로 다르다.

| 테이블 | 성격 | 규칙 |
|---|---|---|
| `monitoring_watch_item` | 보고서에서 파생 | upsert, `updated_at` 있음 |
| `monitoring_observation` | 사람이 본 기록 | append-only, `source` NOT NULL, `updated_at` 없음 |

`value_text`와 `(value_number, unit)`을 함께 저장한다. **NULL인 `unit`은 의미가 있다** — 기록한
사람이 척도를 말하지 않았다는 뜻이고, 이는 평가기가 추측하기를 거부하는 바로 그 경우다.
`value_number`만 읽고 `unit`을 무시하는 질의는 사실의 절반만 읽는 것이다.

`db sync --kinds monitoring`은 **관측이 기록된 기업만** 적재한다. 25개 run 전부의 워치리스트를
넣으면 아무도 보고 있지 않은 행으로 테이블이 찬다.

## 9. 남은 것

- **관측 수집은 자동화되어 있지 않다.** 사람이나 상위 시스템이 `observe`를 부른다. 공시에서
  KPI를 자동 추출하려면 KPI 이름과 공시 항목을 잇는 매핑이 필요하고, 그것은 LLM 판단이거나
  또 하나의 결정론적 매핑 계층이다 — 전자는 이 저장소의 경계를 넘고, 후자는 별도 작업이다
- **`for 2 consecutive periods` 같은 지속성 규칙을 평가하지 않는다.** 로그에 이력이 있으므로
  구현할 수 있지만, 규칙을 파싱하는 순간 다시 산문 해석이 된다. 딥다이브가 지속성을 구조화된
  필드로 쓰게 하는 편이 옳다
- **알림이 없다.** `review_required`를 계산할 뿐 아무에게도 보내지 않는다
- 모니터링 스냅샷은 DB에 색인되지 않는다. 관측과 워치아이템만 들어간다
