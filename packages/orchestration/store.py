"""Immutable triage batch records.

Same rule as a harness run, a screen run and a deep dive: written once, named
by content, never rewritten. A batch is a record of what was attempted and what
the harness then said, and re-running produces a new record beside the old one.

Every record carries the verification scope from `config/triage.json`, so a
reader of a batch result never has to go looking for what the fixtures did and
did not establish.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]


def default_base() -> Path:
    """Beside the runs the harness writes, so an isolated test stays isolated."""
    from . import contracts
    return contracts.harness().ROOT / 'triage_runs'


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


def build_record(body: dict, config: dict) -> dict:
    digest = content_hash(body)
    return {**body,
            'triage_run_id': f"{body.get('as_of_date') or 'undated'}-{digest[:12]}",
            'content_sha256': digest,
            'verification_scope': config['verification_scope'],
            'provenance': {'code_commit_sha': code_commit_sha(),
                           'created_at_utc': datetime.now(timezone.utc).isoformat()}}


def save(record: dict, base=None) -> Path:
    directory = Path(base) if base else default_base()
    directory = directory / record['triage_run_id']
    path = directory / 'triage_run.json'
    if path.exists():
        return path
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def load(triage_run_id: str, base=None) -> Optional[dict]:
    path = (Path(base) if base else default_base()) / triage_run_id / 'triage_run.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def list_runs(base=None) -> list:
    directory = Path(base) if base else default_base()
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob('*/triage_run.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        rows.append({'triage_run_id': record['triage_run_id'],
                     'as_of_date': record.get('as_of_date'),
                     'attempted': record['summary'].get('attempted'),
                     'completed': record['summary'].get('completed'),
                     'created_at_utc': record['provenance']['created_at_utc']})
    return sorted(rows, key=lambda r: r['created_at_utc'], reverse=True)
