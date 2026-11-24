"""Tests: atomic checkpoint+event, optimistic lock, idempotence and recovery."""
import copy
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from persist_reconciliation import (
    ConcurrentUpdate, PersistenceBlocked, build_change, event_paths,
    persist_verified_observation,
)

SHA = "a" * 40
RUN = "12345"
EVENT_PATH, SNAPSHOT_PATH = event_paths(SHA, RUN)
OBS = {
    "result": "VERIFIED_OBSERVATION",
    "errors": [],
    "target_sha": SHA,
    "repository": "c2melendez/Academia_Play",
    "service_id": "srv-dc06lp67bikc739hlghg",
    "workflow_run_id": RUN,
    "deployment_id": "dep-test",
    "observed_at": "2026-11-24T00:00:00+00:00",
    "deployment_finished_at": "2026-11-23T23:59:00Z",
}

def checkpoint():
    return json.loads((ROOT.parents[0] / "continuity.json").read_text(encoding="utf-8"))


class ReconciliationUnitTests(unittest.TestCase):
    def test_atomic_bundle_contains_event_checkpoint_and_observation(self):
        original = checkpoint()
        baseline = copy.deepcopy(original)
        change = build_change(original, OBS, RUN)
        self.assertEqual(set(change), {"continuity.json", EVENT_PATH, SNAPSHOT_PATH})
        self.assertEqual(original, baseline)
        data = json.loads(change["continuity.json"])
        self.assertEqual(data["repo_head_sha"], SHA)
        self.assertEqual(data["qa_ci_verified_sha"], SHA)
        self.assertEqual(data["last_verified_deploy_sha"], SHA)
        self.assertEqual(data["last_verified_deploy_at"], OBS["deployment_finished_at"])
        self.assertEqual(data["course_design_status"], original["course_design_status"])
        self.assertEqual(data["approved_design_revision"], original["approved_design_revision"])
        self.assertEqual(data["module_states"], original["module_states"])
        self.assertEqual(data["next_action"], original["next_action"])
        event = json.loads(change[EVENT_PATH])
        self.assertEqual(event["result"], "VERIFIED_OBSERVATION")
        self.assertEqual(event["repo_sha"], SHA)

    def test_missing_deploy_time_does_not_invent_it(self):
        obs = {**OBS, "deployment_finished_at": None}
        data = json.loads(build_change(checkpoint(), obs, RUN)["continuity.json"])
        self.assertIsNone(data["last_verified_deploy_at"])

    def test_nonverified_observation_fails(self):
        with self.assertRaises(PersistenceBlocked):
            build_change(checkpoint(), {**OBS, "result": "NOT_RUN"}, RUN)

    def test_wrong_service_fails(self):
        with self.assertRaises(PersistenceBlocked):
            build_change(checkpoint(), {**OBS, "service_id": "other"}, RUN)

    def test_wrong_run_fails(self):
        with self.assertRaises(PersistenceBlocked):
            build_change(checkpoint(), {**OBS, "workflow_run_id": "99"}, RUN)

    def test_no_deploy_id_fails(self):
        with self.assertRaises(PersistenceBlocked):
            build_change(checkpoint(), {**OBS, "deployment_id": None}, RUN)

    def test_invalid_ids_fail(self):
        with self.assertRaises(PersistenceBlocked):
            event_paths("../evil", "x")

    @patch("persist_reconciliation.existing_event", return_value=None)
    @patch("persist_reconciliation.read_text_content")
    @patch("persist_reconciliation.observe", return_value=OBS)
    @patch("persist_reconciliation.api_request")
    def test_success_is_single_atomic_tree_commit(self, api, observe, contents, event):
        calls = []
        def respond(method, path, token, payload=None):
            calls.append((method, path, payload))
            if path == "git/ref/heads/main":
                return {"object": {"sha": SHA}}
            if path == f"git/commits/{SHA}":
                return {"tree": {"sha": "tree-old"}}
            if path == "git/trees":
                return {"sha": "tree-new"}
            if path == "git/commits":
                return {"sha": "b" * 40}
            if path == "git/refs/heads/main":
                return {"ref": "refs/heads/main"}
            raise AssertionError(f"Unexpected {method} {path}")
        api.side_effect = respond
        contents.return_value = (json.dumps(checkpoint()), "content-blob-sha")
        result = persist_verified_observation(SHA, RUN, "read-write", "read-only")
        self.assertEqual(result["result"], "RECORDED")
        trees = [c for c in calls if c[1] == "git/trees"]
        self.assertEqual(len(trees), 1)
        self.assertEqual(len(trees[0][2]["tree"]), 3)
        update = [c for c in calls if c[1] == "git/refs/heads/main"]
        self.assertEqual(len(update), 1)
        self.assertIs(update[0][2]["force"], False)
        self.assertEqual(observe.call_count, 1)

    @patch("persist_reconciliation.existing_event")
    @patch("persist_reconciliation.api_request")
    def test_replay_reuses_event_without_writing(self, api, event):
        event.return_value = {"event_id": f"RECONCILIAR-{SHA}-{RUN}",
                              "repo_sha": SHA, "result": "VERIFIED_OBSERVATION"}
        result = persist_verified_observation(SHA, RUN, "token", "token")
        self.assertEqual(result["result"], "ALREADY_RECORDED")
        api.assert_not_called()

    @patch("persist_reconciliation.existing_event", return_value={"result": "NOT_RUN"})
    def test_collision_refuses_overwrite(self, event):
        with self.assertRaises(PersistenceBlocked):
            persist_verified_observation(SHA, RUN, "token", "token")

    @patch("persist_reconciliation.existing_event", return_value=None)
    @patch("persist_reconciliation.api_request")
    def test_stale_head_aborts_before_observation(self, api, event):
        api.return_value = {"object": {"sha": "c" * 40}}
        with self.assertRaises(ConcurrentUpdate):
            persist_verified_observation(SHA, RUN, "token", "token")
        self.assertEqual(api.call_count, 1)

    @patch("persist_reconciliation.existing_event", return_value=None)
    @patch("persist_reconciliation.read_text_content")
    @patch("persist_reconciliation.observe", return_value=OBS)
    @patch("persist_reconciliation.api_request")
    def test_concurrent_head_advance_aborts_before_write(self, api, observe, contents, event):
        heads = iter([SHA, "c" * 40])
        api.side_effect = lambda method, path, token, payload=None: {
            "object": {"sha": next(heads)}
        }
        contents.return_value = (json.dumps(checkpoint()), "blob-sha")
        with self.assertRaises(ConcurrentUpdate):
            persist_verified_observation(SHA, RUN, "token", "token")
        self.assertEqual(api.call_count, 2)

    @patch("persist_reconciliation.existing_event", return_value=None)
    @patch("persist_reconciliation.read_text_content")
    @patch("persist_reconciliation.observe", return_value=OBS)
    @patch("persist_reconciliation.api_request")
    def test_dry_run_writes_nothing(self, api, observe, contents, event):
        api.return_value = {"object": {"sha": SHA}}
        contents.return_value = (json.dumps(checkpoint()), "blob-sha")
        result = persist_verified_observation(SHA, RUN, "token", "token", dry_run=True)
        self.assertEqual(result["result"], "DRY_RUN")
        self.assertTrue(all(c.args[0] == "GET" for c in api.call_args_list))

    @patch("persist_reconciliation.existing_event", return_value=None)
    @patch("persist_reconciliation.read_text_content")
    @patch("persist_reconciliation.observe", return_value=OBS)
    @patch("persist_reconciliation.api_request")
    def test_protected_or_concurrent_ref_update_is_blocked(self, api, observe, contents, event):
        def respond(method, path, token, payload=None):
            if path == "git/ref/heads/main":
                return {"object": {"sha": SHA}}
            if path == f"git/commits/{SHA}":
                return {"tree": {"sha": "tree-old"}}
            if path == "git/trees":
                return {"sha": "tree-new"}
            if path == "git/commits":
                return {"sha": "b" * 40}
            if path == "git/refs/heads/main":
                raise urllib.error.HTTPError("https://api.github.com", 422, "protected", None, None)
            raise AssertionError(path)
        api.side_effect = respond
        contents.return_value = (json.dumps(checkpoint()), "blob-sha")
        with self.assertRaises(ConcurrentUpdate):
            persist_verified_observation(SHA, RUN, "token", "token")


if __name__ == "__main__":
    unittest.main()
