"""Build and persist the investable US/KR universe.

The point of a universe step is to decide, once and visibly, which listings are
even candidates. Two rules shape it.

**Exclusions are recorded, not silent.** An ETF, a warrant, a SPAC shell or a
KONEX listing is written into the file with the reason it was excluded, so the
question "why is this not in my screen?" has an answer that does not require
re-running anything.

**Uncertainty is not resolution.** A listing whose exchange or security type the
adapter could not establish is kept with `requires_review`, not quietly dropped
and not assigned a plausible-looking market. The count of those is part of the
summary, because a universe that silently shrank is worse than one that says it
is unsure about four hundred rows.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .types import Security

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / 'data' / 'universe' / 'securities.json'


def summarize(securities: Iterable[Security]) -> dict:
    rows = list(securities)
    included = [s for s in rows if not s.excluded_reason]
    by_exchange, by_type, by_reason = {}, {}, {}
    for security in rows:
        if not security.excluded_reason:
            by_exchange[security.exchange] = by_exchange.get(security.exchange, 0) + 1
        else:
            by_reason[security.excluded_reason] = by_reason.get(security.excluded_reason, 0) + 1
        by_type[security.security_type] = by_type.get(security.security_type, 0) + 1
    return {'total': len(rows), 'included': len(included),
            'excluded': len(rows) - len(included),
            'requires_review': sum(1 for s in rows if s.requires_review),
            'by_exchange': dict(sorted(by_exchange.items())),
            'by_security_type': dict(sorted(by_type.items())),
            'excluded_by_reason': dict(sorted(by_reason.items()))}


def sync(providers: dict, as_of_date: Optional[str] = None, **provider_kwargs) -> dict:
    """Run `list_universe` on each named provider and merge the results.

    `providers` maps a market code ('US', 'KR') to a `RegulatoryDataProvider`.
    A provider that fails is recorded as an error rather than taking the whole
    sync down: a broken DART key should not cost you the US universe.
    """
    markets, errors, securities = {}, {}, []
    for market, provider in providers.items():
        try:
            rows = provider.list_universe(**(provider_kwargs.get(market) or {}))
        except Exception as error:                  # provider-specific failure modes
            errors[market] = f'{type(error).__name__}: {error}'
            continue
        securities.extend(rows)
        markets[market] = summarize(rows)
    return {
        'schema_version': '1.0',
        'as_of_date': as_of_date,
        'synced_at_utc': datetime.now(timezone.utc).isoformat(),
        'markets': markets,
        'errors': errors,
        'summary': summarize(securities),
        'securities': [s.to_dict() for s in sorted(securities,
                                                   key=lambda s: (s.exchange, s.ticker))],
    }


def save(payload: dict, path=None) -> Path:
    target = Path(path or DEFAULT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return target


def load(path=None) -> Optional[dict]:
    target = Path(path or DEFAULT_PATH)
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding='utf-8'))


def investable(payload: dict) -> list:
    """Rows that survived every exclusion. Review-flagged rows are still in."""
    return [row for row in (payload or {}).get('securities', []) if not row.get('excluded_reason')]
