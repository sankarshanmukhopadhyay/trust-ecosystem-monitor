"""Historical search diagnostic must never imply complete activity coverage."""
import json
import unittest
from urllib.error import HTTPError

from trust_ecosystem_monitor.confluence_search import search_month, resolve_space


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return json.dumps(self.payload).encode("utf-8")


class SearchTests(unittest.TestCase):
    def test_month_query_and_metadata_only(self):
        requests = []
        def opener(req, timeout):
            requests.append(req.full_url)
            return Response({"results": [{"title": "Private title", "content": "secret"}], "totalSize": 3, "_links": {"next": "/wiki/rest/api/content/search?start=25"}})
        result = search_month("2026-08", opener=opener, max_batches=1)
        self.assertIn("lastmodified", requests[0])
        self.assertIn("2026-08-01", requests[0])
        self.assertIn("2026-09-01", requests[0])
        self.assertEqual(result["sample_count"], 1)
        self.assertEqual(result["total_size"], 3)
        self.assertEqual(result["coverage"], "sample_only")
        self.assertNotIn("secret", str(result))
        self.assertNotIn("Private title", str(result))

    def test_space_keys_aggregate_without_page_identifiers(self):
        payload = {"results": [
            {"title": "confidential", "content": {"space": {"key": "TOIP"}, "id": "private-123"}},
            {"content": {"space": {"key": "TOIP"}}},
            {"content": {"space": {"key": "OTHER"}}},
        ], "_links": {}}
        result = search_month("2026-09", opener=lambda req, timeout: Response(payload))
        self.assertEqual(result["observed_space_keys"], ["OTHER", "TOIP"])
        self.assertFalse(result["scope_verified"])
        self.assertNotIn("confidential", str(result))
        self.assertNotIn("private-123", str(result))

    def test_alternate_top_level_space_and_field_shapes(self):
        payload = {"results": [
            {"space": {"key": "PUBLIC"}, "title": "do not retain"},
            {"content": {"space": {"key": "OTHER"}}},
            {"resultGlobalContainer": {"title": "not a space"}},
        ], "_links": {}}
        result = search_month("2026-09", opener=lambda req, timeout: Response(payload))
        self.assertEqual(result["observed_space_keys"], ["OTHER", "PUBLIC"])
        self.assertEqual(result["missing_space_count"], 1)
        self.assertEqual(result["space_key_origins"], ["content.space", "result.space"])
        self.assertNotIn("do not retain", str(result))
        self.assertFalse(result["scope_verified"])

    def test_public_page_metadata_resolves_space_id(self):
        def opener(req, timeout):
            self.assertEqual(req.full_url, "https://lf-toip.atlassian.net/wiki/api/v2/pages/123")
            return Response({"id": "123", "spaceId": "456", "body": {"storage": "must not leak"}})
        self.assertEqual(resolve_space("123", opener=opener), ("456", "resolved"))
        self.assertEqual(resolve_space("../123", opener=opener), (None, "invalid_id"))

    def test_lookup_denial_and_identity_mismatch(self):
        def denied(req, timeout):
            raise HTTPError(req.full_url, 403, "Forbidden", {}, None)
        self.assertEqual(resolve_space("123", opener=denied)[1], "not_authorized")
        self.assertEqual(resolve_space("123", opener=lambda req, timeout: Response({"id": "999", "spaceId": "456"}))[1], "identity_mismatch")

    def test_month_resolves_unmapped_space_without_publishing_page_id(self):
        def opener(req, timeout):
            if "/api/v2/pages/" in req.full_url:
                return Response({"id": "123", "spaceId": "456"})
            return Response({"results": [{"content": {"id": "123"}, "resultGlobalContainer": {"title": "secret"}}], "_links": {}})
        result = search_month("2026-08", opener=opener, resolve_missing=True)
        self.assertEqual(result["resolved_space_ids"], ["456"])
        self.assertEqual(result["metadata_lookup_status"], {"resolved": 1})
        self.assertEqual(result["missing_space_count"], 0)
        self.assertFalse(result["scope_verified"])
        self.assertNotIn("secret", str(result))
        self.assertNotIn("123", str(result))

    def test_http_denial_is_unavailable(self):
        def opener(req, timeout):
            raise HTTPError(req.full_url, 403, "Forbidden", {}, None)
        result = search_month("2026-09", opener=opener)
        self.assertEqual(result["coverage"], "unavailable")
        self.assertEqual(result["http_status"], 403)

    def test_two_batches(self):
        payloads = [
            {"results": [{"id": "1"}], "totalSize": 2, "_links": {"next": "/wiki/rest/api/search?start=1"}},
            {"results": [{"id": "2"}], "totalSize": 2, "_links": {}},
        ]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return Response(payloads[len(calls)-1])
        result = search_month("2026-09", opener=opener, max_batches=2)
        self.assertEqual(result["sample_count"], 2)
        self.assertEqual(result["batches_fetched"], 2)
        self.assertFalse(result["next_page_present"])
        self.assertEqual(result["coverage"], "sample_only")

    def test_canonical_content_search_pagination(self):
        responses = [
            {"results": [{"id": "1"}], "_links": {"next": "/wiki/rest/api/content/search?start=25"}},
            {"results": [{"id": "2"}], "_links": {}},
        ]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return Response(responses[len(calls)-1])
        result = search_month("2026-09", opener=opener, max_batches=2)
        self.assertEqual(result["sample_count"], 2)
        self.assertIn("/wiki/rest/api/content/search", calls[1])

    def test_observed_rest_search_pagination(self):
        responses = [
            {"results": [{"id": "1"}], "_links": {"next": "/rest/api/search?start=25"}},
            {"results": [{"id": "2"}], "_links": {}},
        ]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return Response(responses[len(calls)-1])
        result = search_month("2026-09", opener=opener, max_batches=2)
        self.assertEqual(result["sample_count"], 2)
        self.assertIn("/wiki/rest/api/search", calls[1])

    def test_external_next_link_rejected(self):
        result = search_month("2026-08", opener=lambda req, timeout: Response({"results": [], "_links": {"next": "https://example.com/unsafe"}}))
        self.assertEqual(result["reason"], "unsafe_pagination_url")

    def test_invalid_month(self):
        with self.assertRaises(ValueError):
            search_month("2026-13")


if __name__ == "__main__":
    unittest.main()
