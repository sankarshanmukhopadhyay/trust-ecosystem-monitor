import unittest

from tests.test_toip_authorization_decision import decision, NOW
from trust_ecosystem_monitor.toip_confluence_collect import collect


def sponsor():
    return dict(decision(), issuer="sankarshanmukhopadhyay",
                issuer_role="experiment_sponsor",
                policy_basis="toip_experiment_2026_10_11",
                source_use_compliance_verified=True,
                independent_source_use_review_url="https://example.org/source-use-review")


def review():
    return {"authorization_decision_id": "synthetic-1",
            "source_use_compliance_verified": True,
            "reviewer": "independent-test-reviewer",
            "review_evidence_url": "https://example.org/source-use-review"}


def fetch(path):
    if path.startswith("/wiki/rest/api/content/search?"):
        return {"results": [{"id": "42"}], "size": 1, "_links": {}}
    if path == "/wiki/api/v2/pages/42":
        return {"id": "42", "spaceId": "22970380", "version": {"number": 3}}
    raise AssertionError("unexpected network path")


class CollectionRunnerTests(unittest.TestCase):
    def test_bounded_collection_is_never_admitted(self):
        result = collect(sponsor(), review=review(), revoked_ids=set(),
                         as_of=NOW, months=["2026-08"], fetch=fetch)
        self.assertFalse(result["publication_admitted"])
        self.assertEqual(result["results"][0]["records"][0]["source_id"], "42")
        self.assertFalse(result["results"][0]["publication_admitted"])

    def test_missing_or_mismatched_review_fails_before_network(self):
        for candidate in ({}, dict(review(), review_evidence_url="https://example.org/other"),
                          dict(review(), source_use_compliance_verified=False),
                          dict(review(), reviewer="sankarshanmukhopadhyay")):
            with self.subTest(candidate=candidate), self.assertRaises(PermissionError):
                collect(sponsor(), review=candidate, revoked_ids=set(), as_of=NOW,
                        months=["2026-08"], fetch=lambda _: self.fail("unexpected network"))

    def test_scope_and_revocation_fail_before_network(self):
        for months, revoked in ((["2026-09"], set()), (["2026-08", "2026-08"], set()),
                                (["2026-08"], {"synthetic-1"})):
            with self.subTest(months=months, revoked=revoked), self.assertRaises((ValueError, PermissionError)):
                collect(sponsor(), review=review(), revoked_ids=revoked, as_of=NOW,
                        months=months, fetch=lambda _: self.fail("unexpected network"))

    def test_unavailable_search_is_not_published(self):
        result = collect(sponsor(), review=review(), revoked_ids=set(), as_of=NOW,
                         months=["2026-08"], fetch=lambda _: (_ for _ in ()).throw(ValueError("offline")))
        self.assertEqual(result["results"][0]["coverage"], "unavailable")
        self.assertFalse(result["publication_admitted"])


if __name__ == "__main__":
    unittest.main()
