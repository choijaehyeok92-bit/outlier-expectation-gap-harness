# Current-run archetype revalidation — 2026-09-20

현재 저장된 frozen run 11개 종목을 저장소 `main`의 v3.2 실행 정책에 다시 대입했다. 원 run은 재현성을 위해 수정하지 않았다. NVDA는 최신 `NVDA-V31-2026-09-19`만 정본으로 사용했고 이전 두 run은 중복 집계에서 제외했다.

기존 run에 정식 `reports/LTG.json`이 없으므로, Outlier Growth 판정에 필요한 네 기준은 frozen cross-domain evidence만으로 보수적인 shadow 평가를 작성했다. 이 점수는 정책 마이그레이션 판정에는 사용했지만 원 run의 정식 에이전트 산출물로 가장하지 않는다.

## 결론

| 재검증 아키타입 | 종목 | 수 |
|---|---|---:|
| Compounder | 000660, MSFT, TSM, V | 4 |
| Growth | AVGO, NVDA | 2 |
| Outlier Growth | RKLB | 1 |
| Buffett-Value | ADBE, PYPL | 2 |
| Moonshot | PL | 1 |
| Non-fit / Watch | 267260 | 1 |

가장 큰 변경은 **RKLB의 Moonshot → Outlier Growth**, **PYPL의 expectation_gap → Buffett-Value**다. ADBE와 000660도 Outlier Growth 조건을 통과하지만 deterministic fit이 더 높은 Buffett-Value와 Compounder를 각각 primary로 유지한다.

## 종목별 재분류

| 종목 | 시장 | 저장 라벨 | 재검증 primary | secondary | LTG | Veto | 판정 |
|---|---|---|---|---|---:|---|---|
| 000660 | KR | Compounder | **Compounder** | Buffett-Value, Outlier Growth, Growth | 72.5 | CLEARED | 한국 강화 기준에서 Compounder·Buffett-Value·Growth·Outlier Growth가 적격이며 Compounder fit이 가장 높다. |
| MSFT | US | Compounder | **Compounder** | — | 77.5 | CLEARED | 장기 성장축은 강하지만 AS와 시장 기대오류 조건이 부족해 Compounder를 유지한다. |
| TSM | US | Compounder | **Compounder** | — | 70.0 | CLEARED | 시장 기대오류·AS·upside path가 Outlier Growth 기준에 못 미쳐 Compounder를 유지한다. |
| V | US | Compounder | **Compounder** | — | 67.0 | CLEARED | 5년 기회 규모·시장 기대오류·AS가 Outlier Growth 기준에 못 미쳐 Compounder를 유지한다. |
| AVGO | US | Growth | **Growth** | — | 76.5 | CLEARED | LTG 규모·기간은 강하지만 구체적 시장 기대오류가 65점에 못 미쳐 Growth를 유지한다. |
| NVDA | US | Growth | **Growth** | — | 77.5 | CLEARED | 장기 성장축은 강하지만 시장 기대오류가 입증되지 않아 Growth를 유지한다. |
| RKLB | US | Moonshot | **Outlier Growth** | Moonshot | 84.0 | CLEARED | LTG 84점과 모든 Outlier Growth 조건을 통과해 Moonshot보다 fit이 높은 Outlier Growth로 재분류한다. |
| ADBE | US | Buffett-Value | **Buffett-Value** | Outlier Growth, Compounder | 75.0 | CLEARED | Outlier Growth까지 통과하지만 Buffett-Value fit이 가장 높고 Compounder가 다음이다. |
| PYPL | US | expectation_gap | **Buffett-Value** | — | 58.0 | CLEARED | 사업 규모·지속기간이 Outlier Growth 기준에 못 미치며 Buffett-Value가 유일한 적격 유형이다. |
| PL | US | Moonshot | **Moonshot** | — | 79.5 | CLEARED | LTG는 통과하지만 MA 61.67이 Outlier Growth 하한 65에 못 미쳐 Moonshot을 유지한다. |
| 267260 | KR | Non-fit / Watch | **Non-fit / Watch** | — | 65.0 | UNRESOLVED | 시장 기대오류와 LTG 총점이 Outlier Growth 기준에 못 미치고 Hard Veto도 미해소다. |

## Outlier Growth 재검증

