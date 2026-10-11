"""Rate-limit failures must be explicit and must not disclose API bodies."""
import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from trust_ecosystem_monitor.engine import GitHubClient


class GitHubRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.client = GitHubClient.__new__(GitHubClient)
        self.client.token = "sensitive-token"

    def error(self, code, headers, body):
        return HTTPError("https://api.github.com/repos/example/repo", code, "error", headers, io.BytesIO(body.encode()))

    def test_installation_rate_exhaustion(self):
        err = self.error(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1791600000"}, "sensitive details")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaisesRegex(RuntimeError, "rate limited") as raised:
                self.client.get("/repos/example/repo")
        self.assertIn("reset_epoch=1791600000", str(raised.exception))
        self.assertNotIn("sensitive", str(raised.exception))

    def test_ordinary_access_denied_is_not_rate_limit(self):
        err = self.error(403, {"X-RateLimit-Remaining": "42"}, "private payload")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaisesRegex(RuntimeError, "HTTP 403") as raised:
                self.client.get("/repos/example/repo")
        self.assertNotIn("rate limited", str(raised.exception))
        self.assertNotIn("private payload", str(raised.exception))

    def test_short_retry_then_success(self):
        err = self.error(429, {"Retry-After": "1"}, "hidden")
        class Success:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"ok": true}'
        with patch("urllib.request.urlopen", side_effect=[err, Success()]) as request:
            with patch("trust_ecosystem_monitor.engine.time.sleep") as sleep:
                self.assertEqual(self.client.get("/repos/example/repo"), {"ok": True})
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_long_retry_fails_without_sleep(self):
        err = self.error(429, {"Retry-After": "3600"}, "hidden")
        with patch("urllib.request.urlopen", side_effect=err) as request:
            with patch("trust_ecosystem_monitor.engine.time.sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "rate limited"):
                    self.client.get("/repos/example/repo")
        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()

    def test_nonfinite_retry_headers_fail_closed_without_sleep(self):
        for header, value in (("Retry-After", "nan"),
                              ("Retry-After", "inf"),
                              ("X-RateLimit-Reset", "nan"),
                              ("X-RateLimit-Reset", "inf")):
            with self.subTest(header=header, value=value):
                err = self.error(429, {header: value}, "hidden")
                with patch("urllib.request.urlopen", side_effect=err) as request:
                    with patch("trust_ecosystem_monitor.engine.time.sleep") as sleep:
                        with self.assertRaisesRegex(RuntimeError, "rate limited"):
                            self.client.get("/repos/example/repo")
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_429_retry_after(self):
        err = self.error(429, {"Retry-After": "60"}, "hidden")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaisesRegex(RuntimeError, "retry_after=60"):
                self.client.get("/repos/example/repo")


if __name__ == "__main__":
    unittest.main()
