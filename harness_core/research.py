"""Gap-driven research. Only reviewers decide; intake never edits frozen inputs."""
from datetime import date
import copy
import hashlib
import json

INPUTS = ('company_context.json', 'run_manifest.json', 'sources/README.md',
          'sources/financials/normalized_financials.json', 'sources/financials/derived_metrics.json',
          'sources/financials/adjustment_candidates.json', 'sources/financials/qa_report.json',
          'digest.md', 'aggregate.json')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def inventory(run):
    names = list(INPUTS[:-2]) + [p.relative_to(run).as_posix() for p in sorted((run/'reports').glob('*.json'))
                            if read(p).get('analysis_status') == 'complete'] + list(INPUTS[-2:])
    return [{'path': name, 'exists': (run/name).is_file(),
             'sha256': hashlib.sha256((run/name).read_bytes()).hexdigest() if (run/name).is_file() else None}
            for name in names]


def build_plan(run, reports, stage, aggregate, calibration):
    context = read(run/'company_context.json')
    owners = {r['domain']:r['agent_id'] for r in reports}
    questions = {}
    def add(aid, text, trigger, priority, domain=None):
        text = ' '.join(text.split())
        rid = f'RQ-{aid}-{fingerprint([aid, text])[:10].upper()}'
        q = questions.setdefault(rid, {'research_question_id': rid, 'question': text,
            'agent_id': aid, 'domain': domain, 'triggers': [], 'priority': priority,
            'search_order': ['existing_files', 'regulatory_filings', 'company_ir', 'official_industry', 'secondary'],
            'status': 'pending'})
        q['priority'] = min(q['priority'], priority)
        if trigger not in q['triggers']: q['triggers'].append(trigger)
    for report in reports:
        if report.get('analysis_status') != 'complete': continue
        aid, domain = report['agent_id'], report['domain']
        for flag in report.get('hard_veto_flags', []):
            if flag.get('status') in ('candidate', 'conditional'):
                definition = calibration.get('veto_criteria', {}).get('definitions', {}).get(flag['veto'], {})
                add(aid, f"{flag['veto']}: 구성요건 {json.dumps(definition, ensure_ascii=False)}. 지지·반박 1차 증거를 각각 확인한다.", 'hard_veto', 0, domain)
        for field in ('unknowns', 'next_checks'):
            for question in report.get(field, []): add(aid, question, field, 1 if aid == 'ED' else 2, domain)
    for key, fit in aggregate.get('archetype_fit', {}).items():
        for field in fit.get('missing_conditions', []):
            if not field.startswith(('signal.', 'criterion.')): continue
            domain = field.split('.')[1] if field.startswith('criterion.') else 'expectation_valuation'
            add(owners.get(domain, 'EV' if domain == 'expectation_valuation' else 'OBS'),
                f'{field} 평가에 필요한 누락 관측값은 무엇인가?', 'missing_observable', 1, domain)
    for req in aggregate.get('macro_geo_overlay', {}).get('reanalysis_requests', []):
        if req['status'] == 'pending':
            add('GEO', f"{req['event_id']}: {req['domain']}에 미치는 구조적 영향", 'structural_geopolitical_event', 0, req['domain'])
    if aggregate.get('valuation_model', {}).get('status') == 'INCOMPLETE':
        add('EV', aggregate['valuation_model']['reason'], 'missing_valuation_input', 1, 'expectation_valuation')
    snapshot = read(run/'run_manifest.json').get('input_snapshot_sha256')
    available = {q['research_question_id'] for p in history(run) if p['input_snapshot_sha256'] == snapshot
                 for q in p['questions'] if q['status'] == 'resolved'}
    for rid in available & questions.keys(): questions[rid]['status'] = 'evidence_available_for_review'
    return {'schema_version': '1.0', 'ticker': context['ticker'], 'as_of_date': context['as_of_date'],
        'inputs': inventory(run), 'input_snapshot_sha256': read(run/'run_manifest.json').get('input_snapshot_sha256'),
        'harness_plan': stage, 'questions': sorted(questions.values(), key=lambda q: (q['priority'], q['research_question_id']))}


