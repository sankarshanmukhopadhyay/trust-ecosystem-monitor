import unittest

from trust_ecosystem_monitor.monthly_lfx import convert_lfx_export


class LfxImportTests(unittest.TestCase):
    def test_filters_period_and_deduplicates(self):
        item = {"started_at": "2026-09-12T14:00:00Z", "url": "https://example.org/meeting/1", "group": "DTG", "title": "Weekly call"}
        result = convert_lfx_export({"meetings": [item, item, {**item, "started_at": "2026-08-12T14:00:00Z"}]}, "2026-09")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["classification"], "discussion")
        self.assertEqual(result["coverage"]["lfx"], "partial")

    def test_rejects_unverifiable_meeting(self):
        with self.assertRaises(ValueError):
            convert_lfx_export({"meetings": [{"started_at": "2026-09-12", "url": "http://example.org", "group": "DTG", "title": "Call"}]}, "2026-09")


if __name__ == "__main__":
    unittest.main()
