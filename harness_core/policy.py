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
    dil=calibration.get('dilution_policy',{})
    if dil:
        lines += ['## Dilution watch','', dil['note'],'',
            f"Metric: {dil['metric']}",'',
            '| Annualized dilution at least | Watch status | Position cap |','|---:|---|---|']
        for band in sorted(dil['bands'], key=lambda b: (b.get('min') is None, -(b.get('min') or 0))):
            edge = '(any)' if band.get('min') is None else band['min']
            lines += [f"| {edge} | {band['status']} | {band.get('position_cap') or '—'} |"]
        lines += ['', f"Escalates one band when: {', '.join(dil.get('escalate_one_band_if', [])) or '—'}.",
            f"Position cap applies to: {', '.join(dil.get('applies_position_cap_to_archetypes', [])) or '—'}.",
            '', dil['relation_to_hard_veto'], '']
    veto_defs=calibration.get('veto_criteria',{}).get('definitions',{})
    gated={name:d for name,d in veto_defs.items() if d.get('requires_element_assessment')}
    if gated:
        lines += ['## Element-gated Hard Vetoes','',
            'These vetoes cannot reach `confirmed` or `conditional` on prose. The owner answers every element; '
            '`conditional` leaves exactly one unmet and names the decisive missing evidence.','']
        for name,d in gated.items():
            lines += [f'### {name}','']
            lines += [f"{i}. {element}" for i,element in enumerate(d.get('elements',[]),1)]
            thresholds=d.get('thresholds') or {}
            if thresholds:
                lines += ['', '| Threshold | Value |','|---|---:|']
                lines += [f'| `{k}` | {v} |' for k,v in thresholds.items()]
            lines += ['', 'Not covered: '+d.get('not_covered',''), '']
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
