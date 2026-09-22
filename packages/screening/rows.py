"""The row source the screening compiler reads.

Two backends feed it and they answer different questions, so the merge rule is
explicit rather than convenient.

`harness_run_index` holds companies the harness has actually analysed: frozen
inputs, reviewed numbers, a Hard Veto status somebody owns. `screening_warehouse`
holds mechanically computed metrics for everything that has been ingested,
including companies nobody has looked at yet.

Where both have a field, the harness wins. Its value was frozen and reviewed;
the warehouse value is a calculation over a pack. Where only the warehouse has
it, the warehouse value is used and the row records where it came from, so a
reader can tell a reviewed figure from a computed one.

A company with warehouse metrics and no harness run is kept, not dropped —
that is the whole point of a cheap pre-screen. Its harness fields are simply
absent, so any filter over them evaluates unknown and the default missing
policy excludes it from the *ranked* results while the spec's
`requires_harness_run` flag says why.
"""
import os
from typing import Optional

from . import runs_index, warehouse

HARNESS_PRECEDENCE = ('ticker', 'company_name', 'jurisdiction', 'exchange', 'currency',
                      'as_of_date', 'market_cap_usd', 'current_price', 'net_cash_per_share')


def _fx_to_usd(value: Optional[float], currency: Optional[str], fx_rates: dict) -> Optional[float]:
    """Convert only with a rate the caller supplied. No rate is ever invented."""
    if value is None or not currency:
        return None
    if currency.upper() == 'USD':
        return float(value)
    rate = (fx_rates or {}).get(currency.upper())
    per_usd = (rate or {}).get('per_usd') if isinstance(rate, dict) else rate
    try:
        per_usd = float(per_usd)
    except (TypeError, ValueError):
        return None
    return float(value) / per_usd if per_usd > 0 else None


def merge_row(harness: Optional[dict], metrics: Optional[dict],
              fx_rates: Optional[dict] = None) -> dict:
    """One company as the compiler sees it, with the origin of each field."""
    row: dict = {}
    sources: dict = {}

    for key, value in (metrics or {}).items():
        row[key] = value
        sources[key] = 'screening_warehouse'

    for key, value in (harness or {}).items():
        if value is None and key in row:
            continue                      # the harness has no opinion; keep the computed value
        if key in row and key not in HARNESS_PRECEDENCE and value is None:
            continue
        row[key] = value
        sources[key] = 'harness_run_index'

    row['has_harness_run'] = bool(harness)
    row['has_warehouse_metrics'] = bool(metrics)

    # A market cap in won cannot be compared against a threshold in dollars
    # without a rate, and the rate is the caller's to supply.
    if row.get('market_cap_usd') is None and row.get('market_cap') is not None:
        currency = (row.get('currency') or '').upper()
        converted = _fx_to_usd(row.get('market_cap'), row.get('currency'), fx_rates or {})
        if converted is not None:
            row['market_cap_usd'] = converted
            sources['market_cap_usd'] = ('derived:market_cap' if currency == 'USD'
                                         else f'derived:fx({currency})')

    row['field_sources'] = sources
    return row


def resolve_source(source: str = 'auto') -> str:
    """Where rows come from: the files, or the database if one is configured.

    `auto` uses the database only when `HARNESS_DATABASE_URL` is set, which is
    itself an explicit opt-in. Nothing starts depending on a database silently.
    """
    if source != 'auto':
        return source
    if not os.environ.get('HARNESS_DATABASE_URL'):
        return 'files'
    try:
        import db.repository                        # noqa: F401
    except Exception:
        return 'files'
    return 'db'


def load_rows_from_db(as_of_date: Optional[str] = None,
                      fx_rates: Optional[dict] = None) -> list:
    """The same merged shape, assembled from the index rather than the files."""
    from db.repository import merged_rows
    from db.session import engine_for, session_scope
    with session_scope(engine_for()) as session:
        return merged_rows(session, as_of_date, fx_rates)


def load_rows(as_of_date: Optional[str] = None, fx_rates: Optional[dict] = None,
              runs_dir=None, warehouse_payload: Optional[dict] = None,
              include_warehouse: bool = True, source: str = 'auto') -> list:
    """Every company either backend knows about, merged and keyed by ticker."""
    if runs_dir is None and warehouse_payload is None and resolve_source(source) == 'db':
        return load_rows_from_db(as_of_date, fx_rates)
    harness_rows = runs_index.load_rows(runs_dir)
    if as_of_date:
        harness_rows = [row for row in harness_rows if (row.get('as_of_date') or '') <= as_of_date]
    # One row per ticker: the most recent run at or before the cutoff.
    latest: dict = {}
    for row in sorted(harness_rows, key=lambda r: r.get('as_of_date') or ''):
        latest[(row.get('ticker') or '').upper()] = row

    metrics_by_ticker: dict = {}
    if include_warehouse:
        payload = warehouse_payload if warehouse_payload is not None else warehouse.load(as_of_date)
        if payload is None and warehouse_payload is None:
            payload = warehouse.load()
        for row in warehouse.flat_rows(payload or {}):
            if as_of_date and (row.get('as_of_date') or '') > as_of_date:
                continue
            metrics_by_ticker[(row.get('ticker') or '').upper()] = row

    merged = []
    for ticker in sorted(set(latest) | set(metrics_by_ticker)):
        merged.append(merge_row(latest.get(ticker), metrics_by_ticker.get(ticker), fx_rates))
    return merged


def backend_summary(rows: list, source: str = 'auto') -> dict:
    return {'rows': len(rows), 'source': resolve_source(source),
            'with_harness_run': sum(1 for r in rows if r.get('has_harness_run')),
            'with_warehouse_metrics': sum(1 for r in rows if r.get('has_warehouse_metrics')),
            'warehouse_only': sum(1 for r in rows
                                  if r.get('has_warehouse_metrics') and not r.get('has_harness_run')),
            'backends': ['harness_run_index'] + (['screening_warehouse']
                                                 if warehouse.available() else [])}
