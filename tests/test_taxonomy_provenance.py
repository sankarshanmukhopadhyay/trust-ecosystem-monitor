from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.engine import configure_core, _normalize_project_identity
from trust_ecosystem_monitor import core_backend as core
from trust_ecosystem_monitor.profile import classify_portfolio_details, load_profile
from trust_ecosystem_monitor.site import render_catalog


class TaxonomyProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dif = load_profile("organizations/decentralized-identity/profile.toml")
        self.toip = load_profile("organizations/trustoverip/profile.toml")

    def test_override_precedes_pattern_rules(self) -> None:
        detail = classify_portfolio_details("credential-schemas", self.dif)
        self.assertEqual(detail["portfolio"], "Claims & Credentials")
        self.assertEqual(detail["method"], "override")
        self.assertEqual(detail["rule"], "credential-schemas")

    def test_toip_admin_repositories_are_explicit_overrides(self) -> None:
        repositories = (
            "EasyCLA",
            "iso-template",
            "logo-assets",
            "mega",
            "mkdocs-material",
            "next-deliverable-num",
            "PDF-Deliverable-Review",
            "SC",
            "specification-template",
        )
        for repository in repositories:
            with self.subTest(repository=repository):
                detail = classify_portfolio_details(repository, self.toip)
                self.assertEqual(detail["portfolio"], "Admin-Governance")
                self.assertEqual(detail["method"], "override")
                self.assertEqual(detail["rule"], repository.lower())

    def test_creator_assertions_rule(self) -> None:
        detail = classify_portfolio_details("cawg-identity-assertion", self.dif)
        self.assertEqual(detail["portfolio"], "Creator Assertions")
        self.assertEqual(detail["method"], "rule")

    def test_unclassified_remains_explicit(self) -> None:
        detail = classify_portfolio_details("aries-rfcs", self.dif)
        self.assertEqual(detail["portfolio"], "Unclassified")
        self.assertEqual(detail["method"], "unclassified")

    def test_runtime_classification_matches_profile(self) -> None:
        configure_core(self.dif)
        record = core.repo_record(
            {
                "id": 1,
                "name": "delegated-authority-report",
                "full_name": "decentralized-identity/delegated-authority-report",
                "html_url": "https://github.com/decentralized-identity/delegated-authority-report",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-08-25T00:00:00Z",
                "pushed_at": "2026-08-25T00:00:00Z",
                "archived": False,
                "fork": False,
                "default_branch": "main",
            },
            core.datetime(2026, 8, 25, tzinfo=core.timezone.utc),
        )
        self.assertEqual(record["portfolio"], "Trusted AI Agents")

    def test_snapshot_gets_classification_provenance(self) -> None:
        snapshot = {
            "repositories": [
                {"name": "credential-schemas", "full_name": "decentralized-identity/credential-schemas", "portfolio": "Claims & Credentials"},
                {"name": "aries-rfcs", "full_name": "decentralized-identity/aries-rfcs", "portfolio": "Unclassified"},
            ],
            "events": [], "change_units": [], "lifecycle_changes": [], "assertions": [], "findings": [],
            "provenance": {},
        }
        _normalize_project_identity(snapshot, self.dif)
        self.assertEqual(snapshot["repositories"][0]["classification"]["method"], "override")
        self.assertEqual(snapshot["repositories"][1]["classification"]["method"], "unclassified")

    def test_catalog_separates_taxonomy_from_substantive_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "docs" / "demo" / "data"
            target.mkdir(parents=True)
            snapshot = {
                "organization": "example",
                "generated_at": "2026-08-25T12:00:00+00:00",
                "provenance": {"previous_snapshot": None},
                "ecosystem_profile": {"id": "demo", "display_name": "Demo"},
                "repositories": [{"lifecycle": "active", "portfolio": "Unclassified"}],
                "change_units": [{"materiality": 4}],
                "findings": [
                    {"status": "open", "category": "classification", "materiality": 2, "urgency": 2},
                    {"status": "open", "category": "material-change", "materiality": 5, "urgency": 2},
                ],
            }
            (target / "latest.json").write_text(json.dumps(snapshot), encoding="utf-8")
            render_catalog(root)
            manifest = json.loads((root / "docs" / "ecosystems.json").read_text(encoding="utf-8"))
            card = manifest["ecosystems"][0]
            self.assertEqual(card["taxonomy_review"], 1)
            self.assertEqual(card["substantive_open"], 1)
            self.assertEqual(card["priority_findings"], 1)
            self.assertEqual(card["material_changes"], 1)
            self.assertEqual(card["observation_state"], "first baseline")


if __name__ == "__main__":
    unittest.main()
