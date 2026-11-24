"""Negative/provider-contract tests for P0; no network calls or credentials."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from provider_evidence import verify_observations, observe, REPOSITORY, SERVICE_ID

SHA = "a" * 40
RUN = {
    "status": "completed", "conclusion": "success", "head_sha": SHA,
    "repository": {"full_name": REPOSITORY}, "html_url": "https://github.com/example/actions/1",
    "workflow_id": 425123083, "path": ".github/workflows/academia-play-contracts.yml",
    "event": "push", "head_branch": "main"
}
REPO = {"full_name": REPOSITORY, "default_branch": "main"}
SERVICE = {"id": SERVICE_ID, "repo": f"https://github.com/{REPOSITORY}", "branch": "main"}
DEPLOYS = [{"deploy": {"id": "dep-demo", "status": "live", "commit": {"id": SHA}}}]


class ProviderEvidenceTests(unittest.TestCase):
    def verify(self, repo=None, run=None, service=None, deploys=None):
        return verify_observations(SHA, REPO if repo is None else repo,
                                   RUN if run is None else run,
                                   SERVICE if service is None else service,
                                   DEPLOYS if deploys is None else deploys)

    def test_valid_compatible_observations(self):
        self.assertEqual(self.verify(), [])

    def test_ci_failure_is_rejected(self):
        run = {**RUN, "conclusion": "failure"}
        self.assertIn("not completed successfully", " ".join(self.verify(run=run)))

    def test_wrong_ci_sha_is_rejected(self):
        self.assertIn("workflow SHA mismatch", " ".join(self.verify(run={**RUN, "head_sha": "b"*40})))

    def test_wrong_repo_is_rejected(self):
        self.assertIn("repository identity", " ".join(self.verify(repo={**REPO, "full_name": "evil/repo"})))

    def test_workflow_repo_is_rejected(self):
        bad = {**RUN, "repository": {"full_name": "evil/repo"}}
        self.assertIn("workflow repository identity", " ".join(self.verify(run=bad)))

    def test_unrelated_workflow_cannot_certify_contracts(self):
        bad = {**RUN, "workflow_id": 999999}
        self.assertIn("not the canonical contracts workflow", " ".join(self.verify(run=bad)))

    def test_wrong_workflow_path_cannot_certify_contracts(self):
        bad = {**RUN, "path": ".github/workflows/unrelated.yml"}
        self.assertIn("not the canonical contracts workflow", " ".join(self.verify(run=bad)))

    def test_pr_event_cannot_certify_deployed_main(self):
        bad = {**RUN, "event": "pull_request"}
        self.assertIn("must be a push on main", " ".join(self.verify(run=bad)))

    def test_other_branch_cannot_certify_main(self):
        bad = {**RUN, "head_branch": "feature"}
        self.assertIn("must be a push on main", " ".join(self.verify(run=bad)))

    def test_missing_workflow_identity_is_rejected(self):
        bad = {key: value for key, value in RUN.items() if key != "workflow_id"}
        self.assertIn("not the canonical contracts workflow", " ".join(self.verify(run=bad)))

    def test_wrong_render_service_is_rejected(self):
        self.assertIn("service identity mismatch", " ".join(self.verify(service={**SERVICE, "id": "other"})))

    def test_render_not_live_is_rejected(self):
        deployments = copy.deepcopy(DEPLOYS)
        deployments[0]["deploy"]["status"] = "build_failed"
        self.assertIn("not live", " ".join(self.verify(deploys=deployments)))

    def test_render_stale_sha_is_rejected(self):
        deployments = copy.deepcopy(DEPLOYS)
        deployments[0]["deploy"]["commit"]["id"] = "b"*40
        self.assertIn("deployment SHA mismatch", " ".join(self.verify(deploys=deployments)))

    def test_no_deployments_is_rejected(self):
        self.assertIn("No Render deployments", " ".join(self.verify(deploys=[])))

    def test_latest_deploy_must_match_even_if_older_is_live(self):
        deployments = copy.deepcopy(DEPLOYS)
        deployments.insert(0, {"deploy": {"id": "new", "status": "build_failed",
                                            "commit": {"id": "b"*40}}})
        self.assertIn("not live", " ".join(self.verify(deploys=deployments)))

    def test_invalid_sha_is_rejected_before_network(self):
        with self.assertRaises(ValueError):
            observe("short", "123", "token", "token")

    def test_missing_token_rejected(self):
        from provider_evidence import get_json
        with self.assertRaisesRegex(ValueError, "credential"):
            get_json("https://api.github.com", None)

    @patch("provider_evidence.get_json")
    def test_observe_collects_facts_but_does_not_claim_gate_pass(self, request):
        request.side_effect = [REPO, RUN, SERVICE, DEPLOYS]
        result = observe(SHA, "1", "gh-token", "render-token")
        self.assertEqual(result["result"], "VERIFIED_OBSERVATION")
        self.assertNotEqual(result["result"], "PASS")
        self.assertEqual(result["deployment_id"], "dep-demo")
        self.assertEqual(request.call_count, 4)


if __name__ == "__main__":
    unittest.main()
