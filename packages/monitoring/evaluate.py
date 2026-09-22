"""Comparing observations against declared thresholds. Arithmetic, and nothing else.

Every status here comes from a comparison somebody else declared. The analyst
wrote the threshold, the recorder wrote the observation with its source, and
this module applies `>=` or `<=` and reports the result. It does not weigh, it
does not average, and it does not decide what the result means.

That last part is the boundary, and it is the same one the whole system is
built on. A `thesis_break` is **not a sell**. It is a request that the people
who own the judgement look again — the domain reviewer for the score, the veto
owner for the veto, the IC for the state. Monitoring produces
`review_required` and stops there. Nothing in this package can change a score,
an archetype, a Hard Veto status, an `ic_state` or a position range, and a
test pins that the evaluation output contains no such field.

Five statuses do real work, and two of them are about absence:

    ok / warning / thesis_break     a comparison was made and this is its result
    stale                           nothing observed within the declared cadence
    unknown                         nothing observed at all
    not_machine_checkable           the threshold is prose; a person reads it
    unchecked / not_triggered /     a falsifier, which only evidence settles
    triggered

`stale` matters as much as `warning`. An item nobody has looked at in four
quarters is not an item that is fine — it is an item nobody is watching, and a
dashboard that showed it green would be lying by omission.
"""
from datetime import date, timedelta
from typing import Optional

from . import observations as observation_log
from . import thresholds as threshold_parser
from . import watchlist as watchlist_builder

BREACH_ORDER = ('thesis_break', 'warning')


def _comparison(raw: Optional[dict]) -> Optional[threshold_parser.Comparison]:
    if not raw:
        return None
    return threshold_parser.Comparison(operator=raw['operator'], value=raw['value'],
                                       unit=raw['unit'], source_text=raw['source_text'])


def _days_allowed(cadence: Optional[str], config: dict) -> Optional[int]:
    window = (config['cadence_days'] or {}).get(cadence)
    if window is None:
        return None
    return int(window) + int(config['staleness'].get('grace_days', 0))


def _stale(latest: dict, cadence: Optional[str], cutoff: str, config: dict) -> Optional[int]:
    """Days past the cadence window, or None if still current (or never stale)."""
    allowed = _days_allowed(cadence, config)
    if allowed is None:
        return None
    try:
        age = (date.fromisoformat(cutoff) - date.fromisoformat(latest['as_of_date'])).days
    except (TypeError, ValueError, KeyError):
        return None
    return age - allowed if age > allowed else None


def evaluate_item(item: dict, rows: list, cutoff: str, config: dict) -> dict:
    """One watch item's status, with everything the status rests on attached."""
    latest = observation_log.latest(rows)
    result = {
        'watch_id': item['watch_id'], 'kind': item['kind'], 'name': item['name'],
        'source_kind': item['source_kind'], 'source_ref': item['source_ref'],
        'cadence': item.get('cadence'),
        'observations': len(rows),
        'latest_observation': latest,
        'status': 'unknown', 'reason': None, 'review_required': False,
        'checked_levels': [], 'breached_levels': [],
    }

    if item['kind'] == 'falsifier':
        if latest is None:
            result['status'] = 'unchecked'
            result['reason'] = 'nobody has recorded a check of this falsifier'
            return result
        triggered = latest.get('triggered')
        if triggered is None:
            result['status'] = 'unchecked'
            result['reason'] = 'the latest observation records no triggered true/false'
            return result
        result['status'] = 'triggered' if triggered else 'not_triggered'
        result['reason'] = latest.get('note') or latest.get('source')
        result['review_required'] = bool(triggered)
        return result

    if not item.get('machine_checkable'):
        result['status'] = 'not_machine_checkable'
        result['reason'] = item.get('not_machine_checkable_reason')
        return result
    if latest is None:
        result['reason'] = 'no observation has been recorded for this KPI'
        return result

    unit = next((_comparison(item['comparison'][level]).unit for level in BREACH_ORDER
                 if item['comparison'].get(level)), 'number')
    number, problem = threshold_parser.observed_number(
        latest.get('value'), unit, latest.get('unit'))
    if number is None:
        result['status'] = 'not_machine_checkable'
        result['reason'] = problem
        return result

    result['observed_value'] = number
    for level in BREACH_ORDER:
        comparison = _comparison(item['comparison'].get(level))
        if comparison is None:
            continue
        result['checked_levels'].append(level)
        if not comparison.satisfied_by(number):
            result['breached_levels'].append(level)
    result['status'] = result['breached_levels'][0] if result['breached_levels'] else 'ok'
    result['review_required'] = result['status'] in (config.get('review_required_statuses') or [])

    overdue = _stale(latest, item.get('cadence'), cutoff, config)
    if overdue is not None:
        # Staleness outranks `ok`: an all-clear from a number nobody has
        # refreshed in a year is not an all-clear. It never outranks a breach,
        # which is already the louder statement.
        result['days_overdue'] = overdue
        if result['status'] == 'ok':
            result['status'] = 'stale'
            result['reason'] = (f'latest observation is {overdue} day(s) past the '
                                f"{item.get('cadence')} window; the comparison it would give "
                                'is out of date')
    if result['reason'] is None:
        comparison = _comparison(item['comparison'].get(result['breached_levels'][0])) \
            if result['breached_levels'] else None
        result['reason'] = (f'{number} fails {comparison.operator} {comparison.value} '
                            f'({comparison.source_text})' if comparison
                            else 'within every declared threshold')
    return result


