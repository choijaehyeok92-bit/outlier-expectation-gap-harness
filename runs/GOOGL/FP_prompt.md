# GOOGL Financial Preprocessor Prompt

Ticker: GOOGL
As-of: 2026-09-21
Output: runs/GOOGL/sources/financials/normalized_financials.json

Use only documents dated on or before 2026-09-21. Normalize filing facts without economic interpretation. Preserve reported signs except positive-cost metrics defined by the harness. Record source_document, period kind, scale, GAAP status, confidence and review flags. Do not score the company.

Required coverage includes the latest 10-K, latest 10-Q and at least six trailing quarterly filings. The current reconstructed pack includes FY2025 10-K, Q1/Q2 2026, Q1-Q3 2025, Q2-Q3 2024, the August 2026 financing 8-K, and a September 2026 Form 4.

Important review points:
- separate reported net income from large unrealized strategic-equity gains;
- preserve AI infrastructure capex as reported rather than normalizing it away;
- keep strategic equity securities outside conservative net cash unless explicitly justified;
- capture debt/equity financing separately from operating cash generation.
