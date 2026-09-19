"""Locked owner-FCF valuation arithmetic."""
from .conditions import number

def valuation_settings(ctx, VAL_POLICY):
    ov=ctx.get('valuation_overrides') or {}
    om={k:v for k,v in (ov.get('terminal_multiples') or {}).items() if v is not None}
    mult={**VAL_POLICY['terminal_multiples'],**om}
    return {'required_return':float(ov.get('required_return') if ov.get('required_return') is not None else VAL_POLICY['required_return']),
        'horizon_years':int(VAL_POLICY['horizon_years']),'terminal_multiples':{k:float(v) for k,v in mult.items()}}

def deterministic_valuation(report,ctx, VAL_POLICY):
    if not report or report.get('analysis_status')!='complete': return {'status':'INCOMPLETE','reason':'EV report incomplete'}
    vi=report.get('valuation_inputs') or {}; price=ctx.get('current_price'); net_cash=ctx.get('net_cash_per_share')
    if not number(price) or not number(net_cash): return {'status':'INCOMPLETE','reason':'frozen price/net cash missing'}
    s=valuation_settings(ctx,VAL_POLICY); n=s['horizon_years']; r=s['required_return']; out={}
    for case in ('bear','base','bull'):
        path=((vi.get('scenarios') or {}).get(case) or {}).get('owner_fcf_per_share')
        if not isinstance(path,list) or len(path)!=n or any(not number(x) for x in path):
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
