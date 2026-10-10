import unittest
from unittest.mock import patch

from trust_ecosystem_monitor.monthly import month_bounds, in_month, collect_month, render_markdown


class MonthlyTests(unittest.TestCase):
    def test_month_boundary(self):
        bounds = month_bounds("2026-09")
        self.assertTrue(in_month("2026-09-30T23:59:59Z", bounds))
        self.assertFalse(in_month("2026-10-01T00:00:00Z", bounds))
        self.assertFalse(in_month(None, bounds))

    def test_invalid_month(self):
        for value in ("2026-13", "2026-9", "invalid"):
            with self.assertRaises(ValueError):
                month_bounds(value)

    @patch("trust_ecosystem_monitor.monthly.github_pages")
    def test_collection_and_coverage(self, pages):
        pages.side_effect = [
            iter([{"full_name": "trustoverip/example"}]),
            iter([{"number": 3, "title": "Work", "html_url": "https://github.com/trustoverip/example/issues/3", "created_at": "2026-08-05T00:00:00Z", "closed_at": None}]),
            iter([]),
        ]
        result = collect_month("trustoverip", "2026-08", "test-token")
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual(result["external_sources"]["lfx"], "not_checked")
        self.assertIn("https://github.com/trustoverip/example/issues/3", render_markdown(result))


if __name__ == "__main__":
    unittest.main()
