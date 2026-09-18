#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import argparse, hashlib, json, os, re, statistics, shutil, subprocess, sys

ROOT=Path(__file__).resolve().parent
STRATEGY=json.loads((ROOT/'config/strategy.json').read_text(encoding='utf-8'))
MANIFEST=json.loads((ROOT/'config/agents_manifest.json').read_text(encoding='utf-8'))
WORKFLOW=json.loads((ROOT/'config/workflow.json').read_text(encoding='utf-8'))
CALIBRATION=json.loads((ROOT/'config/calibration.json').read_text(encoding='utf-8'))
EXEC=WORKFLOW['execution']
RUBRICS=CALIBRATION['rubrics']
VAL_POLICY=CALIBRATION['valuation']
VETO_REVIEWERS=CALIBRATION['veto_reviewers']
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

def sha256_bytes(data:bytes): return hashlib.sha256(data).hexdigest()
def sha256_file(p:Path): return sha256_bytes(p.read_bytes())

def current_commit():
    try:
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return os.environ.get('HARNESS_COMMIT','unknown')

def snapshot_files(run:Path):
    files=[run/'company_context.json']
    src=run/'sources'
    if src.exists(): files.extend(sorted(p for p in src.rglob('*') if p.is_file()))
    return [p for p in files if p.exists()]

def snapshot_hashes(run:Path):
    return {p.relative_to(run).as_posix():sha256_file(p) for p in snapshot_files(run)}

def combined_hash(items):
    raw='\n'.join(f'{k}:{v}' for k,v in sorted(items.items())).encode('utf-8')
    return sha256_bytes(raw)

def config_hashes():
    files=['config/strategy.json','config/workflow.json','config/agents_manifest.json',
           'config/calibration.json','harness.py']
    return {x:sha256_file(ROOT/x) for x in files if (ROOT/x).exists()}

def load_manifest(ticker):
    p=run_dir(ticker)/'run_manifest.json'
    return load_json(p) if p.exists() else {}

def assert_frozen_inputs(ticker):
    if not CALIBRATION.get('require_frozen_inputs',False): return
    run=run_dir(ticker); m=load_manifest(ticker)
    if not m.get('frozen'):
        raise SystemExit(f'{ticker}: inputs are not frozen; fill current_price/net_cash_per_share then run freeze')
    if snapshot_hashes(run)!=m.get('input_files',{}):
        raise SystemExit(f'{ticker}: frozen inputs changed; review changes and run freeze again')

def rubric_for(domain): return RUBRICS.get(domain)

def rubric_score(report):
    rubric=rubric_for(report.get('domain'))
    if not rubric: return None
    rows={x.get('criterion_id'):x for x in report.get('subscores',[]) if isinstance(x,dict)}
    criteria=rubric.get('criteria',[])
    if not criteria or any(c['id'] not in rows for c in criteria): return None
    total=sum(float(c['weight']) for c in criteria)
    if total<=0: return None
    return sum(float(rows[c['id']]['score_0_100'])*float(c['weight']) for c in criteria)/total

def effective_score(report):
    s=rubric_score(report)
    return float(s) if s is not None else float(report['score_0_100'])

def structured_uncertainty_summary(reports):
    counts={'critical':0,'material':0,'minor':0}; seen=set()
    for r in reports:
        for u in r.get('uncertainties',[]):
            if not isinstance(u,dict): continue
            key=(r.get('agent_id'),u.get('criterion_id'))
            if key in seen: continue
            seen.add(key); sev=u.get('severity')
            if sev in counts: counts[sev]+=1
    return counts

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

def is_scored(domain): return domain in SCORE_DOMAINS or domain in AXIS_DOMAINS

