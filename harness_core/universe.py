"""Universe index: pure logic only.

The universe is an index over `runs/<RUN_ID>/`. Every decision number in a row is
copied from `final_verdict.json` (or, before a run is finalized, from
`aggregate.json`) and carries the path it came from. Nothing in this module
scores, classifies, ranks by merit or sizes a position. It parses ticker
lists, merges them into the index, summarizes recorded artifacts, derives a
lifecycle status and filters/sorts rows descriptively. File IO lives in
`universe_store.py`; batch execution in `universe_runner.py`.

Screen names imported from a screener (for example a StockAnalysis screen the
investor called "compounder") are provenance labels. They are never read as an
archetype: the archetype comes only from the harness's deterministic gates.
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date

RUN_STATUSES = ('QUEUED', 'RUNNING', 'FAILED', 'BLOCKED', 'COMPLETE')
TERMINAL = ('COMPLETE',)
CSV_COLUMNS = ['ticker', 'score', 'score_ex_ev', 'archetype', 'fit', 'ev', 'as', 'di', 'fs', 'price_to_base',
               'hard_veto', 'mechanical_state', 'ic_state', 'position_range', 'macro_pacing', 'status', 'as_of']

ROW_DEFAULTS = {
    'ticker': None, 'run_id': None, 'company_name': None,
    'source': None, 'sources': [], 'screen_name': None, 'screens': [],
    'security_type': 'unknown', 'security_type_source': None, 'exchange': None,
    'imported_at': None, 'last_imported_at': None, 'as_of_date': None, 'queue_seq': None,
    'run_status': 'QUEUED', 'stage': 'stage0', 'started': False,
    'score': None, 'score_ex_valuation': None, 'coverage_weight': None, 'classification': None,
    'archetype': None, 'archetype_fit': None, 'secondary_archetypes': [], 'reachable_archetypes': None,
    'domain_scores': {},
    'hard_veto_status': None, 'mechanical_pre_ic_state': None, 'ic_state': None, 'ic_complete': False,
    'position_range': None, 'position_range_source': None, 'position_range_pre_ic': None,
    'macro_pacing': None, 'price_to_base': None, 'current_price': None,
    'valuation': None, 'early_exit': False, 'early_exit_stage': None, 'last_reachable_archetypes': None,
    'review_only': False, 'reconstructed': False,
    'decision_policy_version': None, 'verdict_source': None,
    'report_status': 'NONE', 'report_tier': None,
    'blocked_reason': None, 'awaiting': [], 'last_error': None, 'attempts': 0,
    'previous_runs': [], 'source_files': {}, 'source_hashes': {},
    'last_synced_at': None, 'last_updated': None,
}

# Fields whose value is copied from run artifacts; a sync replaces all of them together.
SYNCED_FIELDS = ('score', 'score_ex_valuation', 'coverage_weight', 'classification', 'archetype', 'archetype_fit',
                 'secondary_archetypes', 'reachable_archetypes', 'domain_scores', 'hard_veto_status',
                 'mechanical_pre_ic_state', 'ic_state', 'ic_complete', 'position_range', 'position_range_source',
                 'position_range_pre_ic', 'macro_pacing', 'price_to_base', 'current_price', 'valuation',
                 'early_exit', 'early_exit_stage', 'last_reachable_archetypes', 'review_only', 'reconstructed',
                 'decision_policy_version', 'verdict_source', 'source_files', 'source_hashes', 'report_status',
                 'report_tier')


class ImportError_(ValueError):
    """Raised for an unreadable import file (not for individual bad tickers)."""


# ---------------------------------------------------------------- tickers

def valid_as_of(value):
    try:
        return date.fromisoformat(str(value)).isoformat() == str(value)
    except ValueError:
        return False


def normalize_ticker(raw, policy):
    """Return (ticker, exchange, reason). ticker is None when the input is rejected.

    Uppercases, strips whitespace and a leading `$`, splits an `EXCHANGE:` prefix,
    and writes share classes with a dot (BRK-B, BRK/B -> BRK.B) so one company has
    one identifier. Anything that still does not look like a listed ticker is
    rejected rather than guessed at.
    """
    text = str(raw or '').strip().strip('"\'').strip()
    if not text:
        return None, None, 'empty'
    text = text.lstrip('$').strip()
    exchange = None
    if ':' in text:
        prefix, _, rest = text.partition(':')
        if prefix.strip().upper() in {p.upper() for p in policy.get('exchange_prefixes', [])}:
            exchange, text = prefix.strip().upper(), rest.strip()
        else:
            return None, None, f'unknown exchange prefix {prefix.strip()!r}'
    ticker = re.sub(r'\s+', '', text).upper()
    ticker = re.sub(r'(?<=[A-Z])[-/](?=[A-Z0-9]{1,3}$)', '.', ticker)
    if not any(re.fullmatch(p, ticker) for p in policy['ticker_patterns']):
        return None, exchange, f'not a ticker: {str(raw).strip()!r}'
    return ticker, exchange, None


def detect_security_type(ticker, name, declared, policy):
    """(type, source). Only explicit evidence marks a fund; absence of evidence stays 'unknown'."""
    if declared:
        value = str(declared).strip().lower()
        if value in policy.get('fund_type_values', []):
            return ('etf' if 'et' in value else 'fund'), 'import_column'
        if value in ('stock', 'equity', 'common stock', 'common', 'adr', 'reit', 'shares'):
            return 'equity', 'import_column'
    if ticker in set(policy.get('known_funds', [])):
        return 'etf', 'known_fund_list'
    if name and re.search(policy.get('fund_name_pattern', r'$^'), str(name), re.I):
        return ('etf' if re.search(r'\bET[FN]S?\b', str(name), re.I) else 'fund'), 'company_name'
    return 'unknown', None


# ---------------------------------------------------------------- parsing

def _split_screens(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [s.strip() for s in re.split(r'[;|]', str(value)) if s.strip()]


def _ticker_and_name(text):
    if not re.search(r'\s', text.strip()):
        return text.strip().rstrip(':-–|'), None     # a single token, possibly EXCHANGE:TICKER
    match = re.match(r'^\s*(\$?[A-Za-z0-9./\-]+(?::[A-Za-z0-9./\-]+)?)\s*(?:[-–:|\t]\s*|\s+)(.*\S)\s*$', text)
    if match:
        return match.group(1), match.group(2)
    return text.strip().rstrip(':-–|').strip(), None


def parse_txt(text):
    """One ticker per line, optionally followed by a company name.

    `LLY`, `LLY - Eli Lilly`, `LLY: Eli Lilly` and `LLY<TAB>Eli Lilly` are all
    one ticker. Several tickers share a line only when separated by commas or
    semicolons (`LLY, NU, CRWD`); whitespace alone never splits tickers, so a
    vision-extracted "LLY ELI LILLY AND CO" cannot become tickers ELI and LILLY.
    """
    entries = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in re.split(r'[,;]', line) if p.strip()]
        line_entries = []
        for part in parts:
            ticker, name = _ticker_and_name(part)
            if line_entries and len(parts) > 1 and re.search(r'\s', part):
                line_entries[-1].setdefault('company_name', part)   # "LLY, Eli Lilly"
                continue
            entry = {'raw': ticker, 'line': number}
            if name:
                entry['company_name'] = name
            line_entries.append(entry)
        entries += line_entries
    return entries


def parse_csv(text, policy):
    lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    if not lines:
        return []
    delimiter = next((d for d in ('\t', ',', ';', '|') if d in lines[0]), ',')
    rows = list(csv.reader(io.StringIO('\n'.join(lines)), delimiter=delimiter))
    header = [c.strip().lower() for c in rows[0]]

    def column(names):
        return next((header.index(n) for n in names if n in header), None)
    ticker_col = column(policy['ticker_columns'])
    entries = []
    if ticker_col is None:
        # Headerless: ticker[, screen]
        for number, row in enumerate(rows, 1):
            if row and row[0].strip():
                entries.append({'raw': row[0], 'screens': _split_screens(row[1]) if len(row) > 1 else [],
                                'line': number})
        return entries
    screen_col, name_col = column(policy['screen_columns']), column(policy['name_columns'])
    type_col, exchange_col = column(policy['type_columns']), column(policy['exchange_columns'])
    used = {c for c in (ticker_col, screen_col, name_col, type_col, exchange_col) if c is not None}
    for number, row in enumerate(rows[1:], 2):
        if not row or ticker_col >= len(row) or not row[ticker_col].strip():
            continue
        cell = lambda c: row[c].strip() if c is not None and c < len(row) and row[c].strip() else None
        extra = {rows[0][i].strip(): v.strip() for i, v in enumerate(row)
                 if i not in used and i < len(rows[0]) and rows[0][i].strip() and v.strip()}
        entries.append({'raw': row[ticker_col], 'screens': _split_screens(cell(screen_col)),
                        'company_name': cell(name_col), 'security_type': cell(type_col),
                        'exchange': cell(exchange_col), 'screener_fields': extra, 'line': number})
    return entries


def parse_json(text):
    try:
        data = json.loads(text)
    except ValueError as error:
        raise ImportError_(f'invalid JSON: {error}') from error
    entries = []

    def add(item, screens=()):
        if isinstance(item, str):
            entries.append({'raw': item, 'screens': list(screens)})
        elif isinstance(item, dict):
            raw = item.get('ticker') or item.get('symbol')
            own = _split_screens(item.get('screens') or item.get('screen') or item.get('screen_name'))
            entries.append({'raw': raw, 'screens': list(dict.fromkeys([*screens, *own])),
                            'company_name': item.get('company_name') or item.get('name'),
                            'security_type': item.get('security_type') or item.get('type'),
                            'exchange': item.get('exchange')})
        else:
            raise ImportError_(f'unsupported JSON entry: {item!r}')
    if isinstance(data, list):
        for item in data:
            add(item)
    elif isinstance(data, dict) and isinstance(data.get('screens'), dict):
        for screen, items in data['screens'].items():
            for item in items:
                add(item, [screen])
    elif isinstance(data, dict) and isinstance(data.get('tickers'), list):
        screens = _split_screens(data.get('screen') or data.get('screen_name'))
        for item in data['tickers']:
            add(item, screens)
    else:
        raise ImportError_('JSON must be a list, {"tickers": [...]} or {"screens": {name: [...]}}')
    return entries


def parse_import(text, fmt, policy):
    fmt = fmt.lower().lstrip('.')
    if fmt == 'json':
        return parse_json(text)
    if fmt in ('csv', 'tsv'):
        return parse_csv(text, policy)
    return parse_txt(text)


def normalize_entries(entries, policy, default_screens=()):
    """Normalize, reject and de-duplicate one import. Pure."""
    accepted, rejected, duplicates = {}, [], []
    for entry in entries:
        ticker, exchange, reason = normalize_ticker(entry.get('raw'), policy)
        if reason:
            rejected.append({'input': entry.get('raw'), 'line': entry.get('line'), 'reason': reason})
            continue
        screens = list(dict.fromkeys([*(entry.get('screens') or []), *default_screens]))
        if ticker in accepted:
            duplicates.append(ticker)
            row = accepted[ticker]
            row['screens'] = list(dict.fromkeys([*row['screens'], *screens]))
            row['company_name'] = row['company_name'] or entry.get('company_name')
            continue
        kind, kind_source = detect_security_type(ticker, entry.get('company_name'), entry.get('security_type'), policy)
        accepted[ticker] = {'ticker': ticker, 'screens': screens, 'company_name': entry.get('company_name'),
                            'exchange': exchange or entry.get('exchange'), 'security_type': kind,
                            'security_type_source': kind_source, 'screener_fields': entry.get('screener_fields') or {}}
    return list(accepted.values()), rejected, duplicates


def new_row(ticker, as_of, run_id, source, now):
    row = json.loads(json.dumps(ROW_DEFAULTS))
    row.update(ticker=ticker, run_id=run_id, as_of_date=as_of, source=source, sources=[source],
               imported_at=now, last_imported_at=now, last_updated=now)
    return row


def reset_decision_fields(row):
    for key in SYNCED_FIELDS:
        row[key] = json.loads(json.dumps(ROW_DEFAULTS[key]))
    row.update(run_status='QUEUED', stage='stage0', started=False, report_status='NONE', report_tier=None,
               blocked_reason=None, awaiting=[], last_error=None, attempts=0, last_synced_at=None)


def run_id_for(ticker, as_of, run_as_of):
    """Existing convention: `runs/<TICKER>` first, then `runs/<TICKER>-<AS_OF>` for later snapshots.

    `run_as_of(run_id)` returns the as_of_date recorded by that run, or None when
    the run does not exist. A frozen run for another date is never reused or
    overwritten; a dated run id that already holds a different date is a conflict.
    """
    existing = run_as_of(ticker)
    if existing in (None, as_of):
        return ticker, None
    dated = f'{ticker}-{as_of}'
    held = run_as_of(dated)
    if held not in (None, as_of):
        return None, f'{dated} already holds as_of {held}'
    return dated, None


def merge_import(universe, entries, as_of, source, now, run_as_of, run_id_override=None):
    """Merge normalized entries into the universe dict. Returns (universe, report). Pure given run_as_of."""
    rows = universe.setdefault('tickers', {})
    report = {'added': [], 'merged': [], 'new_snapshot': [], 'conflicts': [], 'funds': []}
    seq = max([r.get('queue_seq') or 0 for r in rows.values()] + [0])
    for entry in entries:
        ticker = entry['ticker']
        row = rows.get(ticker)
        if row is None:
            run_id, conflict = (run_id_override, None) if run_id_override else run_id_for(ticker, as_of, run_as_of)
            if conflict:
                report['conflicts'].append({'ticker': ticker, 'reason': conflict})
                continue
            row = new_row(ticker, as_of, run_id, source, now)
            seq += 1
            row['queue_seq'] = seq
            rows[ticker] = row
            report['added'].append(ticker)
        else:
            if row.get('as_of_date') != as_of:
                started = row.get('started') or row.get('run_status') not in ('QUEUED',)
                if started and row.get('run_status') != 'COMPLETE':
                    report['conflicts'].append({'ticker': ticker, 'reason':
                        f"run {row.get('run_id')} for {row.get('as_of_date')} is {row.get('run_status')} at "
                        f"{row.get('stage')}; finish it or `universe reset {ticker}` before importing {as_of}"})
                    continue
                run_id, conflict = (run_id_override, None) if run_id_override else run_id_for(ticker, as_of, run_as_of)
                if conflict:
                    report['conflicts'].append({'ticker': ticker, 'reason': conflict})
                    continue
                if row.get('run_status') == 'COMPLETE':
                    row.setdefault('previous_runs', []).append(snapshot_summary(row))
                    report['new_snapshot'].append(ticker)
                reset_decision_fields(row)
                row.update(as_of_date=as_of, run_id=run_id)
            else:
                report['merged'].append(ticker)
            row['last_imported_at'] = now
            row['last_updated'] = now
            if source not in row.setdefault('sources', []):
                row['sources'].append(source)
        row['source'] = row.get('source') or source
        row['screens'] = list(dict.fromkeys([*(row.get('screens') or []), *entry['screens']]))
        row['screen_name'] = row['screens'][0] if row['screens'] else None
        row['company_name'] = row.get('company_name') or entry.get('company_name')
        row['exchange'] = row.get('exchange') or entry.get('exchange')
        if entry.get('security_type') != 'unknown' or not row.get('security_type_source'):
            row['security_type'] = entry['security_type']
            row['security_type_source'] = entry['security_type_source']
        if entry.get('screener_fields'):
            row.setdefault('screener_fields', {}).update(entry['screener_fields'])
        fund_block = f"security_type={row['security_type']} ({row['security_type_source']}): the harness analyzes operating companies"
        if row['security_type'] in ('etf', 'fund'):
            report['funds'].append(ticker)
            if row['run_status'] == 'QUEUED' and not row.get('started'):
                row.update(run_status='BLOCKED', blocked_reason=fund_block)
        elif row['run_status'] == 'BLOCKED' and str(row.get('blocked_reason') or '').startswith('security_type='):
            row.update(run_status='QUEUED', blocked_reason=None)
    return universe, report


def snapshot_summary(row):
    keep = ('as_of_date', 'run_id', 'run_status', 'score', 'score_ex_valuation', 'archetype', 'archetype_fit',
            'price_to_base', 'hard_veto_status', 'mechanical_pre_ic_state', 'ic_state', 'position_range',
            'early_exit', 'last_synced_at')
    return {k: row.get(k) for k in keep}


# ---------------------------------------------------------------- artifacts -> row

def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def resolved_position(verdict, state_policy):
    """(position_range, source). The recorded value, or the harness's own table value for its state.

    compute_aggregate maps every non-score state to a configured position text
    (for example EARLY_EXIT_NON_FIT -> "0% (...)"). A reconstructed verdict that
    left the field null gets that same configured text, labelled as such.
    """
    if not verdict:
        return None, None
    recorded = verdict.get('position_range')
    if recorded is not None:
        return recorded, 'final_verdict.position_range'
    state = verdict.get('ic_state') or verdict.get('mechanical_pre_ic_state')
    table = {**{b['state']: b['position_range'] for b in state_policy['bands']}, **state_policy['non_score_states']}
    if state in state_policy['non_score_states']:
        return table[state], 'config:state_thresholds.non_score_states'
    return None, None


def summarize_run(art, domain_agents, state_policy):
    """Copy decision fields from recorded artifacts. Never recomputes anything."""
    final, aggregate = art.get('final'), art.get('aggregate')
    verdict = final or aggregate
    out = {k: json.loads(json.dumps(ROW_DEFAULTS[k])) for k in SYNCED_FIELDS}
    out['source_files'] = dict(art.get('paths') or {})
    out['source_hashes'] = dict(art.get('hashes') or {})
    ic = art.get('ic_report') or {}
    out['ic_complete'] = ic.get('analysis_status') == 'complete'
    deep = art.get('deep_report') or {}
    out['report_status'] = 'COMPLETE' if deep else 'NONE'
    out['report_tier'] = deep.get('tier') if deep else None
    if not verdict:
        return out
    archetype = verdict.get('archetype')
    archetype_id = archetype.get('id') if isinstance(archetype, dict) else archetype
    fits = verdict.get('archetype_fit') or (archetype.get('archetype_fit') if isinstance(archetype, dict) else {}) or {}
    signals = ((verdict.get('valuation_model') or {}).get('signals')
               or (archetype.get('signals') if isinstance(archetype, dict) else None) or {})
    model = verdict.get('valuation_model') or {}
    scenarios = model.get('scenarios') or {}
    domains = {}
    for domain, row in (verdict.get('domain_scores') or {}).items():
        if isinstance(row, dict):
            value = row.get('decision_score', row.get('score'))
            if _num(value) is not None:
                domains[domain_agents.get(domain, domain).lower()] = value
    pacing = final.get('macro_pacing_multiplier') if final else None
    if pacing is None:
        pacing = (verdict.get('macro_geo_overlay') or {}).get('purchase_pacing_multiplier')
    position, position_source = resolved_position(final, state_policy) if final else (None, None)
    secondary = final.get('secondary_archetypes') if final else (archetype.get('secondary') if isinstance(archetype, dict) else [])
    out.update({
        'score': _num(verdict.get('score_100')),
        'score_ex_valuation': _num(verdict.get('score_100_ex_valuation')),
        'coverage_weight': _num(verdict.get('coverage_weight')),
        'classification': verdict.get('classification'),
        'archetype': archetype_id,
        'archetype_fit': _num((fits.get(archetype_id) or {}).get('fit_score')) if archetype_id in fits else None,
        'secondary_archetypes': list(secondary or []),
        'reachable_archetypes': verdict.get('reachable_archetypes_raw'),
        'domain_scores': domains,
        'hard_veto_status': verdict.get('hard_veto_status'),
        'mechanical_pre_ic_state': verdict.get('mechanical_pre_ic_state'),
        'ic_state': final.get('ic_state') if final else None,
        'position_range': position,
        'position_range_source': position_source,
        'position_range_pre_ic': verdict.get('position_range_pre_ic'),
        'macro_pacing': _num(pacing),
        'price_to_base': _num(signals.get('price_to_base_value')),
        'current_price': _num(model.get('current_price')),
        'valuation': {'status': model.get('status'),
                      **{k: _num((scenarios.get(k) or {}).get('value_per_share')) for k in ('bear', 'base', 'bull')}}
                     if model else None,
        'early_exit': bool(verdict.get('early_exit')),
        'early_exit_stage': (verdict.get('early_exit_record') or {}).get('stage'),
        'last_reachable_archetypes': (verdict.get('early_exit_record') or {}).get('last_reachable_archetypes'),
        'review_only': bool(verdict.get('review_only')),
        'reconstructed': bool(verdict.get('reconstructed')),
        'decision_policy_version': verdict.get('decision_policy_version'),
        'verdict_source': 'final_verdict' if final else 'aggregate',
    })
    return out


def derive_run_state(art, inspection, stage_map, lead_agent='EV'):
    """Lifecycle status/stage from artifacts plus an optional read-only planner inspection.

    Returns {'run_status','stage','started','blocked_reason','needs_aggregate','awaiting'}.
    COMPLETE requires final_verdict.json: an early exit, or an IC report that the
    final verdict already includes.
    """
    state = {'run_status': 'QUEUED', 'stage': 'stage0', 'started': bool(art.get('exists')),
             'blocked_reason': None, 'needs_aggregate': False, 'awaiting': []}
    if not art.get('exists'):
        return state
    final, aggregate = art.get('final'), art.get('aggregate')
    ic_done = (art.get('ic_report') or {}).get('analysis_status') == 'complete'
    freeze = art.get('freeze') or {}
    current = freeze.get('frozen') and freeze.get('config_current') and freeze.get('inputs_current')
    if final and final.get('early_exit'):
        return {**state, 'run_status': 'COMPLETE', 'stage': 'complete'}
    if final and ic_done and final.get('ic_verdict'):
        return {**state, 'run_status': 'COMPLETE', 'stage': 'complete'}
    if (ic_done and final and not final.get('ic_verdict')) or (not final and aggregate and aggregate.get('early_exit')):
        what = ('final_verdict.json predates the completed IC report' if ic_done
                else 'aggregate.json records an early exit but final_verdict.json is missing')
        if current:
            return {**state, 'stage': 'ic' if ic_done else 'complete', 'needs_aggregate': True}
        return {**state, 'run_status': 'BLOCKED', 'stage': 'ic' if ic_done else 'complete',
                'blocked_reason': f'unfinalized: {what}; `harness.py aggregate` needs a current freeze '
                                  f'({freeze_problem(freeze)})'}
    if not freeze.get('frozen'):
        return {**state, 'stage': 'stage0'}
    if not current:
        return {**state, 'run_status': 'BLOCKED', 'stage': planner_stage(inspection, stage_map, lead_agent) or 'stage0',
                'blocked_reason': f'stale freeze: {freeze_problem(freeze)}; review the change and re-freeze '
                                  f'(or fork-run) before continuing — the runner never re-freezes on its own'}
    stage = planner_stage(inspection, stage_map, lead_agent)
    if inspection and inspection.get('error'):
        return {**state, 'run_status': 'BLOCKED', 'stage': stage or 'stage0',
                'blocked_reason': f"planner inspection failed: {inspection['error']}"}
    return {**state, 'stage': stage or 'stage0'}


def freeze_problem(freeze):
    if not freeze.get('frozen'):
        return 'run is not frozen'
    problems = []
    if not freeze.get('inputs_current'):
        problems.append('frozen inputs changed or were never hashed')
    if not freeze.get('config_current'):
        problems.append('harness/policy changed since freeze')
    return '; '.join(problems) or 'freeze current'


def planner_stage(inspection, stage_map, lead_agent='EV'):
    step = (inspection or {}).get('plan')
    if not step:
        return None
    if step.get('stage') == 'triage' and lead_agent in (step.get('agents') or {}).values():
        return 'ev'
    return stage_map.get(step.get('stage'), step.get('stage'))


def apply_sync(row, summary, state, now):
    """Merge a summary + derived state into a row. Runner-recorded BLOCKED/FAILED survive
    a sync that shows no progress; any progress or completion replaces them. RUNNING is
    not preserved here: the store keeps it only while the ticker lock is actually held,
    so a crashed runner's row falls back to a resumable QUEUED."""
    before = (row.get('run_status'), row.get('stage'))
    row.update(summary)
    row['started'] = row.get('started') or state['started']
    new_status, new_stage = state['run_status'], state['stage']
    if new_status == 'COMPLETE' or new_status == 'BLOCKED':
        row.update(run_status=new_status, stage=new_stage, blocked_reason=state['blocked_reason'],
                   awaiting=[] if new_status == 'COMPLETE' else row.get('awaiting', []))
        if new_status == 'COMPLETE':
            row['last_error'] = None
    elif new_status == 'RUNNING':
        row.update(run_status='RUNNING', stage=new_stage)
    elif before[0] in ('BLOCKED', 'FAILED') and before[1] == new_stage:
        row['stage'] = new_stage
    else:
        row.update(run_status='QUEUED', stage=new_stage, blocked_reason=None, awaiting=[])
    row['last_synced_at'] = now
    row['last_updated'] = now
    return row


