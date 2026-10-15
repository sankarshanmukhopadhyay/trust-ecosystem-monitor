"""Evidence-only longitudinal GitHub subject timeline tests."""
import unittest

from trust_ecosystem_monitor.toip_annual_state import empty, ingest
from trust_ecosystem_monitor.toip_subject_timeline import (
    build_timelines,
    canonical_subject,
    render_timelines,
)


def event(url, event_name, occurred_at, *, title="Delegation authority model"):
    path = url.split("https://github.com/", 1)[1].split("/")
    owner, repo, path_kind, number = path
    kind = "issues" if path_kind == "issues" else "pull_requests"
    return {
        "id": f"github:{owner}/{repo}:{kind}:{number}:{event_name}",
        "source": "github",
        "repository": f"{owner}/{repo}",
        "kind": kind,
        "event": event_name,
        "occurred_at": occurred_at,
        "url": url,
        "title": title,
    }


def github(month, rows):
    return {
        "period": month,
        "coverage_complete": True,
        "collection_scope": "test repositories",
        "evidence": rows,
    }


def content(month):
    return {
        "month": month,
        "coverage": "sample_only",
        "pages": [],
        "unavailable_count": 0,
    }


class SubjectTimelineTests(unittest.TestCase):
    def state(self):
        state = empty(2026)
        issue1 = "https://github.com/trustoverip/dtgwg-example/issues/17"
        issue2 = "https://github.com/trustoverip/dtgwg-example/issues/18"
        ingest(
            state,
            github("2026-08", [
                event(issue1, "opened", "2026-08-03T12:00:00Z"),
                event(issue2, "opened", "2026-08-04T12:00:00Z"),
            ]),
            content("2026-08"),
            observed_at="2026-09-02T00:00:00Z",
        )
        ingest(
            state,
            github("2026-09", [
                event(issue1, "closed", "2026-09-10T12:00:00Z"),
            ]),
            content("2026-09"),
            observed_at="2026-10-02T00:00:00Z",
        )
        return state

    def test_exact_url_identity_builds_longitudinal_timeline(self):
        timelines = build_timelines(self.state())
        self.assertEqual(len(timelines), 2)
        issue17 = next(t for t in timelines if t["number"] == 17)
        self.assertEqual(issue17["transition_count"], 2)
        self.assertEqual(
            [t["event"] for t in issue17["transitions"]],
            ["opened", "closed"],
        )
        self.assertEqual(issue17["identity_basis"], "exact_canonical_github_artifact_url")
        self.assertIn("no_resolution_inferred", issue17["interpretation_limits"])

    def test_similar_titles_do_not_merge_separate_artifacts(self):
        timelines = build_timelines(self.state())
        urls = {t["subject_url"] for t in timelines}
        self.assertEqual(urls, {
            "https://github.com/trustoverip/dtgwg-example/issues/17",
            "https://github.com/trustoverip/dtgwg-example/issues/18",
        })
        self.assertEqual(
            next(t for t in timelines if t["number"] == 18)["transition_count"], 1
        )

    def test_render_only_promotes_multi_event_exact_artifacts(self):
        html = render_timelines(self.state())
        self.assertIn("Observed GitHub artifact timelines", html)
        self.assertIn("dtgwg-example #17", html)
        self.assertNotIn("dtgwg-example #18", html)
        self.assertIn("Closure observed; resolution not established", html)
        self.assertIn("Similar titles, shared terms and temporal proximity do not establish identity", html)
        self.assertGreaterEqual(
            html.count("https://github.com/trustoverip/dtgwg-example/issues/17"), 3
        )

    def test_noncanonical_or_mismatched_evidence_fails_closed(self):
        with self.assertRaises(ValueError):
            canonical_subject("https://github.com/trustoverip/example/issues/1?x=1")

        state = empty(2026)
        row = event(
            "https://github.com/trustoverip/dtgwg-example/issues/17",
            "opened",
            "2026-08-03T12:00:00Z",
        )
        row["repository"] = "trustoverip/other"
        ingest(
            state,
            github("2026-08", [row]),
            content("2026-08"),
            observed_at="2026-09-02T00:00:00Z",
        )
        with self.assertRaises(ValueError):
            build_timelines(state)


if __name__ == "__main__":
    unittest.main()