def prompt(plan):
    return ('# Research Orchestrator\n\n'
        'Harness asks. Research retrieves. Verified evidence stays frozen. Domain reviewers decide.\n'
        '각 질문은 existing_files부터 확인한다. 답이 있으면 웹 검색하지 않는다. 공백만 규제 공시 → IR → 공식 산업자료 → 2차 자료 순서로 검색한다.\n'
        'evidence_available_for_review는 research/result-*.json에 답이 이미 수용되어 reviewer 검토가 필요한 질문이다. 같은 질문을 다시 검색하지 않는다.\n'
        'publication_date와 period를 구분하고 마감일 이후 자료는 excluded_post_cutoff로 분리한다. 검색하지 않은 내용을 보충하지 않는다.\n'
        'fact / estimate / interpretation을 분리한다. 계산값·maintenance capex·경제적 ROIC는 직접 공시가 아니면 fact가 아니다.\n'
        '수치 비교는 verified_fact_refs에 normalized:FACT-ID 또는 context:key를 기록한다. README 주장 비교는 readme:원문 구절을 사용한다.\n'
        '충돌은 verified_value/new_value/possible_reason 및 requires_refreeze로 기록한다. 수정공시도 원본을 덮어쓰지 않는다.\n'
        '동일 사실은 같은 evidence_id/economic_driver, 동일 원 보도자료는 같은 source_origin을 유지한다.\n'
        'Hard Veto 지지·반박 evidence ID와 remaining_unknowns만 제공한다. 점수·등급·veto 판정·포지션은 작성하지 않는다.\n'
        '경제적 조정은 possible_adjustment로만 표시한다. 충분한 답을 얻으면 검색을 멈춘다.\n'
        'resolved는 충분한 증거, partial은 일부 증거, unresolved는 합리적 검색 후 미확보다. search_log에 실제 조회 경로와 결과를 기록한다.\n'
        '출력 계약: schemas/research_packet.schema.json. 모든 새 evidence에 공개일·대상기간·마감일 적격성을 기록한다.\n\n'
        + json.dumps(plan, ensure_ascii=False, indent=2) + '\n')


def verified_catalog(run):
    catalog = {'context:'+k: v for k, v in read(run/'company_context.json').items()}
    path = run/'sources/financials/normalized_financials.json'
    qa = run/'sources/financials/qa_report.json'
    if path.exists() and qa.exists():
        cutoff = read(run/'company_context.json')['as_of_date']
        for fact in read(path).get('facts', []):
            if fact.get('requires_review') is False and fact.get('fact_id') and fact.get('filing_date', '9999') <= cutoff:
                catalog['normalized:'+fact['fact_id']] = fact['value_reported']
    return catalog


def signature(e):
    return fingerprint([e['source_origin'], e['period'], e.get('metric') or e['claim'], e['value'], e['unit']])


