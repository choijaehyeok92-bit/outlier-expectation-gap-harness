"""Fill `data/market/US/` from one bulk call, and say what is still missing.

The script, the worker handler and the API route all come through here, so
there is one description of what "fetch US prices" means rather than three that
drift apart.

Three rules shape it.

**A close comes from the market; a share count comes from the regulator.** The
vendor is asked for one number per listing. `shares_outstanding` is read out of
the Stage 0 packs (`dei:EntityCommonStockSharesOutstanding`), because that is a
disclosure and a quote service has no authority over it.

**A missing number stays missing.** A listing the vendor did not return, or one
with no share count at or before the cutoff, is reported by name. Nothing is
filled with zero: `market_cap` of nothing is a number that will be compared
against a threshold, and `unknown` will not.

**The walk is backwards only.** A request for a weekend or a holiday returns an
empty session. We then step back to the previous trading day, never forward:
using a price printed after the cutoff is exactly the retroactive use the
strategy forbids.
"""
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Optional

from ..base import AdapterError
from .provider import (UsHttpMarketDataProvider, api_key, load_config,  # noqa: F401
                       provider_settings)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_DIR = ROOT / 'runs'
COLUMNS = ('date', 'close', 'shares_outstanding')


# ------------------------------------------------------------------ packs
def _pack_shares(pack: dict, as_of: str) -> Optional[dict]:
    """The latest disclosed share count at or before the cutoff, or nothing."""
    best = None
    for fact in pack.get('facts') or []:
        if fact.get('metric') != 'period_end_shares':
            continue
        if fact.get('period_kind') not in (None, 'instant'):
            continue
        value, period_end = fact.get('value_reported'), fact.get('period_end') or ''
        if value is None or len(period_end) != 10 or period_end > as_of:
            continue
        scaled = float(value) * float(fact.get('scale_multiplier') or 1)
        if scaled <= 0:
            continue
        if best is None or period_end > best['period_end']:
            best = {'shares_outstanding': scaled, 'period_end': period_end,
                    'source': fact.get('source_locator') or fact.get('source_document')}
    return best


def _read_pack(path: Path) -> Optional[dict]:
    try:
        pack = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return pack if pack.get('facts') else None


def pack_paths(packs_dir=None, runs_dir=None) -> list:
    """Stage 0 packs, from an ingest directory and/or from completed runs."""
    paths = []
    if packs_dir:
        paths.extend(sorted(Path(packs_dir).glob('*.json')))
    base = Path(runs_dir) if runs_dir else DEFAULT_RUNS_DIR
    if base.exists():
        paths.extend(sorted(base.glob('*/sources/financials/normalized_financials.json')))
    return paths


def shares_index(as_of: str, packs_dir=None, runs_dir=None) -> dict:
    """{TICKER: {shares_outstanding, period_end, source}} for US packs only.

    A Korean pack is skipped rather than merged: its share count is real, but it
    belongs to a KRW listing that this US file does not describe.
    """
    index = {}
    for path in pack_paths(packs_dir, runs_dir):
        pack = _read_pack(path)
        if pack is None or (pack.get('reporting_currency') or 'USD').upper() != 'USD':
            continue
        ticker = str(pack.get('ticker') or path.stem).strip().upper()
        found = _pack_shares(pack, as_of)
        if not ticker or found is None:
            continue
        previous = index.get(ticker)
        if previous is None or found['period_end'] > previous['period_end']:
            index[ticker] = found
    return index


def pack_tickers(as_of: str, packs_dir=None, runs_dir=None) -> set:
    """Listings a Stage 0 pack exists for — the ones the warehouse can use."""
    found = set()
    for path in pack_paths(packs_dir, runs_dir):
        pack = _read_pack(path)
        if pack is None or (pack.get('reporting_currency') or 'USD').upper() != 'USD':
            continue
        if (pack.get('as_of_date') or '') and pack['as_of_date'] > as_of:
            continue
        ticker = str(pack.get('ticker') or path.stem).strip().upper()
        if ticker:
            found.add(ticker)
    return found


