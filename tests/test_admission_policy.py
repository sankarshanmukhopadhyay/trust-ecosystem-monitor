import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.profile import admission_decision, load_profile


BASE = '''
schema_version = "1"
id = "example"
organization = "example-org"
display_name = "Example"
monitor_title = "Example Monitor"
weekly_brief_title = "Example Brief"
disclaimer = "Independent observation."

[[portfolio_rules]]
portfolio = "Example"
prefixes = ["example-"]
'''


class AdmissionPolicyTests(unittest.TestCase):
    def load_text(self, suffix: str = ""):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.toml"
            path.write_text(BASE + suffix, encoding="utf-8")
            return load_profile(path)

    def test_legacy_profile_admits_every_discovered_repository(self):
        decision = admission_decision("unclassified-repository", self.load_text())
        self.assertEqual((decision.state, decision.tier, decision.method), ("included", "core", "all_discovered"))

    def test_governed_profile_defaults_unknown_repository_to_review_inventory(self):
        profile = self.load_text('''

[admission]
mode = "governed"
''')
        decision = admission_decision("unknown-repository", profile)
        self.assertEqual((decision.state, decision.tier, decision.method), ("review", "inventory", "default_review"))

    def test_governed_override_records_inclusion_evidence(self):
        profile = self.load_text('''

[admission]
mode = "governed"

[[admission.repositories]]
repository = "example-spec"
state = "included"
tier = "core"
rationale = "The ecosystem governance record identifies this as an active specification repository."
evidence = ["https://example.invalid/governance/example-spec"]
''')
        decision = admission_decision("EXAMPLE-SPEC", profile)
        self.assertEqual((decision.state, decision.tier, decision.method), ("included", "core", "override"))
        self.assertEqual(decision.evidence, ("https://example.invalid/governance/example-spec",))

    def test_governed_exclusion_can_retain_inventory_provenance(self):
        profile = self.load_text('''

[admission]
mode = "governed"

[[admission.repositories]]
repository = "historical-example"
state = "excluded"
tier = "inventory"
rationale = "Historical repository retained only so the exclusion decision remains auditable."
''')
        decision = admission_decision("historical-example", profile)
        self.assertEqual((decision.state, decision.tier), ("excluded", "inventory"))

    def assert_invalid(self, suffix: str, message: str):
        with self.assertRaisesRegex(ValueError, message):
            self.load_text(suffix)

    def test_unknown_admission_mode_is_rejected(self):
        self.assert_invalid('\n[admission]\nmode = "guess"\n', "unsupported admission mode")

    def test_governed_default_state_cannot_expand_scope(self):
        self.assert_invalid(
            '\n[admission]\nmode = "governed"\ndefault_state = "included"\n',
            "must default to state=review",
        )

    def test_governed_default_tier_cannot_expand_scope(self):
        self.assert_invalid(
            '\n[admission]\nmode = "governed"\ndefault_tier = "core"\n',
            "must default to state=review",
        )

    def test_unknown_admission_state_is_rejected(self):
        self.assert_invalid('''
[admission]
mode = "governed"
[[admission.repositories]]
repository = "x"
state = "maybe"
tier = "core"
rationale = "reason"
''', "unsupported admission state")

    def test_unknown_collection_tier_is_rejected(self):
        self.assert_invalid('''
[admission]
mode = "governed"
[[admission.repositories]]
repository = "x"
state = "included"
tier = "deep"
rationale = "reason"
''', "unsupported collection tier")

    def test_governed_inclusion_without_evidence_is_rejected(self):
        self.assert_invalid('''
[admission]
mode = "governed"
[[admission.repositories]]
repository = "x"
state = "included"
tier = "core"
rationale = "reason"
''', "requires evidence")

    def test_override_without_rationale_is_rejected(self):
        self.assert_invalid('''
[admission]
mode = "governed"
[[admission.repositories]]
repository = "x"
state = "excluded"
tier = "inventory"
rationale = ""
''', "requires repository and rationale")


if __name__ == "__main__":
    unittest.main()
