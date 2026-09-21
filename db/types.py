"""Column types that mean the same thing on PostgreSQL and on SQLite.

Two dialects, because they answer different needs. PostgreSQL is the target and
the only one the production schema is tuned for. SQLite is what lets the whole
database layer be tested in a unit test with no service running, which is the
difference between a migration that is checked on every commit and one that is
checked when somebody remembers.

`JSONColumn` is JSONB on PostgreSQL and JSON elsewhere. `Money` and `Ratio`
return floats rather than Decimals: a screening metric is compared against a
float threshold, and mixing the two silently raises TypeError deep inside a
filter.
"""
from sqlalchemy import JSON, Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB

JSONColumn = JSON().with_variant(JSONB(), 'postgresql')

# Currency amounts: wide enough for a KRW balance sheet in won, which is where
# a 38-digit total assets figure actually appears.
Money = Numeric(28, 4, asdecimal=False)
# Ratios, margins and growth rates: decimal fractions, never percents.
Ratio = Numeric(18, 8, asdecimal=False)
# One column holds both kinds of screening metric: a margin of 0.70 and a
# revenue of 63,887,000,000 — and, in won, figures two orders larger again. It
# has to fit the widest of them without rounding the narrowest.
MetricValue = Numeric(38, 10, asdecimal=False)
Score = Numeric(8, 4, asdecimal=False)
Shares = Numeric(24, 4, asdecimal=False)

Sha256 = String(64)
ShortText = String(255)
Identifier = String(64)

__all__ = ['JSONColumn', 'Money', 'MetricValue', 'Ratio', 'Score', 'Shares', 'Sha256',
           'ShortText', 'Identifier', 'Date', 'DateTime']
