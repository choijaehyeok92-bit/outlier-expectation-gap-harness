"""Immutable deep-dive persistence.

Same rule as a harness run and a screen run: written once, named by content, and
never overwritten. Rerunning a deep dive with new evidence produces a new
directory beside the old one, so the earlier conclusion and the evidence it
rested on stay readable.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEEP_DIVE_DIR = ROOT / 'deep_dive'


def content_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def deep_dive_id(ticker, as_of_date, digest):
    return f'{ticker}-{as_of_date}-{digest[:12]}'


def save(report, plan=None, base=None):
    directory = Path(base or DEEP_DIVE_DIR) / report['metadata']['deep_dive_id']
    path = directory / 'deep_dive_report.json'
    if path.exists():
        return path
    directory.mkdir(parents=True, exist_ok=True)
    if plan is not None:
        (directory / 'deep_dive_plan.json').write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def load(deep_dive_id_value, base=None):
    path = Path(base or DEEP_DIVE_DIR) / deep_dive_id_value / 'deep_dive_report.json'
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def load_plan(deep_dive_id_value, base=None):
    path = Path(base or DEEP_DIVE_DIR) / deep_dive_id_value / 'deep_dive_plan.json'
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def list_reports(base=None):
    directory = Path(base or DEEP_DIVE_DIR)
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob('*/deep_dive_report.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        metadata = report['metadata']
        rows.append({'deep_dive_id': metadata['deep_dive_id'], 'ticker': metadata['ticker'],
                     'company_name': metadata.get('company_name'),
                     'jurisdiction': metadata['jurisdiction'], 'as_of_date': metadata['as_of_date'],
                     'created_at_utc': metadata['created_at_utc'],
                     'harness_run': metadata['harness_run']['run_id'],
                     'red_team_overall': (report.get('red_team') or {}).get('overall'),
                     'agreement_with_harness': (report.get('final_synthesis') or {}).get('agreement_with_harness')})
    return sorted(rows, key=lambda r: r['created_at_utc'], reverse=True)
