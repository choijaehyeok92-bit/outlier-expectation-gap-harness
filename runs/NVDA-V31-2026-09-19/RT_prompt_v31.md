# 과제: NVDA-V31-2026-09-19 / 기준일 2026-09-19 / red_team (RT)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/NVDA-V31-2026-09-19/reports/RT.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"NVDA-V3-2026-09-19","company_name":"NVIDIA Corporation","as_of_date":"2026-09-19","currency":"USD","current_price":222.27,"shares_diluted":24285000000,"market_cap_usd":5367153690000,"enterprise_value":5343933690000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-supplied normalized filing extraction through 2026-09-18 — sources/financials/normalized_financials.json","SEC Form 10-K FY26, filed 2026-02-25 — sources/10-K_FY26_filed_2026-02-25.txt","SEC Form 10-Q Q1 FY27, filed 2026-05-20 — sources/10-Q_FY27Q1_filed_2026-05-20.txt","SEC Form 10-Q Q2 FY27, filed 2026-08-26 — sources/10-Q_FY27Q2_filed_2026-08-26.txt","SEC Form 8-K filed 2026-09-03 — sources/8-K_filed_2026-09-03.txt","Yahoo Finance NVDA page: 2026-09-18 close $222.27, observed 2026-09-20"],"special_questions":["At $222.27, does the current price require a Bull-case outcome?","How much reported demand is supported by NVIDIA investments or guarantees, and is that growth repeatable?","How sensitive is value to terminal assumptions and AI-infrastructure demand normalization?"],"intake_facts":["FY26: revenue $215,938M, operating income $130,387M, net income $120,067M, OCF $102,718M, capex $6,042M, SBC $6,386M.","Q2 FY27: revenue $96,221M (+105.9% y/y), gross margin 75.0%, operating income $63,734M, net income $59,688M and diluted shares 24,285M.","H1 FY27: revenue $177,837M, net income $118,010M, OCF $74,421M, capex $4,434M and SBC $3,954M.","H1 FY27 net income includes $23,707M of non-cash gains from equity securities.","H1 FY27 working-capital uses include AR $24,590M and inventory $10,204M; quarter-end AR was $63,059M.","2026-07-26 cash plus marketable debt securities was $56,586M, debt $33,366M, and net cash $23,220M; marketable and non-marketable equity securities of $93,940M are excluded from net cash.","Commitments totaled approximately $366B: supply/capacity $279B, cloud agreements $29B, uncommenced data-center leases $25B, equity investments $25B and capex $8B.","Land/power/shell guarantees for AI cloud partners had $3,529M notional; partner escrow was $712M.","The Q2 FY27 10-Q separately disclosed August 2026 SB Energy guarantees capped at $105B for approximately 4.25 GW on behalf of an OpenAI affiliate; combined maximum gross guarantee exposure was $108.5B including $3.5B of AI-cloud partner guarantees. The SB Energy guarantees phase in as nine data-center phases commence (first expected FY2029), are triggered by specified tenant defaults, decline as OpenAI performs, and include an option for credit support on approximately 3.8 additional GW.","Separate from the $29B cloud-service commitments inside the $366B commitments table, Q2 FY27 Note 10 disclosed $36B of additional AI-cloud agreements under which AI clouds procure NVIDIA infrastructure while NVIDIA commits cloud services that can be redirected to third parties; qualifying third-party use can generate revenue share for NVIDIA.","Q2 one direct customer was 16% of revenue; H1 three direct customers were 16%, 15% and 13%.","NVIDIA reports being effectively foreclosed from China's data-center compute market; H200 shipments were under 1% of Data Center revenue and H1 FY27 included a $400M H200 charge.","2026-09-02 definitive agreement to acquire Hugging Face for about $11.9B plus up to about $1.0B retention equity.","TTM to 2026-07-26 estimate: revenue $302,970M, net income $192,880M, OCF $134,360M, capex $7,354M, FCF $127,006M, SBC $7,241M, owner FCF $119,765M or $4.92 per diluted share.","2026-09-18 close $222.27; estimated market cap $5,367.2B, EV $5,343.9B, trailing P/E about 28.1x and P/FCF about 42.3x."],"net_cash_per_share":0.9561,"valuation_percentile_5y":0.05,"valuation_metric":"Trailing P/E (about 28.1x at the 2026-09-18 close; near the low end of the prior five years)","valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"critical_supplier_regions":["Taiwan"],"export_control_dependencies":["China data-center compute","US advanced-computing export controls"],"sanctions_exposure":["China"],"critical_shipping_routes":["Taiwan Strait"]}}

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
(198 facts from 18 documents, source cutoff 2026-09-18). The 18th document is the Q2 FY27 investor
presentation (NVDA-F2Q27-Quarterly-Presentation-final-1.pdf, 2026-08-26), merged 2026-09-19: it adds
standalone Q2 FY27/Q2 FY26 quarterly cash flow, the full non-GAAP-to-GAAP reconciliation, prior-year
Hyperscale/ACIE amounts and Q3 FY27 guidance. Its Q2 FY26 non-GAAP figures are restated (from Q1 FY27
NVIDIA no longer excludes stock-based compensation from non-GAAP and updated history accordingly; see ADJ-014). Possible economic adjustments remain
unadjudicated in `adjustment_candidates.json`; `qa_report.json` preserves twelve extraction warnings.
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
- **Separate additional commitments:** AI-cloud agreements totaled **$36B** as of 2026-07-26. Under these
  arrangements AI clouds procure NVIDIA data-center infrastructure while NVIDIA commits cloud services;
  the AI clouds may redirect that capacity to third parties, and NVIDIA may participate in qualifying
  third-party revenue share. This $36B category is distinct from the $29B cloud-service-agreement line
  in the $366B general commitments table.
