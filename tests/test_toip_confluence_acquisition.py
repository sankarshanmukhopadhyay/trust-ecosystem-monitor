import unittest

from trust_ecosystem_monitor.toip_confluence_acquisition import acquire_metadata


def fixture(path):
    if path.startswith("/wiki/rest/api/content/search?"):
        return {"results": [{"id": "42"}], "size": 1, "_links": {}}
    if path == "/wiki/api/v2/pages/42":
        return {"id": "42", "spaceId": "22970380", "version": {"number": 3}}
    raise AssertionError("unexpected path")


class AcquisitionTests(unittest.TestCase):
    def test_denied_without_both_approvals(self):
        for kwargs in (dict(scope_approved=False, reuse_approved=True),
                       dict(scope_approved=True, reuse_approved=False)):
            with self.assertRaises(PermissionError):
                acquire_metadata("2026-08", approved_space_ids={"22970380"}, fetch=fixture, **kwargs)

    def test_bounded_metadata_only(self):
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=fixture)
        self.assertEqual(data["coverage"], "partial")
        self.assertFalse(data["publication_admitted"])
        self.assertEqual(data["records"][0]["version"], 3)
        self.assertNotIn("title", data["records"][0])

    def test_wrong_space_excluded(self):
        data = acquire_metadata("2026-08", approved_space_ids={"123"},
                                scope_approved=True, reuse_approved=True, fetch=fixture)
        self.assertEqual(data["records"], [])
        self.assertIn("out_of_scope", data["diagnostics"])

    def test_unsafe_pagination(self):
        def bad(path):
            if path.startswith("/wiki/rest/"):
                return {"results": [], "_links": {"next": "https://evil.example/" }}
            raise AssertionError("unexpected")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=bad)
        self.assertIn("unsafe_pagination", data["diagnostics"])

    def test_cycle(self):
        def cycle(path):
            return {"results": [], "_links": {"next": path}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=cycle)
        self.assertIn("pagination_cycle", data["diagnostics"])

    def test_lookup_failure_not_silent(self):
        def fail(path):
            if path.startswith("/wiki/rest/"):
                return {"results": [{"id": "42"}], "_links": {}}
            raise ValueError("offline")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=fail)
        self.assertIn("metadata_lookup_error", data["diagnostics"])


if __name__ == "__main__":
    unittest.main()
