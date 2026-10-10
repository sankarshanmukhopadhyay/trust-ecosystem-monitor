import unittest

from trust_ecosystem_monitor.toip_cross_source_preview import render_preview


G = {"source": "github", "source_id": "example/repo#1", "subject_id": "example-1",
     "subject_evidence_url": "https://github.com/example/repo/pull/1",
     "url": "https://github.com/example/repo/pull/1", "kind": "proposal",
     "occurred_at": "2026-08-01T00:00:00Z", "summary": "Synthetic example"}
C = {"source": "confluence", "source_id": "page-123", "subject_id": "example-1",
     "subject_evidence_url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/123",
     "url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/123",
     "kind": "page_update", "occurred_at": "2026-08-02T00:00:00Z",
     "summary": "Synthetic example", "publication_approved": True}


def fixture(records):
    return {"schema_version": "1", "fixture_only": True,
            "publication_mode": "offline_test_only", "observations": records}


class OfflinePreviewTests(unittest.TestCase):
    def test_synthetic_cross_source_preview(self):
        html = render_preview(fixture([G, C]))
        self.assertIn("NOT FOR PUBLICATION", html)
        self.assertIn("reference the same curator-identified subject", html.lower())
        self.assertIn("does not establish governance approval", html)

    def test_no_unreviewed_cross_source_inference(self):
        html = render_preview(fixture([G, dict(C, subject_id="different")]))
        self.assertNotIn("curator-identified subject", html)

    def test_absent_confluence(self):
        html = render_preview(fixture([G]))
        self.assertIn("NOT FOR PUBLICATION", html)
        self.assertNotIn("curator-identified subject", html)

    def test_no_publication_mode(self):
        with self.assertRaisesRegex(ValueError, "public publication forbidden"):
            render_preview(dict(fixture([G, C]), publication_mode="public"))

    def test_no_nonfixture_input(self):
        with self.assertRaisesRegex(ValueError, "synthetic fixtures"):
            render_preview(dict(fixture([G, C]), fixture_only=False))

    def test_reject_unapproved_record(self):
        with self.assertRaisesRegex(ValueError, "record-level"):
            render_preview(fixture([G, dict(C, publication_approved=False)]))

    def test_escape_subject(self):
        html = render_preview(fixture([dict(G, subject_id="<script>"),
                                       dict(C, subject_id="<script>")]))
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
