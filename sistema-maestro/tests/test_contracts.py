import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_academia_play import validate_manifest,validate_progress,merge_progress,validate_gate,ContractError

def load(name):return json.loads((ROOT/'examples'/name).read_text())
class TestContracts(unittest.TestCase):
 def setUp(self):self.m=load('manifest.json')
 def fails(self,msg):
  errors=validate_manifest(self.m)
  expected={
   'missing objective':'unknown objectives reference',
   'missing oracle':'unknown oracles reference',
   'missing engine':'unknown engines reference',
   'illegal status':'not one of',
   'ADR required':'CREATE requires ADR',
   'source page':'pages not inspected',
   'error concept':'unknown misconceptions reference',
   'exam leakage':'exam leakage',
   'transfer':'transfer variant missing',
   'no semantic variation':'two distinct variant families required',
   'missing diagnostic evidence':'diagnostic evidence required',
   'cycle':'cycle involving',
   'orphan lab':'non-empty',
   'inconclusive fixture':'INCONCLUSIVE fixtures required',
  }.get(msg,msg)
  self.assertTrue(any(expected in e for e in errors),
                  f'Expected {expected!r}; got {errors!r}')
  return errors
 def test_positive_synthetic(self):self.assertEqual(validate_manifest(self.m),[])
 def test_bad_objective_ref(self):
  self.m['modules'][0]['objective_ids']=['ghost'];self.fails('missing objective')
 def test_bad_oracle_ref(self):
  self.m['activities'][0]['oracle_id']='ghost';self.fails('missing oracle')
 def test_bad_engine_ref(self):
  self.m['labs'][0]['engine_id']='ghost';self.fails('missing engine')
 def test_status_enum(self):
  self.m['labs'][0]['status']='FAKE';self.fails('illegal status')
 def test_create_without_adr(self):
  self.m['labs'][0]['decision_adr']='';self.fails('ADR required')
 def test_page_uninspected(self):
  self.m['activities'][0]['source_refs'][0]['pages']=[33];self.fails('source page')
 def test_misconception_missing(self):
  self.m['activities'][0]['feedback_by_error'][0]['misconception_id']='missing';self.fails('error concept')
 def test_duplicate_items_between_exam_and_practice(self):
  self.m['activities'][0]['mode_item_ids']['exam_preparation']=['item-route'];self.fails('exam leakage')
 def test_missing_transfer_variant(self):
  self.m['activities'][0]['transfer_variant_id']='unknown';self.fails('transfer')
 def test_variants_only_change_numbers(self):
  for v in self.m['activities'][0]['variants']:v['family']='same-template'
  self.fails('no semantic variation')
 def test_bad_diagnostic_unlock(self):
  r=self.m['routes'][0];r['unlock_policy']='DIAGNOSTIC_EQUIVALENCE';r['diagnostic_evidence_required']=False
  self.fails('missing diagnostic evidence')
 def test_valid_diagnostic_unlock(self):
  r=self.m['routes'][0];r['unlock_policy']='DIAGNOSTIC_EQUIVALENCE';r['diagnostic_oracle_id']='oracle-linear';r['diagnostic_evidence_required']=True
  self.assertEqual(validate_manifest(self.m),[])
 def test_cycle_modules(self):
  self.m['modules'][0]['depends_on']=['M1'];self.fails('cycle')
 def test_labs_need_objective(self):
  self.m['labs'][0]['course_objective_refs']=[];self.fails('orphan lab')
 def test_inconclusive_fixture_required(self):
  self.m['oracles'][0]['has_inconclusive']=False;self.fails('inconclusive fixture')
 def test_progress_valid(self):self.assertEqual(validate_progress(load('progress.json')),[])
 def test_mastered_without_evidence_rejected(self):
  p=load('progress.json');p['mastery_evidence']=[];self.assertTrue(validate_progress(p))
 def test_merge_monotonic(self):
  p=load('progress.json');stale=copy.deepcopy(p)
  stale['access_grants']=[];stale['mastery_evidence']=[];stale['mastery_estimate']='NEEDS_REVIEW';stale['updated_at']='2026-11-21T00:00:00Z'
  merged=merge_progress(p,stale)
  self.assertEqual(len(merged['access_grants']),1)
  self.assertEqual(merged['mastery_estimate'],'MASTERED')
  self.assertEqual(merge_progress(merged,p)['access_grants'],merged['access_grants'])
 def test_merge_idempotent(self):
  p=load('progress.json');self.assertEqual(merge_progress(p,p)['mastery_evidence'],p['mastery_evidence'])
 def test_merge_conflict(self):
  p=load('progress.json');q=copy.deepcopy(p);q['user_id']='other'
  with self.assertRaises(ContractError):merge_progress(p,q)
 def test_gate_notrun_valid(self):self.assertEqual(validate_gate(load('gate.json')),[])
 def test_gate_fake_pass(self):
  g=load('gate.json');g['result']='PASS';self.assertTrue(validate_gate(g))
 def test_gate_deploy_sha_mismatch(self):
  g=load('gate.json');g.update({'gate_id':'G-DEPLOY','result':'PASS','evidence_level':'E1','commands':['test'],'logs':['real log'],'commit_sha':'abc','deployment_sha':'def','workflow_run_id':'123'})
  self.assertTrue(validate_gate(g))
 def test_gate_design_docpass(self):
  g=load('gate.json');g.update({'gate_id':'G-SOURCE','result':'DOC_PASS','evidence_level':'E1'})
  self.assertEqual(validate_gate(g),[])
