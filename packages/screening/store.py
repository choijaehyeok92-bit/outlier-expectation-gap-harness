"""Immutable screen-run persistence.

A screen is a dated claim about a universe, so it is written once and never
rewritten. The directory name carries the as-of date and a content hash, which
makes an accidental overwrite impossible rather than merely discouraged: a
second run with different content lands in a different directory, and a second
run with identical content is the same artifact.

Every record keeps what would be needed to reproduce it — the spec, the as-of
date, the policy versions, the code commit and the backend the rows came from.
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREEN_RUNS = ROOT / 'screen_runs'
SUMMARY_FIELDS = ('run_id', 'ticker', 'company_name', 'jurisdiction', 'exchange', 'currency',
                  'as_of_date', 'market_cap_usd', 'core_score', 'ex_valuation_score',
                  'classification', 'archetype', 'hard_veto_status', 'ic_state', 'position_range',
                  'price_to_base_value', 'dilution_watch_status', 'domain_scores', 'axis_scores',
                  'early_exit', 'full_harness_complete', 'result_sha256')


def code_commit_sha():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return os.environ.get('HARNESS_COMMIT', 'unknown')


def content_hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def build_record(spec, result, backend='harness_run_index', rows_sha256=None):
    body = {
        'schema_version': '1.0',
        'as_of_date': spec.get('as_of_date'),
        'spec': spec,
        'backend': backend,
        'rows_sha256': rows_sha256,
        'summary': {k: v for k, v in result.items() if k != 'results' and k != 'needs_review'},
        'results': [{k: row.get(k) for k in SUMMARY_FIELDS} | {'match_explain': row.get('match_explain')}
                    for row in result.get('results', [])],
        'needs_review': [{k: row.get(k) for k in SUMMARY_FIELDS} for row in result.get('needs_review', [])],
    }
    # The id identifies the screen, so it hashes the question and its answer —
    # not the parser's timestamp, which would make every rerun a new artifact.
    digest = content_hash({'spec_id': spec.get('spec_id'), 'as_of_date': body['as_of_date'],
                           'backend': backend, 'rows_sha256': rows_sha256,
                           'summary': body['summary'], 'results': body['results'],
                           'needs_review': body['needs_review']})
    return {**body, 'screen_run_id': f"{spec.get('as_of_date')}-{digest[:12]}",
            'content_sha256': digest,
            'provenance': {'code_commit_sha': code_commit_sha(),
                           'created_at_utc': datetime.now(timezone.utc).isoformat(),
                           'parser': (spec.get('source') or {}).get('parser')}}


def save(record, base=None):
    """Write once. An existing directory with the same id is left untouched."""
    directory = Path(base or SCREEN_RUNS) / record['screen_run_id']
    path = directory / 'screen_run.json'
    if path.exists():
        return path
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def load(screen_run_id, base=None):
    path = Path(base or SCREEN_RUNS) / screen_run_id / 'screen_run.json'
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def list_runs(base=None):
    directory = Path(base or SCREEN_RUNS)
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob('*/screen_run.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        rows.append({'screen_run_id': record['screen_run_id'], 'as_of_date': record['as_of_date'],
                     'matched_count': record['summary'].get('matched_count'),
                     'query': ((record['spec'].get('source') or {}).get('text')),
                     'created_at_utc': record['provenance']['created_at_utc']})
    return sorted(rows, key=lambda r: r['created_at_utc'], reverse=True)
