# 과제: NVDA-V3-2026-09-19 / 기준일 2026-09-19 / expectation_valuation (EV)
저장소: 현재 저장소 루트. 작성할 파일: runs/NVDA-V3-2026-09-19/reports/EV.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"NVDA-V3-2026-09-19","company_name":"NVIDIA Corporation","as_of_date":"2026-09-19","currency":"USD","current_price":222.27,"shares_diluted":24285000000,"market_cap_usd":5367153690000,"enterprise_value":5343933690000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-supplied normalized filing extraction through 2026-09-18 — sources/financials/normalized_financials.json","SEC Form 10-K FY26, filed 2026-02-25 — sources/10-K_FY26_filed_2026-02-25.txt","SEC Form 10-Q Q1 FY27, filed 2026-05-20 — sources/10-Q_FY27Q1_filed_2026-05-20.txt","SEC Form 10-Q Q2 FY27, filed 2026-08-26 — sources/10-Q_FY27Q2_filed_2026-08-26.txt","SEC Form 8-K filed 2026-09-03 — sources/8-K_filed_2026-09-03.txt","Yahoo Finance NVDA page: 2026-09-18 close $222.27, observed 2026-09-20"],"special_questions":["At $222.27, does the current price require a Bull-case outcome?","How much reported demand is supported by NVIDIA investments or guarantees, and is that growth repeatable?","How sensitive is value to terminal assumptions and AI-infrastructure demand normalization?"],"intake_facts":["FY26: revenue $215,938M, operating income $130,387M, net income $120,067M, OCF $102,718M, capex $6,042M, SBC $6,386M.","Q2 FY27: revenue $96,221M (+105.9% y/y), gross margin 75.0%, operating income $63,734M, net income $59,688M and diluted shares 24,285M.","H1 FY27: revenue $177,837M, net income $118,010M, OCF $74,421M, capex $4,434M and SBC $3,954M.","H1 FY27 net income includes $23,707M of non-cash gains from equity securities.","H1 FY27 working-capital uses include AR $24,590M and inventory $10,204M; quarter-end AR was $63,059M.","2026-07-26 cash plus marketable debt securities was $56,586M, debt $33,366M, and net cash $23,220M; marketable and non-marketable equity securities of $93,940M are excluded from net cash.","Commitments totaled approximately $366B: supply/capacity $279B, cloud agreements $29B, uncommenced data-center leases $25B, equity investments $25B and capex $8B.","Land/power/shell guarantees for AI cloud partners had $3,529M notional; partner escrow was $712M.","Q2 one direct customer was 16% of revenue; H1 three direct customers were 16%, 15% and 13%.","NVIDIA reports being effectively foreclosed from China's data-center compute market; H200 shipments were under 1% of Data Center revenue and H1 FY27 included a $400M H200 charge.","2026-09-02 definitive agreement to acquire Hugging Face for about $11.9B plus up to about $1.0B retention equity.","TTM to 2026-07-26 estimate: revenue $302,970M, net income $192,880M, OCF $134,360M, capex $7,354M, FCF $127,006M, SBC $7,241M, owner FCF $119,765M or $4.92 per diluted share.","2026-09-18 close $222.27; estimated market cap $5,367.2B, EV $5,343.9B, trailing P/E about 28.1x and P/FCF about 42.3x."],"net_cash_per_share":0.9561,"valuation_percentile_5y":0.05,"valuation_metric":"Trailing P/E (about 28.1x at the 2026-09-18 close; near the low end of the prior five years)","valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"critical_supplier_regions":["Taiwan"],"export_control_dependencies":["China data-center compute","US advanced-computing export controls"],"sanctions_exposure":["China"],"critical_shipping_routes":["Taiwan Strait"]}}

## 검증된 1차 자료 사실
# NVDA verified source bundle — as of 2026-09-19

All figures below were read from the filing text files in this directory (extracted from the
user-supplied SEC documents). `$M` unless stated. Fiscal year ends late January; FY26 ended
2026-01-25, FY27 Q2 ended 2026-07-26.