class TestV41Mastery(unittest.TestCase):
 def setUp(self):self.p=load('progress.json')

 def test_valid_full_mastery(self):
  self.assertEqual(validate_progress(self.p),[])

 def test_single_verified_is_not_mastery(self):
  self.p['mastery_evidence']=self.p['mastery_evidence'][:1]
  self.p['access_grants']=[];self.p['mastery_estimate']='MASTERED'
  self.assertIn('PROGRESS_INVARIANT',str(validate_progress(self.p)))

 def test_missing_transfer_is_not_mastery(self):
  self.p['mastery_evidence']=[x for x in self.p['mastery_evidence'] if x['role']!='TRANSFER']
  self.p['access_grants']=[];self.assertTrue(validate_progress(self.p))

 def test_assisted_transfer_cannot_certify(self):
  self.p['mastery_evidence'][2]['assisted']=True
  self.assertTrue(validate_progress(self.p))

 def test_inconclusive_does_not_certify(self):
  self.p['mastery_evidence'][2]['oracle_result']='INCONCLUSIVE'
  self.assertTrue(validate_progress(self.p))

 def test_duplicate_idempotency_different_event(self):
  self.p['mastery_evidence'][2]['idempotency_key']='demo-idem-1'
  self.assertIn('duplicate idempotency_key',str(validate_progress(self.p)))

 def test_dangling_grant_evidence(self):
  self.p['access_grants'][0]['evidence_ids'].append('nonexistent-evidence')
  self.assertIn('unknown evidence',str(validate_progress(self.p)))

 def test_merge_commutative(self):
  a=copy.deepcopy(self.p);b=copy.deepcopy(self.p)
  a['access_grants']=[];b['mastery_evidence']=b['mastery_evidence'][1:]
  b['access_grants']=[]
  a['mastery_estimate']='MASTERED';b['mastery_estimate']='DEVELOPING'
  left=merge_progress(a,b);right=merge_progress(b,a)
  self.assertEqual(left['mastery_evidence'],right['mastery_evidence'])
  self.assertEqual(left['mastery_estimate'],right['mastery_estimate'])
  self.assertEqual(left['access_grants'],right['access_grants'])

 def test_merge_associative(self):
  parts=[]
  for e in self.p['mastery_evidence']:
   x=copy.deepcopy(self.p);x['mastery_evidence']=[e];x['access_grants']=[];x['mastery_estimate']='DEVELOPING';parts.append(x)
  l=merge_progress(merge_progress(parts[0],parts[1]),parts[2])
  r=merge_progress(parts[0],merge_progress(parts[1],parts[2]))
  self.assertEqual(l['mastery_estimate'],r['mastery_estimate'])
  self.assertEqual(l['mastery_evidence'],r['mastery_evidence'])

 def test_merge_idempotent_events(self):
  merged=merge_progress(self.p,self.p)
  self.assertEqual(len(merged['mastery_evidence']),3)
  self.assertEqual(len(merged['access_grants']),1)

 def test_review_without_revoking_access(self):
  stale=copy.deepcopy(self.p)
  stale['review_events']=[{'event_id':'review-1','review_id':'r1','kind':'OPEN'}]
  stale['mastery_estimate']='NEEDS_REVIEW'
  joined=merge_progress(self.p,stale)
  self.assertEqual(joined['mastery_estimate'],'NEEDS_REVIEW')
  self.assertEqual(joined['access_grants'],self.p['access_grants'])
  recovered=copy.deepcopy(joined)
  recovered['review_events'].append({'event_id':'review-2','review_id':'r1','kind':'RESOLVE'})
  recovered['mastery_estimate']='MASTERED'
  self.assertEqual(validate_progress(recovered),[])

 def test_stale_clock_cannot_demote(self):
  x=copy.deepcopy(self.p);x['updated_at']='2099-01-01T00:00:00Z'
  x['mastery_evidence']=[];x['access_grants']=[]
  x['mastery_estimate']='UNASSESSED'
  joined=merge_progress(x,self.p)
  self.assertEqual(joined['mastery_estimate'],'MASTERED')

 def test_route_policy_mismatch_rejected(self):
  rule=dict(self.p['mastery_rule']);rule['distinct_variant_families']=3
  self.assertIn('mismatches trusted route',str(validate_progress(self.p,rule)))

 def test_route_transfer_must_be_present_in_learning(self):
  m=load('manifest.json')
  m['activities'][0]['mode_item_ids']['learning_path'].remove('item-route-transfer')
  self.assertIn('route missing its own transfer item',str(validate_manifest(m)))

 def test_exam_requires_separate_variant(self):
  m=load('manifest.json')
  m['activities'][0]['variants']=[v for v in m['activities'][0]['variants'] if v['role']!='EXAM']
  self.assertIn('exam mode lacks independent exam variant',str(validate_manifest(m)))


if __name__=='__main__':unittest.main()
