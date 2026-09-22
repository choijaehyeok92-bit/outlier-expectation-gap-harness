"""Decide which listings are worth a Stage 0 ingest, and then ingest them.

Between `universe sync` (every listing) and `screen build` (every metric) sits
a question nothing else answers: of five thousand listings, which few hundred
get an ingest call spent on them?

**It cannot be a market-cap cut, and saying so matters.** Market cap is close ×
shares outstanding, and the share count comes from the regulator — you have to
ingest a company to learn it. Cutting by market cap before ingesting is
circular: it costs exactly what it was supposed to save. So the rank here is
dollar volume, close × volume, which one bulk quote call gives for the whole
market at once.

**A rank is not evidence.** Dollar volume decides where the next call goes and
nothing else. It never reaches a score, an archetype, a Hard Veto, a valuation
or a Stage 0 pack. Liquidity is not company quality, and a long-term outlier is
frequently illiquid before it is obvious — which is why this file ranks what to
*look at* and refuses to rank what to *own*.

**Korea is listed, not ranked.** The KRX adapter quotes one listing per call,
so there is no bulk session to rank against. Korean candidates come back
unranked with that stated, rather than ordered by a number that does not exist.
"""
import json
import re
from pathlib import Path
from typing import Optional

from .base import AdapterError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK_DIR = ROOT / 'data' / 'packs'


def alias_of(ticker: str, rewrite: Optional[dict]) -> str:
    """The vendor's spelling of a regulator's ticker, or the ticker unchanged."""
    if not rewrite:
        return ticker
    return re.sub(rewrite['pattern'], rewrite['replacement'], ticker)


def quote_for(ticker: str, quotes: dict, rewrite: Optional[dict]) -> tuple:
    """A listing's quote, allowing for the two spellings of a share class.

    SEC writes BRK-B and most quote vendors write BRK.B. Left alone, that one
    character drops a real company out of the candidate list as "no quote" —
    the quietest possible failure. The rewrite is declared in config, applies
    only to a trailing single class letter, and is tried only after the
    regulator's own spelling has failed.
    """
    found = quotes.get(ticker)
    if found is not None or not rewrite:
        return found, ticker
    alias = alias_of(ticker, rewrite)
    if alias == ticker:
        return None, ticker
    return quotes.get(alias), alias


# ------------------------------------------------------------------ ranking
def _universe_rows(path=None) -> list:
    from . import universe as universe_store
    payload = universe_store.load(path)
    if payload is None:
        raise AdapterError('no universe file; run `python harness.py universe sync '
                           '--markets US,KR` first (or POST /api/universe/sync)')
    return universe_store.investable(payload)


def ingested_tickers(as_of: str, packs_dir=None, runs_dir=None) -> set:
    """Listings a Stage 0 pack already exists for, in either market."""
    from .market_us import bulk as market_bulk
    found = set()
    for path in market_bulk.pack_paths(packs_dir or DEFAULT_PACK_DIR, runs_dir):
        pack = market_bulk._read_pack(path)
        if pack is None:
            continue
        ticker = str(pack.get('ticker') or path.stem).strip().upper()
        if ticker:
            found.add(ticker)
    return found


def rank(as_of: str, *, provider=None, config=None, markets=('US', 'KR'), limit=200,
         universe_path=None, packs_dir=None, runs_dir=None, include_ingested=False,
         transport=None, environ=None, market_root=None) -> dict:
    """Investable listings ordered by the session's dollar volume.

    `limit` bounds what comes back, not what was considered: the counts say how
    many listings the universe held and how many already have a pack, so a
    short list never reads as a small market.
    """
    from .market_us import bulk as market_bulk
    from .market_us.provider import UsHttpMarketDataProvider

    config = config or market_bulk.load_config()
    wanted = {str(m).upper() for m in markets}
    rows = [row for row in _universe_rows(universe_path)
            if (row.get('currency') == 'KRW' and 'KR' in wanted)
            or (row.get('currency') != 'KRW' and 'US' in wanted)]
    have = ingested_tickers(as_of, packs_dir, runs_dir)

    quotes, session, tried = {}, None, []
    quote_error, quote_source = None, None
    if 'US' in wanted:
        try:
            if provider is None:
                provider = UsHttpMarketDataProvider(config=config, transport=transport,
                                                    environ=environ)
            found = market_bulk.session_rows(as_of, provider, config)
            session, tried = found['session_date'], found['sessions_tried']
            quotes = {row['ticker']: row for row in found['rows']}
            quote_source = 'vendor'
        except AdapterError as error:
            quote_error = str(error)
        if not quotes:
            # One `fetch_day` already wrote close and volume for the whole
            # market. Re-fetching them to sort a list would spend a request to
            # learn what the disk knows — and when the vendor is unreachable,
            # falling back here is the difference between a ranked list and
            # none. Only listings already fetched are covered, and the answer
            # says so rather than implying the market is that small.
            local = market_bulk.local_session(as_of, market_root)
            if local['rows']:
                quotes, session = local['rows'], local['session_date']
                quote_source = 'local_csv'
        if not quotes and quote_error is None:
            quote_error = ('no quote for this session, from the vendor or from '
                           'data/market/US/')

    rewrite = config.get('regulator_ticker_rewrite')
    ranked, unranked = [], []
    for row in rows:
        ticker = str(row.get('ticker') or '').upper()
        # The same two spellings that split a quote lookup also split this
        # check, and getting it wrong re-ingests a company already on disk.
        already = ticker in have or alias_of(ticker, rewrite) in have
        if already and not include_ingested:
            continue
        entry = {'ticker': ticker, 'company_name': row.get('name'),
                 'exchange': row.get('exchange'), 'currency': row.get('currency'),
                 'jurisdiction': 'KR' if row.get('currency') == 'KRW' else 'US',
                 'requires_review': bool(row.get('requires_review')),
                 'already_ingested': already}
        quote, quoted_as = quote_for(ticker, quotes, rewrite)
        if quoted_as != ticker:
            entry['quoted_as'] = quoted_as
        if quote is None or quote.get('volume') is None or quote.get('close') is None:
            # A listing with no session quote is not ranked last; it is not
            # ranked. Sorting it to the bottom would read as "least liquid".
            entry['reason_unranked'] = (
                'KRX는 종목별 조회라 일괄 세션이 없다' if entry['jurisdiction'] == 'KR'
                else '시세 공급자에 닿지 못했고 디스크에도 없다' if quote_error and not quotes
                else '이 세션에 시세가 없다')
            unranked.append(entry)
            continue
        entry.update({'close': quote['close'], 'volume': quote['volume'],
                      'dollar_volume': quote['close'] * quote['volume']})
        ranked.append(entry)

    ranked.sort(key=lambda e: -e['dollar_volume'])
    for position, entry in enumerate(ranked, start=1):
        entry['rank'] = position
    return {
        'as_of_date': as_of,
        'session_date': session,
        'sessions_tried': tried,
        'markets': sorted(wanted),
        'ranked_by': 'dollar_volume' if quotes else None,
        'quote_source': quote_source,
        'quote_error': quote_error,
        'ranked_by_note': (config.get('selection') or {}).get('rank_note'),
        'is_not_evidence': (config.get('selection') or {}).get('is_not_evidence_note'),
        'universe_size': len(rows),
        'already_ingested': sum(1 for r in rows
                                if (str(r.get('ticker') or '').upper() in have
                                    or alias_of(str(r.get('ticker') or '').upper(),
                                                rewrite) in have)),
        'ranked_count': len(ranked),
        'unranked_count': len(unranked),
        'limit': limit,
        'candidates': ranked[:limit],
        'unranked': unranked[:limit],
    }


