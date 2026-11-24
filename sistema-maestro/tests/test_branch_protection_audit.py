"""Ruleset audit is deliberately fail-closed and does not modify GitHub."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from branch_protection_audit import audit_rulesets, rule_targets_main, observe

RULESET = {
    "id": 9,
    "target": "branch",
    "enforcement": "active",
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "bypass_actors": [],
    "rules": [
        {"type": "pull_request", "parameters": {
            "required_approving_review_count": 1,
            "require_code_owner_review": True,
            "dismiss_stale_reviews_on_push": True,
        }},
        {"type": "required_status_checks", "parameters": {
            "required_status_checks": [{"context": "contracts"}]
        }},
    ],
}


class BranchProtectionTests(unittest.TestCase):
    def audit(self, r=None, reviewers=("owner", "independent")):
        return audit_rulesets([RULESET if r is None else r], effective_actors=reviewers)

    def test_complete_policy_passes_structural_check(self):
        self.assertEqual(self.audit()["status"], "VERIFIED")

    def test_no_rulesets_cannot_pass(self):
        self.assertEqual(audit_rulesets([], effective_actors=["a", "b"])["status"], "BLOCKED")

    def test_evaluate_only_active_main_ruleset(self):
        policy = copy.deepcopy(RULESET)
        policy["enforcement"] = "evaluate"
        self.assertFalse(rule_targets_main(policy))
        self.assertEqual(self.audit(policy)["status"], "BLOCKED")

    def test_unrelated_branch_rejected(self):
        policy = copy.deepcopy(RULESET)
        policy["conditions"]["ref_name"]["include"] = ["refs/heads/develop"]
        self.assertEqual(self.audit(policy)["status"], "BLOCKED")

    def test_bypass_fails_closed(self):
        policy = copy.deepcopy(RULESET)
        policy["bypass_actors"] = [{"actor_id": 1, "actor_type": "RepositoryRole"}]
        self.assertIn("bypass", " ".join(self.audit(policy)["errors"]))

    def test_no_independent_reviewer_capacity(self):
        self.assertEqual(self.audit(reviewers=("owner",))["status"], "BLOCKED")
        self.assertEqual(audit_rulesets([RULESET])["status"], "BLOCKED")

    def test_missing_codeowners_review_fails(self):
        policy = copy.deepcopy(RULESET)
        policy["rules"][0]["parameters"]["require_code_owner_review"] = False
        self.assertEqual(self.audit(policy)["status"], "BLOCKED")

    def test_stale_review_dismissal_missing_fails(self):
        policy = copy.deepcopy(RULESET)
        policy["rules"][0]["parameters"]["dismiss_stale_reviews_on_push"] = False
        self.assertEqual(self.audit(policy)["status"], "BLOCKED")

    def test_missing_required_ci_fails(self):
        policy = copy.deepcopy(RULESET)
        policy["rules"][1]["parameters"]["required_status_checks"] = []
        self.assertEqual(self.audit(policy)["status"], "BLOCKED")

    def test_wrong_default_branch_fails(self):
        self.assertEqual(audit_rulesets([RULESET], default_branch="dev",
                                        effective_actors=["owner", "reviewer"])["status"], "BLOCKED")

    @patch("branch_protection_audit.fetch_json")
    def test_observe_fetches_details_not_only_summary(self, fetch):
        fetch.side_effect = [
            {"default_branch": "main"},
            [{"id": 9}],
            RULESET,
        ]
        r = observe("token", verified_human_reviewers=["owner", "reviewer"])
        self.assertEqual(r["status"], "VERIFIED")
        self.assertEqual(fetch.call_count, 3)

    @patch("branch_protection_audit.fetch_json")
    def test_empty_real_policy_is_blocked(self, fetch):
        fetch.side_effect = [{"default_branch": "main"}, []]
        self.assertEqual(observe("token")["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
