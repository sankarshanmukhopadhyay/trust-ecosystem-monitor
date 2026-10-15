"""Annual-state compatibility inspection tests."""
import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.toip_annual_state import SCHEMA, empty
from trust_ecosystem_monitor.toip_state_compatibility import inspect


class StateCompatibilityTests(unittest.TestCase):
    def test_current_manifest_is_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            path.write_text(json.dumps(empty(2026)), encoding="utf-8")
            result = inspect(path)
            self.assertTrue(result["compatible"])
            self.assertFalse(result["migration_required"])
            self.assertEqual(result["source_schema"], SCHEMA)
            self.assertEqual(result["target_schema"], SCHEMA)
            self.assertEqual(result["year"], 2026)

    def test_unknown_manifest_reports_migration_required_without_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            state = empty(2026)
            state["schema"] = "tem-cy-intelligence-v99"
            original = json.dumps(state, sort_keys=True)
            path.write_text(json.dumps(state), encoding="utf-8")
            result = inspect(path)
            self.assertFalse(result["compatible"])
            self.assertTrue(result["migration_required"])
            self.assertIn("explicit reviewed migration", result["message"])
            self.assertEqual(json.dumps(json.loads(path.read_text()), sort_keys=True), original)


if __name__ == "__main__":
    unittest.main()
