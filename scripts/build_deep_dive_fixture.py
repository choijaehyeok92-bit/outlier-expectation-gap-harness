#!/usr/bin/env python3
"""Build the offline deep-dive fixture from a real harness run.

The fixture exists so the whole deep-dive pipeline can run, and be tested,
without a network or an API key. It is generated rather than hand-written for
one reason: hand-written fixture "evidence" is invented evidence, and this
repository's whole point is that invented evidence is not evidence.

So every fixture claim here is lifted from the run's own frozen artifacts — the
domain analysts' recorded evidence and counterevidence — and every citation
points at a file that is actually on disk, with the filing date taken from the
document's own name. The fixture still is not research: it is a replay of one
run's recorded analysis, shaped into the deep-dive contract. The report it
produces says so, because its provenance records provider=fixture.

    python scripts/build_deep_dive_fixture.py MSFT
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research import deep_plan, stages  # noqa: E402

FILING_DATE = re.compile(r'_(\d{4}-\d{2}-\d{2})_')
ASSESSMENT_BY_VERDICT = {'support': 'favorable', 'neutral': 'mixed', 'oppose': 'weak'}
# Each deep-dive domain replays the harness domain that already examined it.
DOMAIN_SOURCE = {
    'business_model': 'SL', 'industry': 'SL', 'customer_product': 'CP', 'moat': 'MT',
    'moat_trajectory': 'MT', 'growth_runway': 'CP', 'unit_economics': 'RF',
    'per_share_economics': 'RF', 'financial_quality': 'FS', 'management': 'MA',
    'capital_allocation': 'MA', 'technology_disruption': 'DI', 'risk_analysis': 'MO',
    'valuation_interpretation': 'EV',
}
QUESTION_SOURCE = {'Q1': 'SL', 'Q2': 'CP', 'Q3': 'MT', 'Q4': 'MT', 'Q5': 'RF',
                   'Q6': 'RF', 'Q7': 'EV', 'Q8': 'EV', 'Q9': 'RT', 'Q10': 'MT'}
ATTACK_VECTORS = [('moat_erosion', 'MT'), ('valuation_expectation_error', 'EV'),
                  ('technological_disruption', 'DI'), ('capital_allocation_failure', 'MA'),
                  ('regulatory_risk', 'MO')]


def publication_date(source, fallback):
    match = FILING_DATE.search(str(source or ''))
    return match.group(1) if match else fallback


def tier_for(source_type, source):
    if source_type == 'filing' or '/sources/' in str(source):
        return 1
    if source_type in ('ir', 'earnings_call', 'presentation'):
        return 2
    if str(source).startswith('runs/'):
        return 0
    return 4


def build_evidence(reports, as_of_date):
    """Evidence and counterevidence from the frozen reports, as deep-dive evidence."""
    catalog, by_agent = [], {}
    for agent_id, report in sorted(reports.items()):
        support, against = [], []
        for index, item in enumerate(report.get('evidence') or [], 1):
            eid = f'EV-{agent_id}-{index:02d}'
            catalog.append({
                'evidence_id': eid, 'claim': item.get('claim', ''), 'value': item.get('value'),
                'unit': item.get('unit'), 'source': item.get('source') or f'runs/{report["ticker"]}/reports/{agent_id}.json',
                'source_origin': item.get('source') or f'harness run {report["ticker"]}/{agent_id}',
                'source_type': item.get('source_type'),
                'source_tier': tier_for(item.get('source_type'), item.get('source')),
                'publication_date': publication_date(item.get('source'), as_of_date),
                'period': str(item.get('period') or 'n/a'), 'as_of_date': as_of_date,
                'fact_or_estimate': item.get('fact_or_estimate') or 'fact',
                'economic_driver': report['domain'], 'confidence': float(report.get('confidence_0_1') or 0.7),
                'verified_fact_refs': [], 'supports': 'harness'})
            support.append(eid)
        for index, text in enumerate(report.get('counterevidence') or [], 1):
            eid = f'CE-{agent_id}-{index:02d}'
            catalog.append({
                'evidence_id': eid, 'claim': text if isinstance(text, str) else json.dumps(text, ensure_ascii=False),
                'source': f'runs/{report["ticker"]}/reports/{agent_id}.json',
                'source_origin': f'harness run {report["ticker"]}/{agent_id} counterevidence',
                'source_type': 'harness_report', 'source_tier': 0,
                'publication_date': as_of_date, 'period': 'as recorded', 'as_of_date': as_of_date,
                'fact_or_estimate': 'interpretation', 'economic_driver': report['domain'],
                'confidence': 0.5, 'verified_fact_refs': [], 'supports': 'contradicts_harness'})
            against.append(eid)
        by_agent[agent_id] = {'support': support, 'against': against}
    return catalog, by_agent


def assessment(report, by_agent, agent_id):
    return {
        'assessment': ASSESSMENT_BY_VERDICT.get(report.get('verdict'), 'mixed'),
        'direction': 'unclear',
        'confidence': float(report.get('confidence_0_1') or 0.6),
        'thesis': report.get('thesis') or '기록된 분석 요지가 없다.',
        'supporting_evidence': by_agent[agent_id]['support'],
        'contradicting_evidence': by_agent[agent_id]['against'],
        'unknowns': list(report.get('unknowns') or []),
        'falsifiers': list(report.get('falsifiers') or []),
        'independent_of_harness': False,
    }


def build(ticker, runs_dir=None):
    config = deep_plan.load_config()
    plan = deep_plan.build(ticker, runs_dir=runs_dir, config=config, user_requested=True)
    run = Path(runs_dir or ROOT / 'runs') / ticker
    reports = {}
    for path in sorted((run / 'reports').glob('*.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        if report.get('analysis_status') == 'complete':
            reports[report['agent_id']] = report
    as_of = plan['as_of_date']
    catalog, by_agent = build_evidence(reports, as_of)
    snapshot = plan['harness_snapshot']

    qualitative = {}
    for domain in config['domains']:
        agent_id = DOMAIN_SOURCE[domain['id']]
        report = reports.get(agent_id)
        if report is None:
            raise SystemExit(f'{ticker}: {agent_id} report is missing; fixture needs a complete run')
        qualitative[domain['id']] = assessment(report, by_agent, agent_id)

    qualitative['investment_question'] = [
        {'id': item['id'], 'question': item['question'],
         'answer': (reports[QUESTION_SOURCE[item['id']]].get('thesis') or '')[:1200] or '기록된 답변이 없다.',
         'supporting_evidence': by_agent[QUESTION_SOURCE[item['id']]]['support'][:3],
         'unknowns': list(reports[QUESTION_SOURCE[item['id']]].get('unknowns') or [])[:2],
         'confidence': float(reports[QUESTION_SOURCE[item['id']]].get('confidence_0_1') or 0.6)}
        for item in config['investment_questions']]

    for key, agent_id, label in (('bull_case', 'AS', 'bull_case'), ('bear_case', 'AS', 'bear_case')):
        qualitative[key] = {
            'narrative': reports[agent_id].get(label) or f'{label} not recorded in the run.',
            'key_drivers': list(reports['SL'].get('key_kpis') and
                                [k['name'] for k in reports['SL']['key_kpis']] or ['recorded KPI set is empty']),
            'evidence': by_agent[agent_id]['support' if key == 'bull_case' else 'against'][:3],
            'what_must_be_true': list(reports[agent_id].get('falsifiers') or [])[:3]}
    qualitative['base_case'] = {
        'narrative': reports['IC'].get('thesis') or 'IC thesis not recorded.',
        'key_drivers': [k['name'] for k in (reports['EV'].get('key_kpis') or [])] or ['recorded KPI set is empty'],
        'evidence': by_agent['EV']['support'][:3],
        'what_must_be_true': list(reports['EV'].get('falsifiers') or [])[:3]}

    red_team_report = reports['RT']
    red_team = {'red_team': {
        'overall': 'unchanged',
        'supporting_harness': by_agent['ED']['support'][:3],
        'contradicting_harness': by_agent['RT']['against'][:3],
        'domains_with_material_disagreement': [],
        'reason': red_team_report.get('thesis') or 'Red Team thesis not recorded.',
        'attack_paths': [
            {'vector': vector,
             'thesis_break_mechanism': (reports[agent_id].get('bear_case')
                                        or reports[agent_id].get('thesis') or 'not recorded')[:600],
             'evidence': by_agent[agent_id]['against'][:2],
             'assessed_likelihood': 'moderate',
             'strongest_counterargument': (reports[agent_id].get('bull_case') or None)}
            for vector, agent_id in ATTACK_VECTORS if agent_id in reports]}}

    tiers = {}
    for item in catalog:
        key = str(item['source_tier'])
        tiers[key] = tiers.get(key, 0) + 1
    primary = sum(1 for item in catalog if item['source_tier'] <= 2)
    synthesis = {
        'executive_summary': (reports['IC'].get('thesis') or '')[:1500] or 'IC thesis not recorded.',
        'harness_comparison': {
            'strongest_supporting_evidence': by_agent['ED']['support'][:3],
            'strongest_contradicting_evidence': by_agent['RT']['against'][:3],
            'possible_harness_overstatement': list(reports['RT'].get('unknowns') or [])[:3],
            'possible_harness_blind_spots': list(reports['ED'].get('unknowns') or [])[:3],
            'unresolved_contradictions': list(reports['RT'].get('next_checks') or [])[:3],
            'by_domain': [
                {'domain': domain['id'],
                 'harness_score': domain['harness_reference']['score'],
                 'qualitative_assessment': qualitative[domain['id']]['assessment'],
                 'agreement': 'consistent',
                 'note': f"replayed from harness agent {DOMAIN_SOURCE[domain['id']]}"}
                for domain in plan['domains']]},
        'falsifiers': [{'statement': text, 'observable': 'as recorded by the domain analyst',
                        'would_break': 'the domain judgement this falsifier belongs to'}
                       for report in reports.values() for text in (report.get('falsifiers') or [])][:8],
        'monitoring_kpis': [
            {'name': kpi.get('name', 'unnamed'),
             'why_it_matters': f"{report['domain']} 판단의 핵심 관측값",
             'current_value': None,
             'direction_required': {'up': 'increasing', 'down': 'decreasing'}.get(kpi.get('direction'), 'stable'),
             'warning_threshold': str(kpi.get('threshold', 'not recorded')),
             'thesis_break_threshold': str(kpi.get('threshold', 'not recorded')) + ' breached for 2 consecutive periods',
             'cadence': kpi.get('cadence') if kpi.get('cadence') in
                        ('quarterly', 'semiannual', 'annual', 'event_driven', 'monthly') else 'quarterly',
             'source': f"runs/{ticker}/reports/{report['agent_id']}.json"}
            for report in reports.values() for kpi in (report.get('key_kpis') or [])][:10],
        'remaining_unknowns': sorted({u for report in reports.values() for u in (report.get('unknowns') or [])})[:10],
        'evidence_quality': {
            'tier_counts': tiers,
            'primary_share': round(primary / len(catalog), 4) if catalog else 0.0,
            'independent_origins': len({item['source_origin'] for item in catalog}),
            'concerns': ['Fixture replay of one frozen run; it is not independent research '
                         'and must not be read as external corroboration.']},
        'final_synthesis': {
            'thesis': (reports['IC'].get('thesis') or 'IC thesis not recorded.')[:1500],
            'what_must_be_true': list(reports['IC'].get('falsifiers') or reports['EV'].get('falsifiers') or
                                      ['not recorded'])[:4],
            'what_would_change_our_mind': list(reports['RT'].get('falsifiers') or ['not recorded'])[:4],
            'agreement_with_harness': 'consistent',
            'decision_authority': 'Harness 결정 권한은 그대로다. 이 보고서는 근거를 설명할 뿐 점수·Veto·포지션을 바꾸지 않는다.'},
    }

    destination = ROOT / 'packages' / 'research' / 'fixtures' / ticker
    destination.mkdir(parents=True, exist_ok=True)
    payloads = {'deep_research': {'evidence': catalog}, 'qualitative': qualitative,
                'red_team': red_team, 'synthesis': synthesis}
    master = stages.report_schema()
    import jsonschema
    for stage, payload in payloads.items():
        jsonschema.validate(payload, stages.stage_schema(stage, master))
        (destination / f'{stage}.json').write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {len(payloads)} stage fixtures for {ticker} -> {destination.relative_to(ROOT)}')
    print(f'  evidence: {len(catalog)} items, snapshot core_score={snapshot["core_score"]}')


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'MSFT')
