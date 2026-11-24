"""Safeguards for protected-main provider reconciliation proposals; offline mocks."""
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from submit_reconciliation_pr import submit, proposal_branch
from persist_reconciliation import PersistenceBlocked, ConcurrentUpdate

SHA = "a" * 40
RUN = "456"
OBS = {
    "result": "VERIFIED_OBSERVATION", "errors": [], "target_sha": SHA,
    "repository": "c2melendez/Academia_Play",
    "service_id": "srv-dc06lp67bikc739hlghg",
    "workflow_run_id": RUN, "deployment_id": "dep-test",
    "observed_at": "2026-11-24T11:00:00+00:00",
    "deployment_finished_at": "2026-11-24T10:59:00Z",
}


def checkpoint():
    return json.loads((ROOT.parents[0] / "continuity.json").read_text(encoding="utf-8"))


class SubmitReconciliationPrTests(unittest.TestCase):
    def test_branch_deterministic(self):
        self.assertEqual(proposal_branch(SHA, RUN), "p0/reconcile-" + SHA + "-" + RUN)

    def test_reject_invalid_input(self):
        with self.assertRaises(PersistenceBlocked):
            proposal_branch("bad", "not-a-run")

    def test_require_provider_tokens(self):
        with self.assertRaises(PersistenceBlocked):
            submit(SHA, RUN, None, "render")
        with self.assertRaises(PersistenceBlocked):
            submit(SHA, RUN, "github", None)

    @patch("submit_reconciliation_pr.existing_event", return_value=None)
    @patch("submit_reconciliation_pr.current_main", return_value=SHA)
    @patch("submit_reconciliation_pr.read_text_content")
    @patch("submit_reconciliation_pr.observe", return_value=OBS)
    @patch("submit_reconciliation_pr.api_request")
    def test_dry_run_never_writes(self, api, observe, read, current, exists):
        read.return_value = (json.dumps(checkpoint()), "blob")
        outcome = submit(SHA, RUN, "github", "render", dry_run=True)
        self.assertEqual(outcome["result"], "DRY_RUN")
        api.assert_not_called()

    @patch("submit_reconciliation_pr.existing_event", return_value=None)
    @patch("submit_reconciliation_pr.current_main", return_value=SHA)
    @patch("submit_reconciliation_pr.read_text_content")
    @patch("submit_reconciliation_pr.observe", return_value=OBS)
    @patch("submit_reconciliation_pr.api_request")
    def test_creates_one_branch_and_pr_without_direct_main_update(self, api, observe, read, current, exists):
        read.return_value = (json.dumps(checkpoint()), "blob")
        calls = []
        def request(method, path, token, payload=None):
            calls.append((method, path, payload))
            if method == "GET" and path.startswith("git/ref/heads/p0/"):
                raise urllib.error.HTTPError("https://api.github.com", 404, "missing", None, None)
            if path == f"git/commits/{SHA}":
                return {"tree": {"sha": "b"*40}}
            if path == "git/trees":
                return {"sha": "c"*40}
            if path == "git/commits":
                return {"sha": "d"*40}
            if path == "git/refs":
                return {"ref": "refs/heads/proposal"}
            if path == "pulls":
                return {"number": 12, "html_url": "https://github.com/c2melendez/Academia_Play/pull/12"}
            raise AssertionError(path)
        api.side_effect = request
        result = submit(SHA, RUN, "github", "render")
        self.assertEqual(result["result"], "PROPOSED_NOT_MERGED")
        self.assertEqual(result["pr_number"], 12)
        self.assertFalse(any(x[1] == "git/refs/heads/main" for x in calls))
        self.assertEqual(len([x for x in calls if x[0] == "POST" and x[1] == "git/refs"]), 1)
        pr = next(x[2] for x in calls if x[1] == "pulls")
        self.assertEqual(pr["base"], "main")

    @patch("submit_reconciliation_pr.existing_event", return_value=None)
    @patch("submit_reconciliation_pr.current_main", return_value="b"*40)
    def test_main_advance_blocks_before_provider_queries(self, current, exists):
        with self.assertRaises(ConcurrentUpdate):
            submit(SHA, RUN, "github", "render")

    @patch("submit_reconciliation_pr.existing_event", return_value={"result": "VERIFIED_OBSERVATION"})
    def test_existing_event_blocks_duplicate_pr(self, exists):
        with self.assertRaises(PersistenceBlocked):
            submit(SHA, RUN, "github", "render")

    @patch("submit_reconciliation_pr.existing_event", return_value=None)
    @patch("submit_reconciliation_pr.current_main", return_value=SHA)
    @patch("submit_reconciliation_pr.read_text_content")
    @patch("submit_reconciliation_pr.observe", return_value={**OBS, "result": "NOT_RUN"})
    def test_unverified_observation_blocks(self, observe, read, current, exists):
        read.return_value = (json.dumps(checkpoint()), "blob")
        with self.assertRaises(PersistenceBlocked):
            submit(SHA, RUN, "github", "render", dry_run=True)

    @patch("submit_reconciliation_pr.existing_event", return_value=None)
    @patch("submit_reconciliation_pr.current_main", return_value=SHA)
    @patch("submit_reconciliation_pr.read_text_content")
    @patch("submit_reconciliation_pr.observe", return_value=OBS)
    @patch("submit_reconciliation_pr.api_request")
    def test_existing_proposal_branch_blocks_overwrite(self, api, observe, read, current, exists):
        read.return_value = (json.dumps(checkpoint()), "blob")
        api.return_value = {"object": {"sha": "b"*40}}
        with self.assertRaises(PersistenceBlocked):
            submit(SHA, RUN, "github", "render")
        self.assertFalse(any(c.args[0] == "POST" for c in api.call_args_list))


if __name__ == "__main__":
    unittest.main()
