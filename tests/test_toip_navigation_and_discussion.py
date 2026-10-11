"""Navigation convergence and substantive source-reference intelligence tests."""
import tempfile
import unittest
from pathlib import Path
from trust_ecosystem_monitor.toip_discussion_blocks import extract_discussions
from trust_ecosystem_monitor.toip_navigation import converge, add_to_toip_overview
from trust_ecosystem_monitor.toip_annual_state import empty, ingest
from trust_ecosystem_monitor.toip_annual import render

BODY = ("""
<h2>Antitrust policy</h2><p>Antitrust and intellectual property rights
notice for all members and attendees.</p>
<h2>Welcome / new members</h2><p>We welcomed new members to the community
and reviewed the working group charter in the meeting.</p>
<h2>Delegation protocol options</h2>
<p>The proposal considers whether delegation authority can be represented
as a verifiable credential. The alternative is an external authorization
policy reference. The issue remains open for protocol discussion
<a href="https://github.com/trustoverip/dtgwg-cred-spec/issues/45">Credential issue</a>
and <a href="https://www.w3.org/TR/vc-data-model-2.0/">VC Data Model</a>.</p>
<h2>Current open questions</h2>
<p>Which verifier will evaluate the delegation policy, and how should
credential status updates affect the authorization relationship?</p>
""")

class ConvergenceTests(unittest.TestCase):
    def test_selected_discussions_include_references_beyond_github(self):
        result = extract_discussions(BODY)
        self.assertGreaterEqual(result["text_sections_inspected"], 3)
        blocks = result["sections"]
        self.assertTrue(blocks)
        self.assertFalse(any("Welcome" in x["section"] for x in blocks))
        self.assertFalse(any("Antitrust" in x["section"] for x in blocks))
        assert any("w3.org/TR/vc-data-model-2.0/" in str(x["references"]) for x in blocks)
        self.assertTrue(any("GitHub" not in x["abstract"] and x["references"] for x in blocks))
        self.assertTrue(any("?" in x["abstract"] or "question" in x["abstract"].lower() for x in blocks))
        self.assertEqual(result, extract_discussions(BODY))

    def test_chose_later_substantive_sections_not_first_six(self):
        body = "".join("<h2>Member introductions</h2><p>Our new members discussed "
                       "working group participation details in the introduction session.</p>"
                       for _ in range(10)) + BODY
        blocks = extract_discussions(body)["sections"]
        self.assertTrue(any("Delegation" in x["section"] for x in blocks))
        self.assertFalse(any("introductions" in x["section"].lower() for x in blocks))

    def test_navigation_wip_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "trustoverip").mkdir()
            (root / "trustoverip/index.html").write_text("<html><main>ToIP</main></html>")
            (root / "index.html").write_text('<html><main>Root<p><a href="monthly/index.html">Monthly</a></p><p><a href="intelligence/toip/">Intelligence</a></p></main></html>')
            converge(root)
            converge(root)
            home = (root / "index.html").read_text()
            self.assertNotIn('href="monthly/index.html"', home)
            self.assertNotIn('href="intelligence/toip/"', home)
            toip = (root / "trustoverip/index.html").read_text()
            self.assertEqual(toip.count('href="../intelligence/toip/2026/"'), 1)
            self.assertIn("Work in progress", toip)
            landing = (root / "intelligence/toip/index.html").read_text()
            self.assertIn('href="2026/"', landing)
            self.assertNotIn('href="2026-08/', landing)

    def test_annual_prefers_latest_tracked_discussion_without_changing_month(self):
        state = empty(2026)
        gh = {"period": "2026-08", "evidence": []}
        observed = {"month": "2026-08", "pages": [{
            "id": "12", "title": "Old notes", "version": 1,
            "section_abstracts": [{"section": "General", "abstract": "Original topic",
                                   "basis_sha256": "a" * 64}]}]}
        ingest(state, gh, observed, observed_at="2026-10-11T00:00:00Z")
        newer = {"id": "12", "title": "Old notes", "version": 2,
                 "section_abstracts": [{"section": "Delegation", "abstract": "Later topic",
                                       "basis_sha256": "b" * 64}],
                 "discussion_blocks": extract_discussions(BODY)["sections"]}
        ingest(state, {"period": "2026-09", "evidence": []},
               {"month": "2026-09", "pages": []}, tracked_pages=[newer],
               observed_at="2026-11-02T00:00:00Z")
        html = render(state)
        self.assertIn("Delegation protocol options", html)
        self.assertIn("w3.org", html)
        self.assertIn("Updated interpretation", html)
        self.assertEqual(state["months"]["2026-08"]["observation"]["confluence"]["sources"][0]["version"], 1)

if __name__ == "__main__":
    unittest.main()
