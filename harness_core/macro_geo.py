"""Global-only component cache and deterministic company transmission.

No scoring dependency is imported here. The output changes pacing and requests
fresh domain evidence; it never changes a fundamental score.
"""
from datetime import datetime, timezone, timedelta
import json
from .conditions import number


def instant(value):
    parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def component_valid(name, row, policy):
    if not isinstance(row,dict) or row.get('scope') != 'global':
        return False
    try:
        instant(row['as_of_utc'])
    except (KeyError,ValueError,TypeError,AttributeError):
        return False
    evidence=row.get('evidence')
    if not isinstance(evidence,list) or not evidence or any(not isinstance(e,dict) or not e.get('source') or not e.get('as_of_date') for e in evidence):
        return False
    try:
        if any(instant(e['as_of_date'])>instant(row['as_of_utc']) for e in evidence):
            return False
    except (ValueError,TypeError,AttributeError):
        return False
    if name in policy['geopolitical_dimensions']:
        dimensions = row.get('dimensions',{})
        if not isinstance(dimensions,dict):return False
        for dim in policy['geopolitical_dimensions'][name]:
            item = dimensions.get(dim,{})
            if not isinstance(item,dict) or item.get('level') not in policy['severity_multipliers']:
                return False
            if not isinstance(item.get('structural_events',[]),list):return False
            for event in item.get('structural_events',[]):
                if not isinstance(event,dict) or not all(event.get(k) for k in ('event_id','event_type','source','as_of_date')):
                    return False
                if event['event_type'] not in policy['structural_routes']:
                    return False
                try:
                    if instant(event['as_of_date'])>instant(row['as_of_utc']):return False
                except (ValueError,TypeError,AttributeError):return False
                if any(not isinstance(event.get(k,[]),list) or any(not isinstance(v,str) for v in event.get(k,[])) for k in ('regions','routes','dependencies')):
                    return False
            if any(not isinstance(item.get(k,[]),list) or any(not isinstance(v,str) for v in item.get(k,[])) for k in ('regions','routes','dependencies')):
                return False
    else:
        value = row.get('risk_budget_multiplier')
        if not number(value) or not 0 <= value <= 2:
            return False
    return True


def sanitize(name, row, policy):
    """Allowlist only global data. Never serialize the original MO report."""
    if not component_valid(name,row,policy):
        raise ValueError(f'Invalid global overlay component: {name}')
    clean = {k:row[k] for k in ('scope','as_of_utc','summary','evidence') if k in row}
    if name in policy['geopolitical_dimensions']:
        clean['dimensions'] = {}
        for dim in policy['geopolitical_dimensions'][name]:
            item = row['dimensions'][dim]
            clean['dimensions'][dim] = {k:item[k] for k in ('level','regions','routes','dependencies') if k in item}
            clean['dimensions'][dim]['structural_events'] = [
                {k:event[k] for k in ('event_id','event_type','source','as_of_date','regions','routes','dependencies') if k in event}
                for event in item.get('structural_events',[])]
    else:
        clean['risk_budget_multiplier'] = row['risk_budget_multiplier']
    return clean


def fresh(name, row, as_of, policy):
    if not component_valid(name,row,policy) or row.get('invalidated'):
        return False
    age = instant(as_of) - instant(row['as_of_utc'])
    return timedelta(0) <= age <= timedelta(hours=policy['component_ttl_hours'][name])


def load_components(cache, as_of, policy):
    candidates = {name:[] for name in policy['component_ttl_hours']}
    if cache.exists():
        for path in sorted(cache.glob('*/components.json')):
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                continue
            for name in candidates:
                row = data.get(name)
                # Explicit invalidation supersedes older observations too.
                if isinstance(row,dict):
                    try:
                        stamp = instant(row['as_of_utc'])
                        if stamp <= instant(as_of):
                            candidates[name].append((stamp,path.as_posix(),row))
                    except (ValueError,KeyError,TypeError,AttributeError):
                        pass
    result = {}
    for name, rows in candidates.items():
        if rows:
            row = max(rows,key=lambda x:(x[0],x[1]))[2]
            if fresh(name,row,as_of,policy):
                result[name] = sanitize(name,row,policy)
    return result


