import json
import tempfile
import unittest
from pathlib import Path

from toip_monitor.site import render_site


class SiteTests(unittest.TestCase):
    def test_site_renders_decision_and_evidence_pages(self):
        snapshot = {
            "generated_at": "2026-08-25T03:00:00+00:00",
            "period": {"since": "2026-08-18T03:00:00+00:00", "until": "2026-08-25T03:00:00+00:00"},
            "provenance": {"source": "test"},
            "repositories": [{"name": "dtgwg-zkp-tf", "full_name": "trustoverip/dtgwg-zkp-tf", "url": "https://example.test/repo", "description": "test", "portfolio": "DTG", "kind": "task-force", "lifecycle": "active"}],
            "events": [{"timestamp": "2026-08-25T01:00:00Z", "portfolio": "DTG", "repository": "trustoverip/dtgwg-zkp-tf", "kind": "commit", "state": None, "url": "https://example.test/event", "title": "Update requirements"}],
            "change_units": [{"portfolio": "DTG", "repository": "trustoverip/dtgwg-zkp-tf", "title": "Update requirements", "materiality": 4, "evidence": ["https://example.test/event"]}],
            "findings": [{"id": "f1", "status": "open", "category": "material-change", "subject": "trustoverip/dtgwg-zkp-tf", "summary": "Update requirements", "materiality": 4, "urgency": 2, "assurance_impact": 2, "evidence": ["https://example.test/event"]}],
            "lifecycle_changes": [],
            "cross_portfolio_seams": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "data").mkdir(parents=True)
            (root / "docs" / "data" / "latest.json").write_text(json.dumps(snapshot), encoding="utf-8")
            render_site(root)
            for name in ("index.html", "findings.html", "portfolios.html", "lifecycle.html", "seams.html", "evidence.html", "methodology.html"):
                self.assertTrue((root / "docs" / name).exists(), name)
            overview = (root / "docs" / "index.html").read_text(encoding="utf-8")
            self.assertIn("What needs attention", overview)
            self.assertIn("Update requirements", overview)

    def test_tooling_observation_is_visible_but_not_counted_as_review_seam(self):
        snapshot = {
            "generated_at": "2026-09-07T03:00:00+00:00",
            "period": {"since": "2026-08-31T03:00:00+00:00", "until": "2026-09-07T03:00:00+00:00"},
            "provenance": {"source": "test"},
            "repositories": [],
            "events": [],
            "change_units": [],
            "findings": [],
            "lifecycle_changes": [],
            "cross_portfolio_seams": [
                {
                    "id": "s1",
                    "strength": "explicit-reference",
                    "relationship_class": "tooling-publication",
                    "review_materiality": "low",
                    "review_required": False,
                    "source_portfolio": "DTG",
                    "target_portfolio": "TSWG",
                    "source_repository": "trustoverip/dtgwg-cred-spec",
                    "target_repository": "trustoverip/spec-up-t",
                    "summary": "Tooling/publication evidence only.",
                    "materiality": 1,
                    "evidence": ["https://example.test/spec-up-t"],
                },
                {
                    "id": "s2",
                    "strength": "explicit-reference",
                    "relationship_class": "cross-portfolio",
                    "review_materiality": "derived",
                    "review_required": True,
                    "source_portfolio": "DTG",
                    "target_portfolio": "TSWG",
                    "source_repository": "trustoverip/dtgwg-cred-spec",
                    "target_repository": "trustoverip/tswg-tsp-specification",
                    "summary": "Material cross-portfolio reference.",
                    "materiality": 4,
                    "evidence": ["https://example.test/material"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "data").mkdir(parents=True)
            (root / "docs" / "data" / "latest.json").write_text(json.dumps(snapshot), encoding="utf-8")
            render_site(root)
            overview = (root / "docs" / "index.html").read_text(encoding="utf-8")
            seams = (root / "docs" / "seams.html").read_text(encoding="utf-8")
            manifest = json.loads((root / "docs" / "data" / "site-manifest.json").read_text(encoding="utf-8"))
            self.assertIn("<strong>1</strong><span>review seams</span>", overview)
            self.assertIn("1</strong> tooling/publication observations", overview)
            self.assertIn("Tooling / publication observations", seams)
            self.assertIn("trustoverip/spec-up-t", seams)
            self.assertEqual(manifest["counts"]["cross_portfolio_seams"], 1)
            self.assertEqual(manifest["counts"]["tooling_publication_observations"], 1)


if __name__ == "__main__":
    unittest.main()
