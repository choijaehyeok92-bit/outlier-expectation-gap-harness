# NU Expectation & Valuation Prompt

Ticker: NU
As-of: 2026-09-21
Frozen price: $14.03
Frozen diluted shares: 4.904837B
Frozen net_cash_per_share: $0.00

Bank-specific valuation convention:
Nu is a regulated financial institution. Cash, securities, deposits and funding liabilities are operating capital, so conventional cash-minus-debt is not added to equity value. The locked owner_fcf_per_share field is used as a distributable owner-earnings/share proxy after capital retention.

Runner metadata: provider/model unspecified because the user invoked `freeze NU` without provider/model flags.

Locked valuation policy:
- required return: 9%
- horizon: 10 years
- terminal multiples: Bear 15x / Base 20x / Bull 25x

Distributable owner-earnings/share proxy paths:
- Bear: [0.20,0.22,0.24,0.27,0.30,0.33,0.36,0.39,0.42,0.45]
- Base: [0.32,0.40,0.50,0.62,0.76,0.92,1.08,1.25,1.42,1.60]
- Bull: [0.40,0.52,0.68,0.87,1.08,1.33,1.60,1.90,2.23,2.60]

Key questions:
- Can 30%+ ROE coexist with 20%+ multi-year growth after required equity retention?
- Does Mexico/Colombia scaling add enough value to offset Brazil maturation and FX/regulatory risk?
- Does unsecured-credit expansion create a permanent-loss path through NPL/ECL or funding stress?
