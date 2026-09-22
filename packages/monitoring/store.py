"""Immutable monitoring snapshots.

An evaluation is a statement about a moment: as of this date, against these
thresholds, with these observations, here is what needs a person. Re-running
tomorrow produces a different statement, and both should stay readable — "when
did this first go red, and what did we know then" is the question monitoring
exists to answer.

So a snapshot follows the rule every other record here follows: written once,
named by content, never rewritten. The observation log underneath it is
append-only for the same reason, and unlike a snapshot it is not regenerable —
it is what people saw, not what the code computed from it.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_NAME = 'monitoring_run.json'


def default_base() -> Path:
    override = os.environ.get('HARNESS_MONITORING_RUNS_DIR')
    return Path(override) if override else ROOT / 'monitoring_runs'


def content_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     default=str).encode('utf-8')).hexdigest()


def code_commit_sha() -> str:
    import os
    import subprocess
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return os.environ.get('HARNESS_COMMIT', 'unknown')


def build_record(body: dict) -> dict:
    digest = content_hash(body)
    scope = body.get('evaluated_as_of') or 'undated'
    name = body.get('ticker') or 'portfolio'
    return {**body,
            'monitoring_run_id': f'{name}-{scope}-{digest[:12]}',
            'content_sha256': digest,
            'provenance': {'code_commit_sha': code_commit_sha(),
                           'created_at_utc': datetime.now(timezone.utc).isoformat()}}


def save(record: dict, base=None) -> Path:
    directory = (Path(base) if base else default_base()) / record['monitoring_run_id']
    path = directory / SNAPSHOT_NAME
    if path.exists():
        return path
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def load(monitoring_run_id: str, base=None) -> Optional[dict]:
    path = (Path(base) if base else default_base()) / monitoring_run_id / SNAPSHOT_NAME
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def list_runs(base=None) -> list:
    directory = Path(base) if base else default_base()
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob(f'*/{SNAPSHOT_NAME}')):
        record = json.loads(path.read_text(encoding='utf-8'))
        summary = record.get('summary') or {}
        rows.append({'monitoring_run_id': record['monitoring_run_id'],
                     'ticker': record.get('ticker'),
                     'evaluated_as_of': record.get('evaluated_as_of'),
                     'items': summary.get('items'),
                     'review_required': summary.get('review_required'),
                     'created_at_utc': record['provenance']['created_at_utc']})
    return sorted(rows, key=lambda r: r['created_at_utc'], reverse=True)
