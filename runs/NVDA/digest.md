# Digest — NVDA (as of 2026-09-17)
score 70.86 (ex-val 74.01, Emerging Outlier) · DI 78.75 · TQ 34.25 · archetype non_fit — 어느 유형 조건도 충족하지 않거나 게이트 점수 미달 · veto UNRESOLVED · state WATCH
signals {'price_to_base_value': 1.0304, 'valuation_percentile_5y': 0.05, 'revenue_cagr_next_3y': 0.29, 'market_cap_usd': 5326671900000.0} · reachable(raw) []
veto codes: V1 경영진 정직성 또는 회계 신뢰성 훼손 / V2 구조적으로 과도한 외부자본 조달 의존 / V3 장기간 지속되는 과도한 희석 / V4 고객가치 없이 마케팅·보조금에 의존하는 성장 / V5 증분 ROIC의 구조적 붕괴 / V6 해자의 지속적인 축소 / V7 현재가격이 비현실적인 Bull Case 이상을 요구 / V8 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성 / V9 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## structural_leadership — 75.5 (raw 75.5, spread 33.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| SL | 75.5 (55–88) | 0.65 | support | – | 구조 변화는 실재하고 NVIDIA는 수혜자가 아니라 규칙 제정자다. 개발자 750만명, 지원 애플리케이션 6,000개, TOP500의 78% 점유, 누적 R&D $76.7B는 단일 사이클로 설명되지 않는다. 매출 $96.2B 분기에 판관비가 1.4%에 불과하다는 점도 수요가 영업력이 … |
bull: 가속 컴퓨팅으로의 전환은 경기순환이 아니라 비용곡선 재편이다. CUDA 개발자 750만명, TOP500의 78%, 누적 R&D $76.7B가 카테고리 규칙을 NVIDIA가 정의한다는 증거다. 연간 아키텍처 cadence(Blackwell Ultra→Vera Rubin)로 경쟁 기준선 … / bear: 매출의 92.5%가 Data Center 단일 시장이고 상위 3개 고객이 44%다. 미국 수출규제만으로 중국 데이터센터 시장이 통째로 사라졌고, EU·미국·영국·중국·한국 경쟁당국이 동시에 자료를 요구 중이다. 구조적 성장과 공급부족발 가격효과를 아직 분리할 수 없다.
unknowns: 가속 컴퓨트 시장에서 NVIDIA의 물량·금액 점유율이 공시되지 않는다. · 최근 성장 중 가격 상승 기여분과 물량 기여분의 분리.

## customer_product — 75.25 (raw 75.25, spread 35.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| CP | 75.25 (50–85) | 0.55 | support | V4=conditional, V8=conditional | 고객가치는 입증된다. 매출 $96.2B 분기에 75.0% gross margin을 유지하면서 판관비가 1.4%에 불과하다는 조합은 프로모션이나 영업력으로 만들어지지 않는다. 고객 선수금이 H1에 $15.6B 유입되고 공급 약정이 $279B 쌓여 있다는 것도 지불의사의 직접 증거다. 그… |
bull: 분기 매출 $96.2B에서 gross margin 75.0%를 받아내면서 판관비는 매출의 1.4%다. 할인·마케팅이 아니라 제품이 수요를 만든다는 가장 강한 증거다. H1에 고객 선수금 $15.6B이 유입됐고 공급 약정 $279B이 뒤를 받친다. AI 랩에게 이 제품은 미션크리티컬이다. / bear: 하드웨어라 NRR·churn 공시가 없어 유지율을 코호트로 검증할 수 없다. 더 큰 문제는 벤더 금융이다. H1에 지분증권 $42.4B을 매입했고 AI 클라우드 리스에 $3.5B을 보증했으며, 10-Q는 이 고객군이 투자등급 자금조달 능력이 없다고 기술한다. 자기조달 수요 비중을 계산…
unknowns: NVIDIA가 지분투자·보증한 주체가 창출한 매출 비중이 공시되지 않는다. 벤더 금융 의존도를 정량화할 수 없다. · 고객의 AI 인프라 투자 회수 기간과 실제 가동률.

## moat_trajectory — 73.75 (raw 73.75, spread 35.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| MT | 73.75 (50–85) | 0.6 | support | V6=cleared | 해자는 현재 넓어지는 방향이다. 매출이 배가되는 국면에서 gross margin이 71.1%→75.0%로 상승한 것은 공급부족만으로 설명되지 않는 가격결정력이다. CUDA 개발자 750만명, 지원 애플리케이션 6,000개는 측정 가능한 생태계 피드백이고 재작성 비용이 전환장벽으로 작동… |
bull: 매출이 2배가 되는 동안 gross margin이 71.1%에서 75.0%로 올랐다. 해자가 유지가 아니라 확대되고 있다는 가장 직접적인 증거다. 개발자 750만명·애플리케이션 6,000개의 CUDA 자산은 재작성 비용이라는 실질 전환장벽이고, Hugging Face가 개방형 모델 유… / bear: 해자를 위협하는 쪽이 자금 제약 없는 고객 본인이다. Hyperscale(+102%)이 ACIE(+138%)보다 느린 것은 자체 실리콘 전환의 초기 신호일 수 있다. Groq 비독점 라이선스에 $15.9B을 쓴 것은 추론 아키텍처 우위가 완결적이지 않다는 뜻이고, Hugging Fac…
unknowns: 커스텀 ASIC이 전체 가속 컴퓨트 물량에서 차지하는 비중. · 공급 정상화 이후 유지 가능한 gross margin 수준.

