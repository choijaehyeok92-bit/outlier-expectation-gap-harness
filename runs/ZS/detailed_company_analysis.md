# Zscaler, Inc. (ZS) 상세 기업분석 보고서

**기준일: 2026-09-18 | Harness: GPT-5.6 Sol / high | Triage Early Exit**

## 0. Executive Summary

Zscaler는 클라우드 네이티브 Zero Trust 보안의 대표 기업으로, FY2026 매출은 $3.353B로 25% 성장했고 ARR은 $3.771B로 25% 성장했다. Red Canary를 제외한 organic ARR도 약 20% 성장했다. FY2027 가이던스는 매출과 ARR 모두 약 17% 성장으로, 고성장 단계에서 지속 가능한 중고속 성장 단계로 이동하는 모습이다.

하지만 투자판정에서 가장 중요한 문제는 **기업 FCF와 주주 관점 owner FCF 사이의 간극**이다. FY2026 회사 정의 FCF는 $779.1M이지만 SBC가 $821.9M으로 FCF보다 크다. OCF에서 capex, capitalized software, SBC를 모두 경제적 비용으로 차감하면 owner-style FCF proxy는 약 **-$42.8M**으로 사실상 0에 가깝다.

Locked DCF는 Bear $45.41 / Base $162.29 / Bull $352.64이고, 2026-09-18 종가 $197.31은 Base의 약 **1.216배**다. 이 값은 Compounder gate인 1.20을 아주 근소하게 초과한다.

Triage 결과:
- Core score: **52.13** — 단, coverage 25%의 triage-only score
- Ex-Valuation score: **64.58**
- Classification: **Reject**
- Archetype: **Non-fit / Avoid**
- Reachable archetypes: **없음**
- State: **EARLY_EXIT_NON_FIT**
- Position: **0%**
- Hard Veto: **PENDING_REVIEW**
- IC: **미실행**

이 결과는 Zscaler의 사업 품질 전체가 Reject라는 의미가 아니다. 현재 가격과 triage 점수만으로는 어떤 archetype도 도달할 수 없어 나머지 9개 agent를 실행하지 않았다는 screening 결과다.

---

## 1. Frozen Inputs

- Ticker: **ZS**
- 기준일: **2026-09-18**
- Frozen price: **$197.31**
- Shares outstanding reference: **163.055M**
- Market cap: 약 **$32.17B**
- Cash and cash equivalents: **$928.4M**
- Short-term investments: **$2.546B**
- Convertible senior notes: **$1.696B**
- Liquid net cash: 약 **$1.778B**
- Net cash/share: **$10.90**

Zscaler는 순현금 구조이므로 생존 리스크는 낮다. 다만 높은 SBC 때문에 현금흐름의 주당 귀속가치는 회사가 제시하는 FCF보다 보수적으로 봐야 한다.

---

## 2. FY2026 실적

FY2026:
- Revenue: **$3.353B**, +25%
- Ex-Red Canary revenue growth: 약 **20%**
- Subscription/support mix: 약 **98%**
- GAAP operating loss: **-$133.3M**
- GAAP net loss: **-$63.2M**
- OCF: **$1.130B**
- Company-defined FCF: **$779.1M**
- SBC: **$821.9M**
- RPO: **$7.365B**
- Deferred revenue: 약 **$2.926B**

Q4 FY2026:
- Revenue: **$898.2M**, +25%
- ARR: **$3.771B**, +25%
- Red Canary contribution: **$141M ARR**
- Ex-Red Canary ARR: **$3.630B**, +20%
- Net new ARR ex-Red Canary: +17%
- Non-GAAP operating margin: **24%**
- GAAP operating loss: **-$15.5M**
- OCF: **$279.3M**
- FCF: **$60.8M**

Q4 FCF가 크게 낮아진 이유는 capex와 internal-use software 투자가 **$218.5M**으로 급증했기 때문이다. 이것이 일회성 인프라 확장인지, AI/security workload 확장에 필요한 구조적 자본집약도 상승인지가 중요하다.