def cmd_init(args):
    ticker=args.ticker.upper(); run=run_dir(ticker)
    (run/'reports').mkdir(parents=True,exist_ok=True)
    ctx=load_json(ROOT/'templates/company_context.json')
    ctx['ticker']=ticker; ctx['as_of_date']=args.as_of
    ctx.setdefault('net_cash_per_share',None)
    ctx.setdefault('valuation_percentile_5y',None)
    ctx.setdefault('valuation_metric','')
    ctx.setdefault('valuation_overrides',{'required_return':None,'terminal_multiples':{'bear':None,'base':None,'bull':None}})
    dump_json(run/'company_context.json',ctx)
    dump_json(run/'run_manifest.json',{'schema_version':'2.1','ticker':ticker,'as_of_date':args.as_of,
        'frozen':False,'harness_commit':current_commit(),
        'runner':{'provider':None,'model':None,'reasoning_effort':None}})
    cached=macro_cache_source(args.as_of)
    for a in MANIFEST:
        cached_report=cached/f"{a['agent_id']}.json" if cached else None
        if a['domain']==MACRO_DOMAIN and cached_report and cached_report.exists():
            rpt=load_json(cached_report); rpt.update(ticker=ticker,cached_from=cached_report.relative_to(ROOT).as_posix())
        else:
            rpt=load_json(ROOT/'templates/agent_report.json')
            rpt.update(agent_id=a['agent_id'],ticker=ticker,as_of_date=args.as_of,domain=a['domain'],role=a['role'])
            if is_scored(a['domain']):
                rb=rubric_for(a['domain'])
                rpt['subscores']=[{'criterion_id':c['id'],'score_0_100':50,'rationale':''} for c in (rb or {}).get('criteria',[])]
                rpt['uncertainties']=[]
            owned=[v for v,ids in VETO_REVIEWERS.items() if a['agent_id'] in ids]
            rpt['hard_veto_flags']=[{'veto':v,'status':'candidate','rationale':'미평가 — 완료 시 cleared/conditional/confirmed로 변경'} for v in owned]
            if a['domain']==SIGNAL_DOMAIN:
                rpt['valuation_inputs']={'valuation_percentile_5y':None,'revenue_cagr_next_3y':None,
                    'scenarios':{k:{'owner_fcf_per_share':[]} for k in ('bear','base','bull')}}
            else:
                rpt.pop('archetype_signals',None)
            if not is_scored(a['domain']):
                for k in ('bull_score','bear_score','bull_case','bear_case'): rpt.pop(k,None)
        dump_json(run/'reports'/f"{a['agent_id']}.json",rpt)
    shutil.copy(ROOT/'templates/one_page_investment_record.md',run/'one_page_investment_record.md')
    print(run)
    if cached: print(f'macro overlay reused from {cached.relative_to(ROOT)}')

def cmd_freeze(args):
    t=args.ticker.upper(); run=run_dir(t)
    if not (run/'company_context.json').exists(): raise SystemExit('run not found; use init first')
    ctx=load_json(run/'company_context.json')
    missing=[k for k in ('current_price','net_cash_per_share') if ctx.get(k) is None]
    if missing: raise SystemExit('freeze requires locked company_context fields: '+', '.join(missing))
    inputs=snapshot_hashes(run); m=load_manifest(t)
    m.update({'schema_version':'2.1','ticker':t,'as_of_date':ctx['as_of_date'],'frozen':True,
        'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'harness_commit':current_commit(),
        'config_files':config_hashes(),'input_files':inputs,'input_snapshot_sha256':combined_hash(inputs),
        'runner':{'provider':args.provider or None,'model':args.model or None,'reasoning_effort':args.reasoning_effort or None}})
    dump_json(run/'run_manifest.json',m)
    print(json.dumps({'ticker':t,'input_snapshot_sha256':m['input_snapshot_sha256'],
        'harness_commit':m['harness_commit'],'runner':m['runner']},ensure_ascii=False,indent=2))

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
    modern=all(rubric_score(r) is not None for r in usable)
    if modern:
        scores=[effective_score(r) for r in usable]
        wm=statistics.median(scores)
    else:
        wm=weighted_median([(float(r['score_0_100']),max(float(r.get('confidence_0_1',0.5)),0.05)) for r in usable])
        scores=[float(r['score_0_100']) for r in usable]
    if len(usable)>1:
        spread=max(scores)-min(scores)
        dispute_penalty=8 if spread>=30 else (4 if spread>=20 else 0)
    else:
        r=usable[0]
        spread=float(r['bull_score'])-float(r['bear_score']) if r.get('bull_score') is not None and r.get('bear_score') is not None else 0
        dispute_penalty=0 if modern else (8 if spread>=30 else (4 if spread>=20 else 0))
    avg_conf=sum(float(r.get('confidence_0_1',0.5)) for r in usable)/len(usable)
    unknown_penalty=0 if modern else min(12,sum(len(r.get('unknowns',[])) for r in usable)*0.75)
    confidence_penalty=0 if modern else max(0,(0.65-avg_conf)*20)
    score=max(0,min(100,wm-unknown_penalty-dispute_penalty-confidence_penalty))
    extra={k:usable[0][k] for k in ('bull_score','bear_score') if len(usable)==1 and usable[0].get(k) is not None}
    unc=structured_uncertainty_summary(usable)
    return {**extra,'raw_weighted_median':round(wm,2),'score':round(score,2),'spread':round(spread,2),
        'avg_confidence':round(avg_conf,3),'unknown_penalty':round(unknown_penalty,2),'dispute_penalty':dispute_penalty,
        'domain_dispute':spread>=20,'review_required':spread>=20 or unc['critical']>0,
        'uncertainties':unc,'score_source':'rubric_subscores' if modern else 'legacy_declared_score'}

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

