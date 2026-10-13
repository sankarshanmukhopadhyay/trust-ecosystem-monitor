import unittest

from trust_ecosystem_monitor.toip_publication_boundary import (
    assert_metadata_publication_boundary,
    audit_metadata_publication_boundary,
)


VALID_PAYLOAD = {
    "schema_version": "1",
    "type": "toip_confluence_metadata_acquisition",
    "authorization_decision_id": "synthetic-1",
    "source_use_review_evidence_url": "https://example.org/source-use-review",
    "retrieved_at": "2026-10-10T00:00:00+00:00",
    "publication_admitted": False,
    "results": [
        {
            "schema_version": "1",
            "period": "2026-08",
            "source": "confluence",
            "space_ids": ["22970380"],
            "records": [
                {
                    "source": "confluence",
                    "source_id": "42",
                    "space_id": "22970380",
                    "version": 3,
                    "url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/42",
                    "kind": "page_update",
                    "classification": "metadata_only",
                }
            ],
            "diagnostics": [],
            "retrieved_at": "2026-10-10T00:00:00+00:00",
            "search_pages_fetched": 1,
            "metadata_lookups_attempted": 1,
            "search_terminated_normally": True,
            "coverage": "partial",
            "scope_verified": False,
            "scope_caller_approved": True,
            "historical_completeness_verified": False,
            "publication_admitted": False,
        }
    ],
}


def payload_with(mutator):
    import copy

    clone = copy.deepcopy(VALID_PAYLOAD)
    mutator(clone)
    return clone


class PublicationBoundaryTests(unittest.TestCase):
    def test_accepts_metadata_only_nonpublication_artifact(self):
        self.assertEqual(audit_metadata_publication_boundary(VALID_PAYLOAD), [])
        self.assertIs(assert_metadata_publication_boundary(VALID_PAYLOAD), VALID_PAYLOAD)

    def test_rejects_top_level_publication_admission(self):
        payload = payload_with(lambda data: data.__setitem__("publication_admitted", True))
        with self.assertRaises(ValueError):
            assert_metadata_publication_boundary(payload)

    def test_rejects_content_like_fields_anywhere(self):
        payload = payload_with(
            lambda data: data["results"][0]["records"][0].__setitem__("page_title", "Meeting notes")
        )
        violations = audit_metadata_publication_boundary(payload)
        self.assertTrue(any("page_title" in item for item in violations), violations)

    def test_rejects_page_body_or_excerpt_even_if_classified_as_metadata(self):
        payload = payload_with(
            lambda data: data["results"][0]["records"][0].__setitem__("excerpt", "discussed proposal")
        )
        with self.assertRaises(ValueError):
            assert_metadata_publication_boundary(payload)

    def test_rejects_non_metadata_record_classification(self):
        payload = payload_with(
            lambda data: data["results"][0]["records"][0].__setitem__("classification", "body_excerpt")
        )
        violations = audit_metadata_publication_boundary(payload)
        self.assertTrue(any("classification" in item for item in violations), violations)

    def test_rejects_noncanonical_page_url(self):
        payload = payload_with(
            lambda data: data["results"][0]["records"][0].__setitem__(
                "url", "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/42?body=storage"
            )
        )
        with self.assertRaises(ValueError):
            assert_metadata_publication_boundary(payload)

    def test_rejects_author_or_account_identifiers(self):
        payload = payload_with(
            lambda data: data["results"][0]["records"][0].__setitem__("author_account_id", "abc")
        )
        violations = audit_metadata_publication_boundary(payload)
        self.assertTrue(any("author_account_id" in item for item in violations), violations)


if __name__ == "__main__":
    unittest.main()