def stage_index(stage, stages):
    return stages.index(stage) if stage in stages else len(stages)


def determine_next_universe_action(art, inspection, statuses, stop_after=None, lead_agents=()):
    """What the batch runner does next for one ticker. Pure.

    The planner stays authoritative: agents come only from `inspection['plan']`.
    This function adds the lifecycle around it (init, Stage 0, finalization,
    blocks and the operator's stop boundary). `lead_agents` only orders work
    inside one planner step: a lead agent that the planner already requests runs
    first, then the planner is consulted again.

    kinds: init | stage0 | agents | finalize | pause | complete | blocked
    """
    stages = statuses['stages']
    stage_map = statuses['planner_stage_map']
    lead = statuses['triage_lead_stage']['agent']
    if not art.get('exists'):
        return {'kind': 'init', 'stage': 'stage0'}
    state = derive_run_state(art, inspection, stage_map, lead)
    if state['run_status'] == 'COMPLETE':
        return {'kind': 'complete', 'stage': 'complete', 'early_exit': bool((art.get('final') or {}).get('early_exit'))}
    if state['run_status'] == 'BLOCKED':
        return {'kind': 'blocked', 'stage': state['stage'], 'reason': state['blocked_reason']}
    if state['needs_aggregate']:
        return {'kind': 'finalize', 'stage': state['stage']}
    if not (art.get('freeze') or {}).get('frozen'):
        return {'kind': 'stage0', 'stage': 'stage0'}
    step = (inspection or {}).get('plan') or {}
    if step.get('execution_control') == 'blocked':
        return {'kind': 'blocked', 'stage': 'stage0',
                'reason': 'Stage 0 incomplete after freeze: ' + ', '.join(step.get('blocking_gaps') or [])}
    if step.get('stage') in ('early_exit', 'complete'):
        return {'kind': 'finalize', 'stage': 'complete', 'early_exit': step.get('stage') == 'early_exit'}
    ustage = planner_stage(inspection, stage_map, lead) or 'stage0'
    if stop_after and stage_index(ustage, stages) > stage_index(stop_after, stages):
        return {'kind': 'pause', 'stage': ustage, 'reason': f'stop boundary {stop_after} reached; next is {ustage}'}
    agents = list((step.get('agents') or {}).values())
    if not agents:
        return {'kind': 'blocked', 'stage': ustage, 'reason': f"planner returned stage {step.get('stage')} with no agents"}
    first = [a for a in agents if a in lead_agents]
    batch = first if first and len(agents) > len(first) else agents
    return {'kind': 'agents', 'stage': ustage, 'planner_stage': step.get('stage'), 'agents': batch,
            'requested': agents}


