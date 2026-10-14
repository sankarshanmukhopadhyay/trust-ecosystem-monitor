"""Publication checks for ToIP CY data-contract assets."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC_DATA_DIR = ROOT / "docs" / "intelligence" / "toip" / "2026" / "data"
SOURCE_ASSET_DIR = ROOT / "trust_ecosystem_monitor" / "toip_cy_data_contract"
MONTHLY_WORKFLOW = ROOT / ".github" / "workflows" / "monthly-intelligence.yml"
BACKFILL_WORKFLOW = ROOT / ".github" / "workflows" / "toip-cy-backfill.yml"


class ToipCyDataContractPublicationTests(unittest.TestCase):
    def test_source_assets_match_documented_data_contract_assets(self):
        self.assertEqual(
            json.loads((DOC_DATA_DIR / "schema.json").read_text(encoding="utf-8")),
            json.loads((SOURCE_ASSET_DIR / "schema.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(
            (DOC_DATA_DIR / "README.md").read_text(encoding="utf-8"),
            (SOURCE_ASSET_DIR / "README.md").read_text(encoding="utf-8"),
        )

    def test_publication_workflows_copy_static_contract_assets(self):
        for workflow in (MONTHLY_WORKFLOW, BACKFILL_WORKFLOW):
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("Publish ToIP CY data-contract assets", text)
            self.assertIn("trust_ecosystem_monitor/toip_cy_data_contract/schema.json", text)
            self.assertIn("$data_dir/schema.json", text)
            self.assertIn("trust_ecosystem_monitor/toip_cy_data_contract/README.md", text)
            self.assertIn("$data_dir/README.md", text)

    def test_monthly_workflow_validates_contract_assets_before_publish(self):
        text = MONTHLY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('test -s "docs/intelligence/toip/${MONTH%-*}/data/manifest.json"', text)
        self.assertIn('test -s "docs/intelligence/toip/${MONTH%-*}/data/schema.json"', text)
        self.assertIn('test -s "docs/intelligence/toip/${MONTH%-*}/data/README.md"', text)


if __name__ == "__main__":
    unittest.main()