def universe_tickers(path=None) -> set:
    """Investable US listings from `harness.py universe sync`, when it has run."""
    from .. import universe as universe_store
    payload = universe_store.load(path)
    if payload is None:
        return set()
    return {str(row['ticker']).upper() for row in universe_store.investable(payload)
            if row.get('currency') == 'USD'}


# ------------------------------------------------------------------ session
def session_rows(as_of: str, provider, config: dict) -> dict:
    """Rows for the last trading session at or before `as_of`.

    Returns the session actually used, so a caller never has to assume the
    answer is about the date it asked for.
    """
    lookback = int(config.get('max_session_lookback_days') or 0)
    start = date.fromisoformat(as_of)
    tried = []
    for step in range(lookback + 1):
        session = (start - timedelta(days=step)).isoformat()
        tried.append(session)
        rows = provider.grouped_daily(session)
        if rows:
            return {'session_date': session, 'rows': rows, 'sessions_tried': tried}
    return {'session_date': None, 'rows': [], 'sessions_tried': tried}


# ------------------------------------------------------------------ writing
def csv_path(ticker: str, root=None) -> Path:
    base = Path(root) if root else ROOT / 'data' / 'market'
    return base / 'US' / f'{ticker.upper()}.csv'


def _existing(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding='utf-8', newline='') as handle:
        return {str(row.get('date') or '').strip(): dict(row)
                for row in csv.DictReader(handle)
                if len(str(row.get('date') or '').strip()) == 10}


def write_csv(ticker: str, row: dict, root=None) -> Path:
    """Upsert one dated close. Other dates in the file are preserved.

    The same date arriving again overwrites: an adjusted close is restated
    after a split, and keeping the pre-split number would be keeping a price
    the vendor no longer stands behind.
    """
    path = csv_path(ticker, root)
    merged = _existing(path)
    merged[row['date']] = {'date': row['date'], 'close': row['close'],
                           'shares_outstanding': row.get('shares_outstanding')}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        for stamp in sorted(merged):
            existing = merged[stamp]
            writer.writerow({column: ('' if existing.get(column) in (None, '') else
                                      existing.get(column)) for column in COLUMNS})
    return path


# ------------------------------------------------------------------ the job
def selection(as_of: str, tickers: Optional[Iterable[str]] = None, *, scope: str = 'packs',
              packs_dir=None, runs_dir=None, universe_path=None) -> tuple:
    """Which listings to write, and the human-readable reason for that set.

    The default is `packs`: writing ten thousand files for listings no Stage 0
    pack exists for would fill a disk to no purpose, because the warehouse
    cannot use a price without the financials beside it.
    """
    if tickers:
        wanted = {str(t).strip().upper() for t in tickers if str(t).strip()}
        return wanted, f'{len(wanted)} explicitly named'
    if scope == 'all':
        return None, 'every listing the vendor returned'
    if scope == 'universe':
        wanted = universe_tickers(universe_path)
        if not wanted:
            raise AdapterError('no universe file; run `python harness.py universe sync '
                               '--markets US` or use --scope packs')
        return wanted, f'{len(wanted)} investable US listings from the synced universe'
    wanted = pack_tickers(as_of, packs_dir, runs_dir)
    if not wanted:
        raise AdapterError('no US Stage 0 packs found; run `harness.py ingest` first, '
                           'or pass --tickers / --scope all')
    return wanted, f'{len(wanted)} listings a Stage 0 pack exists for'


