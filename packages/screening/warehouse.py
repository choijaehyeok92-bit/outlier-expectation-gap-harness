"""The screening warehouse: deterministic metrics for every ingested company.

Stage 2 of the funnel. Running the full harness over a universe is not
affordable, so a cheap, entirely mechanical pass narrows it first — and
"mechanical" is the operative word. Nothing here asks a model anything; every
number is `MetricCalculator` output with its provenance attached.

A row records what it could *not* compute as carefully as what it could. That
is not politeness: a screen over a warehouse whose gaps were silently zeroed
would rank companies by how little they disclose.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .metrics import MetricCalculator, load_config

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / 'data' / 'warehouse'
IDENTITY_FIELDS = ('ticker', 'company_name', 'jurisdiction', 'exchange', 'currency',
                   'security_type', 'issuer_key')


def default_path(as_of_date: str, base=None) -> Path:
    return Path(base or DEFAULT_DIR) / as_of_date / 'metrics.json'


def latest_path(base=None) -> Optional[Path]:
    directory = Path(base or DEFAULT_DIR)
    if not directory.exists():
        return None
    candidates = sorted(p for p in directory.glob('*/metrics.json'))
    return candidates[-1] if candidates else None


def _pack_digest(pack: dict) -> str:
    return hashlib.sha256(json.dumps(pack, sort_keys=True, ensure_ascii=False)
                          .encode('utf-8')).hexdigest()


def compute_row(entry: dict, as_of_date: str, config: Optional[dict] = None) -> dict:
    """One company's metrics, with identity, provenance and what is missing."""
    pack = entry['pack']
    calculator = MetricCalculator(pack, config=config, market_snapshot=entry.get('market_snapshot'))
    computed = calculator.compute(as_of_date)
    identity = {field: entry.get(field) for field in IDENTITY_FIELDS}
    identity['ticker'] = (identity.get('ticker') or pack.get('ticker') or '').upper()
    identity['company_name'] = identity.get('company_name') or pack.get('company_name')
    identity['currency'] = identity.get('currency') or pack.get('reporting_currency')
    return {
        **identity,
        'as_of_date': as_of_date,
        'consolidation_basis': computed['consolidation_basis'],
        'anchor_fiscal_year': computed['anchor_fiscal_year'],
        'metrics': computed['metrics'],
        'provenance': computed['provenance'],
        'unavailable': computed['unavailable'],
        'requires_review': computed['requires_review'],
        'source': {
            'regulator': (pack.get('ingestion') or {}).get('regulator'),
            'pack_sha256': _pack_digest(pack),
            'facts': len(pack.get('facts') or []),
            'live_api_verified': (pack.get('ingestion') or {}).get('live_api_verified'),
            'market_source': (entry.get('market_snapshot') or {}).get('source'),
        },
    }


def build(entries: Iterable[dict], as_of_date: str, config: Optional[dict] = None) -> dict:
    config = config or load_config()
    rows, failures, seen = [], [], set()
    for entry in entries:
        try:
            row = compute_row(entry, as_of_date, config)
        except Exception as error:               # one bad pack must not lose the warehouse
            failures.append({'ticker': entry.get('ticker'),
                             'error': f'{type(error).__name__}: {error}'})
            continue
        if row['ticker'] in seen:
            failures.append({'ticker': row['ticker'],
                             'error': 'duplicate ticker; a warehouse holds one row per company'})
            continue
        seen.add(row['ticker'])
        rows.append(row)
    coverage: dict = {}
    for row in rows:
        for metric, value in row['metrics'].items():
            bucket = coverage.setdefault(metric, {'computed': 0, 'missing': 0})
            bucket['computed' if value is not None else 'missing'] += 1
    return {
        'schema_version': '1.0',
        'as_of_date': as_of_date,
        'built_at_utc': datetime.now(timezone.utc).isoformat(),
        'metric_config_version': config.get('schema_version'),
        'companies': len(rows),
        'tickers': sorted(row['ticker'] for row in rows),
        'coverage': dict(sorted(coverage.items())),
        'failures': failures,
        'rows': sorted(rows, key=lambda r: r['ticker']),
    }


def save(payload: dict, path=None, base=None) -> Path:
    target = Path(path) if path else default_path(payload['as_of_date'], base)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return target


def load(as_of_date: Optional[str] = None, path=None, base=None) -> Optional[dict]:
    target = Path(path) if path else (default_path(as_of_date, base) if as_of_date
                                      else latest_path(base))
    if target is None or not Path(target).exists():
        return None
    return json.loads(Path(target).read_text(encoding='utf-8'))


def available(base=None) -> bool:
    """Whether the warehouse backend has anything to answer with."""
    return latest_path(base) is not None


def flat_rows(payload: dict) -> list:
    """Warehouse rows flattened into the shape the screening compiler reads."""
    rows = []
    for row in (payload or {}).get('rows', []):
        flat = {field: row.get(field) for field in IDENTITY_FIELDS if row.get(field) is not None}
        flat.update({
            'as_of_date': row.get('as_of_date'),
            'consolidation_basis': row.get('consolidation_basis'),
            'anchor_fiscal_year': row.get('anchor_fiscal_year'),
            'warehouse_unavailable': row.get('unavailable', []),
            'warehouse_requires_review': row.get('requires_review', []),
            'warehouse_source': row.get('source', {}),
        })
        for metric, value in (row.get('metrics') or {}).items():
            if value is not None:
                flat[metric] = value
        rows.append(flat)
    return rows