def valuation_settings(ctx):
    ov=ctx.get('valuation_overrides') or {}
    om={k:v for k,v in (ov.get('terminal_multiples') or {}).items() if v is not None}
    mult={**VAL_POLICY['terminal_multiples'],**om}
    return {'required_return':float(ov.get('required_return') if ov.get('required_return') is not None else VAL_POLICY['required_return']),
        'horizon_years':int(VAL_POLICY['horizon_years']),'terminal_multiples':{k:float(v) for k,v in mult.items()}}

def deterministic_valuation(report,ctx):
    if not report or not is_complete(report): return {'status':'INCOMPLETE','reason':'EV report incomplete'}
    vi=report.get('valuation_inputs') or {}; price=ctx.get('current_price'); net_cash=ctx.get('net_cash_per_share')
    if price is None or net_cash is None: return {'status':'INCOMPLETE','reason':'frozen price/net cash missing'}
    s=valuation_settings(ctx); n=s['horizon_years']; r=s['required_return']; out={}
    for case in ('bear','base','bull'):
        path=((vi.get('scenarios') or {}).get(case) or {}).get('owner_fcf_per_share')
        if not isinstance(path,list) or len(path)!=n or any(not isinstance(x,(int,float)) for x in path):
            return {'status':'INCOMPLETE','reason':f'{case}.owner_fcf_per_share must have {n} numeric years'}
        pv=sum(float(x)/((1+r)**i) for i,x in enumerate(path,1))
        tv=float(path[-1])*s['terminal_multiples'][case]/((1+r)**n); op=pv+tv; value=float(net_cash)+op
        out[case]={'value_per_share':round(value,4),'pv_owner_fcf':round(pv,4),'pv_terminal':round(tv,4),
            'terminal_multiple':s['terminal_multiples'][case],'terminal_fraction':round(tv/op,4) if op>0 else None}
    pct=ctx.get('valuation_percentile_5y')
    if pct is None: pct=vi.get('valuation_percentile_5y')
    signals={'price_to_base_value':round(float(price)/out['base']['value_per_share'],4) if out['base']['value_per_share']>0 else None,
        'valuation_percentile_5y':pct,'revenue_cagr_next_3y':vi.get('revenue_cagr_next_3y')}
    return {'status':'COMPLETE','method':'locked owner-FCF/share DCF','required_return':r,'horizon_years':n,
        'net_cash_per_share':float(net_cash),'current_price':float(price),'scenarios':out,'signals':signals}

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
        gate_threshold=float(t.get('min_gate_score',ARCHETYPES['min_gate_score']))
        evaluations.append({'id':t['id'],'label':t['label'],
            'conditions_met':all(r is True for _,r in checks),
            'gate_score':round(gate,2) if gate is not None else None,
            'gate_threshold':gate_threshold,
            'gate_passed':gate is not None and gate>=gate_threshold,
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

def veto_gate(reports):
    by_id={r.get('agent_id'):r for r in reports if is_complete(r)}
    items=[]; confirmed=[]; unresolved=[]; pending=[]
    for veto in VETOES:
        owners=VETO_REVIEWERS.get(veto,[]); statuses=[]; missing_reports=[]; missing_assessments=[]
        for r in by_id.values():
            hit=next((v for v in r.get('hard_veto_flags',[]) if v.get('veto')==veto),None)
            if hit:
                statuses.append({'agent_id':r.get('agent_id'),'owner':r.get('agent_id') in owners,
                    'status':hit.get('status'),'rationale':hit.get('rationale')})
        for aid in owners:
            r=by_id.get(aid)
            if not r: missing_reports.append(aid)
            elif not any(x['agent_id']==aid for x in statuses): missing_assessments.append(aid)
        vals=[x['status'] for x in statuses]
        if 'confirmed' in vals: status='CONFIRMED'
        elif missing_assessments or any(x in ('candidate','conditional') for x in vals): status='UNRESOLVED'
        elif missing_reports: status='PENDING_REVIEW'
        elif owners and all(any(x['agent_id']==aid and x['status']=='cleared' for x in statuses) for aid in owners): status='CLEARED'
        else: status='UNRESOLVED'
        row={'veto':veto,'status':status,'owners':owners,'assessments':statuses,
            'missing_reports':missing_reports,'missing_assessments':missing_assessments}
        items.append(row)
        if status=='CONFIRMED': confirmed.append(row)
        elif status=='UNRESOLVED': unresolved.append(row)
        elif status=='PENDING_REVIEW': pending.append(row)
    overall='CONFIRMED' if confirmed else ('UNRESOLVED' if unresolved else ('PENDING_REVIEW' if pending else 'CLEARED'))
    return {'overall':overall,'items':items,'confirmed':confirmed,'unresolved':unresolved,'pending':pending}

def compute_aggregate(ticker, reports):
    by_domain={}
    for r in reports: by_domain.setdefault(r.get('domain','unknown'),[]).append(r)
    ds={}
    for d in [*SCORE_DOMAINS, *AXIS_DOMAINS]:
        if d in by_domain: ds[d]=domain_aggregate(by_domain[d])
    normalized,covered=core_score(ds)
    score_ex_valuation,_=core_score(ds,exclude=(SIGNAL_DOMAIN,))
    gate=veto_gate(reports); confirmed=gate['confirmed']; unresolved=gate['unresolved']; veto_status=gate['overall']
    disputes=[{'domain':d,**x} for d,x in ds.items() if x and x.get('domain_dispute')]
    cls=classification(normalized) if normalized is not None else 'INCOMPLETE'
    ctx=load_json(run_dir(ticker)/'company_context.json')
    ev=next((r for r in reports if r.get('domain')==SIGNAL_DOMAIN and is_complete(r)),None)
    valuation=deterministic_valuation(ev,ctx)
    signals=valuation.get('signals') if valuation.get('status')=='COMPLETE' else archetype_signals(reports)
    archetype=classify_archetype(ds,signals,normalized,score_ex_valuation,confirmed)
    reachable=reachable_archetypes(ds,signals,confirmed)
    early_exit=covered<100 and EXEC['early_exit'] and not reachable and triage_complete(reports)
    # valuation-tolerant archetypes (moonshot) are staged on the score excluding expectation_valuation
    state_score=archetype['gate_score'] if archetype['gate_score'] is not None else normalized
    # mechanical pre-IC state only
    if early_exit: state='EARLY_EXIT_NON_FIT'
    elif covered < 100: state='INCOMPLETE'
    elif confirmed: state='REJECT'
    elif veto_status in ('UNRESOLVED','PENDING_REVIEW'): state='WATCH'
    elif state_score>=90: state='EXCEPTIONAL_WINNER_CANDIDATE'
    elif state_score>=85: state='CORE_WINNER_CANDIDATE'
    elif state_score>=75: state='NORMAL_CANDIDATE'
    elif state_score>=65: state='STARTER_OR_WATCH'
    else: state='REJECT'
    if archetype['id']==ARCHETYPES['fallback'] and state in BUY_STATES: state=ARCHETYPES['buy_state_cap_for_fallback']
    if early_exit: archetype['reason']='조기 종료: 감점 전 원점수로도 도달 가능한 유형 없음'
    pos={'EXCEPTIONAL_WINNER_CANDIDATE':'6-10% (IC cap)','CORE_WINNER_CANDIDATE':'4-8%','NORMAL_CANDIDATE':'2-4%','STARTER_OR_WATCH':'0-2%','WATCH':'0% until veto cleared','REJECT':'0%','INCOMPLETE':'N/A','EARLY_EXIT_NON_FIT':'0% (유형 도달 불가 — 조기 종료)'}[state]
    if archetype['position_cap'] and state in BUY_STATES: pos=archetype['position_cap']
    di=ds.get('disruptive_innovation'); tq=ds.get('turnaround_quality')
    return {'ticker':ticker.upper(),'score_100':round(normalized,2) if normalized is not None else None,'score_100_ex_valuation':round(score_ex_valuation,2) if score_ex_valuation is not None else None,'coverage_weight':covered,'classification':cls,'disruptive_innovation_score':di['score'] if di else None,'turnaround_quality_score':tq['score'] if tq else None,'archetype':archetype,'reachable_archetypes_raw':reachable,'early_exit':early_exit,'hard_veto_status':veto_status,'mechanical_pre_ic_state':state,'position_range_pre_ic':pos,'domain_scores':ds,'disputes':disputes,'confirmed_vetoes':confirmed,'unresolved_vetoes':unresolved,'veto_gate':gate,'valuation_model':valuation,'run_manifest':load_manifest(ticker)}

def triage_complete(reports):
    status={}
    for r in reports: status.setdefault(r.get('domain'),[]).append(is_complete(r))
    return all(status.get(d) and all(status[d]) for d in EXEC['triage_domains'])

def cmd_aggregate(args):
    reports=load_reports(args.ticker)
    result=compute_aggregate(args.ticker,reports)
    dump_json(run_dir(args.ticker)/'aggregate.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

def pending_agents(reports):
    out={}
    for r in reports:
        if not is_complete(r): out.setdefault(r.get('domain'),[]).append(r['agent_id'])
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
            if name=='phase3': print(f'  (run python harness.py digest {t} first)')
            if name=='ic': print(f'  (run python harness.py aggregate {t} and digest {t} first)')
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
       f"score {res['score_100']} (ex-val {res['score_100_ex_valuation']}, {res['classification']}) · DI {res['disruptive_innovation_score']} · TQ {res['turnaround_quality_score']} · archetype {a['id']} — {a['reason']} · veto {res['hard_veto_status']} · state {res['mechanical_pre_ic_state']}",
       f"signals {a['signals']} · reachable(raw) {res['reachable_archetypes_raw']}",
       'veto codes: '+' / '.join(f'V{i+1} {v}' for i,v in enumerate(VETOES)),'']
    order=[m['domain'] for m in MANIFEST]
    domains=sorted({r['domain'] for r in done.values()},key=lambda d:order.index(d) if d in order else len(order))
    for d in domains:
        rows=[r for r in done.values() if r['domain']==d]
        agg=res['domain_scores'].get(d)
        head=f"## {d}"+(f" — {agg['score']} (raw {agg['raw_weighted_median']}, spread {agg['spread']}{', DISPUTE' if agg['domain_dispute'] else ''})" if agg else '')
        L+=[head,'| agent | score (bear–bull) | conf | verdict | vetoes | thesis |','|---|---|---|---|---|---|']
        for r in rows:
            vs=', '.join(f"{veto_code(v['veto'])}={v['status']}" for v in r.get('hard_veto_flags',[]) if v.get('status')!='none') or '–'
            extra=f" mult={r['risk_budget_multiplier']}" if 'risk_budget_multiplier' in r else ''
            rng=f" ({r['bear_score']}–{r['bull_score']})" if r.get('bull_score') is not None and r.get('bear_score') is not None else ''
            L.append(f"| {r['agent_id']} | {r['score_0_100']}{rng} | {r['confidence_0_1']} | {r['verdict']}{extra} | {vs} | {short(r.get('thesis',''),args.thesis_chars)} |")
            if r.get('bull_case') or r.get('bear_case'):
                L.append(f"bull: {short(r.get('bull_case',''),args.thesis_chars)} / bear: {short(r.get('bear_case',''),args.thesis_chars)}")
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
       'counterevidence':[''],'unknowns':[''],'uncertainties':[],'falsifiers':[''],
       'hard_veto_flags':[],
       'key_kpis':[{'name':'','direction':'','threshold':'','cadence':''}],'next_checks':[''],'verdict':'support|neutral|oppose'}
    if is_scored(agent['domain']):
        rb=rubric_for(agent['domain'])
        s['subscores']=[{'criterion_id':c['id'],'score_0_100':50,'rationale':''} for c in (rb or {}).get('criteria',[])]
        s['uncertainties']=[]
        s={**{k:v for k,v in s.items() if k in ('analysis_status','score_0_100','confidence_0_1')},
           'bull_score':0,'bear_score':0,'bull_case':f"≤{lim['case_chars']}자",'bear_case':f"≤{lim['case_chars']}자",
           **{k:v for k,v in s.items() if k not in ('analysis_status','score_0_100','confidence_0_1')}}
    owned=[v for v,ids in VETO_REVIEWERS.items() if agent['agent_id'] in ids]
    s['hard_veto_flags']=[{'veto':v,'status':'candidate','rationale':'미평가 — cleared/conditional/confirmed 중 하나로 변경'} for v in owned]
    if agent['domain']==SIGNAL_DOMAIN:
        s['valuation_inputs']={'valuation_percentile_5y':None,'revenue_cagr_next_3y':None,
            'scenarios':{k:{'owner_fcf_per_share':[]} for k in ('bear','base','bull')}}
        s['archetype_signals']={'price_to_base_value':None,'valuation_percentile_5y':None,'revenue_cagr_next_3y':None}
    if agent['domain']==MACRO_DOMAIN: s['risk_budget_multiplier']=1.0
    return json.dumps(s,ensure_ascii=False)

def cmd_prompt(args):
    t=args.ticker.upper(); run=run_dir(t)
    assert_frozen_inputs(t)
    agent=next((a for a in MANIFEST if args.target in (a['agent_id'],a['domain'])),None)
    if not agent: raise SystemExit(f'unknown domain or agent: {args.target}')
    ctx=load_json(run/'company_context.json'); lim=EXEC['report_limits']
    domain=agent['domain']; aid=agent['agent_id']
    P=[f"# 과제: {t} / 기준일 {ctx['as_of_date']} / {domain} ({aid})",
       f"저장소: {ROOT}. 작성할 파일: runs/{t}/reports/{aid}.json"+(f", runs/{t}/final_verdict.json, runs/{t}/one_page_investment_record.md" if domain==IC_DOMAIN else '')+'. 그 외 파일은 수정하지 않는다.',
       f"웹 검색·페치 예산: 최대 {EXEC['research_budget']['per_agent_web_calls']}회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.",
       '','## 기업 기준 정보 (재검증 금지)',json.dumps(compact_context(ctx),ensure_ascii=False,separators=(',',':'))]
    facts=run/'sources'/'README.md'; index=run/'sources'/'INDEX.md'
    if facts.exists(): P+=['','## 검증된 1차 자료 사실',facts.read_text(encoding='utf-8').strip()]
    if index.exists(): P+=['',f'공시 원문: runs/{t}/sources/*.txt — runs/{t}/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.']
    if domain in (*REVIEW_DOMAINS,IC_DOMAIN):
        P+=['','## 입력',f"runs/{t}/digest.md"+(f"와 runs/{t}/aggregate.json" if domain==IC_DOMAIN else '')+f" (없으면 `python harness.py aggregate {t}` 후 `digest {t}` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다."]
    elif domain!=MACRO_DOMAIN:
        P+=['','## 독립성',f"runs/{t}/reports/의 다른 에이전트 보고서는 읽지 않는다."]
    P+=['',f"## 지침 {aid} ({agent['role']})",strip_common((ROOT/agent['instructions']).read_text(encoding='utf-8'))]
    rb=rubric_for(domain)
    if rb:
        P+=['','## 고정 채점 루브릭',
            json.dumps({'global_bands':CALIBRATION['global_bands'],'domain':rb},ensure_ascii=False,indent=2),
            'criterion은 5점 단위로 채점한다. score_0_100은 subscores 고정 가중평균과 같아야 한다. self-confidence와 bull/bear 폭은 자동 감점하지 않는다.']
    owned=[v for v,ids in VETO_REVIEWERS.items() if aid in ids]
    if owned:
        P+=['','## 필수 Hard Veto 판정',
            '아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.']+[f'- {v}' for v in owned]
    if domain==SIGNAL_DOMAIN:
        P+=['','## 결정론적 밸류에이션',
            json.dumps({'policy':VAL_POLICY,'locked_context':{
                'current_price':ctx.get('current_price'),'net_cash_per_share':ctx.get('net_cash_per_share'),
                'valuation_percentile_5y':ctx.get('valuation_percentile_5y'),'valuation_overrides':ctx.get('valuation_overrides')}},ensure_ascii=False,indent=2),
            f"Bear/Base/Bull owner_fcf_per_share를 각각 정확히 {VAL_POLICY['horizon_years']}개 연도로 작성한다. 할인 계산과 price_to_base_value는 하네스가 수행한다."]
    common=[l for l in (ROOT/'agents/COMMON.md').read_text(encoding='utf-8').splitlines() if not l.startswith('# ')]
    P+=['','## 공통 규칙','\n'.join(common).strip(),
        '','## Hard Veto (정확한 문자열 사용)']+[f'- {v}' for v in VETOES]
    P+=['','## 출력',f"agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis {lim['thesis_chars']}자, evidence {lim['evidence'][0]}~{lim['evidence'][1]}개, counterevidence {lim['counterevidence']}개, unknowns {lim['unknowns']}개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 {lim['falsifiers']}개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.",
        skeleton(agent,lim),f"작성 후 `python harness.py validate {t} {aid}`로 검증한다."]
    P+=['','최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.']
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
    if is_scored(r['domain']):
        rb=rubric_for(r['domain']); rows=r.get('subscores',[])
        if rb:
            if 'uncertainties' not in r: e.append('uncertainties required for scored domains')
            expected={c['id'] for c in rb['criteria']}; got={x.get('criterion_id') for x in rows if isinstance(x,dict)}
            if got!=expected: e.append(f"subscores criteria mismatch: expected {sorted(expected)}, got {sorted(got)}")
            step=CALIBRATION.get('score_step',5)
            for x in rows:
                sc=x.get('score_0_100')
                if not isinstance(sc,(int,float)) or not 0<=sc<=100 or abs((sc/step)-round(sc/step))>1e-9:
                    e.append(f"bad subscore {x.get('criterion_id')}: must be 0..100 in {step}-point steps")
            calc=rubric_score(r)
            if calc is not None and abs(float(r['score_0_100'])-calc)>0.11:
                e.append(f"score_0_100 {r['score_0_100']} != rubric weighted score {calc:.2f}")
        seen=set()
        for u in r.get('uncertainties',[]):
            cid=u.get('criterion_id'); sev=u.get('severity')
            if cid in seen: e.append(f'duplicate uncertainty criterion: {cid}')
            seen.add(cid)
            if sev not in ('minor','material','critical'): e.append(f'bad uncertainty severity: {sev}')
        bull,bear=r.get('bull_score'),r.get('bear_score')
        if bull is None or bear is None: e.append('bull_score/bear_score required for scored domains')
        elif not bear<=r['score_0_100']<=bull: e.append(f"score {r['score_0_100']} not within bear {bear} – bull {bull}")
        for k in ('bull_case','bear_case'):
            if not r.get(k): e.append(f'{k} missing')
            elif len(r[k])>lim['case_chars']: e.append(f"{k} {len(r[k])} chars > {lim['case_chars']}")
    owned=[v for v,ids in VETO_REVIEWERS.items() if r.get('agent_id') in ids]
    flags={v.get('veto'):v.get('status') for v in r.get('hard_veto_flags',[])}
    for v in owned:
        if flags.get(v) not in ('cleared','conditional','confirmed','candidate'):
            e.append(f'owned veto not explicitly assessed: {v}')
    if r['domain']==SIGNAL_DOMAIN:
        vi=r.get('valuation_inputs') or {}
        for case in ('bear','base','bull'):
            path=((vi.get('scenarios') or {}).get(case) or {}).get('owner_fcf_per_share')
            if not isinstance(path,list) or len(path)!=VAL_POLICY['horizon_years']:
                e.append(f'valuation_inputs.{case}.owner_fcf_per_share must have {VAL_POLICY["horizon_years"]} values')
    return e

def cmd_validate(args):
    t=args.ticker.upper(); d=run_dir(t)/'reports'; bad=0
    targets=args.agents or [p.stem for p in sorted(d.glob('*.json')) if is_complete(load_json(p))]
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

def cmd_selftest(args):
    def mk(domain,aid,scores,bull=95,bear=45):
        rb=rubric_for(domain)
        rows=[{'criterion_id':c['id'],'score_0_100':s,'rationale':'test'} for c,s in zip(rb['criteria'],scores)]
        score=sum(x['score_0_100']*c['weight'] for x,c in zip(rows,rb['criteria']))
        return {'agent_id':aid,'domain':domain,'analysis_status':'complete','score_0_100':score,'confidence_0_1':0.2,
            'bull_score':bull,'bear_score':bear,'subscores':rows,'unknowns':['a','b','c'],'uncertainties':[]}
    a=mk('structural_leadership','SL',[80,80,80]); b=json.loads(json.dumps(a)); b['confidence_0_1']=0.95; b['unknowns']=[]
    assert domain_aggregate([a])['score']==80 and domain_aggregate([b])['score']==80
    x=domain_aggregate([mk('asymmetry','AS',[80,80,80])])
    assert x['spread']==50 and x['dispute_penalty']==0 and x['score']==80
    tq=domain_aggregate([mk('turnaround_quality','TQ',[80,80,80,80])])
    assert tq['score']==80
    ta=classify_archetype({
        'turnaround_quality':{'score':80,'raw_weighted_median':80},
        'financial_survival':{'score':70,'raw_weighted_median':70},
        'management_allocation':{'score':65,'raw_weighted_median':65},
        'expectation_valuation':{'score':70,'raw_weighted_median':70},
        'asymmetry':{'score':70,'raw_weighted_median':70}},
        {'price_to_base_value':1.3,'valuation_percentile_5y':0.5,'revenue_cagr_next_3y':0.0},60,60,[])
    assert ta['id']=='turnaround' and ta['gate_score']==60
    ev=mk('expectation_valuation','EV',[75,75,75])
    ev['valuation_inputs']={'valuation_percentile_5y':0.5,'revenue_cagr_next_3y':0.12,
        'scenarios':{k:{'owner_fcf_per_share':[10.0]*10} for k in ('bear','base','bull')}}
    vo=deterministic_valuation(ev,{'current_price':100.0,'net_cash_per_share':5.0,
        'valuation_overrides':{'required_return':None,'terminal_multiples':{}}})
    assert vo['status']=='COMPLETE' and vo['scenarios']['base']['terminal_multiple']==VAL_POLICY['terminal_multiples']['base']
    print('provider calibration selftest: OK')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init'); p.add_argument('ticker'); p.add_argument('--as-of',required=True); p.set_defaults(func=cmd_init)
    p=sub.add_parser('freeze',help='freeze input/source hashes and runner metadata for reproducible model comparisons')
    p.add_argument('ticker'); p.add_argument('--provider'); p.add_argument('--model'); p.add_argument('--reasoning-effort'); p.set_defaults(func=cmd_freeze)
    p=sub.add_parser('selftest',help='run provider-calibration invariance checks'); p.set_defaults(func=cmd_selftest)
    p=sub.add_parser('plan',help='show the next stage to run, or early exit'); p.add_argument('ticker'); p.set_defaults(func=cmd_plan)
    p=sub.add_parser('prompt',help='print a compact self-contained prompt for a domain or agent'); p.add_argument('ticker'); p.add_argument('target'); p.add_argument('--out'); p.set_defaults(func=cmd_prompt)
    p=sub.add_parser('validate'); p.add_argument('ticker'); p.add_argument('agents',nargs='*'); p.set_defaults(func=cmd_validate)
    p=sub.add_parser('digest',help='compact summary of completed reports for Phase 3 and IC'); p.add_argument('ticker'); p.add_argument('--thesis-chars',type=int,default=160); p.add_argument('--unknowns',type=int,default=2); p.set_defaults(func=cmd_digest)
    p=sub.add_parser('sources',help='extract filings to text and build a section index'); p.add_argument('ticker'); p.add_argument('--pdf-dir'); p.add_argument('--max-headings',type=int,default=40); p.set_defaults(func=cmd_sources)
    p=sub.add_parser('cache-macro',help='reuse this run\'s macro overlay for other tickers'); p.add_argument('ticker'); p.set_defaults(func=cmd_cache_macro)
    p=sub.add_parser('aggregate'); p.add_argument('ticker'); p.set_defaults(func=cmd_aggregate)
    args=ap.parse_args(); args.func(args)
if __name__=='__main__': main()