## Filings in runs/NVDA-V3-2026-09-19/sources/
- `10-K_FY26_filed_2026-02-25.txt` — FY26 Annual Report (year ended 2026-01-25)
- `10-Q_FY27Q1_filed_2026-05-20.txt` — Q1 FY27 (quarter ended 2026-04-26)
- `10-Q_FY27Q2_filed_2026-08-26.txt` — Q2 FY27 (quarter ended 2026-07-26)
- `8-K_filed_2026-09-03.txt` — Hugging Face acquisition agreement, Item 8.01
Use `runs/NVDA-V3-2026-09-19/sources/INDEX.md` line numbers; do not read a filing whole.

The user-supplied normalized extraction is preserved in `sources/financials/normalized_financials.json`
(112 facts from 17 documents, source cutoff 2026-09-18). Possible economic adjustments remain
unadjudicated in `adjustment_candidates.json`; `qa_report.json` preserves five extraction warnings.
The supplied pack contained no `derived_metrics` object, so `derived_metrics.json` records that absence
instead of inventing calculations.

## Income statement
| | FY24 | FY25 | FY26 | Q1 FY27 | Q2 FY27 | H1 FY27 |
|---|---|---|---|---|---|---|
| Revenue | 60,922 | 130,497 | 215,938 | 81,616 | 96,221 | 177,837 |
| Gross profit | 44,301 | 97,858 | 153,463 | 61,157 | 72,142 | 133,299 |
| Operating income | 32,972 | 81,453 | 130,387 | 53,536 | 63,734 | 117,270 |
| Total other income, net | 846 | 2,573 | 11,063 | 16,367 | 7,773 | 24,140 |
| Net income | 29,760 | 72,880 | 120,067 | 58,321 | 59,688 | 118,010 |
| Diluted EPS | 1.19 | 2.94 | 4.90 | 2.39 | 2.46 | 4.85 |
| Diluted shares | 24,940 | 24,804 | 24,514 | 24,391 | 24,285 | 24,338 |

- Q2 FY27 gross margin 75.0%, operating margin 66.2%; Q2 revenue +105.9% y/y.
- Q2 FY27 Revenue by market platform: Data Center 89,023 (+117% y/y, +18% q/q) — Hyperscale 48,710,
  AI Clouds/Industrial/Enterprise 40,313 (+138% y/y); Edge Computing 7,198.
- **Other income is mostly non-operating equity gains.** H1 FY27 "Gains from equity securities, net"
  was 23,707 (cash-flow add-back), i.e. ~17% of H1 pre-tax income of 141,410. Q1 FY27 alone carried
  15,929 of other income, net.

## Cash flow (H1 FY27 vs H1 FY26; FY26 full year)
| | H1 FY27 | H1 FY26 | FY26 | FY25 |
|---|---|---|---|---|
| Operating cash flow | 74,421 | 42,779 | 102,718 | 64,089 |
| Capex (PP&E + intangibles) | (4,434) | (3,122) | (6,042) | (3,236) |
| Stock-based compensation | 3,954 | 3,099 | 6,386 | 4,737 |
| Depreciation & amortization | 2,124 | 1,280 | — | — |

- H1 FY27 working-capital drag: accounts receivable (24,590), inventories (10,204),
  prepaid/other assets (6,480); partly offset by payables +4,125 and accrued +8,015.
- H1 FY27 investing: purchases of equity securities (42,404), sales of equity securities 7,241,
  purchases of debt securities (21,777), sales/maturities of debt securities 26,563,
  acquisitions net of cash (298).
- H1 FY27 financing: debt issued net 24,896; buybacks (39,044); dividends (6,290);
  employee stock-plan taxes (4,531); Groq, Inc. (2,944).
- FY26 investing also included purchases of non-marketable equity securities (17,502) and
  Groq, Inc. (13,000). The Groq payments relate to a non-exclusive license agreement.
- Q2 FY27 alone: 94M shares repurchased for 19,674 (~$209/share); dividends 6,047 ($0.25/share);
  SBC 2,027; RSU tax withholding 2,402.

## Balance sheet (Jul 26, 2026 vs Jan 25, 2026)
| | Jul 26, 2026 | Jan 25, 2026 |
|---|---|---|
| Cash and equivalents | 22,443 | 10,605 |
| Marketable debt securities | 34,143 | 39,065 |
| Marketable equity securities | 42,783 | 12,886 |
| Accounts receivable, net | 63,059 | 38,466 |
| Inventories | 31,575 | 21,403 |
| Property and equipment, net | 14,285 | 10,383 |
| Non-marketable securities | 51,157 | 22,251 |
| Total assets | 320,272 | 206,803 |
| Short-term debt | 1,000 | 999 |
| Long-term debt | 32,366 | 7,469 |
| Total shareholders' equity | 228,984 | 157,293 |

