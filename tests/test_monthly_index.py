import unittest

from trust_ecosystem_monitor.monthly_index import REPORTS, render_index


class MonthlyIndexTests(unittest.TestCase):
    def test_all_links_are_present(self):
        page = render_index("2026-10-10 00:00")
        for _, filename in REPORTS:
            self.assertIn(f'href="{filename}"', page)

    def test_evidence_boundary_and_freshness(self):
        page = render_index("2026-10-10 00:00")
        self.assertIn("GitHub-only partial evidence", page)
        self.assertIn("LFX", page)
        self.assertIn("Confluence", page)
        self.assertIn("2026-10-10 00:00 UTC", page)
        self.assertIn("not ToIP-authoritative", page)
