# Taiwan Semiconductor Manufacturing Company (TSM) 상세 기업분석 보고서

**기준일: 2026-09-18 | Harness: GPT-5.6 Sol / high | 최종 분류: Emerging Outlier · Compounder**

## 0. Executive Summary

TSMC는 2026년 현재 글로벌 leading-edge foundry의 구조적 리더다. FY2025 매출은 US$121.4B, OCF는 US$72.5B였고, 2026년 2분기에는 매출 US$40.2B, gross margin 67.7%, operating margin 60.3%를 기록했다. 2026년 1~8월 누적 매출은 전년 대비 39.3% 증가했고, 2nm는 2Q26부터 wafer revenue의 3%를 차지하며 본격 ramp에 진입했다.

Harness 최종 결과는 **76.32점**, ex-valuation **81.61점**, 분류는 **Emerging Outlier**, archetype은 **Compounder**다. Hard Veto 9개는 모두 CLEARED, 기계적 포지션 가이드는 **2–4%**, macro pacing은 **0.7**, IC verdict는 **support**다.

TSMC의 핵심 투자논리는 사업의 질 자체가 아니라 **현재 가격이 그 질을 얼마나 선반영하고 있는가**에 있다. 2026-09-18 ADR 종가 $434.67 대비 locked owner-FCF/share DCF는 Bear $120.10 / Base $377.78 / Bull $600.72다. Current/Base는 **1.1506**으로 Compounder valuation gate인 1.2는 통과하지만, 시장가격이 Base보다 약 15% 높기 때문에 기대수익률의 상당 부분은 향후 owner FCF/share가 Base 경로를 웃도는 데 달려 있다.

핵심 결론은 다음과 같다.

1. **TSMC의 해자는 단순 미세공정 선두가 아니라 process + yield + packaging + design ecosystem + capacity scale의 복합체**다.
2. AI/HPC는 현재 매출·마진·설비투자 수익률을 동시에 끌어올리고 있다.
3. 재투자 능력은 탁월하지만 2026년 capex US$52B-$56B와 해외 fab 확대는 장기 ROIC의 가장 중요한 시험대다.
4. 고객집중과 Taiwan/geopolitical tail risk는 실재하지만, frozen evidence만으로 Hard Veto의 치명적 단일종속·과도한 영구손실 predicate를 확정할 수준은 아니다.
5. 현재 주가는 저평가 구간이 아니라 **고품질 Compounder를 높은 기대수준에서 보유하는 구간**에 가깝다.

---

## 1. 기본 정보 및 Frozen Inputs

- Ticker: **TSM**
- 기준일: **2026-09-18**
- Frozen ADR price: **$434.67**
- 1 ADR = **5 common shares**
- Common shares outstanding: 약 **25.933B**
- ADR-equivalent shares: 약 **5.187B**
- Market cap: 약 **$2.254T**
- 2Q26 cash & marketable securities: **NT$3.518T**
- 2Q26 interest-bearing debt: **NT$1.032T**
- Net cash reserves: **NT$2.486T**
- Net cash per ADR: **$15.17**

### Harness 결과

| 항목 | 결과 |
|---|---:|
| Core Score | **76.32** |
| Ex-Valuation | **81.61** |
| Classification | **Emerging Outlier** |
| Archetype | **Compounder** |
| Hard Veto | **CLEARED** |
| Mechanical State | **NORMAL_CANDIDATE** |
| Position | **2–4%** |
| Macro Pacing | **0.7** |
| IC Verdict | **support** |
| Early Exit | **false** |

Provider calibration은 OpenAI family 하향보정이 적용됐다. 현재 calibration은 NVDA 한 종목 paired sample을 기초로 한 잠정치이므로 절대점수보다 **도메인별 상대 강도와 threshold 통과 여부**를 우선 해석해야 한다.

---

## 2. 기업 구조: 왜 TSMC가 단순 제조업체가 아닌가

TSMC의 본질은 고객 설계를 대신 생산하는 dedicated foundry다. 그러나 경제적 실체는 단순 생산대행보다 훨씬 복합적이다.

TSMC가 공급하는 것은:
- leading-edge process technology
- yield learning
- 고품질 대규모 생산능력
- design enablement
- EDA/IP ecosystem
- advanced packaging
- supply assurance
- 고객 time-to-market

이다.

반도체 설계 고객에게 이 모든 요소는 제품 성능, 전력효율, 원가, 출시시점에 직접 영향을 준다. 따라서 TSMC의 가격결정력은 wafer 자체보다 **전체 시스템 수준의 성공확률을 높여주는 능력**에서 나온다.

---

## 3. Technology Leadership

FY2025 wafer revenue mix:
- 3nm: **24%**
- 5nm: **36%**
- 7nm: **14%**
- 7nm 이하 advanced technologies: **74%**

