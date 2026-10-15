"""Diagnostic Confluence structure parsing tests."""
import unittest

from trust_ecosystem_monitor.toip_confluence_structure import extract_structure, synthesize_diagnostic_evidence


SYNTHETIC_CONFLUENCE = """
<h1>DTWG working session</h1>
<p>Standing agenda and meeting logistics are present, but this fixture does not
prove that a meeting occurred.</p>
<h2>Agenda</h2>
<table>
  <tr><th>Topic</th><th>Resource</th><th>Status wording</th></tr>
  <tr>
    <td>Delegation authority model</td>
    <td><a href="https://github.com/trustoverip/dtgwg-cred-spec/issues/45">Credential issue</a>
        and <a href="https://www.w3.org/TR/vc-data-model-2.0/">VC Data Model</a></td>
    <td>Decision wording appears here, but authority is not established.</td>
  </tr>
</table>
<div class="expand-container" data-macro-name="expand">
  <h3>Nested notes</h3>
  <p>Proposal language references an implementation option and a follow-up
  pull request <a href="https://github.com/trustoverip/dtgwg-cred-spec/pull/52">PR 52</a>.</p>
</div>
"""


EDGE_CASE_CONFLUENCE = """
<h2>Agenda resources</h2>
<div class="panel macro-container" data-macro-name="panel">
  <p>Meeting notes mention a decision, but neither is established.</p>
  <table>
    <tr><th>Item</th><th>Links</th></tr>
    <tr><td>Authority</td><td>
      <a href="/wiki/spaces/HOME/pages/22970381/Related">Related page</a>
      <a href="https://github.com/trustoverip/dtgwg-cred-spec/issues/45#issuecomment-1">Issue 45</a>
      <a href="https://github.com/trustoverip/dtgwg-cred-spec/issues/45">Issue 45 duplicate</a>
      <a href="https://evil.example.org/private">Disallowed</a>
    </td></tr>
  </table>
</div>
"""


class ConfluenceStructureTests(unittest.TestCase):
    def parse(self):
        return extract_structure(
            SYNTHETIC_CONFLUENCE,
            page_id="22970380",
            source_url="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22970380/Example",
            page_version=7,
        )

    def test_extracts_diagnostic_blocks_for_tables_and_macro_like_content(self):
        result = self.parse()
        self.assertEqual(result["admission_state"], "diagnostic_only")
        self.assertEqual(result["summary_method"], "diagnostic_confluence_structure_v1")
        self.assertIn("no meeting", result["disclosure"].lower())
        kinds = {block["block_kind"] for block in result["blocks"]}
        self.assertIn("table_row", kinds)
        self.assertIn("macro_like_block", kinds)

    def test_links_are_associated_with_structural_blocks(self):
        result = self.parse()
        table_rows = [b for b in result["blocks"] if b["block_kind"] == "table_row"]
        self.assertTrue(any("dtgwg-cred-spec/issues/45" in str(b["github_references"]) for b in table_rows))
        self.assertTrue(any("w3.org/TR/vc-data-model-2.0/" in str(b["external_references"]) for b in table_rows))
        macro_blocks = [b for b in result["blocks"] if b["block_kind"] == "macro_like_block"]
        self.assertTrue(any("dtgwg-cred-spec/pull/52" in str(b["github_references"]) for b in macro_blocks))

    def test_structural_blocks_preserve_source_basis_and_limits(self):
        result = self.parse()
        for block in result["blocks"]:
            self.assertRegex(block["text_basis_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(block["admission_state"], "diagnostic_only")
            self.assertIn("no_decision_inferred", block["interpretation_limits"])
            self.assertIn("no_source_publication_rights_inferred", block["interpretation_limits"])
            self.assertNotIn("summary", block)
            self.assertNotIn("decision", block.get("outcome_state", ""))

    def test_decision_and_meeting_language_are_unsupported_signals_not_claims(self):
        result = self.parse()
        signals = {signal for block in result["blocks"] for signal in block["language_signals"]}
        unsupported = {claim for block in result["blocks"] for claim in block["unsupported_claims"]}
        self.assertIn("decision_like_language", signals)
        self.assertIn("meeting_like_language", signals)
        self.assertIn("decision_or_adoption_not_established", unsupported)
        self.assertIn("meeting_occurrence_not_established", unsupported)
        self.assertNotIn("decision_established", unsupported)
        self.assertNotIn("meeting_held", unsupported)

    def test_edge_case_links_and_macro_table_structure_fail_closed(self):
        result = extract_structure(
            EDGE_CASE_CONFLUENCE,
            page_id="22970381",
            source_url="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22970381/Edge",
            page_version=8,
        )
        self.assertEqual(result["admission_state"], "diagnostic_only")
        blocks = result["blocks"]
        self.assertTrue(any(b["block_kind"] == "macro_like_block" for b in blocks))
        self.assertTrue(any(b["block_kind"] == "table_row" for b in blocks))
        links = [link for block in blocks for link in block["links"]]
        self.assertIn("https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22970381/Related", links)
        self.assertEqual(sum("dtgwg-cred-spec/issues/45" in link for link in links), 2)
        self.assertFalse(any("evil.example.org" in link for link in links))

    def test_diagnostic_synthesis_is_source_linked_without_source_text(self):
        structure = self.parse()
        synthesis = synthesize_diagnostic_evidence(structure)
        self.assertEqual(synthesis["admission_state"], "diagnostic_only")
        self.assertEqual(synthesis["claim_state"], "not_admitted")
        self.assertEqual(synthesis["synthesis_method"], "diagnostic_evidence_handoff_v1")
        self.assertEqual(synthesis["page_id"], "22970380")
        self.assertEqual(synthesis["page_version"], 7)
        self.assertTrue(synthesis["items"])
        for item in synthesis["items"]:
            self.assertEqual(item["admission_state"], "diagnostic_only")
            self.assertEqual(item["claim_state"], "not_admitted")
            self.assertRegex(item["basis_sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn("text", item)
            self.assertNotIn("excerpt", item)
        unsupported = {
            claim for item in synthesis["items"] for claim in item["unsupported_claims"]
        }
        self.assertIn("decision_or_adoption_not_established", unsupported)
        self.assertIn("meeting_occurrence_not_established", unsupported)

    def test_diagnostic_synthesis_rejects_admitted_or_malformed_input(self):
        structure = self.parse()
        structure["admission_state"] = "admitted"
        with self.assertRaises(ValueError):
            synthesize_diagnostic_evidence(structure)
        structure = self.parse()
        structure["blocks"][0]["text_basis_sha256"] = "bad"
        with self.assertRaises(ValueError):
            synthesize_diagnostic_evidence(structure)

    def test_invalid_source_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            extract_structure(SYNTHETIC_CONFLUENCE, page_id="abc", source_url="https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/1")
        with self.assertRaises(ValueError):
            extract_structure(SYNTHETIC_CONFLUENCE, page_id="1", source_url="http://example.com/insecure")


if __name__ == "__main__":
    unittest.main()
