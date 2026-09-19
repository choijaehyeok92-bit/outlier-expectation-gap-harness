"""Band-centre-preserving interpolation for continuous observable anchors.

Discrete tables (counts, presence tests) keep their step behaviour: interpolating a
count would invent a state the evidence cannot be in. Only rows that declare numeric
`lo`/`hi` bounds on a single continuous metric take part.

The rule keeps the published table value at each band's centre, so a run scored at the
centre under the old step table is unchanged, and it is continuous across band edges,
so no discontinuity is introduced where none exists in the underlying metric.

    p  = (x - lo) / (hi - lo)                       position inside the band
    p < 0.5 -> score = S - (0.5 - p) * (S - S_prev)
    p >= 0.5 -> score = S + (p - 0.5) * (S_next - S)

Rows are ordered by the metric ascending, so the formula holds for decreasing metrics
too (S_next is simply lower than S). A terminal band that is open on one side has no
neighbour to interpolate toward on that side and keeps its published score.
"""
from .conditions import number


def _rows(table):
    """Rows that carry numeric bounds, ordered by the metric ascending."""
    bounded = [r for r in table if number(r.get('lo')) or number(r.get('hi'))]
    return sorted(bounded, key=lambda r: (r['lo'] if number(r.get('lo')) else float('-inf')))


def interpolate(table, x, step=None):
    """Score for metric value `x`, or None when the table is not interpolable.

    `step` rounds the result to that grid (the harness scores on a 5-point grid).
    """
    if not number(x):
        return None
    rows = _rows(table)
    if not rows:
        return None
    for i, row in enumerate(rows):
        lo, hi = row.get('lo'), row.get('hi')
        low_ok = not number(lo) or x >= lo
        high_ok = not number(hi) or x < hi
        if not (low_ok and high_ok):
            continue
        score = float(row['score'])
        lo, hi = _closed_bounds(rows, i)
        if lo is None or hi is None or hi <= lo:
            return _round(score, step)
        p = (x - lo) / (hi - lo)
        p = min(max(p, 0.0), 1.0)
        if p < 0.5 and i > 0:
            score -= (0.5 - p) * (score - float(rows[i - 1]['score']))
        elif p >= 0.5 and i + 1 < len(rows):
            score += (p - 0.5) * (float(rows[i + 1]['score']) - score)
        return _round(score, step)
    return None


def _closed_bounds(rows, i):
    """Bounds for band `i`, mirroring a neighbour's width across an open outer edge.

    A terminal band is unbounded on one side, so it has no centre of its own. Borrowing
    the adjacent band's width gives it one and keeps the curve continuous at the shared
    edge; values beyond that mirrored centre simply hold the band's published score.
    """
    row = rows[i]
    lo, hi = row.get('lo'), row.get('hi')
    if not number(lo) and number(hi) and i + 1 < len(rows):
        nxt = rows[i + 1]
        if number(nxt.get('lo')) and number(nxt.get('hi')):
            lo = hi - (nxt['hi'] - nxt['lo'])
    if not number(hi) and number(lo) and i > 0:
        prev = rows[i - 1]
        if number(prev.get('lo')) and number(prev.get('hi')):
            hi = lo + (prev['hi'] - prev['lo'])
    return (lo if number(lo) else None, hi if number(hi) else None)


def _round(value, step):
    if not step:
        return round(value, 4)
    return round(round(value / step) * step, 4)


def reachable_scores(table, step=5):
    """Scores the table can actually produce, used to catch unreachable thresholds."""
    rows = _rows(table)
    if not rows:
        return sorted({float(r['score']) for r in table})
    out = {float(r['score']) for r in table}
    for row in rows:
        lo, hi = row.get('lo'), row.get('hi')
        if not (number(lo) and number(hi)) or hi <= lo:
            continue
        span = hi - lo
        for n in range(0, 1001):
            value = interpolate(table, lo + span * n / 1000.0, step)
            if value is not None:
                out.add(value)
    return sorted(out)


def interpolable(criterion):
    anchors = criterion.get('observable_anchors') or {}
    return bool(_rows(anchors.get('table') or []))