---

## 3. FY2027 가이던스

Management guidance:
- Revenue: **$3.908B-$3.938B**, +16.6%-17.5%
- ARR: **$4.396B-$4.426B**, +16.6%-17.4%
- Non-GAAP gross margin: 약 **80%**
- Non-GAAP operating income: **$924M-$932M**
- FCF margin: **23.0%-23.5%**

성장률은 여전히 높지만 FY2026의 25%에서 FY2027 약 17%로 정상화된다.

FY2027 midpoint revenue 약 $3.923B와 23.25% FCF margin을 단순 적용하면 회사 정의 FCF는 약 **$912M**이다. 현재 market cap 약 $32.17B 대비 약 **35x forward company FCF** 수준이다.

그러나 이 FCF는 SBC 경제비용을 차감하지 않는다. 주당 intrinsic value 관점에서는 **SBC가 revenue/FCF보다 얼마나 빠르게 정상화되는가**가 핵심이다.

---

## 4. Zero Trust Exchange와 해자

Zscaler의 원래 투자논리는 명확하다.

전통 보안:
- hub-and-spoke network
- firewall
- VPN
- trusted internal network

Zscaler:
- 사용자/기기/workload를 network에 연결하지 않고
- identity와 policy 기반으로
- 필요한 application/data에 직접 연결

한다.

이 구조는 공격 surface와 lateral movement를 줄이며, SaaS/cloud/mobile 환경에 더 적합하다.

AI 시대에는 이 구조가 user뿐 아니라 **AI agents와 models**로 확장된다. AI agent가 machine speed로 application과 data를 호출하는 환경에서는 identity, segmentation, inline inspection, data protection이 중요해진다.

### 구조적 강점

1. Cloud-native Zero Trust architecture
2. 대규모 글로벌 security cloud
3. 사용자 보안에서 workload/branch/data/AI까지 확장
4. high recurring revenue
5. 고객 workflow에 깊이 삽입되는 policy layer
6. AI security와 agent governance라는 신규 TAM

### 구조적 위험

1. Palo Alto Networks의 platformization
2. Netskope의 SASE 경쟁
3. Cloudflare의 network/security convergence
4. Microsoft 등 hyperscaler의 native security bundling
5. 가격경쟁과 bundle discounting

즉 ZS의 해자는 “Zero Trust라는 아이디어” 자체가 아니라 **동일 architecture에서 얼마나 많은 트래픽·policy·data-security use case를 통합하는가**에 달려 있다.

---

## 5. Red Canary 인수

Zscaler는 2025-08-01 Red Canary를 **$651.4M cash**에 인수했다.

Red Canary는 managed detection and response/MDR 및 SecOps 영역의 기업으로, ZS의 Zero Trust Exchange를 endpoint/SOC workflow 쪽으로 확장한다.

FY2026 Q4 ARR:
- Reported ARR: $3.771B
- Red Canary contribution: $141M
- Ex-Red Canary ARR: $3.630B

따라서 reported +25% 성장과 organic +20% 성장을 구분해야 한다.

전략적으로는:
**Zero Trust access → threat detection → Agentic SecOps**

로 value chain을 넓힐 수 있다.

하지만 평가 기준은 acquisition revenue가 아니라:
- cross-sell rate
- retention
- sales efficiency
- owner FCF/share
- goodwill/intangible return

이다.

---

## 6. 현금흐름의 질과 SBC

FY2026:
- OCF: $1.1297B
- Property/equipment/other purchases: $277.3M
- Capitalized software: $73.2M
- Company FCF: 약 $779.1M
- SBC: $821.9M

Owner-style proxy:

**$1.1297B - $277.3M - $73.2M - $821.9M ≈ -$42.8M**

이는 Zscaler 분석에서 가장 중요한 숫자다.

회사의 cash balance는 실제로 증가할 수 있지만, SBC는 기존 주주의 economic ownership을 희석한다. 따라서 장기 투자자에게 중요한 것은 회사 FCF 자체보다:

