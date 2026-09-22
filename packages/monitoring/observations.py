"""The append-only log of what was actually observed.

An observation is a fact, so it follows the rule facts follow everywhere else
in this repository: it carries `as_of_date`, `source_type`, `source`, `period`
and `value`, it is written once, and it is never edited. A correction is a new
observation that supersedes the old one, with a reason, and both stay readable.
Someone asking "what did we believe in March, and why" gets an answer.

Three refusals are deliberate.

**No source, no observation.** A number nobody can trace is not evidence, and
a monitoring status computed from one would be worse than no status.

**Nothing dated after the cutoff.** The harness never uses information from
after its `as_of_date`, and neither does this. An observation dated in the
future is refused at write time rather than filtered at read time, because a
typo that silently disappears is a typo nobody fixes.

**An observation older than the analysis is marked, not hidden.** A value from
before the run's cutoff is a legitimate thing to record — it establishes a
trend — but reading it as news would be a mistake, so it carries
`pre_analysis: true` and says which cutoff it precedes.
"""
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
MONITORING_DIR = ROOT / 'monitoring'
SOURCE_TYPES = ('filing', 'ir', 'industry', 'secondary', 'market', 'other')
LOG_NAME = 'observations.jsonl'
ENV_DIR = 'HARNESS_MONITORING_DIR'


class ObservationRejected(ValueError):
    """The observation was not written, and why."""


def base_dir(base=None) -> Path:
    """Where the log lives. `HARNESS_MONITORING_DIR` moves it off the repository.

    Observations are the one thing here that cannot be regenerated — they are
    what people saw — so a deployment that keeps them somewhere durable should
    be able to say so without editing code.
    """
    if base:
        return Path(base)
    return Path(os.environ.get(ENV_DIR) or MONITORING_DIR)


def log_path(ticker: str, base=None) -> Path:
    return base_dir(base) / ticker.upper() / LOG_NAME


def observation_id(payload: dict) -> str:
    fields = ('ticker', 'watch_id', 'value', 'unit', 'triggered', 'period', 'as_of_date',
              'source', 'source_type', 'fact_or_estimate', 'note', 'supersedes')
    body = {k: payload.get(k) for k in fields}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                                     default=str).encode('utf-8')).hexdigest()[:16]


def _today() -> str:
    return date.today().isoformat()


def record(ticker: str, watch_id: str, *, as_of_date: str, source: str, source_type: str,
           value=None, unit: Optional[str] = None, triggered: Optional[bool] = None,
           period: Optional[str] = None, fact_or_estimate: str = 'fact',
           note: Optional[str] = None, supersedes: Optional[str] = None,
           run_as_of_date: Optional[str] = None, cutoff: Optional[str] = None,
           base=None) -> dict:
    """Append one observation. Returns the stored row; raises rather than guessing."""
    if not source or not str(source).strip():
        raise ObservationRejected(
            'an observation needs a source. A number nobody can trace is not evidence.')
    if source_type not in SOURCE_TYPES:
        raise ObservationRejected(f'source_type must be one of {SOURCE_TYPES}, got {source_type!r}')
    if fact_or_estimate not in ('fact', 'estimate', 'interpretation'):
        raise ObservationRejected(
            f'fact_or_estimate must be fact|estimate|interpretation, got {fact_or_estimate!r}')
    try:
        date.fromisoformat(as_of_date)
    except (TypeError, ValueError):
        raise ObservationRejected(f'as_of_date must be YYYY-MM-DD, got {as_of_date!r}') from None
    if as_of_date > (cutoff or _today()):
        raise ObservationRejected(
            f'{as_of_date} is after the cutoff {cutoff or _today()}. Monitoring does not record '
            'information from the future any more than the harness uses it.')
    if value is None and triggered is None:
        raise ObservationRejected(
            'record either a value (for a KPI) or triggered=true/false (for a falsifier). '
            'An empty observation is not the same as an unknown, and unknown is the default.')

    row = {
        'ticker': ticker.upper(), 'watch_id': watch_id, 'value': value, 'unit': unit,
        'triggered': triggered, 'period': period, 'as_of_date': as_of_date,
        'source': str(source).strip(), 'source_type': source_type,
        'fact_or_estimate': fact_or_estimate, 'note': note, 'supersedes': supersedes,
    }
    row['observation_id'] = observation_id(row)
    row['recorded_at_utc'] = datetime.now(timezone.utc).isoformat()
    if run_as_of_date and as_of_date < run_as_of_date:
        row['pre_analysis'] = True
        row['pre_analysis_note'] = (f'dated before the analysis cutoff {run_as_of_date}; '
                                    'context for a trend, not news since the run')
    return append(row, base)


def append(row: dict, base=None) -> dict:
    """Write one row, ignoring a byte-identical re-append. Never rewrites a line."""
    path = log_path(row['ticker'], base)
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(existing['observation_id'] == row['observation_id'] for existing in load(row['ticker'], base=base)):
        return row
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return row


def load(ticker: str, watch_id: Optional[str] = None, cutoff: Optional[str] = None,
         base=None) -> list:
    """Every observation for this ticker, oldest first, at or before the cutoff."""
    path = log_path(ticker, base)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            # A corrupt line is reported by `integrity`, not silently dropped
            # into the middle of a status computation.
            continue
        if watch_id and row.get('watch_id') != watch_id:
            continue
        if cutoff and (row.get('as_of_date') or '') > cutoff:
            continue
        rows.append(row)
    return sorted(rows, key=lambda r: (r.get('as_of_date') or '', r.get('recorded_at_utc') or ''))


def integrity(ticker: str, base=None) -> dict:
    """Unreadable lines and superseded chains — named, not swallowed."""
    path = log_path(ticker, base)
    if not path.exists():
        return {'lines': 0, 'unreadable': [], 'superseded': []}
    unreadable, rows = [], []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as error:
            unreadable.append({'line': number, 'reason': str(error)})
    known = {row.get('observation_id') for row in rows}
    superseded = [{'observation_id': row['observation_id'], 'supersedes': row['supersedes'],
                   'target_exists': row['supersedes'] in known}
                  for row in rows if row.get('supersedes')]
    return {'lines': len(rows), 'unreadable': unreadable, 'superseded': superseded}


def latest(observations: list) -> Optional[dict]:
    """The observation in force: the newest that nothing later supersedes."""
    if not observations:
        return None
    replaced = {row['supersedes'] for row in observations if row.get('supersedes')}
    live = [row for row in observations if row.get('observation_id') not in replaced]
    return (live or observations)[-1]


def tickers(base=None) -> list:
    directory = base_dir(base)
    if not directory.exists():
        return []
    return sorted(path.parent.name for path in directory.glob(f'*/{LOG_NAME}'))
