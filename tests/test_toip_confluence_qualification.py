import unittest

from trust_ecosystem_monitor.toip_confluence_acquisition import acquire_metadata
from trust_ecosystem_monitor.toip_confluence_evidence_adapter import stage_confluence_metadata
from trust_ecosystem_monitor.toip_confluence_qualification import qualify_confluence_metadata
from trust_ecosystem_monitor.toip_evidence_contract import validate_observations, infer_correlations


def fixture(path):
    if path.startswith("/wiki/rest/api/content/search?"):
        return {"results": [{"id": "42"}], "_links": {}}
    if path == "/wiki/api/v2/pages/42":
        return {"id": "42", "spaceId": "22970380", "version": {"number": 3}}
    raise AssertionError(path)


def manifest():
    return stage_confluence_metadata(acquire_metadata(
        "2026-08", approved_space_ids={"22970380"},
        scope_approved=True, reuse_approved=True,
        retrieved_at="2026-10-10T09:00:00Z", fetch=fixture))


def review():
    return {
        "source_id": "42", "version": 3, "reviewer": "example-curator",
        "reviewed_at": "2026-10-10T10:00:00Z",
        "occurred_at": "2026-08-13T10:00:00Z",
        "subject_id": "example-change-12",
        "summary": "Synthetic page update for offline contract testing",
        "event_type": "page_update", "evidence_checked": True,
        "event_evidence_url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/42",
        "subject_evidence_url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/42",
        "source_owner_authority_verified": False,
        "publication_approved": False,
    }


class QualificationTests(unittest.TestCase):
    def test_review_ready_but_never_admitted(self):
        result = qualify_confluence_metadata(manifest(), review())
        self.assertEqual(result["status"], "review_ready")
        self.assertFalse(result["publication_admitted"])
        self.assertFalse(result["correlation_eligible"])
        self.assertEqual(result["page_version"], {"source_id": "42", "version": 3})
        with self.assertRaisesRegex(ValueError, "record-level"):
            validate_observations([result["candidate"]], approved_confluence=True)
        with self.assertRaises(ValueError):
            infer_correlations([result["candidate"]], approved_confluence=True)

    def test_rejects_wrong_page_version(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), version=4))

    def test_rejects_unreviewed_evidence(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), evidence_checked=False))

    def test_rejects_governance_decision_inference(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), event_type="decision"))

    def test_rejects_implicit_publication(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), publication_approved=True))

    def test_rejects_unverified_authority_assertion(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), source_owner_authority_verified=True))

    def test_rejects_missing_subject_evidence(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), subject_evidence_url=""))

    def test_rejects_naive_event_timestamp(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), occurred_at="2026-08-13T10:00:00"))

    def test_rejects_wrong_evidence_host(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(manifest(), dict(review(), event_evidence_url="https://example.org/42"))

    def test_rejects_unquarantined_manifest(self):
        with self.assertRaises(ValueError):
            qualify_confluence_metadata(dict(manifest(), publication_admitted=True), review())


if __name__ == "__main__":
    unittest.main()
