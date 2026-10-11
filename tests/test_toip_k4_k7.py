"""K4–K7 semantic filtering, ranked presentation and monthly operations tests."""
import json
import tempfile
import unittest
from pathlib import Path
from trust_ecosystem_monitor.toip_content_interpretation import extract
from trust_ecosystem_monitor.toip_monthly_editorial import present, priority
from trust_ecosystem_monitor.toip_monthly_one import publish_month
from trust_ecosystem_monitor.toip_experimental_combined import render

GITHUB = "https://github.com/trustoverip/dtgwg-test/issues/4"
GH = {"period": "2026-08", "evidence": [{"repository": "trustoverip/dtgwg-test",
      "kind": "issues", "title": "Delegation authority protocol clarification", "url": GITHUB,
      "occurred_at": "2026-08-10T01:00:00Z", "event": "opened"}]}
CF = {"month": "2026-08", "coverage": "sample_only", "resolved_space_ids": ["22970380"],
      "sample_count": 1, "total_size": 1, "missing_space_count": 0}

class MonthlyEditorialTests(unittest.TestCase):
    def test_admin_boilerplate_excluded(self):
        html = ('<h2>Antitrust and IPR notice</h2><p>The Linux Foundation requires compliance '
                'with the Antitrust policy and intellectual property rights disclosure.</p>'
                '<h2>Technical discussion</h2><p>Proposal: clarify delegation credential '
                'authority semantics and protocol implementation requirements for the next release.</p>')
        report = extract(html)
        self.assertEqual(len(report["sections"]), 1)
        self.assertEqual(report["sections"][0]["section"], "Technical discussion")
        self.assertIn("proposal", report["sections"][0]["abstract"].lower())
        self.assertNotIn("Text under this section addresses", str(report))
        self.assertEqual(report, extract(html))

    def test_rank_not_severity(self):
        d = {"semantic": "authority", "change": "Opening observed; subsequent status not determined"}
        self.assertEqual(priority(d, True)[0], "Review first")
        self.assertEqual(priority(d, False)[0], "Context")

    def test_tem_tables_and_source_link(self):
        raw = ('<h2>Delegation discussion</h2><p>Proposal: clarify delegation '
               'credential authority semantics and policy validation.</p>')
        section = extract(raw)["sections"][0]
        contents = {"month": "2026-08", "pages": [{"id": "20", "title": "Delegation minutes",
                  "url": "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/20",
                  "version": 1, "page_kind": "substantive",
                  "section_abstracts": [section], "github_references": [GITHUB]}]}
        page = render(GH, CF, contents)
        self.assertIn("Executive intelligence brief", page)
        self.assertIn("Prioritized developments", page)
        self.assertIn("Cross-source review seams", page)
        self.assertIn("What substantive Confluence records describe", page)
        self.assertIn("<table>", page)
        self.assertIn("Trust Ecosystem Monitor", page)
        self.assertIn("Review first", page)
        self.assertIn(GITHUB, page)
        self.assertIn("source", page.lower())

    def test_completed_month_publication_and_index(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gh = root / "monthly"
            gh.mkdir()
            (gh / "2026-08.json").write_text(json.dumps(GH))
            site = root / "docs"
            site.mkdir()
            (site / "index.html").write_text("<html><main>Existing</main></html>")
            contents = {"month": "2026-08", "pages": [], "unavailable_count": 0}
            output = publish_month("2026-08", gh, site,
                                   search=lambda month, resolve_missing: CF,
                                   content_collect=lambda month: contents)
            self.assertTrue(output.is_file())
            self.assertIn("2026-08/experimental-combined.html", (site / "index.html").read_text())
            # Repeated publication does not add duplicate links.
            publish_month("2026-08", gh, site,
                          search=lambda month, resolve_missing: CF,
                          content_collect=lambda month: contents)
            self.assertEqual((site / "index.html").read_text().count('href="2026-08/experimental-combined.html"'), 1)

    def test_monthly_schedule_and_no_push_trigger(self):
        workflow = Path(".github/workflows/monthly-intelligence.yml").read_text()
        self.assertIn("schedule:", workflow)
        self.assertIn("40 2 2 * *", workflow)
        self.assertNotIn("  push:", workflow)
        self.assertIn("generated-observations", workflow)


if __name__ == "__main__":
    unittest.main()
