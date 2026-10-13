"""Tests for the ToIP CY intelligence machine-ingestion data contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from trust_ecosystem_monitor.toip_annual_state import SCHEMA, validate

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "intelligence" / "toip" / "2026" / "data" / "schema.json"
CONTRACT_PATH = ROOT / "docs" / "toip-cy-intelligence-data-contract.md"
DATA_README_PATH = ROOT / "docs" / "intelligence" / "toip" / "2026" / "data" / "README.md"


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class ToipCyDataContractTests(unittest.TestCase):
    def test_schema_file_documents_current_manifest_identifier(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual("tem-cy-intelligence-v1", schema["properties"]["schema"]["const"])
        self.assertEqual(SCHEMA, schema["properties"]["schema"]["const"])
        self.assertIn("months", schema["required"])
        self.assertIn("source_ledger", schema["required"])
        self.assertIn("revision_notices", schema["required"])
        self.assertIn("monthRecord", schema["$defs"])
        self.assertIn("githubObservation", schema["$defs"])
        self.assertIn("confluenceObservation", schema["$defs"])
        self.assertIn("revisionNotice", schema["$defs"])

    def test_contract_points_ml_tooling_to_manifest_not_rendered_html(self):
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        readme = DATA_README_PATH.read_text(encoding="utf-8")
        self.assertIn("manifest.json", contract)
        self.assertIn("schema.json", contract)
        self.assertIn("ML tooling should prefer the JSON manifest", contract)
        self.assertIn("not scrape the rendered HTML", contract)
        self.assertIn("ML tooling should ingest `manifest.json`, not scrape the HTML", readme)

    def test_contract_preserves_source_and_authority_boundaries(self):
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        required_phrases = [
            "not an official ToIP inventory",
            "not a meeting record",
            "not a decision register",
            "source-owner authorization",
            "Do not infer",
            "official ToIP WG/TF structure",
            "meeting occurrence or attendance",
            "formal decision, approval, adoption or rejection",
            "absence of activity from absence of observations",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, contract)

    def test_representative_github_only_manifest_validates_with_runtime_schema(self):
        observation = {
            "github": {
                "scope": {"org": "trustoverip", "prefixes": ["dtgwg-", "tswg-"]},
                "coverage_complete": True,
                "evidence": [
                    {
                        "repository": "trustoverip/dtgwg-rahp-tf",
                        "url": "https://github.com/trustoverip/dtgwg-rahp-tf/issues/17",
                        "title": "Example observed issue",
                        "event": "opened",
                        "number": 17,
                    }
                ],
            },
            "confluence": {
                "coverage": "sample_only",
                "source_count": 0,
                "unavailable_count": 0,
                "sources": [],
            },
        }
        manifest = {
            "schema": SCHEMA,
            "year": 2026,
            "months": {
                "2026-01": {
                    "period": "2026-01",
                    "observed_at": "2026-10-13T14:00:00+00:00",
                    "observation": observation,
                    "observation_digest": _digest(observation),
                    "temporal_basis": "retrospective-current-public-source",
                }
            },
            "source_ledger": {},
            "revision_notices": [],
        }
        self.assertIs(validate(manifest), manifest)

    def test_runtime_manifest_validation_rejects_digest_mismatch(self):
        observation = {
            "github": {"scope": {}, "coverage_complete": True, "evidence": []},
            "confluence": {"coverage": "sample_only", "source_count": 0, "unavailable_count": 0, "sources": []},
        }
        manifest = {
            "schema": SCHEMA,
            "year": 2026,
            "months": {
                "2026-01": {
                    "period": "2026-01",
                    "observed_at": "2026-10-13T14:00:00+00:00",
                    "observation": observation,
                    "observation_digest": "0" * 64,
                    "temporal_basis": "retrospective-current-public-source",
                }
            },
            "source_ledger": {},
            "revision_notices": [],
        }
        with self.assertRaisesRegex(ValueError, "monthly observation digest mismatch"):
            validate(manifest)


if __name__ == "__main__":
    unittest.main()
