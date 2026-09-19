"""Render executable thresholds without maintaining a second numeric policy."""


def render(strategy, workflow, calibration):
    lines=['# Executable v3 policy','',
        'Generated from config; update with `python harness.py policy --out docs/POLICY.md`.','',
        f"Strategy / schema / decision policy: {strategy['strategy_version']} / {strategy['schema_version']} / {strategy['decision_policy_version']}.",'']
    for t in strategy['archetypes']['types']:
        lines += [f"## {t['id']} — {t['label_en']}",'','| Field | Operator | Threshold | Fit weight |','|---|---|---:|---:|']
        for c in t['conditions']:
            lines += [f"| `{c['field']}` | {c['op']} | {c['value']} | {c['fit_weight']} |"]
        gate='core excluding EV' if t.get('valuation_tolerant') else 'core'
        lines += ['',f"Gate: {gate} >= {t.get('min_gate_score',strategy['archetypes']['min_gate_score'])}.",'']
    fit=strategy['archetypes']['fit_policy']
    lines += ['## Fit and selection','',fit['note'],
        f"Tie tolerance: {fit['tie_tolerance']}; tie priority: {' > '.join(fit['tie_breaker'])}.",'',
        'All listed veto blockers remain binding; ownership coverage is required before buying.',
        '',f"Provider calibration mode: **{calibration['provider_calibration']['mode']}**.",'',
        '## Component freshness','', '| Global component | TTL hours |','|---|---:|']
    for name,hours in workflow['execution']['overlay_policy']['component_ttl_hours'].items():
        lines += [f'| {name} | {hours} |']
    lines += ['', '## State bands','', '| Minimum | Mechanical state | Position cap |','|---:|---|---|']
    for b in strategy['state_thresholds']['bands']:
        lines += [f"| {b['min']} | {b['state']} | {b['position_range']} |"]
    return '\n'.join(lines)+'\n'
