import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.monthly_meetings import empty_manifest, load_meetings
from trust_ecosystem_monitor.monthly_report import render


class MonthlySourceAwareTests(unittest.TestCase):
    def test_coverage_without_meeting_claims(self):
        github = {
            "period": "2026-08",
            "coverage_complete": True,
            "collection_scope": "explicit repositories: trustoverip/example",
            "evidence": [],
        }
        report = render(github, empty_manifest("2026-08", confluence="not_authorized"))
        self.assertIn("Confluence: not_authorized", report)
        self.assertIn("no conclusions about meeting activity", report)

    def test_curated_claims_remain_classified_and_cited(self):
        github = {
            "period": "2026-09",
            "coverage_complete": False,
            "collection_scope": "test",
            "evidence": [],
        }
        manifest = empty_manifest("2026-09", confluence="partial")
        manifest["records"] = [{
            "source": "confluence",
            "url": "https://example.org/meeting",
            "occurred_at": "2026-09-05T12:00:00Z",
            "classification": "discussion",
            "group": "DTG",
            "summary": "Discussed a possible change",
        }]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meeting.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = render(github, load_meetings(path, "2026-09"))
            self.assertIn("**discussion**", result)
            self.assertIn("https://example.org/meeting", result)
            self.assertNotIn("**decision**", result)

    def test_wrong_period_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meeting.json"
            path.write_text(json.dumps(empty_manifest("2026-08")), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_meetings(path, "2026-09")


if __name__ == "__main__":
    unittest.main()
