"""Annual report immutability, source-version revisions, idempotence and rendering."""
import json
import tempfile
import unittest
from pathlib import Path
from trust_ecosystem_monitor.toip_annual_state import empty, ingest, validate, write, read
from trust_ecosystem_monitor.toip_annual import render, publish
from trust_ecosystem_monitor.toip_tracked_sources import inspect, MAX_TRACKED

def github(month="2026-08"):
    return {"period": month, "coverage_complete": True,
            "collection_scope": "test repositories", "evidence": [{
                "url": "https://github.com/trustoverip/dtgwg-test/issues/17",
                "title": "Delegation authority question",
                "repository": "trustoverip/dtgwg-test",
                "event": "opened", "kind": "issues",
                "occurred_at": month + "-03T12:00:00Z"}]}

def page(version=1, abstraction="Discussion of delegation"):
    return {"id": "123", "title": "Credential discussion", "version": version,
            "section_abstracts": [{"section": "Authority",
              "abstract": abstraction, "basis_sha256": str(version)*64}],
            "topic_headings": ["Authority"], "github_references": []}

def content(month="2026-08", version=1):
    return {"month": month, "coverage": "sample_only", "pages": [page(version)],
            "unavailable_count": 0}

class AnnualTests(unittest.TestCase):
    def test_append_month_and_idempotent_replay(self):
        state = empty(2026)
        ingest(state, github(), content(), observed_at="2026-10-11T05:00:00Z")
        immutable = json.dumps(state["months"]["2026-08"], sort_keys=True)
        ingest(state, github(), content(), observed_at="2026-10-12T05:00:00Z")
        self.assertEqual(immutable, json.dumps(state["months"]["2026-08"], sort_keys=True))
        self.assertEqual(state["revision_notices"], [])
        self.assertEqual(len(state["source_ledger"]["123"]), 1)

    def test_later_month_source_revision_preserves_old_record(self):
        state = empty(2026)
        ingest(state, github(), content(), observed_at="2026-10-11T05:00:00Z")
        prior = json.dumps(state["months"]["2026-08"], sort_keys=True)
        ingest(state, github("2026-09"), content("2026-09", 2),
               observed_at="2026-11-02T05:00:00Z")
        self.assertEqual(prior, json.dumps(state["months"]["2026-08"], sort_keys=True))
        self.assertEqual(len(state["revision_notices"]), 1)
        self.assertEqual(state["revision_notices"][0]["impact"], "review_required")
        self.assertEqual(len(state["source_ledger"]["123"]), 2)
        page_html = render(state)
        self.assertIn("Subsequent source revisions", page_html)
        self.assertIn("2026-08", page_html)
        self.assertIn("2026-09", page_html)
        self.assertIn("<table>", page_html)

    def test_tracked_reinspection_not_new_month_activity(self):
        state = empty(2026)
        ingest(state, github(), content(), observed_at="2026-10-11T05:00:00Z")
        September = {"month": "2026-09", "coverage": "sample_only", "pages": [],
                     "unavailable_count": 0}
        ingest(state, github("2026-09"), September,
               tracked_pages=[page(3)], observed_at="2026-11-02T05:00:00Z")
        self.assertEqual(state["months"]["2026-09"]["observation"]["confluence"]["source_count"], 0)
        self.assertEqual(len(state["revision_notices"]), 1)

    def test_tracked_reinspection_bound_is_enforced(self):
        self.assertEqual(MAX_TRACKED, 80)
        with self.assertRaises(ValueError):
            inspect([str(i) for i in range(MAX_TRACKED + 1)])

    def test_reobservation_notice_without_overwrite(self):
        state = empty(2026)
        ingest(state, github(), content(), observed_at="2026-10-11T05:00:00Z")
        original = state["months"]["2026-08"]["observation_digest"]
        ingest(state, github(), content(version=4), observed_at="2026-10-12T05:00:00Z")
        self.assertEqual(state["months"]["2026-08"]["observation_digest"], original)
        self.assertEqual({n["kind"] for n in state["revision_notices"]},
                         {"month_reobservation", "source_version_change"})

    def test_corrupted_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            state = empty(2026)
            ingest(state, github(), content(), observed_at="2026-10-11T05:00:00Z")
            write(path, state)
            self.assertEqual(read(path, 2026), state)
            state["months"]["2026-08"]["observation"]["github"]["evidence"] = []
            with self.assertRaises(ValueError):
                validate(state)

    def test_publish_replay_index_and_tracked_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gh = root / "github"
            gh.mkdir()
            (gh / "2026-08.json").write_text(json.dumps(github()), encoding="utf-8")
            (gh / "2026-09.json").write_text(json.dumps(github("2026-09")), encoding="utf-8")
            site = root / "toip"
            site.mkdir()
            (site / "index.html").write_text("<html><main>Index</main></html>", encoding="utf-8")
            first = publish("2026-08", gh, site, content_collect=lambda m: content(m),
                            tracked_collect=lambda ids: {"pages": [], "unavailable": []},
                            observed_at="2026-10-11T05:00:00Z")
            self.assertTrue(first.is_file())
            self.assertIn("2026/", (site / "index.html").read_text())
            seen = []
            def reread(ids):
                seen.extend(ids)
                return {"pages": [page(2)], "unavailable": []}
            publish("2026-09", gh, site, content_collect=lambda m: {
                "month": m, "coverage": "sample_only", "pages": []},
                tracked_collect=reread, observed_at="2026-11-02T05:00:00Z")
            self.assertEqual(seen, ["123"])
            report = (site / "2026" / "index.html").read_text()
            self.assertIn("2026-08", report)
            self.assertIn("2026-09", report)
            self.assertIn("source version", report.lower())
            self.assertEqual((site / "index.html").read_text().count('href="2026/"'), 1)

    def test_replay_idempotence_operator_guidance_is_bound_to_current_invariants(self):
        guide = Path("docs/toip-monthly-replay-idempotence.md").read_text(encoding="utf-8")
        self.assertIn("same-month rerun", guide.lower())
        self.assertIn("observation digest remains unchanged", guide)
        self.assertIn("month_reobservation", guide)
        self.assertIn("revision notices", guide.lower())
        self.assertIn("generated-observations promotion", guide)
        self.assertIn("must not introduce new Confluence admission, LFX, Zoom", guide)

    def test_workflows_preserve_manual_budget_and_periodic_update(self):
        historical = Path(".github/workflows/monthly-prototype.yml").read_text()
        scheduled = Path(".github/workflows/monthly-intelligence.yml").read_text()
        backfill = Path(".github/workflows/toip-cy-backfill.yml").read_text()
        self.assertIn("toip_annual", historical)
        self.assertIn("toip_annual", scheduled)
        self.assertIn("schedule:", scheduled)
        self.assertNotIn("  push:", scheduled)
        self.assertNotIn("  schedule:", historical)
        self.assertIn("previous_completed_month", scheduled)
        self.assertIn("--max-pages 25", scheduled)
        for workflow in (historical, scheduled, backfill):
            self.assertIn("--force-with-lease=refs/heads/generated-observations:$parent", workflow)
            self.assertIn("concurrency:", workflow)
            self.assertIn("group: pages", workflow)

    def test_monthly_operations_guide_is_bound_to_operational_guards(self):
        guide = Path("docs/toip-monthly-operations.md").read_text(encoding="utf-8")
        self.assertIn("previous_completed_month", guide)
        self.assertIn("--max-pages 25", guide)
        self.assertIn("MAX_TRACKED = 80", guide)
        self.assertIn("--force-with-lease=refs/heads/generated-observations:$parent", guide)
        self.assertIn("30 days", guide)
        self.assertIn("month_reobservation", guide)
        self.assertIn("Do not force-push", guide)

if __name__ == "__main__":
    unittest.main()