def validate_packet(packet, plan, run, schema, prior=()):
    import jsonschema
    jsonschema.validate(packet, schema)
    cutoff = date.fromisoformat(plan['as_of_date'])
    if packet['ticker'] != plan['ticker'] or packet['as_of_date'] != plan['as_of_date']:
        raise ValueError('Research ticker/cutoff differs from plan')
    if packet['input_snapshot_sha256'] != plan['input_snapshot_sha256']:
        raise ValueError('Research snapshot differs from plan')
    requested = {q['research_question_id']: q for q in plan['questions']}
    catalog = verified_catalog(run)
    readme = (run/'sources/README.md').read_text(encoding='utf-8') if (run/'sources/README.md').exists() else ''
    result = copy.deepcopy(packet)
    seen_questions, ids, signatures, drivers = set(), {}, {}, {}
    for old in prior:
        for e in old.get('candidate_new_evidence', []) + old.get('excluded_post_cutoff', []) + old.get('conflicts', []):
            ids[e['evidence_id']] = signature(e)
            signatures[signature(e)] = e['evidence_id']
            drivers[e['evidence_id']] = e['economic_driver']
    accepted, excluded, conflicts, reruns = {}, {}, {}, set()
    prior_ids = set(ids)
    for question in result['questions']:
        rid = question['research_question_id']
        if rid not in requested or rid in seen_questions: raise ValueError('Unknown or duplicate research question: '+rid)
        seen_questions.add(rid)
        if question['question'] != requested[rid]['question']: raise ValueError('Question changed: '+rid)
        log = question['search_log']
        if not log or log[0]['tier'] != 0: raise ValueError('Existing files must be checked first: '+rid)
        tiers = [entry['tier'] for entry in log]
        if tiers != sorted(tiers): raise ValueError('Search priority must proceed from primary to secondary sources')
        usable, late = [], []
        for evidence in question['evidence'] + question['excluded_post_cutoff']:
            pub = date.fromisoformat(evidence['publication_date'])
            if evidence['as_of_date'] != plan['as_of_date']: raise ValueError('Evidence cutoff mismatch')
            eligible = pub <= cutoff
            if evidence['eligible_under_as_of_date'] != eligible: raise ValueError('Incorrect cutoff eligibility')
            if evidence['source_tier'] > 2 and evidence['source_type'] in ('10-K','10-Q','8-K','regulatory_filing','audited_financials'):
                raise ValueError('Primary source type/tier mismatch')
            if evidence.get('metric') in ('maintenance_capex', 'normalized_owner_fcf', 'economic_roic') and evidence['fact_or_estimate'] == 'fact':
                if not evidence.get('direct_company_disclosure') or evidence['source_tier'] > 2:
                    raise ValueError('Economic normalization requires a directly disclosed primary source to be a fact')
            sig, eid = signature(evidence), evidence['evidence_id']
            if eid in ids and (ids[eid] != sig or drivers[eid] != evidence['economic_driver']):
                raise ValueError('Evidence ID reused for a different fact/driver: '+eid)
            if sig in signatures and signatures[sig] != eid: raise ValueError('Same fact must reuse its evidence ID')
            ids[eid], signatures[sig], drivers[eid] = sig, eid, evidence['economic_driver']
            detected = []
            for ref in evidence['verified_fact_refs']:
                if ref.startswith('readme:'):
                    if not ref[7:] or ref[7:] not in readme: raise ValueError('Unknown README reference')
                elif ref not in catalog: raise ValueError('Unknown or QA-unverified fact reference: '+ref)
                elif catalog[ref] != evidence.get('comparison_value', evidence['value']): detected.append(catalog[ref])
            if detected and not evidence['conflict_with_verified_fact']:
                raise ValueError('Undeclared verified fact conflict: '+eid)
            if evidence['conflict_with_verified_fact']:
                if not evidence.get('possible_reason') or 'verified_value' not in evidence or 'new_value' not in evidence:
                    raise ValueError('Conflict detail required')
                if evidence['new_value'] != evidence['value'] or (detected and evidence['verified_value'] not in detected):
                    raise ValueError('Conflict values differ from referenced fact')
            if evidence.get('is_amendment') or evidence.get('is_restatement'): evidence['requires_refreeze'] = True
            if not eligible:
                late.append(evidence); excluded[eid] = evidence
            elif evidence['conflict_with_verified_fact'] or evidence['requires_refreeze']:
                conflicts[eid] = evidence
            else:
                usable.append(evidence); accepted[eid] = evidence
        question['evidence'], question['excluded_post_cutoff'] = usable, late
        question['agent_id'] = requested[rid]['agent_id']
        question['domain'] = requested[rid]['domain']
        for field in ('evidence_supporting_veto', 'evidence_against_veto'):
            if any(eid not in {e['evidence_id'] for e in usable} for eid in question.get(field, [])):
                raise ValueError('Veto evidence must reference eligible unconflicted evidence')
        if 'hard_veto' in requested[rid]['triggers']:
            if any(field not in question for field in ('evidence_supporting_veto', 'evidence_against_veto')):
                raise ValueError('Veto research must explicitly document both sides')
            if question['status'] == 'resolved' and not all(question[field] for field in ('evidence_supporting_veto', 'evidence_against_veto')):
                raise ValueError('Absent veto counterevidence remains an unknown; reviewer decides the veto status')
        if question['status'] == 'resolved' and (not usable or question['remaining_unknowns']):
            raise ValueError('Resolved requires usable evidence and no remaining unknowns')
        if question['status'] != 'resolved' and not question['remaining_unknowns']:
            raise ValueError('Partial/unresolved must explain remaining unknowns')
        if question['status'] == 'partial' and not usable: raise ValueError('Partial requires usable evidence')
        aid = requested[rid]['agent_id']
        if any(e['evidence_id'] not in prior_ids for e in usable):
            if aid not in ('OBS', 'GEO'): reruns.add(aid)
            elif requested[rid]['domain']: reruns.add(requested[rid]['domain'])
    missing = sorted(set(requested)-seen_questions)
    resolved = [q['research_question_id'] for q in result['questions'] if q['status'] == 'resolved']
    unresolved = sorted(set(requested)-set(resolved))
    result.update(research_summary={'questions_requested': len(requested), 'questions_resolved': len(resolved),
        'questions_unresolved': len(unresolved), 'new_primary_evidence': sum(e['source_tier'] <= 2 and eid not in prior_ids for eid, e in accepted.items()),
        'new_secondary_evidence': sum(e['source_tier'] > 2 and eid not in prior_ids for eid, e in accepted.items()),
        'verified_fact_conflicts': sum(e['conflict_with_verified_fact'] for e in conflicts.values()),
        'requires_refreeze': any(e['requires_refreeze'] for e in conflicts.values())},
        resolved_questions=resolved, unresolved_questions=unresolved, unsubmitted_questions=missing,
        candidate_new_evidence=list(accepted.values()), conflicts=list(conflicts.values()),
        excluded_post_cutoff=list(excluded.values()), recommended_harness_reruns=sorted(reruns),
        source_independence_groups=sorted({e['source_origin'] for e in accepted.values()}))
    return result


def history(run):
    packets = []
    for path in sorted((run/'research').glob('result-*.json')):
        packet = read(path)
        if path.stem != 'result-'+fingerprint(packet):
            raise ValueError('Research archive changed: '+str(path))
        packets.append(packet)
    return packets


def supplemental(run, domain=None):
    """Only current-snapshot, eligible candidates; never import decision fields."""
    manifest = read(run/'run_manifest.json')
    rows = {}
    for packet in history(run):
        if packet['input_snapshot_sha256'] != manifest.get('input_snapshot_sha256'): continue
        for q in packet['questions']:
            if domain and q['domain'] != domain: continue
            for e in q['evidence']:
                if e['eligible_under_as_of_date'] and e['publication_date'] <= packet['as_of_date'] and not e['conflict_with_verified_fact'] and not e['requires_refreeze']:
                    rows[e['evidence_id']] = e
    return [rows[k] for k in sorted(rows)]
