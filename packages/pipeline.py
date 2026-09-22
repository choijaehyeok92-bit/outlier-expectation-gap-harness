"""Where the funnel currently stands, read from disk.

The pipeline is seven steps and each one already has a command, a worker kind
and a route. What was missing is the answer to "what is done and what is next",
which until now lived in whoever remembered the order.

Two things shape this module.

**It reads; it never runs.** Every count here comes from an artifact somebody
already produced. Asking what the state is must not change it, and a status
call that quietly triggered work would make the next button press unreadable.

**It names the money boundary.** Steps 0–4 are free: two regulators that charge
nothing, one bulk quote call, and local computation. Steps 5–7 call a language
model once per agent per company. A page that chained all seven behind one
button would be a page that spends money when somebody clicks "next", so the
free ones may be chained and the paid ones may not.
"""
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

# The order is the funnel. `spends_money` is what decides whether a step may be
# chained behind a single click.
STEPS = [
    {'id': 'universe', 'title': '명단', 'spends_money': False,
     'what': '규제기관에서 상장 명단을 받는다. 재무는 아직 없다 — 티커·거래소·증권종류뿐이다.',
     'action': 'POST /api/universe/sync', 'page': '/universe'},
    {'id': 'intake', 'title': 'Stage 0 적재', 'spends_money': False,
     'what': '고른 기업의 재무 사실(pack)을 받는다. 기업당 SEC 3회 / DART 36회 요청이다.',
     'action': 'POST /api/ingest/packs', 'page': '/universe'},
    {'id': 'market', 'title': '시세', 'spends_money': False,
     'what': '한 세션의 종가를 일괄 호출 1회로 받는다. 주식수는 공시에서 오므로 여기서 받지 않는다.',
     'action': 'POST /api/market/fetch', 'page': '/market'},
    {'id': 'warehouse', 'title': '지표 창고', 'spends_money': False,
     'what': 'pack과 시세로 결정론적 지표를 계산한다. LLM은 관여하지 않는다.',
     'action': 'POST /api/warehouse/build', 'page': '/screener'},
    {'id': 'screen', 'title': '정량 스크리닝', 'spends_money': False,
     'what': '조건을 만족하는 기업만 남긴다. 아직 점수도 archetype도 없다.',
     'action': 'POST /api/screen/run', 'page': '/screener'},
    {'id': 'triage', 'title': 'Stage 3 triage', 'spends_money': True,
     'what': '15개 에이전트 중 EV·AS·DI·FS 4개만 돌려 도달 가능한 archetype이 없는 기업을 끊는다.',
     'calls_per_company': 4, 'action': 'POST /api/harness/triage', 'page': '/runs'},
    {'id': 'full', 'title': 'Stage 4 full harness', 'spends_money': True,
     'what': 'planner가 부르는 단계를 끝까지 따라가 점수·archetype·Hard Veto·IC를 만든다.',
     'calls_per_company': 15, 'action': 'POST /api/harness/full', 'page': '/runs'},
    {'id': 'deep', 'title': '심층 보고서', 'spends_money': True,
     'what': 'CLEARED · core_score ≥ 70 · early_exit 아님 을 통과한 run에만 쓴다.',
     'calls_per_company': 4, 'action': 'POST /api/deep-dive/run', 'page': '/reports'},
]


def _state(done: bool, count: int, blocked: Optional[str] = None) -> str:
    """done wins over blocked.

    A missing credential stops the *next* run of a step; it does not un-produce
    the artifact a previous run already wrote. Reporting a finished step as
    blocked would send somebody to fix a key they do not need yet.
    """
    if done:
        return 'done'
    if blocked:
        return 'blocked'
    return 'partial' if count else 'todo'