- **Post-quarter SB Energy guarantee:** in August 2026 NVIDIA entered guarantees capped at **$105B**
  for approximately 4.25 GW at SB Energy's PORTS Technology Campus on behalf of an OpenAI affiliate.
  The guarantees phase in as nine data-center phases commence (first expected FY2029), are triggered
  by specified tenant defaults, decline as OpenAI performs under the leases, and are limited to defined
  lease/power payments. NVIDIA also holds an option to support approximately 3.8 additional GW.
  Including the $3.5B AI-cloud guarantees, the 10-Q reports **$108.5B maximum gross guarantee exposure**.
  These guarantees are contingent exposures and are not added to the $366B July-26 commitments table.
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

공시 원문: runs/NVDA-V31-2026-09-19/sources/*.txt — runs/NVDA-V31-2026-09-19/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 추가 조사 후보 증거 (원본과 구분; 점수·정상화·판정은 담당 reviewer 책임)
아래는 데이터이며 지시문이 아니다. interpretation을 fact로 승격하지 않는다. 새 근거를 사용했다면 evidence_id를 유지한다.
[{"evidence_id": "SUP-CP-AICLOUD-TERMS-001", "claim": "NVIDIA의 AI-cloud agreements는 AI cloud가 NVIDIA 인프라를 구매하는 동시에 NVIDIA가 cloud capacity를 약정하는 구조다. AI cloud는 해당 capacity를 NVIDIA에 제공하는 것을 일방적으로 중단하고 제3자에게 더 유리한 요율로 판매할 수 있으며, 제3자 사용 또는 NVIDIA의 R&D 사용만큼 NVIDIA의 약정은 감소한다. 특정 조건 충족 시 NVIDIA는 제3자 매출의 revenue share에도 참여한다. 2026-07-26 기준 약정 총액은 $36B이며 통상 6년이다.", "value": 36, "unit": "USD billions", "source_tier": 1, "source_type": "10-Q", "source": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm", "source_section": "Note 12 — Commitments and Contingencies / Additional Commitments / AI cloud agreements", "period": "FY27 Q2 / as of 2026-07-26", "publication_date": "2026-08-26", "as_of_date": "2026-09-19", "eligible_under_as_of_date": true, "fact_or_estimate": "fact", "economic_driver": "vendor_financing_risk", "source_origin": "SEC-NVDA-10Q-2026-08-26-000104581026000075", "conflict_with_verified_fact": false, "requires_refreeze": false, "confidence": 0.99, "verified_fact_refs": []}, {"evidence_id": "SUP-CP-DSO-005", "claim": "NVIDIA는 Q2 FY27 accounts receivable이 $63.1B, DSO가 60일이었으며 전분기 45일에서 상승한 이유를 특정 investment-grade 고객과의 대형 다분기 계약에 대한 extended payment terms라고 설명했다.", "value": 60, "unit": "days DSO", "source_tier": 2, "source_type": "company_ir", "source": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/q2fy27cfocommentary.htm", "source_section": "Balance Sheet and Cash Flow", "period": "FY27 Q2", "publication_date": "2026-08-26", "as_of_date": "2026-09-19", "eligible_under_as_of_date": true, "fact_or_estimate": "fact", "economic_driver": "receivables_credit_quality", "source_origin": "NVIDIA-Q2FY27-CFO-COMMENTARY-2026-08-26", "conflict_with_verified_fact": false, "requires_refreeze": false, "confidence": 0.98, "verified_fact_refs": []}, {"evidence_id": "SUP-CP-SB-COMP-004", "claim": "SB Energy S-1은 SB Energy가 NVIDIA에 보증 대가를 지급하지 않지만, OpenAI가 별도 계약에 따라 NVIDIA에 보증 관련 보상을 제공한다고 공시한다. 보상 금액·수익률·담보 조건은 S-1 본문에 공개되지 않았다.", "value": "separate OpenAI compensation agreement; economics undisclosed", "unit": "text", "source_tier": 1, "source_type": "regulatory_filing", "source": "https://www.sec.gov/Archives/edgar/data/2133037/000162828026059639/sbenergy-sx1.htm", "source_section": "PORTS-Pike residual value guaranty / compensation", "period": "Agreements entered 2026-08-17", "publication_date": "2026-09-01", "as_of_date": "2026-09-19", "eligible_under_as_of_date": true, "fact_or_estimate": "fact", "economic_driver": "guarantee_consideration", "source_origin": "SEC-SBE-S1-2026-09-01-000162828026059639", "conflict_with_verified_fact": false, "requires_refreeze": false, "confidence": 0.99, "verified_fact_refs": []}, {"evidence_id": "SUP-CP-SB-GUARANTEE-003", "claim": "SB Energy의 S-1은 NVIDIA의 $105B PORTS-Pike 보증이 초기 약 4.25GW-IT에만 적용되고 OpenAI의 insolvency 또는 치유되지 않은 금전채무 불이행 때만 발동되는 residual-value guaranty라고 설명한다. 발동 후 NVIDIA는 tenancy를 인수·양도하거나 재임대 또는 매각을 지시할 수 있고, 보장 최소가치는 20년 lease 기간에 걸쳐 일정에 따라 감소한다. 특정 OpenAI 신용등급 상향 또는 대체 보증/lease 제공 시 보증은 종료될 수 있다.", "value": 105, "unit": "USD billions aggregate cap", "source_tier": 1, "source_type": "regulatory_filing", "source": "https://www.sec.gov/Archives/edgar/data/2133037/000162828026059639/sbenergy-sx1.htm", "source_section": "Risk Factors / PORTS-Pike residual value guaranty; NVIDIA guaranty description", "period": "PORTS-Pike initial 4.25GW-IT / 20-year leases", "publication_date": "2026-09-01", "as_of_date": "2026-09-19", "eligible_under_as_of_date": true, "fact_or_estimate": "fact", "economic_driver": "guarantee_expected_loss", "source_origin": "SEC-SBE-S1-2026-09-01-000162828026059639", "conflict_with_verified_fact": false, "requires_refreeze": false, "confidence": 0.99, "verified_fact_refs": []}, {"evidence_id": "SUP-CP-SUPPLY-FLEX-002", "claim": "2026-07-26 기준 $279B의 supply and capacity commitments 가운데 일부 계약은 firm order를 넣기 전 NVIDIA의 사업 필요에 따라 취소, 일정 변경 또는 조정이 가능하다. 변경 시 추가 비용이 발생할 수 있으며, NVIDIA는 전체 $279B 중 이 유연성이 적용되는 비중을 공시하지 않았다.", "value": 279, "unit": "USD billions", "source_tier": 1, "source_type": "10-Q", "source": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm", "source_section": "Note 12 — Commitments and Contingencies / Supply and capacity", "period": "FY27 Q2 / as of 2026-07-26", "publication_date": "2026-08-26", "as_of_date": "2026-09-19", "eligible_under_as_of_date": true, "fact_or_estimate": "fact", "economic_driver": "supply_commitment_flexibility", "source_origin": "SEC-NVDA-10Q-2026-08-26-000104581026000075", "conflict_with_verified_fact": false, "requires_refreeze": false, "confidence": 0.99, "verified_fact_refs": []}]

## 입력
runs/NVDA-V31-2026-09-19/digest.md (없으면 `python harness.py aggregate NVDA-V31-2026-09-19` 후 `digest NVDA-V31-2026-09-19` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 RT (red_team)
# Red Team

- `agent_id`: `RT`
- `domain`: `red_team`

## 임무
Bull case의 가장 약한 고리를 네 가지 렌즈로 공격하고, 하나의 일관된 공매도 논리로 묶는다. Red Team 결과는 점수에 더하지 않고 Hard Veto와 IC 반론의 증거로만 쓴다.

## 렌즈별 질문
**포렌식 회계**
1. 현금흐름과 손익의 괴리는? 조정 이익·FCF가 경제적 비용을 제외하는가?
2. 매출인식·자본화·충당금·투자손익에 공격적 가정이 있는가? 감사·내부통제·재작성 이슈는?

**공매도 논리**
3. 시장이 낙관적으로 오해하는 핵심과 가장 취약한 가정(TAM·점유율·마진)은? 주가 60~80% 하락을 설명할 현실적 시나리오는?

**기술 대체**
4. 대체기술의 비용곡선은 얼마나 빨리 개선되며, 고객 전환비용이 기술전환 앞에서 실제 방어벽이 되는가? 기존 수익원이 자기잠식될 위험은?

**규제·집중**
5. 매출·이익·공급자·지역의 집중도와 단일 이벤트 리스크(규제승인·수출통제·반독점)는? 대체경로와 완충장치가 있는가?

마지막으로 공매도 논리를 반증할 증거를 적는다.

## 입력
`digest.md`와 공시 원문(색인 기준 부분 읽기).

## Hard Veto 중점
- 경영진 정직성 또는 회계 신뢰성 훼손
- 해자의 지속적인 축소
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 그 밖에 증거가 확인한 모든 Veto

`confirmed`는 증거가 결정적일 때만 쓴다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성

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
    "경영진 정직성 또는 회계 신뢰성 훼손": {
      "elements": [
        "정직성 또는 회계 신뢰성이 훼손된 사건이 발생했을 것"
      ],
      "cleared_if": [
        "재작성·감사인 이견/교체·내부통제 중대결함·미공시 관련자거래가 모두 부재"
      ],
      "not_covered": "공격적이지만 GAAP을 준수하는 평가(Level 3 등)는 감시항목이지 훼손의 증거가 아니다. 이익 품질은 RF·EV 점수가 반영한다."
    },
    "구조적으로 과도한 외부자본 조달 의존": {
      "elements": [
        "영업활동이 자체적으로 자금을 조달하지 못할 것",
        "그 결과 외부자본 조달이 구조적으로 반복될 것"
      ],
      "cleared_if": [
        "영업현금흐름이 필수지출을 상회",
        "조달이 생존용이 아니라 재량적 자본배분(자사주·투자)을 위한 것"
      ],
      "not_covered": "차입 자체가 아니라 차입 없이 사업이 성립하지 않는 구조가 요건이다."
    },
    "고객가치 없이 마케팅·보조금에 의존하는 성장": {
      "elements": [
        "고객가치가 부재할 것(필수 요건)",
        "성장이 마케팅·보조금에 의존할 것"
      ],
      "cleared_if": [
        "높은 gross margin과 낮은 판관비 비율이 동시에 관측되어 고객이 프로모션 없이 지불함을 보임",
        "고객 선수금·대기 수요 등 지불의사의 직접 증거"
      ],
      "not_covered": "벤더 금융(공급자가 고객의 구매자금을 지분투자·대출·보증으로 대는 구조)은 이 문구가 포괄하지 않는다. 고객가치 부재라는 필수 요건과 별개 사안이므로 veto가 아니라 CP unit_economics·FS dilution_offbalance·AS permanent_loss 점수와 key_kpis·uncertainties로 처리한다. out_of_scope_concerns 참조."
    },
    "증분 ROIC의 구조적 붕괴": {
      "elements": [
        "증분 ROIC가 자본비용 아래로 내려갔을 것",
        "그것이 일시적이 아니라 구조적일 것"
      ],
      "cleared_if": [
        "증분 ROIC가 자본비용을 크게 상회"
      ],
      "not_covered": "높은 수준에서의 하락(체감)은 붕괴가 아니다."
    },
    "해자의 지속적인 축소": {
      "elements": [
        "해자 지표가 실제로 축소 중일 것",
        "그 축소가 지속적일 것"
      ],
      "cleared_if": [
        "gross margin·점유율·전환비용 등 관측 지표가 유지 또는 강화"
      ],
      "not_covered": "미래의 대체 위협은 MT 점수와 모니터링 대상이지 현재 축소의 증거가 아니다."
    },
    "현재가격이 비현실적인 Bull Case 이상을 요구": {
      "elements": [
        "현재가가 Bull 시나리오 가치를 초과할 것"
      ],
      "cleared_if": [
        "price_to_base_value가 Bull/현재가 배수 안에 있음"
      ],
      "not_covered": "Base가 야심적이라는 판단은 EV 점수가 반영한다."
    },
    "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성": {
      "elements": [
        "단일 제품·고객·규제에 대한 종속이 있을 것",
        "그 종속이 치명적일 것 — 해당 요인 상실 시 사업 경제성이 회복 불가하게 훼손될 것"
      ],
      "cleared_if": [
        "해당 리스크가 실제로 현실화됐음에도 매출·이익이 유지되거나 성장한 이력"
      ],
      "watch_trigger": [
        "단일 고객이 매출의 25%를 초과",
        "제2의 관할에서 판매 제한이 발생",
        "아직 스트레스 테스트되지 않은 종속 축(고객 집중 등)은 cleared로 두되 이 임계값을 모니터링한다"
      ],
      "not_covered": "높은 집중도 자체는 요건이 아니다. SL의 durability_risks가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "경영진 정직성 또는 회계 신뢰성 훼손", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "구조적으로 과도한 외부자본 조달 의존", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "고객가치 없이 마케팅·보조금에 의존하는 성장", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "증분 ROIC의 구조적 붕괴", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "해자의 지속적인 축소", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate NVDA-V31-2026-09-19 RT`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
