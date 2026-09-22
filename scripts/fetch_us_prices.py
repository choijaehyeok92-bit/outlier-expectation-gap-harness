#!/usr/bin/env python3
"""Fill `data/market/US/` so the screener can compute market-based metrics.

Why this exists: `market_cap`, `current_price` and `price_to_owner_fcf` are
`kind: market` in `config/screening_metrics.json`, and `missing_policy: exclude`
drops any company whose filter cannot be judged. With no US prices on disk,
every US listing falls out of a screen that mentions size or valuation — not
because it failed a test, but because nothing could be tested. Fifteen
companies can carry hand-entered prices in `company_context.json`; a universe
cannot.

One call fetches a whole session. `--scope packs` (the default) then writes only
the listings a Stage 0 pack exists for, because a price without financials
beside it is not a screenable row.

    export POLYGON_API_KEY=...                      # never passed as an argument
    python scripts/fetch_us_prices.py --as-of 2026-09-21
    python harness.py screen build --as-of 2026-09-21 --from-runs --market-data data/market

The key is read from the environment inside the provider. Nothing here accepts
one on the command line, where it would land in shell history and in `ps`.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_adapters.base import AdapterError                      # noqa: E402
from data_adapters.market_us import bulk, load_config            # noqa: E402
from data_adapters.market_us.provider import UsHttpMarketDataProvider  # noqa: E402


def build_provider(args, config):
    if not args.fixtures:
        return UsHttpMarketDataProvider(args.provider, config=config)
    # Replaying a recording reaches no vendor, so the auth gate has nothing to
    # protect. It stays strict for the live path; here it is handed a value
    # that is visibly not a credential rather than being switched off.
    from data_adapters.testing import FixtureTransport
    _, settings = bulk.provider_settings(config, args.provider)
    return UsHttpMarketDataProvider(
        args.provider, config=config, transport=FixtureTransport(args.fixtures),
        environ={settings['api_key_env']: 'offline-fixture-replay'})


def main(argv=None) -> int:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--as-of', required=True, metavar='YYYY-MM-DD',
                        help='cutoff. The last session at or before it is used; never after')
    parser.add_argument('--provider', default=None,
                        help=f"quote vendor declared in config/market_us.json "
                             f"(default: {config.get('default_provider')})")
    parser.add_argument('--scope', choices=('packs', 'universe', 'all'), default='packs',
                        help='packs: listings a Stage 0 pack exists for (default). '
                             'universe: investable listings from `universe sync`. '
                             'all: every listing the vendor returned')
    parser.add_argument('--tickers', help='comma-separated subset; overrides --scope')
    parser.add_argument('--packs', help='directory of Stage 0 packs from `harness.py ingest --out`')
    parser.add_argument('--out', help='market root (default: data/market)')
    parser.add_argument('--fixtures', help='replay recorded responses instead of calling a vendor')
    parser.add_argument('--dry-run', action='store_true',
                        help='fetch and report, write nothing')
    parser.add_argument('--quiet', action='store_true', help='summary only, no per-row output')
    args = parser.parse_args(argv)

    tickers = [t.strip() for t in (args.tickers or '').split(',') if t.strip()] or None
    try:
        result = bulk.fetch_day(
            args.as_of, provider=build_provider(args, config), config=config,
            tickers=tickers, scope=args.scope, packs_dir=args.packs,
            root=args.out, write=not args.dry_run)
    except AdapterError as error:
        print(f'{error}', file=sys.stderr)
        return 2

    if args.quiet:
        result = {k: v for k, v in result.items() if k not in ('written', 'files')}
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result['session_date'] is None:
        print(f"no trading session on or before {args.as_of} within "
              f"{config.get('max_session_lookback_days')} days", file=sys.stderr)
        return 1
    if result['missing_price']:
        # Not an error: the vendor genuinely does not cover every listing. It is
        # printed because a screen that silently loses companies is worse.
        print(f"{len(result['missing_price'])} listing(s) had no quote this session: "
              f"{', '.join(result['missing_price'][:20])}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
