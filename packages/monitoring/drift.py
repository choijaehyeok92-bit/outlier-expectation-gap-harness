"""What changed between one harness run and the next, and whether that is the company.

A company's score moving from 62 to 71 can mean two entirely different things.
The business may have changed. Or the rubric may have changed, or the policy
version, or the harness itself — in which case the two numbers were never
measuring the same thing and the difference says nothing about the company at
all.

The repository already takes this seriously for provider comparisons: a direct
comparison is only valid at the same harness commit and the same input
snapshot. A time series is the same problem stretched over time, so every pair
of consecutive runs is labelled. When `strategy_version` or
`decision_policy_version` differ, the delta is still shown — hiding it would
be its own distortion — but `comparable` is false and
`attributable_to_company` is false with it.

Assembling the series has its own catch. `harness.py init` will not overwrite
an existing run, so a company re-run under a later cutoff necessarily gets a
new run id — `NVDA`, then `NVDA-2026-09-18`, then `NVDA-V31-2026-09-19` — and
several of those carry the run id as their ticker. Grouping strictly by ticker
would therefore return a one-point "series" for a company that has been run
four times. So runs are collected by ticker **or** by the repository's own
`<TICKER>-…` naming convention, every point records `matched_by` so the
grouping is visible, and passing explicit run ids turns the inference off
entirely.

This module reads only what the harness already wrote. It computes no score
and re-runs nothing.
"""
from typing import Optional

from . import watchlist as watchlist_builder


def _value(row: dict, field: str):
    return row.get(field)


def _delta(before, after):
    if isinstance(before, (int, float)) and isinstance(after, (int, float)) \
            and not isinstance(before, bool) and not isinstance(after, bool):
        return round(float(after) - float(before), 4)
    return None


def compare(before: dict, after: dict, config: dict) -> dict:
    """One consecutive pair, field by field, with its comparability verdict."""
    policy_fields = config['drift']['comparability_fields']
    policy_changes = {field: {'before': before.get(field), 'after': after.get(field)}
                      for field in policy_fields if before.get(field) != after.get(field)}
    comparable = not policy_changes

    changes = []
    for field in config['drift']['tracked_fields']:
        old, new = _value(before, field), _value(after, field)
        if old == new:
            continue
        changes.append({'field': field, 'before': old, 'after': new,
                        'delta': _delta(old, new),
                        'attributable_to_company': comparable})
    return {
        'from_run': before['run_id'], 'to_run': after['run_id'],
        'from_as_of': before.get('as_of_date'), 'to_as_of': after.get('as_of_date'),
        'comparable': comparable,
        'policy_changes': policy_changes,
        'not_comparable_reason': (None if comparable else
                                  'the decision policy changed between these runs, so the '
                                  'difference measures the policy as much as the company'),
        'changes': changes,
    }


def collect(ticker: str, config: dict, runs_dir=None, run_ids: Optional[list] = None) -> list:
    """The runs that belong to one company's series, oldest first, each saying why.

    `run_ids` given explicitly is the honest path: no inference at all. Without
    it, a run matches on its ticker or on the `<TICKER>-…` naming convention,
    and `matched_by` records which.
    """
    from packages.screening import runs_index
    wanted = {r.upper() for r in (run_ids or [])}
    prefix_allowed = config['drift'].get('run_id_prefix_match', True) and not wanted
    upper = ticker.upper()

    rows = []
    for row in runs_index.load_rows(runs_dir):
        run_id = (row.get('run_id') or '').upper()
        if wanted:
            if run_id in wanted:
                rows.append({**row, 'matched_by': 'explicit_run_id'})
            continue
        if (row.get('ticker') or '').upper() == upper:
            rows.append({**row, 'matched_by': 'ticker'})
        elif prefix_allowed and run_id.startswith(upper + '-'):
            rows.append({**row, 'matched_by': 'run_id_prefix'})
    return sorted(rows, key=lambda r: (r.get('as_of_date') or '', r['run_id']))


def series(ticker: str, config: Optional[dict] = None, runs_dir=None,
           run_ids: Optional[list] = None) -> dict:
    """Every run for one company in order, and the change across each step."""
    config = config or watchlist_builder.load_config()
    rows = collect(ticker, config, runs_dir, run_ids)
    if not rows:
        raise ValueError(f'{ticker}: no harness run to build a series from')

    tracked = config['drift']['tracked_fields'] + config['drift']['comparability_fields']
    points = [{'run_id': row['run_id'], 'as_of_date': row.get('as_of_date'),
               'matched_by': row['matched_by'],
               **{field: row.get(field) for field in tracked}} for row in rows]
    steps = [compare(rows[index], rows[index + 1], config) for index in range(len(rows) - 1)]

    return {
        'ticker': upper_ticker(ticker),
        'runs': len(rows),
        'comparable_steps': sum(1 for step in steps if step['comparable']),
        'matched_by': sorted({row['matched_by'] for row in rows}),
        'points': points,
        'steps': steps,
        'reading_note': ('comparable=false인 구간의 차이는 기업이 아니라 정책이 바뀐 것일 수 있다. '
                         '같은 티커의 여러 run이 시점이 아니라 정책 버전 변형인 경우도 있으므로 '
                         'as_of_date와 policy_changes를 함께 본다. matched_by가 run_id_prefix면 '
                         '명명 관행으로 묶인 것이므로 정말 같은 기업인지 확인한다.'),
    }


def upper_ticker(ticker: str) -> str:
    return ticker.upper()
