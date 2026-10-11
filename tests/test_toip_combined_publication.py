"""Combined Pages publication must fail closed until both months are admitted."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trust_ecosystem_monitor.toip_combined_publication import publish
from trust_ecosystem_monitor.toip_intelligence import publish as publish_github
from tests.test_toip_combined_report import inputs


class CombinedPublicationTests(unittest.TestCase):
    def prepare(self, root):
        github_dir, admitted_dir, site = (root / "github", root / "admitted",
                                          root / "docs/intelligence/toip")
        github_dir.mkdir()
        admitted_dir.mkdir()
        for month in ("2026-08", "2026-09"):
            gh, cf = inputs()
            gh["period"] = month
            cf["period"] = month
            if month == "2026-09":
                gh["evidence"][0]["occurred_at"] = "2026-09-12T10:00:00Z"
                cf["observations"][0]["occurred_at"] = "2026-09-13T10:00:00Z"
                cf["reviewed_github_observations"][0]["occurred_at"] = "2026-09-12T10:00:00Z"
            (github_dir / (month + ".json")).write_text(json.dumps(gh))
            (admitted_dir / (month + ".json")).write_text(json.dumps(cf))
        site.mkdir(parents=True)
        (site / "index.html").write_text("<html><main>Home</main></html>")
        for month in ("2026-08", "2026-09"):
            (site / month).mkdir()
            (site / month / "index.html").write_text("<html><main>Month</main></html>")
        return github_dir, admitted_dir, site

    def test_both_months_render_and_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            self.assertEqual(publish(gh, cf, site), ["2026-08", "2026-09"])
            self.assertIn('href="2026-08/cross-source.html"',
                          (site / "index.html").read_text())
            for month in ("2026-08", "2026-09"):
                self.assertIn("Admitted Confluence page updates",
                              (site / month / "cross-source.html").read_text())
                self.assertIn('href="cross-source.html"',
                              (site / month / "index.html").read_text())

    def test_missing_destination_shell_fails_before_writing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            (site / "2026-09/index.html").unlink()
            with self.assertRaisesRegex(ValueError, "missing intelligence HTML shell"):
                publish(gh, cf, site)
            self.assertFalse((site / "2026-08/cross-source.html").exists())

    def test_combined_publication_reconciles_github_only_disclosures(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            (site / "index.html").write_text(
                "<html><main>The current public release uses GitHub issue/PR lifecycle evidence; "
                "Confluence discovery is documented but its records are not yet admitted as historical activity."
                "</main></html>")
            (site / "2026-08/index.html").write_text(
                "<html><main>Confluence source identity is verified but historical page activity "
                "is not yet admitted as report evidence.</main></html>")
            publish(gh, cf, site)
            self.assertIn("independently admitted Confluence",
                          (site / "index.html").read_text())
            self.assertNotIn("not yet admitted",
                             (site / "2026-08/index.html").read_text())

    def test_missing_second_month_leaves_site_unmodified(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            (cf / "2026-09.json").unlink()
            with self.assertRaises(FileNotFoundError):
                publish(gh, cf, site)
            self.assertFalse((site / "2026-08/cross-source.html").exists())
            self.assertNotIn("cross-source.html", (site / "index.html").read_text())

    def test_unadmitted_month_fails_without_partial_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            path = cf / "2026-09.json"
            item = json.loads(path.read_text())
            item["publication_admitted"] = False
            path.write_text(json.dumps(item))
            with self.assertRaisesRegex(ValueError, "not admitted"):
                publish(gh, cf, site)
            self.assertFalse((site / "2026-08/cross-source.html").exists())

    def test_missing_observations_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh, cf, site = self.prepare(Path(tmp))
            path = cf / "2026-08.json"
            item = json.loads(path.read_text())
            item["observations"] = []
            path.write_text(json.dumps(item))
            with self.assertRaisesRegex(ValueError, "real admitted"):
                publish(gh, cf, site)


if __name__ == "__main__":
    unittest.main()