2Q26:
- 2nm: **3%**
- 3nm: **30%**
- 5nm: **33%**
- 7nm: **11%**
- advanced nodes: **77%**

이는 중요한 구조적 신호다. 기술 선도는 단순 roadmap 발표가 아니라 실제 revenue mix로 전환되고 있다.

N2의 초기 revenue contribution이 이미 발생했고, 향후 N2P/A16까지 이어질 경우 고객의 설계 migration은 다시 yield-learning과 ecosystem lock-in을 강화한다.

### 해자의 순환 구조

1. 선도 node 개발
2. 대형 고객 early tape-out
3. 높은 volume
4. yield learning 가속
5. unit cost 개선
6. 더 많은 고객 유입
7. 설계 ecosystem 확대
8. 다음 node R&D와 capacity funding

이 순환은 작은 foundry가 자본만 투입한다고 쉽게 복제하기 어렵다.

---

## 4. Advanced Packaging

AI accelerator의 병목은 transistor scaling만이 아니다.

HBM, chiplet, interconnect, package power/thermal design이 중요해질수록 CoWoS/3DFabric 같은 advanced packaging은 별도 가치풀로 커진다.

이 점은 TSMC 해자의 질을 높인다.

과거에는:
**process node leadership**

이 핵심이었다면, AI 시대에는:

**process + packaging + system integration**

으로 경쟁축이 이동한다.

따라서 경쟁사가 특정 node의 transistor 성능을 따라잡아도 TSMC 전체 ecosystem과 packaging capacity를 동시에 복제해야 한다.

---

## 5. AI/HPC 성장

FY2025 매출은 NT$3.809T, US$121.4B로 31.6% 성장했다.

2026년 2분기:
- Revenue: **US$40.2B**
- NTD revenue growth: **+36.0%**
- USD revenue growth: **+33.7%**
- Net income: **NT$706.6B**, +77.4%
- Gross margin: **67.7%**
- Operating margin: **60.3%**

2026년 월별 매출:
- July: **NT$467.6B**, +44.7%
- August: **NT$514.8B**, +53.3%
- Jan-Aug: **NT$3.387T**, +39.3%

이 속도는 단순 가격인상보다는 AI/HPC 수요, advanced-node mix, utilization, packaging bottleneck이 동시에 작동하고 있음을 시사한다.

### 3Q26 guidance

- Revenue: **US$44.6B-$45.8B**
- Gross margin: **65%-67%**
- Operating margin: **56%-58%**

2Q의 매우 높은 margin이 일부 정상화되더라도 역사적으로 매우 높은 수준이다.

---

## 6. 고객 가치와 집중도

2025:
- Top 10 customers: **78%**
- Largest customer: **19%**
- Second-largest customer: **17%**

고객집중은 명백한 리스크다.

하지만 concentration을 곧바로 fatal dependency로 볼 수는 없다.

TSMC의 고객 기반은:
- HPC / AI accelerators
- smartphones
- custom silicon
- IoT
- automotive
- specialty semiconductor

등 여러 end market으로 분산되어 있고, 수백 개 고객에 서비스를 제공한다.

또 대형 고객도 TSMC에 의존하지만 TSMC 역시 대형 고객의 volume과 learning에 의존한다. 즉 관계는 일방적인 supplier dependency보다 **상호 의존적인 ecosystem**에 가깝다.

Hard Veto V8은 largest customer 19%라는 숫자만으로는 성립하지 않는다고 판단했다. 치명적 실패경로까지 입증되어야 하기 때문이다.

---

## 7. 재무제표 분석

### FY2025

- Revenue: **US$121.4B**
- Net income attributable to parent: **US$54.1B**
- Gross margin: **59.9%**
- OCF: **US$72.5B**
- Capex: 약 **US$40.6B**
- R&D: **US$7.86B**

단순 owner-style FCF:

**OCF - Capex ≈ US$32.0B**

ADR 기준 약 **$6.16/share** 수준이다.

### H1 2026

- OCF: **NT$1.482T**
- Capex: **NT$846.8B**
- FCF proxy: **NT$635.6B**

ADR 기준 H1 약 **$3.88**, 단순 연율화 약 **$7.76**다.

즉 record capex cycle 속에서도 owner FCF/share는 FY2025보다 증가하는 방향이다.

---

## 8. 재투자와 증분 ROIC

Harness Reinvestment & FCF calibrated score는 **80.17**이다.

TSMC의 특이점은 매우 큰 규모의 자본을 내부에서 흡수하면서도 높은 수익성을 유지한다는 것이다.

2025:
- OCF ≈ $72.5B
- Capex ≈ $40.6B
- R&D ≈ $7.9B

