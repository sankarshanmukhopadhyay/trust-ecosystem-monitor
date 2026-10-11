"""K1/K2/K3 source interpretation, relationship and publication contract tests."""
import unittest
from trust_ecosystem_monitor.toip_content_interpretation import extract
from trust_ecosystem_monitor.toip_monthly_cross_source import correlate
from trust_ecosystem_monitor.toip_experimental_combined import render

GH = "https://github.com/trustoverip/dtgwg-example/issues/17"
BODY = ('<h2>Delegation protocol discussion</h2>'
        '<p>Proposal: Clarify delegated authority credentials and policy evaluation. '
        'Review whether permission claims can be verified.</p>'
        '<p>Follow-up: compare the authorization credential with the existing protocol issue '
        '<a href="' + GH + '">Issue 17</a>.</p>')


def github(month="2026-08"):
    return {"period": month, "evidence": [{
        "url": GH, "repository": "trustoverip/dtgwg-example",
        "kind": "issues", "event": "opened",
        "title": "Clarify delegation protocol authority credentials",
        "occurred_at": month + "-10T12:00:00Z"}]}


def confluence(month="2026-08"):
    return {"month": month, "coverage": "sample_only",
            "resolved_space_ids": ["22970380"],
            "sample_count": 1, "total_size": 1, "missing_space_count": 0}


def content(month="2026-08"):
    ext = extract(BODY)
    return {"month": month, "pages": [{"id": "123", "version": 2,
             "title": "Delegation discussion", "topic_headings": ["Delegation protocol discussion"],
             "section_abstracts": ext["sections"], "github_references": ext["github_references"]}],
             "unavailable_count": 0}


class ContentKnowledgeTests(unittest.TestCase):
    def test_section_grounding_is_bounded_and_not_full_body(self):
        result = extract(BODY)
        self.assertTrue(result["sections"])
        self.assertIn("proposal_language", result["sections"][0]["language_signals"])
        self.assertEqual(result["github_references"], [GH])
        self.assertRegex(result["sections"][0]["basis_sha256"], r"^[a-f0-9]{64}$")
        self.assertLessEqual(len(result["sections"][0]["brief_source_excerpt"]), 160)
        self.assertEqual(result["sections"][1]["brief_source_excerpt"], "")
        self.assertEqual(extract(BODY), result)

    def test_reject_unbounded_body(self):
        with self.assertRaises(ValueError):
            extract("x" * 250001)

    def test_explicit_link_to_collected_artifact(self):
        relations = correlate(github(), content())
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]["state"], "explicit_reference")
        self.assertEqual(relations[0]["github"], GH)
        self.assertIn("not a determination", relations[0]["limitations"])

    def test_no_false_explicit_link_without_matching_monthly_event(self):
        blank = {"period": "2026-08", "evidence": []}
        self.assertFalse(correlate(blank, content()))

    def test_period_mismatch_fail_closed(self):
        with self.assertRaises(ValueError):
            correlate(github(), content("2026-09"))

    def test_experimental_page_displays_evidence_not_decision(self):
        page = render(github(), confluence(), content())
        self.assertIn("Connections across sources", page)
        self.assertIn("Explicit hyperlink", page)
        self.assertIn("The record raises or examines a question", page)
        self.assertIn("Proposal", BODY)
        self.assertIn("not human-reviewed", page)
        self.assertNotIn("approved by ToIP", page)
        self.assertIn("Source excerpt:", page)

    def test_escaping_untrusted_section_text(self):
        cf = content()
        cf["pages"][0]["section_abstracts"][0]["abstract"] = "<script>x</script>"
        page = render(github(), confluence(), cf)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_missing_provenance_rejected(self):
        cf = content()
        cf["pages"][0]["section_abstracts"][0].pop("basis_sha256")
        with self.assertRaises(ValueError):
            render(github(), confluence(), cf)


if __name__ == "__main__":
    unittest.main()
