#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import date, timedelta
import argparse, json, re, statistics, shutil, sys

ROOT=Path(__file__).resolve().parent
STRATEGY=json.loads((ROOT/'config/strategy.json').read_text(encoding='utf-8'))
MANIFEST=json.loads((ROOT/'config/agents_manifest.json').read_text(encoding='utf-8'))
WORKFLOW=json.loads((ROOT/'config/workflow.json').read_text(encoding='utf-8'))
EXEC=WORKFLOW['execution']
SCORE_DOMAINS={x['id']:x for x in STRATEGY['scorecard']}
AXIS_DOMAINS={x['id']:x for x in STRATEGY['evaluation_axes']}
ARCHETYPES=STRATEGY['archetypes']
VETOES=STRATEGY['hard_vetoes']
BUY_STATES=('EXCEPTIONAL_WINNER_CANDIDATE','CORE_WINNER_CANDIDATE','NORMAL_CANDIDATE')
SIGNAL_DOMAIN='expectation_valuation'
MACRO_DOMAIN='macro_overlay'
REVIEW_DOMAINS=('evidence_quality','red_team')
IC_DOMAIN='investment_committee'
VETO_STATUSES=('none','candidate','conditional','confirmed','cleared')


def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump_json(p:Path,obj): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def run_dir(ticker): return ROOT/'runs'/ticker.upper()
def agents_in(domain): return [a for a in MANIFEST if a['domain']==domain]
def is_complete(r): return r.get('analysis_status')=='complete'

def load_reports(ticker):
    d=run_dir(ticker)/'reports'
    if not d.exists(): raise SystemExit('run not found; use init first')
    reports=[]
    for p in sorted(d.glob('*.json')):
        try: reports.append(load_json(p))
        except Exception as e: print('skip',p,e)
    return reports

def macro_cache_source(as_of:str):
    cache=ROOT/'runs'/'_macro'
    if not cache.exists(): return None
    target=date.fromisoformat(as_of); oldest=target-timedelta(days=EXEC['macro_cache_days'])
    dated=[]
    for p in cache.iterdir():
        try: d=date.fromisoformat(p.name)
        except ValueError: continue
        if oldest<=d<=target: dated.append((d,p))
    return max(dated)[1] if dated else None

def cmd_init(args):
    ticker=args.ticker.upper(); run=run_dir(ticker)
    (run/'reports').mkdir(parents=True,exist_ok=True)
    (run/'cross_exam').mkdir(exist_ok=True)
    ctx=load_json(ROOT/'templates/company_context.json')
    ctx['ticker']=ticker; ctx['as_of_date']=args.as_of
    dump_json(run/'company_context.json',ctx)
    cached=macro_cache_source(args.as_of)
    for a in MANIFEST:
        cached_report=cached/f"{a['agent_id']}.json" if cached else None
        if a['domain']==MACRO_DOMAIN and cached_report and cached_report.exists():
            rpt=load_json(cached_report); rpt.update(ticker=ticker,cached_from=cached_report.relative_to(ROOT).as_posix())
        else:
            rpt=load_json(ROOT/'templates/agent_report.json')
            rpt.update(agent_id=a['agent_id'],ticker=ticker,as_of_date=args.as_of,domain=a['domain'],role=a['role'])
            if a['domain']!=SIGNAL_DOMAIN: rpt.pop('archetype_signals',None)
        dump_json(run/'reports'/f"{a['agent_id']}.json",rpt)
    shutil.copy(ROOT/'templates/one_page_investment_record.md',run/'one_page_investment_record.md')
    print(run)
    if cached: print(f'macro overlay reused from {cached.relative_to(ROOT)}')

def cmd_cache_macro(args):
    run=run_dir(args.ticker)
    as_of=load_json(run/'company_context.json')['as_of_date']
    dest=ROOT/'runs'/'_macro'/as_of; n=0
    for a in agents_in(MACRO_DOMAIN):
        src=run/'reports'/f"{a['agent_id']}.json"
        if src.exists() and is_complete(load_json(src)):
            dest.mkdir(parents=True,exist_ok=True); shutil.copy(src,dest/src.name); n+=1
    print(f'cached {n} macro reports -> {dest.relative_to(ROOT)}')

