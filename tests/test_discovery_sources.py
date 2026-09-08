import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.profile import DiscoverySource, load_profile


BASE = '''
schema_version = "1"
id = "example"
organization = "example-org"
display_name = "Example"
monitor_title = "Example Monitor"
weekly_brief_title = "Example Brief"
disclaimer = "Independent."

[[portfolio_rules]]
portfolio = "Core"
prefixes = ["core-"]
'''


class DiscoverySourceTests(unittest.TestCase):
    def load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.toml"
            path.write_text(text, encoding="utf-8")
            return load_profile(path)

    def test_legacy_profile_gets_explicit_github_source(self):
        profile = self.load_text(BASE)
        self.assertEqual(
            profile.discovery_sources,
            (DiscoverySource(type="github_organization", value="example-org"),),
        )

    def test_multiple_discovery_sources_are_preserved(self):
        profile = self.load_text(
            BASE
            + '''
[[discovery_sources]]
type = "github_organization"
value = "w3c"

[[discovery_sources]]
type = "explicit_repository"
value = "w3c-cg/dataspaces"
'''
        )
        self.assertEqual(len(profile.discovery_sources), 2)
        self.assertEqual(profile.discovery_sources[1].value, "w3c-cg/dataspaces")

    def test_unknown_source_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported discovery source type"):
            self.load_text(
                BASE
                + '''
[[discovery_sources]]
type = "semantic_guess"
value = "trust"
'''
            )

    def test_empty_source_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "without a value"):
            self.load_text(
                BASE
                + '''
[[discovery_sources]]
type = "github_organization"
value = ""
'''
            )


if __name__ == "__main__":
    unittest.main()
