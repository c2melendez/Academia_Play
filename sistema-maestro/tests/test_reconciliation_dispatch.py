"""P0: fail-closed static controls for manual authenticated dry-run workflow."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0-reconciliation-dryrun.yml"

class ReconciliationDispatchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_dispatch_only_and_no_schedule(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("schedule:", self.workflow)
        self.assertNotIn("push:", self.workflow)

    def test_read_only_github_permissions(self):
        self.assertIn("contents: read", self.workflow)
        self.assertIn("actions: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)

    def test_requires_main_and_render_secret(self):
        self.assertIn('refs/heads/main', self.workflow)
        self.assertIn('secrets.RENDER_API_KEY', self.workflow)
        self.assertIn('repository secret is missing', self.workflow)

    def test_validator_dependencies_installed_before_execution(self):
        install = self.workflow.index("python -m pip install -r sistema-maestro/requirements-dev.txt")
        execute = self.workflow.index("python sistema-maestro/scripts/submit_reconciliation_pr.py")
        self.assertLess(install, execute)

    def test_dry_run_only(self):
        self.assertIn("submit_reconciliation_pr.py", self.workflow)
        self.assertIn("--dry-run", self.workflow)
        self.assertNotIn("git push", self.workflow)
        self.assertNotIn("gh pr create", self.workflow)

if __name__ == "__main__":
    unittest.main()