Capex + R&D는 OCF의 약 **67%**다.

즉 회사는 생성한 현금의 대부분을 내부 기술·capacity에 재투자한다.

2026 capex guidance는 **US$52B-$56B**로 더 증가한다.

### 긍정적 해석

현재 AI/HPC 수요와 67%대 gross margin을 보면 이 투자는 높은 incremental return을 내고 있다.

### 부정적 해석

해외 fab은 Taiwan cluster보다:
- construction cost
- labor cost
- supplier density
- yield-learning speed
- utilization

측면에서 불리할 수 있다.

따라서 앞으로의 가장 중요한 ROIC 질문은:

> **글로벌 diversification이 moat를 강화하면서도 그룹 incremental ROIC를 얼마나 유지할 수 있는가?**

이다.

---

## 9. Arizona / Japan / Europe Expansion

TSMC는 Taiwan 이외 생산능력을 빠르게 확장 중이다.

이는 두 가지 목적을 가진다.

1. 고객의 geographic diversification 요구 대응
2. supply-chain resilience 및 정책 환경 대응

하지만 투자자는 이를 순수한 성장 CAPEX로 봐서는 안 된다.

일부는:
- 전략적 resilience investment
- 고객 요구 대응
- 정책·보조금 대응

성격을 가진다.

따라서 Taiwan fab와 동일한 ROIC를 기대하기 어렵다.

장기적으로 TSMC의 consolidated margin이 내려갈 수 있는 가장 현실적인 구조요인 중 하나다.

---

## 10. Balance Sheet와 Financial Survival

2Q26:
- Cash + marketable securities: **NT$3.518T**
- Interest-bearing debt: **NT$1.032T**
- Net cash: **NT$2.486T**

Net cash/ADR는 약 **$15.17**이다.

FY2025 OCF만 US$72.5B였기 때문에 leverage 리스크는 사실상 없다.

Harness Financial Survival score는 **84.17**.

따라서 TSM의 downside는:
- refinancing
- liquidity
- forced equity issuance

가 아니라:
- physical disruption
- demand cycle
- technology loss
- geopolitical/export-control shocks

이다.

---

## 11. Taiwan / Geopolitical Tail Risk

TSMC 20-F는 Taiwan의 정치·군사 조건, 무역제한, export control, 해외사업 규제 등을 명시적인 risk factor로 다룬다.

이 위험은 일반적인 corporate risk와 다르다. 극단적 시나리오에서는 balance sheet보다 physical capacity와 global semiconductor supply chain 자체가 문제된다.

그러나 투자평가에서 확률을 임의로 추정해 Hard Veto로 확정하는 것은 적절하지 않다.

이번 harness는 다음처럼 처리했다.

- risk 자체: **material**
- V9의 “영구손실 확률이 기대수익에 비해 지나치게 높음”: **CLEARED**
- 이유: frozen evidence로는 그 확률과 기대수익 대비 과도성을 입증할 수 없음

즉 이 위험은 제거된 것이 아니라 **position sizing과 required return에서 별도로 관리해야 할 tail risk**다.

---

## 12. Valuation

Locked owner-FCF/share DCF:

| Scenario | Value/ADR | Current 대비 |
|---|---:|---:|
| Bear | **$120.10** | 약 **-72%** |
| Base | **$377.78** | 약 **-13%** |
| Bull | **$600.72** | 약 **+38%** |

Current/Base = **1.1506**

Terminal value fraction:
- Bear: **57.4%**
- Base: **69.9%**
- Bull: **75.8%**

Base owner FCF/share path:

$8.8 → $10.5 → $12.5 → $14.8 → $17.0 → $19.5 → $22.0 → $24.5 → $27.0 → $30.0

이 경로는 현재 H1 2026 annualized FCF 약 $7.8/ADR에서 시작해 상당한 장기 복리를 가정한다.

하지만 TSMC의 기술·capacity 리더십과 AI/HPC 성장률을 고려하면 불가능한 경로는 아니다.

문제는 현재가가 이미 Base보다 높다는 점이다.

즉 현재 매수는:

> **“TSMC가 좋은 회사인가?”**

보다

> **“Base보다 높은 FCF compounding을 실현할 가능성이 충분한가?”**

가 핵심 질문이다.

---

## 13. Harness Domain Scores

| Domain | Calibrated Score |
|---|---:|
| Structural Leadership | **87.17** |
| Moat Trajectory | **85.17** |
| Management Allocation | **84.67** |
| Financial Survival | **84.17** |
| Customer / Product | **83.25** |
| Disruptive Innovation | **83.42** |
| Reinvestment & FCF | **80.17** |
| Asymmetry | **62.83** |
| Expectation Valuation | **46.33** |
| Turnaround Quality | **20.00** |