def eligible_for_full_run(row, inspection):
    """`--eligible-only`: triage finished and at least one archetype still reachable."""
    if row.get('run_status') == 'COMPLETE':
        return False
    if row.get('stage') in ('domain_analysis', 'macro', 'evidence_and_red_team', 'ic'):
        return True
    return bool(inspection and inspection.get('triage_complete') and inspection.get('reachable')
                and not inspection.get('early_exit'))


# ---------------------------------------------------------------- presentation

def display_status(row):
    if row.get('run_status') == 'COMPLETE' and row.get('early_exit'):
        return 'EARLY_EXIT'
    return row.get('run_status')


def fmt(value, digits=2):
    if value is None:
        return ''
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        text = f'{value:.{digits}f}'.rstrip('0').rstrip('.')
        return '0' if text in ('-0', '') else text
    return str(value)


def csv_record(row):
    ds = row.get('domain_scores') or {}
    return {'ticker': row['ticker'], 'score': fmt(row.get('score')), 'score_ex_ev': fmt(row.get('score_ex_valuation')),
            'archetype': row.get('archetype') or '', 'fit': fmt(row.get('archetype_fit')),
            'ev': fmt(ds.get('ev')), 'as': fmt(ds.get('as')), 'di': fmt(ds.get('di')), 'fs': fmt(ds.get('fs')),
            'price_to_base': fmt(row.get('price_to_base'), 4), 'hard_veto': row.get('hard_veto_status') or '',
            'mechanical_state': row.get('mechanical_pre_ic_state') or '', 'ic_state': row.get('ic_state') or '',
            'position_range': row.get('position_range') or '', 'macro_pacing': fmt(row.get('macro_pacing')),
            'status': display_status(row) or '', 'as_of': row.get('as_of_date') or ''}


