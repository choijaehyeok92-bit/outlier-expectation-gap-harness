"""Decision invariants. All writes are isolated in temporary directories."""
import contextlib
import copy
import gzip
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from harness_core import runtime as h, archetypes, macro_geo, calibration, fetch, planner
from harness_core.conditions import resolve, check_condition

REPO = h.ROOT


def report(agent, score=85):
    r = copy.deepcopy(h.load_json(REPO/'templates/agent_report.json'))
    r.update(agent_id=agent['agent_id'],domain=agent['domain'],role=agent['role'],ticker='SYNTH',
        as_of_date='2026-09-19',analysis_status='complete',score_0_100=score,bull_score=100,bear_score=0,
        bull_case='Upside evidence',bear_case='Failure evidence',thesis='Synthetic fixture',verdict='support')
    r['evidence']=[{'evidence_id':f'{agent["agent_id"]}-{i}','claim':'Fixture','source_type':'filing',
        'source':'synthetic','period':'2026','as_of_date':'2026-09-19','value':1,'fact_or_estimate':'fact'} for i in range(3)]
    r['hard_veto_flags']=[{'veto':v,'status':'cleared','rationale':'Synthetic counterevidence'} for v,owners in h.VETO_REVIEWERS.items() if agent['agent_id'] in owners]
    rb=h.rubric_for(agent['domain'])
    if rb:
        r['subscores']=[{'criterion_id':c['id'],'score_0_100':score,'rationale':'Fixture'} for c in rb['criteria']]
    if agent['agent_id']=='EV':
        r['valuation_inputs']={'scenarios':{k:{'owner_fcf_per_share':[10]*h.VAL_POLICY['horizon_years']} for k in ('bear','base','bull')}}
    if agent['agent_id']=='MO':
        r['global_components']=macro_geo.skeleton(h.OVERLAY_POLICY,'2026-09-19')
        for component in r['global_components'].values():
            component['evidence']=copy.deepcopy(r['evidence'][:1])
            for item in component.get('dimensions',{}).values(): item['level']='low'
    return r


def set_scores(r,values):
    for row in r['subscores']:
        row['score_0_100']=values.get(row['criterion_id'],row['score_0_100'])
    r['score_0_100']=h.rubric_score(r)


