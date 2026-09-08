import json
import unittest
from pathlib import Path

from trust_ecosystem_monitor import core
from trust_ecosystem_monitor.engine import configure_core
from trust_ecosystem_monitor.profile import DEFAULT_PROFILE_PATH, classify_portfolio, load_profile


class TrustOverIPProfileCompatibilityTests(unittest.TestCase):
    INTENTIONAL_CLASSIFICATION_MIGRATIONS = {
        "EasyCLA": ("Unclassified", "Admin-Governance"),
        "iso-template": ("Unclassified", "Admin-Governance"),
        "logo-assets": ("Unclassified", "Admin-Governance"),
        "mega": ("Unclassified", "Admin-Governance"),
        "mkdocs-material": ("Unclassified", "Admin-Governance"),
        "next-deliverable-num": ("Unclassified", "Admin-Governance"),
        "PDF-Deliverable-Review": ("Unclassified", "Admin-Governance"),
        "SC": ("Unclassified", "Admin-Governance"),
        "specification-template": ("Unclassified", "Admin-Governance"),
    }

    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(DEFAULT_PROFILE_PATH)

    def test_default_profile_identity_is_trustoverip(self):
        self.assertEqual(self.profile.id, "trustoverip")
        self.assertEqual(self.profile.organization, "trustoverip")
        self.assertEqual(self.profile.monitor_title, "ToIP Portfolio Monitor")
        self.assertEqual(self.profile.weekly_brief_title, "ToIP Weekly Portfolio Brief")

    def test_representative_taxonomy_is_unchanged(self):
        expected = {
            "dtgwg-zkp-tf": "DTG",
            "aimwg-tmcp-specification": "AIMWG",
            "kswg-keri-specification": "KERI Suite",
            "ctwg-main-glossary": "CTWG",
            "tswg-trust-registry-protocol": "TSWG",
            "egwg-example": "EGWG",
            "vlei-example": "vLEI / EGF",
            "spec-up": "Spec-Up",
            "governance-stack": "Governance",
            "tss001": "Legacy deliverables",
            "unexpected-new-project": "Unclassified",
        }
        for repository, portfolio in expected.items():
            with self.subTest(repository=repository):
                self.assertEqual(classify_portfolio(repository, self.profile), portfolio)

    def test_profile_reproduces_current_retained_repository_classifications(self):
        latest = Path("docs/data/latest.json")
        if not latest.exists():
            self.skipTest("retained latest snapshot is not present")
        snapshot = json.loads(latest.read_text(encoding="utf-8"))
        mismatches = []
        for repository in snapshot.get("repositories", []):
            actual = classify_portfolio(repository["name"], self.profile)
            retained = repository["portfolio"]
            if actual == retained:
                continue
            allowed = self.INTENTIONAL_CLASSIFICATION_MIGRATIONS.get(repository["name"])
            if allowed == (retained, actual):
                continue
            mismatches.append((repository["name"], retained, actual))
        self.assertEqual(mismatches, [], f"profile changed retained ToIP classifications: {mismatches}")

    def test_runtime_adapter_preserves_core_api(self):
        configure_core(self.profile)
        from trust_ecosystem_monitor import core_backend
        self.assertEqual(core_backend.ORG, "trustoverip")
        self.assertEqual(core_backend.classify_portfolio("dtgwg-zkp-tf"), "DTG")
        self.assertEqual(core_backend.classify_portfolio("unexpected-new-project"), "Unclassified")


if __name__ == "__main__":
    unittest.main()
