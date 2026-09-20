"""Explain a fresh harness result without making another investment decision."""
import html

STATES = {
    'WATCH': '지켜보기 — 신규 매수 보류', 'REJECT': '현재 기준에서 투자 제외',
    'INCOMPLETE': '분석 미완료', 'EARLY_EXIT_NON_FIT': '유형 조건 미충족으로 분석 종료',
    'STARTER_OR_WATCH': '소액 검토 또는 관찰 단계', 'STARTER': '소액 투자 검토',
    'NORMAL': '일반 투자 검토', 'HIGH_CONVICTION': '높은 확신의 투자 검토',
    'CORE_WINNER': '핵심 보유 검토', 'EXCEPTIONAL_WINNER': '최상위 보유 검토',
    'HOLD_REVIEW': '기존 보유분 재검토', 'TRIM_THESIS_RISK': '투자가설 위험으로 축소 검토',
    'EXIT_THESIS_BROKEN': '투자가설 훼손으로 정리 검토',
    'NORMAL_CANDIDATE': '일반 투자 후보', 'CORE_WINNER_CANDIDATE': '핵심 보유 후보',
    'EXCEPTIONAL_WINNER_CANDIDATE': '최상위 보유 후보',
}
TYPES = {
    'compounder': '컴파운더: 번 돈을 높은 수익률로 다시 투자하며 오래 성장하는 기업',
    'growth': '성장주: 고객과 현금창출을 확인했고 빠르게 사업을 키우는 기업',
    'buffett_value': '가치주: 보수적으로 계산한 가치보다 충분히 싼 기업',
    'moonshot': '문샷: 큰 성공 가능성과 큰 실패 위험이 함께 있는 초기 혁신 기업',
    'non_fit': '현재 투자 유형 미확정: 필요한 조건이나 위험 검토가 충족되지 않음',
}
DOMAINS = {
    'structural_leadership': '산업의 변화와 회사의 경쟁력',
    'customer_product': '고객이 제품을 선택하는 이유', 'moat_trajectory': '경쟁사의 추격을 막는 힘',
    'reinvestment_fcf': '재투자가 주주 몫의 현금을 늘리는지',
    'management_allocation': '경영진이 돈을 쓰는 방식', 'financial_survival': '위기를 버틸 재무 여력',
    'expectation_valuation': '현재 가격에 비해 가치가 충분한지', 'asymmetry': '성공의 이익과 실패의 손실',
}
JARGON = {'Hard Veto': '매수를 막는 중대 위험', 'owner FCF': '주주 몫으로 보는 현금(추정)',
          'FCF': '투자지출 후 남는 현금', 'SBC': '주식보상 비용', 'ROIC': '투자한 돈의 수익률',
          'Bull': '낙관', 'Base': '기준', 'Bear': '비관', 'terminal': '먼 미래 가치',
          'TTM': '최근 12개월', 'DCF': '미래 현금을 현재 가치로 환산한 계산'}


def plain(text):
    text = str(text)
    for old, new in JARGON.items(): text = text.replace(old, new)
    return html.escape(text).replace('|', r'\|').replace('\n', ' ')


def number(value):
    return '자료 없음' if value is None else f'{value:,.2f}'


