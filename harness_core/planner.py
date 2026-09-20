"""Stages are computed from reachability, coverage, and explicit activation."""


def diagnostic_enabled(context):
    return context.get('diagnostics',{}).get('turnaround_candidate',False) is True


def next_stage(reports, result, context, manifest, core_domains, triage_domains, policy, veto_reviewers):
    complete = {r['agent_id'] for r in reports if r.get('analysis_status')=='complete'}
    pending = {a['domain']:a['agent_id'] for a in manifest if a['agent_id'] not in complete}
    missing_assessments={aid for item in result['veto_gate']['items'] for aid in item['missing_assessments']}
    pending.update({a['domain']:a['agent_id'] for a in manifest if a['agent_id'] in missing_assessments})
    triage = {d:pending[d] for d in triage_domains if d in pending}
    if triage:
        return {'stage':'triage','agents':triage}
    reanalysis = result['macro_geo_overlay']['pending_reanalysis_domains']
    if reanalysis:
        return {'stage':'fundamental_reanalysis','agents':{a['domain']:a['agent_id'] for a in manifest if a['domain'] in reanalysis}}
    if result['early_exit']:
        return {'stage':'early_exit','agents':{},'early_exit_record':result['early_exit_record']}
    reachable = set(result['reachable_archetypes_raw'])
    needed = set(core_domains)  # full score coverage is required for any buy state
    needed |= {c['field'].split('.')[1] for t in policy['types'] if t['id'] in reachable for c in t['conditions'] if c['field'].startswith(('domain.','criterion.'))}
    owners = {aid for ids in veto_reviewers.values() for aid in ids}
    needed |= {a['domain'] for a in manifest if a['agent_id'] in owners and a['role']=='domain_analyst'}
    if diagnostic_enabled(context):
        needed.add('turnaround_quality')
    if result['macro_geo_overlay']['missing_or_stale_components'] and not (result.get('review_only') and 'MO' in complete):
        pending['macro_overlay']=next(a['agent_id'] for a in manifest if a['domain']=='macro_overlay')
    stages = [('domain_analysis',sorted(needed-set(triage_domains))), ('macro',['macro_overlay']),
              ('evidence_and_red_team',['evidence_quality','red_team']), ('ic',['investment_committee'])]
    for stage, domains in stages:
        todo = {d:pending[d] for d in domains if d in pending}
        if todo:
            return {'stage':stage,'agents':todo}
    return {'stage':'complete','agents':{}}


def early_exit_record(result, policy, stage, last_reachable):
    fits = result['archetype_fit']
    eliminated = {}
    for t in policy['types']:
        fit = fits[t['id']]
        failed = [c for c in t['conditions'] if c['field'] in fit['failed_conditions']]
        eliminated[t['id']] = {'failed_conditions':failed, 'missing_conditions':fit['missing_conditions'],
            'gate_failed':'gate_score' in fit['failed_conditions'],'blocking_vetoes':fit['blocking_vetoes']}
    return {'stage':stage,'last_reachable_archetypes':last_reachable,
        'reachability_history_method':'Deterministic replay in manifest order; not a claim about wall-clock execution order.',
        'eliminated_archetypes':eliminated,'confirmed_vetoes':result['confirmed_vetoes'],
        'unresolved_vetoes':result['unresolved_vetoes'],'pending_vetoes':result['veto_gate']['pending'],
        'future_reentry':{'required_conditions':eliminated,'requirements':['New evidence must satisfy all gates for at least one archetype.','Complete core coverage, deterministic valuation and all veto ownership before any buy.']},
        'ic_intentionally_not_run':True,'statement':'IC was intentionally not run because no investable archetype remains reachable.'}
