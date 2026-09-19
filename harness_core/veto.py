"""Explicit ownership: missing assessments never mean cleared."""
def veto_gate(reports, VETOES, VETO_REVIEWERS):
    by_id={r.get('agent_id'):r for r in reports if r.get('analysis_status')=='complete'}
    items=[]; confirmed=[]; unresolved=[]; pending=[]
    for veto in VETOES:
        owners=VETO_REVIEWERS.get(veto,[]); statuses=[]; missing_reports=[]; missing_assessments=[]
        for r in by_id.values():
            for hit in (v for v in r.get('hard_veto_flags',[]) if v.get('veto')==veto):
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
