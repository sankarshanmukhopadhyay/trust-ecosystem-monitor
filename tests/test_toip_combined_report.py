import unittest
from tests.test_toip_evidence_contract import GITHUB, CONFLUENCE
from trust_ecosystem_monitor.toip_combined_report import compose, markdown, main, html
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
import json


def inputs():
    gh = {"period": "2026-08", "evidence": [{
        "id": "gh-1", "url": GITHUB["url"], "title": "PR",
        "occurred_at": GITHUB["occurred_at"]}], "coverage_complete": True}
    cf = {"period": "2026-08", "publication_admitted": True,
          "coverage": "partial", "observations": [
              dict(CONFLUENCE, authorization_decision_id="synthetic",
                   independent_review_evidence_url="https://example.org/review")],
          "reviewed_github_observations": [GITHUB]}
    return gh, cf


class CombinedReportTests(unittest.TestCase):
    def test_composition_and_findings(self):
        gh, cf = inputs()
        result = compose(gh, cf)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["coverage"]["confluence"], "partial")
        self.assertIn("Admitted Confluence", markdown(result))

    def test_reject_missing_admission(self):
        gh, cf = inputs()
        cf["publication_admitted"] = False
        with self.assertRaises(ValueError):
            compose(gh, cf)

    def test_reject_synthetic_flag(self):
        gh, cf = inputs()
        cf["fixture_only"] = True
        with self.assertRaises(ValueError):
            compose(gh, cf)

    def test_reject_wrong_period_and_outside_month(self):
        gh, cf = inputs()
        cf["period"] = "2026-09"
        with self.assertRaises(ValueError):
            compose(gh, cf)
        gh, cf = inputs()
        cf["observations"][0]["occurred_at"] = "2026-09-01T00:00:00Z"
        with self.assertRaises(ValueError):
            compose(gh, cf)

    def test_reject_unreviewed_and_unmatched_mapping(self):
        gh, cf = inputs()
        cf["observations"][0].pop("independent_review_evidence_url")
        with self.assertRaises(ValueError):
            compose(gh, cf)
        gh, cf = inputs()
        cf["reviewed_github_observations"][0] = dict(GITHUB, url="https://github.com/other")
        with self.assertRaises(ValueError):
            compose(gh, cf)

    def test_reject_missing_coverage(self):
        gh, cf = inputs()
        cf.pop("coverage")
        with self.assertRaises(ValueError):
            compose(gh, cf)

    def test_html_has_clickable_source_and_review_links(self):
        gh, cf = inputs()
        page = html(compose(gh, cf))
        self.assertIn('<a href="https://github.com/org/repo/pull/12">', page)
        self.assertIn('<a href="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/45">', page)
        self.assertIn('<a href="https://example.org/review">', page)

    def test_html_rejects_unsafe_source_url(self):
        gh, cf = inputs()
        gh["evidence"][0]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            html(compose(gh, cf))

    def test_html_escapes_untrusted_text(self):
        gh, cf = inputs()
        gh["evidence"][0]["title"] = "<script>alert(1)</script>"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "github.json").write_text(json.dumps(gh))
            (root / "confluence.json").write_text(json.dumps(cf))
            with patch("sys.argv", ["prog", "--github", str(root / "github.json"),
                                     "--admitted-confluence", str(root / "confluence.json"),
                                     "--output", str(root / "out")]):
                main()
            html = (root / "out/2026-08.html").read_text()
            self.assertNotIn("<script>", html)
            self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