def fetch_day(as_of: str, *, provider=None, provider_name=None, config=None,
              tickers=None, scope='packs', packs_dir=None, runs_dir=None,
              universe_path=None, root=None, write=True, transport=None,
              environ=None) -> dict:
    """One bulk call, merged with disclosed share counts, written to CSV."""
    config = config or load_config()
    if provider is None:
        provider = UsHttpMarketDataProvider(provider_name, config=config,
                                            transport=transport, environ=environ)
    wanted, reason = selection(as_of, tickers, scope=scope, packs_dir=packs_dir,
                               runs_dir=runs_dir, universe_path=universe_path)
    session = session_rows(as_of, provider, config)
    shares = shares_index(as_of, packs_dir, runs_dir)
    returned = {row['ticker']: row for row in session['rows']}
    targets = sorted(wanted) if wanted is not None else sorted(returned)

    written, missing_price, missing_shares, files = [], [], [], []
    for ticker in targets:
        row = returned.get(ticker)
        if row is None:
            missing_price.append(ticker)
            continue
        disclosed = shares.get(ticker)
        if disclosed is None:
            missing_shares.append(ticker)
        record = {'date': row['date'], 'close': row['close'],
                  'shares_outstanding': disclosed['shares_outstanding'] if disclosed else None}
        if write:
            files.append(str(write_csv(ticker, record, root)))
        written.append({'ticker': ticker, **record,
                        'shares_as_of': disclosed['period_end'] if disclosed else None})
    return {
        'as_of_date': as_of,
        'session_date': session['session_date'],
        'sessions_tried': session['sessions_tried'],
        'provider': getattr(provider, 'provider_name', getattr(provider, 'name', 'unknown')),
        'selection_reason': reason,
        'vendor_rows': len(session['rows']),
        'requested': len(targets),
        'written_count': len(written),
        'written': written,
        'missing_price': missing_price,
        'missing_shares_outstanding': missing_shares,
        'files': files,
        'wrote_files': bool(write),
        'note': ('no trading session found in the lookback window; nothing was written'
                 if session['session_date'] is None else
                 'shares_outstanding comes from Stage 0 packs, never from the quote vendor'),
    }


# ------------------------------------------------------------------ status
def coverage(as_of: str, *, root=None, packs_dir=None, runs_dir=None) -> dict:
    """What the screener would find: which US listings have a usable close.

    Counted against the Stage 0 packs, because a price without financials is
    not a screenable row and a pack without a price is the gap this module
    exists to close.
    """
    from .provider import UsMarketCsvProvider
    reader = UsMarketCsvProvider(root=root)
    wanted = sorted(pack_tickers(as_of, packs_dir, runs_dir))
    priced, stale, unpriced = [], [], []
    for ticker in wanted:
        snapshot = reader.get_snapshot(reader.resolve_security(ticker), as_of)
        if snapshot is None or snapshot.close is None:
            unpriced.append(ticker)
            continue
        entry = {'ticker': ticker, 'observed_date': snapshot.as_of_date,
                 'close': snapshot.close, 'shares_outstanding': snapshot.shares_outstanding}
        priced.append(entry)
        if snapshot.as_of_date < as_of:
            stale.append(entry)
    return {
        'as_of_date': as_of,
        'market_root': str(Path(root) if root else ROOT / 'data' / 'market'),
        'packs': len(wanted),
        'priced': len(priced),
        'unpriced': unpriced,
        'without_shares': [row['ticker'] for row in priced
                           if row['shares_outstanding'] is None],
        'older_than_cutoff': stale,
        'rows': priced,
    }


def describe(config=None, environ=None) -> list:
    """The declared vendors and whether a key exists for each.

    Never returns a key, a prefix of one, or its length — only whether one is
    set. This is served to a browser.
    """
    config = config or load_config()
    rows = []
    for name in sorted((config.get('providers') or {})):
        _, settings = provider_settings(config, name)
        rows.append({
            'name': name,
            'label': settings.get('label', name),
            'env_var': settings.get('api_key_env'),
            'configured': api_key(settings, environ) is not None,
            'bulk': bool(settings.get('bulk')),
            'signup': settings.get('signup'),
            'note': settings.get('cost_note'),
            'auth_note': settings.get('auth_note'),
            'is_default': name == config.get('default_provider'),
        })
    return rows
