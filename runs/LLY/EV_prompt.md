# LLY Expectation & Valuation Prompt

Ticker: LLY
As-of: 2026-09-21
Frozen price: $1,164.89
Frozen diluted shares: 893.7M
Frozen net_cash_per_share: -$47.1098

Locked valuation policy:
- required return: 9%
- horizon: 10 years
- terminal multiples: Bear 15x / Base 20x / Bull 25x

Owner-FCF/share paths:
- Bear: [18,20,22,24,26,28,30,32,34,36]
- Base: [24,31,39,48,58,69,80,91,102,113]
- Bull: [28,38,49,61,74,88,103,118,134,150]

Interpret owner FCF as operating cash flow less capital expenditures, with explicit caution that acquired IPR&D and acquisitions are economically meaningful pharmaceutical reinvestment and should not be dismissed as "one-time" simply because they sit outside CFO.

Reference normalization:
- FY2025 CFO-capex = about $8.97B.
- TTM through Q2 2026 CFO-capex proxy = about $18.19B, or ~$20.35/share.
- The Base path begins above this TTM level because current manufacturing capex is unusually high and requires normalization, but it also assumes sustained obesity/diabetes franchise and pipeline execution.
- Conservative net debt is included through net_cash_per_share = -$47.11.

Key questions:
1. Does the current price require continued tirzepatide-scale growth, or can Base execution support it?
2. How much terminal dependence remains if Mounjaro/Zepbound growth decelerates?
3. Do orforglipron, retatrutide and non-cardiometabolic pipeline assets sufficiently diversify the franchise?
4. How should pricing/rebate pressure and manufacturing capacity spending affect robustness?

Runner metadata: provider/model unspecified because the user invoked `freeze LLY` without provider/model flags.
