# Digest — NVDA (as of 2026-09-17)
score 50.65 (ex-val 52.75, Reject) · DI 78.75 · TQ 34.25 · archetype non_fit — 조기 종료: 감점 전 원점수로도 도달 가능한 유형 없음 · veto UNRESOLVED · state EARLY_EXIT_NON_FIT
signals {'price_to_base_value': 1.0304, 'valuation_percentile_5y': 0.05, 'revenue_cagr_next_3y': 0.29, 'market_cap_usd': 5326671900000.0} · reachable(raw) []
veto codes: V1 경영진 정직성 또는 회계 신뢰성 훼손 / V2 구조적으로 과도한 외부자본 조달 의존 / V3 장기간 지속되는 과도한 희석 / V4 고객가치 없이 마케팅·보조금에 의존하는 성장 / V5 증분 ROIC의 구조적 붕괴 / V6 해자의 지속적인 축소 / V7 현재가격이 비현실적인 Bull Case 이상을 요구 / V8 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성 / V9 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## expectation_valuation — 49.25 (raw 49.25, spread 65.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| EV | 49.25 (20–85) | 0.6 | neutral | V7=cleared | 고정 정책(9% 할인율, terminal 15/20/25x)으로 owner FCF/share(OCF-capex-SBC)를 10년 추정하면 Bear $75, Base $213, Bull $431이다. 종가 $219.34는 Base의 1.03배여서 기대차가 사실상 없다. Base 자체가 … |
bull: AI 인프라 투자가 10년 사이클이면 Y10 owner FCF/share $29.6, 25x terminal로 주당 $431(+97%)이다. CUDA·NVLink에 Hugging Face가 더해져 개발자 표준을 유지하고 네트워킹·소프트웨어 attach가 커지면 점유를 마진 훼손 없이 … / bear: 고객 상당수가 자체 조달 능력이 부족해 NVIDIA가 지분투자 H1 $42.4B와 land/power/shell 보증으로 수요를 직접 대고 있다. 이 고리가 끊기면 매출은 둔화가 아니라 역성장한다. 디지션 국면에서 GM 60%대와 재고·AR 손상이 겹치면 Y3 owner FCF/sha…
unknowns: AR 증가 $24,590M 중 투자등급 고객 비중과 NVIDIA가 지분·보증으로 자금을 댄 AI 클라우드 비중이 공시되지 않는다. 매출의 자기조달 비율을 계산할… · FY28 supply/capacity 약정 $87B가 실제 수요 정체 신호인지 발주 시계(booking horizon) 한계인지 구분할 수 없다.

## asymmetry — 52.75 (raw 52.75, spread 53.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| AS | 52.75 (25–78) | 0.55 | neutral | V9=conditional, V7=cleared | 비대칭성은 상방보다 하방이 크다. 시총 $5.33T에서 5x/10x는 각각 $26.6T/$53.3T로 글로벌 주식시장 규모 대비 비현실적이고, 가장 낙관적인 경로도 10년 3.4x(CAGR 약 13%)에 그친다. 하방은 Bear 주당 $75로 -66%다. 확률을 Bear 30/Base… |
bull: AI 인프라가 10년 자본재 사이클이면 Bull 경로는 Y10 owner FCF/share $29.6, 주당 $431이다. 순현금·무차입에 가까운 구조와 투자자산 $93.9B가 하방을 받치고, 네트워킹·소프트웨어·로보틱스가 추가 상승축이 된다. Bull 확률을 30%로 올리면 확률가중… / bear: 시총 $5.33T에서 5x는 $26.6T로, 25x 배수에서 순이익 $1.06T를 요구한다. 현실적 상방은 10년 3.4x(CAGR 약 13%)이며 power-law가 아니다. 반면 하방은 Bear $75(-66%)이고, 수요 일부를 NVIDIA 지분투자·보증이 떠받쳐 하락 시 상관관…
unknowns: NVIDIA가 지분·보증으로 자금을 댄 고객이 창출한 매출 비중이 공시되지 않아 하락 국면의 상관관계를 정량화할 수 없다. · Bear 시나리오에서 AR $63,059M과 재고 $31,575M의 손상률 추정 근거가 없다.

## disruptive_innovation — 78.75 (raw 78.75, spread 30.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| DI | 78.75 (60–90) | 0.7 | support | – | 가속 컴퓨팅은 진성 파괴적 혁신이고 NVIDIA는 그 신(新)가치사슬의 지배자다. 분기 Data Center 매출 $89.0B(+117% y/y)와 75.0% gross margin은 파일럿이 아니라 주류 확산과 검증된 단위경제를 뜻한다. CUDA·NVLink·네트워킹에 Hugging… |
bull: 가속 컴퓨팅은 범용 CPU 대비 10배급 비용·성능 재편이고, NVIDIA는 그 가치사슬 자체를 소유한다. Data Center +117% y/y, ACIE +138%로 주류 확산 구간이며 gross margin 75.0%가 가격결정력을 입증한다. Hugging Face 인수로 개방형… / bear: S-curve 단위경제는 NVIDIA 쪽에서만 입증됐다. 고객의 AI 투자 회수율은 미검증이고 일부 수요는 NVIDIA 지분투자·보증이 떠받친다. 대응 주체가 제약된 기존사업자가 아니라 자금력이 무제한인 하이퍼스케일러 커스텀 실리콘이라는 점이 통상의 파괴 구도와 다르다.
unknowns: 고객의 AI 인프라 투자 회수율(ROI) 실측 데이터가 공개되지 않는다. · 전체 가속 컴퓨트 물량 중 커스텀 ASIC이 차지한 비중.

## turnaround_quality — 34.25 (raw 34.25, spread 25.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| TQ | 34.25 (25–50) | 0.75 | neutral | – | NVIDIA는 턴어라운드 후보가 아니다. 이 축의 전제인 실적 저점과 self-help 회복 구조가 존재하지 않는다. 매출은 FY24 $60.9B → FY26 $215.9B로 3.5배가 됐고 Q2 FY27 영업이익률 66.2%는 사상 최고 수준이다. 회복의 동력도 경영진이 통제하는 비… |
bull: 좁게 보면 회복 요소가 있다. 중국 규제로 상각한 H20 $4.5B·H200 $0.4B는 이미 손실 처리돼 재진입 시 순수 상방이고, Edge Computing(+27% y/y)은 상대적 부진 구간에서 회복 중이다. 규제 완화가 오면 self-help 없이도 이익 정상화 폭이 크다. / bear: 턴어라운드의 전제인 저점이 없다. 매출은 FY24 $60.9B에서 FY26 $215.9B로 3.5배, Q2 영업이익률은 66.2%로 사상 최고다. 개선이 아니라 악화 중인 지표는 운전자본이다. DSO 45→60일, 재고 $21.4B→$31.6B. 정상화 대상은 저점이 아니라 현재 이익…
unknowns: 중국 재진입 시점·규모와 그때 남아 있을 상각 재고 수량. · 현재 이익률이 정상 이익률 대비 어느 정도 위인지 판단할 사이클 기준선이 없다.