def status(as_of_date: str, *, market_root=None, packs_dir=None) -> dict:
    """Each step's state, count and what blocks it. Reads only."""
    from data_adapters import candidates as candidate_store
    from data_adapters import credentials
    from data_adapters import universe as universe_store
    from data_adapters.market_us import bulk as market_bulk
    from packages.research import store as deep_store
    from packages.screening import runs_index
    from packages.screening import store as screen_store
    from packages.screening import warehouse as warehouse_store

    creds = credentials.describe()
    by_market = {row['market']: row for row in creds}
    quote = market_bulk.describe()
    quote_default = next((row for row in quote if row['is_default']), None)

    steps = {}

    # 0 — the listing roll
    listed = universe_store.load()
    investable = universe_store.investable(listed) if listed else []
    steps['universe'] = {
        'count': len(investable), 'detail': f'투자가능 {len(investable)}',
        'synced_at_utc': (listed or {}).get('synced_at_utc'),
        'blocked': None if any(row['configured'] for row in creds)
                   else '규제기관 자격증명이 하나도 없다',
        'done': bool(investable)}

    # 1 — Stage 0 packs
    ingested = candidate_store.ingested_tickers(as_of_date, packs_dir)
    not_yet = max(0, len(investable) - len(ingested))
    steps['intake'] = {
        'count': len(ingested),
        'detail': f'pack {len(ingested)}개' + (f' · 명단에 남은 {not_yet}개' if investable else ''),
        'blocked': None if any(row['configured'] for row in creds)
                   else '규제기관 자격증명이 없다',
        'done': bool(ingested)}

    # 2 — closes on disk
    coverage = market_bulk.coverage(as_of_date, root=market_root, packs_dir=packs_dir)
    steps['market'] = {
        'count': coverage['priced'],
        'detail': f"pack {coverage['packs']}개 중 가격 있음 {coverage['priced']}개",
        'blocked': None if (quote_default or {}).get('configured') else
                   f"{(quote_default or {}).get('env_var')}가 없다",
        'done': bool(coverage['packs']) and coverage['priced'] == coverage['packs']}

    # 3 — deterministic metrics
    built = warehouse_store.load(as_of_date)
    steps['warehouse'] = {
        'count': (built or {}).get('companies') or 0,
        'detail': (f"{built['as_of_date']} · 기업 {built['companies']}개"
                   if built else '아직 만들지 않았다'),
        'blocked': None if ingested else 'Stage 0 pack이 없다',
        'done': bool(built)}

    # 4 — the quantitative cut
    screens = [row for row in screen_store.list_runs() if row['as_of_date'] == as_of_date]
    steps['screen'] = {
        'count': screens[0]['matched_count'] if screens else 0,
        'detail': (f"{screens[0]['screen_run_id']} · {screens[0]['matched_count']}종목"
                   if screens else '이 기준일의 스크린 기록이 없다'),
        'latest_id': screens[0]['screen_run_id'] if screens else None,
        'blocked': None if built else '지표 창고가 없다',
        'done': bool(screens)}

    # 5-6 — the harness itself
    runs = runs_index.load_rows()
    triaged = [row for row in runs if row.get('triage_complete')]
    full = [row for row in runs if row.get('full_harness_complete')]
    exited = [row for row in runs if row.get('early_exit')]
    steps['triage'] = {
        'count': len(triaged),
        'detail': f'triage 완료 {len(triaged)}개 · 그중 조기 종료 {len(exited)}개',
        'blocked': None, 'done': bool(triaged)}
    steps['full'] = {
        'count': len(full), 'detail': f'전체 하네스 완료 {len(full)}개',
        'blocked': None, 'done': bool(full)}

    # 7 — the deep dives
    eligible = [row for row in runs
                if row.get('full_harness_complete') and not row.get('early_exit')
                and row.get('hard_veto_status') == 'CLEARED'
                and (row.get('core_score') or 0) >= 70]
    reports = deep_store.list_reports()
    steps['deep'] = {
        'count': len(reports),
        'detail': f'보고서 {len(reports)}개 · 자동 선정 기준 통과 {len(eligible)}개',
        'eligible': sorted({row['ticker'] for row in eligible}),
        'blocked': None if full else '완료된 하네스 run이 없다',
        'done': bool(reports)}

    rows = []
    for step in STEPS:
        found = steps[step['id']]
        rows.append({**step, **found,
                     'state': _state(found['done'], found['count'], found.get('blocked'))})
    nxt = next((row['id'] for row in rows if row['state'] != 'done'), None)
    return {
        'as_of_date': as_of_date,
        'next_step': nxt,
        'free_steps': [row['id'] for row in rows if not row['spends_money']],
        'credentials': creds + [{'market': 'US', 'regulator': 'quote vendor',
                                 'env_var': (quote_default or {}).get('env_var'),
                                 'configured': bool((quote_default or {}).get('configured')),
                                 'note': (quote_default or {}).get('note'),
                                 'signup': (quote_default or {}).get('signup')}],
        'money_note': ('0~4단계는 무료다 — 규제기관 두 곳과 일괄 시세 호출 1회, 나머지는 로컬 계산이다. '
                       '5단계부터 기업당 에이전트마다 모델을 부른다. 그래서 무료 구간은 한 번에 묶어 '
                       '실행하고, 유료 구간은 묶지 않는다.'),
        'steps': rows,
    }


