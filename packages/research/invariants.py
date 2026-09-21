"""Checks the JSON Schema cannot express.

A schema can insist that `contradicting_evidence` is an array. It cannot insist
that the array is not empty everywhere at once, which is exactly what
positive-only research looks like. It cannot check that an evidence id points
at evidence that exists, that nothing cited was published after the cutoff, or
that the harness snapshot in the report is still the harness's own numbers.

So these rules live here, they return error strings rather than raising one at
a time, and a report that fails any of them is not written.

The rule worth spelling out is the last one. A deep dive exists to test the
harness, not to ratify it. A domain assessment that cites no contradicting
evidence and declares no unknown has not looked; it is rejected, and an analyst
who genuinely found nothing against the thesis says so as an unknown ("no
disconfirming disclosure found in X") rather than by leaving the field empty.
"""
from datetime import date


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def check(report, config, expected_snapshot=None, domain_keys=()):
    errors = []
    as_of = _date((report.get('metadata') or {}).get('as_of_date'))
    rules = (config or {}).get('report_invariants', {})

    evidence = report.get('evidence') or []
    known = {e.get('evidence_id') for e in evidence}
    if len(known) != len(evidence):
        errors.append('duplicate evidence_id in the evidence catalog')

    if rules.get('evidence_must_predate_as_of_date', True) and as_of:
        for item in evidence:
            published = _date(item.get('publication_date'))
            if published is None:
                errors.append(f"{item.get('evidence_id')}: publication_date is unreadable")
            elif published > as_of:
                errors.append(f"{item.get('evidence_id')}: published {item['publication_date']} "
                              f'after the as-of cutoff {as_of.isoformat()}')
            if item.get('as_of_date') != (report.get('metadata') or {}).get('as_of_date'):
                errors.append(f"{item.get('evidence_id')}: as_of_date differs from the report cutoff")

    def refs(path, ids):
        for eid in ids or []:
            if eid not in known:
                errors.append(f'{path}: evidence id {eid} is not in the evidence catalog')

    for key in domain_keys:
        section = report.get(key) or {}
        refs(f'{key}.supporting_evidence', section.get('supporting_evidence'))
        refs(f'{key}.contradicting_evidence', section.get('contradicting_evidence'))
        if rules.get('require_contradicting_evidence_or_unknowns', True):
            if not section.get('contradicting_evidence') and not section.get('unknowns'):
                errors.append(f'{key}: no contradicting evidence and no declared unknown — '
                              'positive-only research is not accepted')

    for key in ('bull_case', 'base_case', 'bear_case'):
        refs(f'{key}.evidence', (report.get(key) or {}).get('evidence'))
    for item in report.get('investment_question') or []:
        refs(f"investment_question.{item.get('id')}", item.get('supporting_evidence'))

    red_team = report.get('red_team') or {}
    if rules.get('require_red_team', True):
        if not red_team:
            errors.append('red_team is required and was not produced')
        else:
            minimum = int(rules.get('min_red_team_vectors', 3))
            vectors = {path.get('vector') for path in red_team.get('attack_paths') or []}
            if len(vectors) < minimum:
                errors.append(f'red_team covers {len(vectors)} attack vectors; at least {minimum} are required')
            for path in red_team.get('attack_paths') or []:
                refs(f"red_team.{path.get('vector')}", path.get('evidence'))
            refs('red_team.supporting_harness', red_team.get('supporting_harness'))
            refs('red_team.contradicting_harness', red_team.get('contradicting_harness'))

    comparison = report.get('harness_comparison') or {}
    refs('harness_comparison.strongest_supporting_evidence', comparison.get('strongest_supporting_evidence'))
    refs('harness_comparison.strongest_contradicting_evidence', comparison.get('strongest_contradicting_evidence'))

    # A disagreement found in the comparison must survive into the Red Team
    # record; that is where a later reader looks for it.
    disagreed = {row['domain'] for row in comparison.get('by_domain') or []
                 if row.get('agreement') == 'material_disagreement'}
    persisted = set(red_team.get('domains_with_material_disagreement') or [])
    for domain in sorted(disagreed - persisted):
        errors.append(f'{domain}: material disagreement recorded in harness_comparison but dropped '
                      'from red_team.domains_with_material_disagreement')
    if disagreed and red_team.get('overall') not in ('material_disagreement', 'weakened'):
        errors.append('material domain disagreement present but red_team.overall does not reflect it')

    if rules.get('require_falsifiers', True) and not report.get('falsifiers'):
        errors.append('falsifiers are required')
    if rules.get('require_monitoring_kpis', True) and not report.get('monitoring_kpis'):
        errors.append('monitoring KPIs are required')

    if expected_snapshot is not None and report.get('harness_snapshot') != expected_snapshot:
        errors.append('harness_snapshot does not match the harness run; the deep dive may not '
                      'alter a harness score, archetype, veto status or position range')

    if rules.get('forbid_new_composite_score', True):
        for key in domain_keys:
            for field in (report.get(key) or {}):
                if field not in ('assessment', 'direction', 'confidence', 'thesis', 'supporting_evidence',
                                 'contradicting_evidence', 'unknowns', 'falsifiers', 'independent_of_harness'):
                    errors.append(f'{key}.{field}: qualitative sections carry no extra fields; '
                                  'a new composite score is never produced')

    required_questions = {item['id'] for item in (config or {}).get('investment_questions', [])}
    answered = {item.get('id') for item in report.get('investment_question') or []}
    for missing in sorted(required_questions - answered):
        errors.append(f'investment question {missing} was not answered')

    return errors