# ------------------------------------------------------------------ ingest
class IngestProblem(AdapterError):
    """One company's ingest failed, named. The batch keeps going."""


def _provider(market: str, transport=None, environ=None, corp_codes=None):
    from .credentials import regulator_provider
    return regulator_provider(market, transport=transport, environ=environ,
                              corp_codes=corp_codes)


def ingest_one(identifier: str, market: str, as_of: str, *, out_dir=None, force=False,
               transport=None, environ=None, provider=None, **kwargs) -> dict:
    """Build one Stage 0 pack and write it where `screen build --packs` reads.

    A pack that already exists is left alone unless `force` says otherwise:
    re-ingesting silently would replace facts a frozen run may already cite.
    """
    from .pack import validate_pack
    target_dir = Path(out_dir or DEFAULT_PACK_DIR)
    existing = target_dir / f'{identifier.strip().upper()}.json'
    if existing.exists() and not force:
        return {'ticker': identifier.strip().upper(), 'status': 'exists',
                'path': str(existing), 'note': 'pack already present; pass force to rebuild'}
    provider = provider or _provider(market, transport, environ)
    extra = {'years': kwargs['years']} if market.upper() == 'KR' and 'years' in kwargs else {}
    pack = provider.build_financial_pack(identifier, as_of, **extra)
    errors = validate_pack(pack)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f'{pack["ticker"].upper()}.json'
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {
        'ticker': pack['ticker'], 'company_name': pack.get('company_name'),
        'market': market.upper(), 'as_of_date': pack['as_of_date'],
        'status': 'validation_errors' if errors else 'ok',
        'documents': len(pack['documents']), 'facts': len(pack['facts']),
        'requires_review': sum(1 for f in pack['facts'] if f['requires_review']),
        'validation_errors': errors, 'path': str(path),
    }


def ingest_batch(tickers, market: str, as_of: str, *, out_dir=None, force=False,
                 max_companies: int = 10, transport=None, environ=None, **kwargs) -> dict:
    """Ingest several companies, reporting each outcome rather than the first failure.

    Bounded on purpose. Each company is several requests to a regulator that
    meters access, and a request handler that walks five thousand listings is a
    timeout with a half-finished directory behind it. Larger runs belong in the
    `ingest_pack` job kind, where a lease and a retry policy exist.
    """
    wanted = [str(t).strip().upper() for t in tickers if str(t).strip()]
    if not wanted:
        raise AdapterError('no tickers given')
    if len(wanted) > max_companies:
        raise AdapterError(f'{len(wanted)} companies in one call; the cap is {max_companies}. '
                           'Queue an `ingest_pack` job for a larger batch — it has a lease '
                           'and a retry policy, and this request would time out.')
    provider = _provider(market, transport, environ)
    results, failed = [], 0
    for ticker in wanted:
        try:
            results.append(ingest_one(ticker, market, as_of, out_dir=out_dir, force=force,
                                      provider=provider, **kwargs))
        except Exception as error:                  # one bad ticker is not the batch
            failed += 1
            results.append({'ticker': ticker, 'status': 'failed',
                            'error': f'{type(error).__name__}: {error}'})
    return {'as_of_date': as_of, 'market': market.upper(), 'requested': len(wanted),
            'written': sum(1 for r in results if r['status'] in ('ok', 'validation_errors')),
            'skipped_existing': sum(1 for r in results if r['status'] == 'exists'),
            'failed': failed, 'pack_dir': str(Path(out_dir or DEFAULT_PACK_DIR)),
            'results': results}