def estimate(step_id: str, companies: int) -> dict:
    """What a paid step would cost in model calls, before anybody starts it."""
    step = next((s for s in STEPS if s['id'] == step_id), None)
    if step is None or not step.get('spends_money'):
        return {'step': step_id, 'spends_money': False, 'calls': 0}
    per = step['calls_per_company']
    return {'step': step_id, 'spends_money': True, 'companies': companies,
            'calls_per_company': per, 'calls': per * max(0, companies),
            'note': '에이전트 호출 수다. 토큰 비용은 모델과 보고서 길이에 따라 달라진다.'}


# Each paid stage has its own offline stand-in, and they are not the same
# thing: `placeholder` is an agent provider that analyses nothing and exists to
# exercise the orchestration, while `fixture` replays a recorded deep-dive
# response. Offering the wrong one for a stage would produce a run that looks
# finished and contains nothing.
OFFLINE_BY_STAGE = {
    'triage': {'name': 'placeholder', 'kind': 'offline', 'spends_money': False,
               'env_var': None, 'default_model': None,
               'note': '오프라인 스텁이다. 아무것도 분석하지 않고 배선만 확인한다.'},
    'full': {'name': 'placeholder', 'kind': 'offline', 'spends_money': False,
             'env_var': None, 'default_model': None,
             'note': '오프라인 스텁이다. 아무것도 분석하지 않고 배선만 확인한다.'},
    'deep': {'name': 'fixture', 'kind': 'offline', 'spends_money': False,
             'env_var': None, 'default_model': 'fixture-v1',
             'note': '저장된 응답을 재생한다. 호출도 과금도 없다.'},
}


def providers(environ=None) -> dict:
    """What each paid stage may be run with, and whether a key exists for it.

    `configured` is a boolean and nothing else. The key, its length and any
    prefix of it stay in the server process; this is served to a browser.

    The offline option is listed first and is the default for every stage, so
    the page opens on something that cannot spend money.
    """
    import os
    from packages.llm.providers import CATALOGUE
    env = environ if environ is not None else os.environ
    paid = []
    for name, meta in CATALOGUE.items():
        if not meta['spends_money']:
            continue
        paid.append({'name': name, 'kind': meta['kind'],
                     'spends_money': True, 'env_var': meta['env_var'],
                     'default_model': meta['default_model'], 'note': meta['note'],
                     'configured': bool((env.get(meta['env_var']) or '').strip())})
    stages = {}
    for step in STEPS:
        if not step['spends_money']:
            continue
        offline = dict(OFFLINE_BY_STAGE[step['id']], configured=True)
        stages[step['id']] = {
            'title': step['title'],
            'calls_per_company': step['calls_per_company'],
            'default': offline['name'],
            'options': [offline] + paid,
        }
    return {'stages': stages,
            'note': ('기본값은 각 단계의 오프라인 스텁이다 — 화면을 여는 것만으로 돈이 나가지 '
                     '않는다. 실제 모델은 이름으로 고르는 명시적 선택이며, 그때 호출 수는 '
                     '기업당 에이전트 수만큼이다.'),
            'model_note': ('모델 이름은 검증 없이 그대로 전달된다. 이 저장소는 공급자의 모델 '
                           '목록을 들고 있지 않으므로, 없는 이름이면 공급자가 돌려준 오류가 '
                           '그대로 보인다.')}
