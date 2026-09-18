# 참조 실행 — NVDA 2026-09-18 / gpt-5.6-sol

`.github/workflows/nvda-ev-run.yml`에 base64로 박혀 있던 실행본을 디코딩해 보존한 것입니다.
`harness.py calibrate`의 프로바이더 비교 기준선으로 쓰입니다.

- provider/model: openai / gpt-5.6-sol / reasoning-effort high
- 기준일 2026-09-18, 종가 $219.34 (2026-09-17 종가와 동일)
- 당시 하네스는 TQ 에이전트 도입 전이므로 보고서는 13개입니다.
- 당시 캘리브레이션은 `config/profiles/_original/`입니다. 현재 config로 재집계하지 마십시오.

```bash
python harness.py calibrate runs/NVDA runs/_reference/NVDA-2026-09-18-sol
```

이 실행은 **점수 비교 전용**입니다. 기준일·소스 번들·config가 현재 run과 다르므로
`aggregate` 결과를 직접 비교하지 말고 criterion 단위 격차만 보십시오.
