"""`universe` and `ingest` subcommands.

These are additive to the existing harness CLI and import lazily, so a
checkout without PyYAML or without the adapters keeps every command it had.

Nothing here writes into an existing run. `ingest` produces a Stage 0 financial
pack and, unless told otherwise, prints where it would go rather than
overwriting a frozen run's sources — a frozen run is frozen.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'data_adapters' / 'fixtures'
EMPTY_DART = {'status': '013', 'message': '조회된 데이타가 없습니다.'}


def _print(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _transport(args, vendor):
    """A fixture transport when `--fixtures` is given, else the live one.

    `--fixtures` names a base directory holding one subdirectory per vendor, so
    a single flag can serve a sync that touches both regulators.
    """
    if not getattr(args, 'fixtures', None):
        return None
    from .testing import FixtureTransport
    base = Path(args.fixtures)
    if not base.exists() and not base.is_absolute():
        base = FIXTURES / args.fixtures
    root = base / vendor if (base / vendor).is_dir() else base
    return FixtureTransport(root, default=EMPTY_DART if vendor == 'dart' else None)


def _sec_provider(args):
    from .sec import SecEdgarProvider
    return SecEdgarProvider(user_agent=getattr(args, 'user_agent', None)
                            or os.environ.get('SEC_USER_AGENT'),
                            transport=_transport(args, 'sec'))


def _dart_provider(args, refresh_corp_codes=False):
    from .dart import DartProvider
    from .dart.corpcode import CorpCodeCache, parse_corp_code_zip
    transport = _transport(args, 'dart')
    provider = DartProvider(api_key=getattr(args, 'api_key', None), transport=transport,
                            corp_codes=CorpCodeCache(path=getattr(args, 'corp_codes', None)))
    if refresh_corp_codes or not provider.corp_codes.entries:
        payload = provider.client.get(provider._url('corp_code'),
                                      {'crtfc_key': provider._require_key()})
        provider.corp_codes.refresh(payload)
        provider.corp_codes.save()
    return provider


def cmd_universe_sync(args):
    from . import universe
    markets = [m.strip().upper() for m in (args.markets or 'US,KR').split(',') if m.strip()]
    providers, kwargs = {}, {}
    if 'US' in markets:
        providers['US'] = _sec_provider(args)
    if 'KR' in markets:
        providers['KR'] = _dart_provider(args, refresh_corp_codes=args.refresh_corp_codes)
        kwargs['KR'] = {'enrich_limit': args.enrich_limit}
    if not providers:
        raise SystemExit(f'no known market in --markets {args.markets!r}; use US and/or KR')
    payload = universe.sync(providers, as_of_date=args.as_of, **kwargs)
    path = universe.save(payload, args.out)
    print(path)
    _print({'summary': payload['summary'], 'markets': payload['markets'],
            'errors': payload['errors']})


def cmd_universe_show(args):
    from . import universe
    payload = universe.load(args.path)
    if payload is None:
        raise SystemExit('no universe file; run `harness.py universe sync` first')
    rows = universe.investable(payload) if args.investable_only else payload['securities']
    if args.market:
        wanted = args.market.upper()
        rows = [r for r in rows if r['currency'] == ('KRW' if wanted == 'KR' else 'USD')]
    _print({'synced_at_utc': payload['synced_at_utc'], 'summary': payload['summary'],
            'count': len(rows), 'securities': rows[:args.limit]})


def cmd_ingest(args):
    from .pack import validate_pack
    provider = _dart_provider(args) if args.market.upper() == 'KR' else _sec_provider(args)
    pack = provider.build_financial_pack(args.identifier, args.as_of, **(
        {'years': args.years} if args.market.upper() == 'KR' else {}))
    errors = validate_pack(pack)
    summary = {
        'ticker': pack['ticker'], 'company_name': pack.get('company_name'),
        'as_of_date': pack['as_of_date'], 'documents': len(pack['documents']),
        'facts': len(pack['facts']),
        'requires_review': sum(1 for f in pack['facts'] if f['requires_review']),
        'ingestion': {k: v for k, v in pack['ingestion'].items() if k != 'capital_events'},
        'validation_errors': errors,
    }
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(target)
    else:
        # A frozen run's sources are frozen; say where this would go instead of
        # writing into one.
        summary['suggested_path'] = f'runs/{pack["ticker"]}/sources/financials/normalized_financials.json'
        summary['note'] = ('Pass --out to write. The ingester never overwrites a run\'s sources; '
                           'review the pack, then place it and re-run Stage 0 validation.')
    _print(summary)
    if errors:
        raise SystemExit(1)


def register(sub):
    universe_parser = sub.add_parser('universe', help='US/KR listed universe from SEC and DART')
    universe_sub = universe_parser.add_subparsers(dest='universe_cmd', required=True)

    p = universe_sub.add_parser('sync', help='build the investable universe from the regulators')
    p.add_argument('--markets', default='US,KR')
    p.add_argument('--as-of')
    p.add_argument('--out')
    p.add_argument('--user-agent', help='SEC fair-access contact; else $SEC_USER_AGENT')
    p.add_argument('--api-key', help='OpenDART key; else $OPENDART_API_KEY')
    p.add_argument('--corp-codes', help='corpCode cache path')
    p.add_argument('--refresh-corp-codes', action='store_true')
    p.add_argument('--enrich-limit', type=int, default=0,
                   help='how many KR issuers to look up for their market segment (corp_cls)')
    p.add_argument('--fixtures', nargs='?', const=str(FIXTURES),
                   help='replay recorded responses instead of calling the regulators; '
                        'optionally a base directory holding sec/ and dart/')
    p.set_defaults(func=cmd_universe_sync)

    p = universe_sub.add_parser('show', help='read the persisted universe')
    p.add_argument('--path')
    p.add_argument('--market')
    p.add_argument('--investable-only', action='store_true')
    p.add_argument('--limit', type=int, default=25)
    p.set_defaults(func=cmd_universe_show)

    p = sub.add_parser('ingest', help='build a Stage 0 financial pack from SEC or DART')
    p.add_argument('identifier', help='ticker, CIK, or 종목코드')
    p.add_argument('--market', required=True, choices=['US', 'KR', 'us', 'kr'])
    p.add_argument('--as-of', required=True)
    p.add_argument('--years', type=int, default=4)
    p.add_argument('--out')
    p.add_argument('--user-agent')
    p.add_argument('--api-key')
    p.add_argument('--corp-codes')
    p.add_argument('--fixtures', nargs='?', const=str(FIXTURES))
    p.set_defaults(func=cmd_ingest)
    return sub