> **SBC-adjusted owner FCF/share**

이다.

ZS가 진정한 Compounder가 되려면:
1. revenue/ARR가 계속 성장하고
2. SBC/revenue가 하락하며
3. diluted share growth가 안정되고
4. FCF margin이 유지되어

owner FCF/share가 빠르게 증가해야 한다.

---

## 7. Locked DCF

정책:
- Required return: 9%
- Horizon: 10 years
- Terminal multiples: 15x / 20x / 25x
- Net cash/share: $10.90

### Bear owner FCF/share
-0.3 → 0 → 0.5 → 1.0 → 1.5 → 2.0 → 2.5 → 3.0 → 3.5 → 4.0

Value: **$45.41**

### Base
1.0 → 2.0 → 3.2 → 4.5 → 5.8 → 7.2 → 8.7 → 10.2 → 11.8 → 13.5

Value: **$162.29**

### Bull
2.0 → 3.5 → 5.5 → 7.5 → 10.0 → 12.5 → 15.5 → 18.5 → 22.0 → 26.0

Value: **$352.64**

| Scenario | Value | Current 대비 |
|---|---:|---:|
| Bear | **$45.41** | 약 -77% |
| Base | **$162.29** | 약 -18% |
| Bull | **$352.64** | 약 +79% |

Signals:
- price/Base = **1.2158**
- Bull/current = **1.787**
- Bear/current = **0.230**

Terminal fraction:
- Bear: **73.5%**
- Base: **75.3%**
- Bull: **80.3%**

따라서 DCF는 장기 margin/FCF normalization에 민감하다.

---

## 8. Triage 점수

Provider calibration 후 대략:

- EV: **43.83**
- AS: **64.58**
- DI: **81.67**
- TQ: **20.00**

### DI가 가장 강함

Zero Trust architecture는 기존 perimeter security를 구조적으로 바꾸는 혁신성이 있다. AI agent/security 확장도 인접 가치풀을 늘린다.

### AS가 Moonshot을 막음

Moonshot AS threshold는 72다.

Bull/current 1.79x는 의미 있는 upside지만, Bear/current가 0.23x이므로 downside asymmetry가 크다.

결과적으로 AS가 **64.58**로 threshold를 넘지 못했다.

---

## 9. 왜 Early Exit인가

### Moonshot
- Market cap < $50B: **통과**
- DI ≥78: **통과**
- AS ≥72: **실패**
- SL/FS: 아직 미실행

AS는 raw score에서도 72 미만이므로 SL/FS를 최고점으로 가정해도 Moonshot은 현재 도달할 수 없다.

### Compounder
- price/Base ≤1.2 필요
- 실제 **1.2158**

따라서 가격 gate에서 실패한다.

매우 근소한 차이다.

Base가 $162.29로 유지된다고 가정하면 Compounder valuation gate는 약:

**$162.29 × 1.2 = $194.75**

이하다.

현재 $197.31 대비 약 **1.3% 낮은 가격**이다.

다만 가격이 $194.75 아래가 된다고 자동 Compounder가 되는 것은 아니다. 그때는 MT, RF, MA, FS가 실제 threshold를 통과해야 한다.

### Turnaround
- TQ가 크게 미달
- EV도 Turnaround 요구치 미달

ZS는 정상적으로 성장 중인 기업이지 turnaround 기업이 아니다.

### Expectation Gap
- price/Base ≤0.85 필요
- 현재 1.2158
- EV ≥65도 미달

Base가 그대로라면 price criterion은 약 **$137.95 이하**에서 충족한다.

---

## 10. Hard Veto 상태

최종 상태는 **PENDING_REVIEW**다.

이것은 Hard Veto가 발생했다는 뜻이 아니다.

조기 종료 때문에:
- FS
- RF
- MA
- CP
- MT
- RT

등 veto owner/reviewer가 실행되지 않았기 때문에 review가 끝나지 않은 상태다.