def render(context, verdict, reports, research_packets=()):
    ic = verdict.get('ic_verdict') or {}
    reviewed = bool(ic and ic.get('ic_state'))
    narrative = ic.get('plain_language') or {}
    title = context.get('company_name') or context['ticker']
    lines = [f"# {plain(title)} — 쉽게 읽는 투자 검토", '',
        f"정보 기준일: **{context['as_of_date']}** · 정책 {verdict['decision_policy_version']}", '',
        f"**현재 결과: {STATES.get(verdict['ic_state'], plain(verdict['ic_state']))}**", '',
        '투자위원회 검토를 반영한 결과입니다.' if reviewed else '아직 투자위원회 최종 결론이 아닙니다. 아래 내용은 현재까지의 기계적 집계입니다.', '',
        TYPES[verdict['archetype']]+'.', '']
    for key, label in [('business', '무엇으로 돈을 버는 회사인가'), ('opportunity', '성장할 수 있는 이유'),
                       ('risk', '가장 조심할 점'), ('decision_reason', '현재 결론의 이유')]:
        if key == 'decision_reason' and verdict.get('ic_review_flags'): continue
        if narrative.get(key): lines += [f'**{label}** — {plain(narrative[key])}', '']
    reasons = []
    if verdict.get('review_only'): reasons.append('이번 실행은 매수 승인을 내릴 수 없는 검토 전용 실행입니다.')
    if verdict['coverage_weight'] < 100: reasons.append('필수 사업 분석이 아직 끝나지 않았습니다.')
    status = verdict['hard_veto_status']
    if status == 'CONFIRMED': reasons.append('매수를 막는 중대 위험이 확인되었습니다.')
    elif status != 'CLEARED': reasons.append('매수를 막는 중대 위험의 검증이 아직 끝나지 않았습니다.')
    if verdict['valuation_model']['status'] != 'COMPLETE': reasons.append('가격과 가치를 비교할 핵심 입력이 부족합니다.')
    if verdict['macro_geo_overlay']['pending_reanalysis_domains']: reasons.append('국제정세 변화가 사업에 미치는 영향을 다시 확인해야 합니다.')
    if verdict.get('ic_review_flags'): reasons.append('위원회가 요청한 결정 중 일부는 하네스의 안전 조건을 통과하지 못했습니다.')
    if reasons: lines += [' '.join(reasons), '']
    # State comes exclusively from final_verdict/reconcile_ic, never narrative or raw IC intent.
    if verdict['ic_state'] in ('WATCH','REJECT','INCOMPLETE','EARLY_EXIT_NON_FIT'):
        lines += ['현재 신규 매수 승인은 없습니다. 기존 보유분 처분 여부는 별도 검토가 필요합니다.', '']
    lines += ['| 살펴본 항목 | 점수 / 100 |', '|---|---:|']
    for domain, label in DOMAINS.items():
        row = verdict['domain_scores'].get(domain)
        lines += [f"| {label} | {number(row.get('decision_score', row.get('score'))) if row else '미완료'} |"]
    lines += ['', f"종합 점수는 **{number(verdict['score_100'])}**입니다. 점수는 수익률이나 성공 확률이 아닙니다.", '']
    model = verdict['valuation_model']
    if model['status'] == 'COMPLETE':
        currency = context.get('currency') or '통화 미지정'
        lines += [f"**가격을 어떻게 보았나** — 기준일 가격은 주당 {number(model['current_price'])} {plain(currency)}입니다.",
            '아래는 미래 현금창출을 가정해 계산한 현재 가치입니다. 회사가 발표한 사실이나 보장된 목표주가가 아닙니다.', '',
            '| 가정 | 계산된 주당 가치 |', '|---|---:|']
        for key, label in [('bear','사업이 기대보다 나쁜 경우'),('base','기준 가정이 실현되는 경우'),('bull','사업이 기대보다 좋은 경우')]:
            lines += [f"| {label} | {number(model['scenarios'][key]['value_per_share'])} {plain(currency)} |"]
        lines += ['', '가정이 달라지면 가치도 달라집니다. 좋은 회사라도 가격이 높으면 투자 결과가 나쁠 수 있습니다.', '']
    else: lines += ['가격 대비 가치: 자료가 부족하여 계산을 완료하지 못했습니다.', '']
    rows = [r for r in reports if r.get('analysis_status') == 'complete']
    checks = list(dict.fromkeys(check for r in ([ic] if ic else rows) for check in r.get('next_checks', [])))
    if checks:
        lines += ['**다음에 확인할 것**', ''] + [f'- {plain(check)}' for check in checks[:4]] + ['']
    conflicts = {e['evidence_id'] for p in research_packets for e in p.get('conflicts',[])}
    if conflicts: lines += [f'추가 조사에서 원본과 충돌하거나 재고정이 필요한 증거 {len(conflicts)}건을 분리했습니다. 원본 숫자는 바꾸지 않았습니다.', '']
    lines += ['**사실과 판단의 구분** — 원본 공시와 기준 입력은 보존합니다. 미래 성장률, 시나리오 가치와 위원회의 설명은 추정 또는 판단입니다. 자료가 없는 항목은 0으로 처리하지 않습니다.', '',
        '[상세 계산과 결정](final_verdict.json) · [분석 요약](digest.md) · [원본과 출처](sources/README.md)', '']
    if ic: lines += ['[투자위원회 근거](reports/IC.json)', '']
    return '\n'.join(lines)
