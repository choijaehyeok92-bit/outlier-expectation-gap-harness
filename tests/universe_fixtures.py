"""Synthetic, network-free runs for universe/runner/report tests.

Runs are built through the harness's own commands (init, freeze, aggregate) in a
temporary root, so every artifact has the shape the real pipeline produces:

* `complete`      — LLY/NU-like: full core, ED/RT/MO, IC STARTER, compounder.
* `triage_exit`   — GOOGL-like: triage only, no archetype reachable, early exit.
* `core_exit`     — MELI-like: full core, compounder eliminated by RF, early exit pre-IC.
* `triaged`       — triage done, compounder still reachable, paused before domain analysis.
* `initialised`   — init + frozen Stage 0 only.
"""
import argparse
import contextlib
import copy
import io
import shutil
from pathlib import Path

from harness_core import runtime as h, macro_geo

REPO = Path(__file__).resolve().parents[1]
AS_OF = '2026-09-19'
HARNESS_DIRS = ('harness_core', 'config', 'templates', 'schemas', 'agents')


def copy_harness(root):
    for directory in HARNESS_DIRS:
        shutil.copytree(REPO/directory, Path(root)/directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for filename in ('harness.py', 'AGENTS.md'):
        shutil.copy2(REPO/filename, Path(root)/filename)


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def report(agent, ticker, score=85, as_of=AS_OF):
    r = copy.deepcopy(h.load_json(REPO/'templates/agent_report.json'))
    r.update(agent_id=agent['agent_id'], domain=agent['domain'], role=agent['role'], ticker=ticker,
             as_of_date=as_of, analysis_status='complete', score_0_100=score, bull_score=100, bear_score=0,
             bull_case=f'{agent["agent_id"]} upside evidence', bear_case=f'{agent["agent_id"]} failure evidence',
             thesis=f'{agent["agent_id"]} synthetic thesis', verdict='support')
    r['evidence'] = [{'evidence_id': f'{agent["agent_id"]}-{i}', 'claim': f'{agent["agent_id"]} fixture claim {i}',
                      'source_type': 'filing', 'source': 'synthetic', 'period': '2026', 'as_of_date': as_of,
                      'value': 1, 'fact_or_estimate': 'fact'} for i in range(3)]
    r['counterevidence'] = [f'{agent["agent_id"]} counterevidence']
    r['unknowns'] = [f'{agent["agent_id"]} unknown']
    r['falsifiers'] = [f'{agent["agent_id"]} falsifier']
    r['key_kpis'] = [{'name': f'{agent["agent_id"]} KPI', 'direction': 'up', 'threshold': 'stable', 'cadence': 'quarterly'}]
    r['next_checks'] = [f'{agent["agent_id"]} next check']
    r['hard_veto_flags'] = [{'veto': v, 'status': 'cleared', 'rationale': 'Synthetic counterevidence'}
                            for v, owners in h.VETO_REVIEWERS.items() if agent['agent_id'] in owners]
    rb = h.rubric_for(agent['domain'])
    if rb:
        r['subscores'] = [{'criterion_id': c['id'], 'score_0_100': score, 'rationale': 'Fixture'} for c in rb['criteria']]
    if agent['agent_id'] == 'EV':
        r['valuation_inputs'] = {'scenarios': {k: {'owner_fcf_per_share': [10]*h.VAL_POLICY['horizon_years']}
                                               for k in ('bear', 'base', 'bull')}}
    if agent['agent_id'] == 'MO':
        r['global_components'] = macro_geo.skeleton(h.OVERLAY_POLICY, as_of)
        for component in r['global_components'].values():
            component['evidence'] = copy.deepcopy(r['evidence'][:1])
            for item in component.get('dimensions', {}).values():
                item['level'] = 'low'
    return r


def set_scores(r, values):
    for row in r['subscores']:
        row['score_0_100'] = values.get(row['criterion_id'], row['score_0_100'])
    r['score_0_100'] = h.rubric_score(r)


def agent(aid):
    return next(a for a in h.MANIFEST if a['agent_id'] == aid)


def minimal_pack(ticker, as_of=AS_OF):
    docs = [{'document_id': 'DOC-001', 'source_document': 'annual.htm', 'document_type': '10-K',
             'filing_date': None, 'period_end': None, 'is_amendment': False}]
    docs += [{'document_id': 'DOC-%03d' % (i+2), 'source_document': 'q%d.htm' % i, 'document_type': '10-Q',
              'filing_date': None, 'period_end': None, 'is_amendment': False} for i in range(6)]
    fact = {'fact_id': 'FACT-0001', 'metric': 'revenue', 'metric_detail': None, 'reported_label': 'Revenue',
            'statement': 'income', 'gaap_status': 'gaap', 'value_reported': 1.0, 'unit_kind': 'currency',
            'currency': 'USD', 'scale_multiplier': 1000000, 'period_kind': 'quarter', 'fiscal_year': 2026,
            'fiscal_quarter': 2, 'segment': 'consolidated', 'source_document': 'q0.htm',
            'is_amended': False, 'is_restated': False, 'requires_review': False}
    return {'schema_version': '1.0', 'ticker': ticker, 'as_of_date': as_of, 'documents': docs,
            'facts': [fact], 'adjustment_candidates': [], 'extraction_warnings': []}


def context_for(ticker, as_of=AS_OF):
    ctx = h.load_json(REPO/'templates/company_context.json')
    ctx.update(ticker=ticker, as_of_date=as_of, current_price=100, net_cash_per_share=5, market_cap_usd=100e9,
               company_name=f'{ticker} Synthetic Inc.')
    return ctx


def stage0(ticker, as_of=AS_OF, freeze=True):
    """init + context + pack (+ freeze). Mirrors what staged inputs provide."""
    quiet(h.cmd_init, argparse.Namespace(ticker=ticker, as_of=as_of))
    run = h.run_dir(ticker)
    h.dump_json(run/'company_context.json', context_for(ticker, as_of))
    h.dump_json(run/h.FINANCIAL_PACK, minimal_pack(ticker, as_of))
    if freeze:
        quiet(h.cmd_freeze, argparse.Namespace(ticker=ticker, provider='openai', model='gpt-fixture',
                                               reasoning_effort=None, review_only=False))
    return run


def reports_for(kind, ticker, as_of=AS_OF):
    """Agent reports keyed by agent id for a fixture kind."""
    domain_ids = [a['agent_id'] for a in h.MANIFEST if a['role'] == 'domain_analyst']
    by = {aid: report(agent(aid), ticker, as_of=as_of) for aid in domain_ids}
    set_scores(by['DI'], {x['criterion_id']: 50 for x in by['DI']['subscores']})
    set_scores(by['LG'], {x['criterion_id']: 40 for x in by['LG']['subscores']})
    for aid in ('ED', 'RT', 'MO'):
        by[aid] = report(agent(aid), ticker, as_of=as_of)
    if kind == 'triage_exit':
        for aid in ('EV', 'AS', 'DI', 'FS'):
            set_scores(by[aid], {x['criterion_id']: 20 for x in by[aid]['subscores']})
    if kind == 'core_exit':
        set_scores(by['RF'], {x['criterion_id']: 30 for x in by['RF']['subscores']})
    return by


TRIAGE = ('EV', 'AS', 'DI', 'FS')


def write_reports(ticker, reports, only=None):
    run = h.run_dir(ticker)
    for aid, r in reports.items():
        if only is None or aid in only:
            h.dump_json(run/'reports'/f'{aid}.json', r)


def aggregate(ticker):
    quiet(h.cmd_aggregate, argparse.Namespace(ticker=ticker))
    quiet(h.cmd_digest, argparse.Namespace(ticker=ticker, thesis_chars=160, unknowns=2))


def ic_report(ticker, state='STARTER', as_of=AS_OF):
    r = report(agent('IC'), ticker, as_of=as_of)
    r['ic_state'] = state
    r['plain_language'] = {'business': f'{ticker} sells synthetic products.',
                           'opportunity': 'Synthetic opportunity.', 'risk': 'Synthetic risk.',
                           'decision_reason': 'Synthetic decision reason.'}
    return r


def build(kind, ticker, as_of=AS_OF, ic_state='STARTER'):
    """Build one run of the given kind and return its directory."""
    run = stage0(ticker, as_of)
    if kind == 'initialised':
        return run
    reports = reports_for('triage_exit' if kind == 'triage_exit' else ('core_exit' if kind == 'core_exit' else 'complete'),
                          ticker, as_of)
    if kind in ('triage_exit', 'triaged'):
        write_reports(ticker, reports, TRIAGE)
    elif kind == 'core_exit':
        write_reports(ticker, reports, [a['agent_id'] for a in h.MANIFEST if a['role'] == 'domain_analyst'])
    else:
        write_reports(ticker, reports)
    aggregate(ticker)
    if kind == 'complete':
        h.dump_json(run/'reports'/'IC.json', ic_report(ticker, ic_state, as_of))
        (run/'one_page_investment_record.md').write_text(f'# One-page Investment Record — {ticker}\n', encoding='utf-8')
        aggregate(ticker)
    return run


def staged_inputs(root, ticker, kind='complete', as_of=AS_OF, agents=None):
    """Write `.harness_inputs/<RUN>/` the way the CI workflows stage agent output."""
    base = Path(root)/'.harness_inputs'/ticker
    h.dump_json(base/'company_context.json', context_for(ticker, as_of))
    h.dump_json(base/'sources'/'financials'/'normalized_financials.json', minimal_pack(ticker, as_of))
    reports = reports_for(kind, ticker, as_of)
    reports['IC'] = ic_report(ticker, 'STARTER', as_of)
    for aid, r in reports.items():
        if agents is None or aid in agents:
            h.dump_json(base/'reports'/f'{aid}.json', r)
    (base/'one_page_investment_record.md').parent.mkdir(parents=True, exist_ok=True)
    (base/'one_page_investment_record.md').write_text(f'# One-page Investment Record — {ticker}\n', encoding='utf-8')
    return base
