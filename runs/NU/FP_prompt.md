# NU Financial Preprocessor Prompt

Ticker: NU
As-of: 2026-09-21
Output: runs/NU/sources/financials/normalized_financials.json

Nu Holdings is a foreign private issuer. Treat Form 20-F as the annual-report source and only count Form 6-K as an interim-quarter equivalent when quarter or YTD financial facts are actually extracted from that exact document.

Normalize facts without economic interpretation. Preserve IFRS/non-IFRS labels, source document, period kind, scale and review status.

Bank-specific cautions:
- customer deposits, securities, reverse repos and wholesale funding are operating balance-sheet items;
- do not calculate industrial-company net cash or free cash flow from bank cash-flow statements;
- preserve capital, equity, deposits, credit portfolio, NPL/ECL, NIM/risk-adjusted NIM and ROE evidence;
- separate accounting P&L from managerial/non-IFRS P&L;
- preserve share repurchases and SBC dilution separately.

Required coverage:
- latest annual 20-F;
- latest interim financial 6-K;
- at least six quarter/ytd-bearing 6-Ks.