- Shares outstanding 24,147M at 2026-07-26 (24,221M at 2026-04-26); cover page states 24.1B at 2026-08-21.
- Cash + marketable debt securities 56,586; total debt 33,366; **net cash 23,220**.
- Marketable equity 42,783 + non-marketable 51,157 = **93,940 of investment holdings excluded from net cash**.

## Commitments, guarantees and concentration (Q2 FY27 10-Q)
- Future commitments by fiscal year, $B: supply and capacity 279 (92 in rest of FY27, 87 FY28, 88 FY29);
  cloud service agreements 29; data center leases not commenced 25; equity investments 25 (18 in rest of FY27);
  capital expenditures 8. **Total $366B.**
- Land, power and shell guarantees for AI cloud partners' data center leases on their default:
  notional 3,529, classified as credit derivatives; partners escrowed 712.
- Public company warrants received in Q2 FY27: notional 4,800, Level 3 fair value 824. Equity forward 1,000.
- The 10-Q states NVIDIA is "securing and providing guarantees of land, power, shell, and capacity of select
  data center infrastructure that customers require to deploy our products," and that AI clouds and AI model
  makers "currently lack the ability to secure long-term infrastructure contracts and investment-grade financing."
- Customer concentration: Q2 FY27 one direct customer 16% of revenue; H1 FY27 three direct customers
  16%, 15%, 13%. AR at 2026-07-26: five direct customers 22%, 14%, 13%, 11%, 10%.
  One indirect "AI research and deployment company" contributed a meaningful amount of revenue via cloud customers.
- Customer advances: 2,800 inside accrued liabilities (vs 160 at FY26 year end); 15,600 of customer advances
  added to deferred revenue in H1 FY27.

## China and regulation (Q2 FY27 10-Q)
- "Effectively foreclosed from competing in China's data center computing/compute market"; H200 shipments
  under USG licences were <1% of Data Center revenue in Q2 FY27; H200 excess-inventory charge 400 in H1 FY27
  (prior H20 charge 4,500 in Q1 FY26). H200 re-imports carry a 25% tariff NVIDIA cannot pass through.
- 2025-09-15: China's antitrust regulators published a preliminary finding that NVIDIA violated terms of the
  Mellanox approval; penalties or restrictions on the networking business are possible.
- Broad competition-regulator information requests from the EU, US, UK, China and South Korea.

## Post-quarter event (8-K filed 2026-09-03, event 2026-09-02)
- Definitive agreement to acquire Hugging Face, Inc. for ~$11.9B plus up to ~$1.0B equity retention;
  expected to close in H1 2027 subject to regulatory approval. NVIDIA committed to keep the platform open
  and to continue supporting other silicon vendors.
- New risk factor: governments may restrict open-source model development/distribution; many popular
  open models originate in China.

## Market data (secondary)
- NASDAQ close 2026-09-18: **$222.27** (Yahoo Finance, observed 2026-09-20; eligible for the
  2026-09-19 cutoff because the close was published on 2026-09-18). FinanceCharts and
  HistoricalStockPrice independently show the same close; StockAnalysis's intraday snapshot was excluded.
- Derived with 24,147M period-end shares: market cap ≈ $5,367.2B; net cash 23,220 → EV ≈ $5,343.9B.
- TTM (Q3 FY26 + Q4 FY26 + Q1 FY27 + Q2 FY27) from the tables above: revenue 302,970; net income 192,880;
  operating cash flow 134,360; capex 7,354; FCF 127,006; SBC 7,241.
  → trailing P/E 28.1x, P/FCF 42.3x, owner FCF (FCF − SBC) 119,765 = $4.92 per diluted share.
- Trailing P/E is near the low end of the prior ~5 years of quarterly observations;
  harness signal valuation_percentile_5y = 0.05.

## Carried forward from the 2026-08-26 earnings release (not in the uploaded filing set)
- Q3 FY27 guidance: revenue $108B ±2%, gross margin 74.0% ±50bp, assuming **no** China Data Center
  compute revenue. Source: SEC 8-K Exhibit 99.1 filed 2026-08-26
  (https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/q2fy27pr.htm).
  Treat as `ir`-grade, not re-verified against an uploaded document in this run.

