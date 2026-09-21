# BRK.B verified source bundle — as of 2026-09-18

## Primary filings
- SEC 10-Q, quarter ended 2026-06-30, filed 2026-08-10: https://www.sec.gov/Archives/edgar/data/1067983/000119312526341032/brka-20260630.htm
  - H1 operating cash flow $21.7B; capex $10.6B.
  - Insurance & Other cash/cash equivalents/U.S. Treasury Bills $359.2B.
  - Borrowings excluding BHE/BNSF $43.3B; BNSF debt $23.5B; BHE borrowings $61.8B.
  - H1 share repurchases about $4.8B.
  - OxyChem acquired for about $9.4B; Taylor Morrison completed 2026-07-24 for about $6.8B equity value.
- SEC Q2 earnings release: https://www.sec.gov/Archives/edgar/data/1067983/000119312526344495/d159922dex991.htm
  - Q2 operating earnings $12.983B; H1 $24.329B vs $20.801B prior year.
  - H1 underwriting $3.448B; insurance investment income $5.738B; BNSF $2.935B; BHE $2.005B; manufacturing/service/retail $7.669B.
  - Insurance float about $177.5B at 2026-06-30.
- SEC 10-Q, quarter ended 2026-03-31, filed 2026-05-04: https://www.sec.gov/Archives/edgar/data/1067983/000119312526202243/brka-20260331.htm
- SEC 2025 10-K: https://www.sec.gov/Archives/edgar/data/1067983/000119312526083899/brka-20251231.htm
- SEC 2026 DEF 14A, filed 2026-03-13: https://www.sec.gov/Archives/edgar/data/1067983/000119312526106253/d882687ddef14a.htm
  - Gregory Abel became CEO 2026-01-01; Warren Buffett remained Chairman as of the cutoff.

## Market data fixed at cutoff
- StockAnalysis BRK.B history: https://stockanalysis.com/stocks/brk.b/history/
  - 2026-09-18 close $509.77.
- FinanceCharts P/B: https://www.financecharts.com/stocks/BRK.B/value/price-to-book-value-averages
  - P/B 1.47; 5-year average P/B 1.49.

## Frozen modeling conventions
- Current B-equivalent share count from 2026 Q2 filing cover (2026-07-29): 488,450 A + 1,408,035,161 B = 2,140,710,161 B-equivalent.
- market_cap_usd = $509.77 × 2,140,710,161 ≈ $1.0913T.
- net_cash_per_share = (Insurance & Other cash/T-bills $359.2B - Insurance & Other borrowings $43.3B) / 2,140,710,161 ≈ $147.57.
- Equity securities and BNSF/BHE operating debt are excluded from net_cash_per_share; their economics remain in operating/owner earnings.
- EV owner-FCF paths use normalized operating earnings as a proxy, explicitly flagged as model uncertainty.
