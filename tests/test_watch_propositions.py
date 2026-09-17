import unittest

from trust_ecosystem_monitor.intelligence import analyze_snapshot
from trust_ecosystem_monitor.watches import build_watch_propositions


ABSENCE = {
    "id": "tem-propagation-absence",
    "state": "no_follow_up_observed",
    "referencing_repository": "example/source",
    "referenced_repository": "example/target",
    "relationship_id": "tem-relationship-1",
    "trigger_change_unit": "toip-change-target-1",
    "responding_change_unit": None,
    "trigger_timestamp": "2026-09-17T10:00:00Z",
    "response_timestamp": None,
    "evidence": ["https://example.test/target-change", "https://example.test/reference"],
}

FOLLOW_UP = {
    "id": "tem-propagation-follow-up",
    "state": "observed_follow_up",
    "referencing_repository": "example/source",
    "referenced_repository": "example/target",
    "relationship_id": "tem-relationship-2",
    "trigger_change_unit": "toip-change-target-1",
    "responding_change_unit": "toip-change-source-2",
    "trigger_timestamp": "2026-09-17T10:00:00Z",
    "response_timestamp": "2026-09-17T11:00:00Z",
    "evidence": ["https://example.test/target-change", "https://example.test/source-follow-up"],
}


class WatchPropositionTests(unittest.TestCase):
    def test_bounded_absence_creates_waiting_watch(self):
        watches = build_watch_propositions([ABSENCE], observed_at="2026-09-17T12:00:00Z")

        self.assertEqual(1, len(watches))
        watch = watches[0]
        self.assertEqual("waiting_external", watch["state"])
        self.assertEqual("follow_up_after_referenced_change", watch["kind"])
        self.assertEqual("example/source", watch["source_repository"])
        self.assertEqual("example/target", watch["target_repository"])
        self.assertFalse(watch["authority"]["upstream_action_authorized"])
        self.assertIn("does not establish dependency", watch["interpretation"])

    def test_insufficient_history_does_not_manufacture_watch(self):
        insufficient = dict(ABSENCE, id="tem-propagation-insufficient", state="insufficient_history")

        self.assertEqual([], build_watch_propositions([insufficient], observed_at="2026-09-17T12:00:00Z"))

    def test_watch_persists_with_stable_identity(self):
        first = build_watch_propositions([ABSENCE], observed_at="2026-09-17T12:00:00Z")[0]
        previous = {"watch_propositions": [first]}
        newer_absence = dict(
            ABSENCE,
            id="tem-propagation-absence-2",
            trigger_change_unit="toip-change-target-2",
            trigger_timestamp="2026-09-18T10:00:00Z",
            evidence=ABSENCE["evidence"] + ["https://example.test/target-change-2"],
        )

        second = build_watch_propositions(
            [newer_absence], previous=previous, observed_at="2026-09-18T12:00:00Z"
        )[0]

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["created_at"], second["created_at"])
        self.assertEqual("waiting_external", second["state"])
        self.assertEqual("toip-change-target-2", second["trigger_change_unit"])
        self.assertIn("https://example.test/target-change", second["evidence"])
        self.assertIn("https://example.test/target-change-2", second["evidence"])

    def test_follow_up_triggers_existing_watch_without_completing_it(self):
        waiting = build_watch_propositions([ABSENCE], observed_at="2026-09-17T12:00:00Z")[0]

        triggered = build_watch_propositions(
            [FOLLOW_UP], previous={"watch_propositions": [waiting]}, observed_at="2026-09-17T12:30:00Z"
        )[0]

        self.assertEqual(waiting["id"], triggered["id"])
        self.assertEqual("trigger_observed", triggered["state"])
        self.assertEqual("toip-change-source-2", triggered["response_change_unit"])
        self.assertNotEqual("completed", triggered["state"])

    def test_retained_trigger_requires_reassessment(self):
        waiting = build_watch_propositions([ABSENCE], observed_at="2026-09-17T12:00:00Z")[0]
        triggered = build_watch_propositions(
            [FOLLOW_UP], previous={"watch_propositions": [waiting]}, observed_at="2026-09-17T12:30:00Z"
        )[0]

        reassessment = build_watch_propositions(
            [], previous={"watch_propositions": [triggered]}, observed_at="2026-09-18T12:00:00Z"
        )[0]

        self.assertEqual(triggered["id"], reassessment["id"])
        self.assertEqual("reassessment_required", reassessment["state"])

    def test_same_pair_is_deduplicated_by_proposition_identity(self):
        duplicate = dict(ABSENCE, id="tem-propagation-absence-duplicate")

        watches = build_watch_propositions([ABSENCE, duplicate], observed_at="2026-09-17T12:00:00Z")

        self.assertEqual(1, len(watches))

    def test_analyze_snapshot_publishes_watch_propositions(self):
        repositories = [
            {
                "name": "source",
                "full_name": "example/source",
                "portfolio": "A",
                "lifecycle": "active",
                "url": "https://github.com/example/source",
            },
            {
                "name": "target",
                "full_name": "example/target",
                "portfolio": "B",
                "lifecycle": "active",
                "url": "https://github.com/example/target",
            },
        ]
        previous = {
            "repositories": repositories,
            "relationships": [
                {
                    "id": "tem-relationship-prior",
                    "source_repository": "example/source",
                    "target_repository": "example/target",
                    "evidence": ["https://example.test/prior-reference"],
                }
            ],
            "change_units": [],
            "watch_propositions": [],
        }
        snapshot = {
            "generated_at": "2026-09-17T12:00:00Z",
            "repositories": repositories,
            "events": [
                {
                    "repository": "example/target",
                    "portfolio": "B",
                    "repo_kind": "specification",
                    "title": "Protocol semantics update",
                    "timestamp": "2026-09-17T10:00:00Z",
                    "materiality": 5,
                    "kind": "pull_request",
                    "number": 22,
                    "url": "https://example.test/target/pull/22",
                }
            ],
        }

        result = analyze_snapshot(snapshot, previous)

        self.assertEqual("no_follow_up_observed", result["change_propagation"][0]["state"])
        self.assertEqual(1, len(result["watch_propositions"]))
        self.assertEqual("waiting_external", result["watch_propositions"][0]["state"])


if __name__ == "__main__":
    unittest.main()