def weighted_median(vals):
    # vals: [(value, weight)]
    vals=sorted(vals,key=lambda x:x[0]); total=sum(w for _,w in vals)
    if total<=0: return statistics.median(v for v,_ in vals)
    acc=0
    for v,w in vals:
        acc+=w
        if acc>=total/2: return v
    return vals[-1][0]

def domain_aggregate(reports):
    usable=[r for r in reports if is_complete(r) and r.get('score_0_100') is not None]
    if not usable: return None
    wm=weighted_median([(float(r['score_0_100']),max(float(r.get('confidence_0_1',0.5)),0.05)) for r in usable])
    scores=[float(r['score_0_100']) for r in usable]
    spread=max(scores)-min(scores) if len(scores)>1 else 0
    avg_conf=sum(float(r.get('confidence_0_1',0.5)) for r in usable)/len(usable)
    unknown_penalty=min(12, sum(len(r.get('unknowns',[])) for r in usable)*0.75)
    dispute_penalty=0
    if spread>=30: dispute_penalty=8
    elif spread>=20: dispute_penalty=4
    confidence_penalty=max(0,(0.65-avg_conf)*20)
    score=max(0,min(100,wm-unknown_penalty-dispute_penalty-confidence_penalty))
    return {'raw_weighted_median':round(wm,2),'score':round(score,2),'spread':round(spread,2),'avg_confidence':round(avg_conf,3),'unknown_penalty':round(unknown_penalty,2),'dispute_penalty':dispute_penalty,'domain_dispute':spread>=20}

def classification(score):
    for c in STRATEGY['classifications']:
        if c['min']<=score<=c['max']: return c['label']
    return 'Unclassified'

def core_score(ds, exclude=()):
    total=0; covered=0
    for d,meta in SCORE_DOMAINS.items():
        if d in exclude or not ds.get(d): continue
        total+=ds[d]['score']/100*meta['weight']; covered+=meta['weight']
    return (total/covered*100 if covered else None), covered

def archetype_signals(reports):
    vals={}
    for r in reports:
        if not is_complete(r): continue
        for k,v in (r.get('archetype_signals') or {}).items():
            if isinstance(v,(int,float)) and not isinstance(v,bool): vals.setdefault(k,[]).append(float(v))
    return {k:round(statistics.median(v),4) for k,v in vals.items()}

def check_condition(c, ds, signals, key='score'):
    kind,name=c['field'].split('.',1)
    val=(ds.get(name) or {}).get(key) if kind=='domain' else signals.get(name)
    if val is None: return None
    if c['op']=='>=': return val>=c['value']
    if c['op']=='<=': return val<=c['value']
    if c['op']=='between': return c['value'][0]<=val<=c['value'][1]
    raise ValueError(f"unknown op {c['op']}")

def reachable_archetypes(ds, signals, confirmed):
    # Optimistic: pre-penalty medians for finished domains, unfinished domains/signals assumed achievable.
    if confirmed: return []
    return [t['id'] for t in ARCHETYPES['types'] if t['id']!=ARCHETYPES['fallback']
            and all(check_condition(c,ds,signals,key='raw_weighted_median') is not False for c in t['conditions'])]

