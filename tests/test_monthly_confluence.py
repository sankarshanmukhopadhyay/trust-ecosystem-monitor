import unittest

from trust_ecosystem_monitor.monthly_confluence import convert_confluence_export


class ConfluenceImportTests(unittest.TestCase):
    def test_filters_period_and_deduplicates_pages(self):
        page = {"updated_at": "2026-09-12T14:00:00Z", "url": "https://example.org/wiki/page/1", "group": "DTG", "title": "Working notes", "version": 3}
        result = convert_confluence_export({"pages": [page, page, {**page, "updated_at": "2026-08-12T14:00:00Z"}]}, "2026-09")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["classification"], "discussion")
        self.assertEqual(result["coverage"]["confluence"], "partial")
        self.assertIn("version 3", result["records"][0]["summary"])

    def test_rejects_missing_timezone(self):
        with self.assertRaises(ValueError):
            convert_confluence_export({"pages": [{"updated_at": "2026-09-12T14:00:00", "url": "https://example.org/page", "group": "DTG", "title": "Notes"}]}, "2026-09")


if __name__ == "__main__":
    unittest.main()
