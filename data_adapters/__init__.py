"""Regulatory and market data adapters for the US and Korean markets.

The harness must not know which regulator a number came from. That is the whole
point of this package: `SecEdgarProvider` and `DartProvider` implement the same
`RegulatoryDataProvider` interface and both emit a document that validates
against the existing `schemas/financial_pack.schema.json`, so Stage 0 reads one
shape whether the filing was a 10-K or a 사업보고서.

Market data is a separate interface on purpose. A price is not a regulatory
disclosure, and mixing the two is how a valuation ends up quietly resting on a
number nobody filed. `DartProvider` has no price method at all.
"""
from .base import (AdapterError, ConsolidationMixError, MarketDataProvider,
                   RegulatoryDataProvider)
from .types import Filing, FinancialFact, Issuer, MarketSnapshot, Security

__all__ = ['AdapterError', 'ConsolidationMixError', 'MarketDataProvider',
           'RegulatoryDataProvider', 'Filing', 'FinancialFact', 'Issuer',
           'MarketSnapshot', 'Security']