class V3Tests(unittest.TestCase):
    outlier_price=192          # ~1.25x Base: above Growth's 1.10 gate, inside outlier_growth

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.root_patch=patch.object(h,'ROOT',self.root); self.root_patch.start()
        self.addCleanup(self.root_patch.stop); self.addCleanup(self.tmp.cleanup)
        self.context=h.load_json(REPO/'templates/company_context.json')
        self.context.update(ticker='SYNTH',as_of_date='2026-09-19',current_price=100,net_cash_per_share=5,market_cap_usd=100e9)
        self.save_context()

    def save_context(self):
        h.dump_json(h.run_dir('SYNTH')/'company_context.json',self.context)

    def fixture(self,kind='compounder',reviews=True):
        agents=[a for a in h.MANIFEST if a['agent_id'] not in ('TQ','IC') and (reviews or a['role']=='domain_analyst')]
        reports=[report(a) for a in agents]
        by={r['agent_id']:r for r in reports}
        set_scores(by['DI'],{x['criterion_id']:50 for x in by['DI']['subscores']})
        # LG is an independent axis like DI: default it low so the existing archetypes
        # classify exactly as they did before outlier_growth existed.
        set_scores(by['LG'],{x['criterion_id']:40 for x in by['LG']['subscores']})
        if kind=='buffett_value':
            set_scores(by['RF'],{'incremental_roic':60,'reinvestment_runway':20,'fcf_per_share_quality':90})
            set_scores(by['MT'],{x['criterion_id']:65 for x in by['MT']['subscores']})
        elif kind=='growth':
            by['EV']['valuation_inputs']['revenue_cagr_next_3y']=.20
            for aid in ('MT','RF'):
                set_scores(by[aid],{x['criterion_id']:70 for x in by[aid]['subscores']})
        elif kind=='moonshot':
            self.context['market_cap_usd']=50e9; self.save_context()
            for aid,value in [('DI',85),('MT',50),('RF',50),('FS',65)]:
                set_scores(by[aid],{x['criterion_id']:value for x in by[aid]['subscores']})
        elif kind=='outlier_growth':
            # Deliberately priced above ordinary Growth's <=1.10 gate while the
            # long-duration evidence carries the archetype instead.
            self.context['current_price']=self.outlier_price; self.save_context()
            set_scores(by['LG'],{'opportunity_scale_5y':80,'growth_duration_10y':75,
                                 'culture_adaptability':70,'market_misperception':70})
            # FCF quality stays under Growth's 65 gate: outlier_growth must not require it.
            set_scores(by['RF'],{'incremental_roic':75,'reinvestment_runway':60,'fcf_per_share_quality':60})
            for aid in ('MT','CP','MA'):
                set_scores(by[aid],{x['criterion_id']:70 for x in by[aid]['subscores']})
            set_scores(by['FS'],{x['criterion_id']:65 for x in by['FS']['subscores']})
            set_scores(by['AS'],{'upside_path':75,'permanent_loss':55,
                                 **{x['criterion_id']:70 for x in by['AS']['subscores']
                                    if x['criterion_id'] not in ('upside_path','permanent_loss')}})
        elif kind=='non_fit':
            for r in reports:
                if r['subscores']: set_scores(r,{x['criterion_id']:20 for x in r['subscores']})
        return reports

    def aggregate(self,reports): return h.compute_aggregate('SYNTH',reports)

    @staticmethod
    def minimal_pack(ticker):
        """Smallest pack that satisfies stage 0's required rows."""
        docs=[{'document_id':'DOC-001','source_document':'annual.htm','document_type':'10-K',
               'filing_date':None,'period_end':None,'is_amendment':False}]
        docs+=[{'document_id':'DOC-%03d'%(i+2),'source_document':'q%d.htm'%i,'document_type':'10-Q',
                'filing_date':None,'period_end':None,'is_amendment':False} for i in range(6)]
        fact={'fact_id':'FACT-0001','metric':'revenue','metric_detail':None,'reported_label':'Revenue',
              'statement':'income','gaap_status':'gaap','value_reported':1.0,'unit_kind':'currency',
              'currency':'USD','scale_multiplier':1000000,'period_kind':'quarter','fiscal_year':2026,
              'fiscal_quarter':2,'segment':'consolidated','source_document':'q0.htm',
              'is_amended':False,'is_restated':False,'requires_review':False}
        return {'schema_version':'1.0','ticker':ticker,'as_of_date':'2026-09-19','documents':docs,
                'facts':[fact],'adjustment_candidates':[],'extraction_warnings':[]}

    def test_exactly_five_and_synthetic_classifications(self):
        self.assertEqual(set(h.ARCHETYPE_IDS),
                         {'compounder','outlier_growth','growth','buffett_value','moonshot'})
        self.assertNotIn('long_term_growth',{x['id'] for x in h.STRATEGY['scorecard']})
        self.assertIn('long_term_growth',{x['id'] for x in h.STRATEGY['evaluation_axes']})
        for kind in (*h.ARCHETYPE_IDS,'non_fit'):

            with self.subTest(kind=kind):
                # Reset every context field a fixture may move, so one kind cannot
                # leak its price or size into the next.
                self.context['market_cap_usd']=100e9; self.context['current_price']=100
                self.save_context()
                result=self.aggregate(self.fixture(kind))
                self.assertEqual(result['archetype']['id'],kind)
                self.assertEqual(len(result['archetype_fit']),len(h.ARCHETYPE_IDS))
                if kind!='non_fit': self.assertIn(result['mechanical_pre_ic_state'],h.BUY_STATES)

    def test_value_trap_and_integrity_block_cheap_value(self):
        for veto in (h.VETOES[0],h.VETOES[4],h.VETOES[5]):
            for status in ('confirmed','conditional','candidate'):
                reports=self.fixture('buffett_value')
                owner=h.VETO_REVIEWERS[veto][0]
                r=next(r for r in reports if r['agent_id']==owner)
                next(v for v in r['hard_veto_flags'] if v['veto']==veto)['status']=status
                result=self.aggregate(reports)
                self.assertFalse(result['archetype_fit']['buffett_value']['eligible'])
                self.assertNotIn(result['mechanical_pre_ic_state'],h.BUY_STATES)

    def test_criterion_resolution_missing_and_validation(self):
        reports=self.fixture(); result=self.aggregate(reports); ds=result['domain_scores']
        field='criterion.reinvestment_fcf.incremental_roic'
        self.assertEqual(resolve(field,ds,{}),85)
        self.assertIsNone(resolve('criterion.reinvestment_fcf.missing',ds,{}))
        self.assertIsNone(check_condition({'field':field,'op':'>=','value':75},{},{}))
        for value in (True,float('nan'),float('inf'),73,101):
            bad=copy.deepcopy(reports); bad[0]['subscores'][0]['score_0_100']=value
            with self.assertRaises(ValueError): self.aggregate(bad)
        bad=copy.deepcopy(reports); bad[0]['subscores'].append(bad[0]['subscores'][0])
        with self.assertRaises(ValueError): self.aggregate(bad)

    def test_compounder_each_gate_boundary(self):
        result=self.aggregate(self.fixture()); ds=result['domain_scores']
        policy=next(t for t in h.ARCHETYPES['types'] if t['id']=='compounder')
        for condition in policy['conditions']:
            test=copy.deepcopy(ds); signals={'price_to_base_value':1.0,'market_cap_usd':100e9}
            parts=condition['field'].split('.'); threshold=condition['value']
            def assign(value):
                if parts[0]=='signal': signals[parts[1]]=value
                elif parts[0]=='domain': test[parts[1]]['score']=value
                else: test[parts[1]]['criteria'][parts[2]]=value
            assign(threshold)
            fit=h.classify_archetype(test,signals,85,85,[])['archetype_fit']['compounder']
            self.assertTrue(fit['eligible'],condition)
            assign(threshold+0.001 if condition['op']=='<=' else threshold-0.001)
            self.assertFalse(h.classify_archetype(test,signals,85,85,[])['archetype_fit']['compounder']['eligible'])

    def test_moonshot_market_cap_boundary(self):
        reports=self.fixture('moonshot')
        cap=next(c['value'] for t in h.ARCHETYPES['types'] if t['id']=='moonshot' for c in t['conditions'] if c['field']=='signal.market_cap_usd')
        self.assertEqual(cap,50_000_000_000)  # deliberate regression guard against the old prose $20B
        self.context['market_cap_usd']=cap;self.save_context()
        self.assertEqual(self.aggregate(reports)['archetype']['id'],'moonshot')
        self.context['market_cap_usd']=cap+1;self.save_context()
        self.assertNotIn('moonshot',self.aggregate(reports)['reachable_archetypes_raw'])

    def test_order_independence_and_explicit_ties(self):
        ds=self.aggregate(self.fixture())['domain_scores']; signals={'price_to_base_value':.8,'market_cap_usd':100e9}
        base=h.classify_archetype(ds,signals,85,85,[])
        policy=copy.deepcopy(h.ARCHETYPES);policy['types'].reverse()
        self.assertEqual(base,archetypes.classify(policy,ds,signals,85,85,[]))
        conditions=next(t['conditions'] for t in policy['types'] if t['id']=='compounder')
        fit_axes=next(t['fit_axes'] for t in policy['types'] if t['id']=='compounder')
        # A real tie now needs identical fit axes too: since v3.3 ranking reads
        # fit_axes, matching the gates alone would leave the scores different.
        for t in policy['types']:
            t['conditions']=copy.deepcopy(conditions)
            t['fit_axes']=copy.deepcopy(fit_axes)
        tie=archetypes.classify(policy,ds,signals,85,85,[])
        self.assertEqual(tie['id'],policy['fit_policy']['tie_breaker'][0])
        self.assertEqual(len(tie['secondary']),len(h.ARCHETYPE_IDS)-1)

    def test_shadow_offsets_cannot_flip_decision_and_active_is_explicit(self):
        reports=self.fixture();h.dump_json(h.run_dir('SYNTH')/'run_manifest.json',{'runner':{'provider':'openai'}})
        baseline=self.aggregate(reports)
        with patch.dict(h.PROVIDER_CAL,base_offset=1000,max_abs_offset=100):
            shadow=self.aggregate(reports)
        self.assertEqual(baseline['archetype'],shadow['archetype'])
        self.assertEqual(baseline['score_100'],shadow['score_100'])
        self.assertNotEqual(baseline['domain_scores']['moat_trajectory']['calibrated_score'],shadow['domain_scores']['moat_trajectory']['calibrated_score'])
        h.dump_json(h.run_dir('SYNTH')/'run_manifest.json',{'runner':{'provider':'openai'},'provider_calibration_mode':'active'})
        active=self.aggregate(reports)
        self.assertLess(active['score_100'],baseline['score_100'])
        self.assertEqual(active,self.aggregate(reports))
        ds=copy.deepcopy(active['domain_scores']);h.apply_provider_calibration(ds,active['run_manifest'])
        self.assertEqual(ds,active['domain_scores'])

    def test_optional_tq_and_triage_reachability(self):
        for kind in ('compounder','growth','buffett_value','moonshot'):
            reports=self.fixture(kind)
            triage=[r for r in reports if r['domain'] in h.EXEC['triage_domains']]
            result=self.aggregate(triage)
            self.assertIn(kind,result['reachable_archetypes_raw'])
            self.assertNotIn('turnaround_quality',h.plan('SYNTH',triage,result)['agents'])
        self.context['diagnostics']['turnaround_candidate']=True;self.save_context()
        reports=self.fixture('compounder')
        self.assertIn('turnaround_quality',h.plan('SYNTH',reports)['agents'])
        reports.append(report(next(a for a in h.MANIFEST if a['agent_id']=='TQ')))
        self.assertEqual(self.aggregate(reports)['turnaround_quality_score'],85)
        self.context['diagnostics']['turnaround_candidate']=False;self.save_context()
        without=self.aggregate([r for r in reports if r['agent_id']!='TQ'])
        self.assertEqual(without['coverage_weight'],100)
        self.assertIn(without['mechanical_pre_ic_state'],h.BUY_STATES)

    def test_missing_veto_owner_never_buy_and_planner_requests_it(self):
        reports=self.fixture()
        for aid in sorted({aid for owners in h.VETO_REVIEWERS.values() for aid in owners}):
            pending=[r for r in reports if r['agent_id']!=aid]
            result=self.aggregate(pending)
            self.assertNotIn(result['mechanical_pre_ic_state'],h.BUY_STATES,aid)
            self.assertIn(aid,h.plan('SYNTH',pending,result)['agents'].values(),aid)
        next(r for r in reports if r['hard_veto_flags'])['hard_veto_flags']=[]
        self.assertNotEqual(self.aggregate(reports)['hard_veto_status'],'CLEARED')
        self.assertNotEqual(h.plan('SYNTH',reports)['stage'],'ic')

    def test_early_exit_triage_and_pre_ic_record(self):
        reports=self.fixture('non_fit')
        for subset in ([r for r in reports if r['domain'] in h.EXEC['triage_domains']],reports):
            result=self.aggregate(subset)
            self.assertTrue(result['early_exit'])
            self.assertIsNone(result['ic_verdict'])
            self.assertTrue(result['early_exit_record']['ic_intentionally_not_run'])
            self.assertEqual(h.plan('SYNTH',subset,result)['stage'],'early_exit')
            self.assertEqual(len(result['early_exit_record']['eliminated_archetypes']),len(h.ARCHETYPE_IDS))
        self.assertEqual(result['early_exit_record']['stage'],'pre_ic')

    def test_global_cache_never_copies_company_conclusions(self):
        reports=self.fixture();mo=next(r for r in reports if r['agent_id']=='MO')
        mo['company_transmission']={'ticker':'WRONG','secret':'never cache'}
        mo['global_components']['financial_conditions']['company_transmission']={'ticker':'WRONG'}
        for r in reports: h.dump_json(h.run_dir('SYNTH')/'reports'/f'{r["agent_id"]}.json',r)
        with contextlib.redirect_stdout(io.StringIO()): h.cmd_cache_macro(SimpleNamespace(ticker='SYNTH'))
        cached=h.macro_cache_source('2026-09-19')
        self.assertNotIn('WRONG',json.dumps(cached))
        self.assertNotIn('company_transmission',json.dumps(cached))
        self.assertEqual(len(cached),4)
        later=h.macro_cache_source('2026-09-21')
        self.assertNotIn('geopolitical_events',later)
        self.assertIn('financial_conditions',later)
        self.assertEqual(h.macro_cache_source('2026-09-27'),{})
        self.assertEqual(h.macro_cache_source('2026-09-18'),{})

    def test_ttl_boundary_and_invalidation(self):
        rows=macro_geo.skeleton(h.OVERLAY_POLICY,'2026-09-19')
        for component in rows.values():component['evidence']=[{'source':'fixture','as_of_date':'2026-09-19'}]
        row=rows['geopolitical_events']
        self.assertTrue(macro_geo.fresh('geopolitical_events',row,'2026-09-20',h.OVERLAY_POLICY))
        self.assertFalse(macro_geo.fresh('geopolitical_events',row,'2026-09-20T00:00:01Z',h.OVERLAY_POLICY))
        h.dump_json(self.root/'runs/_macro/2026-09-19/components.json',rows)
        row=copy.deepcopy(row);row.update(as_of_utc='2026-09-19T01:00:00Z',invalidated=True)
        h.dump_json(self.root/'runs/_macro/invalidation/components.json',{'geopolitical_events':row})
        self.assertNotIn('geopolitical_events',h.macro_cache_source('2026-09-20'))

    def test_structural_geo_routes_and_core_score_invariant(self):
        reports=self.fixture();before=self.aggregate(reports)
        mo=next(r for r in reports if r['agent_id']=='MO')
        dimension=mo['global_components']['structural_trade']['dimensions']['export_controls']
        dimension.update(level='critical',dependencies=['chip-tool'],structural_events=[{
            'event_id':'ban-1','event_type':'permanent_export_ban','dependencies':['chip-tool'],
            'source':'synthetic official ban','as_of_date':'2026-09-19'}])
        self.context['geo_exposure']['export_control_dependencies']=['chip-tool'];self.save_context()
        after=self.aggregate(reports)
        self.assertEqual(before['score_100'],after['score_100'])
        self.assertEqual(before['domain_scores'],after['domain_scores'])
        self.assertEqual(after['macro_geo_overlay']['risk_budget_multiplier'],.25)
        self.assertEqual(after['mechanical_pre_ic_state'],'WATCH')
        self.assertEqual(h.plan('SYNTH',reports,after)['stage'],'fundamental_reanalysis')
        for r in reports:
            if r['domain'] in after['macro_geo_overlay']['pending_reanalysis_domains']:r['geo_events_reviewed']=['ban-1']
        self.assertEqual(self.aggregate(reports)['macro_geo_overlay']['pending_reanalysis_domains'],[])
        self.context['geo_exposure']['export_control_dependencies']=['other'];self.save_context()
        other=self.aggregate(reports)
        self.assertEqual(other['macro_geo_overlay']['reanalysis_requests'],[])
        self.assertEqual(other['score_100'],before['score_100'])

    def test_evidence_concentration_flags_do_not_change_scores(self):
        reports=self.fixture();before=self.aggregate(reports)
        for r in reports[:4]:r['evidence'][0].update(evidence_id='backlog-2026',economic_driver='backlog')
        after=self.aggregate(reports)
        self.assertEqual(len(after['evidence_concentration_flags']),2)
        self.assertEqual(before['score_100'],after['score_100'])

    def test_historical_reports_read_without_mutation(self):
        with patch.object(h,'ROOT',REPO):
            paths=list((REPO/'runs').glob('*/reports/EV.json'))
            self.assertTrue(paths)
            ticker=paths[0].parent.parent.name
            files=sorted((REPO/'runs'/ticker).rglob('*.json'))
            before={p:h.sha256_file(p) for p in files}
            result=h.compute_aggregate(ticker,h.load_reports(ticker))
            self.assertIn(result['archetype']['id'],{'compounder','growth','buffett_value','moonshot','non_fit'})
            self.assertEqual(before,{p:h.sha256_file(p) for p in files})
        legacy=report(h.MANIFEST[0]);legacy.pop('subscores');legacy.update(archetype='expectation_gap',provider_calibration={'old':'metadata'})
        result=h.domain_aggregate([legacy])
        self.assertEqual(result['criteria'],{})
        self.assertEqual(result['score_source'],'legacy_declared_score')

    def test_existing_rubric_and_valuation_invariants(self):
        r=report(h.MANIFEST[0],80);r.update(confidence_0_1=.1,unknowns=['one','two'])
        first=h.domain_aggregate([r]);r.update(confidence_0_1=.99,unknowns=[])
        self.assertEqual(first['score'],h.domain_aggregate([r])['score'])
        self.assertEqual(first['dispute_penalty'],0)
        ev=next(r for r in self.fixture() if r['agent_id']=='EV')
        valuation=h.deterministic_valuation(ev,self.context)
        n=h.VAL_POLICY['horizon_years'];rate=h.VAL_POLICY['required_return'];mult=h.VAL_POLICY['terminal_multiples']['base']
        expected=5+sum(10/(1+rate)**i for i in range(1,n+1))+10*mult/(1+rate)**n
        self.assertAlmostEqual(valuation['scenarios']['base']['value_per_share'],expected,places=3)
        self.assertEqual(set(h.CALIBRATION['veto_criteria']['definitions']),set(h.VETOES))
        self.assertTrue(all(h.VETO_REVIEWERS[v] for v in h.VETOES))

    def test_schemas_and_new_reports(self):
        import jsonschema
        for path in (REPO/'schemas').glob('*.json'):
            jsonschema.Draft202012Validator.check_schema(h.load_json(path))
        schema=h.load_json(REPO/'schemas/final_verdict.schema.json')
        report_schema=h.load_json(REPO/'schemas/agent_report.schema.json')
        for kind in ('compounder','growth','buffett_value','moonshot','non_fit'):
            reports=self.fixture(kind);result=self.aggregate(reports)
            jsonschema.validate(h.final_verdict(result,reports),schema)
            for r in reports:
                self.assertEqual(h.validate_report(r),[],r['agent_id'])
                jsonschema.validate(r,report_schema)
        for old in ('expectation_gap','turnaround'):
            final=h.final_verdict(result,reports);final['archetype']=old
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(final,schema)

    def test_generated_documentation_and_policy_invariants(self):
        from harness_core.policy import render
        self.assertEqual((REPO/'docs/POLICY.md').read_text(encoding='utf-8'),render(h.STRATEGY,h.WORKFLOW,h.CALIBRATION))
        self.assertEqual([r['weight'] for r in h.STRATEGY['scorecard']],[15,10,15,15,10,10,15,10])
        self.assertEqual(set(h.ARCHETYPES['fit_policy']['tie_breaker']),{t['id'] for t in h.ARCHETYPES['types']})
        self.assertEqual(h.PROVIDER_CAL['mode'],'shadow')

    def test_ic_can_reduce_state_but_cannot_bypass_veto_or_caps(self):
        reports=self.fixture()
        ic=report(next(a for a in h.MANIFEST if a['agent_id']=='IC'))
        ic['ic_state']='STARTER';reports.append(ic)
        result=self.aggregate(reports)
        self.assertEqual(h.final_verdict(result,reports)['ic_state'],'STARTER')
        ic['ic_state']='EXCEPTIONAL_WINNER'
        final=h.final_verdict(self.aggregate(reports),reports)
        self.assertTrue(final['ic_review_flags'])
        ic['ic_state']='NORMAL'
        owner=next(r for r in reports if r['hard_veto_flags'])
        owner['hard_veto_flags'][0]['status']='conditional'
        final=h.final_verdict(self.aggregate(reports),reports)
        self.assertEqual(final['ic_state'],'WATCH')
        self.assertTrue(final['ic_review_flags'])
        ic['ic_state']='REJECT'
        self.assertEqual(h.final_verdict(self.aggregate(reports),reports)['ic_state'],'REJECT')

    def test_duplicate_confirmed_veto_cannot_be_hidden(self):
        reports=self.fixture();owner=next(r for r in reports if r['hard_veto_flags'])
        veto=copy.deepcopy(owner['hard_veto_flags'][0]);veto['status']='confirmed'
        owner['hard_veto_flags'].append(veto)
        self.assertEqual(self.aggregate(reports)['hard_veto_status'],'CONFIRMED')

    def test_missing_modern_valuation_does_not_use_declared_signal(self):
        reports=self.fixture();ev=next(r for r in reports if r['agent_id']=='EV')
        ev['valuation_inputs']={};ev['archetype_signals']={'price_to_base_value':999}
        result=self.aggregate(reports)
        self.assertNotIn('price_to_base_value',result['archetype']['signals'])
        self.assertFalse(result['early_exit'])
        self.assertEqual(result['mechanical_pre_ic_state'],'WATCH')

    def test_stale_and_malformed_macro_requests_refresh(self):
        reports=self.fixture();mo=next(r for r in reports if r['agent_id']=='MO')
        mo['global_components']['geopolitical_events']['as_of_utc']='2026-09-17T00:00:00Z'
        result=self.aggregate(reports)
        self.assertIn('geopolitical_events',result['macro_geo_overlay']['missing_or_stale_components'])
        self.assertEqual(h.plan('SYNTH',reports,result)['stage'],'macro')
        for value in (None,[],{},True):
            broken=copy.deepcopy(mo['global_components']['structural_trade']);broken['dimensions']=value
            self.assertFalse(macro_geo.component_valid('structural_trade',broken,h.OVERLAY_POLICY))
        mo['global_components']['structural_trade']['as_of_utc']=42
        self.assertIn('structural_trade',self.aggregate(reports)['macro_geo_overlay']['missing_or_stale_components'])

    def test_expiry_cannot_clear_known_structural_reanalysis(self):
        reports=self.fixture();mo=next(r for r in reports if r['agent_id']=='MO')
        dim=mo['global_components']['structural_trade']['dimensions']['sanctions']
        dim['regions']=['region-a'];dim['structural_events']=[{'event_id':'s-1','event_type':'sanctions',
            'regions':['region-a'],'source':'fixture','as_of_date':'2026-09-19'}]
        self.context['geo_exposure']['sanctions_exposure']=['region-a']
        self.context['as_of_date']='2026-09-29';self.save_context()
        result=self.aggregate(reports)
        self.assertTrue(result['macro_geo_overlay']['pending_reanalysis_domains'])
        self.assertEqual(result['mechanical_pre_ic_state'],'WATCH')

    def test_cli_roundtrip_isolated(self):
        for directory in ('harness_core','config','templates','schemas','agents'):
            shutil.copytree(REPO/directory,self.root/directory)
        for filename in ('harness.py','AGENTS.md'):
            shutil.copy2(REPO/filename,self.root/filename)
        def cli(*args,ok=True):
            completed=subprocess.run([sys.executable,'harness.py',*args],cwd=self.root,capture_output=True,text=True,encoding='utf-8')
            if ok:self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
            else:self.assertNotEqual(completed.returncode,0)
            return completed
        cli('init','ROUNDTRIP','--as-of','2026-09-19')
        cli('init','ROUNDTRIP','--as-of','2026-09-19',ok=False)
        run=self.root/'runs/ROUNDTRIP';ctx=h.load_json(run/'company_context.json');ctx.update(current_price=100,net_cash_per_share=5,market_cap_usd=100e9)
        h.dump_json(run/'company_context.json',ctx)
        # Stage 0 first: a new run cannot freeze until the raw pack is in place.
        cli('intake','ROUNDTRIP',ok=False)
        cli('freeze','ROUNDTRIP','--provider','openai','--model','gpt-6-astra',ok=False)
        cli('prompt','ROUNDTRIP','FP')
        h.dump_json(run/h.FINANCIAL_PACK,self.minimal_pack('ROUNDTRIP'))
        cli('intake','ROUNDTRIP')
        cli('validate-pack','ROUNDTRIP')
        cli('freeze','ROUNDTRIP','--provider','openai','--model','gpt-6-astra')
        manifest=h.load_json(run/'run_manifest.json')
        self.assertEqual(manifest['decision_policy_version'],h.VERSIONS['decision_policy_version'])
        self.assertIn('harness_core/archetypes.py',manifest['config_files'])
        cli('prompt','ROUNDTRIP','EV')
        cli('prompt','ROUNDTRIP','TQ',ok=False)
        cli('prompt','ROUNDTRIP','IC',ok=False)
        for r in self.fixture('non_fit'):
            r['ticker']='ROUNDTRIP';h.dump_json(run/'reports'/f'{r["agent_id"]}.json',r)
        cli('validate','ROUNDTRIP')
        cli('plan','ROUNDTRIP')
        cli('aggregate','ROUNDTRIP')
        cli('digest','ROUNDTRIP')
        final=h.load_json(run/'final_verdict.json')
        self.assertTrue(final['early_exit_record']['ic_intentionally_not_run'])
        self.assertIn('Deterministic early exit',(run/'digest.md').read_text(encoding='utf-8'))
        cli('research-plan','ROUNDTRIP')
        cli('research-prompt','ROUNDTRIP')
        rp=h.load_json(run/'research/plan.json')
        self.assertTrue(rp['questions'])
        q=rp['questions'][0]
        packet={'schema_version':'1.0','ticker':rp['ticker'],'as_of_date':rp['as_of_date'],
            'input_snapshot_sha256':rp['input_snapshot_sha256'],'questions':[{
                'research_question_id':q['research_question_id'],'question':q['question'],
                'status':'unresolved','evidence':[],'excluded_post_cutoff':[],
                'remaining_unknowns':['Fixture has no answer'],
                'search_log':[{'tier':0,'source':'synthetic fixture','outcome':'searched_but_not_found'}]}]}
        h.dump_json(self.root/'packet.json',packet)
        cli('research-ingest','ROUNDTRIP',str(self.root/'packet.json'))
        cli('report','ROUNDTRIP')
        self.assertIn('아직 투자위원회 최종 결론이 아닙니다',(run/'easy_report.md').read_text(encoding='utf-8'))
        before={p:p.read_bytes() for p in run.rglob('*') if p.is_file()}
        cli('fork-run','ROUNDTRIP','FORKED','--carry-domain-reports')
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        fork=self.root/'runs/FORKED'
        self.assertEqual((run/'company_context.json').read_bytes(),(fork/'company_context.json').read_bytes())
        self.assertEqual(h.load_json(fork/'reports/IC.json')['analysis_status'],'pending')
        self.assertFalse(h.load_json(fork/'run_manifest.json')['frozen'])
        cli('freeze','FORKED','--review-only')
        cli('aggregate','FORKED')
        self.assertTrue(h.load_json(fork/'final_verdict.json')['review_only'])
        cli('fork-run','ROUNDTRIP','FORKED',ok=False)
        for kind in ('compounder','growth','buffett_value','moonshot'):
            self.context['market_cap_usd']=100e9;self.save_context()
            reports=self.fixture(kind)
            ticker=kind.upper();cli('init',ticker,'--as-of','2026-09-19')
            path=self.root/'runs'/ticker
            context=copy.deepcopy(self.context);context['ticker']=ticker;h.dump_json(path/'company_context.json',context)
            h.dump_json(path/h.FINANCIAL_PACK,self.minimal_pack(ticker))
            cli('freeze',ticker,'--provider','openai','--model','gpt-6-astra')
            for r in reports:
                r['ticker']=ticker;h.dump_json(path/'reports'/f'{r["agent_id"]}.json',r)
            cli('validate',ticker);cli('aggregate',ticker);cli('digest',ticker)
            self.assertEqual(h.load_json(path/'final_verdict.json')['archetype'],kind)
            cli('prompt',ticker,'IC')
            ic=report(next(a for a in h.MANIFEST if a['agent_id']=='IC'));ic.update(ticker=ticker,ic_state='STARTER')
            h.dump_json(path/'reports/IC.json',ic)
            cli('aggregate',ticker)
            self.assertEqual(h.load_json(path/'final_verdict.json')['ic_state'],'STARTER')
        cli('cache-macro','COMPOUNDER');cli('init','CACHED','--as-of','2026-09-19');cli('validate','CACHED','MO')
        self.assertNotIn('COMPOUNDER',json.dumps(h.load_json(self.root/'runs/CACHED/reports/MO.json')))
        code=self.root/'harness_core/conditions.py';code.write_text(code.read_text(encoding='utf-8')+'\n# changed\n',encoding='utf-8')
        self.assertIn('frozen policy',cli('prompt','COMPOUNDER','EV',ok=False).stderr)
        cli('aggregate','COMPOUNDER',ok=False)
        cli('report','COMPOUNDER',ok=False)

    def test_review_only_allows_nonfit_ic_but_never_buy(self):
        reports=self.fixture('non_fit')
        h.dump_json(h.run_dir('SYNTH')/'run_manifest.json',{'review_only':True})
        self.assertFalse(self.aggregate(reports)['early_exit'])
        self.assertEqual(h.plan('SYNTH',reports)['stage'],'ic')
        ic=report(next(a for a in h.MANIFEST if a['agent_id']=='IC'))
        ic['ic_state']='NORMAL';reports.append(ic)
        verdict=h.final_verdict(self.aggregate(reports),reports)
        self.assertEqual(verdict['ic_state'],'WATCH')
        self.assertTrue(verdict['ic_review_flags'])
        ic['ic_state']='WATCH'
        self.assertEqual(h.final_verdict(self.aggregate(reports),reports)['ic_review_flags'],[])


