import unittest

from trust_ecosystem_monitor.intelligence import (
    analyze_snapshot,
    build_relationship_graph,
    classify_semantic_change,
    consolidate_change_units,
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


if __name__ == "__main__":
    unittest.main()