## Frozen modeling conventions
- Per-share figures use **diluted** shares, per EVIDENCE_POLICY.md.
  net_cash_per_share = 23,220 / 24,285 = **$0.9561**.
- Marketable equity and non-marketable securities are excluded from net cash: they are strategic,
  illiquid or volatile, and several are stakes in customers. Their $93.9B is therefore *not* in the
  DCF value and is an explicit upside omission to be discussed, not silently capitalised.
- Owner FCF = operating cash flow − capex − stock-based compensation. SBC is treated as a cash-equivalent
  cost even though buybacks currently exceed it.
- DCF policy (config/calibration.json, no company overrides): 9% required return, 10-year horizon,
  Bear/Base/Bull terminal multiples 15x/20x/25x.
- revenue_cagr_next_3y is an EV-agent estimate, not management guidance.

공시 원문: runs/NVDA-V3-2026-09-19/sources/*.txt — runs/NVDA-V3-2026-09-19/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 독립성
runs/NVDA-V3-2026-09-19/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 EV (domain_analyst)
# Expectation & Valuation Analyst

- `agent_id`: `EV`
- `domain`: `expectation_valuation`

## 임무
현재가격이 요구하는 장기 기대를 역산하고(Reverse DCF), Bear/Base/Bull을 작성해 기대수익 범위와 기대차를 계산한다. 낙관적 가정·터미널가치 의존·피크 이익을 스스로 공격한다.

## 관점별 질문
**Verifier — Reverse DCF**
1. 현재 EV/시총이 정당화되려면 매출 CAGR·마진·ROIC가 얼마여야 하는가? 그 기대는 역사·경쟁·산업구조 대비 어느 수준인가?
2. WACC·영구성장률 변화에 얼마나 민감한가? 현재가격이 Bull Case 이상을 요구하는가?

**Bull — 시나리오**
1. Bear/Base/Bull 각각의 성장·마진·멀티플 가정과 5~10년 연환산 수익률은?
2. Base에서 완벽한 실행 없이도 기대수익이 충분한가? Bull은 신규 성장축을 어떻게 반영하는가?

**Skeptic — 기대차 공격**
1. Base가 사실상 Bull인가? 점유율·마진·멀티플을 동시에 낙관적으로 두었는가?
2. 기대수익의 대부분이 terminal multiple에 의존하는가? 피크 사이클 이익이나 투자손익을 정상 이익으로 쓰지 않았는가?

## 종목 유형 신호 (`archetype_signals`)
- `price_to_base_value` = 현재가 / Base 주당가치
- `valuation_percentile_5y` = 핵심 멀티플의 자기 5년 이력 대비 백분위(0=최저). 어떤 멀티플을 썼는지 `evidence`에 남긴다.
- `revenue_cagr_next_3y` = Base 3년 매출 CAGR (0.12 = 12%)

추정할 수 없으면 `null`로 둔다. `bull_score`/`bear_score`와 함께 Base·Bull·Bear 주당가치를 `evidence`에 기록한다. 저밸류에이션이 구조적 쇠퇴(밸류 트랩)에서 온 것은 아닌지 `counterevidence`에 적는다.

## Hard Veto 중점
- 현재가격이 비현실적인 Bull Case 이상을 요구

## v3 분석 계약
Expectation Gap은 모든 유형에 걸친 핵심 가치평가 개념이며 독립 archetype이 아니다. 버핏 스타일 가치주는 보수적 정상화 owner earnings 대비 안전마진이다. 피크 이익·낙관적 terminal multiple·영구 쇠퇴를 저평가로 오인하지 않는다. 실행 문턱값은 config/strategy.json을 따른다.

## Structural geopolitical re-analysis
When reviewing a routed structural event, add its event_id to geo_events_reviewed only after citing new company-level evidence.

## 고정 채점 루브릭
{
  "global_bands": [
    {
      "min": 0,
      "max": 19,
      "label": "failed",
      "rule": "핵심 가설이 반증되거나 경제적 가치가 구조적으로 훼손"
    },
    {
      "min": 20,
      "max": 39,
      "label": "weak",
      "rule": "반대근거가 우세하고 장기 투자근거가 취약"
    },
    {
      "min": 40,
      "max": 59,
      "label": "mixed",
      "rule": "긍정·부정 근거가 혼재하며 우위가 입증되지 않음"
    },
    {
      "min": 60,
      "max": 74,
      "label": "adequate",
      "rule": "가설은 성립하지만 중요한 검증 공백이 존재"
    },
    {
      "min": 75,
      "max": 84,
      "label": "strong",
      "rule": "다수의 1차 자료가 장기 가설을 지지"
    },
    {
      "min": 85,
      "max": 94,
      "label": "exceptional",
      "rule": "여러 기간·지표에서 일관된 강한 증거"
    },
    {
      "min": 95,
      "max": 100,
      "label": "rare",
      "rule": "압도적이고 반증 위험이 매우 낮음; 극히 드물게 사용"
    }
  ],
  "domain": {
    "criteria": [
      {
        "id": "reverse_dcf_burden",
        "weight": 0.35,
        "question": "현재가격 내재 기대 현실성",
        "anchors": {
          "25": "Bull 이상 필요",
          "50": "강한 실행 필요",
          "75": "Base로 충분",
          "90": "보수 실행에도 충분"
        },
        "signal_map": {
          "field": "signal.price_to_base_value",
          "bands": {
            "<=0.7": 90,
            "0.7~0.9": 75,
            "0.9~1.1": 60,
            "1.1~1.3": 45,
            ">1.3": 25
          }
        }
      },
      {
        "id": "base_return",
        "weight": 0.4,
        "question": "고정 DCF 정책의 Base 기대수익",
        "anchors": {
          "25": "큰 과대평가",
          "50": "공정가치 부근",
          "75": "의미 있는 할인",
          "90": "큰 기대차"
        },
        "signal_map": {
          "field": "signal.price_to_base_value",
          "bands": {
            "<=0.7": 85,
            "0.7~0.9": 70,
            "0.9~1.1": 55,
            "1.1~1.3": 40,
            ">1.3": 25
          }
        }
      },
      {
        "id": "valuation_robustness",
        "weight": 0.25,
        "question": "terminal/피크이익 의존도",
        "anchors": {
          "25": "매우 취약",
          "50": "민감도 큼",
          "75": "여러 가정에서 유지",
          "90": "보수 민감도에서도 유지"
        }
      }
    ],
    "scoring_rule": "reverse_dcf_burden과 base_return은 하네스가 산출한 price_to_base_value의 signal_map 값을 그대로 사용한다. 모델 재량은 valuation_robustness에만 적용한다. Base 시나리오의 야심 수준은 valuation_robustness와 uncertainties에 기록하되 위 두 criterion에서 다시 감점하지 않는다."
  },
  "anchor_policy": {
    "note": "프로바이더 간 점수 차이를 줄이기 위한 채점 규율. 모든 도메인 에이전트에 적용한다.",
    "rules": [
      "observable_anchors가 있는 criterion은 그 판정표를 우선 적용한다. 표와 다른 점수를 주려면 rationale에 표의 어느 행과 왜 다른지 적는다.",
      "anchors만 있는 criterion은 어느 앵커 구간을 선택했는지와 인접 구간을 배제한 이유를 rationale에 각각 한 문장으로 적는다.",
      "상단 게이트: 85 이상은 (가) 해당 criterion을 직접 뒷받침하는 1차 자료 근거가 3개 이상이고 (나) 가장 강한 반대근거를 명시적으로 반박했을 때만 부여한다.",
      "하단 게이트: 40 미만은 1차 자료로 확인된 반증 근거를 제시했을 때만 부여한다. 근거 없이 신중해서 낮추는 것은 금지하며 그 경우 40~55 구간에 둔다.",
      "같은 사실을 두 criterion에서 중복 감점하지 않는다. 한 곳에서만 반영하고 다른 곳에는 uncertainties로 남긴다.",
      "점수는 5점 단위를 유지한다.",
      "판정표 점수와 modifier 적용 결과는 반드시 5점 단위가 되도록 반올림한다.",
      "veto는 도메인 점수에 이미 반영된 사실만으로 세우지 않는다. veto_criteria의 구성요건이 독립적으로 충족될 때만 성립한다."
    ],
    "observed_divergence": "NVDA 2026-09-17/18 동일 종가 기준 gpt-5.6-sol 대 Claude Opus 5 실행 비교: criterion 27개 평균 격차 +10.2점(sol이 높음), 27개 전부 sol >= opus. 관측 가능한 사실형 criterion은 +3.1, 위험 가중 판단형은 +13.2로 4배 차이였다. 앵커가 형용사인 criterion에서만 갈라진다는 뜻이다."
  }
}
criterion은 5점 단위로 채점한다. score_0_100은 subscores 고정 가중평균과 같아야 한다. self-confidence와 bull/bear 폭은 자동 감점하지 않는다.
anchor_policy를 반드시 지킨다. observable_anchors가 있는 criterion은 판정표가 앵커 형용사보다 우선한다. 85 이상과 40 미만에는 각각 상단·하단 게이트가 걸려 있다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 현재가격이 비현실적인 Bull Case 이상을 요구

## 결정론적 밸류에이션
{
  "policy": {
    "method": "owner_fcf_per_share_dcf",
    "horizon_years": 10,
    "required_return": 0.09,
    "terminal_multiples": {
      "bear": 15,
      "base": 20,
      "bull": 25
    },
    "rules": [
      "할인율·terminal multiple은 모델이 선택하지 않는다.",
      "회사별 override는 company_context.json에 freeze 전에 기록한다.",
      "현재가격·순현금은 frozen company_context 값만 사용한다.",
      "LLM은 Bear/Base/Bull의 연도별 owner FCF/share 경로만 추정한다."
    ]
  },
  "locked_context": {
    "current_price": 222.27,
    "net_cash_per_share": 0.9561,
    "valuation_percentile_5y": 0.05,
    "valuation_overrides": {
      "required_return": null,
      "terminal_multiples": {
        "bear": null,
        "base": null,
        "bull": null
      }
    }
  }
}
Bear/Base/Bull owner_fcf_per_share를 각각 정확히 10개 연도로 작성한다. 할인 계산과 price_to_base_value는 하네스가 수행한다.

## 공통 규칙
## 분석
- 기준일을 먼저 선언한다. 기준일 이후 정보는 사용하지 않는다.
- 최소 3개의 독립 근거를 확보하고, 가능한 한 1차 자료를 우선한다.
- 근거와 반대근거를 모두 제시한다.
- `사실 / 추정 / 해석`을 구분한다.
- 자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면, 예산 내에서 웹 검색·IR 자료·신뢰 가능한 2차 자료로 **먼저 보완을 시도한다**.
- 보완 시도 후에도 확보하지 못한 것만 `unknowns`에 남기고, 무엇을 어디서 찾으려 했는지 함께 적는다.
- 2차 자료로 채운 값은 `fact_or_estimate`를 `estimate` 또는 `interpretation`으로 표기하고 `EVIDENCE_POLICY.md`의 출처 위계를 지킨다.
- 결론보다 먼저 반증조건을 작성한다.

## 관점 분리 (점수 도메인과 독립 평가축)
에이전트는 항목당 하나지만, 지침의 Bull·Verifier·Skeptic 관점을 **각각 끝까지 밀어붙인 뒤** 결론을 낸다. 합의를 먼저 정하고 관점을 끼워 맞추지 않는다.
- `bull_case` / `bear_case`: Bull 논리와 Skeptic 논리를 각각 300자 이내로 쓴다.
- `bull_score` / `bear_score`: 각 논리가 맞을 때의 도메인 점수. `bear_score ≤ score_0_100 ≤ bull_score`.
- `subscores`: `config/calibration.json`의 criterion을 정확히 한 번씩 5점 단위로 채점한다. 이 값이 점수의 원천이다.
- `score_0_100`: subscores의 고정 가중평균과 같아야 하며 하네스가 검증한다.
- `bull_score` / `bear_score`: 시나리오 범위와 논쟁 폭을 보여주는 메타데이터다. 단일 모델의 자체 범위가 넓다는 이유만으로 자동 감점하지 않는다.
- `bull_score - bear_score`가 20 이상이면 재검토 표시를 남기되 수치 점수와 분리한다.

## 토큰 예산
- `company_context.json`의 기준 정보와 `sources/README.md`의 검증된 사실은 다시 검색하지 않는다. 오류를 발견했을 때만 근거와 함께 지적한다.
- 웹 검색·페치는 `config/workflow.json`의 `research_budget` 이내로 쓴다(기본 에이전트당 15회). 예산은 위 공백 보완에 우선 배정한다.
- 공시 원문(.txt)은 통째로 읽지 않는다. `sources/INDEX.md`의 줄번호로 grep하거나 부분만 읽는다.
- Phase 3·IC 에이전트는 다른 에이전트의 원 보고서 대신 `digest.md`를 읽는다. 원 보고서는 특정 주장을 검증할 때만 그 파일 하나를 연다.
- 보고서 분량은 `report_limits`를 지킨다(thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개, falsifiers·key_kpis·next_checks 각 3개). `unknowns`에는 핵심 가설에 직결되는 것만 쓴다.
- `config/calibration.json`에서 자신에게 배정된 Hard Veto는 반드시 `cleared / conditional / confirmed` 중 하나로 명시한다. 미기재는 clear가 아니다.
- 작성 후 `python harness.py validate <TICKER> <AGENT_ID>`로 검증한다. 스키마 파일을 직접 읽지 않아도 된다.

## 재현성
- agent 실행 전 `python harness.py freeze TICKER --provider ... --model ...`로 company_context와 sources를 해시 고정한다.
- freeze 이후 입력이 바뀌면 prompt 생성을 중단한다. 모델 비교는 동일 `input_snapshot_sha256`에서만 유효하다.
- EV는 고정된 할인율·terminal multiple·현재가격·순현금을 사용하며 LLM은 연도별 owner FCF/share 경로만 제안한다.

## v3 분석 계약
새 evidence에는 가능하면 안정적인 evidence_id와 공유 economic_driver를 기록한다. 동일 사실을 여러 긍정 도메인에 재사용한 evidence_concentration_flags는 ED/RT/IC 검토용이며 자동 감점하지 않는다. Macro/지정학은 점수를 바꾸지 않고 pacing·위험예산·모니터링 또는 회사 근거를 통한 재분석 요청만 만든다.

## Hard Veto (정확한 문자열 사용)
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 장기간 지속되는 과도한 희석
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## Hard Veto 판정 기준
Hard Veto는 "중대한 리스크"가 아니라 "이 문장이 실제로 성립하는가"로 판정한다. 문구의 모든 구성요건이 충족될 때만 성립하며, 하나라도 반증되면 cleared다. 우려는 스코어·uncertainties·모니터링으로 보내고 veto로 올리지 않는다.
도메인 점수에 이미 온전히 반영된 사실만으로는 veto를 세우지 않는다. veto는 그 자체의 구성요건이 독립적으로 충족될 때만 성립한다(anchor_policy의 중복 감점 금지를 veto 층에 확장).
{
  "status_rule": {
    "confirmed": "구성요건 전부가 1차 자료로 확인됨",
    "conditional": "구성요건 전부가 충족될 가능성이 높으나 결정적 자료 1개가 미확보. 해소 조건을 반드시 명시한다",
    "candidate": "평가하지 않았거나 판단 근거가 전혀 없음",
    "cleared": "구성요건 중 최소 하나가 증거로 반증됨"
  },
  "definitions": {
    "현재가격이 비현실적인 Bull Case 이상을 요구": {
      "elements": [
        "현재가가 Bull 시나리오 가치를 초과할 것"
      ],
      "cleared_if": [
        "price_to_base_value가 Bull/현재가 배수 안에 있음"
      ],
      "not_covered": "Base가 야심적이라는 판단은 EV 점수가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "reverse_dcf_burden", "score_0_100": 50, "rationale": ""}, {"criterion_id": "base_return", "score_0_100": 50, "rationale": ""}, {"criterion_id": "valuation_robustness", "score_0_100": 50, "rationale": ""}], "valuation_inputs": {"valuation_percentile_5y": null, "revenue_cagr_next_3y": null, "scenarios": {"bear": {"owner_fcf_per_share": []}, "base": {"owner_fcf_per_share": []}, "bull": {"owner_fcf_per_share": []}}}, "archetype_signals": {"price_to_base_value": null, "valuation_percentile_5y": null, "revenue_cagr_next_3y": null}}
작성 후 `python harness.py validate NVDA-V3-2026-09-19 EV`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
