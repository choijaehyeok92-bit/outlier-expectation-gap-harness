"""Config-driven eligibility, explicit fit ranking, and optimistic reachability."""
from .conditions import check_condition, resolve


def fit_score(archetype, domains, signals):
    weighted, total = 0.0, 0.0
    for c in archetype['conditions']:
        weight = float(c['fit_weight'])
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
        fits[t['id']] = {'eligible':not failed and not missing and not confirmed and not blockers,
            'fit_score':fit_score(t, domains, signals), 'failed_conditions':failed,
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
