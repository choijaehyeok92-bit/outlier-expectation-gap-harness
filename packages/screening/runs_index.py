"""Read the completed harness run corpus into normalised screening rows.

Strictly read-only. It opens `runs/<RUN_ID>/aggregate.json` and
`company_context.json` and copies what is already there. It recomputes nothing:
a score in a row is the score the harness wrote, and a Hard Veto status is the
one its configured owner recorded.

Two compatibility rules matter, because this corpus spans several policy
versions. Historical runs may carry retired archetype strings or pre-v3.3 IC
state names, and a few were written before `domain_scores` was populated in
`final_verdict.json`. So the reader prefers `aggregate.json`, falls back to
`final_verdict.json`, and never rewrites a historical artifact to make it
easier to read.

Jurisdiction is inferred from the reporting currency and the run identifier
shape — a six-digit KRX code is Korean — and recorded as `unknown` rather than
guessed when neither says.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / 'runs'
NON_COMPANY_DIRS = {'_macro', '_reference'}
KRX_CODE = re.compile(r'^\d{6}$')
TRIAGE_DOMAINS = ('expectation_valuation', 'asymmetry', 'disruptive_innovation', 'financial_survival')
CORE_DOMAINS = ('structural_leadership', 'customer_product', 'moat_trajectory', 'reinvestment_fcf',
                'management_allocation', 'financial_survival', 'expectation_valuation', 'asymmetry')


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _sha256(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def jurisdiction_of(run_id, context):
    currency = (context.get('currency') or '').upper()
    if currency == 'KRW' or KRX_CODE.match(run_id.split('-')[0]):
        return 'KR'
    if currency == 'USD':
        return 'US'
    return 'unknown'


def exchange_of(run_id, jurisdiction, context):
    declared = context.get('exchange')
    if declared:
        return declared
    # Without an exchange in the frozen context the venue is genuinely unknown.
    # KRX segment (KOSPI vs KOSDAQ) is not derivable from the six-digit code.
    return 'KRX' if jurisdiction == 'KR' else None


def run_ids(runs_dir=None):
    base = Path(runs_dir or RUNS_DIR)
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and p.name not in NON_COMPANY_DIRS and (p / 'company_context.json').exists())


def load_row(run_id, runs_dir=None):
    """One normalised screening row, or None when the run has no readable result."""
    run = Path(runs_dir or RUNS_DIR) / run_id
    context_path = run / 'company_context.json'
    if not context_path.exists():
        return None
    context = _read(context_path)

    result, source, digest = None, None, None
    for name in ('aggregate.json', 'final_verdict.json'):
        path = run / name
        if path.exists():
            try:
                candidate = _read(path)
            except ValueError:
                continue
            if result is None or (candidate.get('domain_scores') and not result.get('domain_scores')):
                result, source, digest = candidate, name, _sha256(path)
            if name == 'aggregate.json':
                break
    if result is None:
        return None

    verdict_path = run / 'final_verdict.json'
    verdict = _read(verdict_path) if verdict_path.exists() else {}
    manifest_path = run / 'run_manifest.json'
    manifest = _read(manifest_path) if manifest_path.exists() else {}

    domain_scores = {name: (row or {}).get('score') if isinstance(row, dict) else None
                     for name, row in (result.get('domain_scores') or {}).items()}
    axis_scores = dict(result.get('axis_scores') or {})
    archetype = result.get('archetype')
    if isinstance(archetype, dict):
        archetype = archetype.get('id')
    valuation = result.get('valuation_model') or {}
    signals = valuation.get('signals') or {}
    dilution = result.get('dilution_watch') or verdict.get('dilution_watch') or {}
    jurisdiction = jurisdiction_of(run_id, context)
    completed = {name for name, score in domain_scores.items() if score is not None}

    return {
        'run_id': run_id,
        'ticker': context.get('ticker') or run_id,
        'company_name': context.get('company_name'),
        'jurisdiction': jurisdiction,
        'exchange': exchange_of(run_id, jurisdiction, context),
        'currency': context.get('currency'),
        'as_of_date': result.get('as_of_date') or context.get('as_of_date'),
        'market_cap_usd': context.get('market_cap_usd'),
        'current_price': context.get('current_price'),
        'net_cash_per_share': context.get('net_cash_per_share'),
        'core_score': result.get('score_100'),
        'ex_valuation_score': result.get('score_100_ex_valuation'),
        'coverage_weight': result.get('coverage_weight'),
        'classification': result.get('classification'),
        'archetype': archetype,
        'hard_veto_status': result.get('hard_veto_status'),
        'ic_state': verdict.get('ic_state') or result.get('mechanical_pre_ic_state'),
        'mechanical_pre_ic_state': result.get('mechanical_pre_ic_state'),
        'position_range': verdict.get('position_range') or result.get('position_range_pre_ic'),
        'early_exit': bool(result.get('early_exit')),
        'valuation_status': valuation.get('status'),
        'price_to_base_value': signals.get('price_to_base_value'),
        'revenue_cagr_next_3y': signals.get('revenue_cagr_next_3y'),
        'dilution_watch_status': dilution.get('status') if isinstance(dilution, dict) else None,
        'domain_scores': domain_scores,
        'axis_scores': axis_scores,
        'triage_complete': all(d in completed for d in TRIAGE_DOMAINS),
        'full_harness_complete': all(d in completed for d in CORE_DOMAINS),
        'strategy_version': result.get('strategy_version') or manifest.get('strategy_version'),
        'decision_policy_version': result.get('decision_policy_version') or manifest.get('decision_policy_version'),
        'input_snapshot_sha256': manifest.get('input_snapshot_sha256'),
        'frozen': bool(manifest.get('frozen')),
        'result_source': source,
        'result_sha256': digest,
    }


def load_rows(runs_dir=None):
    rows = [load_row(run_id, runs_dir) for run_id in run_ids(runs_dir)]
    return [row for row in rows if row]


def universe_summary(rows):
    by_jurisdiction = {}
    for row in rows:
        by_jurisdiction[row['jurisdiction']] = by_jurisdiction.get(row['jurisdiction'], 0) + 1
    dates = sorted({row['as_of_date'] for row in rows if row.get('as_of_date')})
    return {'backend': 'harness_run_index', 'runs': len(rows),
            'by_jurisdiction': by_jurisdiction,
            'as_of_dates': dates,
            'latest_as_of_date': dates[-1] if dates else None,
            'note': 'Completed harness runs only. The full US/KR issuer universe arrives with '
                    'SEC/DART ingestion in Phase 3; this index is not a market universe.'}
