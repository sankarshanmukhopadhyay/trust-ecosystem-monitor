import unittest
from test_toip_authorization_decision import decision, NOW
from trust_ecosystem_monitor.toip_confluence_admission import admit_qualified_confluence
from trust_ecosystem_monitor.toip_evidence_contract import infer_correlations


def qualified():
    url = "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/42"
    return {
        "status": "review_ready", "publication_admitted": False,
        "correlation_eligible": False, "reviewer": "curator",
        "reviewed_at": "2026-10-10T09:00:00Z",
        "page_version": {"source_id": "42", "version": 3},
        "event_evidence_url": url,
        "candidate": {"source": "confluence", "source_id": "42",
                      "kind": "page_update", "url": url,
                      "occurred_at": "2026-08-13T10:00:00Z",
                      "subject_id": "synthetic-subject", "subject_evidence_url": url,
                      "summary": "Synthetic metadata revision",
                      "publication_approved": False},
    }


def independent():
    return {"approved": True, "reviewer": "independent-reviewer",
            "source_links_verified": True, "subject_mapping_verified": True,
            "review_evidence_url": "https://example.org/review",
            "reviewed_at": "2026-10-10T09:30:00Z"}


def admit(q=None, d=None, i=None, revoked=None):
    return admit_qualified_confluence(
        qualified() if q is None else q, decision() if d is None else d,
        as_of=NOW, revoked_ids=set() if revoked is None else revoked,
        independent_review=independent() if i is None else i)


class AdmissionTests(unittest.TestCase):
    def test_synthetic_admission_preserves_lineage(self):
        result = admit()
        self.assertTrue(result["publication_approved"])
        self.assertEqual(result["page_version"], 3)
        self.assertEqual(result["authorization_decision_id"], "synthetic-1")
        self.assertEqual(infer_correlations([result], approved_confluence=True), [])

    def test_wrong_period(self):
        d = decision()
        d["scope"]["periods"] = ["2026-09"]
        with self.assertRaises(ValueError):
            admit(d=d)

    def test_wrong_space(self):
        d = decision()
        d["scope"]["space_ids"] = ["12345"]
        with self.assertRaises(ValueError):
            admit(d=d)

    def test_no_independent_review(self):
        with self.assertRaises(ValueError):
            admit(i=dict(independent(), approved=False))

    def test_same_reviewer(self):
        with self.assertRaises(ValueError):
            admit(i=dict(independent(), reviewer="curator"))

    def test_no_subject_mapping_review(self):
        with self.assertRaises(ValueError):
            admit(i=dict(independent(), subject_mapping_verified=False))

    def test_qualification_remains_quarantined(self):
        with self.assertRaises(ValueError):
            admit(q=dict(qualified(), publication_admitted=True))

    def test_future_review(self):
        with self.assertRaises(ValueError):
            admit(i=dict(independent(), reviewed_at="2026-11-01T00:00:00Z"))

    def test_revoked_decision(self):
        with self.assertRaises(ValueError):
            admit(revoked={"synthetic-1"})


if __name__ == "__main__":
    unittest.main()
