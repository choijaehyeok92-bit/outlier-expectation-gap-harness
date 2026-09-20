"""Render executable thresholds without maintaining a second numeric policy."""
import json


def render(strategy, workflow, calibration):
    lines=[f"# Executable v{strategy['strategy_version']} policy",'',
        'Generated from config; update with `python harness.py policy --out docs/POLICY.md`.','',
        f"Strategy / schema / decision policy: {strategy['strategy_version']} / {strategy['schema_version']} / {strategy['decision_policy_version']}.",'']
    for t in strategy['archetypes']['types']:
        lines += [f"## {t['id']} — {t['label_en']}",'',
            '### Eligibility conditions','',
            '| Field | Operator | Threshold |','|---|---|---:|']
        for c in t['conditions']:
            lines += [f"| `{c['field']}` | {c['op']} | {c['value']} |"]
        if t.get('fit_axes'):
            lines += ['', '### Fit axes','',
                '| Field | Weight | Normalization |','|---|---:|---|']
            for axis in t['fit_axes']:
                spec = axis.get('normalization') or {'kind':'score_100'}
                lines += [f"| `{axis['field']}` | {axis['weight']} | `{json.dumps(spec,ensure_ascii=False,sort_keys=True)}` |"]
        gate='core excluding EV' if t.get('valuation_tolerant') else 'core'
        lines += ['',f"Gate: {gate} >= {t.get('min_gate_score',strategy['archetypes']['min_gate_score'])}.",'']
    fit=strategy['archetypes']['fit_policy']
    lines += ['## Fit and selection','',fit['note'],
        f"Tie tolerance: {fit['tie_tolerance']}; tie priority: {' > '.join(fit['tie_breaker'])}.",'',
        'All listed veto blockers remain binding; ownership coverage is required before buying.',
        '',f"Provider calibration mode: **{calibration['provider_calibration']['mode']}**.",'']
    qb=workflow['execution'].get('research_policy',{}).get('question_budget',{})
    if qb:
        lines += ['## Research budget','',
            f"- Active-question cap: {qb.get('max_active_questions')}",
            f"- Monitoring cap: {qb.get('max_monitoring_questions')}",
            f"- Optional cap: {qb.get('max_optional_questions')}",
            f"- Non-blocking per-domain cap: {qb.get('max_nonblocking_per_domain')}",
            '- Decision-blocking questions are never removed by these caps.','']
    sanity=calibration.get('valuation',{}).get('sanity_policy',{})
    if sanity:
        lines += ['## Valuation sanity','',
            f"- Yearly scenario crossing mode: {sanity.get('yearly_scenario_crossing')}",
            f"- Terminal-value review threshold: {sanity.get('terminal_fraction_review')}",
            f"- Terminal-value high threshold: {sanity.get('terminal_fraction_high')}",
            '- Sanity REVIEW flags do not auto-confirm a Hard Veto.','']
    lines += ['## Component freshness','', '| Global component | TTL hours |','|---|---:|']
    for name,hours in workflow['execution']['overlay_policy']['component_ttl_hours'].items():
        lines += [f'| {name} | {hours} |']
    lines += ['', '## State bands','', '| Minimum | Mechanical state | Position cap |','|---:|---|---|']
    for b in strategy['state_thresholds']['bands']:
        lines += [f"| {b['min']} | {b['state']} | {b['position_range']} |"]
    disp = strategy['state_thresholds'].get('dispersion_policy')
    if disp:
        lines += ['', '## Bull/bear dispersion', '', disp['note'], '', f"Metric: {disp['metric']}", '',
            '| Mean skew at least | Label | Position bands removed |', '|---:|---|---:|']
        for b in disp['bands']:
            lines += [f"| {'(any)' if b['min_skew'] is None else b['min_skew']} | {b['label']} | {b['reduce_bands']} |"]
        lines += ['', 'The spread never changes a score, an archetype or a veto, and never widens a position.', '']
    lines += ['## Observable anchor interpolation', '',
        'Continuous single-metric tables interpolate between rows; counts and gated tables stay stepped.', '',
        '| Criterion | Mode | Reachable scores (5-point grid) |', '|---|---|---|']
    from . import anchors
    for domain, rubric in sorted(calibration['rubrics'].items()):
        for criterion in rubric['criteria']:
            table = (criterion.get('observable_anchors') or {}).get('table')
            if not table:
                continue
            mode = criterion['observable_anchors'].get('interpolation', {}).get('mode', 'none')
            reachable = anchors.reachable_scores(table, calibration.get('score_step', 5))
            shown = ', '.join(f'{v:g}' for v in reachable)
            lines += [f"| `{domain}.{criterion['id']}` | {mode} | {shown} |"]
    return '\n'.join(lines)+'\n'