Triage에서 직접 확인된 V7과 V9는:
- V7 unrealistic Bull+: **cleared**
- V9 bankruptcy/permanent impairment: **cleared**

로 판단했다.

---

## 11. 재평가 조건

### 가장 가까운 trigger: 가격

Base $162.29가 유지된다면:
- Compounder price gate: **약 $194.75 이하**
- Expectation Gap price gate: **약 $137.95 이하**

현재 가격은 Compounder gate에서 매우 가깝다.

### 펀더멘털 trigger

가격이 유지되더라도 Base intrinsic value가 약:

**$197.31 / 1.2 ≈ $164.43**

이상으로 올라가면 price/Base gate는 통과한다.

즉 Base valuation이 현재 $162.29에서 약 **1.3%만 상향**돼도 Compounder path가 다시 열린다.

그러나 그 경우에도 핵심은:
- MT ≥76
- RF ≥76
- MA ≥72
- FS ≥72

를 실제로 통과하는가다.

특히 RF는 SBC 때문에 가장 중요한 검증 영역이 될 가능성이 높다.

---

## 12. 핵심 추적 KPI

1. Organic ARR growth ex-acquisition
2. Net new ARR
3. Revenue growth
4. RPO
5. FCF margin
6. OCF
7. SBC / revenue
8. SBC-adjusted owner FCF
9. Diluted share count
10. Capex + internal software / revenue
11. Red Canary cross-sell
12. Z-Flex adoption
13. Non-seat-based solution growth
14. Large deal activity
15. Sales productivity
16. GAAP operating margin
17. Customer retention / NRR
18. AI security / agent security monetization

---

## 13. SWOT

### Strengths
- 선도적인 cloud-native Zero Trust architecture
- 높은 recurring revenue
- $7.4B+ RPO
- 약 20% organic ARR growth
- 순현금
- AI security 신규 TAM
- founder-led leadership

### Weaknesses
- 매우 높은 SBC
- GAAP 적자 지속
- owner FCF가 company FCF보다 크게 낮음
- organic growth 둔화
- Q4 capex/software investment 급증
- acquisition integration risk

### Opportunities
- AI agent security
- Data security
- Agentic SecOps
- Workload/branch expansion
- vendor consolidation
- Red Canary cross-sell

### Threats
- Palo Alto Networks
- Netskope
- Cloudflare
- Microsoft/hyperscaler bundling
- pricing pressure
- growth multiple compression
- dilution

---

## 14. 최종 정리

Zscaler의 이번 판정은 PANW와는 다르다.

PANW는 Base보다 크게 비싼 상태에서 명확하게 valuation gate를 잃었다면, ZS는 **Compounder price gate를 단 1.3% 정도 초과한 경계선**에 있다.

동시에 ZS의 핵심 질적 문제는 valuation보다도:

**$779M의 회사 FCF가 왜 SBC를 반영하면 owner FCF 기준 거의 0이 되는가**

이다.

향후 SBC/revenue 하락과 per-share cash conversion이 확인되면 ZS의 Compounder case는 빠르게 개선될 수 있다.

현재 deterministic harness 상태는:

**EARLY_EXIT_NON_FIT / 0% / Hard Veto PENDING_REVIEW**

이다.

이 상태는 “회사 자체를 피해야 한다”는 완전한 기업평가가 아니라, **현재 frozen price와 triage evidence에서 전체 pipeline을 실행할 만큼 archetype reachability가 없다는 판정**이다.

## Source Notes

Frozen repository evidence:
- runs/ZS/sources/FY2026_10K_key_facts.txt
- runs/ZS/sources/FY2026_Q4_8K_key_facts.txt
- runs/ZS/sources/README.md

Only EV, AS, DI and TQ were executed because the deterministic harness issued an early exit after triage. GPT-5.6 Sol triage reports were authored in-session and validated/aggregated by the repository harness; no separate live OpenAI API adapter call was used.
