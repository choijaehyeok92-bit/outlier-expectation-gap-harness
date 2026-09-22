"""Immutable orchestration batch records.

Same rule as a harness run, a screen run and a deep dive: written once, named
by content, never rewritten. A batch is a record of what was attempted and what
the harness then said, and re-running produces a new record beside the old one.

Triage batches and full-harness batches are kept in separate directories with
separate id fields. They answer different questions — "which of these thirty
survive the first four agents" and "what did the committee conclude about these
ten" — and a listing that mixed them would invite reading one as the other.

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


STAGES = {'triage': {'directory': 'triage_runs', 'id_field': 'triage_run_id'},
          'full': {'directory': 'full_harness_runs', 'id_field': 'full_run_id'}}


def stage_spec(stage: str) -> dict:
    if stage not in STAGES:
        raise ValueError(f'unknown stage {stage!r}; known: {sorted(STAGES)}')
    return STAGES[stage]


def default_base(stage: str = 'triage') -> Path:
    """Beside the runs the harness writes, so an isolated test stays isolated."""
    from . import contracts
    return contracts.harness().ROOT / stage_spec(stage)['directory']


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


def build_record(body: dict, config: dict, stage: str = 'triage') -> dict:
    spec = stage_spec(stage)
    digest = content_hash(body)
    return {**body, 'stage': stage,
            spec['id_field']: f"{body.get('as_of_date') or 'undated'}-{digest[:12]}",
            'content_sha256': digest,
            'verification_scope': config['verification_scope'],
            'provenance': {'code_commit_sha': code_commit_sha(),
                           'created_at_utc': datetime.now(timezone.utc).isoformat()}}


def record_id(record: dict) -> str:
    return record.get('triage_run_id') or record['full_run_id']


def save(record: dict, base=None, stage: Optional[str] = None) -> Path:
    stage = stage or record.get('stage', 'triage')
    spec = stage_spec(stage)
    directory = (Path(base) if base else default_base(stage)) / record[spec['id_field']]
    path = directory / f'{stage}_run.json'
    if path.exists():
        return path
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path


def load(run_id: str, base=None, stage: str = 'triage') -> Optional[dict]:
    stage_spec(stage)
    path = (Path(base) if base else default_base(stage)) / run_id / f'{stage}_run.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def list_runs(base=None, stage: str = 'triage') -> list:
    spec = stage_spec(stage)
    directory = Path(base) if base else default_base(stage)
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob(f'*/{stage}_run.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        summary = record.get('summary', {})
        rows.append({spec['id_field']: record[spec['id_field']], 'stage': stage,
                     'as_of_date': record.get('as_of_date'),
                     'attempted': summary.get('attempted'),
                     'completed': summary.get('completed'),
                     'screened_out': summary.get('screened_out'),
                     'created_at_utc': record['provenance']['created_at_utc']})
    return sorted(rows, key=lambda r: r['created_at_utc'], reverse=True)
