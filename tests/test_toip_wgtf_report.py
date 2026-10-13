"""WG/TF-first annual report prototype and integration tests."""
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.toip_annual import render as render_annual
from trust_ecosystem_monitor.toip_annual_state import empty, ingest
from trust_ecosystem_monitor.toip_wgtf_report import (
    build_wgtf_development_groups,
    render_wgtf_first_section,
)


GITHUB = {
    "period": "2026-08",
    "evidence": [
        {
            "repository": "trustoverip/dtgwg-cred-spec",
            "kind": "issues",
            "url": "https://github.com/trustoverip/dtgwg-cred-spec/issues/45",
            "title": "Clarify delegation credential handling",
            "event": "opened",
            "occurred_at": "2026-08-12T00:00:00Z",
        },
        {
            "repository": "trustoverip/tswg-trust-registry-protocol",
            "kind": "pull",
            "url": "https://github.com/trustoverip/tswg-trust-registry-protocol/pull/18",
            "title": "Update trust registry discovery language",
            "event": "merged",
            "occurred_at": "2026-08-14T00:00:00Z",
        },
        {
            "repository": "trustoverip/unmapped-demo",
            "kind": "issues",
            "url": "https://github.com/trustoverip/unmapped-demo/issues/1",
            "title": "Unmapped evidence should stay visible",
            "event": "opened",
            "occurred_at": "2026-08-15T00:00:00Z",
        },
    ],
}

CONFLUENCE = {"month": "2026-08", "pages": []}


class WGTFReportTests(unittest.TestCase):
    def _state(self):
        state = empty(2026)
        return ingest(state, GITHUB, CONFLUENCE, observed_at="2026-10-13T00:00:00Z")

    def test_groups_mapped_and_unmapped_developments(self):
        groups = build_wgtf_development_groups(self._state(), {
            "schema_version": "1",
            "registry_status": "curated_incomplete",
            "official_toip_inventory": False,
            "source_owner_authority_verified": False,
            "complete_group_inventory": False,
            "entities": [
                {
                    "id": "toip:dtwg",
                    "name": "Digital Trust Working Group",
                    "entity_type": "working_group",
                    "authority_state": "not_official",
                    "lifecycle_state": "unknown",
                    "official_status_asserted": False,
                    "confidence": "medium",
                    "curator_rationale": "Candidate mapping used for reader grouping without official authority.",
                    "provenance": [{"label": "candidate", "state": "candidate", "url": "https://github.com/trustoverip/dtgwg-cred-spec"}],
                    "mappings": {
                        "repositories": [{"full_name": "trustoverip/dtgwg-cred-spec", "url": "https://github.com/trustoverip/dtgwg-cred-spec", "mapping_state": "candidate", "confidence": "medium"}],
                        "confluence": [],
                        "meeting_series": [],
                    },
                }
            ],
        })
        labels = {group["label"] for group in groups}
        self.assertIn("Digital Trust Working Group", labels)
        self.assertIn("Unmapped / unknown ToIP body", labels)
        unmapped = next(group for group in groups if group["entity_id"] == "unmapped")
        self.assertEqual(unmapped["authority_state"], "not_verified")
        self.assertTrue(any(item["repository"] == "trustoverip/unmapped-demo" for item in unmapped["items"]))

    def test_render_uses_seed_registry_and_preserves_non_authority_boundary(self):
        html = render_wgtf_first_section(self._state())
        self.assertIn("WG/TF-first candidate view", html)
        self.assertIn("Digital Trust Working Group", html)
        self.assertIn("Technical Stack Working Group", html)
        self.assertIn("Unmapped / unknown ToIP body", html)
        self.assertIn("not an official ToIP", html)
        self.assertIn("not_official", html)
        self.assertIn("toip:dtwg", html)
        self.assertIn("trustoverip/unmapped-demo", html)

    def test_annual_render_includes_wgtf_section_without_authority_claim(self):
        html = render_annual(self._state())
        self.assertIn("WG/TF-first candidate view", html)
        self.assertIn("Digital Trust Working Group", html)
        self.assertIn("Technical Stack Working Group", html)
        self.assertIn("Unmapped / unknown ToIP body", html)
        self.assertIn("not an official ToIP", html)
        self.assertIn("Prioritized year-to-date developments", html)
        self.assertIn("Evidence and limitations", html)

    def test_invalid_or_missing_registry_renders_unavailable_not_silent_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"schema_version":"1","registry_status":"official"}', encoding="utf-8")
            html = render_wgtf_first_section(self._state(), registry_path=path)
        self.assertIn("WG/TF-first view", html)
        self.assertIn("Unavailable", html)
        self.assertIn("Repository-first sections remain", html)


if __name__ == "__main__":
    unittest.main()
