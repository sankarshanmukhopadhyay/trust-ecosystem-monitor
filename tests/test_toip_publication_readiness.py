"""Local publication checks must reject missing pages and broken links."""
import tempfile
import unittest
from pathlib import Path
from trust_ecosystem_monitor.toip_publication_readiness import check, REQUIRED


class PublicationReadinessTests(unittest.TestCase):
    def test_missing_pages_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(any("Missing required page" in error for error in check(Path(temp))))

    def test_broken_local_links_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in REQUIRED:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('<!doctype html><html><a href="missing.html">broken</a>LFX Confluence GitHub Pending / deferred publication rights</html>', encoding="utf-8")
            self.assertTrue(any("Broken local link" in error for error in check(root)))

    def test_minimal_valid_site(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in REQUIRED:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('<!doctype html><html><a href="index.html">self</a>LFX Confluence GitHub Pending / deferred publication rights</html>', encoding="utf-8")
            self.assertEqual(check(root), [])


if __name__ == "__main__":
    unittest.main()
