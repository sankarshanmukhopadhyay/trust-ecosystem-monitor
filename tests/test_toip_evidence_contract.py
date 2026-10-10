import unittest

from trust_ecosystem_monitor.toip_evidence_contract import infer_correlations, validate_observations


GITHUB = dict(source="github", source_id="org/repo#12", subject_id="change-12",
              kind="proposal", url="https://github.com/org/repo/pull/12",
              occurred_at="2026-08-12T10:00:00Z", summary="PR opened", subject_evidence_url="https://github.com/org/repo/pull/12")
CONFLUENCE = dict(source="confluence", source_id="page-45-v2", subject_id="change-12",
                  kind="page_update", url="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/45",
                  occurred_at="2026-08-13T10:00:00Z", summary="Page revised",
                  publication_approved=True, subject_evidence_url="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/45")


class ContractTests(unittest.TestCase):
    def test_requires_source_authorization(self):
        with self.assertRaisesRegex(ValueError, "approval required"):
            infer_correlations([GITHUB, CONFLUENCE])

    def test_explicit_shared_subject_is_bounded(self):
        findings = infer_correlations([GITHUB, CONFLUENCE], approved_confluence=True)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "cross_source_reference")
        self.assertIn("does not establish governance approval", findings[0]["limitations"])

    def test_missing_reviewable_subject_evidence_suppresses_inference(self):
        self.assertEqual(infer_correlations([GITHUB, dict(CONFLUENCE, subject_evidence_url="")],
                                            approved_confluence=True), [])

    def test_unsafe_subject_evidence_suppresses_inference(self):
        self.assertEqual(infer_correlations([GITHUB, dict(CONFLUENCE, subject_evidence_url="http://bad.example")],
                                            approved_confluence=True), [])

    def test_unrelated_subjects_not_correlated(self):
        self.assertEqual(infer_correlations([GITHUB, dict(CONFLUENCE, subject_id="other")],
                                            approved_confluence=True), [])

    def test_temporal_proximity_is_not_correlation(self):
        self.assertEqual(infer_correlations([GITHUB, dict(CONFLUENCE, subject_id="other",
                                occurred_at="2026-08-12T10:00:01Z")], approved_confluence=True), [])

    def test_reject_duplicate_records(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_observations([GITHUB, GITHUB])

    def test_reject_unapproved_record(self):
        with self.assertRaisesRegex(ValueError, "record-level"):
            validate_observations([GITHUB, dict(CONFLUENCE, publication_approved=False)],
                                  approved_confluence=True)

    def test_page_update_is_not_decision(self):
        with self.assertRaisesRegex(ValueError, "decision requires"):
            validate_observations([dict(CONFLUENCE, kind="decision")], approved_confluence=True)

    def test_requires_explicit_subject(self):
        with self.assertRaisesRegex(ValueError, "subject_id"):
            validate_observations([dict(GITHUB, subject_id="")])

    def test_requires_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_observations([dict(GITHUB, occurred_at="2026-08-12T10:00:00")])

    def test_reject_unsafe_url(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_observations([dict(GITHUB, url="http://github.com/org/repo")])


if __name__ == "__main__":
    unittest.main()
