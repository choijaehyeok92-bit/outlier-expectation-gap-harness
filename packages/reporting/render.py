"""Markdown rendering.

Rendering makes no decisions. It reads a validated document and lays it out, so
a number in the output is a number the harness wrote and a judgement is one the
qualitative stage recorded. The one thing it adds is a warning: a report whose
provenance says `fixture` is a replay, not research, and every rendering of one
says so at the top where it cannot be missed.
"""

ASSESSMENT_KO = {'strong': '강함', 'favorable': '우호적', 'mixed': '혼재', 'weak': '약함', 'critical': '치명적'}
DIRECTION_KO = {'strengthening': '강화', 'stable': '유지', 'weakening': '약화', 'unclear': '불명확'}
SECTIONS = [
    ('business_model', 'Business Model'), ('industry', 'Industry & Competitors'),
    ('customer_product', 'Customer & Product'), ('moat', 'Moat'),
    ('moat_trajectory', 'Moat Trajectory'), ('growth_runway', 'Growth Runway'),
    ('unit_economics', 'Unit Economics'), ('per_share_economics', 'Per-Share Economics'),
    ('financial_quality', 'Financial Quality'), ('management', 'Management & Governance'),
    ('capital_allocation', 'Capital Allocation'), ('technology_disruption', 'Technology / Disruption'),
    ('risk_analysis', 'Regulatory & Geopolitical Risk'),
    ('valuation_interpretation', 'Market Expectations & Valuation'),
]


def is_fixture(report):
    stages = ((report.get('metadata') or {}).get('provenance') or {}).get('stages') or []
    return any(stage.get('provider') == 'fixture' for stage in stages)


def _bullets(items, empty='없음'):
    items = [i for i in (items or []) if i]
    return '\n'.join(f'- {i}' for i in items) if items else f'- {empty}'