def to_csv(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow(csv_record(row))
    return buffer.getvalue()


def position_bounds(text):
    """Descriptive parse of a position-range string for sorting only: '1-2%' -> (1.0, 2.0)."""
    if not text:
        return (-1.0, -1.0)
    numbers = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', str(text).split('(')[0])]
    if not numbers:
        return (0.0, 0.0)
    return (numbers[0], numbers[1] if len(numbers) > 1 else numbers[0])


def state_rank(state, state_policy):
    """Order states by the harness's own configured ranks; not a merit score."""
    ic = state_policy['ic_policy']['buy_state_rank']
    mechanical = [b['state'] for b in sorted(state_policy['bands'], key=lambda b: b['min'])]
    if state in ic:
        return 100 + ic[state]
    if state in mechanical:
        return 50 + mechanical.index(state)
    return 0


SORT_KEYS = {
    'ticker': lambda r, p: r.get('ticker') or '',
    'score': lambda r, p: r.get('score'),
    'ex_ev': lambda r, p: r.get('score_ex_valuation'),
    'fit': lambda r, p: r.get('archetype_fit'),
    'price_to_base': lambda r, p: r.get('price_to_base'),
    'ic_state': lambda r, p: state_rank(r.get('ic_state'), p),
    'position': lambda r, p: position_bounds(r.get('position_range')),
    'as_of': lambda r, p: r.get('as_of_date') or '',
    'queue': lambda r, p: r.get('queue_seq') or 0,
}


def sort_rows(rows, key, descending, state_policy):
    getter = SORT_KEYS[key]
    present = [r for r in rows if getter(r, state_policy) is not None]
    missing = [r for r in rows if getter(r, state_policy) is None]
    present.sort(key=lambda r: (getter(r, state_policy), r.get('ticker') or ''), reverse=descending)
    return present + sorted(missing, key=lambda r: r.get('ticker') or '')


def filter_rows(rows, f):
    """Every given filter must hold. Missing values never pass a numeric filter."""
    def keep(r):
        if f.get('archetype') and (r.get('archetype') or '').lower() != f['archetype'].lower():
            return False
        if f.get('state') and (r.get('ic_state') or '').upper() != f['state'].upper():
            return False
        if f.get('mechanical_state') and (r.get('mechanical_pre_ic_state') or '').upper() != f['mechanical_state'].upper():
            return False
        if f.get('veto') and (r.get('hard_veto_status') or '').upper() != f['veto'].upper():
            return False
        if f.get('status') and (display_status(r) or '').upper() != f['status'].upper() \
                and (r.get('run_status') or '').upper() != f['status'].upper():
            return False
        if f.get('stage') and r.get('stage') != f['stage']:
            return False
        if f.get('screen') and f['screen'] not in (r.get('screens') or []):
            return False
        for field, key, lower in (('score', 'min_score', True), ('archetype_fit', 'min_fit', True),
                                  ('price_to_base', 'max_price_base', False), ('score_ex_valuation', 'min_ex_ev', True)):
            if f.get(key) is not None:
                value = r.get(field)
                if value is None or (value < f[key] if lower else value > f[key]):
                    return False
        return True
    return [r for r in rows if keep(r)]


def history_changes(previous, current, fields):
    if previous is None:
        return {k: [None, current.get(k)] for k in fields if current.get(k) is not None}
    return {k: [previous.get(k), current.get(k)] for k in fields if previous.get(k) != current.get(k)}


# ---------------------------------------------------------------- invariants

def validate_row(row, art, state_policy):
    """Universe invariants against recorded artifacts. Returns [(level, message)]."""
    out = []
    t = row.get('ticker')
    err = lambda m: out.append(('ERROR', f'{t}: {m}'))
    warn = lambda m: out.append(('WARNING', f'{t}: {m}'))
    final, aggregate = art.get('final'), art.get('aggregate')
    status = row.get('run_status')
    if status not in RUN_STATUSES:
        err(f'unknown run_status {status!r}')
    if status == 'COMPLETE' and not final:
        err('run_status COMPLETE but final_verdict.json is missing')
    verdict = final or aggregate
    if verdict:
        for field, key in (('score', 'score_100'), ('score_ex_valuation', 'score_100_ex_valuation')):
            if row.get(field) != verdict.get(key):
                err(f"universe {field} {row.get(field)} != {'final_verdict' if final else 'aggregate'} {key} {verdict.get(key)}")
        if final and aggregate and final.get('score_100') != aggregate.get('score_100'):
            err(f"final_verdict score_100 {final.get('score_100')} != aggregate score_100 {aggregate.get('score_100')}")
    if final:
        position, _ = resolved_position(final, state_policy)
        for field, value in (('ic_state', final.get('ic_state')), ('hard_veto_status', final.get('hard_veto_status')),
                             ('mechanical_pre_ic_state', final.get('mechanical_pre_ic_state')),
                             ('position_range', position)):
            if row.get(field) != value:
                err(f'universe {field} {row.get(field)!r} != final_verdict {value!r}')
        out += [(lvl, f'{t}: {m}') for lvl, m in verdict_invariants(final, aggregate, art.get('ic_report'), state_policy)]
    if row.get('early_exit') and (art.get('ic_report') or {}).get('analysis_status') == 'complete':
        warn('early exit recorded but a completed IC report exists (IC should not run after an early exit)')
    if row.get('security_type') in ('etf', 'fund') and status not in ('BLOCKED', 'QUEUED'):
        warn(f"security_type {row.get('security_type')} has run_status {status}")
    return out


def verdict_invariants(final, aggregate, ic_report, state_policy):
    """Gate invariants a final verdict must satisfy. Pure; used by universe and report validation."""
    from .state import reconcile_ic
    out = []
    ic_policy = state_policy['ic_policy']
    ic_buy = set(ic_policy['buy_state_rank'])
    buy = ic_buy | set(state_policy['buy_states'])
    state = final.get('ic_state')
    if state in buy:
        if final.get('hard_veto_status') != 'CLEARED':
            out.append(('ERROR', f"buy state {state} with Hard Veto {final.get('hard_veto_status')}"))
        if final.get('coverage_weight') != 100:
            out.append(('ERROR', f"buy state {state} with coverage {final.get('coverage_weight')}"))
        pending = ((final.get('macro_geo_overlay') or {}).get('pending_reanalysis_domains') or [])
        if pending:
            out.append(('ERROR', f'buy state {state} while structural re-analysis is pending: {pending}'))
        if final.get('archetype') == 'non_fit' or final.get('review_only'):
            out.append(('ERROR', f"buy state {state} for {'review-only run' if final.get('review_only') else 'non_fit'}"))
    if state in ic_buy:
        cap = ic_policy['max_buy_rank_by_pre_ic_state'].get(final.get('mechanical_pre_ic_state'), 0)
        if ic_policy['buy_state_rank'][state] > cap:
            out.append(('ERROR', f"IC state {state} exceeds the deterministic cap for {final.get('mechanical_pre_ic_state')}"))
    if final.get('early_exit') and (ic_report or {}).get('analysis_status') == 'complete' and not final.get('review_only'):
        out.append(('WARNING', 'early exit but a completed IC report exists'))
    replay_source = aggregate if isinstance(aggregate, dict) and isinstance(aggregate.get('archetype'), dict) else None
    if replay_source is not None:
        try:
            replay = dict(replay_source)
            if ic_report and ic_report.get('analysis_status') == 'complete':
                replay['ic_verdict'] = ic_report
            expected_state, expected_position, _ = reconcile_ic(replay, state_policy)
            if expected_state != state:
                out.append(('ERROR', f'IC reconciliation replay gives {expected_state}, final_verdict says {state}'))
            elif final.get('position_range') is not None and expected_position != final.get('position_range'):
                out.append(('ERROR', f"IC reconciliation replay gives position {expected_position!r}, "
                                     f"final_verdict says {final.get('position_range')!r}"))
        except (KeyError, TypeError) as error:
            out.append(('WARNING', f'IC reconciliation could not be replayed from aggregate.json: missing {error}'))
    else:
        out.append(('INFO', 'aggregate.json absent or reconstructed without an archetype record; IC replay skipped'))
    return out
