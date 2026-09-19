"""Provider offsets are research-only unless active mode is explicitly selected."""


def provider_family(manifest, policy):
    runner = (manifest or {}).get('runner') or {}
    hay = ' '.join(str(runner.get(k) or '') for k in ('provider','model')).lower()
    return next((fam for fam in policy.get('families',[]) if any(tok in hay for tok in fam['match'])), None)


def apply(domains, manifest, policy, rubrics):
    mode = (manifest or {}).get('provider_calibration_mode', policy.get('mode','shadow'))
    if mode not in ('shadow','active'):
        raise ValueError(f'Unknown provider calibration mode: {mode}')
    family = provider_family(manifest, policy)
    applied = bool(policy.get('enabled') and family)
    base, cap = float(policy['base_offset']), float(policy['max_abs_offset'])
    offsets = {}
    for domain, meta in domains.items():
        if not meta:
            continue
        criteria = rubrics.get(domain,{}).get('criteria',[])
        uncovered = sum('observable_anchors' not in c and 'signal_map' not in c for c in criteria)/len(criteria) if criteria else 0
        offset = max(-cap,min(cap,base*family['sign']*uncovered)) if applied else 0.0
        # Idempotent: repeated calls never compound offsets.
        raw = meta.get('raw_score', meta['score'])
        calibrated = round(max(0,min(100,raw+offset)),2)
        meta.update(raw_score=raw, calibrated_score=calibrated, calibrated_shadow_score=calibrated,
            decision_score=calibrated if mode=='active' else raw, provider_offset=round(offset,2),
            score_before_provider_calibration=raw, raw_before_provider_calibration=meta['raw_weighted_median'])
        meta['score'] = meta['decision_score']
        offsets[domain] = round(offset,2)
    return {'mode':mode,'applied':applied,'decision_effect':applied and mode=='active',
        'family':family['id'] if family else None, 'base_offset':base,'max_abs_offset':cap,
        'per_domain_offset':offsets,'basis':policy.get('basis'),
        'reason':None if applied else 'disabled or provider family not recognised'}
