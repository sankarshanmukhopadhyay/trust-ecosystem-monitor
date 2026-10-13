import copy
import unittest

from trust_ecosystem_monitor.toip_wgtf_registry import group_repositories, load_registry, validate_registry

REGISTRY_PATH = "data/trustoverip/wgtf-registry.json"


class ToipWgTfRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry(REGISTRY_PATH)

    def test_seed_registry_is_explicitly_curated_and_incomplete(self):
        self.assertEqual(self.registry["registry_status"], "curated_incomplete")
        self.assertFalse(self.registry["official_toip_inventory"])
        self.assertFalse(self.registry["source_owner_authority_verified"])
        self.assertFalse(self.registry["complete_group_inventory"])
        self.assertGreaterEqual(len(self.registry["entities"]), 3)

    def test_entries_do_not_claim_official_status(self):
        for entry in self.registry["entities"]:
            self.assertFalse(entry["official_status_asserted"])
            self.assertIn(entry["authority_state"], {"not_official", "not_verified"})
            self.assertIn("curator_rationale", entry)
            self.assertTrue(entry["provenance"])

    def test_repository_grouping_preserves_candidate_mappings(self):
        grouped = group_repositories(self.registry)
        self.assertEqual(grouped["trustoverip/dtgwg-rahp-tf"], ["toip:dtwg"])
        self.assertEqual(grouped["trustoverip/tswg-trust-registry-protocol"], ["toip:tswg"])
        self.assertNotIn("trustoverip/unknown-repo", grouped)

    def test_official_or_complete_claims_are_rejected(self):
        for key in ("official_toip_inventory", "source_owner_authority_verified", "complete_group_inventory"):
            mutated = copy.deepcopy(self.registry)
            mutated[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_registry(mutated)

    def test_entry_cannot_assert_official_status(self):
        mutated = copy.deepcopy(self.registry)
        mutated["entities"][0]["official_status_asserted"] = True
        with self.assertRaises(ValueError):
            validate_registry(mutated)

    def test_duplicate_entity_ids_are_rejected(self):
        mutated = copy.deepcopy(self.registry)
        mutated["entities"][1]["id"] = mutated["entities"][0]["id"]
        with self.assertRaises(ValueError):
            validate_registry(mutated)

    def test_unsafe_mapping_urls_are_rejected(self):
        mutated = copy.deepcopy(self.registry)
        mutated["entities"][0]["mappings"]["repositories"][0]["url"] = "https://example.com/not-toip"
        with self.assertRaises(ValueError):
            validate_registry(mutated)

    def test_meeting_series_must_not_be_silently_treated_as_held(self):
        for entry in self.registry["entities"]:
            for series in entry["mappings"].get("meeting_series", []):
                self.assertIn(series["held_state"], {"not_checked", "unknown", "scheduled_only", "held_verified"})
        mutated = copy.deepcopy(self.registry)
        mutated["entities"][0]["mappings"]["meeting_series"][0]["held_state"] = "held"
        with self.assertRaises(ValueError):
            validate_registry(mutated)


if __name__ == "__main__":
    unittest.main()
