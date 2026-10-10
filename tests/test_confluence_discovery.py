"""Confluence discovery is metadata-only, bounded, and coverage-conservative."""
import io
import json
import unittest

from trust_ecosystem_monitor.confluence_discovery import discover


class Response:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return json.dumps(self.value).encode("utf-8")


class DiscoveryTests(unittest.TestCase):
    def test_metadata_only_sample(self):
        payload = {"results": [{"id": "123", "spaceId": "456", "title": "Private meeting title", "body": {"storage": "secret"}, "createdAt": "2026-08-01", "_links": {"webui": "/wiki/pages/123"}}], "_links": {"next": "/next"}}
        result = discover(opener=lambda req, timeout: Response(payload), limit=1)
        self.assertEqual(result["coverage"], "sample_only")
        self.assertEqual(result["pages"][0]["id"], "123")
        self.assertTrue(result["next_page_present"])
        self.assertNotIn("secret", str(result))
        self.assertNotIn("Private meeting title", str(result))

    def test_unknown_schema_not_complete(self):
        result = discover(opener=lambda req, timeout: Response({"message": "unexpected"}))
        self.assertEqual(result["coverage"], "unavailable")

    def test_pagination_deduplicates(self):
        payloads = [
            {"results": [{"id": "1"}], "_links": {"next": "/wiki/api/v2/pages?cursor=next"}},
            {"results": [{"id": "1"}, {"id": "2"}], "_links": {}},
        ]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return Response(payloads[len(calls) - 1])
        result = discover(opener=opener, limit=2, max_batches=2)
        self.assertEqual([p["id"] for p in result["pages"]], ["1", "2"])
        self.assertEqual(result["batches_fetched"], 2)
        self.assertFalse(result["next_page_present"])
        self.assertEqual(result["coverage"], "sample_only")

    def test_rejects_external_pagination(self):
        payload = {"results": [{"id": "1"}], "_links": {"next": "https://attacker.example/steal"}}
        result = discover(opener=lambda req, timeout: Response(payload), max_batches=2)
        self.assertEqual(result["reason"], "unsafe_next_page_url")

    def test_month_filter_is_explicitly_sample_only(self):
        payload = {"results": [
            {"id": "aug", "createdAt": "2026-08-05T00:00:00Z"},
            {"id": "sep", "createdAt": "2026-09-01T00:00:00Z"},
            {"id": "unknown"},
        ], "_links": {"next": "/wiki/api/v2/pages?cursor=next"}}
        result = discover(opener=lambda req, timeout: Response(payload), month="2026-08")
        self.assertEqual([p["id"] for p in result["pages"]], ["aug"])
        self.assertEqual(result["month_match_count"], 1)
        self.assertEqual(result["unknown_timestamp_count"], 1)
        self.assertEqual(result["coverage"], "sample_only")
        self.assertTrue(result["next_page_present"])

    def test_invalid_month_rejected(self):
        with self.assertRaises(ValueError):
            discover(month="2026-13")

    def test_bounded_limit(self):
        with self.assertRaises(ValueError):
            discover(limit=51)


if __name__ == "__main__":
    unittest.main()