def classify_archetype(ds, signals, score, score_ex_valuation, confirmed):
    types={t['id']:t for t in ARCHETYPES['types']}
    evaluations=[]
    for t in ARCHETYPES['types']:
        if t['id']==ARCHETYPES['fallback']: continue
        checks=[(c['field'],check_condition(c,ds,signals)) for c in t['conditions']]
        gate=score_ex_valuation if t.get('valuation_tolerant') else score
        evaluations.append({'id':t['id'],'label':t['label'],
            'conditions_met':all(r is True for _,r in checks),
            'gate_score':round(gate,2) if gate is not None else None,
            'gate_passed':gate is not None and gate>=ARCHETYPES['min_gate_score'],
            'failed':[f for f,r in checks if r is False],'missing':[f for f,r in checks if r is None]})
    matches=[e for e in evaluations if e['conditions_met'] and e['gate_passed']]
    if confirmed:
        primary=None; reason='Hard Veto 확정'
    elif matches:
        primary=matches[0]; reason='유형 조건 및 게이트 점수 충족'
    else:
        primary=None
        pending=[e['id'] for e in evaluations if e['missing'] and not e['failed']]
        reason=f"판정 데이터 부족: {', '.join(pending)}" if pending else '어느 유형 조건도 충족하지 않거나 게이트 점수 미달'
    t=types[primary['id'] if primary else ARCHETYPES['fallback']]
    return {'id':t['id'],'label':t['label'],'label_en':t['label_en'],'reason':reason,
        'gate_score':primary['gate_score'] if primary else None,
        'secondary':[e['id'] for e in matches[1:]] if primary else [],
        'position_guidance':t.get('position_guidance'),'position_cap':t.get('position_cap'),
        'signals':signals,'evaluations':evaluations}

def compute_aggregate(ticker, reports):
    by_domain={}
    for r in reports: by_domain.setdefault(r.get('domain','unknown'),[]).append(r)
    ds={}
    for d in [*SCORE_DOMAINS, *AXIS_DOMAINS]:
        if d in by_domain: ds[d]=domain_aggregate(by_domain[d])
    normalized,covered=core_score(ds)
    score_ex_valuation,_=core_score(ds,exclude=(SIGNAL_DOMAIN,))
    confirmed=[]; unresolved=[]
    for r in reports:
        if not is_complete(r): continue
        for v in r.get('hard_veto_flags',[]):
            status=v.get('status')
            item={'agent_id':r.get('agent_id'),'veto':v.get('veto'),'status':status,'rationale':v.get('rationale')}
            if status=='confirmed': confirmed.append(item)
            elif status in ('candidate','conditional'): unresolved.append(item)
    if confirmed: veto_status='CONFIRMED'
    elif unresolved: veto_status='UNRESOLVED'
    else: veto_status='CLEAR_OR_NOT_FLAGGED'
    disputes=[{'domain':d,**x} for d,x in ds.items() if x and x.get('domain_dispute')]
    cls=classification(normalized) if normalized is not None else 'INCOMPLETE'
    signals=archetype_signals(reports)
    archetype=classify_archetype(ds,signals,normalized,score_ex_valuation,confirmed)
    reachable=reachable_archetypes(ds,signals,confirmed)
    early_exit=covered<100 and EXEC['early_exit'] and not reachable and triage_complete(reports)
    # valuation-tolerant archetypes (moonshot) are staged on the score excluding expectation_valuation
    state_score=archetype['gate_score'] if archetype['gate_score'] is not None else normalized
    # mechanical pre-IC state only
    if early_exit: state='EARLY_EXIT_NON_FIT'
    elif covered < 100: state='INCOMPLETE'
    elif confirmed: state='REJECT'
    elif unresolved: state='WATCH'
    elif state_score>=90: state='EXCEPTIONAL_WINNER_CANDIDATE'
    elif state_score>=85: state='CORE_WINNER_CANDIDATE'
    elif state_score>=75: state='NORMAL_CANDIDATE'
    elif state_score>=65: state='STARTER_OR_WATCH'
    else: state='REJECT'
    if archetype['id']==ARCHETYPES['fallback'] and state in BUY_STATES: state=ARCHETYPES['buy_state_cap_for_fallback']
    if early_exit: archetype['reason']='조기 종료: 감점 전 원점수로도 도달 가능한 유형 없음'
    pos={'EXCEPTIONAL_WINNER_CANDIDATE':'6-10% (IC cap)','CORE_WINNER_CANDIDATE':'4-8%','NORMAL_CANDIDATE':'2-4%','STARTER_OR_WATCH':'0-2%','WATCH':'0% until veto cleared','REJECT':'0%','INCOMPLETE':'N/A','EARLY_EXIT_NON_FIT':'0% (유형 도달 불가 — 조기 종료)'}[state]
    if archetype['position_cap'] and state in BUY_STATES: pos=archetype['position_cap']
    di=ds.get('disruptive_innovation')
    return {'ticker':ticker.upper(),'score_100':round(normalized,2) if normalized is not None else None,'score_100_ex_valuation':round(score_ex_valuation,2) if score_ex_valuation is not None else None,'coverage_weight':covered,'classification':cls,'disruptive_innovation_score':di['score'] if di else None,'archetype':archetype,'reachable_archetypes_raw':reachable,'early_exit':early_exit,'hard_veto_status':veto_status,'mechanical_pre_ic_state':state,'position_range_pre_ic':pos,'domain_scores':ds,'disputes':disputes,'confirmed_vetoes':confirmed,'unresolved_vetoes':unresolved}

