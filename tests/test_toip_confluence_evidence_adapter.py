import unittest

from trust_ecosystem_monitor.toip_confluence_acquisition import acquire_metadata
from trust_ecosystem_monitor.toip_confluence_evidence_adapter import stage_confluence_metadata
from trust_ecosystem_monitor.toip_evidence_contract import validate_observations


def fixture(path):
    if path.startswith("/wiki/rest/api/content/search?"):
        return {"results": [{"id": "42"}], "size": 1, "_links": {}}
    if path == "/wiki/api/v2/pages/42":
        return {"id": "42", "spaceId": "22970380", "version": {"number": 3}}
    raise AssertionError("unexpected request")


def batch():
    return acquire_metadata(
        "2026-08", approved_space_ids={"22970380"},
        scope_approved=True, reuse_approved=True, fetch=fixture,
        retrieved_at="2026-10-10T09:00:00Z",
    )


class AdapterTests(unittest.TestCase):
    def test_offline_acquisition_to_quarantine(self):
        staged = stage_confluence_metadata(batch())
        self.assertEqual(len(staged["records"]), 1)
        record = staged["records"][0]
        self.assertEqual(record["version"], 3)
        self.assertEqual(record["retrieved_at"], "2026-10-10T09:00:00Z")
        self.assertFalse(record["correlation_eligible"])
        self.assertFalse(record["publication_admitted"])
        for field in ("occurred_at", "subject_id", "summary", "subject_evidence_url",
                      "publication_approved", "decision_evidence_url"):
            self.assertNotIn(field, record)
        with self.assertRaises(ValueError):
            validate_observations(staged["records"], approved_confluence=True)

    def test_rejects_publication_flag(self):
        with self.assertRaises(ValueError):
            stage_confluence_metadata(dict(batch(), publication_admitted=True))

    def test_rejects_claim_of_verified_scope(self):
        with self.assertRaises(ValueError):
            stage_confluence_metadata(dict(batch(), scope_verified=True))

    def test_rejects_wrong_page_url(self):
        source = batch()
        source["records"][0]["url"] = "https://evil.example/wiki/spaces/HOME/pages/42"
        with self.assertRaises(ValueError):
            stage_confluence_metadata(source)

    def test_rejects_duplicate_version(self):
        source = batch()
        source["records"].append(dict(source["records"][0]))
        with self.assertRaises(ValueError):
            stage_confluence_metadata(source)

    def test_rejects_naive_retrieval_time(self):
        with self.assertRaises(ValueError):
            stage_confluence_metadata(dict(batch(), retrieved_at="2026-10-10T09:00:00"))

    def test_page_modification_cannot_be_reclassified_as_decision(self):
        source = batch()
        source["records"][0]["kind"] = "decision"
        with self.assertRaises(ValueError):
            stage_confluence_metadata(source)


if __name__ == "__main__":
    unittest.main()
