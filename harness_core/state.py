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
