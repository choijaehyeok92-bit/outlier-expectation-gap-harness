"""Locked owner-FCF valuation arithmetic."""
from .conditions import number

def valuation_settings(ctx, VAL_POLICY):
    ov=ctx.get('valuation_overrides') or {}
    om={k:v for k,v in (ov.get('terminal_multiples') or {}).items() if v is not None}
    mult={**VAL_POLICY['terminal_multiples'],**om}
    return {'required_return':float(ov.get('required_return') if ov.get('required_return') is not None else VAL_POLICY['required_return']),
        'horizon_years':int(VAL_POLICY['horizon_years']),'terminal_multiples':{k:float(v) for k,v in mult.items()}}

def valuation_sanity(paths, scenarios, current_price, policy):
    """Deterministic arithmetic sanity checks on a completed valuation.

    Only an internal contradiction blocks. A Bear intrinsic value above Base is
    arithmetic that cannot be right, so it stops the run. Everything else here
    is a signal for a reviewer: near-term FCF paths can legitimately cross when
    the scenarios assume different reinvestment, a terminal-heavy Base is a fact
    about the model rather than a verdict on the company, and a price above Bull
    is exactly what the existing valuation Hard Veto exists to judge. None of
    these confirm that veto — its owner still does.
    """
    policy = policy or {}
    checks = []

    def add(check_id, status, detail, blocking=False, severity='info'):
        checks.append({'id': check_id, 'status': status, 'severity': severity,
                       'blocking': bool(blocking), 'detail': detail})

    bad_years = [i + 1 for i, row in enumerate(zip(paths['bear'], paths['base'], paths['bull']))
                 if not row[0] <= row[1] <= row[2]]
    if bad_years:
        blocking = policy.get('yearly_scenario_crossing', 'review') == 'block'
        add('yearly_scenario_order', 'FAIL' if blocking else 'REVIEW',
            f'bear/base/bull FCF paths cross in year(s) {bad_years}; '
            'this may be economically valid but requires EV review',
            blocking=blocking, severity='critical' if blocking else 'material')
    else:
        add('yearly_scenario_order', 'PASS', 'bear <= base <= bull for every forecast year')

    values = [scenarios[k]['value_per_share'] for k in ('bear', 'base', 'bull')]
    if values[0] <= values[1] <= values[2]:
        add('scenario_value_order', 'PASS', 'Bear <= Base <= Bull intrinsic values')
    else:
        add('scenario_value_order', 'FAIL', f'intrinsic values are not ordered: {values}',
            blocking=True, severity='critical')

    base_fraction = scenarios['base'].get('terminal_fraction')
    review_at = float(policy.get('terminal_fraction_review', 0.80))
    high_at = float(policy.get('terminal_fraction_high', 0.90))
    if base_fraction is None:
        add('terminal_value_concentration', 'REVIEW',
            'Base operating value is non-positive or terminal fraction is unavailable', severity='high')
    elif base_fraction >= high_at:
        add('terminal_value_concentration', 'REVIEW',
            f'Base terminal fraction {base_fraction:.1%} >= {high_at:.0%}', severity='high')
    elif base_fraction >= review_at:
        add('terminal_value_concentration', 'REVIEW',
            f'Base terminal fraction {base_fraction:.1%} >= {review_at:.0%}', severity='material')
    else:
        add('terminal_value_concentration', 'PASS', f'Base terminal fraction {base_fraction:.1%}')

    if policy.get('price_above_bull_review', True):
        bull = scenarios['bull']['value_per_share']
        if current_price > bull:
            add('price_above_bull_value', 'REVIEW',
                f'current price {current_price:.4f} > Bull value {bull:.4f}; '
                'route to the existing valuation Hard Veto owner', severity='high')
        else:
            add('price_above_bull_value', 'PASS', 'current price does not exceed Bull value')

    blocking = any(row['blocking'] and row['status'] == 'FAIL' for row in checks)
    status = 'FAIL' if blocking else ('REVIEW' if any(row['status'] == 'REVIEW' for row in checks) else 'PASS')
    return {'status': status, 'blocking': blocking, 'checks': checks}


def deterministic_valuation(report,ctx, VAL_POLICY):
    if not report or report.get('analysis_status')!='complete': return {'status':'INCOMPLETE','reason':'EV report incomplete'}
    vi=report.get('valuation_inputs') or {}; price=ctx.get('current_price'); net_cash=ctx.get('net_cash_per_share')
    if not number(price) or not number(net_cash): return {'status':'INCOMPLETE','reason':'frozen price/net cash missing'}
    s=valuation_settings(ctx,VAL_POLICY); n=s['horizon_years']; r=s['required_return']; out={}; paths={}
    for case in ('bear','base','bull'):
        path=((vi.get('scenarios') or {}).get(case) or {}).get('owner_fcf_per_share')
        if not isinstance(path,list) or len(path)!=n or any(not number(x) for x in path):
            return {'status':'INCOMPLETE','reason':f'{case}.owner_fcf_per_share must have {n} numeric years'}
        path=[float(x) for x in path]; paths[case]=path
        pv=sum(float(x)/((1+r)**i) for i,x in enumerate(path,1))
        tv=float(path[-1])*s['terminal_multiples'][case]/((1+r)**n); op=pv+tv; value=float(net_cash)+op
        out[case]={'value_per_share':round(value,4),'pv_owner_fcf':round(pv,4),'pv_terminal':round(tv,4),
            'terminal_multiple':s['terminal_multiples'][case],'terminal_fraction':round(tv/op,4) if op>0 else None}
    pct=ctx.get('valuation_percentile_5y')
    if pct is None: pct=vi.get('valuation_percentile_5y')
    signals={'price_to_base_value':round(float(price)/out['base']['value_per_share'],4) if out['base']['value_per_share']>0 else None,
        'valuation_percentile_5y':pct,'revenue_cagr_next_3y':vi.get('revenue_cagr_next_3y')}
    sanity=valuation_sanity(paths,out,float(price),VAL_POLICY.get('sanity_policy'))
    return {'status':'COMPLETE','method':'locked owner-FCF/share DCF','required_return':r,'horizon_years':n,
        'net_cash_per_share':float(net_cash),'current_price':float(price),'scenarios':out,'signals':signals,
        'sanity':sanity}
