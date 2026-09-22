"""Recording observations from the deterministic warehouse, once a person has said which metric.

Monitoring had a hole: 95 watch items for one company and no way to fill them
except typing. The obvious fix — match a KPI name to a warehouse metric — is
the same mistake as reading `quantified and rising` as `>= 2`, and here is what
it would produce on the real corpus:

    watch item : "Microsoft Cloud gross margin", warning >= 66%
    metric     : gross_margin = 0.679          (company-wide, every segment)
    status     : ok

A number that was never measured, compared against a threshold it does not
belong to, reported as fine. So nothing is matched automatically.

What happens instead is split in two. **A person links a watch item to a
metric, once.** The system may *suggest* a link only when the normalised name
equals the metric id or a declared alias exactly — no partial matches, no
similarity scores — and it records whether the link was `exact` or
`operator_asserted`, which travels into every observation made through it.

**Everything after the link is arithmetic.** Ingest reads the warehouse row,
takes the value, its `method` and the fact ids behind it, and writes an
observation dated to the metric's own period end. No judgement anywhere, and
re-ingesting the same build writes nothing: the observation id is a hash of
the fact, so the same fact is the same row.

Four things are refused rather than filled in: an unlinked item, a metric the
warehouse could not compute (unknown is not zero), a falsifier (evidence
settles those, not arithmetic), and a metric with no period end (an observation
whose date nobody knows cannot be judged stale).
"""
import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import observations as observation_log
from . import watchlist as watchlist_builder

LINKS_NAME = 'links.json'
SCHEMA_VERSION = '1.0'


class LinkRefused(ValueError):
    """The link was not made, and why."""


def policy(config: Optional[dict] = None) -> dict:
    config = config or watchlist_builder.load_config()
    return config.get('ingest') or {}


def links_path(ticker: str, base=None) -> Path:
    return observation_log.base_dir(base) / ticker.upper() / LINKS_NAME


def load_links(ticker: str, base=None) -> dict:
    path = links_path(ticker, base)
    if not path.exists():
        return {}
    try:
        return (json.loads(path.read_text(encoding='utf-8')) or {}).get('links') or {}
    except ValueError:
        return {}


