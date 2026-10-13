"""Negative fixtures for ToIP Confluence discussion extraction.

These tests protect the #122 parser-quality claim that extraction must not turn
administrative pages, charter/member pages or decision-like wording into
established governance outcomes.
"""
import unittest

from trust_ecosystem_monitor.toip_discussion_blocks import extract_discussions


CHARTER_AND_MEMBERSHIP_PAGE = """
<h1>Working Group Charter</h1>
<p>The group charter describes the governance scope, membership process,
chairs, cadence, contribution rules and standing meeting schedule.</p>
<h2>Member list</h2>
<p>Current members and observers are listed for administrative reference.
This page is maintained as a membership and onboarding record.</p>
<h2>Terms of reference</h2>
<p>The terms of reference were approved by the steering committee before
this monitored period and are provided here for background.</p>
"""

DECISION_LIKE_DISCUSSION = """
<h2>Delegation outcome wording</h2>
<p>The delegation protocol issue was discussed and the group agreed that
the authorization relationship needs additional implementation evidence
before any specification change can be treated as resolved
<a href="https://github.com/trustoverip/dtgwg-cred-spec/issues/45">the open issue</a>.</p>
"""

MIXED_ADMIN_AND_TECHNICAL_PAGE = """
<h2>Roll call and attendance</h2>
<p>Attendees, apologies and calendar logistics were reviewed.</p>
<h2>Housekeeping</h2>
<p>Meeting logistics and Zoom recording reminders were repeated.</p>
<h2>Credential status semantics</h2>
<p>The proposal asks whether verifier behavior should change when credential
status changes after presentation. The issue remains open and needs an
implementation test before any specification wording is proposed
<a href="https://www.w3.org/TR/vc-data-model-2.0/">VC Data Model</a>.</p>
"""


class DiscussionNegativeFixtureTests(unittest.TestCase):
    def test_charter_and_membership_page_does_not_become_discussion(self):
        result = extract_discussions(CHARTER_AND_MEMBERSHIP_PAGE)
        self.assertEqual(result["sections"], [])
        self.assertIn("no approval, decision, adoption or outcome inferred", result["disclosure"])

    def test_decision_language_remains_not_established(self):
        result = extract_discussions(DECISION_LIKE_DISCUSSION)
        self.assertEqual(len(result["sections"]), 1)
        block = result["sections"][0]
        self.assertIn("decision_language", block["language_signals"])
        self.assertEqual(block["outcome_state"], "not_established")
        self.assertIn("no_outcome_inferred", block["interpretation_limits"])
        self.assertIn("not an established decision", block["abstract"])
        self.assertNotIn("Decision:", block["abstract"])

    def test_admin_blocks_are_ignored_while_substantive_question_survives(self):
        result = extract_discussions(MIXED_ADMIN_AND_TECHNICAL_PAGE)
        sections = result["sections"]
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["section"], "Credential status semantics")
        self.assertIn("question_language", sections[0]["language_signals"])
        self.assertEqual(sections[0]["outcome_state"], "not_established")
        self.assertFalse(any("Roll call" in item["section"] for item in sections))
        self.assertFalse(any("Housekeeping" in item["section"] for item in sections))

    def test_every_selected_block_carries_interpretation_limits(self):
        result = extract_discussions(MIXED_ADMIN_AND_TECHNICAL_PAGE + DECISION_LIKE_DISCUSSION)
        self.assertTrue(result["sections"])
        for block in result["sections"]:
            self.assertEqual(block["outcome_state"], "not_established")
            self.assertIn("extractive_passage_only", block["interpretation_limits"])
            self.assertIn("no_authority_inferred", block["interpretation_limits"])
            self.assertIn("no_adoption_or_implementation_inferred", block["interpretation_limits"])


if __name__ == "__main__":
    unittest.main()
