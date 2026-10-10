import unittest

from trust_ecosystem_monitor.monthly_overview import portfolio, render


class MonthlyOverviewTests(unittest.TestCase):
    def test_portfolio_names(self):
        self.assertEqual(portfolio("trustoverip/dtgwg-rahp-tf"), "DTG")
        self.assertEqual(portfolio("trustoverip/tswg-trust-registry-protocol"), "TSWG")
        self.assertEqual(portfolio("trustoverip/unclassified"), "Other / unclassified")

    def test_summary_cites_source_and_limits_inference(self):
        item = {"repository": "trustoverip/dtgwg-example", "event": "merged", "kind": "pull_requests", "id": "one", "title": "Example", "occurred_at": "2026-09-10T00:00:00Z", "url": "https://github.com/trustoverip/dtgwg-example/pull/1"}
        report = render({"period": "2026-09", "collection_scope": "test", "coverage_complete": True, "coverage": [{"repository": "trustoverip/dtgwg-example"}], "evidence": [item]})
        self.assertIn("### DTG", report)
        self.assertIn(item["url"], report)
        self.assertIn("not distinct work items", report)


if __name__ == "__main__":
    unittest.main()