def render_markdown(report):
    metadata = report['metadata']
    snapshot = report['harness_snapshot']
    lines = []
    if is_fixture(report):
        lines += ['> **FIXTURE REPLAY — 실제 리서치가 아니다.** 이 보고서는 고정된 하네스 run의 기록을 '
                  '딥다이브 계약 형태로 재생한 것이다. 외부 검증이나 독립 조사로 읽어서는 안 된다.', '']
    lines += [
        f"# Deep Dive — {metadata['ticker']} ({metadata.get('company_name') or '-'})",
        f"기준일 {metadata['as_of_date']} · 관할 {metadata['jurisdiction']} · "
        f"harness run `{metadata['harness_run']['run_id']}` · id `{metadata['deep_dive_id']}`",
        '',
        '## Harness Snapshot (읽기 전용)',
        '| 항목 | 값 |', '|---|---|',
        f"| Core score | {snapshot.get('core_score')} |",
        f"| Ex-valuation score | {snapshot.get('ex_valuation_score')} |",
        f"| Classification | {snapshot.get('classification')} |",
        f"| Archetype | {snapshot.get('archetype')} |",
        f"| Hard Veto | {snapshot.get('hard_veto_status')} |",
        f"| IC state | {snapshot.get('ic_state')} |",
        f"| Position range | {snapshot.get('position_range')} |",
        f"| Price / Base | {snapshot.get('price_to_base_value')} |",
        '',
        '## Executive Summary', report['executive_summary'], '',
        '## 투자 10문답', '',
    ]
    for item in report['investment_question']:
        lines += [f"**{item['id']}. {item['question']}**", '', item['answer'],
                  f"_근거_: {', '.join(item['supporting_evidence']) or '없음'} · "
                  f"_확신도_ {item['confidence']}", '']

    for key, title in SECTIONS:
        section = report[key]
        lines += [
            f'## {title}',
            f"판정 **{ASSESSMENT_KO.get(section['assessment'], section['assessment'])}** · "
            f"방향 **{DIRECTION_KO.get(section['direction'], section['direction'])}** · "
            f"확신도 {section['confidence']}",
            '', section['thesis'], '',
            f"- 지지 증거: {', '.join(section['supporting_evidence']) or '없음'}",
            f"- 반박 증거: {', '.join(section['contradicting_evidence']) or '없음'}",
            '', '**남은 미확인**', _bullets(section['unknowns']),
            '', '**반증조건**', _bullets(section['falsifiers']), '']

    for key, title in (('bull_case', 'Bull Case'), ('base_case', 'Base Case'), ('bear_case', 'Bear Case')):
        case = report[key]
        lines += [f'## {title}', case['narrative'], '',
                  '**핵심 동인**', _bullets(case['key_drivers']),
                  '', f"_근거_: {', '.join(case.get('evidence') or []) or '없음'}", '']

    red_team = report['red_team']
    lines += ['## Red Team', f"종합 판정: **{red_team['overall']}**", '', red_team['reason'], '']
    for path in red_team['attack_paths']:
        lines += [f"### {path['vector']} ({path['assessed_likelihood']})", path['thesis_break_mechanism'],
                  '', f"_근거_: {', '.join(path.get('evidence') or []) or '없음'}", '']
    if red_team['domains_with_material_disagreement']:
        lines += ['**하네스와 실질적으로 불일치하는 도메인**',
                  _bullets(red_team['domains_with_material_disagreement']), '']

    comparison = report['harness_comparison']
    lines += ['## Harness 비교',
              '**하네스를 지지하는 가장 강한 증거**', _bullets(comparison['strongest_supporting_evidence']),
              '', '**하네스를 반박하는 가장 강한 증거**', _bullets(comparison['strongest_contradicting_evidence']),
              '', '**하네스가 과대평가했을 수 있는 지점**', _bullets(comparison['possible_harness_overstatement']),
              '', '**하네스가 놓쳤을 수 있는 지점**', _bullets(comparison['possible_harness_blind_spots']),
              '', '**해소되지 않은 모순**', _bullets(comparison['unresolved_contradictions']), '',
              '| 도메인 | Harness | 정성판정 | 일치 |', '|---|---|---|---|']
    for row in comparison['by_domain']:
        lines.append(f"| {row['domain']} | {row['harness_score']} | "
                     f"{ASSESSMENT_KO.get(row['qualitative_assessment'], row['qualitative_assessment'])} | "
                     f"{row['agreement']} |")

    lines += ['', '## Falsifiers', '', '| 조건 | 관측값 | 무엇이 깨지는가 |', '|---|---|---|']
    for row in report['falsifiers']:
        lines.append(f"| {row['statement']} | {row['observable']} | {row['would_break']} |")

    lines += ['', '## Monitoring KPIs', '',
              '| KPI | 왜 중요한가 | 현재 | 방향 | 경고 | thesis 폐기 | 주기 | 출처 |',
              '|---|---|---|---|---|---|---|---|']
    for kpi in report['monitoring_kpis']:
        lines.append(f"| {kpi['name']} | {kpi['why_it_matters']} | {kpi['current_value']} | "
                     f"{kpi['direction_required']} | {kpi['warning_threshold']} | "
                     f"{kpi['thesis_break_threshold']} | {kpi['cadence']} | {kpi['source']} |")

    quality = report['evidence_quality']
    synthesis = report['final_synthesis']
    lines += ['', '## 남은 미확인', _bullets(report['remaining_unknowns']),
              '', '## 증거 품질',
              f"- tier 분포: {quality['tier_counts']}",
              f"- 1차 자료 비중: {quality['primary_share']}",
              f"- 독립 출처 수: {quality['independent_origins']}",
              '', _bullets(quality['concerns']),
              '', '## 최종 종합', synthesis['thesis'], '',
              '**반드시 성립해야 하는 것**', _bullets(synthesis['what_must_be_true']),
              '', '**판단을 바꿀 관측값**', _bullets(synthesis['what_would_change_our_mind']),
              '', f"하네스와의 관계: **{synthesis['agreement_with_harness']}**",
              '', f"_{synthesis['decision_authority']}_", '']
    return '\n'.join(lines) + '\n'


def render_screen_markdown(record):
    spec = record['spec']
    summary = record['summary']
    lines = [f"# Screen — {record['screen_run_id']}",
             f"기준일 {record['as_of_date']} · backend `{record['backend']}` · "
             f"{summary['matched_count']}/{summary['considered']} matched", '']
    query = (spec.get('source') or {}).get('text')
    if query:
        lines += [f'> {query}', '']
    if spec.get('unresolved_conditions'):
        lines += ['## 해석되지 않은 조건', '', '| 원문 | 사유 | 상세 |', '|---|---|---|']
        for row in spec['unresolved_conditions']:
            lines.append(f"| {row['text']} | {row['reason']} | {row.get('detail') or ''} |")
        lines.append('')
    lines += ['## 결과', '',
              '| # | Ticker | Company | 시장 | MCap(USD) | Core | Ex-Val | Archetype | '
              'Veto | MT | P/Base | IC state |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for index, row in enumerate(record['results'], 1):
        lines.append(
            f"| {index} | {row['ticker']} | {row.get('company_name') or '-'} | {row['jurisdiction']} | "
            f"{row.get('market_cap_usd')} | {row.get('core_score')} | {row.get('ex_valuation_score')} | "
            f"{row.get('archetype')} | {row.get('hard_veto_status')} | "
            f"{(row.get('domain_scores') or {}).get('moat_trajectory')} | "
            f"{row.get('price_to_base_value')} | {row.get('ic_state')} |")
    if summary.get('excluded_missing_data'):
        lines += ['', '## 값이 없어 제외된 종목 (0으로 간주하지 않는다)', '']
        for row in summary['excluded_missing_data']:
            lines.append(f"- {row['ticker']}: {', '.join(row['missing_fields'])}")
    return '\n'.join(lines) + '\n'
