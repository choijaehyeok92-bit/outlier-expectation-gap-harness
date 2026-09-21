# Dilution policy — regression against stored runs

`python harness.py policy --out docs/POLICY.md`이 만드는 문서가 아니다. 희석 정책 변경이 기존 run에 무엇을
의미하는지 read-only로 재계산한 기록이다. **`runs/` 아래 어떤 파일도 수정하지 않았다.**

## 집계 결과는 바뀌지 않는다

저장된 25개 run을 변경 전후 코드로 각각 `compute_aggregate`한 결과, `hard_veto_status`·`mechanical_pre_ic_state`·
`archetype`·`position_range_pre_ic`·`score_100`이 **모두 동일하다.** 어떤 기존 run도 `dilution_metrics`를 선언하지
않으므로 `dilution_watch`는 전부 `null`이고 포지션도 움직이지 않는다.

## 전체 corpus에서 희석 판정의 분포

25개 run에 담긴 희석 veto 판정 48건: `cleared` 42건 · `conditional` 3건 · `candidate` 3건.

`cleared`가 압도적이고, 새 규율에 걸리는 것은 `conditional` 3건 전부다. 즉 이 변경이 바꾸는 것은 corpus의
극히 일부이며, 그 일부가 정확히 문제로 지목된 패턴이다. `candidate` 3건은 규율 대상이 아니다(평가 미실시).

## 저장된 희석 판정에 새 규율을 적용하면

`veto_element_assessment` 규율은 **재검증(`harness.py validate`) 시점에만** 작동한다. 저장된 보고서와
`final_verdict.json`은 그대로 읽힌다.

| run | archetype | 저장된 veto | 저장된 state | FS dilution 점수 | 담당 판정 | 새 규율 |
|---|---|---|---|---:|---|---|
| IOT | outlier_growth | CLEARED | NORMAL_CANDIDATE | 30 | FS `cleared`<br>RF `cleared` | 통과<br>통과 |
| RBRK | outlier_growth | CLEARED | STARTER_OR_WATCH | 30 | FS `cleared`<br>RF `cleared` | 통과<br>통과 |
| PL | moonshot | CLEARED | None | 80 | FS `cleared`<br>RF `cleared`<br>RT `cleared` | 통과<br>통과<br>통과 |
| RKLB | non_fit | UNRESOLVED | EARLY_EXIT_NON_FIT | 30 | FS `candidate`<br>RF `candidate` | 통과<br>통과 |
| TMDX | non_fit | UNRESOLVED | EARLY_EXIT_NON_FIT | 70 | FS `conditional`<br>RF `conditional` | **재검증 거부**<br>**재검증 거부** |
| CRWD | non_fit | UNRESOLVED | EARLY_EXIT_NON_FIT | 55 | FS `conditional`<br>RF `candidate` | **재검증 거부**<br>통과 |

## 사례별 판단

**IOT · RBRK · PL — 변화 없음, 그리고 그것이 옳다.**
세 run 모두 이미 `cleared`이고, 근거도 정확히 새 정의가 요구하는 형태다. IOT는 "희석 +3.28%는 감점 사유지만
ARR·매출 30% 성장 대비 주당 성장은 여전히 높다", RBRK는 "material but the evidence does not yet establish
a long-duration pattern", PL은 "has not yet met the strict long-duration excessive-dilution predicate".
높은 희석은 FS 점수에서 이미 크게 감점되어 있다(IOT·RBRK 30점). **장기성이 불명확하다는 이유만으로 Hard Veto가
되지 않는다**는 일관성은 이미 성립하고 있었고, 이번 변경은 그 판단을 개별 에이전트의 재량이 아니라 config의
명시적 구성요건으로 고정한다.

**TMDX · CRWD — 여기가 실제 결함이었다.**
세 건의 `conditional`이 모두 "정보 부족·장래 가능성"을 사유로 한다.

> TMDX FS: *"Current common-share growth appears manageable, but the convertible notes and ongoing SBC create a meaningful future dilution path that is not yet fully resolved."*
> TMDX RF: *"SBC is recurring and convertibles can dilute shares; current dilution is manageable but long-duration per-share impact remains unresolved."*
> CRWD FS: *"Current share-count growth is moderate, but SBC is economically large and requires continued per-share monitoring."*

세 건 모두 현재 희석은 "manageable/moderate"라고 스스로 말하면서 `conditional`을 썼다. 이는 "거의 confirmed"가
아니라 "아직 모른다"이며, 게이트에서 `UNRESOLVED`가 되어 automatic buy를 막는다. 새 규율에서는 셋 다
`elements_met` 없이는 `conditional`을 쓸 수 없어 **재검증 시 거부**된다. 올바른 기록은 `cleared` + FS 점수 감점 +
`dilution_metrics`(SBC·전환증권 관측값) + `key_kpis` 모니터링이다.

**RKLB — 이번 변경으로 풀리지 않는다.**
FS는 실제 증거(주식수 +10%, ATM 29.3M주)를 들고 `candidate`를, RF는 미작성 템플릿 그대로 `candidate`를 남겼다.
`candidate`는 "평가하지 않음"이므로 규율 대상이 아니고, RKLB의 `UNRESOLVED`는 **RF가 실행되지 않은 것**이 원인이다.
게이트를 완화해 풀 문제가 아니라 RF를 실행해 풀 문제다. 대규모 ATM/M&A 자금조달이 one-off인지 structural인지는
새 정의의 네 번째 구성요건(`구조적 반복 원인`)과 `structural_financing_need` 플래그가 구분하도록 했으나, 그 판정을
내릴 보고서 자체가 아직 없다.

## 재현

```bash
python -m unittest discover -s tests -p 'test_dilution.py' -v
```

위 표는 저장된 보고서를 읽어 `harness_core.runtime.veto_element_errors`를 적용한 결과다.

