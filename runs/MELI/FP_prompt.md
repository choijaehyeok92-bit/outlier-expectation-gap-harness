# MELI Financial Preprocessor Prompt

Ticker: MELI
As-of: 2026-09-21
Output: runs/MELI/sources/financials/normalized_financials.json

Use only documents dated on or before 2026-09-21. Normalize reported financial facts without changing their economic meaning. Preserve GAAP/non-GAAP labels, period kind, scale, source document and review status. Do not score the company.

Required Stage 0 coverage:
- latest 10-K;
- latest 10-Q;
- at least six trailing 10-Q filings.

Decision-useful review points:
- distinguish GAAP operating cash flow from company-defined adjusted free cash flow;
- treat Mercado Pago customer funds, lending receivables and fintech funding as operating/economic working-capital items rather than ordinary surplus cash;
- preserve credit-loss provisions and loan-book growth;
- keep logistics/warehouse leases and purchase commitments visible;
- record the September 2026 $1B notes issue separately;
- do not infer a change in net debt from the notes issue without post-settlement use-of-proceeds evidence.
