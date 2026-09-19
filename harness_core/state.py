"""IC may reduce deployment; deterministic eligibility and veto gates remain binding."""


def reconcile_ic(result, state_policy):
    mechanical = result['mechanical_pre_ic_state']
    position = result['position_range_pre_ic']
    ic = result.get('ic_verdict') or {}
    requested = ic.get('ic_state')
    if not requested:
        return mechanical, position, []
    policy = state_policy['ic_policy']
    if requested in policy['non_buy_states']:
        return requested, '0% new purchases; review existing holdings', []
    rank = policy['buy_state_rank'].get(requested)
    cap = policy['max_buy_rank_by_pre_ic_state'].get(mechanical, 0)
    safe = (result['coverage_weight']==100 and result['hard_veto_status']=='CLEARED'
            and result['archetype']['id']!='non_fit' and result['valuation_model']['status']=='COMPLETE'
            and not result['macro_geo_overlay']['pending_reanalysis_domains'])
    if rank is None or not safe or rank>cap:
        return mechanical, position, [f'IC request {requested} was not accepted: deterministic gates or state cap.']
    # A lower deployment recommendation cannot enlarge the mechanical position cap.
    if rank < cap:
        position = policy['position_range_by_rank'][str(rank)]
        if result['archetype'].get('position_cap'):
            position += '; also subject to '+result['archetype']['position_cap']
    return requested, position, []


def dispersion_review(domain_scores, policy):
    """Bull/bear width per domain, aggregated as downside skew.

    The spread is deliberately kept out of the score: it narrows deployment instead.
    A wide bull case never widens a position, so only positive (downside) skew acts.
    """
    if not policy:
        return None
    rows = []
    for name, row in sorted(domain_scores.items()):
        if not isinstance(row, dict):
            continue  # domain present in the manifest but not yet reported
        bull, bear = row.get('bull_score'), row.get('bear_score')
        score = row.get('decision_score', row.get('score'))
        if bull is None or bear is None or score is None:
            continue
        upside, downside = float(bull) - float(score), float(score) - float(bear)
        rows.append({'domain': name, 'spread': round(float(bull) - float(bear), 2),
                     'upside_width': round(upside, 2), 'downside_width': round(downside, 2),
                     'skew': round(downside - upside, 2)})
    if not rows:
        return None
    mean_skew = sum(r['skew'] for r in rows) / len(rows)
    band = next(b for b in policy['bands']
                if b['min_skew'] is None or mean_skew >= b['min_skew'])
    return {'metric': policy['metric'], 'mean_skew': round(mean_skew, 2),
            'label': band['label'], 'reduce_bands': band['reduce_bands'],
            'widest_domain': max(rows, key=lambda r: r['spread'])['domain'],
            'most_downside_skewed': max(rows, key=lambda r: r['skew'])['domain'],
            'by_domain': rows}


def narrowed_position(state, reduce_bands, state_policy):
    """Position range `reduce_bands` steps below `state`'s own band; never above it."""
    bands = sorted(state_policy['bands'], key=lambda b: -b['min'])
    index = next((i for i, b in enumerate(bands) if b['state'] == state), None)
    if index is None or reduce_bands <= 0:
        return None
    floor_state = (state_policy.get('dispersion_policy') or {}).get('never_below_state')
    floor = next((i for i, b in enumerate(bands) if b['state'] == floor_state), len(bands) - 1)
    return bands[min(index + reduce_bands, max(floor, index))]['position_range']
