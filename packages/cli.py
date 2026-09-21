"""Screening and deep-dive subcommands for the existing harness CLI.

These are additive. `harness.py` keeps every command it had, with the same
arguments and the same behaviour, and the modules those commands use keep their
standard-library-only diet: everything in here is imported lazily, inside the
handler, so running `harness.py aggregate` never loads the screening stack.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _print(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _write(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding='utf-8')
    print(path)


def _fx_rates(pairs, as_of_date):
    """--fx KRW=1380.2 → an explicit, attributed rate. Nothing is looked up."""
    rates = {}
    for pair in pairs or []:
        if '=' not in pair:
            raise SystemExit(f'--fx expects CODE=RATE_PER_USD, got {pair!r}')
        code, value = pair.split('=', 1)
        try:
            rates[code.strip().upper()] = {'per_usd': float(value), 'source': 'operator-supplied (--fx)',
                                           'as_of_date': as_of_date}
        except ValueError:
            raise SystemExit(f'--fx rate must be a number, got {value!r}')
    return rates


def _provider(name, model=None, fixtures=None):
    from packages.llm import resolve_provider
    if name == 'fixture':
        return resolve_provider('fixture', model, root=fixtures) if fixtures else resolve_provider('fixture', model)
    return resolve_provider(name, model)


def cmd_screen_fields(args):
    from packages.screening.fields import Registry
    rows = Registry().describe()
    if args.available_only:
        rows = [r for r in rows if r['available']]
    _print(rows)


def cmd_screen_nl(args):
    from packages.screening import nl
    provider = _provider(args.provider, args.model, args.fixtures) if args.provider != 'lexicon' else None
    spec = nl.parse(args.text, args.as_of, provider=provider, fx_rates=_fx_rates(args.fx, args.as_of))
    if args.out:
        _write(args.out, json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    else:
        _print(spec)


def _warehouse_entries_from_runs(runs_dir=None, tickers=None, as_of=None):
    """Stage 0 packs that existing runs already hold, with their frozen prices.

    A completed run carries a preprocessed pack and a frozen market
    observation. Reusing them means the warehouse can be built and checked
    against real disclosures rather than only against fixtures.
    """
    import json as _json
    from packages.screening import runs_index
    base = Path(runs_dir or runs_index.RUNS_DIR)
    entries, unreadable = [], []
    for run_id in runs_index.run_ids(runs_dir):
        run = base / run_id
        pack_path = run / 'sources' / 'financials' / 'normalized_financials.json'
        if not pack_path.exists():
            continue
        try:
            pack = _json.loads(pack_path.read_text(encoding='utf-8'))
            context = _json.loads((run / 'company_context.json').read_text(encoding='utf-8'))
        except ValueError as error:
            # A corrupt artifact is a finding, not something to pass over quietly.
            unreadable.append(f'{run_id}: {type(error).__name__} in '
                              f'{pack_path.relative_to(base)} ({error})')
            continue
        if not (pack.get('facts') or []):
            continue
        ticker = (context.get('ticker') or pack.get('ticker') or run_id).upper()
        if tickers and ticker not in tickers:
            continue
        run_as_of = context.get('as_of_date') or ''
        if as_of and run_as_of > as_of:
            continue            # a run dated after the cutoff is not evidence this cutoff had
        price, shares = context.get('current_price'), context.get('shares_diluted')
        snapshot = {'as_of_date': context.get('as_of_date'),
                    'source': f'runs/{run_id}/company_context.json (frozen)'}
        if isinstance(price, (int, float)):
            snapshot['close'] = float(price)
        if isinstance(shares, (int, float)):
            snapshot['shares_outstanding'] = float(shares)
        entries.append({
            'ticker': ticker, 'company_name': context.get('company_name'),
            'jurisdiction': 'KR' if (context.get('currency') or '').upper() == 'KRW' else 'US',
            'currency': context.get('currency') or pack.get('reporting_currency'),
            'pack': pack, 'market_snapshot': snapshot, 'run_id': run_id,
            'run_as_of': run_as_of})
    # One entry per ticker: several runs of the same company differ by policy
    # version, not by what the company disclosed.
    newest = {}
    for entry in sorted(entries, key=lambda e: (e['run_as_of'], e['run_id'])):
        newest[entry['ticker']] = entry
    return list(newest.values()), unreadable


def _warehouse_entries_from_packs(directory):
    import json as _json
    entries = []
    for path in sorted(Path(directory).glob('*.json')):
        pack = _json.loads(path.read_text(encoding='utf-8'))
        if not pack.get('facts'):
            continue
        entries.append({'ticker': (pack.get('ticker') or path.stem).upper(),
                        'company_name': pack.get('company_name'),
                        'jurisdiction': 'KR' if (pack.get('reporting_currency') or '') == 'KRW' else 'US',
                        'currency': pack.get('reporting_currency'),
                        'pack': pack, 'market_snapshot': {}, 'source_file': str(path)})
    return entries


def _attach_market_data(entries, root, as_of):
    """Fill each entry's market snapshot from a market provider, not from a filing.

    A regulator publishes what a company disclosed; a price is not one of those
    things. So the snapshot arrives through `MarketDataProvider`, and an entry
    with no market observation simply has no market-derived metric.
    """
    try:
        from data_adapters.market_kr.provider import KrMarketCsvProvider
        from data_adapters.market_us import UsMarketDataProvider
    except Exception:
        return 0
    providers = {'US': UsMarketDataProvider(root=root), 'KR': KrMarketCsvProvider(root=root)}
    attached = 0
    for entry in entries:
        if entry.get('market_snapshot'):
            continue
        provider = providers.get(entry.get('jurisdiction'))
        if provider is None:
            continue
        security = provider.resolve_security(entry['ticker'])
        snapshot = provider.get_snapshot(security, as_of)
        if snapshot is None:
            continue
        entry['market_snapshot'] = {k: v for k, v in snapshot.to_dict().items() if v is not None}
        attached += 1
    return attached


def cmd_screen_build(args):
    """Stage 2: compute the deterministic metric warehouse. No LLM is involved."""
    from packages.screening import warehouse
    entries, unreadable = [], []
    if args.packs:
        entries.extend(_warehouse_entries_from_packs(args.packs))
    if args.from_runs or not entries:
        tickers = {t.strip().upper() for t in (args.tickers or '').split(',') if t.strip()}
        from_runs, unreadable = _warehouse_entries_from_runs(tickers=tickers or None,
                                                             as_of=args.as_of)
        entries.extend(from_runs)
    if not entries:
        raise SystemExit('no Stage 0 packs found; pass --packs DIR or use --from-runs')
    attached = _attach_market_data(entries, args.market_data, args.as_of) if args.market_data else 0
    payload = warehouse.build(entries, args.as_of)
    payload['market_snapshots_attached'] = attached
    path = warehouse.save(payload, args.out)
    print(path, file=sys.stderr)
    coverage = {k: v for k, v in payload['coverage'].items()}
    _print({'as_of_date': payload['as_of_date'], 'companies': payload['companies'],
            'tickers': payload['tickers'], 'failures': payload['failures'],
            'unreadable_artifacts': unreadable,
            'market_snapshots_attached': attached, 'coverage': coverage})


def _execute(spec, save, markdown_out=None, source='auto'):
    from packages.screening import compiler, rows as row_source, store
    fx = spec.get('fx_rates') or {}
    rows = row_source.load_rows(spec.get('as_of_date'), fx_rates=fx, source=source)
    result = compiler.run(spec, rows)
    record = store.build_record(spec, result, rows_sha256=store.content_hash(
        [{k: v for k, v in row.items() if k != 'match_explain'} for row in rows]))
    record['backends'] = row_source.backend_summary(rows, source)
    if save:
        print(store.save(record), file=sys.stderr)
    if markdown_out:
        from packages.reporting import render_screen_markdown
        _write(markdown_out, render_screen_markdown(record))
    return record


def cmd_screen_query(args):
    from packages.screening import spec as spec_module
    spec = spec_module.normalise(json.loads(Path(args.spec).read_text(encoding='utf-8')))
    record = _execute(spec, args.save, args.markdown, getattr(args, 'source', 'auto'))
    _print(record if args.full else {**record, 'results': [
        {k: row.get(k) for k in ('ticker', 'company_name', 'jurisdiction', 'core_score', 'ex_valuation_score',
                                 'archetype', 'hard_veto_status', 'price_to_base_value', 'ic_state')}
        for row in record['results']]})


def cmd_screen_run(args):
    from packages.screening import nl
    provider = _provider(args.provider, args.model, args.fixtures) if args.provider != 'lexicon' else None
    spec = nl.parse(args.text, args.as_of, provider=provider, fx_rates=_fx_rates(args.fx, args.as_of))
    record = _execute(spec, not args.no_save, args.markdown, getattr(args, 'source', 'auto'))
    _print({'screen_run_id': record['screen_run_id'],
            'unresolved_conditions': spec['unresolved_conditions'],
            'requires_harness_run': spec['requires_harness_run'],
            'matched_count': record['summary']['matched_count'],
            'excluded_missing_data': record['summary']['excluded_missing_data'],
            'results': [{k: row.get(k) for k in ('ticker', 'company_name', 'jurisdiction', 'core_score',
                                                 'archetype', 'hard_veto_status', 'price_to_base_value')}
                        for row in record['results']]})


def cmd_screen_runs(args):
    from packages.screening import store
    _print(store.list_runs())


def cmd_deep_plan(args):
    from packages.research import deep_plan
    plan = deep_plan.build(args.ticker.upper() if not args.ticker.isdigit() else args.ticker,
                           user_requested=args.force)
    if args.out:
        _write(args.out, json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    else:
        _print(plan)


def cmd_deep_run(args):
    from packages.llm import LLMError
    from packages.research import deep_run
    run_id = args.ticker.upper() if not args.ticker.isdigit() else args.ticker
    fixtures = args.fixtures or (ROOT / 'packages' / 'research' / 'fixtures' / run_id)
    try:
        report, _plan, path = deep_run.run(run_id, _provider(args.provider, args.model, fixtures),
                                           user_requested=args.force)
    except LLMError as error:
        raise SystemExit(str(error))
    print(path, file=sys.stderr)
    if args.markdown:
        from packages.reporting import render_markdown
        _write(args.markdown, render_markdown(report))
    _print({'deep_dive_id': report['metadata']['deep_dive_id'],
            'ticker': report['metadata']['ticker'],
            'harness_run': report['metadata']['harness_run']['run_id'],
            'red_team_overall': report['red_team']['overall'],
            'agreement_with_harness': report['final_synthesis']['agreement_with_harness'],
            'evidence_count': len(report['evidence']),
            'stages': report['metadata']['provenance']['stages']})


def cmd_deep_report(args):
    from packages.reporting import render_markdown
    from packages.research import store
    report = store.load(args.deep_dive_id)
    if report is None:
        raise SystemExit(f'{args.deep_dive_id}: no such deep dive')
    text = render_markdown(report)
    if args.out:
        _write(args.out, text)
    else:
        print(text)


def cmd_deep_list(args):
    from packages.research import store
    _print(store.list_reports())


def register(sub):
    """Attach the screening and deep-dive commands to an existing subparser set."""
    screen = sub.add_parser('screen', help='US/KR screening over the completed harness run corpus')
    screen_sub = screen.add_subparsers(dest='screen_cmd', required=True)

    p = screen_sub.add_parser('fields', help='list the field identifiers a ScreeningSpec may name')
    p.add_argument('--available-only', action='store_true')
    p.set_defaults(func=cmd_screen_fields)

    p = screen_sub.add_parser('nl', help='natural language -> validated ScreeningSpec (no SQL, no metrics)')
    p.add_argument('text')
    p.add_argument('--as-of', required=True)
    p.add_argument('--provider', default='lexicon',
                   help='lexicon (deterministic, offline) | fixture | anthropic | openai')
    p.add_argument('--model')
    p.add_argument('--fixtures')
    p.add_argument('--fx', action='append', metavar='CODE=PER_USD',
                   help='explicit as-of FX rate, e.g. --fx KRW=1380.2; never looked up automatically')
    p.add_argument('--out')
    p.set_defaults(func=cmd_screen_nl)

    p = screen_sub.add_parser('query', help='execute a ScreeningSpec file')
    p.add_argument('--spec', required=True)
    p.add_argument('--save', action='store_true', help='persist an immutable screen run')
    p.add_argument('--markdown')
    p.add_argument('--full', action='store_true')
    p.add_argument('--source', choices=['auto', 'files', 'db'], default='auto',
                   help='where rows come from; db needs $HARNESS_DATABASE_URL')
    p.set_defaults(func=cmd_screen_query)

    p = screen_sub.add_parser('run', help='parse and execute in one step')
    p.add_argument('text')
    p.add_argument('--as-of', required=True)
    p.add_argument('--provider', default='lexicon')
    p.add_argument('--model')
    p.add_argument('--fixtures')
    p.add_argument('--fx', action='append', metavar='CODE=PER_USD')
    p.add_argument('--markdown')
    p.add_argument('--no-save', action='store_true')
    p.add_argument('--source', choices=['auto', 'files', 'db'], default='auto',
                   help='where rows come from; db needs $HARNESS_DATABASE_URL')
    p.set_defaults(func=cmd_screen_run)

    p = screen_sub.add_parser('build', help='stage 2: compute the deterministic metric warehouse')
    p.add_argument('--as-of', required=True)
    p.add_argument('--packs', help='directory of Stage 0 packs from `harness.py ingest --out`')
    p.add_argument('--from-runs', action='store_true',
                   help='use the packs completed runs already hold')
    p.add_argument('--tickers', help='comma-separated subset')
    p.add_argument('--market-data', help='market CSV root (data/market/<US|KR>/<TICKER>.csv); '
                                         'prices never come from a regulator')
    p.add_argument('--out')
    p.set_defaults(func=cmd_screen_build)

    p = screen_sub.add_parser('runs', help='list persisted screen runs')
    p.set_defaults(func=cmd_screen_runs)

    p = sub.add_parser('deep-plan', help='build a deep-dive plan from a completed harness run')
    p.add_argument('ticker')
    p.add_argument('--force', action='store_true', help='request a deep dive the automatic policy did not select')
    p.add_argument('--out')
    p.set_defaults(func=cmd_deep_plan)

    p = sub.add_parser('deep-run', help='run research, qualitative analysis, red team and synthesis')
    p.add_argument('ticker')
    p.add_argument('--provider', default='fixture')
    p.add_argument('--model')
    p.add_argument('--fixtures')
    p.add_argument('--force', action='store_true')
    p.add_argument('--markdown')
    p.set_defaults(func=cmd_deep_run)

    p = sub.add_parser('deep-report', help='render a stored deep dive as markdown')
    p.add_argument('deep_dive_id')
    p.add_argument('--out')
    p.set_defaults(func=cmd_deep_report)

    p = sub.add_parser('deep-list', help='list stored deep dives')
    p.set_defaults(func=cmd_deep_list)

    _register_data_adapters(sub)
    _register_database(sub)
    return sub


def _register_database(sub):
    """Database commands, when SQLAlchemy is installed.

    The database is optional. A checkout without it keeps every other command,
    and nothing else in the platform reads from it unless asked.
    """
    try:
        from db import cli as database_cli
    except Exception:
        return None
    return database_cli.register(sub)


def _register_data_adapters(sub):
    """SEC/DART ingestion commands, when the adapters are installed.

    They carry their own dependencies (PyYAML for the Korean account map), so a
    checkout without them keeps every other command rather than failing at
    argument-parsing time.
    """
    try:
        from data_adapters import cli as adapters_cli
    except Exception:
        return None
    return adapters_cli.register(sub)
