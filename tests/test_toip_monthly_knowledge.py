"""Regression tests for bounded, evidence-grounded monthly knowledge."""
import unittest
from trust_ecosystem_monitor.toip_monthly_knowledge import build_developments, render_developments
from trust_ecosystem_monitor.toip_confluence_content_signals import collect
from trust_ecosystem_monitor.toip_experimental_combined import render


def event(name, transition, title="Fix authorization validation"):
    return {"repository": "trustoverip/dtgwg-example", "kind": "pull_requests",
            "url": "https://github.com/trustoverip/dtgwg-example/pull/" + str(name),
            "title": title, "event": transition, "occurred_at": "2026-08-10T12:00:00Z"}


class MonthlyKnowledgeTests(unittest.TestCase):
    def test_lifecycle_consolidation_and_semantics(self):
        data = [event(1, "opened"), event(1, "merged"),
                event(2, "opened", "Improve privacy threat review")]
        developments = build_developments(data)
        self.assertEqual(len(developments), 2)
        merged = next(x for x in developments if x["url"].endswith("/1"))
        self.assertEqual(merged["change"], "PR merge observed")
        self.assertEqual(merged["event_count"], 2)
        self.assertEqual(merged["semantic"], "authority")
        page = render_developments(data)
        self.assertIn("evidence-backed developments", page)
        self.assertIn("authorization", page)
        self.assertIn("not establish", page)

    def test_html_escaping_and_evidence_validation(self):
        page = render_developments([event(1, "opened", "<script>alert(1)</script>")])
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        bad = event(2, "merged")
        bad["url"] = "https://evil.example.org/"
        with self.assertRaises(ValueError):
            render_developments([bad])

    def test_content_signals_bound_by_space_and_source(self):
        class Response:
            def __init__(self, d):
                import json
                self.payload = json.dumps(d).encode()
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, amount):
                return self.payload
        calls = []
        def fake(request, timeout):
            url = request.full_url
            calls.append(url)
            if "/rest/api/search?" in url:
                return Response({"results": [{"content": {"id": "123"}}],
                                 "totalSize": 1, "_links": {}})
            return Response({"id": "123", "spaceId": "22970380",
                             "title": "AIM WG Meeting",
                             "version": {"number": 3, "createdAt": "2026-08-19T00:00:00Z"},
                             "body": {"storage": {"value": "<h2>Discussion of delegation</h2><p>Text not carried into report.</p>"}}})
        result = collect("2026-08", opener=fake)
        self.assertEqual(len(result["pages"]), 1)
        self.assertEqual(result["pages"][0]["topic_headings"], ["Discussion of delegation"])
        self.assertNotIn("Text not carried", str(result))
        self.assertEqual(len(calls), 2)

    def test_confluence_in_render_is_topic_only(self):
        gh = {"period": "2026-08", "evidence": [event(1, "merged")]}
        cf = {"month": "2026-08", "coverage": "sample_only", "resolved_space_ids": ["22970380"],
              "sample_count": 1, "total_size": 1, "missing_space_count": 0}
        signal = {"month": "2026-08", "pages": [{
            "id": "123", "title": "Meeting notes", "version": 3,
            "topic_headings": ["Discussion", "Questions"]}], "unavailable_count": 0}
        html = render(gh, cf, signal)
        self.assertIn("What Confluence records describe", html)
        self.assertIn("Headings identify these recorded topics", html)
        self.assertIn("What changed: evidence-backed developments", html)
        self.assertNotIn("approved decision:", html)


if __name__ == "__main__":
    unittest.main()
