# Current-run archetype revalidation — 2026-09-20

현재 저장된 frozen run을 저장소 `main`의 v3.2 실행 정책에 다시 대입한 정책 마이그레이션 감사다. 원 run은 재현성을 위해 수정하지 않았다. NVDA는 가장 최신인 `NVDA-V31-2026-09-19`만 정본으로 사용했고, 이전 두 run은 중복 집계에서 제외했다.

## 결론

| 재검증 아키타입 | 종목 | 수 |
|---|---|---:|
| Compounder | 000660, MSFT, TSM, V | 4 |
| Growth | AVGO, NVDA | 2 |
| Outlier Growth | 없음 | 0 |
| Buffett-Value | ADBE, PYPL | 2 |
| Moonshot | PL, RKLB | 2 |
| Non-fit / Watch | 267260 | 1 |

Outlier Growth는 0종목으로 확정한 것이 아니라 **미검증**이다. 현재 모든 run에 `reports/LTG.json`이 없으므로, v3.2의 누락 조건 불통과 원칙에 따라 어느 종목도 해당 유형으로 승격하지 않았다.

## 종목별 재분류

| 종목 | 시장 | 기준 run | 저장 라벨 | 재검증 primary | secondary | Veto | 판정 |
|---|---|---|---|---|---|---|---|
| 000660 | KR | `000660` | Compounder | **Compounder** | Buffett-Value, Growth | CLEARED | 한국 강화 가격·성장 조건을 모두 통과했고, 적격 유형 중 deterministic fit이 가장 높다. |
| MSFT | US | `MSFT` | Compounder | **Compounder** | — | CLEARED | 적격 유형 중 Compounder fit이 가장 높다. |
| TSM | US | `TSM` | Compounder | **Compounder** | — | CLEARED | 적격 유형 중 Compounder fit이 가장 높다. |
| V | US | `V` | Compounder | **Compounder** | — | CLEARED | 적격 유형 중 Compounder fit이 가장 높다. |
| AVGO | US | `AVGO` | Growth | **Growth** | — | CLEARED | 적격 유형은 Growth 하나다. |
| NVDA | US | `NVDA-V31-2026-09-19` | Growth | **Growth** | — | CLEARED | 최신 정본 run에서 적격 유형은 Growth 하나다. |
| ADBE | US | `ADBE` | Buffett-Value | **Buffett-Value** | Compounder | CLEARED | 두 유형을 통과하지만 Buffett-Value fit이 더 높다. |
| PYPL | US | `PYPL` | expectation_gap | **Buffett-Value** | — | CLEARED | v3.2에서 expectation_gap이 제거됐고, Buffett-Value의 가격·현금흐름·생존·자본배분·해자·비대칭 조건을 모두 통과한다. |
| PL | US | `PL` | Moonshot | **Moonshot** | — | CLEARED | 적격 유형은 Moonshot 하나다. |
| RKLB | US | `RKLB` | Moonshot | **Moonshot** | — | CLEARED | 적격 유형은 Moonshot 하나다. |
| 267260 | KR | `267260` | Non-fit / Watch | **Non-fit / Watch** | — | UNRESOLVED | v3.2 적격 유형이 없고 Hard Veto도 미해소다. |

## 변경점

- **PYPL:** v3.1의 `expectation_gap`은 v3.2 투자 가능 유형 목록에서 제거됐다. 현 가격/Base 0.3988, FCF/주 품질 90, FS 82.67, MA 75.42, MT 66.92, AS 86.83으로 Buffett-Value를 통과한다.
- **NVDA:** `runs/NVDA`와 `runs/NVDA-V3-2026-09-19`는 최신 `runs/NVDA-V31-2026-09-19`로 대체한다. 최신 run의 분류는 Growth다.
- **000660:** 기본 v3.2에서 Compounder·Buffett-Value·Growth가 모두 적격이다. 한국 강화 가격/성장 기준까지 통과하며 fit이 가장 높은 Compounder를 primary로 유지한다.
- **267260:** 기본 기준에서도 적격 유형이 없고, 경영진 정직성·회계 신뢰성 관련 Hard Veto가 `UNRESOLVED`다. 한국 강화 기준에서는 가격/Base 1.0411이 Compounder 상한 1.00을 넘고, 3년 매출 CAGR 12%가 Growth 하한 20%에 못 미친다.

## 방법과 제한

- 실행 정책: `config/strategy.json`의 strategy/schema/decision policy v3.2.
- 예전 aggregate가 criterion 세부값을 저장하지 않은 경우, 동일 frozen run의 `reports/RF.json`과 `reports/AS.json` subscores를 다시 결합했다. 점수나 증거를 새로 추정하지 않았다.
- 한국 강화 기준: Compounder 가격/Base ≤1.00, Growth CAGR ≥20% 및 가격/Base ≤0.90, Buffett-Value 가격/Base ≤0.70, 한국 Moonshot 제외. 미해소 지배구조·관계자 거래·희석·자본배분 증거는 통과로 처리하지 않는다.
- 원 run은 frozen snapshot이므로 이 감사에서 `final_verdict.json`을 덮어쓰지 않았다. Outlier Growth를 최종 판정하려면 각 run을 fork한 뒤 LTG, ED, RT, MO, IC를 다시 실행해야 한다.

## 중복 run 처리

| 제외 run | 저장 라벨 | 대체 run |
|---|---|---|
| `NVDA` | Compounder | `NVDA-V31-2026-09-19` |
| `NVDA-V3-2026-09-19` | Non-fit / Watch | `NVDA-V31-2026-09-19` |

기계 판정 세부값과 실패·누락 조건은 동명의 JSON 파일에 기록했다.
