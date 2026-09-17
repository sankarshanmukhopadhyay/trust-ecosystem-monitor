import unittest

from trust_ecosystem_monitor.intelligence import (
    analyze_snapshot,
    build_relationship_graph,
    classify_semantic_change,
    consolidate_change_units,
    detect_change_propagation,
)


class SemanticChangeTests(unittest.TestCase):
    def test_classifies_authority_change_from_observed_text(self):
        unit = {
            "title": "Define delegation revocation semantics",
            "event_kinds": ["pull_request"],
            "events": [],
        }

        classification = classify_semantic_change(unit)

        self.assertEqual("authority", classification["type"])
        self.assertEqual("derived", classification["evidence_state"])
        self.assertIn("revocation", classification["matched_terms"])

    def test_unknown_remains_explicit_when_no_rule_matches(self):
        classification = classify_semantic_change(
            {"title": "Adjust frobnicator behavior", "event_kinds": ["commit"], "events": []}
        )

        self.assertEqual("unknown", classification["type"])
        self.assertEqual("insufficient", classification["evidence_state"])
        self.assertEqual("low", classification["confidence"])

    def test_change_units_carry_semantic_classification(self):
        units = consolidate_change_units(
            [
                {
                    "repository": "example/source",
                    "portfolio": "A",
                    "repo_kind": "specification",
                    "title": "OpenAPI endpoint compatibility update",
                    "timestamp": "2026-09-17T00:00:00Z",
                    "materiality": 4,
                    "kind": "pull_request",
                    "number": 7,
                    "url": "https://github.com/example/source/pull/7",
                }
            ]
        )

        self.assertEqual("api", units[0]["semantic_change"]["type"])