구조가 명확하다.

**사업 품질은 매우 높고 valuation/asymmetry가 전체 점수를 낮춘다.**

Ex-Valuation이 **81.61**인 이유다.

---

## 14. 왜 Compounder인가

Compounder 조건:

- price/Base ≤1.2 → **1.1506: 통과**
- MT ≥76 → **85.17: 통과**
- RF ≥76 → **80.17: 통과**
- MA ≥72 → **84.67: 통과**
- FS ≥72 → **84.17: 통과**
- EV ≥42 → **46.33: 통과**

모든 조건이 통과했다.

Moonshot은 시총 조건에서 불가능하고, Turnaround는 TQ가 낮으며, Expectation Gap은 현재 가격이 Base 대비 할인 상태가 아니므로 탈락한다.

---

## 15. Hard Veto 검토

모든 Veto는 **CLEARED**.

### V2 외부자본 조달 의존
거대한 OCF와 순현금으로 cleared.

### V3 장기 과도한 희석
TSMC는 SBC/주식발행 의존형 구조가 아니므로 cleared.

### V5 증분 ROIC 붕괴
매출, margin, OCF 증가가 이를 반증.

### V6 해자 축소
advanced-node revenue mix와 margin 추세가 오히려 강화.

### V7 Bull+ 가격
현재가는 Base보다 높지만 Bull보다 훨씬 낮다.

### V8 치명적 단일 dependency
고객집중은 높지만 최대 고객 19%로, fatal single dependency의 증거는 아님.

### V9 영구손실 확률 과도
geopolitical tail risk는 존재하지만 frozen evidence로 exact predicate를 입증하지 못했다.

---

## 16. Upgrade Trigger

다음이 확인되면 score와 intrinsic value가 상승할 수 있다.

- N2/A16 ramp가 예상보다 빠름
- advanced packaging 병목 해소와 높은 pricing 지속
- AI/HPC revenue growth 20%+ 장기 지속
- overseas fab margin dilution이 제한적
- owner FCF/share가 Base path를 상회
- customer concentration 감소
- 2027 이후 capex/revenue 정상화

---

## 17. Downgrade Trigger

- leading-edge node delay 또는 yield 문제
- Samsung/Intel foundry의 기술격차 급격한 축소
- major customer의 의미 있는 dual-source/insourcing 확대
- AI accelerator demand 급격한 둔화
- overseas fabs의 지속적인 낮은 utilization
- group gross margin의 구조적 55% 이하 하락
- owner FCF/share가 capex 증가에도 정체
- export-control로 주요 고객 매출이 실질적으로 훼손

---

## 18. SWOT

### Strengths
- 글로벌 leading-edge foundry leadership
- world-class yield and manufacturing execution
- OIP ecosystem
- N2/A16 roadmap
- advanced packaging
- enormous scale
- net cash
- AI/HPC structural demand

### Weaknesses
- 매우 높은 capital intensity
- 고객집중
- Taiwan 생산집중
- 해외 fab 비용
- 특정 장비/소재 공급망 의존

### Opportunities
- AI accelerator
- custom silicon
- advanced packaging
- 2nm/A16
- chiplets
- HBM integration
- 글로벌 fab diversification
- automotive advanced nodes

### Threats
- geopolitical disruption
- export controls
- AI capex cycle reversal
- Samsung/Intel competition
- 고객 insourcing
- 해외 fab ROIC dilution
- 전력/물/장비 bottleneck

---

## 19. 최종 정리

TSMC는 이번 harness에서 **전형적인 고품질 Compounder**로 분류됐다.

핵심 강점은:
- technology leadership
- widening moat
- customer mission-criticality
- high-return reinvestment
- financial survival

이다.

반대로 투자수익을 제한하는 것은 현재 valuation이다.

현재 가격에서는 “싸서 사는” thesis가 아니라:

**“세계 최고 수준의 반도체 제조 해자가 AI/HPC 시대에도 Base보다 높은 owner-FCF/share 복리를 만들어낼 것”**

이라는 thesis가 필요하다.

따라서 이번 판정은:

**Emerging Outlier / Compounder / Hard Veto CLEARED / NORMAL_CANDIDATE / 2–4% / macro pacing 0.7 / IC support**

이다.

## Source Notes

Frozen repository evidence:
- runs/TSM/sources/FY2025_20F_key_facts.txt
- runs/TSM/sources/Q2_2026_key_facts.txt
- runs/TSM/sources/2026_monthly_revenue.txt
- runs/TSM/sources/README.md

The report separates filing/company-reported historical facts from modeled DCF assumptions. GPT-5.6 Sol reports were authored in-session and validated/aggregated by the deterministic harness; no separate live OpenAI API adapter call was used.