## reinvestment_fcf — 74.5 (raw 74.5, spread 33.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| RF | 74.5 (55–88) | 0.6 | support | V5=cleared, V3=cleared | 영업자본 기준 증분 수익률은 예외적으로 높다. FY25→FY26 증분 NOPAT $40.1B / 증분 영업투하자본 $39.8B로 증분 ROIC 약 101%이고, capex는 FY26 기준 매출의 2.8%에 불과하다. owner FCF/share(OCF-capex-SBC)도 FY25 $… |
bull: FY25→FY26 증분 NOPAT $40.1B을 증분 영업투하자본 $39.8B으로 얻었다. 증분 ROIC 약 101%다. capex는 매출의 2.8%에 불과해 성장이 자본집약적이지 않다. owner FCF/share는 FY25 $2.26에서 TTM $4.92로 2년 만에 2.2배가 됐… / bear: 재투자 활주로가 자본창출 속도를 못 따라간다. 그래서 H1에 자사주 $39.0B, 지분증권 $42.4B이 밖으로 나갔다. 지분증권까지 투하자본에 넣으면 증분 ROIC는 급락한다. 보고 FCF도 왜곡돼 있다. H1 운전자본이 $41.3B을 흡수했고 순이익에는 비현금 평가익 $23.7B이…
unknowns: 지분증권 $93.9B의 실현 수익률과 그 자금을 자사주에 썼을 때의 기회비용 비교. · 운전자본 증가가 영구적 수준 이동인지 일시적 계약 조건 효과인지.

## management_allocation — 73.75 (raw 73.75, spread 27.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| MA | 73.75 (55–82) | 0.55 | neutral | V1=cleared | 과거 자본배분 성적은 좋고 현재 배분은 판단을 유보해야 한다. FY26 자사주 282M주를 평균 약 $143에 사들인 것은 현재가 대비 53% 할인 매입으로 명확한 가치창출이었다. 실행력도 입증됐다. 중국 데이터센터 시장 전체를 상실하고도 매출을 배로 키웠고 H20·H200 손실을 지… |
bull: FY26에 282M주를 평균 약 $143에 매입했다. 현재가 $219.34 대비 53% 저가 매입으로 명백한 가치창출이다. 실행 트랙레코드도 강하다. 중국 시장 전체를 잃고도 매출을 배로 키웠고, H20 $4.5B·H200 $0.4B 손실을 끌지 않고 즉시 인식했다. CFO는 DSO … / bear: 자본배분의 무게중심이 검증 가능한 영역에서 자기평가 영역으로 옮겨갔다. H1 지분증권 매입 $42.4B, 평가익 $23.7B이 순이익에 계상되고 비시장성 지분 $51.2B은 Level 3다. Groq 비독점 라이선스 $15.9B, Hugging Face $11.9B의 회수 근거도 아직…
unknowns: 지분투자 대상 기업의 명세와 그들이 창출한 매출 규모. · 비시장성 지분 $51,157M의 공정가치 산정 방법과 관측 가능한 입력의 비중.

## financial_survival — 77.75 (raw 77.75, spread 26.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| FS | 77.75 (62–88) | 0.7 | support | V2=cleared, V3=cleared, V9=cleared | 재무 생존력 자체는 최상위권이다. 순현금 $23.2B, 투자자산 $93.9B, TTM 영업현금흐름 $134.4B에 대해 총차입은 $33.4B(OCF의 0.25배)이고 1년 내 만기는 $1.0B뿐이며 만기는 2060년까지 분산돼 있다. $25B 기업어음 한도는 전액 미사용이다. cape… |
bull: 순현금 $23.2B에 투자자산 $93.9B이 더해지고 TTM 영업현금흐름은 $134.4B이다. 총차입 $33.4B은 TTM OCF의 0.25배이며 1년 내 만기는 $1.0B뿐, 만기는 2060년까지 사다리형이다. $25B 기업어음 한도는 미사용이고 covenant도 준수 중이다. ca… / bear: 위험은 대차대조표가 아니라 부외에 있다. 총약정 $366B은 TTM 매출의 1.2배이고 그중 구속력 있는 공급·capacity 약정이 $279B다. 수요가 꺾이면 이것이 재고·약정 손실로 전환된다는 것은 H20 $4.5B, H200 $0.4B으로 이미 입증됐다. AI 클라우드 리스 보…
unknowns: 공급·capacity 약정 $279B 중 취소 가능 비중과 구속력 있는 비중. · land/power/shell 보증의 파트너별 신용도와 최대 총노출.

