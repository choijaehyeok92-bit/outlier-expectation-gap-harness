"""Korean market data provider, KRX-compatible.

Prices for Korean listings come from a KRX-compatible quote service, never from
OpenDART. DART is the regulator: it publishes what a company disclosed, and a
share price is not one of those things. Mixing the two would put a number into
a valuation that no exchange ever printed.

The endpoint, its parameters and its field names are declared in
`config/market_kr.json` so a different KRX-compatible service is a config
change. The transport is injectable, so the parsing is covered by tests without
reaching a live venue — which is just as well: this environment cannot reach
one, so the live call has never been exercised.
"""
import json
from pathlib import Path
from typing import Optional

from ..base import AdapterError
from ..http import TransportError
from ..marketdata import CsvMarketDataProvider, HttpMarketDataProvider, _number
from ..types import Security

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'config' / 'market_kr.json'


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


class KrMarketCsvProvider(CsvMarketDataProvider):
    name = 'kr_market_csv'
    jurisdiction = 'KR'
    currency = 'KRW'
    default_exchange = 'KRX'

    def __init__(self, root=None, securities: Optional[dict] = None):
        super().__init__(root=root, jurisdiction='KR', securities=securities)


class KrxMarketDataProvider(HttpMarketDataProvider):
    """Daily closes and market cap for a KRX listing."""

    name = 'krx'
    jurisdiction = 'KR'
    currency = 'KRW'
    default_exchange = 'KRX'

    def __init__(self, config: Optional[dict] = None, transport=None,
                 fallback=None, securities: Optional[dict] = None, **kwargs):
        config = config or load_config()
        super().__init__(config, transport=transport,
                         fallback=fallback if fallback is not None else KrMarketCsvProvider(),
                         **kwargs)
        self.securities = dict(securities or {})
        self.fields = config['response_fields']

    def resolve_security(self, identifier: str) -> Security:
        ticker = str(identifier).strip().upper().zfill(6) if str(identifier).strip().isdigit() \
            else str(identifier).strip().upper()
        if ticker in self.securities:
            return self.securities[ticker]
        return Security(issuer_key='', ticker=ticker, exchange=self.default_exchange,
                        currency='KRW', security_type='common', requires_review=True)

    def _fetch_rows(self, security: Security, start_date: str, end_date: str) -> list:
        params = {self.config['params']['ticker']: security.ticker,
                  self.config['params']['start_date']: start_date.replace('-', ''),
                  self.config['params']['end_date']: end_date.replace('-', '')}
        params.update(self.config.get('static_params') or {})
        try:
            payload = self.client.get_json(self.config['endpoint'], params)
        except TransportError as error:
            raise AdapterError(f'KRX-compatible quote service unavailable: {error}') from error
        rows = payload
        for key in (self.config.get('rows_path') or []):
            rows = (rows or {}).get(key) or []
        parsed = []
        for row in rows or []:
            stamp = str(row.get(self.fields['date']) or '').strip().replace('/', '-')
            if len(stamp) == 8 and stamp.isdigit():
                stamp = f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}'
            if len(stamp) != 10:
                continue
            parsed.append({
                'date': stamp,
                'close': _number(row.get(self.fields['close'])),
                'market_cap': _number(row.get(self.fields.get('market_cap'))),
                'shares_outstanding': _number(row.get(self.fields.get('shares_outstanding')))})
        return parsed
