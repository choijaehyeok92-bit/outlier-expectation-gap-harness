"""Report-layer invariants: a deep report must agree with the verdict it explains.

    validate_deep_report(context, markdown, final)   pure; JSON + markdown vs final_verdict.json
    validate_narrative(narrative, bundle, context)   pure; guards the optional model-written text
    validate_run_report(runtime, run_id)              IO; everything above for one run on disk
"""
from __future__ import annotations

import bisect
import json
import re

from .report_builder import authority_from_final, fmt_num, load_bundle, parse_authority, report_tier, _cell

FORBIDDEN_KEYS = {'target_price', 'price_target', 'recommended_position', 'recommendation', 'new_score',
                  'score_override', 'archetype_override', 'ic_state_override', 'position_override'}
DECISION_KEYS = {'score', 'score_100', 'archetype', 'archetype_fit', 'hard_veto_status', 'ic_state',
                 'position_range', 'mechanical_pre_ic_state', 'macro_pacing_multiplier', 'valuation'}
VISIBLE = (('IC State', 'ic_state'), ('Position Range', 'position_range'), ('Archetype', 'archetype'),
           ('Hard Veto', 'hard_veto_status'), ('Score', 'score_100'))


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _canonical(value):
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


def validate_deep_report(context, markdown, final, state_policy):
    out = []
    if not final:
        return [('ERROR', 'deep report exists but final_verdict.json is missing')]
    expected = _canonical(authority_from_final(final, state_policy))
    got = _canonical(context.get('authority') or {})
    for key, value in expected.items():
        if got.get(key) != value:
            out.append(('ERROR', f'deep_report.json {key} {got.get(key)!r} != final_verdict {value!r}'))
    embedded = parse_authority(markdown)
    if embedded is None:
        out.append(('ERROR', 'deep_report.md has no harness-authority block'))
    elif _canonical(embedded) != expected:
        diff = sorted(k for k in expected if _canonical(embedded).get(k) != expected[k])
        out.append(('ERROR', f'deep_report.md authority block disagrees with final_verdict on {diff}'))
    for label, key in VISIBLE:
        match = re.search(r'^\| ' + re.escape(label) + r' \| (.*?) \|$', markdown or '', re.M)
        value = expected.get(key)
        shown = _cell(fmt_num(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)
        if not match:
            out.append(('ERROR', f'deep_report.md does not show {label}'))
        elif match.group(1) != shown:
            out.append(('ERROR', f'deep_report.md shows {label} {match.group(1)!r}, final_verdict has {shown!r}'))
    bad = sorted(set(_walk_keys(context)) & FORBIDDEN_KEYS)
    if bad:
        out.append(('ERROR', f'deep report carries forbidden decision keys {bad}'))
    return out


# ------------------------------------------------------------------ narrative

NUMBER = re.compile(r'(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(\s?%)?')


def numbers_in(text, with_percent=False):
    """Numeric tokens; with_percent=True yields (value, written_as_percent)."""
    values = []
    for match in NUMBER.finditer(str(text)):
        raw = match.group(0).rstrip('% ').rstrip(',')
        try:
            value = float(raw.replace(',', ''))
        except ValueError:
            continue
        values.append((value, bool(match.group(1))) if with_percent else value)
    return values


def number_corpus(bundle, context):
    texts = [json.dumps(x, ensure_ascii=False) for x in (bundle.get('final'), bundle.get('aggregate'),
                                                        bundle.get('context'), context.get('derived'))]
    texts += [json.dumps(r, ensure_ascii=False) for r in bundle.get('reports', {}).values()]
    texts.append(bundle.get('one_page') or '')
    corpus = sorted({v for t in texts for v in numbers_in(t)})
    return corpus


def _known(value, corpus, tolerance, percent=False):
    # "33%" may be recorded as 0.33; any other number must match as written.
    for candidate in ((value, value / 100) if percent else (value,)):
        span = max(abs(candidate) * tolerance, 0.005)
        index = bisect.bisect_left(corpus, candidate - span)
        if index < len(corpus) and corpus[index] <= candidate + span:
            return True
    return False


def validate_narrative(narrative, bundle, context, policy):
    """Errors (strings) for a model-written narrative; empty means it may be merged."""
    errors = []
    if not isinstance(narrative, dict):
        return ['narrative must be a JSON object']
    extra = sorted(set(narrative) - set(policy['allowed_top_level_keys']))
    if extra:
        errors.append(f'unexpected top-level keys {extra}')
    ticker = str(narrative.get('ticker') or '').upper()
    if ticker not in {str(context.get('ticker') or '').upper(), str(context.get('run_id') or '').upper()}:
        errors.append(f"narrative ticker {narrative.get('ticker')!r} does not match {context.get('run_id')}")
    if narrative.get('as_of_date') != context.get('as_of_date'):
        errors.append(f"narrative as_of_date {narrative.get('as_of_date')!r} != {context.get('as_of_date')}")
    sections = narrative.get('sections')
    if not isinstance(sections, dict) or not sections:
        return errors + ['sections must be a non-empty object keyed by section id']
    run_path = bundle['run_path']
    allowed = {s['path'] for s in bundle['sources'].values()} | {f'{run_path}/reports/{aid}.json' for aid in bundle['reports']}
    valid_ids = {f'{i:02d}' for i in range(22)}
    corpus = number_corpus(bundle, context)
    tolerance = float(policy.get('number_tolerance_relative', 0.005))
    free_int = int(policy.get('free_integers_up_to', 10))
    years = policy.get('free_year_range', [1990, 2100])
    for sid, entry in sections.items():
        where = f'section {sid}'
        if sid not in valid_ids:
            errors.append(f'{where}: unknown section id')
            continue
        if not isinstance(entry, dict):
            errors.append(f'{where}: must be an object with text and sources')
            continue
        keys = set(entry) - {'text', 'sources'}
        if keys & DECISION_KEYS or keys & FORBIDDEN_KEYS:
            errors.append(f'{where}: decision fields are not narrative ({sorted(keys)})')
        elif keys:
            errors.append(f'{where}: unexpected keys {sorted(keys)}')
        text = entry.get('text')
        if not isinstance(text, str) or not text.strip():
            errors.append(f'{where}: text is required')
            continue
        if len(text) > int(policy['max_chars_per_section']):
            errors.append(f"{where}: {len(text)} chars > {policy['max_chars_per_section']}")
        lowered = text.lower()
        for term in policy['forbidden_terms']:
            if term.lower() in lowered:
                errors.append(f'{where}: forbidden phrase {term!r} (the report never recommends or targets)')
        sources = entry.get('sources')
        if not isinstance(sources, list) or not sources:
            errors.append(f'{where}: sources must be a non-empty list')
        else:
            for source in sources:
                path = str(source).split('#', 1)[0]
                path = path if path.startswith(run_path + '/') else f'{run_path}/{path}'
                if path not in allowed:
                    errors.append(f'{where}: source {source!r} is not a recorded artifact of this run')
        for value, percent in numbers_in(text, with_percent=True):
            if value.is_integer() and (value <= free_int or years[0] <= value <= years[1]):
                continue
            if not _known(value, corpus, tolerance, percent):
                errors.append(f'{where}: number {fmt_num(value, 4)} does not appear in the recorded artifacts')
    return errors


# ------------------------------------------------------------------ one run on disk

def validate_run_report(runtime, run_id, reader, row=None):
    """Findings for runs/<RUN>/deep_report.{json,md}. [(level, message)]"""
    from .universe_store import load_policy
    run = runtime.run_dir(run_id)
    label = run_id
    policy = load_policy(runtime.ROOT)['report_policy']
    json_path, md_path = run/'deep_report.json', run/'deep_report.md'
    bundle = load_bundle(runtime, run_id, reader)
    final = bundle['final']
    ic_complete = bundle['report_status'].get('IC') == 'complete'
    out = []
    if not json_path.exists() and not md_path.exists():
        if final:
            tier, reason = report_tier(final, ic_complete, policy)
            if tier != 'none':
                out.append(('INFO', f'{label}: no deep report yet (policy tier {tier}: {reason})'))
        return out
    if not (json_path.exists() and md_path.exists()):
        return [('ERROR', f'{label}: deep_report.json and deep_report.md must exist together')]
    context = json.loads(json_path.read_text(encoding='utf-8'))
    markdown = md_path.read_text(encoding='utf-8')
    out += [(lvl, f'{label}: {m}') for lvl, m in validate_deep_report(context, markdown, final, runtime.STATE_POLICY)]
    if not final:
        return out
    recorded = ((context.get('authority_sources') or {}).get('final_verdict') or {}).get('sha256')
    current = (bundle['sources'].get('final_verdict') or {}).get('sha256')
    if recorded and current and recorded != current:
        out.append(('WARNING', f'{label}: final_verdict.json changed after the deep report was generated; regenerate it'))
    expected_tier, reason = report_tier(final, ic_complete, policy, bool(context.get('forced')))
    if not context.get('forced') and expected_tier != context.get('tier'):
        out.append(('WARNING', f"{label}: report tier {context.get('tier')} but policy gives {expected_tier} ({reason})"))
    if final.get('early_exit') and not context.get('forced'):
        out.append(('WARNING', f'{label}: early-exit run carries a deep report without --force'))
    narrative = context.get('narrative') or {}
    if narrative.get('status') == 'merged':
        path = run/policy['narrative']['file']
        if not path.exists():
            out.append(('WARNING', f'{label}: merged RP narrative file is gone'))
        else:
            errors = validate_narrative(json.loads(path.read_text(encoding='utf-8')), bundle, context, policy['narrative'])
            out += [('ERROR', f'{label}: RP narrative: {e}') for e in errors]
    if row is not None:
        if row.get('report_tier') and row.get('report_tier') != context.get('tier'):
            out.append(('WARNING', f"{label}: universe report_tier {row.get('report_tier')} != deep report {context.get('tier')}"))
    return out
