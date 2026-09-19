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
