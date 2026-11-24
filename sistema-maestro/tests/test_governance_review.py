"""Independent governance approvals; synthetic inputs do not count as real approvals."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from governance_review import review_result, normative_paths, observe_pr, fetch_all_pages

SHA = "a" * 40
PR = {
    "state": "open",
    "draft": False,
    "head": {"sha": SHA},
    "base": {"ref": "main", "repo": {"full_name": "c2melendez/Academia_Play"}},
    "user": {"login": "contributor"},
}
APPROVAL = {
    "id": 1,
    "user": {"login": "c2melendez"},
    "state": "APPROVED",
    "commit_id": SHA,
    "submitted_at": "2026-11-24T00:00:00Z",
}
PATHS = ["sistema-maestro/CONSTITUCION.md"]


class GovernanceReviewTests(unittest.TestCase):
    def evaluate(self, pr=None, files=None, reviews=None):
        return review_result(pr if pr is not None else PR,
                             files if files is not None else PATHS,
                             reviews if reviews is not None else [APPROVAL])

    def test_authenticated_independent_review_matches_revision(self):
        self.assertEqual(self.evaluate()["result"], "VERIFIED_REVIEW")

    def test_unrelated_change_does_not_require_governance_review(self):
        result = self.evaluate(files=["web/index.html"], reviews=[])
        self.assertEqual(result["result"], "NOT_APPLICABLE")

    def test_sensitive_files_are_recognized(self):
        paths = normative_paths(["sistema-maestro/scripts/x.py", "infra/project_identity.json",
                                  ".github/workflows/ci.yml", "continuity.json",
                                  ".github/CODEOWNERS", "web/index.html"])
        self.assertEqual(len(paths), 5)

    def test_no_reviews_is_blocked(self):
        self.assertEqual(self.evaluate(reviews=[])["result"], "BLOCKED")

    def test_self_approval_is_not_accepted(self):
        pr = copy.deepcopy(PR)
        pr["user"]["login"] = "c2melendez"
        self.assertEqual(self.evaluate(pr=pr)["result"], "BLOCKED")

    def test_outdated_head_approval_is_not_accepted(self):
        review = dict(APPROVAL, commit_id="b"*40)
        self.assertEqual(self.evaluate(reviews=[review])["result"], "BLOCKED")

    def test_untrusted_reviewer_cannot_approve(self):
        review = copy.deepcopy(APPROVAL)
        review["user"]["login"] = "unknown"
        self.assertEqual(self.evaluate(reviews=[review])["result"], "BLOCKED")

    def test_later_dismissal_revokes_approval(self):
        dismissed = dict(APPROVAL, id=2, state="DISMISSED",
                         submitted_at="2026-11-24T01:00:00Z")
        self.assertEqual(self.evaluate(reviews=[APPROVAL, dismissed])["result"], "BLOCKED")

    def test_later_changes_requested_revokes_approval(self):
        change = dict(APPROVAL, id=2, state="CHANGES_REQUESTED",
                      submitted_at="2026-11-24T01:00:00Z")
        self.assertEqual(self.evaluate(reviews=[APPROVAL, change])["result"], "BLOCKED")

    def test_draft_pr_is_blocked(self):
        pr = dict(PR, draft=True)
        self.assertEqual(self.evaluate(pr=pr)["result"], "BLOCKED")

    def test_wrong_target_branch_is_blocked(self):
        pr = copy.deepcopy(PR)
        pr["base"]["ref"] = "elsewhere"
        self.assertEqual(self.evaluate(pr=pr)["result"], "BLOCKED")

    def test_does_not_approve_curriculum(self):
        result = self.evaluate()
        self.assertIn("not APROBAR_DISEÑO", result["note"])

    @patch("governance_review.github_json")
    def test_observe_retrieves_pr_reviews_and_files_from_github(self, fetch):
        fetch.side_effect = [PR, [{"filename": "sistema-maestro/CONSTITUCION.md"}], [APPROVAL]]
        self.assertEqual(observe_pr(8, "token")["result"], "VERIFIED_REVIEW")
        self.assertEqual(fetch.call_count, 3)

    @patch("governance_review.github_json")
    def test_empty_pagination_terminates(self, fetch):
        fetch.return_value = []
        self.assertEqual(fetch_all_pages("pulls/8/reviews", "token"), [])
        self.assertEqual(fetch.call_count, 1)

    def test_bad_pr_number_rejected(self):
        with self.assertRaises(ValueError):
            observe_pr(0, "token")


if __name__ == "__main__":
    unittest.main()
