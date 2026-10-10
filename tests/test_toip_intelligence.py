import tempfile
import json
import unittest
from pathlib import Path

from trust_ecosystem_monitor.toip_intelligence import publish, month_page, safe_link


class IntelligencePublicationTests(unittest.TestCase):
    def manifest(self, period):
        return {"period": period, "coverage_complete": False,
                "collection_scope": "configured prefixes",
                "evidence": [
                    {"kind": "pull_requests", "event": "opened", "repository": "trustoverip/dtgwg-test",
                     "url": "https://github.com/trustoverip/dtgwg-test/pull/3", "title": "<test>"},
                    {"kind": "pull_requests", "event": "merged", "repository": "trustoverip/dtgwg-test",
                     "url": "https://github.com/trustoverip/dtgwg-test/pull/3", "title": "<test>"}]}

    def test_inference_is_bounded_and_escaped(self):
        html = month_page(self.manifest("2026-08"))
        self.assertIn("opening and merge both observed", html)
        self.assertIn("&lt;test&gt;", html)
        self.assertNotIn("<test>", html)
        self.assertIn("not adoption", html)
        self.assertIn("LFX Calendar/Zoom is pending", html)

    def test_untrusted_links_not_clickable(self):
        self.assertNotIn("<a ", safe_link("https://evil.example/record", "external"))
        self.assertNotIn("<a ", safe_link("javascript:alert(1)", "external"))

    def test_month_pair_and_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = []
            for month in ("2026-08", "2026-09"):
                path = root / (month + ".json")
                path.write_text(json.dumps(self.manifest(month)), encoding="utf-8")
                inputs.append(path)
            publish(inputs, root / "intelligence" / "toip")
            for suffix in ("index.html", "coverage/index.html", "methodology/index.html",
                           "2026-08/index.html", "2026-09/index.html"):
                self.assertTrue((root / "intelligence" / "toip" / suffix).is_file())
            self.assertIn("pending", (root / "intelligence/toip/coverage/index.html").read_text().lower())

    def test_missing_month_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "one.json"
            path.write_text(json.dumps(self.manifest("2026-08")))
            with self.assertRaises(ValueError):
                publish([path], Path(directory) / "out")


if __name__ == "__main__":
    unittest.main()