def triage_complete(reports):
    done={r['agent_id'] for r in reports if is_complete(r)}
    return all(a['agent_id'] in done for d in EXEC['triage_domains'] for a in agents_in(d))

def write_scorekeeper(ticker, result):
    path=run_dir(ticker)/'reports'/'IC-01.json'
    if path.exists():
        cur=load_json(path)
        if is_complete(cur) and cur.get('generated_by')!='harness.py aggregate': return
    as_of=load_json(run_dir(ticker)/'company_context.json')['as_of_date']
    state=result['mechanical_pre_ic_state']; a=result['archetype']
    verdict='support' if state in BUY_STATES else 'neutral' if state in ('STARTER_OR_WATCH','INCOMPLETE') else 'oppose'
    must=[d['domain'] for d in result['disputes'] if d['spread']>=30]
    dump_json(path,{'agent_id':'IC-01','ticker':ticker.upper(),'as_of_date':as_of,'domain':IC_DOMAIN,'role':'aggregator',
        'generated_by':'harness.py aggregate','analysis_status':'complete',
        'score_0_100':result['score_100'] if result['score_100'] is not None else 0,'confidence_0_1':1.0,
        'thesis':f"기계적 집계: 점수 {result['score_100']} ({result['classification']}), 유형 {a['label']} — {a['reason']}. Hard Veto {result['hard_veto_status']}, 상태 {state}, 비중 {result['position_range_pre_ic']}.",
        'evidence':[{'claim':'harness 집계 결과','source_type':'harness_output','source':f'runs/{ticker.upper()}/aggregate.json','period':as_of,'as_of_date':as_of,
            'value':{k:result[k] for k in ('score_100','score_100_ex_valuation','disruptive_innovation_score','hard_veto_status','mechanical_pre_ic_state')},'fact_or_estimate':'fact'}],
        'counterevidence':[],'unknowns':[],'falsifiers':[],'hard_veto_flags':[],'key_kpis':[],
        'next_checks':[f'{d} 재조사 (점수차 30 이상)' for d in must],'verdict':verdict})