| 종목 | 5년 기회 | 10년 지속 | 문화·적응 | 기대오류 | LTG | Outlier Growth 결과 |
|---|---:|---:|---:|---:|---:|---|
| 000660 | 80 | 65 | 70 | 75 | 72.5 | 통과 |
| 267260 | 75 | 65 | 65 | 50 | 65.0 | 미통과: domain.long_term_growth, criterion.long_term_growth.market_misperception |
| ADBE | 75 | 75 | 75 | 75 | 75.0 | 통과 |
| AVGO | 90 | 75 | 75 | 60 | 76.5 | 미통과: criterion.long_term_growth.market_misperception |
| MSFT | 75 | 90 | 90 | 50 | 77.5 | 미통과: criterion.long_term_growth.market_misperception, domain.asymmetry, criterion.asymmetry.upside_path |
| NVDA | 90 | 75 | 90 | 50 | 77.5 | 미통과: criterion.long_term_growth.market_misperception |
| PL | 90 | 75 | 75 | 75 | 79.5 | 미통과: domain.management_allocation |
| PYPL | 50 | 50 | 65 | 75 | 58.0 | 미통과: domain.long_term_growth, criterion.long_term_growth.opportunity_scale_5y, criterion.long_term_growth.growth_duration_10y |
| RKLB | 90 | 90 | 75 | 75 | 84.0 | 통과 |
| TSM | 75 | 75 | 75 | 50 | 70.0 | 미통과: criterion.long_term_growth.market_misperception, domain.asymmetry, criterion.asymmetry.upside_path |
| V | 50 | 90 | 75 | 50 | 67.0 | 미통과: domain.long_term_growth, criterion.long_term_growth.opportunity_scale_5y, criterion.long_term_growth.market_misperception, domain.asymmetry, criterion.asymmetry.upside_path |

세부 rationale은 `2026-09-20-current-run-ltg-shadow-assessments.json`에 기준별로 기록했다.

## 주요 변경

- **RKLB:** LTG 84점, opportunity 90, duration 90, culture 75, misperception 75다. CP·MT·MA·FS·AS·EV와 upside/permanent-loss 조건도 모두 통과해 Outlier Growth fit 75.32가 Moonshot 72.36보다 높다.
- **PYPL:** v3.2에서 `expectation_gap`이 투자 가능 유형에서 제거됐다. 가격/Base 0.3988, FCF/주 품질 90, FS 82.67, MA 75.42, MT 66.92, AS 86.83으로 Buffett-Value를 통과한다.
- **ADBE:** Outlier Growth를 통과하지만 Buffett-Value fit 80.53이 Outlier Growth 79.90과 Compounder 79.42보다 높아 primary는 유지한다.
- **000660:** 한국 강화 기준에서도 Compounder·Buffett-Value·Growth·Outlier Growth가 적격이다. Compounder fit 80.14가 가장 높다.
- **267260:** LTG 총점 65, market misperception 50으로 Outlier Growth에 못 미친다. 가격/Base 1.0411은 한국 Compounder 상한 1.00을 넘고, 매출 CAGR 12%는 한국 Growth 하한 20%에 못 미치며 integrity Hard Veto도 `UNRESOLVED`다.
- **NVDA:** `runs/NVDA`와 `runs/NVDA-V3-2026-09-19`는 최신 `runs/NVDA-V31-2026-09-19`로 대체한다. LTG 77.5지만 market misperception 50이 하한 65에 못 미쳐 Growth를 유지한다.

## 방법과 제한

- 실행 정책: `config/strategy.json`의 strategy/schema/decision policy v3.2.
- 예전 aggregate가 criterion 세부값을 저장하지 않은 경우 동일 frozen run의 `reports/RF.json`과 `reports/AS.json` subscores를 다시 결합했다. 기존 점수는 새로 추정하지 않았다.
- LTG는 `agents/15_long_term_growth/AGENTS.md`와 `config/calibration.json`의 30/30/20/20 가중치, 5점 단위 기준을 적용했다. 각 점수는 기존 SL·CP·MT·MA·EV·AS·DI의 frozen evidence 범위 안에서만 부여했다.
- 한국 강화 기준: Compounder 가격/Base ≤1.00, Growth CAGR ≥20% 및 가격/Base ≤0.90, Buffett-Value 가격/Base ≤0.70, 한국 Moonshot 제외. 미해소 지배구조·관계자 거래·희석·자본배분 증거는 통과로 처리하지 않는다.
- 정식 `final_verdict.json` 갱신에는 각 run을 fork하고 LG, ED, RT, MO, IC를 다시 실행해야 한다. 이번 결과는 그 전 단계의 정책 마이그레이션 재분류다.

## 중복 run 처리

| 제외 run | 저장 라벨 | 대체 run |
|---|---|---|
| `NVDA` | Compounder | `NVDA-V31-2026-09-19` |
| `NVDA-V3-2026-09-19` | Non-fit / Watch | `NVDA-V31-2026-09-19` |

기계 판정 전체와 실패 조건은 동명의 revalidation JSON, LTG 근거는 shadow-assessments JSON에 기록했다.