def tokens(value):
    if isinstance(value,dict):
        return {str(k).casefold() for k,v in value.items() if number(v) and v>0}
    if isinstance(value,list):
        return {str(v).casefold() for v in value if isinstance(v,str)}
    return set()


def transmission(components, context, reports, policy):
    as_of = context['as_of_date']
    current = {name:sanitize(name,row,policy) for name,row in components.items()
               if name in policy['component_ttl_hours'] and fresh(name,row,as_of,policy)}
    missing = sorted(set(policy['component_ttl_hours'])-set(current))
    financial = {k:v for k,v in current.items() if k not in policy['geopolitical_dimensions']}
    geo = {dim:item for k,v in current.items() for dim,item in v.get('dimensions',{}).items()}
    # TTL expiry cannot erase a known permanent company risk before re-analysis.
    routing_geo=dict(geo)
    for name,row in components.items():
        if name in policy['component_ttl_hours'] and component_valid(name,row,policy) and not row.get('invalidated') and instant(row['as_of_utc'])<=instant(as_of):
            for dim,item in row.get('dimensions',{}).items():
                if item.get('structural_events') and dim not in routing_geo:
                    routing_geo[dim]=item
    multipliers = [v['risk_budget_multiplier'] for v in financial.values()]
    multipliers += [policy['severity_multipliers'][v['level']] for v in geo.values()]
    if missing:
        multipliers.append(policy['missing_component_multiplier'])
    exposure = context.get('geo_exposure') or {}
    company, requests = {}, []
    completed = {r['domain']:r for r in reports if r.get('analysis_status')=='complete'}
    for dimension,item in sorted(routing_geo.items()):
        exposed = set().union(*(tokens(exposure.get(field)) for field in policy['transmission_fields'][dimension]))
        targets = set().union(*(tokens(item.get(key)) for key in ('regions','routes','dependencies')))
        matches = sorted(exposed & targets)
        company[dimension] = {'status':'exposed' if matches else ('unknown' if not exposed or not targets else 'no_direct_match'),
            'matched_exposures':matches, 'level':item['level']}
        for event in item.get('structural_events',[]):
            event_targets = set().union(*(tokens(event.get(k)) for k in ('regions','routes','dependencies')))
            if not (exposed & event_targets):
                continue
            for domain in policy['structural_routes'][event['event_type']]:
                report = completed.get(domain,{})
                reviewed = event['event_id'] in report.get('geo_events_reviewed',[]) and bool(report.get('evidence')) and report.get('as_of_date','') >= event['as_of_date']
                requests.append({'event_id':event['event_id'],'event_type':event['event_type'],
                    'domain':domain,'status':'reviewed' if reviewed else 'pending','source':event['source']})
    pacing = min(multipliers) if multipliers else policy['missing_component_multiplier']
    return {'financial_regime':financial, 'geopolitical_regime':geo,
        'company_transmission':company,'missing_or_stale_components':missing,
        'reanalysis_requests':requests, 'pending_reanalysis_domains':sorted({r['domain'] for r in requests if r['status']=='pending'}),
        'risk_budget_multiplier':pacing,'purchase_pacing_multiplier':pacing,
        'monitoring_urgency':'high' if missing or pacing<1 or requests else 'routine','fundamental_score_effect':0}


def skeleton(policy, as_of):
    components = {}
    for name in policy['component_ttl_hours']:
        row = {'scope':'global','as_of_utc':as_of+'T00:00:00+00:00','summary':'','evidence':[]}
        if name in policy['geopolitical_dimensions']:
            row['dimensions'] = {dim:{'level':'unknown','regions':[],'routes':[],'dependencies':[], 'structural_events':[]}
                                 for dim in policy['geopolitical_dimensions'][name]}
        else:
            row['risk_budget_multiplier'] = 1.0
        components[name] = row
    return components
