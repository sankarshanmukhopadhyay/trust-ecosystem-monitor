import unittest
from unittest.mock import patch

from trust_ecosystem_monitor.monthly import month_bounds, previous_completed_month, in_month, collect_month, render_markdown
from trust_ecosystem_monitor.monthly_compare import compare, render_markdown as render_comparison
from trust_ecosystem_monitor.monthly_continuity import continuity


class MonthlyTests(unittest.TestCase):
    def test_month_boundary(self):
        bounds = month_bounds("2026-09")
        self.assertTrue(in_month("2026-09-30T23:59:59Z", bounds))
        self.assertFalse(in_month("2026-10-01T00:00:00Z", bounds))
        self.assertFalse(in_month(None, bounds))

    def test_previous_completed_month_uses_utc_calendar_boundary(self):
        import datetime as dt
        self.assertEqual(
            previous_completed_month(dt.datetime(2026, 10, 1, 0, 0, tzinfo=dt.timezone.utc)),
            "2026-09",
        )
        self.assertEqual(
            previous_completed_month(dt.datetime(2026, 1, 31, 23, 59, tzinfo=dt.timezone.utc)),
            "2025-12",
        )
        with self.assertRaises(ValueError):
            previous_completed_month(dt.datetime(2026, 10, 1, 0, 0))

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
        result = collect_month("trustoverip", "2026-08", "test-token", max_pages=25)
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual(result["collection_budget"]["max_pages_per_endpoint"], 25)
        self.assertTrue(all(call.kwargs.get("max_pages") == 25 for call in pages.call_args_list))
        self.assertEqual(result["external_sources"]["lfx"], "not_checked")
        self.assertTrue(result["coverage_complete"])
        self.assertIn("https://github.com/trustoverip/example/issues/3", render_markdown(result))

    def test_comparison_is_evidence_only(self):
        first = {"ecosystem": "trustoverip", "period": "2026-08", "coverage_complete": True, "evidence": [{"repository": "trustoverip/a", "event": "opened", "url": "https://github.com/trustoverip/a/issues/1"}]}
        second = {"ecosystem": "trustoverip", "period": "2026-09", "coverage_complete": False, "evidence": []}
        result = compare(first, second)
        self.assertEqual(result["repositories"][0]["earlier"]["opened"], 1)
        self.assertIn("incomplete", render_comparison(result))
        with self.assertRaises(ValueError):
            compare(second, first)

    def test_continuity_with_shared_item(self):
        first = {"ecosystem": "trustoverip", "period": "2026-08", "coverage_complete": True, "evidence": [{"repository": "trustoverip/a", "url": "https://github.com/trustoverip/a/issues/1"}]}
        second = {"ecosystem": "trustoverip", "period": "2026-09", "coverage_complete": True, "evidence": [{"repository": "trustoverip/a", "url": "https://github.com/trustoverip/a/issues/1"}]}
        self.assertEqual(continuity(first, second)[0]["classification"], "continuing_observed")
        second["coverage_complete"] = False
        self.assertEqual(continuity(first, second)[0]["classification"], "evidence_insufficient")

    @patch("trust_ecosystem_monitor.monthly.github_pages")
    def test_discovery_failure_is_not_complete(self, pages):
        pages.side_effect = RuntimeError("pagination limit")
        result = collect_month("trustoverip", "2026-09", "token")
        self.assertFalse(result["coverage_complete"])
        self.assertEqual(result["evidence"], [])
        self.assertIn("discovery", result["coverage"][0])

    @patch("trust_ecosystem_monitor.monthly.github_pages")
    def test_prefix_scope(self, pages):
        pages.side_effect = [
            iter([{"full_name": "trustoverip/dtgwg-example"}, {"full_name": "trustoverip/admin"}]),
            iter([]),
            iter([]),
        ]
        result = collect_month("trustoverip", "2026-09", "token", prefixes=["dtgwg-"])
        self.assertEqual([row["repository"] for row in result["coverage"]], ["trustoverip/dtgwg-example"])
        self.assertTrue(result["coverage_complete"])

    def test_invalid_collection_budget_fails_closed(self):
        for value in (0, 101, "25"):
            with self.assertRaises(ValueError):
                collect_month("trustoverip", "2026-08", "token", max_pages=value)

    def test_explicit_repository_scope_rejects_cross_org(self):
        with self.assertRaises(ValueError):
            collect_month("trustoverip", "2026-08", "token", ["other/a"])

    @patch("trust_ecosystem_monitor.monthly.github_pages")
    def test_partial_failure_is_visible(self, pages):
        pages.side_effect = [
            iter([{"full_name": "trustoverip/example"}]),
            ValueError("bad source"),
            iter([]),
        ]
        result = collect_month("trustoverip", "2026-08", "test-token")
        self.assertFalse(result["coverage_complete"])
        self.assertIn("unavailable", result["coverage"][0]["issues"])


if __name__ == "__main__":
    unittest.main()
