"""Config-driven eligibility, explicit fit ranking, and optimistic reachability.

Eligibility and fit answer different questions. Eligibility asks whether an
archetype may own the company at all; fit asks which of the eligible ones best
describes it. v3.2 ranked on the eligibility conditions themselves, which let a
detailed contract outvote a terse one: compounder gates both
`domain.reinvestment_fcf` and two of its own criteria, so that one economic idea
cast three ballots. v3.3 ranks on `fit_axes` instead, a short weighted list per
archetype that must be a subset of its own gates.
"""
from .conditions import check_condition, resolve


def _legacy_fit_score(archetype, domains, signals):
    """v3.2 compatibility for configs that still rank on eligibility conditions."""
    weighted, total = 0.0, 0.0
    for c in archetype['conditions']:
        weight = float(c.get('fit_weight', 1.0))
        value = resolve(c['field'], domains, signals)
        normalized = 0.0
        if value is not None:
            if c['field'].startswith(('domain.', 'criterion.')):
                normalized = value / 100
            elif c['op'] == '<=':
                normalized = 1 - value / (2 * c['value'])
            elif c['op'] == '>=':
                normalized = value / (2 * c['value'])
            else:
                lo, hi = c['value']
                normalized = 1 - abs(value - (lo+hi)/2) / (hi-lo)
        weighted += weight * max(0, min(1, normalized))
        total += weight
    return round(100 * weighted / total, 8)


def _normalize_fit_axis(axis, value):
    """Map a raw value onto 0..1 for ranking.

    Scores are already on 0..100. A signal like revenue growth is not, so it
    declares an explicit linear range rather than being folded against its own
    eligibility threshold the way v3.2 did — a gate is a floor, not a scale.
    """
    spec = axis.get('normalization') or {'kind': 'score_100'}
    kind = spec.get('kind', 'score_100')
    if kind == 'score_100':
        return value / 100
    if kind == 'linear':
        lo, hi = float(spec['min']), float(spec['max'])
        if hi <= lo:
            raise ValueError(f'Invalid fit-axis range: {axis}')
        normalized = (value - lo) / (hi - lo)
        direction = spec.get('direction', 'higher')
        if direction == 'lower':
            normalized = 1 - normalized
        elif direction != 'higher':
            raise ValueError(f'Unknown fit-axis direction: {axis}')
        return normalized
    raise ValueError(f'Unknown fit-axis normalization: {kind}')


def fit_breakdown(archetype, domains, signals):
    """Rank eligible archetypes on dedicated fit axes, not gate count.

    Returns the score and the per-axis rows behind it, so a ranking can be read
    rather than trusted. A missing axis contributes zero to fit and is marked,
    which never relaxes eligibility: that is decided by the conditions.
    """
    axes = archetype.get('fit_axes')
    if not axes:
        return _legacy_fit_score(archetype, domains, signals), []
    weighted, total, rows = 0.0, 0.0, []
    for axis in axes:
        weight = float(axis['weight'])
        value = resolve(axis['field'], domains, signals)
        normalized = 0.0 if value is None else _normalize_fit_axis(axis, value)
        normalized = max(0.0, min(1.0, normalized))
        weighted += weight * normalized
        total += weight
        rows.append({'field': axis['field'], 'weight': weight, 'value': value,
                     'normalized': round(normalized, 8), 'missing': value is None})
    if total <= 0:
        raise ValueError(f'Archetype {archetype.get("id")} has no positive fit weight')
    return round(100 * weighted / total, 8), rows


def fit_score(archetype, domains, signals):
    return fit_breakdown(archetype, domains, signals)[0]


def classify(policy, domains, signals, score, score_ex_valuation, confirmed, unresolved=()):
    evaluations, fits = [], {}
    for t in sorted(policy['types'], key=lambda t:t['id']):
        checks = [(c['field'], check_condition(c, domains, signals)) for c in t['conditions']]
        gate = score_ex_valuation if t.get('valuation_tolerant') else score
        threshold = float(t.get('min_gate_score', policy['min_gate_score']))
        failed = [field for field, result in checks if result is False]
        missing = [field for field, result in checks if result is None]
        if gate is None:
            missing.append('gate_score')
        elif gate < threshold:
            failed.append('gate_score')
        blockers = sorted({v['veto'] for v in (*confirmed, *unresolved) if v['veto'] in t.get('blocked_vetoes', [])})
        fit, fit_axes = fit_breakdown(t, domains, signals)
        fits[t['id']] = {'eligible':not failed and not missing and not confirmed and not blockers,
            'fit_score':fit, 'fit_axes':fit_axes, 'failed_conditions':failed,
            'missing_conditions':missing, 'blocking_vetoes':blockers}
        evaluations.append({'id':t['id'], 'label':t['label'], 'conditions_met':all(r is True for _,r in checks),
            'gate_score':round(gate,2) if gate is not None else None, 'gate_threshold':threshold,
            'gate_passed':gate is not None and gate>=threshold, 'failed':failed, 'missing':missing})
    eligible = [key for key, fit in fits.items() if fit['eligible']]
    tie = policy['fit_policy']['tie_breaker']
    tolerance = policy['fit_policy']['tie_tolerance']
    ranked = []
    while eligible:
        best = max(fits[k]['fit_score'] for k in eligible)
        chosen = min((k for k in eligible if best-fits[k]['fit_score']<=tolerance), key=tie.index)
        ranked.append(chosen)
        eligible.remove(chosen)
    primary = ranked[0] if ranked else policy['fallback']
    types = {t['id']:t for t in policy['types']}
    selected = types.get(primary, policy['fallback_metadata'])
    reason = 'Highest eligible deterministic fit; ties use configured priority' if ranked else 'No eligible archetype: see failed/missing conditions and vetoes'
    return {'id':primary, 'label':selected['label'], 'label_en':selected['label_en'], 'reason':reason,
        'gate_score':next(e['gate_score'] for e in evaluations if e['id']==primary) if ranked else None,
        'secondary':ranked[1:], 'position_guidance':selected.get('position_guidance'),
        'position_cap':selected.get('position_cap'), 'signals':signals, 'evaluations':evaluations,
        'archetype_fit':fits}


def reachable(policy, domains, signals, confirmed, scorecard):
    if confirmed:
        return []
    possible = []
    for t in sorted(policy['types'], key=lambda t:t['id']):
        if any(check_condition(c, domains, signals) is False for c in t['conditions']):
            continue
        # Missing criteria/signals remain attainable, even in historical reports.
        rows = [r for r in scorecard if not (t.get('valuation_tolerant') and r['id']=='expectation_valuation')]
        upper = sum(((domains.get(r['id']) or {}).get('score',100))*r['weight'] for r in rows)/sum(r['weight'] for r in rows)
        if upper >= t.get('min_gate_score', policy['min_gate_score']):
            possible.append(t['id'])
    return possible
