import base64
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"sistema-maestro/scripts"))
from branch_continuity import audit,CONTRACTS,REPOSITORY
A="a"*40
B="b"*40
class BranchContinuityTests(unittest.TestCase):
    def setUp(self):
        self.cp=json.loads((ROOT/"continuity.json").read_text())
        self.cp.update(active_branch="main",repo_head_sha=A,qa_ci_verified_sha=A)
        self.behind=0
        self.moved=False
        self.reads=0
        self.runs=[]
        self.run_count=None
    def get(self,path):
        if path=="git/ref/heads/main":
            self.reads+=1
            return {"object":{"sha":"c"*40 if self.moved and self.reads>1 else A}}
        if path=="git/ref/heads/curriculum/mm110": return {"object":{"sha":B}}
        if path.startswith("compare/"):
            return {"ahead_by":197,"behind_by":self.behind,"base_commit":{"sha":A},"merge_base_commit":{"sha":A}}
        if path.startswith("contents/"):
            return {"encoding":"base64","content":base64.b64encode(json.dumps(self.cp).encode()).decode()}
        if path.startswith("actions/runs?"):
            return {"total_count":len(self.runs) if self.run_count is None else self.run_count,"workflow_runs":self.runs}
        raise AssertionError(path)
    def test_aligned_history_distinct_checkpoints(self):
        result=audit(self.get)
        self.assertEqual("CURRICULUM_CONTAINS_MAIN",result["status"])
        self.assertEqual("CURRENT_POINTER",result["branches"][0]["checkpoint_state"])
        self.assertEqual("HISTORICAL_OR_STALE_POINTER",result["branches"][1]["checkpoint_state"])
        self.assertFalse(result["certification_transfer"])
    def test_one_missing_main_commit(self):
        self.behind=1
        self.assertEqual("RECONCILE_REQUIRED",audit(self.get)["status"])
    def test_moving_head_not_certified(self):
        self.moved=True
        self.assertEqual("INCONCLUSIVE",audit(self.get)["status"])
    def test_pr_success_not_exact_checkout(self):
        self.runs=[{"id":1,"head_sha":B,"head_branch":"curriculum/mm110","path":CONTRACTS,"event":"pull_request","repository":{"full_name":REPOSITORY},"status":"completed","conclusion":"success","created_at":"2026-11-27T00:00:00Z"}]
        self.assertEqual("PR_RESULT_REQUIRES_CHECKOUT_VERIFICATION",audit(self.get)["branches"][1]["runs"][0]["state"])
    def test_latest_failure_not_hidden(self):
        old={"id":1,"head_sha":B,"head_branch":"curriculum/mm110","path":CONTRACTS,"event":"pull_request","repository":{"full_name":REPOSITORY},"status":"completed","conclusion":"success","created_at":"2026-11-27T00:00:00Z"}
        self.runs=[old,dict(old,id=2,conclusion="failure")]
        self.assertEqual("FAILED_OR_NON_SUCCESS",audit(self.get)["branches"][1]["runs"][0]["state"])
    def test_incomplete_run_page_rejected(self):
        self.run_count=101
        with self.assertRaises(ValueError): audit(self.get)
    def test_foreign_checkpoint_rejected(self):
        self.cp["repository_full_name"]="other/repo"
        with self.assertRaises(ValueError): audit(self.get)
