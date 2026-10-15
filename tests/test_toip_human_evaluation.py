"""C5 human-evaluation packet preparation tests."""
import unittest

from trust_ecosystem_monitor.toip_annual_state import empty, ingest
from trust_ecosystem_monitor.toip_human_evaluation import build_packet, render_markdown


def github(month):
    return {
        "period": month,
        "coverage_complete": True,
        "collection_scope": "test",
        "evidence": [{
            "id": f"github:trustoverip/dtgwg-example:issues:17:opened",
            "source": "github",
            "repository": "trustoverip/dtgwg-example",
            "kind": "issues",
            "event": "opened",
            "occurred_at": month + "-03T12:00:00Z",
            "url": "https://github.com/trustoverip/dtgwg-example/issues/17",
            "title": "Delegation authority model",
        }],
    }


def content(month):
    return {
        "month": month,
        "coverage": "sample_only",
        "unavailable_count": 0,
        "pages": [{
            "id": "123",
            "title": "DTWG notes",
            "version": 3,
            "page_kind": "substantive",
            "topic_headings": ["Delegation"],
            "github_references": ["https://github.com/trustoverip/dtgwg-example/issues/17"],
            "section_abstracts": [{
                "section": "Delegation",
                "abstract": "This source body text must not be copied into the packet.",
                "basis_sha256": "a" * 64,
            }],
            "discussion_blocks": [],
        }],
    }


class HumanEvaluationPacketTests(unittest.TestCase):
    def state(self):
        state = empty(2026)
        for month in ("2026-08", "2026-09"):
            ingest(
                state, github(month), content(month),
                observed_at=month + "-28T00:00:00Z",
            )
        return state

    def test_packet_is_deterministic_except_generation_timestamp(self):
        one = build_packet(self.state())
        two = build_packet(self.state())
        one.pop("generated_at")
        two.pop("generated_at")
        self.assertEqual(one, two)
        self.assertEqual(one["review_status"], "awaiting_independent_human_review")

    def test_packet_preserves_source_links_without_confluence_body(self):
        packet = build_packet(self.state())
        source = packet["samples"][0]["confluence_sources"][0]
        self.assertEqual(source["meeting_status"], "not_established")
        self.assertFalse(source["body_republished"])
        self.assertNotIn("abstract", source)
        self.assertNotIn("evidence", source)
        self.assertNotIn("This source body text", str(packet))
        self.assertIn("dtgwg-example/issues/17", str(packet))

    def test_rubric_has_all_c5_dimensions(self):
        packet = build_packet(self.state())
        dimensions = {row["dimension"] for row in packet["rubric"]}
        self.assertEqual(dimensions, {
            "relevance", "important_omission", "unsupported_claims",
            "traceability", "reader_comprehension",
        })
        markdown = render_markdown(packet)
        self.assertIn("Packet preparation is not the independent review", markdown)
        self.assertIn("C5 is not complete until an independent human reviewer", markdown)

    def test_missing_month_is_explicit(self):
        packet = build_packet(self.state(), months=("2026-07", "2026-08"))
        self.assertEqual(packet["samples"][0]["status"], "not_retained")
        self.assertEqual(packet["samples"][0]["github_artifacts"], [])


if __name__ == "__main__":
    unittest.main()
