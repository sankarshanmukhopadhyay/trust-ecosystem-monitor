import unittest

from trust_ecosystem_monitor.monthly_meetings import empty_manifest
from trust_ecosystem_monitor.monthly_merge_sources import combine


class MergeSourcesTests(unittest.TestCase):
    def test_combines_sources_without_duplicate_evidence(self):
        a = empty_manifest("2026-09", lfx="partial")
        record = {"source": "lfx", "url": "https://example.org/m/1", "occurred_at": "2026-09-12T00:00:00Z", "group": "DTG", "classification": "discussion", "summary": "Meeting listed"}
        a["records"] = [record, record]
        b = empty_manifest("2026-09", confluence="partial")
        result = combine("2026-09", [a, b])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["coverage"], {"lfx": "partial", "confluence": "partial"})

    def test_rejects_mixed_periods(self):
        with self.assertRaises(ValueError):
            combine("2026-09", [empty_manifest("2026-08")])


if __name__ == "__main__":
    unittest.main()
