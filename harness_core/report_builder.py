"""Deep research report — Report Agent RP. Harness decides; report explains.

Every decision number in the report is copied from `final_verdict.json` (the
authority), and every paragraph is a quotation of a recorded artifact with its
path (`reports/SL.json#thesis`). Nothing here scores, classifies, values, sizes
or recommends. The only arithmetic is descriptive and labelled as such (the
ratio of a recorded scenario value to the recorded frozen price).

Authority priority: final_verdict.json > aggregate.json > reports/IC.json >
digest.md > domain reports > Stage 0 pack.

    build_deep_report_context(bundle, ...)  pure: artifacts -> structured report
    render_markdown(context)                pure: structured report -> markdown
    load_bundle / write_deep_report         IO
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPORT_SCHEMA = 'deep_report/1.0'
AUTHORITY_MARKER = 'harness-authority'
SECTIONS = [
    ('00', 'Executive Summary'), ('01', '분석 기준'), ('02', '기업과 사업구조'), ('03', '산업 및 구조적 변화'),
    ('04', 'Structural Leadership'), ('05', 'Customer / Product'), ('06', 'Moat Trajectory'),
    ('07', 'Reinvestment / Incremental ROIC / FCF per Share'), ('08', 'Management / Capital Allocation'),
    ('09', 'Financial Survival'), ('10', 'Disruptive Innovation'), ('11', 'Expectation Gap / Valuation'),
    ('12', 'Asymmetry'), ('13', 'Macro / Geopolitics'), ('14', 'Evidence Audit'), ('15', 'Red Team'),
    ('16', 'Hard Veto'), ('17', 'SWOT'), ('18', 'Investment Thesis'), ('19', 'Position Framework'),
    ('20', 'Monitoring Dashboard'), ('21', 'Final Conclusion')]
DOMAIN_SECTIONS = {'04': ('structural_leadership', 'SL'), '05': ('customer_product', 'CP'),
                   '06': ('moat_trajectory', 'MT'), '07': ('reinvestment_fcf', 'RF'),
                   '08': ('management_allocation', 'MA'), '09': ('financial_survival', 'FS'),
                   '10': ('disruptive_innovation', 'DI')}
CORE_ORDER = ('structural_leadership', 'customer_product', 'moat_trajectory', 'reinvestment_fcf',
              'management_allocation', 'financial_survival', 'expectation_valuation', 'asymmetry')


# ------------------------------------------------------------------ authority (shared with the validator)

def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def authority_from_final(final, state_policy):
    """The decision fields a report may show, copied verbatim from final_verdict.json."""
    from .universe import resolved_position
    archetype = final.get('archetype')
    archetype = archetype.get('id') if isinstance(archetype, dict) else archetype
    fits = final.get('archetype_fit') or {}
    model = final.get('valuation_model') or {}
    scenarios = model.get('scenarios') or {}
    signals = model.get('signals') or {}
    position, source = resolved_position(final, state_policy)
    return {
        'ticker': final.get('ticker'), 'as_of_date': final.get('as_of_date'),
        'decision_policy_version': final.get('decision_policy_version'),
        'score_100': final.get('score_100'), 'score_100_ex_valuation': final.get('score_100_ex_valuation'),
        'coverage_weight': final.get('coverage_weight'), 'classification': final.get('classification'),
        'archetype': archetype, 'archetype_fit': (fits.get(archetype) or {}).get('fit_score') if archetype in fits else None,
        'secondary_archetypes': final.get('secondary_archetypes') or [],
        'hard_veto_status': final.get('hard_veto_status'),
        'mechanical_pre_ic_state': final.get('mechanical_pre_ic_state'),
        'position_range_pre_ic': final.get('position_range_pre_ic'),
        'ic_state': final.get('ic_state'), 'position_range': position, 'position_range_source': source,
        'macro_pacing_multiplier': final.get('macro_pacing_multiplier'),
        'early_exit': bool(final.get('early_exit')), 'review_only': bool(final.get('review_only')),
        'valuation': {'status': model.get('status'), 'current_price': model.get('current_price'),
                      'bear': (scenarios.get('bear') or {}).get('value_per_share'),
                      'base': (scenarios.get('base') or {}).get('value_per_share'),
                      'bull': (scenarios.get('bull') or {}).get('value_per_share'),
                      'price_to_base': signals.get('price_to_base_value')},
    }


def report_tier(final, ic_complete, policy, force=False):
    """(tier, reason). Tiering is by the recorded final state; --force only overrides the tier."""
    if not final:
        return 'none', 'final_verdict.json missing'
    state = final.get('ic_state')
    if force:
        return policy['forced_tier'], f'forced (recorded state {state})'
    if final.get('early_exit'):
        return policy['tiers'].get('EARLY_EXIT_NON_FIT', 'none'), 'early exit: IC intentionally not run'
    if policy.get('requires_ic_complete') and not ic_complete:
        return 'none', 'IC report not complete'
    tier = policy['tiers'].get(state, policy.get('default_tier', 'none'))
    return tier, f'state {state} -> {tier}'


# ------------------------------------------------------------------ IO

def sha256_text(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def load_bundle(runtime, run_id, reader=None):
    """Everything a report may cite, read-only."""
    run = runtime.run_dir(run_id)
    root = runtime.ROOT

    def rel(path):
        return Path(path).relative_to(root).as_posix()

    def read(path):
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
    bundle = {'run_id': run_id, 'run_path': rel(run), 'final': read(run/'final_verdict.json'),
              'aggregate': read(run/'aggregate.json'), 'context': read(run/'company_context.json') or {},
              'manifest': read(run/'run_manifest.json') or {}, 'reports': {}, 'report_status': {},
              'one_page': (run/'one_page_investment_record.md').read_text(encoding='utf-8')
              if (run/'one_page_investment_record.md').exists() else None,
              'digest_exists': (run/'digest.md').exists(), 'sources': {}, 'freeze': {}}
    for path in sorted((run/'reports').glob('*.json')) if (run/'reports').exists() else []:
        try:
            report = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            continue
        bundle['report_status'][path.stem] = report.get('analysis_status')
        if report.get('analysis_status') == 'complete':
            bundle['reports'][path.stem] = report
    for name, path in (('final_verdict', run/'final_verdict.json'), ('aggregate', run/'aggregate.json'),
                       ('ic', run/'reports'/'IC.json'), ('digest', run/'digest.md'),
                       ('one_page', run/'one_page_investment_record.md'),
                       ('company_context', run/'company_context.json')):
        if path.exists():
            bundle['sources'][name] = {'path': rel(path), 'sha256': sha256_text(path)}
    if reader is not None:
        bundle['freeze'] = reader.artifacts(run_id)['freeze']
    return bundle


# ------------------------------------------------------------------ context building (pure)

def _src(bundle, name, anchor=None):
    base = (bundle['sources'].get(name) or {}).get('path') or f"{bundle['run_path']}/{name}"
    return f'{base}#{anchor}' if anchor else base


def _rsrc(bundle, aid, anchor):
    return f"{bundle['run_path']}/reports/{aid}.json#{anchor}"


def one_page_items(text):
    """Numbered items of the IC one-page record: {n: (label, body)}."""
    items = {}
    for line in (text or '').splitlines():
        match = re.match(r'^\s*(\d{1,2})\.\s*(?:\*\*(.+?)\*\*|([^:：]+))\s*[:：]?\s*(.*)$', line)
        if match:
            label = (match.group(2) or match.group(3) or '').strip().rstrip(':：')
            body = match.group(4).strip()
            if body:
                items[int(match.group(1))] = (label, body)
    return items


def fmt_num(value, digits=2, thousands=True):
    if value is None:
        return '—'
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    text = f'{value:,.{digits}f}' if thousands else f'{value:.{digits}f}'
    return text.rstrip('0').rstrip('.') if '.' in text else text


def _domain_score(final, domain):
    row = (final.get('domain_scores') or {}).get(domain)
    if isinstance(row, dict):
        return row.get('decision_score', row.get('score'))
    return None


def _quote(label, text, source):
    return {'type': 'quote', 'label': label, 'text': str(text), 'source': source} if text else None


def _list(label, items, source):
    items = [str(i) for i in (items or []) if i]
    return {'type': 'list', 'label': label, 'items': items, 'source': source} if items else None


def _missing(what):
    return {'type': 'note', 'text': f'{what}: 이 run에서 완료된 보고서가 없다 (조기 종료 또는 미실행). 추정으로 채우지 않는다.'}


def domain_blocks(bundle, domain, aid, evidence_limit, detail=True):
    final = bundle['final']
    report = bundle['reports'].get(aid)
    if not report:
        return [_missing(f'{aid} ({domain})')]
    blocks = [{'type': 'kv', 'rows': [
        ['도메인 점수 (decision)', fmt_num(_domain_score(final, domain)), _src(bundle, 'final_verdict', f'domain_scores.{domain}')],
        ['Bear – Bull 범위', f"{fmt_num(report.get('bear_score'))} – {fmt_num(report.get('bull_score'))}", _rsrc(bundle, aid, 'bear_score,bull_score')],
        ['판정 (verdict)', report.get('verdict'), _rsrc(bundle, aid, 'verdict')]]}]
    blocks.append(_quote('Thesis', report.get('thesis'), _rsrc(bundle, aid, 'thesis')))
    if detail and report.get('subscores'):
        blocks.append({'type': 'table', 'header': ['Criterion', 'Score', 'Rationale'],
                       'rows': [[s.get('criterion_id'), fmt_num(s.get('score_0_100')), s.get('rationale') or '']
                                for s in report['subscores'] if isinstance(s, dict)],
                       'source': _rsrc(bundle, aid, 'subscores')})
    blocks.append(_quote('Bull case', report.get('bull_case'), _rsrc(bundle, aid, 'bull_case')))
    blocks.append(_quote('Bear case', report.get('bear_case'), _rsrc(bundle, aid, 'bear_case')))
    if evidence_limit:
        rows = [[e.get('claim', ''), e.get('fact_or_estimate', ''), e.get('period', ''), e.get('source', '')]
                for e in (report.get('evidence') or [])[:evidence_limit] if isinstance(e, dict)]
        if rows:
            blocks.append({'type': 'table', 'header': ['Evidence (claim)', 'Fact/Estimate', 'Period', 'Source'],
                           'rows': rows, 'source': _rsrc(bundle, aid, 'evidence')})
    if detail:
        blocks.append(_list('Counterevidence', report.get('counterevidence'), _rsrc(bundle, aid, 'counterevidence')))
        blocks.append(_list('Unknowns', report.get('unknowns'), _rsrc(bundle, aid, 'unknowns')))
        blocks.append(_list('Falsifiers', report.get('falsifiers'), _rsrc(bundle, aid, 'falsifiers')))
    flags = [f"{v.get('veto')}: {v.get('status')} — {v.get('rationale') or ''}" for v in report.get('hard_veto_flags') or []
             if v.get('status') not in (None, 'none')]
    blocks.append(_list('Hard Veto assessments (owner report)', flags, _rsrc(bundle, aid, 'hard_veto_flags')))
    return [b for b in blocks if b]


def _ratio(numerator, denominator):
    if _num(numerator) is None or not _num(denominator):
        return None
    return round(numerator / denominator, 4)


def build_deep_report_context(bundle, state_policy, strategy, policy, tier, tier_reason, generated_at,
                              vetoes=(), veto_reviewers=None, forced=False):
    """Structured report from recorded artifacts. Pure."""
    final = bundle['final']
    if not final:
        raise ValueError('final_verdict.json is required; the report explains a recorded verdict')
    auth = authority_from_final(final, state_policy)
    context, reports, ic = bundle['context'], bundle['reports'], bundle['reports'].get('IC') or {}
    plain = ic.get('plain_language') or {}
    items = one_page_items(bundle.get('one_page'))
    evidence_limit = policy['evidence_per_domain'].get(tier, 2)
    detail = tier == 'full'
    as_of = auth['as_of_date'] or context.get('as_of_date')
    currency = context.get('currency') or ''
    val = auth['valuation']
    fs = lambda anchor: _src(bundle, 'final_verdict', anchor)
    ic_src = lambda anchor: _rsrc(bundle, 'IC', anchor)
    manifest = bundle.get('manifest') or {}
    freeze = bundle.get('freeze') or {}
    derived = {'bull_to_current': _ratio(val['bull'], val['current_price']),
               'base_to_current': _ratio(val['base'], val['current_price']),
               'bear_to_current': _ratio(val['bear'], val['current_price'])}
    sections = {}

    authority_rows = [
        ['Score', fmt_num(auth['score_100']), fs('score_100')],
        ['Ex-EV Score', fmt_num(auth['score_100_ex_valuation']), fs('score_100_ex_valuation')],
        ['Archetype', auth['archetype'], fs('archetype')],
        ['Archetype Fit', fmt_num(auth['archetype_fit']), fs(f"archetype_fit.{auth['archetype']}.fit_score")],
        ['Hard Veto', auth['hard_veto_status'], fs('hard_veto_status')],
        ['Mechanical State', auth['mechanical_pre_ic_state'], fs('mechanical_pre_ic_state')],
        ['IC State', auth['ic_state'], fs('ic_state')],
        ['Position Range', auth['position_range'], fs('position_range') if auth['position_range_source'] ==
         'final_verdict.position_range' else 'config/strategy.json#state_thresholds.non_score_states'],
        ['Macro Pacing', fmt_num(auth['macro_pacing_multiplier']), fs('macro_pacing_multiplier')],
        ['Price/Base', fmt_num(val['price_to_base'], 4), fs('valuation_model.signals.price_to_base_value')],
    ]

    # 00 Executive Summary
    sections['00'] = [
        {'type': 'kv', 'rows': authority_rows},
        _quote('판정 근거 (archetype rationale)', final.get('archetype_rationale') or
               ((final.get('archetype') or {}).get('reason') if isinstance(final.get('archetype'), dict) else None),
               fs('archetype_rationale')),
        _quote('IC 결론', plain.get('decision_reason') or ic.get('thesis'),
               ic_src('plain_language.decision_reason' if plain.get('decision_reason') else 'thesis')),
        {'type': 'note', 'text': f'IC 검토 전 기계적 상한은 {auth["mechanical_pre_ic_state"]} / '
                                 f'{auth["position_range_pre_ic"]}이며, 최종 상태는 {auth["ic_state"]} / '
                                 f'{auth["position_range"]}이다. IC는 결정론적 상한을 올릴 수 없고 유지 또는 하향만 한다.'}
        if auth['position_range_pre_ic'] and not auth['early_exit'] else None,
        {'type': 'note', 'text': 'IC는 조기 종료로 의도적으로 실행되지 않았다. 도달 가능한 투자 유형이 없다.'}
        if auth['early_exit'] else None,
    ]

    # 01 분석 기준
    runner = manifest.get('runner') or {}
    freeze_line = ('현재 하네스 코드·정책과 일치' if freeze.get('config_current') and freeze.get('inputs_current')
                   else '현재 하네스와 다른 시점의 동결 — 기록된 판정을 그대로 설명한다 (재계산하지 않음)')
    sections['01'] = [{'type': 'kv', 'rows': [
        ['기준일 (as_of_date)', as_of, fs('as_of_date')],
        ['Frozen price', f"{fmt_num(val['current_price'])} {currency}".strip(), fs('valuation_model.current_price')],
        ['Harness version', f"strategy {final.get('strategy_version')} · schema {final.get('schema_version')} · decision policy {final.get('decision_policy_version')}", fs('decision_policy_version')],
        ['Harness commit (freeze)', manifest.get('harness_commit'), _src(bundle, 'final_verdict').replace('final_verdict.json', 'run_manifest.json#harness_commit')],
        ['Frozen at (UTC)', manifest.get('frozen_at_utc'), _src(bundle, 'final_verdict').replace('final_verdict.json', 'run_manifest.json#frozen_at_utc')],
        ['Input snapshot', manifest.get('input_snapshot_sha256'), _src(bundle, 'final_verdict').replace('final_verdict.json', 'run_manifest.json#input_snapshot_sha256')],
        ['Runner', ' / '.join(str(runner.get(k)) for k in ('provider', 'model') if runner.get(k)) or '미기록', 'run_manifest.json#runner'],
        ['Reconstructed run', 'yes' if final.get('reconstructed') or manifest.get('reconstructed') else 'no', fs('reconstructed')],
        ['Freeze status', freeze_line, 'harness config_hashes vs run_manifest.json'],
        ['Coverage', fmt_num(auth['coverage_weight']), fs('coverage_weight')],
        ['Classification', auth['classification'], fs('classification')],
        *authority_rows]}]
    if final.get('reconstruction_reason'):
        sections['01'].append(_quote('Reconstruction note', final['reconstruction_reason'], fs('reconstruction_reason')))

    # 02 기업과 사업구조
    sections['02'] = [
        {'type': 'kv', 'rows': [
            ['Company', context.get('company_name') or auth['ticker'], _src(bundle, 'company_context', 'company_name')],
            ['Currency', currency or '—', _src(bundle, 'company_context', 'currency')],
            ['Market cap (USD)', fmt_num(context.get('market_cap_usd'), 0), _src(bundle, 'company_context', 'market_cap_usd')],
            ['Diluted shares', fmt_num(context.get('shares_diluted'), 0), _src(bundle, 'company_context', 'shares_diluted')]]},
        _quote('사업 설명 (IC plain language)', plain.get('business'), ic_src('plain_language.business')),
        _list('분석 질문 (company_context.special_questions)', context.get('special_questions'),
              _src(bundle, 'company_context', 'special_questions')),
        _quote('Valuation metric convention', context.get('valuation_metric'), _src(bundle, 'company_context', 'valuation_metric')),
    ]

    # 03 산업 및 구조적 변화
    sl = reports.get('SL') or {}
    secular = [s for s in sl.get('subscores') or [] if isinstance(s, dict) and 'secular' in str(s.get('criterion_id'))]
    sections['03'] = [
        _quote('구조적 변화 (IC one-page §1)', (items.get(1) or (None, None))[1], _src(bundle, 'one_page', '1')),
        _quote('Structural Leadership thesis', sl.get('thesis'), _rsrc(bundle, 'SL', 'thesis')),
        {'type': 'table', 'header': ['Criterion', 'Score', 'Rationale'],
         'rows': [[s.get('criterion_id'), fmt_num(s.get('score_0_100')), s.get('rationale') or ''] for s in secular],
         'source': _rsrc(bundle, 'SL', 'subscores')} if secular else None,
    ] if sl else [_missing('SL (structural_leadership)')]

    for sid, (domain, aid) in DOMAIN_SECTIONS.items():
        sections[sid] = domain_blocks(bundle, domain, aid, evidence_limit, detail)
    if reports.get('LG'):
        sections['10'] += [{'type': 'note', 'text': '장기 성장 축 (LG, 독립 평가축 — 100점 합산에 포함되지 않음)'}] + \
            domain_blocks(bundle, 'long_term_growth', 'LG', evidence_limit, detail)

    # 11 Expectation Gap / Valuation
    model = final.get('valuation_model') or {}
    scen = model.get('scenarios') or {}
    rows = []
    for case in ('bear', 'base', 'bull'):
        row = scen.get(case) or {}
        rows.append([case.capitalize(), fmt_num(row.get('value_per_share')), fmt_num(row.get('terminal_multiple')),
                     fmt_num(row.get('terminal_fraction'), 4)])
    sections['11'] = [
        {'type': 'kv', 'rows': [
            ['Current (frozen) price', f"{fmt_num(val['current_price'])} {currency}".strip(), fs('valuation_model.current_price')],
            ['Bear / Base / Bull value per share', ' / '.join(fmt_num(val[k]) for k in ('bear', 'base', 'bull')), fs('valuation_model.scenarios')],
            ['Price/Base', fmt_num(val['price_to_base'], 4), fs('valuation_model.signals.price_to_base_value')],
            ['Valuation status', val['status'], fs('valuation_model.status')],
            ['Method', model.get('method'), fs('valuation_model.method')],
            ['Required return / horizon', f"{fmt_num(model.get('required_return'), 4)} / {model.get('horizon_years')}y", fs('valuation_model.required_return')]]},
        {'type': 'table', 'header': ['Scenario', 'Value/share', 'Terminal multiple', 'Terminal dependence (PV terminal share)'],
         'rows': rows, 'source': fs('valuation_model.scenarios')},
        {'type': 'note', 'text': '가치는 하네스가 고정된 할인율·terminal multiple로 계산한 locked scenario 결과이며 목표주가가 아니다. '
                                 '보고서는 이 값을 바꾸지 않는다.'},
        _list('Valuation sanity flags', [json.dumps(model.get('sanity'), ensure_ascii=False)] if model.get('sanity') else None,
              fs('valuation_model.sanity')),
    ] + (domain_blocks(bundle, 'expectation_valuation', 'EV', evidence_limit, detail) if reports.get('EV') else [])

    # 12 Asymmetry
    as_report = reports.get('AS') or {}
    crit = {s.get('criterion_id'): s for s in as_report.get('subscores') or [] if isinstance(s, dict)}
    sections['12'] = [
        {'type': 'kv', 'rows': [
            ['Bull / current', fmt_num(derived['bull_to_current'], 4) + 'x' if derived['bull_to_current'] else '—',
             'derived: valuation_model.scenarios.bull.value_per_share ÷ valuation_model.current_price'],
            ['Bear / current', fmt_num(derived['bear_to_current'], 4) + 'x' if derived['bear_to_current'] else '—',
             'derived: valuation_model.scenarios.bear.value_per_share ÷ valuation_model.current_price'],
            ['AS domain score', fmt_num(_domain_score(final, 'asymmetry')), fs('domain_scores.asymmetry')]]},
        _quote('Upside paths (AS upside_path rationale)', (crit.get('upside_path') or {}).get('rationale'), _rsrc(bundle, 'AS', 'subscores.upside_path')),
        _quote('Permanent loss (AS permanent_loss rationale)', (crit.get('permanent_loss') or {}).get('rationale'), _rsrc(bundle, 'AS', 'subscores.permanent_loss')),
        {'type': 'note', 'text': 'Bull/current·Bear/current는 기록된 두 숫자의 비율일 뿐이며 새 추정이 아니다.'},
    ] + (domain_blocks(bundle, 'asymmetry', 'AS', evidence_limit, detail) if as_report else [_missing('AS (asymmetry)')])

    # 13 Macro / Geopolitics
    overlay = final.get('macro_geo_overlay') or (bundle.get('aggregate') or {}).get('macro_geo_overlay') or {}
    mo = reports.get('MO') or {}
    financial = overlay.get('financial_regime') or {}
    transmission = overlay.get('company_transmission') or {}
    sections['13'] = [
        {'type': 'kv', 'rows': [
            ['Purchase pacing multiplier', fmt_num(auth['macro_pacing_multiplier']), fs('macro_pacing_multiplier')],
            ['Fundamental score effect', fmt_num(overlay.get('fundamental_score_effect', 0)), fs('macro_geo_overlay.fundamental_score_effect')],
            ['Missing / stale components', ', '.join(overlay.get('missing_or_stale_components') or []) or '없음', fs('macro_geo_overlay.missing_or_stale_components')],
            ['Pending structural re-analysis', ', '.join(overlay.get('pending_reanalysis_domains') or []) or '없음', fs('macro_geo_overlay.pending_reanalysis_domains')]]},
        {'type': 'table', 'header': ['Financial component', 'Risk-budget multiplier', 'Observed (UTC)'],
         'rows': [[k, fmt_num(v.get('risk_budget_multiplier')), v.get('as_of_utc')] for k, v in sorted(financial.items())],
         'source': fs('macro_geo_overlay.financial_regime')} if financial else None,
        {'type': 'table', 'header': ['Geopolitical dimension', 'Company status', 'Level', 'Matched exposures'],
         'rows': [[k, v.get('status'), v.get('level'), ', '.join(v.get('matched_exposures') or [])] for k, v in sorted(transmission.items())],
         'source': fs('macro_geo_overlay.company_transmission')} if transmission else None,
        {'type': 'note', 'text': strategy.get('macro_rule', '')},
        _quote('MO thesis (global components)', mo.get('thesis'), _rsrc(bundle, 'MO', 'thesis')),
    ]
    if not overlay:
        sections['13'].append({'type': 'note', 'text': 'macro_geo_overlay가 기록되지 않았다 (조기 종료 또는 재구성 run).'})

    # 14 Evidence Audit
    ed = reports.get('ED') or {}
    flags = final.get('evidence_concentration_flags') or []
    sections['14'] = ([
        {'type': 'kv', 'rows': [['ED score (review only)', fmt_num(ed.get('score_0_100')), _rsrc(bundle, 'ED', 'score_0_100')],
                                ['ED verdict', ed.get('verdict'), _rsrc(bundle, 'ED', 'verdict')]]},
        _quote('Evidence audit thesis', ed.get('thesis'), _rsrc(bundle, 'ED', 'thesis')),
        _list('Counterevidence noted by ED', ed.get('counterevidence'), _rsrc(bundle, 'ED', 'counterevidence')),
        _list('Unknowns', ed.get('unknowns'), _rsrc(bundle, 'ED', 'unknowns')),
    ] if ed else [_missing('ED (evidence_quality)')]) + [
        _list('Evidence concentration flags (review only, no score effect)',
              [json.dumps(f, ensure_ascii=False) for f in flags[:6]], fs('evidence_concentration_flags')),
        _list('주요 1차 자료 (company_context.known_sources)', context.get('known_sources'),
              _src(bundle, 'company_context', 'known_sources')),
    ]

    # 15 Red Team
    rt = reports.get('RT') or {}
    sections['15'] = [
        _quote('Strongest short thesis', rt.get('thesis'), _rsrc(bundle, 'RT', 'thesis')),
        _list('Supporting evidence', [e.get('claim') for e in rt.get('evidence') or [] if isinstance(e, dict)],
              _rsrc(bundle, 'RT', 'evidence')),
        _list('Evidence that would falsify the short thesis (RT falsifiers)', rt.get('falsifiers'), _rsrc(bundle, 'RT', 'falsifiers')),
        _list('Counterevidence against the short thesis', rt.get('counterevidence'), _rsrc(bundle, 'RT', 'counterevidence')),
        {'type': 'note', 'text': 'Red Team 결과는 점수에 더하지 않고 Hard Veto와 IC 반론의 증거로만 쓰인다.'},
    ] if rt else [_missing('RT (red_team)')]

    # 16 Hard Veto
    gate = final.get('veto_gate') or {}
    items_rows = gate.get('items') or ((bundle.get('aggregate') or {}).get('veto_gate') or {}).get('items') or []
    if items_rows:
        veto_rows = [[i.get('veto'), i.get('status'), ', '.join(i.get('owners') or []),
                      '; '.join(f"{a.get('agent_id')}={a.get('status')}" for a in i.get('assessments') or []),
                      ', '.join(i.get('missing_reports') or []) or '—'] for i in items_rows]
        veto_source = fs('veto_gate.items') if gate.get('items') else _src(bundle, 'aggregate', 'veto_gate.items')
    else:
        veto_rows = []
        for veto in vetoes:
            owners = (veto_reviewers or {}).get(veto, [])
            marks = [f"{aid}={f.get('status')}" for aid, r in sorted(reports.items())
                     for f in r.get('hard_veto_flags') or [] if f.get('veto') == veto]
            veto_rows.append([veto, 'not recorded per veto', ', '.join(owners), '; '.join(marks) or '—', '—'])
        veto_source = f"{bundle['run_path']}/reports/*.json#hard_veto_flags"
    sections['16'] = [
        {'type': 'kv', 'rows': [['Overall', auth['hard_veto_status'], fs('hard_veto_status')],
                                ['Confirmed', ', '.join(v.get('veto', str(v)) if isinstance(v, dict) else str(v)
                                                        for v in final.get('confirmed_vetoes') or []) or '없음', fs('confirmed_vetoes')],
                                ['Unresolved', ', '.join(v.get('veto', str(v)) if isinstance(v, dict) else str(v)
                                                         for v in final.get('unresolved_vetoes') or []) or '없음', fs('unresolved_vetoes')]]},
        {'type': 'table', 'header': ['Veto', 'Status', 'Owners', 'Assessments', 'Missing owner reports'],
         'rows': veto_rows, 'source': veto_source} if veto_rows else None,
        {'type': 'note', 'text': 'CLEARED와 CONFIRMED는 지정 owner만 낼 수 있고, 누락된 reviewer는 clear가 아니다. 보고서는 veto 상태를 바꾸지 않는다.'},
    ]

    # 17 SWOT — a re-arrangement of recorded bull/bear cases
    scored = [(d, _domain_score(final, d)) for d in CORE_ORDER if _domain_score(final, d) is not None]
    agent_of = {'structural_leadership': 'SL', 'customer_product': 'CP', 'moat_trajectory': 'MT', 'reinvestment_fcf': 'RF',
                'management_allocation': 'MA', 'financial_survival': 'FS', 'expectation_valuation': 'EV', 'asymmetry': 'AS'}
    best = [d for d, _ in sorted(scored, key=lambda x: (-x[1], CORE_ORDER.index(x[0])))][:3]
    worst = [d for d, _ in sorted(scored, key=lambda x: (x[1], CORE_ORDER.index(x[0])))][:3]

    def cases(domains, key):
        out = []
        for d in domains:
            r = reports.get(agent_of[d]) or {}
            if r.get(key):
                out.append(f"[{agent_of[d]} {fmt_num(_domain_score(final, d))}] {r[key]}")
        return out
    opportunities = [plain.get('opportunity')] + [f"[{aid}] {reports[aid]['bull_case']}" for aid in ('AS', 'DI', 'LG')
                                                   if (reports.get(aid) or {}).get('bull_case')]
    threats = [rt.get('thesis'), plain.get('risk')] + list((ic.get('unknowns') or [])[:2])
    sections['17'] = [
        {'type': 'note', 'text': 'SWOT은 기록된 bull/bear 논리를 재배열한 것이며 새 판단을 추가하지 않는다. '
                                 '강점·약점은 기록된 도메인 점수 순서로 골랐다.'},
        _list('Strengths (highest recorded core domains — bull cases)', cases(best, 'bull_case'), f"{bundle['run_path']}/reports/*.json#bull_case"),
        _list('Weaknesses (lowest recorded core domains — bear cases)', cases(worst, 'bear_case'), f"{bundle['run_path']}/reports/*.json#bear_case"),
        _list('Opportunities (IC plain language, AS/DI/LG bull cases)', opportunities, f"{ic_src('plain_language.opportunity')}; reports/AS|DI|LG.json#bull_case"),
        _list('Threats (RT thesis, IC plain-language risk, IC unknowns)', threats, f"{_rsrc(bundle, 'RT', 'thesis')}; {ic_src('plain_language.risk')}; {ic_src('unknowns')}"),
    ]

    # 18 Investment Thesis
    limits = []
    if auth['position_range_pre_ic'] and auth['position_range'] != auth['position_range_pre_ic'] and not auth['early_exit']:
        limits.append(f"IC가 기계적 상한 {auth['mechanical_pre_ic_state']} ({auth['position_range_pre_ic']}) 대비 "
                      f"{auth['ic_state']} ({auth['position_range']})로 배치를 제한했다.")
    dispersion = final.get('dispersion_review') or {}
    if dispersion.get('reduce_bands'):
        limits.append(f"도메인 bull/bear 분산의 하방 치우침 (mean skew {fmt_num(dispersion.get('mean_skew'))}, "
                      f"{dispersion.get('label')})으로 기계적 밴드가 {dispersion.get('position_before')}에서 축소되었다.")
    dilution = final.get('dilution_watch') or {}
    if dilution.get('position_cap'):
        limits.append(f"희석 감시: {dilution.get('status')} — {dilution.get('position_cap')}")
    limits += [f'IC 요청 거부: {f}' for f in final.get('ic_review_flags') or []]
    if auth['hard_veto_status'] != 'CLEARED':
        limits.append(f"Hard Veto 상태 {auth['hard_veto_status']}: CLEARED 전에는 매수 상태가 불가능하다.")
    sections['18'] = [
        _quote('IC thesis', ic.get('thesis'), ic_src('thesis')),
        _list('IC가 인용한 근거 (강점과 위험을 기록된 그대로)', [e.get('claim') for e in ic.get('evidence') or [] if isinstance(e, dict)], ic_src('evidence')),
        _list('현재 제한요인 — 기록된 게이트와 조정', limits, f"{fs('dispersion_review')}; {fs('ic_review_flags')}; {fs('dilution_watch')}"),
        _list('현재 제한요인 — IC unknowns', ic.get('unknowns'), ic_src('unknowns')),
        _list('IC가 기록한 반대 방향 근거 (counterevidence)', ic.get('counterevidence'), ic_src('counterevidence')),
    ] if ic else [_missing('IC (investment_committee)')]

    # 19 Position Framework
    kpis = [f"{k.get('name')} — {k.get('direction')} / {k.get('threshold')} ({k.get('cadence')})"
            for k in ic.get('key_kpis') or [] if isinstance(k, dict)]
    breaks = list(dict.fromkeys([*(ic.get('falsifiers') or []), *(final.get('falsifiers') or [])[:3]]))
    sections['19'] = [
        {'type': 'kv', 'rows': [
            ['Current approved band', f"{auth['ic_state']} · {auth['position_range']}", fs('ic_state, position_range')],
            ['Mechanical cap (pre-IC)', f"{auth['mechanical_pre_ic_state']} · {auth['position_range_pre_ic']}", fs('mechanical_pre_ic_state, position_range_pre_ic')],
            ['Purchase pacing', f"{fmt_num(auth['macro_pacing_multiplier'])}x — 비중 한도가 아니라 집행 속도", fs('macro_pacing_multiplier')]]},
        {'type': 'note', 'text': f"원칙: {strategy.get('increase_rule', '')}. 가격 상승·하락 자체는 비중 변경의 근거가 아니다. "
                                 '확대는 아래 증거가 확인되고 재동결·재분석을 거쳐 결정론적 상한과 IC가 허용할 때만 가능하다.'},
        _quote('Evidence required to increase (IC one-page §18)', (items.get(18) or (None, None))[1], _src(bundle, 'one_page', '18')),
        _list('KPI thresholds recorded by IC', kpis, ic_src('key_kpis')),
        _quote('Reduce / review conditions (IC one-page §19)', (items.get(19) or (None, None))[1], _src(bundle, 'one_page', '19')),
        _list('Thesis-break conditions (IC falsifiers, verdict falsifiers)', breaks, f"{ic_src('falsifiers')}; {fs('falsifiers')}"),
    ]

    # 20 Monitoring Dashboard
    kpi_rows, seen = [], set()
    for aid in ['IC'] + [a for a in ('SL', 'CP', 'MT', 'RF', 'MA', 'FS', 'EV', 'AS', 'DI', 'LG', 'ED', 'RT', 'MO') if a in reports]:
        for k in (reports.get(aid) or {}).get('key_kpis') or []:
            if isinstance(k, dict) and k.get('name') not in seen:
                seen.add(k.get('name'))
                kpi_rows.append([k.get('name'), k.get('direction'), k.get('threshold'), k.get('cadence'), f'{aid}.key_kpis'])
    checks = list(dict.fromkeys(c for aid in ['IC', *sorted(reports)] for c in (reports.get(aid) or {}).get('next_checks') or []))
    sections['20'] = [
        {'type': 'table', 'header': ['KPI', 'Direction', 'Threshold', 'Cadence', 'Source'],
         'rows': kpi_rows[:12 if detail else 6], 'source': f"{bundle['run_path']}/reports/*.json#key_kpis"} if kpi_rows else None,
        _list('Next checks', checks[:8 if detail else 4], f"{bundle['run_path']}/reports/*.json#next_checks"),
        {'type': 'table', 'header': ['Cadence', 'Review scope'],
         'rows': [[k, v] for k, v in (strategy.get('review_cadence') or {}).items()],
         'source': 'config/strategy.json#review_cadence'},
    ]

    # 21 Final Conclusion
    conclusion = (f"{auth['ticker']}는 {as_of} 동결 스냅샷 기준 하네스 판정이 {auth['archetype']} · {auth['ic_state']} · "
                  f"{auth['position_range']} · pacing {fmt_num(auth['macro_pacing_multiplier'])}x 이다 "
                  f"(score {fmt_num(auth['score_100'])}, Hard Veto {auth['hard_veto_status']}).")
    sections['21'] = [
        {'type': 'note', 'text': conclusion},
        _quote('IC decision reason', plain.get('decision_reason'), ic_src('plain_language.decision_reason')),
        {'type': 'note', 'text': freshness_notice(as_of)},
        {'type': 'note', 'text': '이 보고서는 새로운 목표주가·밸류에이션·점수·유형·비중·IC 판정을 만들지 않는다. Harness decides. Report explains.'},
    ]

    wanted = policy['tier_sections'][tier]
    ordered = [{'id': sid, 'title': title, 'blocks': [b for b in sections.get(sid, []) if b]}
               for sid, title in SECTIONS if sid in wanted]
    return {'schema': REPORT_SCHEMA, 'agent_id': 'RP', 'domain': 'deep_research_report',
            'ticker': auth['ticker'], 'run_id': bundle['run_id'], 'company_name': context.get('company_name'),
            'as_of_date': as_of, 'generated_at': generated_at, 'tier': tier, 'tier_reason': tier_reason,
            'forced': bool(forced), 'freshness_notice': freshness_notice(as_of),
            'authority': auth, 'authority_sources': bundle['sources'], 'derived': derived,
            'derived_note': 'Ratios of two recorded numbers (scenario value / frozen price); not estimates.',
            'freeze': {'harness_commit': manifest.get('harness_commit'), 'frozen_at_utc': manifest.get('frozen_at_utc'),
                       'input_snapshot_sha256': manifest.get('input_snapshot_sha256'),
                       'config_current': freeze.get('config_current'), 'inputs_current': freeze.get('inputs_current'),
                       'reconstructed': bool(final.get('reconstructed') or manifest.get('reconstructed'))},
            'sections': ordered, 'narrative': None}


def freshness_notice(as_of):
    return (f'This report is valid only for the frozen snapshot dated {as_of}. '
            f'이 보고서는 {as_of} 동결 스냅샷에만 유효하다. 새 실적·공시가 나오면 기존 보고서를 수정하지 않고 '
            f'refreeze → rerun → 새 보고서를 만든다.')


# ------------------------------------------------------------------ narrative (optional, model-written)

def merge_narrative(context, narrative, errors):
    """Attach a validated RP narrative. `errors` come from report_validator.validate_narrative."""
    if narrative is None:
        return context
    if errors:
        context['narrative'] = {'status': 'rejected', 'errors': errors}
        return context
    by_id = {s['id']: s for s in context['sections']}
    for sid, entry in narrative.get('sections', {}).items():
        if sid in by_id:
            by_id[sid]['blocks'].append({'type': 'narrative', 'text': entry['text'], 'source': '; '.join(entry['sources'])})
    context['narrative'] = {'status': 'merged', 'sections': sorted(narrative.get('sections', {})),
                            'sha256': hashlib.sha256(json.dumps(narrative, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
    return context


# ------------------------------------------------------------------ rendering (pure)

def _cell(value):
    return str(value if value is not None else '—').replace('|', '\\|').replace('\n', ' ')


def render_markdown(context):
    a = context['authority']
    title = context.get('company_name') or context['ticker']
    authority_json = json.dumps({k: a[k] for k in sorted(a)}, ensure_ascii=False, sort_keys=True)
    lines = [f"# {title} ({context['ticker']}) — Deep Research Report", '',
             '> **Harness decides. Report explains.** 이 보고서는 `final_verdict.json`에 기록된 판정을 설명할 뿐 '
             '새로운 투자판단을 만들지 않는다.',
             f"> {context['freshness_notice']}", '',
             f"기준일 **{context['as_of_date']}** · tier **{context['tier']}** ({context['tier_reason']}) · "
             f"generated {context['generated_at']} · run `{context['run_id']}`", '',
             f'<!-- {AUTHORITY_MARKER} {authority_json} -->', '',
             '| Authority field | Value |', '|---|---|']
    for label, key in (('Score', 'score_100'), ('Ex-EV Score', 'score_100_ex_valuation'), ('Archetype', 'archetype'),
                       ('Fit', 'archetype_fit'), ('Hard Veto', 'hard_veto_status'), ('Mechanical State', 'mechanical_pre_ic_state'),
                       ('IC State', 'ic_state'), ('Position Range', 'position_range'), ('Macro Pacing', 'macro_pacing_multiplier')):
        value = a[key]
        lines.append(f'| {label} | {_cell(fmt_num(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)} |')
    lines += ['', f"<sub>Authority: `{(context['authority_sources'].get('final_verdict') or {}).get('path')}` "
                  f"sha256 `{((context['authority_sources'].get('final_verdict') or {}).get('sha256') or '')[:12]}`</sub>", '']
    for section in context['sections']:
        lines += [f"## {section['id']}. {section['title']}", '']
        for block in section['blocks']:
            lines += _render_block(block) + ['']
    if (context.get('narrative') or {}).get('status') == 'rejected':
        lines += ['---', '', 'RP narrative was rejected by validation and not merged:', '']
        lines += [f'- {e}' for e in context['narrative']['errors']] + ['']
    lines += ['---', '', f"*{context['freshness_notice']}*", '']
    return '\n'.join(lines)


def _render_block(block):
    kind = block['type']
    if kind == 'kv':
        out = ['| 항목 | 값 | 출처 |', '|---|---|---|']
        out += [f'| {_cell(k)} | {_cell(v)} | `{_cell(s)}` |' for k, v, s in block['rows']]
        return out
    if kind == 'quote':
        return [f"**{block['label']}**", '', *[f'> {line}' for line in str(block['text']).splitlines() or ['']],
                f"<sub>출처: `{block['source']}`</sub>"]
    if kind == 'list':
        return [f"**{block['label']}**", '', *[f'- {_cell(i)}' for i in block['items']], f"<sub>출처: `{block['source']}`</sub>"]
    if kind == 'table':
        out = ['| ' + ' | '.join(block['header']) + ' |', '|' + '---|' * len(block['header'])]
        out += ['| ' + ' | '.join(_cell(c) for c in row) + ' |' for row in block['rows']]
        return out + [f"<sub>출처: `{block['source']}`</sub>"]
    if kind == 'narrative':
        return ['**RP 서술 (검증된 서술; 판정 수치는 위 표가 권위)**', '', block['text'], f"<sub>출처: `{block['source']}`</sub>"]
    return [f"*{block['text']}*"]


def parse_authority(markdown):
    match = re.search(r'<!-- ' + AUTHORITY_MARKER + r' (\{.*?\}) -->', markdown or '', re.S)
    return json.loads(match.group(1)) if match else None


# ------------------------------------------------------------------ writing (IO)

def write_deep_report(runtime, run_id, force=False, reader=None, now=None):
    """Build, validate and write runs/<RUN>/deep_report.{json,md} per tier. Returns a result dict."""
    from .universe_store import RunReader, load_policy, utcnow, atomic_write_text, atomic_dump_json
    from . import report_validator as V
    reader = reader or RunReader(runtime)
    policy = load_policy(runtime.ROOT)['report_policy']
    bundle = load_bundle(runtime, run_id, reader)
    final = bundle['final']
    run = runtime.run_dir(run_id)
    ic_complete = bundle['report_status'].get('IC') == 'complete'
    tier, reason = report_tier(final, ic_complete, policy, force)
    if tier == 'none':
        return {'run_id': run_id, 'status': 'NONE', 'tier': 'none', 'reason': reason, 'paths': []}
    context = build_deep_report_context(bundle, runtime.STATE_POLICY, runtime.STRATEGY, policy, tier, reason,
                                        now or utcnow(), runtime.VETOES, runtime.VETO_REVIEWERS, force)
    narrative_path = run/policy['narrative']['file']
    narrative = json.loads(narrative_path.read_text(encoding='utf-8')) if narrative_path.exists() else None
    narrative_errors = V.validate_narrative(narrative, bundle, context, policy['narrative']) if narrative is not None else []
    merge_narrative(context, narrative, narrative_errors)
    markdown = render_markdown(context)
    problems = [m for lvl, m in V.validate_deep_report(context, markdown, final, runtime.STATE_POLICY) if lvl == 'ERROR']
    if problems:  # a report that disagrees with the verdict is never written
        raise ValueError(f'{run_id}: deep report failed authority validation: ' + '; '.join(problems))
    atomic_dump_json(run/'deep_report.json', context)
    atomic_write_text(run/'deep_report.md', markdown)
    return {'run_id': run_id, 'status': 'COMPLETE' if not narrative_errors else 'COMPLETE_NARRATIVE_REJECTED',
            'tier': tier, 'reason': reason, 'narrative_errors': narrative_errors,
            'paths': [str((run/'deep_report.md').relative_to(runtime.ROOT)), str((run/'deep_report.json').relative_to(runtime.ROOT))]}


def rp_prompt(runtime, run_id, reader=None):
    """Prompt for the optional model-written narrative (RP). The deterministic context is the input."""
    from .universe_store import RunReader, load_policy, utcnow
    reader = reader or RunReader(runtime)
    policy = load_policy(runtime.ROOT)['report_policy']
    bundle = load_bundle(runtime, run_id, reader)
    if not bundle['final']:
        raise SystemExit(f'{run_id}: final_verdict.json missing; the report explains a recorded verdict')
    context = build_deep_report_context(bundle, runtime.STATE_POLICY, runtime.STRATEGY, policy, 'full', 'prompt', utcnow(),
                                        runtime.VETOES, runtime.VETO_REVIEWERS)
    spec = (runtime.ROOT/'agents/16_report/AGENTS.md').read_text(encoding='utf-8')
    allowed = sorted({s['path'] for s in bundle['sources'].values()} |
                     {f"{bundle['run_path']}/reports/{aid}.json" for aid in bundle['reports']})
    return '\n'.join([
        f"# 과제: {run_id} / 기준일 {context['as_of_date']} / deep_research_report (RP)",
        f"작성할 파일: {bundle['run_path']}/{policy['narrative']['file']}. 그 외 파일은 수정하지 않는다.",
        '', spec, '', '## 권위 필드 (변경 금지, 서술에서 다시 계산하지 않는다)',
        json.dumps(context['authority'], ensure_ascii=False, indent=2),
        '', '## 인용 가능한 파일 (sources에는 이 경로만 쓴다; `#필드` 앵커 허용)', *[f'- {p}' for p in allowed],
        '', '## 결정론적 본문 (섹션별 기록 근거)', json.dumps(context['sections'], ensure_ascii=False),
        '', '## 출력', f"`{policy['narrative']['file']}`: " + json.dumps(
            {'ticker': context['ticker'], 'as_of_date': context['as_of_date'],
             'sections': {'02': {'text': '≤1500자', 'sources': [f"{bundle['run_path']}/reports/SL.json#thesis"]}}},
            ensure_ascii=False),
        f"작성 후 `python harness.py report {run_id} --existing-run`으로 검증·병합한다."]) + '\n'


def cmd_report_entry(args):
    """`report T` (legacy easy report + deep report), `report T --existing-run`, `report validate T`, `report T --prompt`."""
    from . import runtime
    from . import report_validator as V
    from .universe_store import RunReader
    if args.ticker.lower() == 'validate':
        if not args.subject:
            raise SystemExit('usage: harness.py report validate TICKER')
        findings = V.validate_run_report(runtime, runtime.run_dir(args.subject).name, RunReader(runtime))
        for level, message in findings:
            print(f'{level}: {message}')
        errors = [m for lvl, m in findings if lvl == 'ERROR']
        print(f"report validate {args.subject.upper()}: {len(errors)} error(s), "
              f"{sum(1 for lvl, _ in findings if lvl == 'WARNING')} warning(s)")
        raise SystemExit(1 if errors else 0)
    if args.subject:
        raise SystemExit(f'unexpected argument {args.subject!r}; did you mean `report validate {args.subject}`?')
    run_id = runtime.run_dir(args.ticker).name
    if args.prompt:
        text = rp_prompt(runtime, run_id)
        dest = Path(args.out) if args.out else runtime.run_dir(run_id)/'RP_prompt.md'
        dest.write_text(text, encoding='utf-8')
        print(f'{dest}: {len(text)} chars')
        return
    if not args.existing_run:
        try:
            runtime.cmd_report(args)          # unchanged legacy behaviour: fresh verdict + easy_report.md
        except SystemExit as error:
            if 'frozen' in str(error):
                raise SystemExit(f'{error}\nTo explain the recorded verdict without recomputing, use '
                                 f'`harness.py report {args.ticker} --existing-run`.')
            raise
    try:
        result = write_deep_report(runtime, run_id, force=args.force)
    except ValueError as error:
        raise SystemExit(str(error))
    if result['status'] == 'NONE':
        print(f"deep report: none ({result['reason']}); use --force to override the tier")
    else:
        print(f"deep report ({result['tier']}): {', '.join(result['paths'])}")
        for error in result.get('narrative_errors') or []:
            print(f'  RP narrative rejected: {error}')
        if result.get('narrative_errors'):
            raise SystemExit(1)