if __name__=='__main__':unittest.main()


class AnchorInterpolationTests(unittest.TestCase):
    """Continuous anchors gain resolution without moving a band centre."""

    def tables(self):
        for domain, rubric in h.CALIBRATION['rubrics'].items():
            for criterion in rubric['criteria']:
                anchors_spec = criterion.get('observable_anchors')
                if anchors_spec:
                    yield f"{domain}.{criterion['id']}", criterion, anchors_spec

    def test_band_centre_is_unchanged_by_interpolation(self):
        from harness_core import anchors
        step = h.CALIBRATION.get('score_step', 5)
        checked = 0
        for name, _criterion, spec in self.tables():
            if spec.get('interpolation', {}).get('mode') != 'band_centre':
                continue
            for row in spec['table']:
                lo, hi = row.get('lo'), row.get('hi')
                if lo is None or hi is None:
                    continue
                centre = (lo + hi) / 2
                self.assertEqual(anchors.interpolate(spec['table'], centre, step), row['score'],
                                 f'{name} moved at the centre of {row["test"]}')
                checked += 1
        self.assertGreater(checked, 0)

    def test_interpolation_is_continuous_across_band_edges(self):
        from harness_core import anchors
        for name, _criterion, spec in self.tables():
            if spec.get('interpolation', {}).get('mode') != 'band_centre':
                continue
            edges = sorted({r['hi'] for r in spec['table'] if r.get('hi') is not None}
                           & {r['lo'] for r in spec['table'] if r.get('lo') is not None})
            for edge in edges:
                width = max(abs(edge), 1.0)
                below = anchors.interpolate(spec['table'], edge - width * 1e-9, None)
                above = anchors.interpolate(spec['table'], edge, None)
                self.assertAlmostEqual(below, above, places=4, msg=f'{name} jumps at {edge}')

    def test_discrete_and_adjective_anchors_are_never_interpolated(self):
        from harness_core import anchors
        for name, _criterion, spec in self.tables():
            if spec.get('interpolation', {}).get('mode') == 'band_centre':
                continue
            self.assertEqual(spec.get('interpolation', {}).get('mode'), 'none', f'{name} must declare a mode')
            self.assertTrue(spec['interpolation'].get('reason'), f'{name} must say why it stays stepped')
            self.assertFalse(anchors.interpolable(_criterion), f'{name} must not carry numeric bounds')
        for rubric in h.CALIBRATION['rubrics'].values():
            for criterion in rubric['criteria']:
                if 'observable_anchors' not in criterion:
                    self.assertNotIn('interpolation', criterion,
                                     'adjective-anchored criteria stay on the published anchors')

    def test_every_policy_threshold_is_reachable(self):
        """A criterion threshold the anchor grid cannot produce is a silent, stricter gate."""
        from harness_core import anchors
        step = h.CALIBRATION.get('score_step', 5)
        grids = {name: anchors.reachable_scores(spec['table'], step) for name, _c, spec in self.tables()}
        checked = 0
        for archetype in h.ARCHETYPES['types']:
            for condition in archetype['conditions']:
                field = condition['field']
                if not field.startswith('criterion.'):
                    continue
                grid = grids.get(field.split('.', 1)[1])
                if grid is None:
                    continue
                self.assertIn(condition['value'], grid,
                              f"{archetype['id']}: {field} {condition['op']} {condition['value']} "
                              f"is unreachable on the anchor grid {grid}")
                checked += 1
        self.assertGreater(checked, 0)