## expectation_valuation — 53.0 (raw 53.0, spread 65.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| EV | 53.0 (20–85) | 0.6 | neutral | V7=cleared | 고정 정책(9% 할인율, terminal 15/20/25x)으로 owner FCF/share(OCF-capex-SBC)를 10년 추정하면 Bear $75, Base $213, Bull $431이다. 종가 $219.34는 Base의 1.03배여서 기대차가 사실상 없다. Base 자체가 … |
bull: AI 인프라 투자가 10년 사이클이면 Y10 owner FCF/share $29.6, 25x terminal로 주당 $431(+97%)이다. CUDA·NVLink에 Hugging Face가 더해져 개발자 표준을 유지하고 네트워킹·소프트웨어 attach가 커지면 점유를 마진 훼손 없이 … / bear: 고객 상당수가 자체 조달 능력이 부족해 NVIDIA가 지분투자 H1 $42.4B와 land/power/shell 보증으로 수요를 직접 대고 있다. 이 고리가 끊기면 매출은 둔화가 아니라 역성장한다. 디지션 국면에서 GM 60%대와 재고·AR 손상이 겹치면 Y3 owner FCF/sha…
unknowns: AR 증가 $24,590M 중 투자등급 고객 비중과 NVIDIA가 지분·보증으로 자금을 댄 AI 클라우드 비중이 공시되지 않는다. 매출의 자기조달 비율을 계산할… · FY28 supply/capacity 약정 $87B가 실제 수요 정체 신호인지 발주 시계(booking horizon) 한계인지 구분할 수 없다.

## asymmetry — 66.75 (raw 66.75, spread 57.0, DISPUTE)
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| AS | 66.75 (25–82) | 0.55 | neutral | V9=conditional, V7=cleared | 비대칭성은 상방보다 하방이 크다. 시총 $5.33T에서 5x/10x는 각각 $26.6T/$53.3T로 글로벌 주식시장 규모 대비 비현실적이고, 가장 낙관적인 경로도 10년 3.4x(CAGR 약 13%)에 그친다. 하방은 Bear 주당 $75로 -66%다. 확률을 Bear 30/Base… |
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

## evidence_quality
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| ED | 62 | 0.7 | neutral | – | 점수와 Veto를 좌우하는 수치는 대부분 1차 자료로 추적된다. 8개 도메인 보고서의 핵심 증거가 runs/NVDA/sources의 10-K·10-Q·8-K 원문 줄번호로 연결되고, owner FCF 정의(OCF-capex-SBC, 희석주식수)가 EV·RF·MA에서 일관되게 쓰였다. … |
unknowns: NVIDIA 지분투자·보증 대상 기업향 매출 비중 — 현재 어떤 공시에도 없고, 회사가 새 공시를 추가하지 않는 한 다음 10-Q로도 해소되지 않는다. · FY26 10-K의 시장 플랫폼 구분(Gaming/ProViz/Auto)과 FY27의 신구분(Hyperscale/ACIE/Edge) 간 소급 재작성 여부.

## red_team
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| RT | 38 | 0.6 | oppose | V1=cleared, V2=cleared, V4=conditional, V5=cleared, V6=cleared, V8=conditional, V7=cleared | 공매도 논리 한 줄: NVIDIA는 자기 자본의 일부를 매출로, 자기 평가의 일부를 이익으로 계상하고 있으며 둘 다 순환이 멈추면 동시에 역전된다. H1 순이익 $118.0B와 owner FCF $66.0B의 격차는 비현금 평가익 $23.7B과 운전자본 유출 $41.3B이 만든다. 같… |
unknowns: 지분투자·보증 대상 기업향 매출 비중 — 순환 구조의 크기를 정하는 단일 수치인데 공시되지 않는다. · 공급·capacity 약정 $279B 중 취소 가능 비중.

## macro_overlay
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| MO | 45 | 0.55 | neutral mult=0.7 | – | 금융여건이 완화에서 긴축으로 방향을 틀었다. 연준은 2026-09-16 FOMC에서 25bp를 인상해 3.75~4.00%로 올렸다. 3년여 만의 첫 인상이며 유가 급등발 인플레이션이 이유다. 점도표는 2026년 말과 2027년 말 모두 4.00~4.25%를 가리킨다. 실질금리 상승은 … |
unknowns: 유가발 인플레이션의 지속 기간과 연준의 반응함수. · 긴축 전환이 AI 인프라 투자 자금조달(특히 투자등급 미만 AI 클라우드)에 미치는 시차 효과.

## investment_committee
| agent | score (bear–bull) | conf | verdict | vetoes | thesis |
|---|---|---|---|---|---|
| IC | 70.36 | 0.6 | neutral | – | 종합점수 70.36(밸류에이션 제외 73.43), 기계적 유형 non_fit, Hard Veto 3건 미해소로 신규 매수를 승인하지 않는다. 사업의 질은 높다. 8개 도메인 중 6개가 71~78점이고 재무생존 77.75, DI 78.75다. 문제는 가격과 미공시 항목 하나다. 종가 $… |
unknowns: NVIDIA 지분투자·보증 대상 기업향 매출 비중 — Veto 3건이 여기에 걸려 있고 현행 공시로는 해소되지 않는다. · 공급·capacity 약정 $279B의 취소 가능 비중.

## veto conflicts
- V9: AS=conditional, FS=cleared
