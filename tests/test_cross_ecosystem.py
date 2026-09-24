import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.cross_ecosystem import derive_relationships, render, validate_registry


class CrossEcosystemTests(unittest.TestCase):
    def test_grade_c_cannot_be_accepted(self):
        payload = {
            "schema_version": "1",
            "relationships": [{
                "id": "x",
                "source": {"ecosystem": "a", "repository": "a/r", "artifact": "A"},
                "target": {"ecosystem": "b", "repository": "b/r", "artifact": "B"},
                "type": "semantic_overlap",
                "direction": "undirected",
                "evidence_grade": "C",
                "state": "accepted",
                "evidence": ["https://example.test/evidence"],
            }],
        }
        self.assertTrue(any("Grade C" in error for error in validate_registry(payload)))

    def test_render_preserves_candidate_boundary_and_observation_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "relationships").mkdir()
            registry = {
                "schema_version": "1",
                "relationships": [
                    {
                        "id": "accepted",
                        "source": {"ecosystem": "a", "repository": "org-a/source", "artifact": "Source"},
                        "target": {"ecosystem": "b", "repository": "org-b/target", "artifact": "Target"},
                        "type": "implements",
                        "direction": "source_to_target",
                        "evidence_grade": "A",
                        "state": "accepted",
                        "rationale": "Explicit implementation evidence.",
                        "evidence": ["https://example.test/a"],
                    },
                    {
                        "id": "candidate",
                        "source": {"ecosystem": "a", "repository": "org-a/source", "artifact": "Source"},
                        "target": {"ecosystem": "b", "repository": "org-b/other", "artifact": "Other"},
                        "type": "semantic_overlap",
                        "direction": "undirected",
                        "evidence_grade": "C",
                        "state": "candidate",
                        "rationale": "Discovery signal only.",
                        "evidence": ["https://example.test/c"],
                    },
                ],
            }
            (root / "relationships" / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
            for ecosystem, repo in (("a", "org-a/source"), ("b", "org-b/target")):
                path = root / "docs" / ecosystem / "data"
                path.mkdir(parents=True)
                (path / "latest.json").write_text(json.dumps({
                    "generated_at": "2026-09-24T00:00:00+00:00",
                    "ecosystem_profile": {"id": ecosystem},
                    "repositories": [{"full_name": repo, "lifecycle": "active", "portfolio": "P", "url": "https://example.test/repo"}],
                }), encoding="utf-8")

            result = derive_relationships(root)
            self.assertEqual(result["counts"]["established"], 1)
            self.assertEqual(result["counts"]["candidate"], 1)
            self.assertTrue(result["relationships"][0]["observation"]["source_observed"])
            self.assertTrue(result["relationships"][0]["observation"]["target_observed"])
            self.assertFalse(result["relationships"][1]["observation"]["target_observed"])

            render(root)
            self.assertTrue((root / "docs" / "relationships.html").exists())
            published = json.loads((root / "docs" / "data" / "relationships.json").read_text())
            self.assertEqual(published["relationships"][1]["publication_state"], "candidate")


if __name__ == "__main__":
    unittest.main()
