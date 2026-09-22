"""US market data providers.

A price is not a disclosure, so it does not come from SEC. A share count *is* a
disclosure, so it does not come from here: `dei:EntityCommonStockSharesOutstanding`
is already in every Stage 0 pack, and `bulk.py` reads it from there. What this
module fetches is one number per listing — the close — and that is deliberate.

`UsMarketCsvProvider` is the offline default and reads `data/market/US/<T>.csv`.
`UsHttpMarketDataProvider` talks to a quote vendor declared in
`config/market_us.json`; the endpoint, its auth style and its field names live
in that file so a different vendor is a config change, not a code change. The
transport is injectable, so parsing is covered by recorded fixtures without
reaching a live venue — which is just as well: this environment cannot reach
one, and the live call has never been exercised.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..base import AdapterError
from ..http import TransportError
from ..marketdata import CsvMarketDataProvider, HttpMarketDataProvider, _number
from ..types import Security

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'config' / 'market_us.json'


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


def provider_settings(config: dict, name: Optional[str] = None) -> tuple:
    """(name, merged settings) for one declared vendor.

    The vendor block is merged onto the shared block so a caller holds a single
    flat mapping and `HttpMarketDataProvider` finds `request_spacing_seconds`
    where it expects it.
    """
    name = (name or config.get('default_provider') or '').strip()
    vendors = config.get('providers') or {}
    if name not in vendors:
        known = ', '.join(sorted(vendors)) or 'none declared'
        raise AdapterError(f'unknown US market provider {name!r}; config declares: {known}')
    shared = {k: v for k, v in config.items() if k != 'providers'}
    return name, {**shared, **vendors[name]}


def api_key(settings: dict, environ=None) -> Optional[str]:
    """The vendor's key, from the environment only.

    No caller passes one in. A key that can arrive in an argument ends up in a
    job payload, and this repository serves job payloads back over HTTP.
    """
    variable = settings.get('api_key_env')
    if not variable:
        return None
    value = (environ if environ is not None else os.environ).get(variable)
    return value.strip() or None if isinstance(value, str) else None


def authorize(settings: dict, headers: dict, params: dict, key: Optional[str]) -> None:
    """Apply the declared auth style in place. An absent key changes nothing."""
    if not key:
        return
    auth = settings.get('auth') or {}
    kind = auth.get('kind')
    if kind == 'bearer_header':
        headers[auth.get('header', 'Authorization')] = f"{auth.get('prefix', 'Bearer ')}{key}"
    elif kind == 'query_param':
        params[auth['param']] = key
    else:
        raise AdapterError(f'unsupported auth kind {kind!r} in config/market_us.json')


def utc_date(epoch_ms) -> Optional[str]:
    """A daily bar's session date. Vendors stamp these at exchange midnight."""
    number = _number(epoch_ms)
    if number is None:
        return None
    return datetime.fromtimestamp(number / 1000.0, tz=timezone.utc).date().isoformat()


def read_rows(payload, path) -> list:
    rows = payload
    for key in (path or []):
        rows = (rows or {}).get(key) or []
    return rows if isinstance(rows, list) else []


def parse_row(row: dict, fields: dict, fallback_date: Optional[str],
              epoch_field: Optional[str], ticker_suffix: Optional[str] = None) -> Optional[dict]:
    """One vendor row to the shape the CSV and the snapshot both use.

    A row with no usable close is dropped rather than written as zero: a
    missing price and a price of nothing are not the same fact.
    """
    date_field = fields.get('date')
    stamp = str(row.get(date_field) or '').strip() if date_field else ''
    if not stamp and epoch_field:
        stamp = utc_date(row.get(epoch_field)) or ''
    stamp = stamp or (fallback_date or '')
    close = _number(row.get(fields.get('close')))
    if len(stamp) != 10 or close is None:
        return None
    parsed = {'date': stamp, 'close': close}
    for extra in ('market_cap', 'shares_outstanding', 'volume'):
        field = fields.get(extra)
        parsed[extra] = _number(row.get(field)) if field else None
    ticker = str(row.get(fields.get('ticker')) or '').strip().upper()
    # Only the suffix the vendor declares is removed. A blanket split on '.'
    # would turn BRK.B into BRK, which is a different security.
    suffix = (ticker_suffix or '').upper()
    if suffix and ticker.endswith(suffix) and len(ticker) > len(suffix):
        ticker = ticker[:-len(suffix)]
    if ticker:
        parsed['ticker'] = ticker
    return parsed


