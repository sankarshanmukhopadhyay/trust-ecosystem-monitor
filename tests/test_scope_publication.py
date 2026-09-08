import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.scope import build_scope_register, render_scope


class ScopePublicationTests(unittest.TestCase):
    def snapshot(self):
        def repo(name, state, tier):
            return {
                "full_name": f"example/{name}",
                "url": f"https://github.com/example/{name}",
                "portfolio": "Example",
                "lifecycle": "active",
                "admission": {
                    "state": state,
                    "tier": tier,
                    "rationale": [f"{state} rationale"],
                    "evidence": ["https://example.org/evidence"] if state == "included" else [],
                    "method": "test",
                },
                "discovery": {
                    "sources": [{"type": "explicit_repository", "value": f"example/{name}"}]
                },
            }

        return {
            "generated_at": "2026-09-08T00:00:00+00:00",
            "ecosystem_profile": {"id": "example", "display_name": "Example"},
            "repositories": [
                repo("core", "included", "core"),
                repo("related", "included", "related"),
                repo("watch", "watch", "watch"),
                repo("review", "review", "inventory"),
                repo("excluded", "excluded", "inventory"),
            ],
        }

    def test_scope_counts_distinguish_discovery_from_collection(self):
        register = build_scope_register(self.snapshot())
        self.assertEqual(register["counts"]["discovered"], 5)
        self.assertEqual(register["counts"]["deep_monitored"], 2)
        self.assertEqual(register["counts"]["watch_monitored"], 1)
        self.assertEqual(register["counts"]["inventory_only"], 2)
        self.assertEqual(register["counts"]["review"], 1)
        self.assertEqual(register["counts"]["excluded"], 1)

    def test_render_scope_publishes_human_and_machine_readable_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            docs = Path(directory)
            html_path, json_path = render_scope(self.snapshot(), docs)

            self.assertTrue(html_path.exists())
            self.assertTrue(json_path.exists())
            page = html_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("Discovery, admission and collection intensity are separate decisions", page)
            self.assertIn("machine-readable scope", page)
            self.assertEqual(payload["counts"]["deep_monitored"], 2)
            self.assertEqual(payload["repositories"][0]["discovery"]["sources"][0]["type"], "explicit_repository")


if __name__ == "__main__":
    unittest.main()
