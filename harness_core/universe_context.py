"""`universe context`: operator-supplied Stage 0 lock fields for many tickers at once.

The harness never looks up or estimates a price. The operator fills a CSV
(`universe context --template`) or passes values on the command line, and this
command writes them where Stage 0 reads them:

* run exists, not frozen   -> runs/<RUN>/company_context.json
* run does not exist yet   -> .harness_inputs/<RUN>/company_context.json (staged, copied at Stage 0)
* run already frozen       -> refused: a frozen snapshot is never edited; use a new as-of or fork-run

freeze still validates the full context against the schema afterwards.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path

from . import universe as U
from .universe_store import RunReader, Store, atomic_dump_json, utcnow

FIELDS = ('current_price', 'net_cash_per_share', 'shares_diluted', 'market_cap_usd', 'currency', 'company_name')
REQUIRED = ('current_price', 'net_cash_per_share')
NUMERIC = ('current_price', 'net_cash_per_share', 'shares_diluted', 'market_cap_usd')


def parse_values(raw):
    """Clean one row of operator input. Returns (values, errors). Pure."""
    values, errors = {}, []
    for key in FIELDS:
        text = raw.get(key)
        if text is None or str(text).strip() == '':
            continue
        if key in NUMERIC:
            try:
                number = float(str(text).replace(',', '').strip())
            except ValueError:
                errors.append(f'{key}: not a number ({text!r})')
                continue
            if not math.isfinite(number):
                errors.append(f'{key}: not finite')
            elif key in ('current_price', 'shares_diluted', 'market_cap_usd') and number <= 0:
                errors.append(f'{key}: must be positive')
            else:
                values[key] = number
        else:
            values[key] = str(text).strip()
    missing = [k for k in REQUIRED if k not in values]
    if missing:
        errors.append('missing ' + ', '.join(missing))
    return values, errors


def apply_values(context, values, source_note):
    """Merge operator values into a context dict. Pure."""
    out = json.loads(json.dumps(context))
    out.update(values)
    if source_note:
        known = list(out.get('known_sources') or [])
        if source_note not in known:
            known.append(source_note)
        out['known_sources'] = known
    return out


def target_for(runtime, root, row, staged_dir):
    """(path, kind, problem) where the lock fields for this row belong."""
    run_id = row.get('run_id') or row['ticker']
    run = runtime.run_dir(run_id)
    if run.exists():
        manifest = run/'run_manifest.json'
        if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')).get('frozen'):
            return None, 'frozen', f'{run_id} is frozen; a frozen snapshot is never edited (import a new --as-of or fork-run)'
        return run/'company_context.json', 'run', None
    return Path(root)/staged_dir/run_id/'company_context.json', 'staged', None


def write_values(runtime, store, row, values, source_note):
    path, kind, problem = target_for(runtime, store.root, row, store.policy['paths']['staged_inputs_dir'])
    if problem:
        return {'ticker': row['ticker'], 'status': 'REFUSED', 'reason': problem}
    if path.exists():
        context = json.loads(path.read_text(encoding='utf-8'))
    else:
        context = json.loads((runtime.ROOT/'templates/company_context.json').read_text(encoding='utf-8'))
        context.update(ticker=row.get('run_id') or row['ticker'], as_of_date=row['as_of_date'])
    run_id = row.get('run_id') or row['ticker']
    if str(context.get('ticker') or '').upper() != run_id.upper() or context.get('as_of_date') != row['as_of_date']:
        return {'ticker': row['ticker'], 'status': 'REFUSED',
                'reason': f"{path} is for {context.get('ticker')} / {context.get('as_of_date')}, not {run_id} / {row['as_of_date']}"}
    atomic_dump_json(path, apply_values(context, values, source_note))
    return {'ticker': row['ticker'], 'status': 'WRITTEN', 'target': kind,
            'path': path.relative_to(store.root).as_posix()}


def template_rows(rows):
    """Tickers still waiting for Stage 0 lock fields (and not ETFs/funds)."""
    return [r for r in rows if r.get('security_type') not in ('etf', 'fund') and r.get('run_status') != 'COMPLETE'
            and (r.get('stage') in (None, 'stage0'))]


def _runtime():
    from . import runtime
    return runtime


def cmd_context(args):
    h = _runtime()
    store = Store(h.ROOT)
    universe = store.load()
    rows = universe['tickers']
    if args.template:
        chosen = template_rows(Store.ordered(universe))
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator='\n')
        writer.writerow(['ticker', 'as_of', *FIELDS])
        for r in chosen:
            writer.writerow([r['ticker'], r['as_of_date'], '', '', '', '', '', r.get('company_name') or ''])
        Path(args.template).write_text(buffer.getvalue(), encoding='utf-8')
        print(f'{args.template}: {len(chosen)} ticker(s) awaiting current_price / net_cash_per_share')
        return
    note = args.source or f'operator-supplied lock fields via `universe context` ({utcnow()[:10]})'
    entries = []
    if args.file:
        with open(args.file, encoding='utf-8-sig', newline='') as handle:
            for line in csv.DictReader(handle):
                entries.append({k.strip().lower(): v for k, v in line.items() if k})
    elif args.ticker:
        entries.append({'ticker': args.ticker, 'current_price': args.price, 'net_cash_per_share': args.net_cash_per_share,
                        'shares_diluted': args.shares_diluted, 'market_cap_usd': args.market_cap_usd,
                        'currency': args.currency, 'company_name': args.company_name})
    else:
        raise SystemExit('pass a CSV file, a TICKER with --price/--net-cash-per-share, or --template OUT.csv')
    results, bad = [], 0
    for entry in entries:
        ticker, _, reason = U.normalize_ticker(entry.get('ticker'), store.policy['import'])
        if reason or ticker not in rows:
            results.append({'ticker': entry.get('ticker'), 'status': 'REFUSED', 'reason': 'not in the universe'})
            bad += 1
            continue
        if entry.get('as_of') and entry['as_of'] != rows[ticker]['as_of_date']:
            results.append({'ticker': ticker, 'status': 'REFUSED',
                            'reason': f"as_of {entry['as_of']} != universe {rows[ticker]['as_of_date']}"})
            bad += 1
            continue
        values, errors = parse_values(entry)
        if errors:
            results.append({'ticker': ticker, 'status': 'REFUSED', 'reason': '; '.join(errors)})
            bad += 1
            continue
        result = write_values(h, store, rows[ticker], values, note)
        bad += result['status'] != 'WRITTEN'
        results.append(result)
    for r in results:
        print(f"  {r['ticker']:<8} {r['status']:<8} {r.get('path') or r.get('reason')}")
    print(f"universe context: {sum(r['status'] == 'WRITTEN' for r in results)} written, {bad} refused")
    if bad:
        raise SystemExit(1)


def register(us):
    p = us.add_parser('context', help='write operator-supplied Stage 0 lock fields (price, net cash per share, ...)')
    p.add_argument('file', nargs='?', help=f"CSV with ticker[,as_of],{','.join(FIELDS)}")
    p.add_argument('--template', metavar='OUT.csv', help='write a CSV of tickers still awaiting lock fields')
    p.add_argument('--ticker'); p.add_argument('--price'); p.add_argument('--net-cash-per-share')
    p.add_argument('--shares-diluted'); p.add_argument('--market-cap-usd'); p.add_argument('--currency')
    p.add_argument('--company-name')
    p.add_argument('--source', help='provenance note appended to company_context.known_sources')
    p.set_defaults(func=cmd_context)
