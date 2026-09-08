import unittest
from pathlib import Path

from trust_ecosystem_monitor.admission_policy import load_admission_policy
from trust_ecosystem_monitor.profile import load_profile


PROFILE = Path("organizations/w3c/profile.toml")
POLICY = Path("organizations/w3c/admission.toml")


class W3CBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(PROFILE)
        cls.decisions = load_admission_policy(POLICY)

    def test_w3c_does_not_enumerate_the_entire_github_organization(self):
        self.assertNotIn("github_organization", {source.type for source in self.profile.discovery_sources})
        self.assertTrue(all(source.type == "explicit_repository" for source in self.profile.discovery_sources))

    def test_every_discovered_repository_has_an_admission_decision(self):
        discovered = {source.value.lower() for source in self.profile.discovery_sources}
        self.assertEqual(discovered, set(self.decisions))

    def test_every_included_repository_has_evidence(self):
        for repository, decision in self.decisions.items():
            with self.subTest(repository=repository):
                self.assertEqual(decision.state, "included")
                self.assertGreater(len(decision.evidence), 0)

    def test_baseline_is_bounded(self):
        self.assertLessEqual(len(self.decisions), 10)

    def test_expected_core_and_related_boundaries(self):
        self.assertEqual(self.decisions["w3c/vc-data-model"].tier, "core")
        self.assertEqual(self.decisions["w3c/webauthn"].tier, "related")
        self.assertTrue(self.decisions["w3c/vc-data-model"].deep_collection_allowed)


if __name__ == "__main__":
    unittest.main()