def evaluate(ticker: str, cutoff: Optional[str] = None, run_id: Optional[str] = None,
             config: Optional[dict] = None, runs_dir=None, deep_dive_base=None,
             base=None) -> dict:
    """Every watch item for one company, evaluated as of `cutoff` (default today)."""
    config = config or watchlist_builder.load_config()
    cutoff = cutoff or date.today().isoformat()
    watchlist = watchlist_builder.build(ticker, run_id, config, runs_dir, deep_dive_base)

    results = []
    for item in watchlist['items']:
        rows = observation_log.load(watchlist['ticker'], item['watch_id'], cutoff, base)
        results.append(evaluate_item(item, rows, cutoff, config))

    by_status: dict = {}
    for row in results:
        by_status[row['status']] = by_status.get(row['status'], 0) + 1
    review = [row for row in results if row['review_required']]

    return {
        'ticker': watchlist['ticker'], 'run_id': watchlist['run_id'],
        'analysis_as_of_date': watchlist['as_of_date'], 'evaluated_as_of': cutoff,
        'deep_dive_id': watchlist.get('deep_dive_id'),
        'summary': {
            'items': len(results), 'by_status': by_status,
            'review_required': len(review),
            'observed': sum(1 for row in results if row['observations']),
            'never_observed': sum(1 for row in results
                                  if row['status'] in ('unknown', 'unchecked')),
            'not_machine_checkable': by_status.get('not_machine_checkable', 0),
        },
        'review_required': [{'watch_id': row['watch_id'], 'kind': row['kind'],
                             'name': row['name'], 'status': row['status'],
                             'reason': row['reason'], 'source_ref': row['source_ref']}
                            for row in review],
        'authority': config['authority'],
        'items': results,
        'integrity': observation_log.integrity(watchlist['ticker'], base),
    }


def portfolio(tickers: list, cutoff: Optional[str] = None, config: Optional[dict] = None,
              runs_dir=None, deep_dive_base=None, base=None) -> dict:
    """One row per company: what needs a person, and what nobody is watching."""
    config = config or watchlist_builder.load_config()
    cutoff = cutoff or date.today().isoformat()
    rows, unreadable = [], []
    for ticker in tickers:
        try:
            result = evaluate(ticker, cutoff, None, config, runs_dir, deep_dive_base, base)
        except ValueError as error:
            unreadable.append({'ticker': ticker, 'reason': str(error)})
            continue
        rows.append({'ticker': result['ticker'], 'run_id': result['run_id'],
                     'analysis_as_of_date': result['analysis_as_of_date'],
                     'summary': result['summary'],
                     'review_required': result['review_required']})
    return {'evaluated_as_of': cutoff, 'companies': len(rows),
            'needing_review': sum(1 for row in rows if row['summary']['review_required']),
            'rows': sorted(rows, key=lambda r: -r['summary']['review_required']),
            'unreadable': unreadable,
            'authority': config['authority']}


def days_between(earlier: str, later: str) -> int:
    return (date.fromisoformat(later) - date.fromisoformat(earlier)).days


def window_end(as_of: str, cadence: str, config: dict) -> Optional[str]:
    allowed = _days_allowed(cadence, config)
    if allowed is None:
        return None
    return (date.fromisoformat(as_of) + timedelta(days=allowed)).isoformat()
