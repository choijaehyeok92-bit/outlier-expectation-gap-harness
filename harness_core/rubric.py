"""Validate rubric values before they can drive criterion-level policy."""
import statistics
from .conditions import number


def validated_rows(report, rubric, step):
    if not rubric or not report.get('subscores'):
        return None  # legacy report: domain score is readable, criteria stay missing
    rows = report['subscores']
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError('subscores must be a list of criterion objects')
    expected = {c['id'] for c in rubric['criteria']}
    actual = [r.get('criterion_id') for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(f'{report.get("agent_id")}: missing, duplicate or unknown rubric criteria')
    for row in rows:
        value = row.get('score_0_100')
        if not number(value) or not 0 <= value <= 100 or abs(value/step - round(value/step)) > 1e-9:
            raise ValueError(f'Invalid rubric subscore: {row}')
    return {r['criterion_id']: float(r['score_0_100']) for r in rows}


def rubric_score(report, rubric, step):
    rows = validated_rows(report, rubric, step)
    if rows is None:
        return None
    total = sum(c['weight'] for c in rubric['criteria'])
    return sum(rows[c['id']] * c['weight'] for c in rubric['criteria']) / total


def aggregate_criteria(reports, rubric, step):
    values = [validated_rows(r, rubric, step) for r in reports]
    # Mixed legacy/modern domains must not invent historical criterion scores.
    if not values or any(v is None for v in values):
        return {}
    return {key: statistics.median(v[key] for v in values) for key in sorted(values[0])}
