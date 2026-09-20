"""Decision invariants. All writes are isolated in temporary directories."""
import contextlib
import copy
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

from harness_core import runtime as h, archetypes, macro_geo, calibration
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
        elif kind=='non_fit':
            for r in reports:
                if r['subscores']: set_scores(r,{x['criterion_id']:20 for x in r['subscores']})
        return reports

    def aggregate(self,reports): return h.compute_aggregate('SYNTH',reports)

    def test_exactly_four_and_synthetic_classifications(self):
        self.assertEqual({t['id'] for t in h.ARCHETYPES['types']},{'compounder','growth','buffett_value','moonshot'})
        for kind in ('compounder','growth','buffett_value','moonshot','non_fit'):
            with self.subTest(kind=kind):
                self.context['market_cap_usd']=100e9; self.save_context()
                result=self.aggregate(self.fixture(kind))
                self.assertEqual(result['archetype']['id'],kind)
                self.assertEqual(len(result['archetype_fit']),4)
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
        for t in policy['types']: t['conditions']=copy.deepcopy(conditions)
        tie=archetypes.classify(policy,ds,signals,85,85,[])
        self.assertEqual(tie['id'],policy['fit_policy']['tie_breaker'][0])
        self.assertEqual(len(tie['secondary']),3)

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
            self.assertEqual(len(result['early_exit_record']['eliminated_archetypes']),4)
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
        cli('freeze','ROUNDTRIP','--provider','openai','--model','gpt-6-astra')
        manifest=h.load_json(run/'run_manifest.json')
        self.assertEqual(manifest['decision_policy_version'],'3.1')
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
