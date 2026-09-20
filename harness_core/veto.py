"""Hard Veto gate.

Two rules hold the gate up, and both are ownership rules:

1. Only a configured owner can end the question. A `cleared` or `confirmed`
   from someone who does not own the veto is a finding, not a verdict — the
   veto goes to UNRESOLVED and the finding is preserved in
   `non_owner_escalations` so the owner has to answer it.
2. A missing owner report or a missing owner assessment never reads as
   cleared. Silence is not clearance.
"""
ESCALATING = ('candidate', 'conditional', 'confirmed')


def veto_gate(reports, VETOES, VETO_REVIEWERS):
    by_id = {r.get('agent_id'): r for r in reports if r.get('analysis_status') == 'complete'}
    items = []
    confirmed = []
    unresolved = []
    pending = []
    escalations = []
    for veto in VETOES:
        owners = VETO_REVIEWERS.get(veto, [])
        statuses = []
        missing_reports = []
        missing_assessments = []
        for r in by_id.values():
            for hit in (v for v in r.get('hard_veto_flags', []) if v.get('veto') == veto):
                statuses.append({'agent_id': r.get('agent_id'), 'owner': r.get('agent_id') in owners,
                                 'status': hit.get('status'), 'rationale': hit.get('rationale')})
        for aid in owners:
            r = by_id.get(aid)
            if not r:
                missing_reports.append(aid)
            elif not any(x['agent_id'] == aid for x in statuses):
                missing_assessments.append(aid)
        owner_status = [x['status'] for x in statuses if x['owner']]
        non_owner = [x for x in statuses if not x['owner'] and x['status'] in ESCALATING]
        if 'confirmed' in owner_status:
            status = 'CONFIRMED'
        elif non_owner or missing_assessments or any(s in ('candidate', 'conditional') for s in owner_status):
            status = 'UNRESOLVED'
        elif missing_reports:
            status = 'PENDING_REVIEW'
        elif owners and all(any(x['agent_id'] == aid and x['status'] == 'cleared' for x in statuses) for aid in owners):
            status = 'CLEARED'
        else:
            status = 'UNRESOLVED'
        row = {'veto': veto, 'status': status, 'owners': owners, 'assessments': statuses,
               'missing_reports': missing_reports, 'missing_assessments': missing_assessments,
               'non_owner_escalations': non_owner}
        items.append(row)
        escalations.extend({'veto': veto, 'owners': owners, **x} for x in non_owner)
        if status == 'CONFIRMED':
            confirmed.append(row)
        elif status == 'UNRESOLVED':
            unresolved.append(row)
        elif status == 'PENDING_REVIEW':
            pending.append(row)
    overall = 'CONFIRMED' if confirmed else ('UNRESOLVED' if unresolved else ('PENDING_REVIEW' if pending else 'CLEARED'))
    return {'overall': overall, 'items': items, 'confirmed': confirmed, 'unresolved': unresolved,
            'pending': pending, 'non_owner_escalations': escalations}
