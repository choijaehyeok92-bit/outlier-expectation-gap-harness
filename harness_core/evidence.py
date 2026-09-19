"""Review-only flags; no numeric score or veto changes."""


def concentration_flags(reports):
    groups = {}
    for report in reports:
        if report.get('analysis_status') != 'complete' or report.get('verdict') != 'support':
            continue
        for evidence in report.get('evidence',[]):
            for kind in ('evidence_id','economic_driver'):
                value = evidence.get(kind)
                if isinstance(value,str) and value.strip():
                    groups.setdefault((kind,value.strip()),set()).add(report['domain'])
    return [{'kind':kind,'value':value,'domains':sorted(domains),'score_effect':0,
             'review':'Check whether these positive domains rely on one economic fact.'}
            for (kind,value),domains in sorted(groups.items()) if len(domains)>1]
