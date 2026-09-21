"""US market data provider."""
from typing import Optional

from ..marketdata import CsvMarketDataProvider
from ..types import Security


class UsMarketDataProvider(CsvMarketDataProvider):
    """Dated US closes. Exchange comes from the SEC universe, not from a guess."""

    name = 'us_market_csv'
    jurisdiction = 'US'
    currency = 'USD'
    default_exchange = 'UNKNOWN'

    def __init__(self, root=None, securities: Optional[dict] = None):
        super().__init__(root=root, jurisdiction='US', securities=securities)

    @classmethod
    def from_universe(cls, securities, root=None) -> 'UsMarketDataProvider':
        return cls(root=root, securities={s.ticker.upper(): s for s in securities
                                          if s.currency == 'USD'})

    def resolve_security(self, identifier: str) -> Security:
        return super().resolve_security(identifier)