class UsMarketCsvProvider(CsvMarketDataProvider):
    """Dated US closes from disk. Exchange comes from the SEC universe, not a guess."""

    name = 'us_market_csv'
    jurisdiction = 'US'
    currency = 'USD'
    default_exchange = 'UNKNOWN'

    def __init__(self, root=None, securities: Optional[dict] = None):
        super().__init__(root=root, jurisdiction='US', securities=securities)

    @classmethod
    def from_universe(cls, securities, root=None) -> 'UsMarketCsvProvider':
        return cls(root=root, securities={s.ticker.upper(): s for s in securities
                                          if s.currency == 'USD'})

    def resolve_security(self, identifier: str) -> Security:
        return super().resolve_security(identifier)


# The name `screen build` already imports. Kept so existing callers do not move.
UsMarketDataProvider = UsMarketCsvProvider


class UsHttpMarketDataProvider(HttpMarketDataProvider):
    """Daily closes for a US listing from a declared quote vendor."""

    jurisdiction = 'US'
    currency = 'USD'
    default_exchange = 'UNKNOWN'

    def __init__(self, provider: Optional[str] = None, config: Optional[dict] = None,
                 transport=None, fallback=None, securities: Optional[dict] = None,
                 environ=None, **kwargs):
        config = config or load_config()
        self.provider_name, settings = provider_settings(config, provider)
        self.name = self.provider_name
        self.settings = settings
        self.environ = environ
        super().__init__(settings, transport=transport,
                         fallback=fallback if fallback is not None else UsMarketCsvProvider(),
                         **kwargs)
        self.securities = dict(securities or {})
        self.fields = settings['response_fields']

    # -------------------------------------------------------------- plumbing
    @property
    def key(self) -> Optional[str]:
        return api_key(self.settings, self.environ)

    def require_key(self) -> str:
        key = self.key
        if key:
            return key
        raise AdapterError(
            f"{self.settings.get('label', self.provider_name)} needs "
            f"${self.settings.get('api_key_env')}; set it in the environment of the "
            f"process that fetches prices. Sign up: {self.settings.get('signup', '')}".strip())

    def _url(self, endpoint: str, **kwargs) -> str:
        return f"{self.settings['api_base']}{self.settings['endpoints'][endpoint].format(**kwargs)}"

    def _get(self, url: str, params: dict):
        headers, query = {}, dict(self.settings.get('static_params') or {})
        query.update(params)
        authorize(self.settings, headers, query, self.require_key())
        try:
            return self.client.get_json(url, query, headers)
        except TransportError as error:
            # The key is in a header or a param; neither is echoed here.
            raise AdapterError(f'{self.provider_name} quote service unavailable: {error}') from error

    # ------------------------------------------------------------- interface
    def resolve_security(self, identifier: str) -> Security:
        ticker = str(identifier).strip().upper()
        if ticker in self.securities:
            return self.securities[ticker]
        return Security(issuer_key='', ticker=ticker, exchange=self.default_exchange,
                        currency='USD', security_type='common', requires_review=True)

    def _fetch_rows(self, security: Security, start_date: str, end_date: str) -> list:
        url = self._url('ticker_range', ticker=security.ticker,
                        start=start_date, end=end_date)
        mapping = self.settings.get('ticker_range_params') or {}
        params = {mapping[k]: v for k, v in (('start', start_date), ('end', end_date))
                  if k in mapping}
        payload = self._get(url, params)
        rows = read_rows(payload, self.settings.get('ticker_range_rows_path'))
        epoch = self.settings.get('epoch_ms_field')
        parsed = [parse_row(row, self.fields, None, epoch,
                            self.settings.get('ticker_suffix')) for row in rows]
        return [row for row in parsed if row]

    def grouped_daily(self, session_date: str) -> list:
        """Every US listing's close for one session, in a single call.

        This is the whole reason to prefer a vendor with a bulk endpoint: the
        per-ticker loop that would otherwise cost one request per listing
        becomes one request for the market.
        """
        url = self._url('grouped_daily', date=session_date)
        params = {}
        if self.settings.get('date_param'):
            params[self.settings['date_param']] = session_date
        payload = self._get(url, params)
        rows = read_rows(payload, self.settings.get('rows_path'))
        fallback = session_date if self.settings.get('date_from_request') else None
        epoch = self.settings.get('epoch_ms_field')
        parsed = [parse_row(row, self.fields, fallback, epoch,
                            self.settings.get('ticker_suffix')) for row in rows]
        return [row for row in parsed if row and row.get('ticker')]
