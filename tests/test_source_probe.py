"""Tests for the bounded, public-only source reachability diagnostic."""
import io
import unittest
from urllib.error import HTTPError, URLError

from trust_ecosystem_monitor.source_probe import probe


class Response:
    status = 200
    headers = {"Content-Type": "application/json; charset=utf-8"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return b"{}"


class SourceProbeTests(unittest.TestCase):
    def test_success_reports_only_metadata(self):
        result = probe("test", "https://example.org", opener=lambda req, timeout: Response())
        self.assertEqual(result["status"], "reachable")
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["content_type"], "application/json")
        self.assertNotIn("body", result)
        self.assertNotIn("credentials", result)

    def test_http_unauthorized_is_not_declared_source_not_authorized(self):
        def reject(req, timeout):
            raise HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"secret"))
        result = probe("test", "https://example.org", opener=reject)
        self.assertEqual(result["status"], "http_error")
        self.assertEqual(result["http_status"], 401)
        self.assertNotIn("secret", str(result))

    def test_transport_error_has_no_false_http_status(self):
        def fail(req, timeout):
            raise URLError("blocked")
        result = probe("test", "https://example.org", opener=fail)
        self.assertEqual(result["status"], "transport_error")
        self.assertIsNone(result["http_status"])
        self.assertEqual(result["error_type"], "URLError")


if __name__ == "__main__":
    unittest.main()
