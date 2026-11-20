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
  self.assertTrue(errors,f'Expected failure: {msg}')
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
  self.assertEqual(merged['mastery_estimate'],'NEEDS_REVIEW')
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
if __name__=='__main__':unittest.main()