def _save_links(ticker: str, links: dict, base=None) -> Path:
    path = links_path(ticker, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {'schema_version': SCHEMA_VERSION, 'ticker': ticker.upper(), 'links': links},
        ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return path


def metric_definitions() -> dict:
    """`metric_id -> definition` from the Phase 4 config. Read, never edited here."""
    from packages.screening import metrics as metric_module
    return {row['id']: row for row in metric_module.load_config()['definitions']}


def _normalise(text: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', str(text)).strip().split()).casefold()


def alias_index(config: Optional[dict] = None) -> dict:
    """`normalised name -> metric_id`, from the metric ids and the declared aliases."""
    settings = policy(config)
    index = {}
    for metric_id in metric_definitions():
        index[_normalise(metric_id)] = metric_id
        index[_normalise(metric_id.replace('_', ' '))] = metric_id
    for metric_id, aliases in (settings.get('aliases') or {}).items():
        for alias in aliases:
            index[_normalise(alias)] = metric_id
    return index


def suggest(ticker: str, config: Optional[dict] = None, base=None, **kwargs) -> dict:
    """Proposals, not links. Exact name equality only; everything else is listed as unmatched."""
    config = config or watchlist_builder.load_config()
    watchlist = watchlist_builder.build(ticker, config=config, **kwargs)
    index = alias_index(config)
    existing = load_links(watchlist['ticker'], base)
    definitions = metric_definitions()

    proposed, unmatched, linked = [], [], []
    for item in watchlist['items']:
        if item['kind'] != 'kpi':
            continue
        if item['watch_id'] in existing:
            linked.append({'watch_id': item['watch_id'], 'name': item['name'],
                           **existing[item['watch_id']]})
            continue
        metric_id = index.get(_normalise(item['name']))
        if metric_id:
            proposed.append({'watch_id': item['watch_id'], 'name': item['name'],
                             'metric_id': metric_id,
                             'metric_unit': definitions[metric_id].get('unit'),
                             'name_match': 'exact',
                             'source_kind': item['source_kind'],
                             'source_ref': item['source_ref']})
        else:
            unmatched.append({'watch_id': item['watch_id'], 'name': item['name'],
                              'source_kind': item['source_kind'],
                              'source_ref': item['source_ref']})
    return {
        'ticker': watchlist['ticker'], 'run_id': watchlist['run_id'],
        'linked': linked, 'proposed': proposed, 'unmatched': unmatched,
        'summary': {'linked': len(linked), 'proposed': len(proposed),
                    'unmatched': len(unmatched)},
        'note': ('proposed는 제안이지 링크가 아니다. `monitor link`로 사람이 걸어야 적재된다. '
                 'unmatched는 이름이 정확히 일치하지 않은 항목이며, 비슷하다는 이유로 붙이지 '
                 '않는다 — 재지 않은 것을 쟀다고 말하게 된다.'),
    }


def link(ticker: str, watch_id: str, metric_id: str, config: Optional[dict] = None,
         note: Optional[str] = None, linked_by: str = 'operator', base=None,
         **kwargs) -> dict:
    """Record that this watch item is measured by this metric. A person's decision."""
    config = config or watchlist_builder.load_config()
    definitions = metric_definitions()
    if metric_id not in definitions:
        raise LinkRefused(f'{metric_id!r} is not a warehouse metric; '
                          f'known: {sorted(definitions)}')
    watchlist = watchlist_builder.build(ticker, config=config, **kwargs)
    item = next((i for i in watchlist['items'] if i['watch_id'] == watch_id), None)
    if item is None:
        raise LinkRefused(f'{watch_id} is not a watch item for {watchlist["ticker"]}')
    if item['kind'] != 'kpi':
        raise LinkRefused('a falsifier is settled by evidence, not by a metric; '
                          'record a check with `monitor observe --triggered`')

    match = 'exact' if alias_index(config).get(_normalise(item['name'])) == metric_id \
        else 'operator_asserted'
    links = load_links(watchlist['ticker'], base)
    links[watch_id] = {
        'metric_id': metric_id, 'watch_name': item['name'],
        'metric_unit': definitions[metric_id].get('unit'),
        'name_match': match, 'note': note, 'linked_by': linked_by,
        'linked_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    _save_links(watchlist['ticker'], links, base)
    return {'ticker': watchlist['ticker'], 'watch_id': watch_id, **links[watch_id],
            'warning': (None if match == 'exact' else
                        f'{item["name"]!r} does not match {metric_id!r} by name. Recorded as '
                        'operator_asserted; every observation made through this link says so.')}


def unlink(ticker: str, watch_id: str, base=None) -> dict:
    """Remove a link. Observations already recorded through it stay in the log."""
    links = load_links(ticker, base)
    removed = links.pop(watch_id, None)
    if removed is None:
        raise LinkRefused(f'{watch_id} is not linked for {ticker.upper()}')
    _save_links(ticker.upper(), links, base)
    return {'ticker': ticker.upper(), 'watch_id': watch_id, 'removed': removed,
            'note': 'observations recorded through this link remain; the log is append-only'}


def _source_type(provenance: dict, settings: dict) -> str:
    mapping = (settings.get('observation') or {}).get('source_type_by_method') or {}
    method = str(provenance.get('method') or '')
    if method.startswith('market'):
        return mapping.get('market', 'market')
    if provenance.get('inputs'):
        return mapping.get('has_inputs', 'filing')
    return mapping.get('default', 'other')


def _unit(metric_unit: Optional[str], settings: dict) -> str:
    mapping = (settings.get('observation') or {}).get('unit_by_metric_unit') or {}
    return mapping.get(metric_unit or '', mapping.get('default', 'number'))


def source_string(metric_id: str, provenance: dict) -> str:
    """Traceable and stable: no build timestamp, so re-ingesting is a no-op."""
    parts = [f'screening_warehouse/{metric_id}', f"method={provenance.get('method')}"]
    inputs = provenance.get('inputs')
    if inputs:
        parts.append('facts=' + ','.join(inputs))
    return ' '.join(parts)


def ingest(ticker: str, as_of_date: Optional[str] = None, config: Optional[dict] = None,
           base=None, warehouse_payload: Optional[dict] = None, **kwargs) -> dict:
    """Write an observation for every linked item the warehouse can measure."""
    from packages.screening import warehouse as warehouse_store
    config = config or watchlist_builder.load_config()
    settings = policy(config)
    watchlist = watchlist_builder.build(ticker, config=config, **kwargs)
    resolved = watchlist['ticker']
    links = load_links(resolved, base)
    if not links:
        return {'ticker': resolved, 'recorded': 0, 'rows': [], 'skipped': [],
                'note': ('nothing is linked. `monitor suggest` proposes exact name matches; '
                         '`monitor link` is how a person accepts one.')}

    payload = warehouse_payload or warehouse_store.load(as_of_date)
    if payload is None:
        raise LinkRefused(
            'the screening warehouse has not been built; run '
            '`python harness.py screen build --as-of <DATE> --from-runs` first')
    row = next((r for r in payload['rows'] if (r.get('ticker') or '').upper() == resolved), None)
    if row is None:
        raise LinkRefused(f'{resolved} is not in the warehouse built for '
                          f"{payload.get('as_of_date')}")

    run_as_of = watchlist['as_of_date']
    # What the log already holds, so "recorded" means written and not merely
    # computed again. A no-op re-ingest should read as a no-op.
    known = {row['observation_id'] for row in observation_log.load(resolved, base=base)}
    recorded, unchanged, skipped = [], [], []
    for watch_id, link_row in sorted(links.items()):
        metric_id = link_row['metric_id']
        value = (row.get('metrics') or {}).get(metric_id)
        provenance = (row.get('provenance') or {}).get(metric_id) or {}
        if value is None:
            # Unknown is not zero, and a missing metric is not a breach.
            skipped.append({'watch_id': watch_id, 'metric_id': metric_id,
                            'reason': 'the warehouse could not compute this metric'})
            continue
        period_end = provenance.get('period_end')
        if not period_end:
            skipped.append({'watch_id': watch_id, 'metric_id': metric_id,
                            'reason': 'no period end; an observation nobody can date cannot '
                                      'be judged stale'})
            continue
        note = None if link_row.get('name_match') == 'exact' else (
            f"linked by {link_row.get('linked_by')} as operator_asserted: the watch item "
            f"{link_row.get('watch_name')!r} is not this metric's name")
        try:
            stored = observation_log.record(
                resolved, watch_id, as_of_date=period_end,
                source=source_string(metric_id, provenance),
                source_type=_source_type(provenance, settings),
                value=float(value), unit=_unit(link_row.get('metric_unit'), settings),
                period=period_end,
                fact_or_estimate=(settings.get('observation') or {}).get(
                    'fact_or_estimate', 'fact'),
                note=note, run_as_of_date=run_as_of, base=base)
        except observation_log.ObservationRejected as error:
            skipped.append({'watch_id': watch_id, 'metric_id': metric_id,
                            'reason': str(error)})
            continue
        row_summary = {'watch_id': watch_id, 'metric_id': metric_id,
                       'observation_id': stored['observation_id'],
                       'value': stored['value'], 'unit': stored['unit'],
                       'as_of_date': stored['as_of_date'],
                       'name_match': link_row.get('name_match')}
        (unchanged if stored['observation_id'] in known else recorded).append(row_summary)
    return {'ticker': resolved, 'warehouse_as_of': payload.get('as_of_date'),
            'linked': len(links), 'recorded': len(recorded),
            'already_present': len(unchanged), 'rows': recorded, 'unchanged': unchanged,
            'skipped': skipped,
            'note': ('같은 창고를 다시 적재하면 관측 id가 같으므로 already_present로 세고 '
                     '로그는 한 줄도 늘지 않는다. falsifier는 적재 대상이 아니다.')}
