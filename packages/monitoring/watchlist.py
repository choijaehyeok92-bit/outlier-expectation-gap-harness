"""What is being watched for one company, assembled from what was already written.

Nothing here is authored. Every item comes from a document that already exists:
a `key_kpis` entry or a falsifier in an agent report, a `monitoring_kpis` entry
or a falsifier in the deep dive. Monitoring does not invent a KPI, does not
add a threshold, and does not decide that something is worth watching — the
analyst who wrote the report decided that, and this reads it back.

Two decisions in here are worth stating.

**A watch item's identity must outlive a rebuild.** Observations attach to a
`watch_id`, so if the id moved every time a deep dive was re-run, a company's
whole history would be orphaned by re-running the research. So the id is built
from the ticker, the kind, the source kind and the normalised name — and,
for an agent report, the agent id, which is stable. The deep dive id, which is
not, stays out of it. Thresholds stay out of both: an observation is of the
world, not of the threshold it happened to be compared against.

**An agent's single threshold is a warning, not a thesis break.** A deep dive
declares two levels and says which one breaks the thesis. `key_kpis` declares
one and never says that crossing it breaks anything. Reading it as a break
would manufacture an alarm the analyst did not raise.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

from . import thresholds as threshold_parser

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'config' / 'monitoring.json'
_WHITESPACE = re.compile(r'\s+')


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG).read_text(encoding='utf-8'))


def normalize(text: str) -> str:
    """Case- and spacing-insensitive, NFKC — so `Gross Margin` and `gross margin` are one item."""
    return _WHITESPACE.sub(' ', unicodedata.normalize('NFKC', str(text)).strip()).casefold()


def watch_id(ticker: str, kind: str, source_kind: str, name: str,
             source_ref: Optional[str], config: dict) -> str:
    scope = (config['watch_id'].get('source_scope') or {}).get(source_kind)
    parts = [ticker.upper(), kind, source_kind,
             (source_ref or '') if scope == 'source_ref' else '', normalize(name)]
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def _comparison(raw, direction_required, config):
    return threshold_parser.parse(raw, direction_required,
                                  config['thresholds']['direction_operators'])


def _kpi_item(ticker, run_id, kind, source_kind, source_ref, as_of_date, name, config,
              direction_required=None, warning=None, thesis_break=None, cadence=None,
              why=None, source=None, current_value=None) -> dict:
    warning_comparison = _comparison(warning, direction_required, config)
    break_comparison = _comparison(thesis_break, direction_required, config)
    levels = [name for name, parsed in (('warning', warning_comparison),
                                        ('thesis_break', break_comparison)) if parsed]
    checkable = bool(levels)
    reason = None
    if not checkable:
        reason = ('the declared threshold is prose, not a number with a side: '
                  f'warning={warning!r}, thesis_break={thesis_break!r}, '
                  f'direction_required={direction_required!r}')
    elif 'thesis_break' not in levels and thesis_break is not None:
        # Worth saying out loud: this item can raise a warning and can never
        # raise a break, so a quiet status is not evidence the thesis holds.
        reason = ('only the warning level is machine-checkable; the thesis-break threshold '
                  f'{thesis_break!r} states a condition this comparison does not evaluate')
    return {
        'watch_id': watch_id(ticker, kind, source_kind, name, source_ref, config),
        'ticker': ticker.upper(), 'run_id': run_id, 'kind': kind,
        'name': name, 'source_kind': source_kind, 'source_ref': source_ref,
        'as_of_date': as_of_date, 'cadence': cadence,
        'direction_required': direction_required,
        'why_it_matters': why, 'current_value_at_analysis': current_value,
        'where_to_look': source,
        'thresholds': {'warning': warning, 'thesis_break': thesis_break},
        'comparison': {'warning': warning_comparison.to_dict() if warning_comparison else None,
                       'thesis_break': break_comparison.to_dict() if break_comparison else None},
        'machine_checkable': checkable,
        'checkable_levels': levels,
        'not_machine_checkable_reason': reason,
    }


def _falsifier_item(ticker, run_id, source_kind, source_ref, as_of_date, statement, config,
                    observable=None, would_break=None) -> dict:
    return {
        'watch_id': watch_id(ticker, 'falsifier', source_kind, statement, source_ref, config),
        'ticker': ticker.upper(), 'run_id': run_id, 'kind': 'falsifier',
        'name': statement, 'source_kind': source_kind, 'source_ref': source_ref,
        'as_of_date': as_of_date, 'cadence': 'event_driven',
        'observable': observable, 'would_break': would_break,
        # A falsifier is a statement about the world, and whether it has come
        # true is a judgement with evidence behind it. No arithmetic decides
        # it, so it is never machine-checkable; a person records the check.
        'machine_checkable': False,
        'checkable_levels': [],
        'not_machine_checkable_reason': 'a falsifier is confirmed by evidence, not by arithmetic',
    }


def from_agent_reports(run_id: str, ticker: str, as_of_date: str, reports: dict,
                       config: dict) -> list:
    """`key_kpis` and `falsifiers` from each completed agent report."""
    direction_map = config['thresholds'].get('agent_direction_map') or {}
    level = config['thresholds'].get('agent_kpi_threshold_level', 'warning')
    items = []
    for agent_id in sorted(reports):
        report = reports[agent_id]
        if report.get('analysis_status') != 'complete':
            continue
        for kpi in report.get('key_kpis') or []:
            name = (kpi.get('name') or '').strip()
            if not name:
                continue
            direction = direction_map.get(normalize(kpi.get('direction') or ''))
            levels = {'warning': None, 'thesis_break': None}
            levels[level] = kpi.get('threshold')
            items.append(_kpi_item(
                ticker, run_id, 'kpi', 'agent_report', agent_id, as_of_date, name, config,
                direction_required=direction, warning=levels['warning'],
                thesis_break=levels['thesis_break'], cadence=kpi.get('cadence'),
                source=f'runs/{run_id}/reports/{agent_id}.json'))
        for statement in report.get('falsifiers') or []:
            if str(statement).strip():
                items.append(_falsifier_item(ticker, run_id, 'agent_report', agent_id,
                                             as_of_date, str(statement).strip(), config))
    return items


def from_deep_dive(run_id: str, ticker: str, report: dict, config: dict) -> list:
    """`monitoring_kpis` and `falsifiers` from a deep dive, with both threshold levels."""
    metadata = report.get('metadata') or {}
    deep_dive_id = metadata.get('deep_dive_id')
    as_of_date = metadata.get('as_of_date')
    items = []
    for kpi in report.get('monitoring_kpis') or []:
        direction = kpi.get('direction_required')
        items.append(_kpi_item(
            ticker, run_id, 'kpi', 'deep_dive', deep_dive_id, as_of_date,
            kpi.get('name') or '', config, direction_required=direction,
            warning=kpi.get('warning_threshold'), thesis_break=kpi.get('thesis_break_threshold'),
            cadence=kpi.get('cadence'), why=kpi.get('why_it_matters'),
            source=kpi.get('source'), current_value=kpi.get('current_value')))
    for falsifier in report.get('falsifiers') or []:
        items.append(_falsifier_item(
            ticker, run_id, 'deep_dive', deep_dive_id, as_of_date,
            falsifier.get('statement') or '', config,
            observable=falsifier.get('observable'), would_break=falsifier.get('would_break')))
    return items


def latest_deep_dive(ticker: str, base=None) -> Optional[dict]:
    from packages.research import store as deep_store
    rows = [row for row in deep_store.list_reports(base) if row['ticker'].upper() == ticker.upper()]
    if not rows:
        return None
    return deep_store.load(rows[0]['deep_dive_id'], base)


def runs_for(ticker: str, runs_dir=None) -> list:
    """Every run whose ticker matches, oldest first. A ticker can have several."""
    from packages.screening import runs_index
    rows = [row for row in runs_index.load_rows(runs_dir)
            if (row.get('ticker') or '').upper() == ticker.upper()]
    return sorted(rows, key=lambda r: (r.get('as_of_date') or '', r['run_id']))


def build(ticker: str, run_id: Optional[str] = None, config: Optional[dict] = None,
          runs_dir=None, deep_dive_base=None) -> dict:
    """The watchlist for one company: every declared KPI and falsifier, with its source."""
    config = config or load_config()
    rows = runs_for(ticker, runs_dir)
    if not rows:
        raise ValueError(f'{ticker}: no harness run; nothing has declared what to watch')
    row = next((r for r in rows if r['run_id'] == run_id), None) if run_id else rows[-1]
    if row is None:
        raise ValueError(f'{run_id}: no such run for {ticker}')

    from packages.screening import runs_index
    base = Path(runs_dir or runs_index.RUNS_DIR) / row['run_id'] / 'reports'
    reports = {}
    for path in sorted(base.glob('*.json')):
        try:
            reports[path.stem] = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            continue

    items = from_agent_reports(row['run_id'], row['ticker'], row['as_of_date'], reports, config)
    deep_dive = latest_deep_dive(row['ticker'], deep_dive_base)
    if deep_dive:
        items += from_deep_dive(row['run_id'], row['ticker'], deep_dive, config)

    # Two agents can name the same KPI; the id merges them, and the first one
    # in manifest order keeps the entry rather than the later one overwriting.
    unique, seen = [], set()
    for item in items:
        if item['watch_id'] in seen:
            continue
        seen.add(item['watch_id'])
        unique.append(item)

    return {'ticker': row['ticker'], 'run_id': row['run_id'], 'as_of_date': row['as_of_date'],
            'deep_dive_id': (deep_dive or {}).get('metadata', {}).get('deep_dive_id'),
            'summary': {'items': len(unique),
                        'kpis': sum(1 for i in unique if i['kind'] == 'kpi'),
                        'falsifiers': sum(1 for i in unique if i['kind'] == 'falsifier'),
                        'machine_checkable': sum(1 for i in unique if i['machine_checkable']),
                        'can_raise_warning': sum(1 for i in unique
                                                 if 'warning' in i.get('checkable_levels', [])),
                        'can_raise_thesis_break': sum(1 for i in unique
                                                      if 'thesis_break' in i.get('checkable_levels', [])),
                        'by_source': {kind: sum(1 for i in unique if i['source_kind'] == kind)
                                      for kind in ('agent_report', 'deep_dive')}},
            'reading_note': ('machine_checkable가 아닌 항목은 감시에서 빠진 것이 아니라 사람이 '
                             '읽어야 하는 항목이다. can_raise_thesis_break가 0이면 어떤 관측도 '
                             '자동으로 가설 파기를 띄울 수 없다 — 조용한 상태가 가설이 멀쩡하다는 '
                             '증거가 아니다.'),
            'items': unique}
