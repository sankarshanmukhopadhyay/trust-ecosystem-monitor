import unittest
from urllib.parse import parse_qs, urlencode, urlsplit

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

    def test_oversized_search_page_is_not_processed(self):
        calls = []
        def oversized(path):
            calls.append(path)
            return {"results": [{"id": str(i)} for i in range(51)], "_links": {}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=oversized)
        self.assertIn("oversized_search_page", data["diagnostics"])
        self.assertEqual(data["records"], [])
        self.assertEqual(data["metadata_lookups_attempted"], 0)
        self.assertFalse(data["search_terminated_normally"])
        self.assertEqual(len(calls), 1)

    def test_inconsistent_search_size_quarantines_page_before_lookups(self):
        for size in (0, 2, True, "1", -1):
            with self.subTest(size=size):
                calls = []
                def inconsistent(path):
                    calls.append(path)
                    if path.startswith("/wiki/rest/api/content/search?"):
                        return {"results": [{"id": "42"}], "size": size, "_links": {}}
                    raise AssertionError("metadata lookup must not occur")
                data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                        scope_approved=True, reuse_approved=True, fetch=inconsistent)
                self.assertEqual(data["records"], [])
                self.assertEqual(data["metadata_lookups_attempted"], 0)
                self.assertEqual(len(calls), 1)
                self.assertIn("inconsistent_search_size", data["diagnostics"])
                self.assertFalse(data["search_terminated_normally"])

    def test_full_search_page_without_next_reports_possible_truncation(self):
        def full(path):
            return {"results": [{"id": str(i)} for i in range(50)], "_links": {}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=full)
        self.assertIn("possible_truncation", data["diagnostics"])
        self.assertFalse(data["historical_completeness_verified"])

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

    def test_rejects_tampered_pagination_query(self):
        def tampered(path):
            if path.startswith("/wiki/rest/"):
                query = parse_qs(urlsplit(path).query)
                query["cql"] = ['space = OTHER']
                query["start"] = ["50"]
                return {"results": [], "_links": {"next": "/wiki/rest/api/content/search?" + urlencode({k: v[0] for k, v in query.items()})}}
            raise AssertionError("unexpected lookup")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=tampered)
        self.assertIn("unsafe_pagination", data["diagnostics"])

    def test_rejects_extra_query_parameters(self):
        def extra(path):
            if path.startswith("/wiki/rest/"):
                return {"results": [], "_links": {"next": path.replace("start=0", "start=50") + "&expand=body.storage"}}
            raise AssertionError("unexpected lookup")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=extra)
        self.assertIn("unsafe_pagination", data["diagnostics"])

    def test_rejects_backward_pagination_without_refetch(self):
        starts = []
        def backward(path):
            start = int(parse_qs(urlsplit(path).query)["start"][0])
            starts.append(start)
            next_start = 50 if start == 0 else 25
            return {"results": [], "_links": {"next": path.replace(
                f"start={start}", f"start={next_start}")}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=backward)
        self.assertEqual(starts, [0, 50])
        self.assertIn("unsafe_pagination", data["diagnostics"])
        self.assertFalse(data["search_terminated_normally"])

    def test_valid_pagination_preserves_scope(self):
        calls = []
        def pages(path):
            if path.startswith("/wiki/rest/"):
                calls.append(path)
                if len(calls) == 1:
                    return {"results": [], "_links": {"next": path.replace("start=0", "start=50")}}
                return {"results": [], "_links": {}}
            raise AssertionError("unexpected lookup")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=pages)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("unsafe_pagination", data["diagnostics"])

    def test_strict_month_and_december_rollover(self):
        for month in ("2026-8", "2026-08extra", "2026-13", "2026-00"):
            with self.subTest(month=month), self.assertRaises(ValueError):
                acquire_metadata(month, approved_space_ids={"22970380"},
                                 scope_approved=True, reuse_approved=True, fetch=fixture)
        observed = []
        def capture(path):
            observed.append(path)
            return {"results": [], "_links": {}}
        acquire_metadata("2026-12", approved_space_ids={"22970380"},
                         scope_approved=True, reuse_approved=True, fetch=capture)
        self.assertIn('2027-01-01', parse_qs(urlsplit(observed[0]).query)["cql"][0])

    def test_retrieval_provenance_and_caller_scope_are_not_source_verification(self):
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True,
                                retrieved_at="2026-10-10T09:00:00+05:30", fetch=fixture)
        self.assertEqual(data["retrieved_at"], "2026-10-10T09:00:00+05:30")
        self.assertEqual(data["search_pages_fetched"], 1)
        self.assertEqual(data["metadata_lookups_attempted"], 1)
        self.assertTrue(data["search_terminated_normally"])
        self.assertTrue(data["scope_caller_approved"])
        self.assertFalse(data["scope_verified"])

    def test_rejects_naive_retrieval_timestamp(self):
        with self.assertRaises(ValueError):
            acquire_metadata("2026-08", approved_space_ids={"22970380"},
                             scope_approved=True, reuse_approved=True,
                             retrieved_at="2026-10-10T09:00:00", fetch=fixture)

    def test_failed_first_search_is_unavailable(self):
        def failed(path):
            raise ValueError("unavailable")
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=failed)
        self.assertEqual(data["coverage"], "unavailable")
        self.assertEqual(data["search_pages_fetched"], 0)
        self.assertFalse(data["search_terminated_normally"])
        self.assertIn("retrieval_error", data["diagnostics"])

    def test_invalid_page_version_excluded(self):
        def invalid_version(path):
            if path.startswith("/wiki/rest/"):
                return {"results": [{"id": "42"}], "_links": {}}
            return {"id": "42", "spaceId": "22970380", "version": {"number": True}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True, fetch=invalid_version)
        self.assertEqual(data["records"], [])
        self.assertIn("missing_version_provenance", data["diagnostics"])

    def test_page_budget_disclosed(self):
        def paginated(path):
            return {"results": [], "_links": {"next": path.replace("start=0", "start=50")}}
        data = acquire_metadata("2026-08", approved_space_ids={"22970380"},
                                scope_approved=True, reuse_approved=True,
                                max_pages=1, fetch=paginated)
        self.assertIn("page_budget_exhausted", data["diagnostics"])
        self.assertFalse(data["search_terminated_normally"])
        self.assertEqual(data["coverage"], "partial")

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
