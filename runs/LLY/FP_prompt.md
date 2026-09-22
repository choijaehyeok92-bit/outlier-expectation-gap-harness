# LLY Financial Preprocessor Prompt

Ticker: LLY
As-of: 2026-09-21
Output: runs/LLY/sources/financials/normalized_financials.json

Use only documents with filing/publication timestamps on or before the cutoff.

Normalize:
- latest FY2025 10-K plus FY2024/FY2023 annual history;
- Q2/Q1 2026, Q3/Q2/Q1 2025, and Q3/Q2 2024 10-Qs;
- 2026 DEF 14A;
- Q2 2026 earnings release;
- May 2026 debt financing 8-K/related prospectus evidence;
- insider ownership evidence where available.

Pharma-specific cautions:
- distinguish GAAP R&D from acquired IPR&D;
- do not automatically treat acquired IPR&D as non-recurring economically;
- preserve manufacturing capex and supply commitments;
- preserve product concentration (Mounjaro/Zepbound), geography and pricing/rebate evidence;
- separate accounting FCF from acquisitions and pipeline reinvestment;
- preserve diluted shares and repurchases.

Do not score or make an investment conclusion. Output normalized source facts and adjustment candidates only.