def cmd_aggregate(args):
    reports=load_reports(args.ticker)
    result=compute_aggregate(args.ticker,reports)
    dump_json(run_dir(args.ticker)/'aggregate.json',result)
    write_scorekeeper(args.ticker,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

def pending_agents(reports):
    done={r['agent_id'] for r in reports if is_complete(r)}
    out={}
    for a in MANIFEST:
        if a['agent_id'] not in done and a['agent_id'] not in EXEC['mechanical_agents']:
            out.setdefault(a['domain'],[]).append(a['agent_id'])
    return out

def cmd_plan(args):
    t=args.ticker.upper(); reports=load_reports(t)
    pend=pending_agents(reports); result=compute_aggregate(t,reports)
    phase1=[*SCORE_DOMAINS,*AXIS_DOMAINS]
    stages=[('triage',EXEC['triage_domains']),('phase1',[d for d in phase1 if d not in EXEC['triage_domains']]),
            ('macro',[MACRO_DOMAIN]),('phase3',list(REVIEW_DOMAINS)),('ic',[IC_DOMAIN])]
    print(f"{t}: reachable archetypes (raw) = {result['reachable_archetypes_raw'] or 'none'}; veto {result['hard_veto_status']}; state {result['mechanical_pre_ic_state']}")
    skippable=sum(len(v) for d,v in pend.items() if d not in EXEC['triage_domains'])
    if EXEC['early_exit'] and triage_complete(reports) and not result['reachable_archetypes_raw'] and skippable:
        print(f'EARLY EXIT — no archetype reachable even on pre-penalty scores. Skip the remaining {skippable} agents.')
        print(f'next: python harness.py aggregate {t}  (then fill one_page_investment_record.md from the digest)')
        return
    for name,domains in stages:
        todo={d:pend[d] for d in domains if d in pend}
        if todo:
            print(f'next stage: {name}')
            for d,ids in todo.items(): print(f'  {d}: {", ".join(ids)}  ->  python harness.py prompt {t} {d}')
            if name in ('phase3','ic'): print(f'  (run python harness.py digest {t} first)')
            return
    print(f'all agents complete -> python harness.py aggregate {t}')

def short(text, n):
    text=' '.join(str(text).split())
    return text if len(text)<=n else text[:n-1]+'…'

def veto_code(v): return f'V{VETOES.index(v)+1}' if v in VETOES else short(v,20)

def cmd_digest(args):
    t=args.ticker.upper(); reports=load_reports(t); run=run_dir(t)
    done={r['agent_id']:r for r in reports if is_complete(r)}
    res=compute_aggregate(t,reports); a=res['archetype']
    L=[f"# Digest — {t} (as of {load_json(run/'company_context.json')['as_of_date']})",
       f"score {res['score_100']} (ex-val {res['score_100_ex_valuation']}, {res['classification']}) · DI {res['disruptive_innovation_score']} · archetype {a['id']} — {a['reason']} · veto {res['hard_veto_status']} · state {res['mechanical_pre_ic_state']}",
       f"signals {a['signals']} · reachable(raw) {res['reachable_archetypes_raw']}",
       'veto codes: '+' / '.join(f'V{i+1} {v}' for i,v in enumerate(VETOES)),'']
    domains=[]
    for m in MANIFEST:
        if m['domain'] not in domains: domains.append(m['domain'])
    for d in domains:
        rows=[done[m['agent_id']] for m in agents_in(d) if m['agent_id'] in done]
        if not rows: continue
        agg=res['domain_scores'].get(d)
        head=f"## {d}"+(f" — {agg['score']} (raw {agg['raw_weighted_median']}, spread {agg['spread']}{', DISPUTE' if agg['domain_dispute'] else ''})" if agg else '')
        L+=[head,'| agent | role | score | conf | verdict | vetoes | thesis |','|---|---|---|---|---|---|---|']
        for r in rows:
            vs=', '.join(f"{veto_code(v['veto'])}={v['status']}" for v in r.get('hard_veto_flags',[]) if v.get('status')!='none') or '–'
            extra=f" mult={r['risk_budget_multiplier']}" if 'risk_budget_multiplier' in r else ''
            L.append(f"| {r['agent_id']} | {r['role']} | {r['score_0_100']} | {r['confidence_0_1']} | {r['verdict']}{extra} | {vs} | {short(r.get('thesis',''),args.thesis_chars)} |")
        unknowns=[]
        for r in rows:
            for u in r.get('unknowns',[])[:args.unknowns]:
                s=short(u,90)
                if s not in unknowns: unknowns.append(s)
        if unknowns: L.append('unknowns: '+' · '.join(unknowns))
        L.append('')
    votes={}
    for r in done.values():
        for v in r.get('hard_veto_flags',[]): votes.setdefault(v.get('veto'),{})[r['agent_id']]=v.get('status')
    conflicts=[(v,s) for v,s in votes.items() if len(set(s.values()))>1]
    if conflicts:
        L.append('## veto conflicts')
        for v,s in conflicts: L.append(f"- {veto_code(v)}: "+', '.join(f'{k}={x}' for k,x in sorted(s.items())))
    out=run/'digest.md'; out.write_text('\n'.join(L)+'\n',encoding='utf-8')
    raw=sum(len(json.dumps(r,ensure_ascii=False)) for r in done.values())
    print(f'{out.relative_to(ROOT)}: {out.stat().st_size} bytes (reports {raw} chars -> digest {len(chr(10).join(L))} chars)')

def strip_common(md:str):
    i=md.find('## 공통 수행 규칙')
    md=md[:i] if i>=0 else md
    return '\n'.join(l for l in md.splitlines() if not l.startswith('공통 규칙:')).rstrip()

def compact_context(ctx):
    def keep(v): return v not in (None,'',[],{},'YYYY-MM-DD')
    def walk(x):
        if isinstance(x,dict): return {k:walk(v) for k,v in x.items() if keep(v)}
        if isinstance(x,list): return [walk(v) for v in x]
        return x
    return walk(ctx)

def skeleton(agent, lim):
    s={'analysis_status':'complete','score_0_100':0,'confidence_0_1':0,'thesis':f"≤{lim['thesis_chars']}자",
       'evidence':[{'claim':'','source_type':'filing|ir|industry|secondary|other','source':'URL 또는 파일 p.N','period':'','as_of_date':'','value':None,'fact_or_estimate':'fact|estimate|interpretation'}],
       'counterevidence':[''],'unknowns':[''],'falsifiers':[''],
       'hard_veto_flags':[{'veto':'위 Hard Veto 목록의 정확한 문자열','status':'candidate|conditional|confirmed|cleared','rationale':''}],
       'key_kpis':[{'name':'','direction':'','threshold':'','cadence':''}],'next_checks':[''],'verdict':'support|neutral|oppose'}
    if agent['domain']==SIGNAL_DOMAIN: s['archetype_signals']={'price_to_base_value':0,'valuation_percentile_5y':0,'revenue_cagr_next_3y':0}
    if agent['domain']==MACRO_DOMAIN: s['risk_budget_multiplier']=1.0
    return json.dumps(s,ensure_ascii=False)

def cmd_prompt(args):
    t=args.ticker.upper(); run=run_dir(t)
    group=agents_in(args.target) or [a for a in MANIFEST if a['agent_id']==args.target]
    if not group: raise SystemExit(f'unknown domain or agent: {args.target}')
    ctx=load_json(run/'company_context.json'); lim=EXEC['report_limits']; bud=EXEC['research_budget']
    domain=group[0]['domain']; ids=[a['agent_id'] for a in group]
    web=bud['per_role_web_calls'] if len(group)==1 else bud['per_domain_web_calls']
    P=[f"# 과제: {t} / 기준일 {ctx['as_of_date']} / {domain} — {', '.join(ids)}",
       f"저장소: {ROOT}. 작성할 파일: "+', '.join(f'runs/{t}/reports/{i}.json' for i in ids)+'. 그 외 파일은 수정하지 않는다.',
       f"웹 검색·페치 예산: 최대 {web}회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.",
       '','## 기업 기준 정보 (재검증 금지)',json.dumps(compact_context(ctx),ensure_ascii=False,separators=(',',':'))]
    facts=run/'sources'/'README.md'; index=run/'sources'/'INDEX.md'
    if facts.exists(): P+=['','## 검증된 1차 자료 사실',facts.read_text(encoding='utf-8').strip()]
    if index.exists(): P+=['',f'공시 원문: runs/{t}/sources/*.txt — runs/{t}/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.']
    if domain in (*REVIEW_DOMAINS,IC_DOMAIN):
        P+=['','## 입력',f"runs/{t}/digest.md (없으면 `python harness.py digest {t}` 실행)와 runs/{t}/cross_exam/*.md를 읽는다. 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다."]
    elif domain!=MACRO_DOMAIN:
        P+=['','## 독립성',f"runs/{t}/reports/의 다른 에이전트 보고서와 다른 도메인의 cross_exam은 읽지 않는다."+(" 역할별 분석을 서로 맞추지 말고 독립적으로 작성한다." if len(group)>1 else '')]
    for a in group:
        P+=['',f"## 역할 {a['agent_id']} ({a['role']})",strip_common((ROOT/a['instructions']).read_text(encoding='utf-8'))]
    common=[l for l in (ROOT/'agents/COMMON.md').read_text(encoding='utf-8').splitlines() if not l.startswith('# ')]
    P+=['','## 공통 규칙','\n'.join(common).strip(),
        '','## Hard Veto (정확한 문자열 사용)']+[f'- {v}' for v in VETOES]
    P+=['','## 출력',f"각 파일의 agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis {lim['thesis_chars']}자, evidence {lim['evidence'][0]}~{lim['evidence'][1]}개, counterevidence {lim['counterevidence']}개, unknowns {lim['unknowns']}개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 {lim['falsifiers']}개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.",
        skeleton(group[0],lim),f"작성 후 `python harness.py validate {t} {' '.join(ids)}`로 검증한다."]
    if domain in SCORE_DOMAINS or domain in AXIS_DOMAINS:
        P+=[f"마지막으로 runs/{t}/cross_exam/{domain}.md에 교차검증(사실·논리 충돌, 데이터 공백, 점수차 20/30 기준, Veto 불일치)을 한국어로 20줄 이내로 쓴다. 이후 보고서는 수정하지 않는다."]
    P+=['','최종 답변은 150단어 이내: 에이전트별 점수·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.']
    text='\n'.join(P)+'\n'
    if args.out: Path(args.out).write_text(text,encoding='utf-8'); print(f'{args.out}: {len(text)} chars')
    else: sys.stdout.write(text)

def validate_report(r):
    lim=EXEC['report_limits']; e=[]
    req=['agent_id','ticker','as_of_date','domain','role','analysis_status','score_0_100','confidence_0_1','thesis','evidence','counterevidence','unknowns','falsifiers','hard_veto_flags','key_kpis','next_checks','verdict']
    e+=[f'missing {k}' for k in req if k not in r]
    if e: return e
    if r['analysis_status']!='complete': e.append('analysis_status is not complete')
    if not 0<=r['score_0_100']<=100: e.append('score_0_100 out of range')
    if not 0<=r['confidence_0_1']<=1: e.append('confidence_0_1 out of range')
    if r['verdict'] not in ('support','neutral','oppose'): e.append('bad verdict')
    if len(r['thesis'])>lim['thesis_chars']: e.append(f"thesis {len(r['thesis'])} chars > {lim['thesis_chars']}")
    lo,hi=lim['evidence']
    if not lo<=len(r['evidence'])<=hi: e.append(f"evidence count {len(r['evidence'])} not in {lo}-{hi}")
    for i,ev in enumerate(r['evidence']):
        miss=[k for k in ('claim','source_type','source','period','as_of_date') if k not in ev]
        if miss: e.append(f'evidence[{i}] missing {miss}')
    for k in ('counterevidence','unknowns','falsifiers','key_kpis','next_checks'):
        if len(r[k])>lim[k]: e.append(f'{k} count {len(r[k])} > {lim[k]}')
    for v in r['hard_veto_flags']:
        if v.get('veto') not in VETOES: e.append(f"unknown veto string: {v.get('veto')}")
        if v.get('status') not in VETO_STATUSES: e.append(f"bad veto status: {v.get('status')}")
    if r['domain']==SIGNAL_DOMAIN:
        sig=r.get('archetype_signals') or {}
        e+=[f'archetype_signals.{k} missing' for k in ('price_to_base_value','valuation_percentile_5y','revenue_cagr_next_3y') if k not in sig]
    return e

def cmd_validate(args):
    t=args.ticker.upper(); d=run_dir(t)/'reports'; bad=0
    targets=args.agents or [p.stem for p in sorted(d.glob('*.json')) if p.stem not in EXEC['mechanical_agents'] and is_complete(load_json(p))]
    for aid in targets:
        try: errs=validate_report(load_json(d/f'{aid}.json'))
        except Exception as ex: errs=[f'unreadable: {ex}']
        bad+=bool(errs); print(f"{aid}: {'OK' if not errs else '; '.join(errs)}")
    sys.exit(1 if bad else 0)

DOC_TYPES=[('10-Q','FORM 10-Q'),('10-K','FORM 10-K'),('8-K','FORM 8-K'),('Form 4','FORM 4'),('Form 144','Form 144'),('Proxy (DEF 14A)','SCHEDULE 14A')]
HEADING=re.compile(r'^(PART [IVX]+\b|Item \d+[A-C]?\.|Note \d+\s*[-–])',re.I)

def cmd_sources(args):
    out=run_dir(args.ticker)/'sources'; out.mkdir(parents=True,exist_ok=True)
    if args.pdf_dir:
        try: from pypdf import PdfReader
        except ImportError: raise SystemExit('pypdf is required: pip install pypdf')
        for pdf in sorted(Path(args.pdf_dir).glob('*.pdf')):
            pages=PdfReader(str(pdf)).pages
            text=''.join(f'\n===== [page {i}] =====\n{p.extract_text() or ""}' for i,p in enumerate(pages,1))
            (out/f'{pdf.stem}.txt').write_text(text,encoding='utf-8')
    L=['# Source index','Grep or read by line range; never read a whole filing.','']
    for txt in sorted(out.glob('*.txt')):
        lines=txt.read_text(encoding='utf-8').splitlines(); head=' '.join(lines[:80])
        kind=next((k for k,pat in DOC_TYPES if pat in head),'unknown')
        n_pages=sum(1 for l in lines if l.startswith('===== [page'))
        L.append(f'## {txt.name} — {kind}, {n_pages} pages, {len(lines)} lines')
        page=0; seen=set(); items=[]
        for i,l in enumerate(lines,1):
            if l.startswith('===== [page'): page+=1; continue
            m=HEADING.match(l.strip())
            if m and l.strip()[:60] not in seen:
                seen.add(l.strip()[:60]); items.append(f'- L{i} p.{page}: {short(l,80)}')
        L+=items[:args.max_headings]+['']
    (out/'INDEX.md').write_text('\n'.join(L),encoding='utf-8')
    print(f'{(out/"INDEX.md").relative_to(ROOT)} ({len(list(out.glob("*.txt")))} files)')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init'); p.add_argument('ticker'); p.add_argument('--as-of',required=True); p.set_defaults(func=cmd_init)
    p=sub.add_parser('plan',help='show the next stage to run, or early exit'); p.add_argument('ticker'); p.set_defaults(func=cmd_plan)
    p=sub.add_parser('prompt',help='print a compact self-contained prompt for a domain or agent'); p.add_argument('ticker'); p.add_argument('target'); p.add_argument('--out'); p.set_defaults(func=cmd_prompt)
    p=sub.add_parser('validate'); p.add_argument('ticker'); p.add_argument('agents',nargs='*'); p.set_defaults(func=cmd_validate)
    p=sub.add_parser('digest',help='compact summary of completed reports for Phase 3 and IC'); p.add_argument('ticker'); p.add_argument('--thesis-chars',type=int,default=160); p.add_argument('--unknowns',type=int,default=2); p.set_defaults(func=cmd_digest)
    p=sub.add_parser('sources',help='extract filings to text and build a section index'); p.add_argument('ticker'); p.add_argument('--pdf-dir'); p.add_argument('--max-headings',type=int,default=40); p.set_defaults(func=cmd_sources)
    p=sub.add_parser('cache-macro',help='reuse this run\'s macro overlay for other tickers'); p.add_argument('ticker'); p.set_defaults(func=cmd_cache_macro)
    p=sub.add_parser('aggregate'); p.add_argument('ticker'); p.set_defaults(func=cmd_aggregate)
    args=ap.parse_args(); args.func(args)
if __name__=='__main__': main()