class DispersionTests(unittest.TestCase):
    """Bull/bear width reaches deployment, never the score."""

    def policy(self):
        return h.STATE_POLICY['dispersion_policy']

    def test_downside_skew_narrows_and_upside_never_widens(self):
        from harness_core.state import dispersion_review, narrowed_position
        wide_down = {'d': {'decision_score': 70, 'bull_score': 75, 'bear_score': 40}}
        wide_up = {'d': {'decision_score': 70, 'bull_score': 100, 'bear_score': 65}}
        self.assertGreater(dispersion_review(wide_down, self.policy())['reduce_bands'], 0)
        self.assertEqual(dispersion_review(wide_up, self.policy())['reduce_bands'], 0)
        bands = sorted(h.STATE_POLICY['bands'], key=lambda b: -b['min'])
        floor_state = self.policy()['never_below_state']
        floor = next(i for i, b in enumerate(bands) if b['state'] == floor_state)
        for index, band in enumerate(bands):
            narrowed = narrowed_position(band['state'], 1, h.STATE_POLICY)
            if narrowed is not None:
                self.assertEqual(narrowed, bands[min(index + 1, max(floor, index))]['position_range'])

    def test_dispersion_never_rejects_on_its_own(self):
        """Rejection belongs to scores and vetoes; dispersion only narrows deployment."""
        from harness_core.state import narrowed_position
        reject = next(b['position_range'] for b in h.STATE_POLICY['bands'] if b['state'] == 'REJECT')
        for band in h.STATE_POLICY['bands']:
            for steps in range(1, len(h.STATE_POLICY['bands']) + 2):
                narrowed = narrowed_position(band['state'], steps, h.STATE_POLICY)
                if narrowed is not None and band['state'] != 'REJECT':
                    self.assertNotEqual(narrowed, reject,
                                        f"dispersion pushed {band['state']} into REJECT")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(h, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.tmp.cleanup)
        context = h.load_json(REPO/'templates/company_context.json')
        context.update(ticker='SYNTH', as_of_date='2026-09-19', current_price=100,
                       net_cash_per_share=5, market_cap_usd=100e9)
        h.dump_json(h.run_dir('SYNTH')/'company_context.json', context)

    def test_dispersion_changes_no_score_archetype_or_veto(self):
        agents = [a for a in h.MANIFEST if a['agent_id'] not in ('TQ', 'IC')]
        reports = [report(a) for a in agents]
        baseline = h.compute_aggregate('SYNTH', copy.deepcopy(reports))
        for r in reports:
            if r.get('bear_score') is not None:
                r['bear_score'] = 0
                r['bull_score'] = min(100, r['score_0_100'] + 1)
        skewed = h.compute_aggregate('SYNTH', reports)
        self.assertEqual(baseline['score_100'], skewed['score_100'])
        self.assertEqual(baseline['archetype'], skewed['archetype'])
        self.assertEqual(baseline['veto_gate']['overall'], skewed['veto_gate']['overall'])
        self.assertGreater(skewed['dispersion_review']['mean_skew'], baseline['dispersion_review']['mean_skew'])


