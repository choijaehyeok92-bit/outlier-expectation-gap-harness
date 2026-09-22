"""Market data, kept away from the regulators.

A price is not a disclosure. Reading one out of a filings API would produce a
number that cannot be reconciled against any market and that no exchange would
recognise, so `RegulatoryDataProvider` has no price method and these classes
have no filings method.

`CsvMarketDataProvider` is the offline default: a dated close per row, read from
`data/market/<JURISDICTION>/<TICKER>.csv`. It is deliberately dull, because the
part that matters is the same in every implementation — a snapshot is the last
observation *at or before* the as-of date, and never one after it.
"""
import csv
import re
from pathlib import Path
from typing import Optional

from .base import AdapterError, MarketDataProvider
from .types import MarketSnapshot, Security

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKET_DIR = ROOT / 'data' / 'market'
NUMERIC = re.compile(r'^-?\d+(\.\d+)?$')


def _number(value) -> Optional[float]:
    text = str(value or '').strip().replace(',', '')
    if not text or not NUMERIC.match(text):
        return None
    return float(text)


class CsvMarketDataProvider(MarketDataProvider):
    """Dated closes from a local CSV. Columns: date, close[, shares_outstanding, market_cap]."""

    name = 'csv'
    currency = 'USD'
    default_exchange = 'UNKNOWN'

    def __init__(self, root=None, jurisdiction: Optional[str] = None,
                 securities: Optional[dict] = None):
        self.jurisdiction = jurisdiction or self.jurisdiction
        self.root = Path(root or DEFAULT_MARKET_DIR) / self.jurisdiction
        self.securities = dict(securities or {})

    def _path(self, ticker: str) -> Path:
        return self.root / f'{ticker.upper()}.csv'

    def resolve_security(self, identifier: str) -> Security:
        ticker = str(identifier).strip().upper()
        if ticker in self.securities:
            return self.securities[ticker]
        return Security(issuer_key='', ticker=ticker, exchange=self.default_exchange,
                        currency=self.currency, security_type='common',
                        requires_review=True)

    def _rows(self, security: Security) -> list:
        path = self._path(security.ticker)
        if not path.exists():
            return []
        with path.open(encoding='utf-8', newline='') as handle:
            rows = []
            for row in csv.DictReader(handle):
                stamp = str(row.get('date') or '').strip()
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp):
                    continue
                rows.append({'date': stamp, 'close': _number(row.get('close')),
                             'shares_outstanding': _number(row.get('shares_outstanding')),
                             'market_cap': _number(row.get('market_cap'))})
        rows.sort(key=lambda r: r['date'])
        return rows

    def get_snapshot(self, security: Security, as_of_date: str) -> Optional[MarketSnapshot]:
        eligible = [r for r in self._rows(security) if r['date'] <= as_of_date]
        if not eligible:
            return None
        row = eligible[-1]
        return MarketSnapshot(
            security_key=security.security_key, as_of_date=row['date'],
            close=row['close'], market_cap=row['market_cap'],
            shares_outstanding=row['shares_outstanding'],
            currency=security.currency or self.currency,
            source=f'{self.name}:{self._path(security.ticker).name}')

    def get_price_history(self, security: Security, start_date: str, end_date: str) -> list:
        return [r for r in self._rows(security) if start_date <= r['date'] <= end_date]


class HttpMarketDataProvider(MarketDataProvider):
    """A market provider backed by a quote endpoint, with the transport injected.

    Subclasses declare `endpoint`, the query parameters and how to read one row
    out of the response. Everything venue-specific lives in config, so pointing
    this at a different KRX-compatible service is a config change.
    """

    name = 'http'
    currency = 'USD'
    default_exchange = 'UNKNOWN'

    def __init__(self, config: dict, transport=None, user_agent: str = 'outlier-harness/1.0',
                 fallback: Optional[MarketDataProvider] = None, client=None):
        from .http import HttpClient
        self.config = config
        self.client = client or HttpClient(
            user_agent, transport=transport,
            spacing_seconds=float(config.get('request_spacing_seconds', 0.2)))
        self.fallback = fallback

    def resolve_security(self, identifier: str) -> Security:
        return Security(issuer_key='', ticker=str(identifier).strip().upper(),
                        exchange=self.default_exchange, currency=self.currency,
                        security_type='common', requires_review=True)

    def _fetch_rows(self, security: Security, start_date: str, end_date: str) -> list:
        raise NotImplementedError

    def get_price_history(self, security: Security, start_date: str, end_date: str) -> list:
        try:
            rows = self._fetch_rows(security, start_date, end_date)
        except AdapterError:
            if self.fallback is None:
                raise
            return self.fallback.get_price_history(security, start_date, end_date)
        return [r for r in sorted(rows, key=lambda r: r['date'])
                if start_date <= r['date'] <= end_date]

    def get_snapshot(self, security: Security, as_of_date: str) -> Optional[MarketSnapshot]:
        window_start = self.config.get('snapshot_lookback_start', '1990-01-01')
        rows = self.get_price_history(security, window_start, as_of_date)
        if not rows:
            return self.fallback.get_snapshot(security, as_of_date) if self.fallback else None
        row = rows[-1]
        return MarketSnapshot(
            security_key=security.security_key, as_of_date=row['date'],
            close=row.get('close'), market_cap=row.get('market_cap'),
            shares_outstanding=row.get('shares_outstanding'),
            currency=security.currency or self.currency, source=self.name)
