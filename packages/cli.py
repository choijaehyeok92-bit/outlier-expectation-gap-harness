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


def _execute(spec, save, markdown_out=None):
    from packages.screening import compiler, runs_index, store
    rows = runs_index.load_rows()
    result = compiler.run(spec, rows)
    record = store.build_record(spec, result, rows_sha256=store.content_hash(
        [{k: v for k, v in row.items() if k != 'match_explain'} for row in rows]))
    if save:
        print(store.save(record), file=sys.stderr)
    if markdown_out:
        from packages.reporting import render_screen_markdown
        _write(markdown_out, render_screen_markdown(record))
    return record


def cmd_screen_query(args):
    from packages.screening import spec as spec_module
    spec = spec_module.normalise(json.loads(Path(args.spec).read_text(encoding='utf-8')))
    record = _execute(spec, args.save, args.markdown)
    _print(record if args.full else {**record, 'results': [
        {k: row.get(k) for k in ('ticker', 'company_name', 'jurisdiction', 'core_score', 'ex_valuation_score',
                                 'archetype', 'hard_veto_status', 'price_to_base_value', 'ic_state')}
        for row in record['results']]})


def cmd_screen_run(args):
    from packages.screening import nl
    provider = _provider(args.provider, args.model, args.fixtures) if args.provider != 'lexicon' else None
    spec = nl.parse(args.text, args.as_of, provider=provider, fx_rates=_fx_rates(args.fx, args.as_of))
    record = _execute(spec, not args.no_save, args.markdown)
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
    p.set_defaults(func=cmd_screen_run)

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
    return sub