class Stage0IntakeTests(unittest.TestCase):
    """Stage 0 gates raw-document readiness and never touches a score."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(h, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.tmp.cleanup)
        context = h.load_json(REPO/'templates/company_context.json')
        context.update(ticker='SYNTH', as_of_date='2026-09-19', current_price=100,
                       net_cash_per_share=5, market_cap_usd=100e9)
        h.dump_json(h.run_dir('SYNTH')/'company_context.json', context)

    def pack(self, quarters=6):
        built = V3Tests.minimal_pack('SYNTH')
        built['documents'] = [built['documents'][0]] + built['documents'][1:1 + quarters]
        return built

    def enforce(self, required=True):
        h.dump_json(h.run_dir('SYNTH')/'run_manifest.json',
                    {'ticker': 'SYNTH', 'financial_pack_required': required})

    def test_legacy_runs_without_a_pack_are_never_blocked(self):
        self.enforce(required=False)
        status = h.intake_status('SYNTH')
        self.assertFalse(status['blocking'])
        self.assertFalse(status['enforced'])
        self.assertEqual(status['stage_0'], 'missing_pack')

    def test_enforced_run_blocks_until_required_documents_exist(self):
        self.enforce()
        self.assertTrue(h.intake_status('SYNTH')['blocking'])
        h.dump_json(h.run_dir('SYNTH')/h.FINANCIAL_PACK, self.pack(quarters=2))
        blocked = h.intake_status('SYNTH')
        self.assertTrue(blocked['blocking'])
        self.assertIn('trailing_quarters', [g['id'] for g in blocked['coverage']['blocking_gaps']])
        h.dump_json(h.run_dir('SYNTH')/h.FINANCIAL_PACK, self.pack(quarters=6))
        ready = h.intake_status('SYNTH')
        self.assertFalse(ready['blocking'])
        self.assertEqual(ready['stage_0'], 'ready')

    def test_plan_puts_intake_first_when_stage_0_is_incomplete(self):
        self.enforce()
        step = h.plan('SYNTH', [])
        self.assertEqual(step['stage'], 'intake')
        self.assertEqual(step['agents'], {'financial_preprocessor': 'FP'})

    def test_freeze_refuses_while_stage_0_is_incomplete(self):
        self.enforce()
        with self.assertRaises(SystemExit):
            h.cmd_freeze(SimpleNamespace(ticker='SYNTH', provider='openai', model='m',
                                         reasoning_effort=None))

    def test_conditional_requirements_are_not_counted_as_gaps(self):
        from harness_core import intake as intake_module
        result = intake_module.coverage(self.pack(), h.INTAKE_POLICY)
        conditional = {r['id'] for r in result['conditional_unverified']}
        self.assertIn('registration_statement', conditional)
        self.assertNotIn('registration_statement', {g['id'] for g in result['advisory_gaps']})
        self.assertNotIn('registration_statement', {g['id'] for g in result['blocking_gaps']})

    def test_invariants_catch_sign_period_and_dangling_reference(self):
        from harness_core import intake as intake_module
        pack = self.pack()
        base = pack['facts'][0]
        base.update(metric='capex', value_reported=-5)
        pack['facts'].append({**base, 'fact_id': 'FACT-0002', 'metric': 'revenue',
                              'value_reported': 1, 'period_kind': 'fy', 'fiscal_quarter': 2})
        pack['facts'].append({**base, 'fact_id': 'FACT-0003', 'metric': 'other',
                              'metric_detail': None, 'value_reported': 1})
        pack['adjustment_candidates'].append({'adjustment_id': 'ADJ-001', 'type': 'sbc',
                                              'amount_fact_id': 'FACT-9999',
                                              'judgment_status': 'requires_economic_review'})
        errors = ' | '.join(intake_module.pack_invariants(pack))
        self.assertIn('positive cost magnitude', errors)
        self.assertIn('period_kind=fy cannot carry fiscal_quarter', errors)
        self.assertIn('metric=other requires metric_detail', errors)
        self.assertIn('FACT-9999 does not exist', errors)

    def test_instant_may_carry_the_quarter_it_falls_in(self):
        from harness_core import intake as intake_module
        pack = self.pack()
        pack['facts'][0].update(metric='cash', period_kind='instant', fiscal_quarter=2,
                                statement='balance_sheet', value_reported=1)
        self.assertEqual(intake_module.pack_invariants(pack), [])

    def test_shipped_pack_passes_its_own_schema_and_invariants(self):
        import jsonschema
        from harness_core import intake as intake_module
        pack = h.load_json(REPO/'runs/NVDA-V3-2026-09-19'/h.FINANCIAL_PACK)
        jsonschema.Draft7Validator(h.load_json(REPO/'schemas/financial_pack.schema.json')).validate(pack)
        self.assertEqual(intake_module.pack_invariants(pack), [])


class Stage0FetchTests(unittest.TestCase):
    """EDGAR acquisition is deterministic retrieval; the cutoff binds it."""

    TICKERS = {'0': {'cik_str': 1730168, 'ticker': 'AVGO', 'title': 'Broadcom Inc.'}}

    def submissions(self, rows):
        columns = {'form': [], 'filingDate': [], 'accessionNumber': [],
                   'primaryDocument': [], 'reportDate': [], 'primaryDocDescription': []}
        for i, (form, date) in enumerate(rows):
            columns['form'].append(form)
            columns['filingDate'].append(date)
            columns['accessionNumber'].append('0001730168-%02d-000001' % i)
            columns['primaryDocument'].append('doc%d.htm' % i)
            columns['reportDate'].append(date)
            columns['primaryDocDescription'].append(form)
        return {'name': 'Broadcom Inc.', 'filings': {'recent': columns}}

    def opener(self, rows, captured=None):
        def _opener(url, user_agent, timeout=30):
            if captured is not None:
                captured.append((url, user_agent))
            if 'company_tickers' in url:
                return json.dumps(self.TICKERS).encode()
            if 'submissions' in url:
                return json.dumps(self.submissions(rows)).encode()
            return b'<html>filing body</html>'
        return _opener

    def test_resolves_ticker_and_rejects_unknown_one(self):
        opener = self.opener([])
        self.assertEqual(fetch.resolve_cik('AVGO', 'ua', opener)[0], 1730168)
        with self.assertRaises(fetch.FetchError):
            fetch.resolve_cik('NOSUCH', 'ua', opener)

    def test_open_requests_identity_encoding_from_sec(self):
        captured = {}
        class Response:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc, tb): return False
            def read(self): return b'{}'
        def fake_urlopen(request, timeout=30):
            captured['accept_encoding'] = request.get_header('Accept-encoding')
            return Response()
        with patch('harness_core.fetch.urllib.request.urlopen', fake_urlopen):
            self.assertEqual(fetch._open('https://www.sec.gov/files/company_tickers.json',
                                         'Tester t@example.com'), b'{}')
        self.assertEqual(captured['accept_encoding'], 'identity')

    def test_nothing_filed_after_the_cutoff_is_planned(self):
        rows, _ = fetch.recent_filings(1730168, 'ua', self.opener(
            [('10-K', '2026-12-01'), ('10-K', '2026-06-01'), ('10-Q', '2026-05-01')]))
        planned = fetch.plan(rows, h.INTAKE_POLICY, '2026-09-18')
        self.assertEqual(planned['excluded_post_cutoff'], 1)
        self.assertTrue(all(r['filingDate'] <= '2026-09-18' for r in planned['download']))

    def test_plan_reports_a_shortfall_rather_than_inventing_filings(self):
        rows, _ = fetch.recent_filings(1730168, 'ua', self.opener(
            [('10-K', '2026-06-01')] + [('10-Q', '2026-0%d-01' % m) for m in (1, 2)]))
        planned = fetch.plan(rows, h.INTAKE_POLICY, '2026-09-18')
        trailing = next(s for s in planned['shortfalls'] if s['requirement'] == 'trailing_quarters')
        self.assertEqual(trailing['shortfall'], 4)

    def test_download_writes_files_and_carries_the_contact(self):
        captured = []
        opener = self.opener([('10-K', '2026-06-01')], captured)
        rows, _ = fetch.recent_filings(1730168, 'ua', opener)
        planned = fetch.plan(rows, h.INTAKE_POLICY, '2026-09-18')
        with tempfile.TemporaryDirectory() as tmp:
            saved = fetch.download(1730168, planned['download'][:1], Path(tmp), 'Tester t@example.com', opener)
            self.assertEqual(len(saved), 1)
            self.assertTrue((Path(tmp)/saved[0]['file']).exists())
            self.assertIn('Archives/edgar/data/1730168', saved[0]['source_url'])
        self.assertTrue(all(agent for _url, agent in captured))

    def test_blocked_egress_surfaces_as_a_fetch_error(self):
        def blocked(url, user_agent, timeout=30):
            raise OSError('CONNECT tunnel failed, response 403')
        with self.assertRaises(fetch.FetchError):
            fetch.resolve_cik('AVGO', 'ua', lambda u, a, timeout=30: blocked(u, a))

    def test_default_opener_decodes_gzip_responses(self):
        payload = json.dumps(self.TICKERS).encode()

        class Response:
            headers = {'Content-Encoding': 'gzip'}
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self): return gzip.compress(payload)

        with patch('urllib.request.urlopen', return_value=Response()):
            self.assertEqual(json.loads(fetch._open('https://www.sec.gov/test', 'ua')), self.TICKERS)

    def test_every_checklist_row_declares_its_edgar_forms(self):
        for requirement in h.INTAKE_POLICY['requirements']:
            self.assertIn('edgar_forms', requirement, requirement['id'])


class OutlierGrowthTests(unittest.TestCase):
    """The fifth archetype earns eligibility on duration and scale, not on cheapness."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(h, 'ROOT', Path(self.tmp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.tmp.cleanup)
        self.context = h.load_json(REPO/'templates/company_context.json')
        self.context.update(ticker='SYNTH', as_of_date='2026-09-19', current_price=V3Tests.outlier_price,
                            net_cash_per_share=5, market_cap_usd=100e9)
        self.save_context()

    def save_context(self):
        h.dump_json(h.run_dir('SYNTH')/'company_context.json', self.context)

    # V3Tests owns the fixture builders; reuse them rather than duplicating.
    fixture = V3Tests.fixture
    outlier_price = V3Tests.outlier_price

    def aggregate(self, reports):
        return h.compute_aggregate('SYNTH', reports)

    def eligible(self, reports):
        return self.aggregate(reports)['archetype_fit']['outlier_growth']['eligible']

    def tweak(self, **subscores_by_agent):
        reports = self.fixture('outlier_growth')
        by = {r['agent_id']: r for r in reports}
        for agent, values in subscores_by_agent.items():
            known = {row['criterion_id'] for row in by[agent]['subscores']}
            unknown = set(values) - known
            self.assertFalse(unknown, f'{agent} has no criterion {sorted(unknown)}')
            set_scores(by[agent], values)
        return reports

    def verdict(self, reports):
        """The shape stored in final_verdict.json, built the way cmd_aggregate builds it."""
        return h.final_verdict(self.aggregate(reports), reports)

    def test_baseline_fixture_is_eligible_and_ordinary_growth_is_not(self):
        result = self.aggregate(self.fixture('outlier_growth'))
        self.assertTrue(result['archetype_fit']['outlier_growth']['eligible'])
        self.assertFalse(result['archetype_fit']['growth']['eligible'])
        self.assertIn('signal.price_to_base_value', result['archetype_fit']['growth']['failed_conditions'])
        self.assertEqual(result['archetype']['id'], 'outlier_growth')
        self.assertIn(result['mechanical_pre_ic_state'], h.BUY_STATES)

    def test_cheapness_and_current_fcf_quality_are_not_required(self):
        conditions = {c['field'] for t in h.ARCHETYPES['types'] if t['id'] == 'outlier_growth'
                      for c in t['conditions']}
        self.assertNotIn('signal.price_to_base_value', conditions)
        self.assertNotIn('criterion.reinvestment_fcf.fcf_per_share_quality', conditions)
        self.assertNotIn('signal.revenue_cagr_next_3y', conditions)
        for required in ('domain.customer_product', 'domain.financial_survival',
                         'criterion.asymmetry.upside_path', 'criterion.long_term_growth.market_misperception'):
            self.assertIn(required, conditions)

    def test_A_short_term_growth_without_five_year_scale_fails(self):
        self.assertFalse(self.eligible(self.tweak(LG={'opportunity_scale_5y': 70})))

    def test_B_scale_without_duration_fails(self):
        self.assertFalse(self.eligible(self.tweak(LG={'growth_duration_10y': 60})))

    def test_C_without_a_specific_expectation_gap_fails(self):
        self.assertFalse(self.eligible(self.tweak(LG={'market_misperception': 60})))

    def test_D_without_a_five_times_path_fails(self):
        self.assertFalse(self.eligible(self.tweak(AS={'upside_path': 70})))

    def test_E_weak_financial_survival_fails(self):
        self.assertFalse(self.eligible(self.tweak(FS={c: 55 for c in
                                                      ('liquidity_leverage', 'stress_survival', 'dilution_offbalance')})))

    def test_F_price_above_bull_blocks_any_buy_state(self):
        veto = '현재가격이 비현실적인 Bull Case 이상을 요구'
        reports = self.fixture('outlier_growth')
        owner = h.VETO_REVIEWERS[veto][0]
        flags = next(r for r in reports if r['agent_id'] == owner)['hard_veto_flags']
        next(v for v in flags if v['veto'] == veto)['status'] = 'confirmed'
        result = self.aggregate(reports)
        self.assertFalse(result['archetype_fit']['outlier_growth']['eligible'])
        self.assertNotIn(result['mechanical_pre_ic_state'], h.BUY_STATES)

    def test_G_missing_LG_leaves_it_reachable_but_not_eligible_and_planner_asks(self):
        reports = [r for r in self.fixture('outlier_growth') if r['agent_id'] != 'LG']
        result = self.aggregate(reports)
        fit = result['archetype_fit']['outlier_growth']
        self.assertFalse(fit['eligible'])
        self.assertTrue(any(f.startswith('criterion.long_term_growth') or f == 'domain.long_term_growth'
                            for f in fit['missing_conditions']))
        self.assertEqual(fit['failed_conditions'], [])
        self.assertIn('outlier_growth', result['reachable_archetypes_raw'])
        step = planner.next_stage(reports, result, self.context, h.MANIFEST, h.SCORE_DOMAINS,
                                  h.EXEC['triage_domains'], h.ARCHETYPES, h.VETO_REVIEWERS)
        self.assertEqual(step['agents'].get('long_term_growth'), 'LG')

    def test_G2_planner_does_not_ask_for_LG_once_outlier_growth_is_unreachable(self):
        reports = [r for r in self.tweak(CP={c: 30 for c in ('customer_roi', 'retention_usage', 'unit_economics')})
                   if r['agent_id'] != 'LG']
        result = self.aggregate(reports)
        self.assertNotIn('outlier_growth', result['reachable_archetypes_raw'])
        step = planner.next_stage(reports, result, self.context, h.MANIFEST, h.SCORE_DOMAINS,
                                  h.EXEC['triage_domains'], h.ARCHETYPES, h.VETO_REVIEWERS)
        self.assertNotIn('long_term_growth', step['agents'])

    def test_H_outlier_growth_can_be_secondary_to_compounder(self):
        reports = self.fixture('outlier_growth')
        by = {r['agent_id']: r for r in reports}
        self.context['current_price'] = 100; self.save_context()      # back inside compounder's 1.2 gate
        for agent in ('MT', 'MA', 'FS'):
            set_scores(by[agent], {x['criterion_id']: 80 for x in by[agent]['subscores']})
        set_scores(by['RF'], {'incremental_roic': 80, 'reinvestment_runway': 75, 'fcf_per_share_quality': 75})
        result = self.aggregate(reports)
        self.assertEqual(result['archetype']['id'], 'compounder')
        self.assertIn('outlier_growth', result['archetype']['secondary'])

    def test_I_tie_break_order_is_deterministic_and_config_driven(self):
        order = h.ARCHETYPES['fit_policy']['tie_breaker']
        self.assertEqual(order, ['compounder', 'outlier_growth', 'growth', 'buffett_value', 'moonshot'])
        self.assertEqual(sorted(order), sorted(h.ARCHETYPE_IDS))
        self.assertLess(order.index('outlier_growth'), order.index('growth'))

    def test_L_final_verdict_schema_accepts_the_fifth_archetype(self):
        import jsonschema
        verdict = self.verdict(self.fixture('outlier_growth'))
        self.assertEqual(verdict['archetype'], 'outlier_growth')
        self.assertIn('outlier_growth', verdict['archetype_fit'])
        jsonschema.Draft7Validator(h.load_json(REPO/'schemas/final_verdict.schema.json')).validate(verdict)

    def test_L2_v31_verdicts_with_four_archetypes_still_validate(self):
        """A stored v3.1 verdict has four fits and must keep validating unmigrated."""
        import jsonschema
        verdict = self.verdict(self.fixture('outlier_growth'))
        legacy = {**verdict, 'schema_version': '3.1', 'archetype': 'growth',
                  'archetype_fit': {k: v for k, v in verdict['archetype_fit'].items() if k != 'outlier_growth'}}
        jsonschema.Draft7Validator(h.load_json(REPO/'schemas/final_verdict.schema.json')).validate(legacy)

    def test_long_term_growth_stays_out_of_the_core_score(self):
        with_axis = self.aggregate(self.fixture('outlier_growth'))
        stripped = self.aggregate([r for r in self.fixture('outlier_growth') if r['agent_id'] != 'LG'])
        self.assertEqual(with_axis['score_100'], stripped['score_100'])
        self.assertEqual(with_axis['coverage_weight'], stripped['coverage_weight'])
        self.assertIn('long_term_growth', with_axis['axis_scores'])
