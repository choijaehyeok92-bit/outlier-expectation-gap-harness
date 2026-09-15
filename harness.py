#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, statistics, math, shutil

ROOT=Path(__file__).resolve().parent
STRATEGY=json.loads((ROOT/'config/strategy.json').read_text(encoding='utf-8'))
MANIFEST=json.loads((ROOT/'config/agents_manifest.json').read_text(encoding='utf-8'))
SCORE_DOMAINS={x['id']:x for x in STRATEGY['scorecard']}


def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump_json(p:Path,obj): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def cmd_init(args):
    run=ROOT/'runs'/args.ticker.upper()
    (run/'reports').mkdir(parents=True,exist_ok=True)
    (run/'cross_exam').mkdir(exist_ok=True)
    ctx=load_json(ROOT/'templates/company_context.json')
    ctx['ticker']=args.ticker.upper(); ctx['as_of_date']=args.as_of
    dump_json(run/'company_context.json',ctx)
    for a in MANIFEST:
        rpt=load_json(ROOT/'templates/agent_report.json')
        rpt.update(agent_id=a['agent_id'],ticker=args.ticker.upper(),as_of_date=args.as_of,domain=a['domain'],role=a['role'])
        dump_json(run/'reports'/f"{a['agent_id']}.json",rpt)
    shutil.copy(ROOT/'templates/one_page_investment_record.md',run/'one_page_investment_record.md')
    print(run)

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
    usable=[r for r in reports if r.get('analysis_status')=='complete' and r.get('score_0_100') is not None]
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

def cmd_aggregate(args):
    run=ROOT/'runs'/args.ticker.upper()/ 'reports'
    if not run.exists(): raise SystemExit('run not found; use init first')
    reports=[]
    for p in run.glob('*.json'):
        try: reports.append(load_json(p))
        except Exception as e: print('skip',p,e)
    by_domain={}
    for r in reports: by_domain.setdefault(r.get('domain','unknown'),[]).append(r)
    ds={}
    for d in SCORE_DOMAINS:
        if d in by_domain: ds[d]=domain_aggregate(by_domain[d])
    # weighted 100 point score: convert 0-100 domain score to assigned weight
    total=0; covered=0
    for d,meta in SCORE_DOMAINS.items():
        if d in ds and ds[d] is not None:
            w=meta['weight']; total += ds[d]['score']/100*w; covered+=w
    normalized = total/covered*100 if covered else None
    # veto scan across all agents
    confirmed=[]; unresolved=[]; candidates=[]
    for r in reports:
        if r.get('analysis_status')!='complete':
            continue
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
    # mechanical pre-IC state only
    if covered < 100: state='INCOMPLETE'
    elif confirmed: state='REJECT'
    elif unresolved: state='WATCH'
    elif normalized>=90: state='EXCEPTIONAL_WINNER_CANDIDATE'
    elif normalized>=85: state='CORE_WINNER_CANDIDATE'
    elif normalized>=75: state='NORMAL_CANDIDATE'
    elif normalized>=65: state='STARTER_OR_WATCH'
    else: state='REJECT'
    pos={'EXCEPTIONAL_WINNER_CANDIDATE':'6-10% (IC cap)','CORE_WINNER_CANDIDATE':'4-8%','NORMAL_CANDIDATE':'2-4%','STARTER_OR_WATCH':'0-2%','WATCH':'0% until veto cleared','REJECT':'0%','INCOMPLETE':'N/A'}[state]
    result={'ticker':args.ticker.upper(),'score_100':round(normalized,2) if normalized is not None else None,'coverage_weight':covered,'classification':cls,'hard_veto_status':veto_status,'mechanical_pre_ic_state':state,'position_range_pre_ic':pos,'domain_scores':ds,'disputes':disputes,'confirmed_vetoes':confirmed,'unresolved_vetoes':unresolved}
    out=ROOT/'runs'/args.ticker.upper()/'aggregate.json'; dump_json(out,result); print(json.dumps(result,ensure_ascii=False,indent=2))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init'); p.add_argument('ticker'); p.add_argument('--as-of',required=True); p.set_defaults(func=cmd_init)
    p=sub.add_parser('aggregate'); p.add_argument('ticker'); p.set_defaults(func=cmd_aggregate)
    args=ap.parse_args(); args.func(args)
if __name__=='__main__': main()
