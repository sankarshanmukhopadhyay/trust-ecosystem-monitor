"""Offline experimental combined-page contract tests."""
import tempfile
import unittest
from pathlib import Path
from trust_ecosystem_monitor.toip_experimental_combined import render, publish


class ExperimentalCombinedTests(unittest.TestCase):
    def setUp(self):
        self.cf = {"month": "2026-08", "coverage": "sample_only",
                   "resolved_space_ids": ["22970380"], "sample_count": 22,
                   "total_size": 22, "missing_space_count": 0}
        self.gh = {"period": "2026-08", "evidence": [
            {"url": "https://github.com/trustoverip/test/issues/1",
             "occurred_at": "2026-08-10T00:00:00Z", "title": "Test issue"}]}

    def test_experimental_disclosure_and_provenance(self):
        page = render(self.gh, self.cf)
        self.assertIn("Experimental; non-authoritative", page)
        self.assertIn("22 matching results", page)
        self.assertIn("sample only", page)
        self.assertIn("No verified page-to-GitHub", page)
        self.assertIn("https://github.com/trustoverip/test/issues/1", page)
        self.assertNotIn("publication_admitted", page)

    def test_rejects_unverified_space(self):
        self.cf["resolved_space_ids"] = []
        with self.assertRaises(ValueError):
            render(self.gh, self.cf)

    def test_rejects_wrong_month(self):
        self.cf["month"] = "2026-09"
        with self.assertRaises(ValueError):
            render(self.gh, self.cf)

    def test_rejects_missing_coverage(self):
        self.cf["coverage"] = "unavailable"
        with self.assertRaises(ValueError):
            render(self.gh, self.cf)

    def test_escapes_untrusted_titles(self):
        self.gh["evidence"][0]["title"] = "<script>alert(1)</script>"
        page = render(self.gh, self.cf)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
