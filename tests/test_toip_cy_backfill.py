"""CY GitHub-only backfill controls."""
from datetime import datetime, timezone
import json
import tempfile
import unittest
from pathlib import Path

from trust_ecosystem_monitor.toip_cy_backfill import (
    backfill,
    github_only_content,
    month_range,
    previous_completed_month,
)


class ToipCyBackfillTests(unittest.TestCase):
    def test_month_range_is_inclusive_and_validated(self):
        self.assertEqual(month_range("2026-01", "2026-03"), ["2026-01", "2026-02", "2026-03"])
        with self.assertRaises(ValueError):
            month_range("2026-03", "2026-01")

    def test_previous_completed_month_uses_utc_calendar(self):
        self.assertEqual(
            previous_completed_month(datetime(2026, 10, 13, tzinfo=timezone.utc)),
            "2026-09",
        )
        self.assertEqual(
            previous_completed_month(datetime(2026, 1, 2, tzinfo=timezone.utc)),
            "2025-12",
        )

    def test_github_only_content_has_empty_confluence_sources(self):
        content = github_only_content("2026-01")
        self.assertEqual(content["month"], "2026-01")
        self.assertEqual(content["coverage"], "sample_only")
        self.assertEqual(content["pages"], [])
        self.assertIn("GitHub-only", content["boundary"])
        self.assertIn("does not retrieve", content["boundary"])

    def test_backfill_collects_only_missing_months_and_preserves_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            github_dir = root / "github"
            site = root / "site"
            (site / "2026" / "data").mkdir(parents=True)
            (site / "2026" / "data" / "manifest.json").write_text(
                json.dumps({
                    "schema": "tem-cy-intelligence-v1",
                    "year": 2026,
                    "months": {
                        "2026-02": {
                            "period": "2026-02",
                            "observed_at": "2026-03-01T00:00:00+00:00",
                            "observation": {
                                "github": {"scope": "test", "coverage_complete": True, "evidence": []},
                                "confluence": {"coverage": "sample_only", "source_count": 0, "unavailable_count": 0, "sources": []},
                            },
                            "observation_digest": "5cb7d266107142a5a8500ac5aa07890b8cc587c40ac7230f068c38be74f3dc98",
                            "temporal_basis": "retrospective-current-public-source",
                        }
                    },
                    "source_ledger": {},
                    "revision_notices": [],
                }) + "\n",
                encoding="utf-8",
            )
            collected = []
            published = []

            def collector(org, month, token, prefixes=None):
                collected.append((org, month, token, prefixes))
                return {
                    "schema_version": "1",
                    "ecosystem": org,
                    "period": month,
                    "collection_scope": "test",
                    "coverage_complete": True,
                    "evidence": [],
                    "coverage": [],
                    "external_sources": {"confluence": "not_checked", "lfx": "not_checked"},
                }

            def publisher(month, gh_dir, site_dir, *, content_collect, tracked_collect, observed_at=None):
                content = content_collect(month)
                self.assertEqual(content["pages"], [])
                self.assertIn("GitHub-only", content["boundary"])
                self.assertEqual(tracked_collect(["123"]), {"pages": [], "unavailable": []})
                published.append(month)
                return site_dir / "2026" / "index.html"

            summary = backfill(
                org="trustoverip",
                start="2026-01",
                end="2026-03",
                github_dir=github_dir,
                site=site,
                token="token",
                prefixes=["dtgwg-"],
                collector=collector,
                publisher=publisher,
                observed_at="2026-10-13T00:00:00+00:00",
            )

            self.assertEqual(summary["processed"], ["2026-01", "2026-03"])
            self.assertEqual(summary["skipped_existing"], ["2026-02"])
            self.assertEqual(published, ["2026-01", "2026-03"])
            self.assertEqual([item[1] for item in collected], ["2026-01", "2026-03"])
            self.assertTrue((github_dir / "2026-01.json").is_file())
            self.assertTrue((github_dir / "2026-03.md").is_file())


if __name__ == "__main__":
    unittest.main()
