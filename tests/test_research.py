"""Research intake and reader-facing decisions must preserve the evidence boundary."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import jsonschema

from harness_core import runtime as h, research, plain_report

REPO = h.ROOT


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name)
        self.context = {'ticker':'TEST','as_of_date':'2026-09-19','current_price':100}
        h.dump_json(self.run/'company_context.json', self.context)
        h.dump_json(self.run/'run_manifest.json', {'input_snapshot_sha256':'a'*64})
        self.report = {'agent_id':'RF','domain':'reinvestment_fcf','analysis_status':'complete',
            'unknowns':['Is maintenance capex disclosed?'],'next_checks':[], 'hard_veto_flags':[]}
        self.plan = research.build_plan(self.run, [self.report], {'stage':'domain_analysis'}, {}, h.CALIBRATION)
        self.schema = h.load_json(REPO/'schemas/research_packet.schema.json')
        self.evidence = {'evidence_id':'SUP-RF-CAPEX-001','claim':'Capex was 4','value':4,'unit':'USD million',
            'source_tier':1,'source_type':'10-Q','source':'sources/filing.txt','source_section':'Cash flow',
            'source_origin':'SEC filing accession 0001','period':'Q2 FY2026','publication_date':'2026-08-01',
            'as_of_date':'2026-09-19','eligible_under_as_of_date':True,'fact_or_estimate':'fact',
            'economic_driver':'cash_conversion','conflict_with_verified_fact':False,'requires_refreeze':False,
            'confidence':.99,'verified_fact_refs':[]}
        self.question = {'research_question_id':self.plan['questions'][0]['research_question_id'],
            'question':self.plan['questions'][0]['question'],'status':'resolved','evidence':[self.evidence],
            'remaining_unknowns':[], 'excluded_post_cutoff':[],
            'search_log':[{'tier':0,'source':'sources/filing.txt','outcome':'found'}]}
        self.packet = {'schema_version':'1.0','ticker':'TEST','as_of_date':'2026-09-19',
            'input_snapshot_sha256':'a'*64,'questions':[self.question]}

    def validate(self, prior=()):
        return research.validate_packet(self.packet,self.plan,self.run,self.schema,prior)

    def test_local_plan_stable_prioritized_and_missing_input_visible(self):
        self.report['hard_veto_flags']=[{'veto':h.VETOES[4],'status':'conditional'}]
        p = research.build_plan(self.run,[self.report],{}, {},h.CALIBRATION)
        self.assertEqual(p['questions'][0]['priority'],0)
        self.assertIn('구성요건',p['questions'][0]['question'])
        self.assertEqual(p['questions'][1]['research_question_id'],self.question['research_question_id'])
        missing = [i['path'] for i in p['inputs'] if not i['exists']]
        self.assertIn('sources/financials/derived_metrics.json', missing)

    def test_intake_preserves_files_and_reports(self):
        before = {p:p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        result = self.validate()
        self.assertEqual(result['research_summary']['questions_resolved'],1)
        self.assertEqual(result['recommended_harness_reruns'],['RF'])
        self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_portable_hash_ignores_only_line_endings(self):
        path=self.run/'fixture.txt'
        path.write_bytes(b'first\nsecond\n'); first=h.sha256_file(path)
        path.write_bytes(b'first\r\nsecond\r\n'); self.assertEqual(h.sha256_file(path),first)
        path.write_bytes(b'first\r\nchanged\r\n'); self.assertNotEqual(h.sha256_file(path),first)

    def test_post_cutoff_excluded_not_supplemented(self):
        self.evidence.update(publication_date='2026-09-20',eligible_under_as_of_date=False)
        self.question.update(status='unresolved',remaining_unknowns=['No eligible disclosure'])
        result = self.validate()
        self.assertEqual(result['candidate_new_evidence'],[])
        self.assertEqual(len(result['excluded_post_cutoff']),1)
        self.assertEqual(result['recommended_harness_reruns'],[])
        self.evidence['eligible_under_as_of_date']=True
        with self.assertRaisesRegex(ValueError,'cutoff eligibility'): self.validate()

    def test_conflict_quarantined_and_not_auto_overwritten(self):
        self.evidence.update(value=120,verified_fact_refs=['context:current_price'])
        with self.assertRaisesRegex(ValueError,'Undeclared'): self.validate()
        self.evidence.update(conflict_with_verified_fact=True,verified_value=100,new_value=120,possible_reason='period mismatch')
        self.question.update(status='unresolved',remaining_unknowns=['Reviewer must resolve date mismatch'])
        result = self.validate()
        self.assertEqual(result['research_summary']['verified_fact_conflicts'],1)
        self.assertEqual(result['candidate_new_evidence'],[])
        self.assertEqual(h.load_json(self.run/'company_context.json')['current_price'],100)

    def test_restated_primary_requires_refreeze_even_without_value_conflict(self):
        self.evidence['is_restatement']=True
        self.question.update(status='unresolved',remaining_unknowns=['Requires refreeze review'])
        result = self.validate()
        self.assertTrue(result['research_summary']['requires_refreeze'])
        self.assertEqual(result['candidate_new_evidence'],[])

    def test_wrong_identity_unknown_question_and_invalid_date(self):
        for field,value in [('ticker','OTHER'),('as_of_date','2026-09-18'),('input_snapshot_sha256','b'*64)]:
            with self.subTest(field=field):
                old = self.packet[field]; self.packet[field]=value
                with self.assertRaises(ValueError): self.validate()
                self.packet[field]=old
        self.evidence['publication_date']='2026-99-99'
        with self.assertRaises(ValueError): self.validate()

    def test_search_order_and_decision_field_rejected(self):
        self.question['search_log'][0]['tier']=4
        with self.assertRaisesRegex(ValueError,'Existing files'): self.validate()
        self.question['search_log'][0]['tier']=0
        self.packet['ic_state']='NORMAL'
        with self.assertRaises(jsonschema.ValidationError): self.validate()

    def test_no_normalization_as_fact_without_direct_disclosure(self):
        self.evidence['metric']='maintenance_capex'
        with self.assertRaisesRegex(ValueError,'normalization'): self.validate()
        self.evidence['fact_or_estimate']='estimate'
        self.evidence['possible_adjustment']=True
        self.assertEqual(self.validate()['research_summary']['questions_resolved'],1)

    def test_source_tier_and_unknown_fact_reference(self):
        self.evidence['source_tier']=4
        with self.assertRaisesRegex(ValueError,'tier mismatch'): self.validate()
        self.evidence['source_tier']=1
        self.evidence['verified_fact_refs']=['normalized:DOES-NOT-EXIST']
        with self.assertRaisesRegex(ValueError,'QA-unverified'): self.validate()

    def test_same_fact_requires_same_id_and_driver_across_packets(self):
        first = self.validate()
        self.evidence['evidence_id']='SUP-RF-CAPEX-002'
        with self.assertRaisesRegex(ValueError,'Same fact'): self.validate([first])
        self.evidence['evidence_id']='SUP-RF-CAPEX-001'
        self.evidence['economic_driver']='new_driver'
        with self.assertRaisesRegex(ValueError,'different fact'): self.validate([first])
        self.evidence['economic_driver']='cash_conversion'
        result = self.validate([first])
        self.assertEqual(result['research_summary']['new_primary_evidence'],0)
        self.assertEqual(result['recommended_harness_reruns'],[])

    def test_content_addressed_archive_and_domain_routing(self):
        result = self.validate()
        path = self.run/'research'/('result-'+research.fingerprint(result)+'.json')
        h.dump_json(path,result)
        self.assertEqual(len(research.supplemental(self.run,'reinvestment_fcf')),1)
        self.assertEqual(research.supplemental(self.run,'moat_trajectory'),[])
        result['candidate_new_evidence'][0]['value']=99
        h.dump_json(path,result)
        with self.assertRaisesRegex(ValueError,'archive changed'): research.supplemental(self.run)

    def test_veto_both_sides_and_unresolved_missing_not_zero(self):
        self.plan['questions'][0]['triggers']=['hard_veto']
        with self.assertRaisesRegex(ValueError,'both sides'): self.validate()
        self.question.update(evidence_supporting_veto=[],evidence_against_veto=[])
        with self.assertRaisesRegex(ValueError,'counterevidence'): self.validate()
        self.question.update(status='partial',remaining_unknowns=['Counterevidence not found'])
        self.assertEqual(self.validate()['research_summary']['questions_unresolved'],1)
        self.packet['questions']=[]
        self.assertEqual(self.validate()['research_summary']['questions_unresolved'],1)


class GrowthAndReportTests(unittest.TestCase):
    def setUp(self):
        self.policy = next(t for t in h.ARCHETYPES['types'] if t['id']=='growth')
        self.signals = {'revenue_cagr_next_3y':.20,'price_to_base_value':1.0,'market_cap_usd':1e12}
        self.ds = {d:{'score':85,'criteria':{c['id']:85 for c in h.RUBRICS[d]['criteria']}} for d in h.RUBRICS}

    def fit(self, score=85, veto=()):
        return h.classify_archetype(self.ds,self.signals,score,score,[],veto)['archetype_fit']['growth']

    def test_growth_each_condition_boundary_missing_gate_and_veto(self):
        for condition in self.policy['conditions']:
            old_ds,old_signals=copy.deepcopy(self.ds),dict(self.signals)
            kind,*rest=condition['field'].split('.')
            target=self.signals if kind=='signal' else (self.ds[rest[0]] if kind=='domain' else self.ds[rest[0]]['criteria'])
            key=rest[0] if kind=='signal' else ('score' if kind=='domain' else rest[1])
            target[key]=condition['value']
            self.assertTrue(self.fit()['eligible'],condition['field'])
            target[key]+= .001 if condition['op']=='<=' else -.001
            self.assertFalse(self.fit()['eligible'],condition['field'])
            del target[key]
            self.assertFalse(self.fit()['eligible'],condition['field'])
            self.ds,self.signals=old_ds,old_signals
        self.assertFalse(self.fit(64.99)['eligible'])
        self.assertTrue(self.fit(65)['eligible'])
        self.assertFalse(self.fit(veto=[{'veto':h.VETOES[0]}])['eligible'])
        self.assertFalse(self.policy['valuation_tolerant'])

    def test_plain_report_provisional_missing_and_guarded_final(self):
        context={'ticker':'TEST','company_name':'Company','as_of_date':'2026-09-19','currency':'USD'}
        v={'decision_policy_version':'3.1','ic_verdict':None,'ic_state':'INCOMPLETE','archetype':'non_fit',
           'coverage_weight':15,'hard_veto_status':'PENDING_REVIEW','valuation_model':{'status':'INCOMPLETE'},
           'macro_geo_overlay':{'pending_reanalysis_domains':[]},'domain_scores':{},'score_100':None}
        text=plain_report.render(context,v,[])
        self.assertIn('아직 투자위원회 최종 결론이 아닙니다',text)
        self.assertIn('자료 없음',text)
        self.assertNotIn('**0.00**',text)
        v.update(ic_state='WATCH',ic_verdict={'ic_state':'NORMAL','plain_language':{'business':'<script>alert(1)</script>'}},
                 ic_review_flags=['blocked'])
        text=plain_report.render(context,v,[])
        self.assertIn('신규 매수 보류',text)
        self.assertNotIn('**현재 결과: 일반 투자 검토',text)
        self.assertIn('&lt;script&gt;',text)
        self.assertIn('현재 신규 매수 승인은 없습니다',text)
