import io
import json
import unittest
from urllib.error import HTTPError

from trust_ecosystem_monitor.confluence_space_identity import inspect_space


class Response:
    def __init__(self, data):
        self.payload = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, count): return self.payload[:count]


class SpaceIdentityTests(unittest.TestCase):
    def test_identity_and_scope_remain_separate(self):
        def opener(req, timeout):
            self.assertEqual(req.full_url, "https://lf-toip.atlassian.net/wiki/api/v2/spaces/22970380")
            return Response({"id": "22970380", "key": "HOME", "name": "Public space", "description": "private"})
        result = inspect_space("22970380", opener=opener)
        self.assertTrue(result["identity_verified"])
        self.assertFalse(result["authority_verified"])
        self.assertFalse(result["publication_rights_verified"])
        self.assertNotIn("description", result)

    def test_mismatched_identity(self):
        result = inspect_space("123", opener=lambda req, timeout: Response({"id": "456", "key": "HOME"}))
        self.assertEqual(result["reason"], "identity_mismatch")

    def test_reject_unsafe_identifier(self):
        with self.assertRaises(ValueError):
            inspect_space("../123")

    def test_denied_is_unavailable(self):
        def denied(req, timeout):
            raise HTTPError(req.full_url, 403, "Forbidden", {}, io.BytesIO())
        result = inspect_space("123", opener=denied)
        self.assertEqual(result["http_status"], 403)
        self.assertFalse(result["identity_verified"])


if __name__ == "__main__":
    unittest.main()