class RelationshipGraphTests(unittest.TestCase):
    def setUp(self):
        self.repositories = [
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

    def test_explicit_reference_creates_observed_edge_without_dependency_claim(self):
        units = consolidate_change_units(
            [
                {
                    "repository": "example/source",
                    "portfolio": "A",
                    "repo_kind": "specification",
                    "title": "Align behavior with example/target",
                    "timestamp": "2026-09-17T00:00:00Z",
                    "materiality": 4,
                    "kind": "issue",
                    "number": 4,
                    "url": "https://github.com/example/source/issues/4",
                }
            ]
        )

        relationships = build_relationship_graph(units, self.repositories)

        self.assertEqual(1, len(relationships))
        edge = relationships[0]
        self.assertEqual("observed-reference", edge["relationship_type"])
        self.assertEqual("observed", edge["claim_strength"])
        self.assertFalse(edge["formal_dependency"])
        self.assertFalse(edge["recognition_inferred"])
        self.assertFalse(edge["authority_inferred"])
        self.assertEqual("observed", edge["evidence_state"])

    def test_co_movement_without_reference_does_not_create_relationship(self):
        units = consolidate_change_units(
            [
                {
                    "repository": "example/source",
                    "portfolio": "A",
                    "repo_kind": "specification",
                    "title": "Material protocol change",
                    "timestamp": "2026-09-17T00:00:00Z",
                    "materiality": 5,
                    "kind": "pull_request",
                    "number": 8,
                    "url": "https://github.com/example/source/pull/8",
                },
                {
                    "repository": "example/target",
                    "portfolio": "B",
                    "repo_kind": "specification",
                    "title": "Material schema change",
                    "timestamp": "2026-09-17T00:01:00Z",
                    "materiality": 5,
                    "kind": "pull_request",
                    "number": 9,
                    "url": "https://github.com/example/target/pull/9",
                },
            ]
        )

        self.assertEqual([], build_relationship_graph(units, self.repositories))

    def test_analyze_snapshot_exposes_relationships_and_semantics(self):
        snapshot = {
            "repositories": self.repositories,
            "events": [
                {
                    "repository": "example/source",
                    "portfolio": "A",
                    "repo_kind": "specification",
                    "title": "Reference example/target for interoperability",
                    "timestamp": "2026-09-17T00:00:00Z",
                    "materiality": 4,
                    "kind": "issue",
                    "number": 10,
                    "url": "https://github.com/example/source/issues/10",
                }
            ],
        }

        result = analyze_snapshot(snapshot)

        self.assertEqual(1, len(result["relationships"]))
        self.assertEqual("interop", result["change_units"][0]["semantic_change"]["type"])


class ChangePropagationTests(unittest.TestCase):
    def setUp(self):
        self.repositories = [
            {"name": "source", "full_name": "example/source", "portfolio": "A", "lifecycle": "active", "url": "https://github.com/example/source"},
            {"name": "target", "full_name": "example/target", "portfolio": "B", "lifecycle": "active", "url": "https://github.com/example/target"},
        ]

    def _units(self, events):
        return consolidate_change_units(events)

    def test_later_explicit_reference_is_observed_follow_up(self):
        units = self._units([
            {
                "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                "title": "Change schema field", "timestamp": "2026-09-17T00:00:00Z", "materiality": 5,
                "kind": "pull_request", "number": 1, "url": "https://github.com/example/target/pull/1",
            },
            {
                "repository": "example/source", "portfolio": "A", "repo_kind": "specification",
                "title": "Align with example/target schema", "timestamp": "2026-09-17T01:00:00Z", "materiality": 4,
                "kind": "issue", "number": 2, "url": "https://github.com/example/source/issues/2",
            },
        ])
        relationships = build_relationship_graph(units, self.repositories)

        propagation = detect_change_propagation(units, relationships)

        observed = [item for item in propagation if item["state"] == "observed_follow_up"]
        self.assertEqual(1, len(observed))
        self.assertEqual("example/target", observed[0]["referenced_repository"])
        self.assertEqual("example/source", observed[0]["referencing_repository"])
        self.assertIsNotNone(observed[0]["trigger_change_unit"])
        self.assertIsNotNone(observed[0]["responding_change_unit"])
        self.assertIn("does not establish causation", observed[0]["interpretation"])

    def test_reference_before_target_change_is_not_response_to_later_change(self):
        units = self._units([
            {
                "repository": "example/source", "portfolio": "A", "repo_kind": "specification",
                "title": "Reference example/target", "timestamp": "2026-09-17T00:00:00Z", "materiality": 4,
                "kind": "issue", "number": 3, "url": "https://github.com/example/source/issues/3",
            },
            {
                "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                "title": "Later protocol change", "timestamp": "2026-09-17T02:00:00Z", "materiality": 5,
                "kind": "pull_request", "number": 4, "url": "https://github.com/example/target/pull/4",
            },
        ])
        relationships = build_relationship_graph(units, self.repositories)

        propagation = detect_change_propagation(units, relationships)

        self.assertFalse(any(item["state"] == "observed_follow_up" for item in propagation))
        self.assertTrue(any(item["state"] == "insufficient_history" for item in propagation))

    def test_prior_relationship_can_support_no_follow_up_observed(self):
        previous = {
            "change_units": [],
            "relationships": [
                {
                    "id": "rel-prior", "source_repository": "example/source", "target_repository": "example/target",
                    "source_change_unit": "prior-source", "evidence": ["https://github.com/example/source/issues/1"],
                }
            ],
        }
        units = self._units([
            {
                "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                "title": "New normative protocol change", "timestamp": "2026-09-17T03:00:00Z", "materiality": 5,
                "kind": "pull_request", "number": 5, "url": "https://github.com/example/target/pull/5",
            }
        ])

        propagation = detect_change_propagation(units, [], previous)

        absent = [item for item in propagation if item["state"] == "no_follow_up_observed"]
        self.assertEqual(1, len(absent))
        self.assertIsNone(absent[0]["responding_change_unit"])
        self.assertIn("not evidence that follow-up was required", absent[0]["interpretation"])

    def test_first_baseline_does_not_emit_absence_claim(self):
        units = self._units([
            {
                "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                "title": "Protocol change", "timestamp": "2026-09-17T03:00:00Z", "materiality": 5,
                "kind": "pull_request", "number": 6, "url": "https://github.com/example/target/pull/6",
            }
        ])

        propagation = detect_change_propagation(units, [], None)

        self.assertFalse(any(item["state"] == "no_follow_up_observed" for item in propagation))

    def test_previous_target_change_can_be_trigger_for_current_follow_up(self):
        previous_target = self._units([
            {
                "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                "title": "Schema revision", "timestamp": "2026-09-16T23:00:00Z", "materiality": 5,
                "kind": "pull_request", "number": 7, "url": "https://github.com/example/target/pull/7",
            }
        ])[0]
        previous = {"change_units": [previous_target], "relationships": []}
        current_units = self._units([
            {
                "repository": "example/source", "portfolio": "A", "repo_kind": "specification",
                "title": "Update for example/target schema", "timestamp": "2026-09-17T04:00:00Z", "materiality": 4,
                "kind": "pull_request", "number": 8, "url": "https://github.com/example/source/pull/8",
            }
        ])
        relationships = build_relationship_graph(current_units, self.repositories)

        propagation = detect_change_propagation(current_units, relationships, previous)

        observed = [item for item in propagation if item["state"] == "observed_follow_up"]
        self.assertEqual(1, len(observed))
        self.assertEqual(previous_target["id"], observed[0]["trigger_change_unit"])

    def test_analyze_snapshot_publishes_change_propagation(self):
        snapshot = {
            "repositories": self.repositories,
            "events": [
                {
                    "repository": "example/target", "portfolio": "B", "repo_kind": "specification",
                    "title": "Schema change", "timestamp": "2026-09-17T00:00:00Z", "materiality": 5,
                    "kind": "pull_request", "number": 9, "url": "https://github.com/example/target/pull/9",
                },
                {
                    "repository": "example/source", "portfolio": "A", "repo_kind": "specification",
                    "title": "Align example/target schema", "timestamp": "2026-09-17T01:00:00Z", "materiality": 4,
                    "kind": "issue", "number": 10, "url": "https://github.com/example/source/issues/10",
                },
            ],
        }

        result = analyze_snapshot(snapshot)

        self.assertIn("change_propagation", result)
        self.assertTrue(any(item["state"] == "observed_follow_up" for item in result["change_propagation"]))


if __name__ == "__main__":
    unittest.main()
