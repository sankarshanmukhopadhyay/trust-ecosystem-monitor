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


EXISTING_DIGEST = "080848931980f9bd5bfbc556a46d68277d4198f21caef04936460e25f2fdb308"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "toip-cy-backfill.yml"


def _write_manifest(site: Path, months: list[str]) -> None:
    (site / "2026" / "data").mkdir(parents=True)
    records = {}
    for month in months:
        records[month] = {
            "period": month,
            "observed_at": "2026-03-01T00:00:00+00:00",
            "observation": {
                "github": {"scope": "test", "coverage_complete": True, "evidence": []},
                "confluence": {"coverage": "sample_only", "source_count": 0, "unavailable_count": 0, "sources": []},
            },
            "observation_digest": EXISTING_DIGEST,
            "temporal_basis": "retrospective-current-public-source",
        }
    (site / "2026" / "data" / "manifest.json").write_text(
        json.dumps({
            "schema": "tem-cy-intelligence-v1",
            "year": 2026,
            "months": records,
            "source_ledger": {},
            "revision_notices": [],
        }) + "\n",
        encoding="utf-8",
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
            summary_path = root / "summary" / "cy-backfill-summary.json"
            _write_manifest(site, ["2026-02"])
            collected = []
            published = []
            logs = []

            def collector(org, month, token, prefixes=None, log=None, progress_state=None):
                collected.append((org, month, token, prefixes))
                if progress_state is not None:
                    progress_state.update({
                        "repository": "trustoverip/dtgwg-example",
                        "endpoint": "pull_requests",
                        "page": 2,
                        "status": "complete",
                        "elapsed_seconds": 1.25,
                    })
                return {
                    "schema_version": "1",
                    "ecosystem": org,
                    "period": month,
                    "collection_scope": "test",
                    "coverage_complete": True,
                    "evidence": [],
                    "coverage": [],
                    "external_sources": {"confluence": "not_checked", "lfx": "not_checked"},
                    "collection_elapsed_seconds": 1.25,
                    "traversal_diagnostics": [{
                        "repository": "trustoverip/dtgwg-example",
                        "endpoint": "pull_requests",
                        "pages_fetched": 2,
                        "items_fetched": 12,
                        "last_page": 2,
                        "elapsed_seconds": 1.25,
                        "status": "complete",
                    }],
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
                summary_path=summary_path,
                log=logs.append,
            )

            self.assertEqual(summary["processed"], ["2026-01", "2026-03"])
            self.assertEqual(summary["skipped_existing"], ["2026-02"])
            self.assertEqual(summary["last_event"], "completed")
            self.assertEqual(published, ["2026-01", "2026-03"])
            self.assertEqual([item[1] for item in collected], ["2026-01", "2026-03"])
            self.assertTrue((github_dir / "2026-01.json").is_file())
            self.assertTrue((github_dir / "2026-03.md").is_file())
            persisted = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["last_event"], "completed")
            self.assertIn("skip 2026-02", "\n".join(logs))
            self.assertIn("collect GitHub evidence for 2026-01", "\n".join(logs))
            self.assertEqual(
                summary["traversal_by_month"]["2026-01"]["last"]["repository"],
                "trustoverip/dtgwg-example",
            )
            self.assertEqual(
                summary["traversal_by_month"]["2026-01"]["steps"][0]["last_page"], 2
            )

    def test_backfill_writes_failure_summary_before_reraising(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            summary_path = root / "summary.json"

            def collector(org, month, token, prefixes=None, log=None, progress_state=None):
                raise RuntimeError("rate budget exhausted")

            with self.assertRaisesRegex(RuntimeError, "rate budget exhausted"):
                backfill(
                    org="trustoverip",
                    start="2026-01",
                    end="2026-01",
                    github_dir=root / "github",
                    site=root / "site",
                    token="token",
                    collector=collector,
                    publisher=lambda *a, **k: root / "index.html",
                    summary_path=summary_path,
                    log=lambda message: None,
                )
            persisted = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["last_event"], "failed")
            self.assertEqual(persisted["failed"][0]["month"], "2026-01")
            self.assertIn("rate budget exhausted", persisted["failed"][0]["error"])
            self.assertEqual(
                persisted["failed"][0]["last_repository"], "trustoverip/dtgwg-example"
            )
            self.assertEqual(persisted["failed"][0]["last_endpoint"], "issues")
            self.assertEqual(persisted["failed"][0]["last_page"], 7)
            self.assertEqual(persisted["failed"][0]["elapsed_seconds"], 3.5)

    def test_workflow_exposes_single_month_operator_mode(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("single_month:", text)
        self.assertIn("args+=(--month", text)
        self.assertIn("args+=(--start", text)
        self.assertIn("args+=(--end", text)
        self.assertIn("--summary monthly-prototype/cy-backfill-summary.json", text)


if __name__ == "__main__":
    unittest.main()
