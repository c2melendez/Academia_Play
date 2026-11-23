import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reconcile_observation import differences

SHA = "a" * 40

class ReconcileObservationTests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = json.loads((ROOT.parents[0] / "continuity.json").read_text(encoding="utf-8"))
        self.observation = {
            "result": "VERIFIED_OBSERVATION",
            "repository": "c2melendez/Academia_Play",
            "service_id": "srv-dc06lp67bikc739hlghg",
            "target_sha": SHA,
            "observed_at": "2026-11-23T18:00:00+00:00",
        }

    def test_stale_checkpoint_reported_not_overwritten(self):
        original = json.dumps(self.checkpoint, sort_keys=True)
        result = differences(self.checkpoint, self.observation)
        self.assertEqual(result["status"], "STALE")
        self.assertTrue(any(row["field"] == "repo_head_sha" for row in result["differences"]))
        self.assertEqual(json.dumps(self.checkpoint, sort_keys=True), original)

    def test_reject_unverified_observation(self):
        self.observation["result"] = "NOT_RUN"
        self.assertEqual(differences(self.checkpoint, self.observation)["status"], "BLOCKED")

    def test_reject_wrong_service(self):
        self.observation["service_id"] = "other"
        self.assertEqual(differences(self.checkpoint, self.observation)["status"], "BLOCKED")

    def test_consistent_observation(self):
        self.checkpoint.update({
            "repo_head_sha": SHA,
            "qa_ci_verified_sha": SHA,
            "last_verified_deploy_sha": SHA,
            "last_observed_at": self.observation["observed_at"],
            "active_branch": "main"
        })
        self.assertEqual(differences(self.checkpoint, self.observation)["status"], "CONSISTENT")


if __name__ == "__main__":
    unittest.main()
