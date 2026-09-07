import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from toip_monitor.core import classify_kind, classify_portfolio, lifecycle, normalize_event, score_event, validate
from toip_monitor.engine import configure_core
from toip_monitor.findings import apply_dispositions, build_findings, validate_dispositions
from toip_monitor.intelligence import consolidate_change_units, detect_cross_portfolio_seams, detect_lifecycle_changes
from toip_monitor.profile import load_profile

# Core no longer embeds an organization or portfolio taxonomy. Tests that
# exercise the legacy core classification API configure it exactly as the CLI
# does: through the default organization profile.
configure_core(load_profile())


class ClassificationTests(unittest.TestCase):
    def test_portfolio_prefixes(self):
        self.assertEqual(classify_portfolio("dtgwg-zkp-tf"), "DTG")
        self.assertEqual(classify_portfolio("aimwg-tmcp-specification"), "AIMWG")
        self.assertEqual(classify_portfolio("kswg-keri-specification"), "KERI Suite")
        self.assertEqual(classify_portfolio("ctwg-main-glossary"), "CTWG")
        self.assertEqual(classify_portfolio("tswg-trust-registry-protocol"), "TSWG")

    def test_unclassified_is_explicit(self):
        self.assertEqual(classify_portfolio("unexpected-new-project"), "Unclassified")

    def test_kind_detection(self):
        self.assertEqual(classify_kind("dtgwg-zkp-tf"), "task-force")
        self.assertEqual(classify_kind("tswg-tsp-specification"), "specification")
        self.assertEqual(classify_kind("ctwg-main-glossary"), "terminology")

    def test_archived_lifecycle_wins(self):
        repo = {"archived": True, "pushed_at": "2026-08-25T00:00:00Z"}
        self.assertEqual(lifecycle(repo, datetime.now(timezone.utc)), "archived")

    def test_materiality(self):
        self.assertEqual(score_event({"kind": "release", "repo_kind": "repository"}), 5)
        self.assertEqual(score_event({"kind": "pull_request", "state": "merged", "repo_kind": "specification"}), 5)
        self.assertEqual(score_event({"kind": "commit", "repo_kind": "repository"}), 1)

    def test_commit_timestamp_uses_nested_metadata(self):
        repo = {"full_name": "trustoverip/example", "portfolio": "Unclassified", "kind": "repository"}
        item = {"sha": "abc", "html_url": "https://example.test/abc", "commit": {"message": "docs: update", "committer": {"date": "2026-08-25T01:02:03Z"}}}
        event = normalize_event("commit", repo, item)
        self.assertEqual(event["timestamp"], "2026-08-25T01:02:03Z")
        self.assertEqual(event["sha"], "abc")

    def test_change_units_group_numbered_events(self):
        events = [
            {"kind": "issue", "repository": "trustoverip/example", "portfolio": "Test", "repo_kind": "repository", "timestamp": "2026-08-25T01:00:00Z", "title": "Track feature", "url": "https://example.test/issues/7", "number": 7, "materiality": 2},
            {"kind": "pull_request", "repository": "trustoverip/example", "portfolio": "Test", "repo_kind": "repository", "timestamp": "2026-08-25T02:00:00Z", "title": "Implement feature", "url": "https://example.test/pull/7", "number": 7, "state": "merged", "materiality": 4},
        ]
        units = consolidate_change_units(events)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["event_count"], 2)
        self.assertEqual(units[0]["materiality"], 4)

    def test_lifecycle_changes_compare_snapshots(self):
        previous = [{"full_name": "trustoverip/example", "portfolio": "Test", "lifecycle": "active", "default_branch": "main", "url": "https://example.test"}]
        current = [{"full_name": "trustoverip/example", "portfolio": "Test", "lifecycle": "archived", "default_branch": "main", "url": "https://example.test"}]
        changes = detect_lifecycle_changes(current, previous)
        self.assertEqual(changes[0]["type"], "lifecycle")
        self.assertEqual(changes[0]["from"], "active")
        self.assertEqual(changes[0]["to"], "archived")

    def test_explicit_cross_portfolio_reference(self):
        repos = [
            {"name": "dtgwg-zkp-tf", "full_name": "trustoverip/dtgwg-zkp-tf", "portfolio": "DTG"},
            {"name": "tswg-tsp-specification", "full_name": "trustoverip/tswg-tsp-specification", "portfolio": "TSWG"},
        ]
        units = [{"id": "u1", "repository": "trustoverip/dtgwg-zkp-tf", "portfolio": "DTG", "title": "Align with tswg-tsp-specification", "materiality": 4, "evidence": ["https://example.test/u1"], "events": []}]
        seams = detect_cross_portfolio_seams(units, repos)
        explicit = [s for s in seams if s["strength"] == "explicit-reference"]
        self.assertEqual(len(explicit), 1)
        self.assertEqual(explicit[0]["target_portfolio"], "TSWG")
        self.assertTrue(explicit[0]["review_required"])
        self.assertEqual(explicit[0]["relationship_class"], "cross-portfolio")
        self.assertEqual(explicit[0]["materiality"], 4)

    def test_spec_up_reference_is_tooling_observation_not_material_review_seam(self):
        repos = [
            {"name": "dtgwg-cred-spec", "full_name": "trustoverip/dtgwg-cred-spec", "portfolio": "DTG"},
            {"name": "spec-up-t", "full_name": "trustoverip/spec-up-t", "portfolio": "TSWG"},
        ]
        units = [{"id": "u1", "repository": "trustoverip/dtgwg-cred-spec", "portfolio": "DTG", "title": "Update spec-up-t rendering", "materiality": 5, "evidence": ["https://example.test/u1"], "events": []}]
        seams = detect_cross_portfolio_seams(units, repos)
        explicit = [s for s in seams if s["strength"] == "explicit-reference"]
        self.assertEqual(len(explicit), 1)
        observation = explicit[0]
        self.assertFalse(observation["review_required"])
        self.assertEqual(observation["relationship_class"], "tooling-publication")
        self.assertEqual(observation["review_materiality"], "low")
        self.assertEqual(observation["materiality"], 1)
        self.assertEqual(observation["observed_materiality"], 5)
        self.assertIn("no material cross-portfolio review is inferred", observation["summary"])

    def test_non_open_disposition_requires_governance_fields(self):
        with self.assertRaises(ValueError):
            validate_dispositions([{"finding_id": "f1", "status": "resolved"}])
        validate_dispositions([{"finding_id": "f1", "status": "resolved", "authority": "maintainer", "rationale": "reviewed", "timestamp": "2026-08-25T00:00:00Z", "evidence": ["https://example.test/review"]}])

    def test_disposition_is_applied_by_stable_id(self):
        snapshot = {"assertions": [{"id": "a1", "category": "classification", "subject": "trustoverip/example", "summary": "Needs classification", "materiality": 2, "evidence": []}], "lifecycle_changes": [], "cross_portfolio_seams": [], "change_units": []}
        findings = build_findings(snapshot)
        disposition = [{"finding_id": findings[0]["id"], "status": "accepted", "authority": "maintainer", "rationale": "known exception", "timestamp": "2026-08-25T00:00:00Z", "evidence": ["https://example.test/decision"]}]
        apply_dispositions(findings, disposition)
        self.assertEqual(findings[0]["status"], "accepted")

    def test_source_validation_tolerates_legacy_generated_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("README.md", "LICENSE", "LICENSE-CONTENT.md", "LICENSES.md", "pyproject.toml"):
                (root / rel).write_text("x", encoding="utf-8")
            (root / "docs" / "data").mkdir(parents=True)
            legacy = {"schema_version": "0.1", "organization": "trustoverip", "repositories": [], "events": [], "provenance": {}}
            (root / "docs" / "data" / "latest.json").write_text(json.dumps(legacy), encoding="utf-8")
            self.assertEqual(validate(root), [])
            strict = validate(root, require_generated=True)
            self.assertTrue(any("expected '0.2'" in error for error in strict))
            self.assertTrue(any("change_units" in error for error in strict))

    def test_strict_generated_validation_accepts_current_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("README.md", "LICENSE", "LICENSE-CONTENT.md", "LICENSES.md", "pyproject.toml"):
                (root / rel).write_text("x", encoding="utf-8")
            (root / "docs" / "data").mkdir(parents=True)
            current = {
                "schema_version": "0.2", "organization": "trustoverip", "repositories": [], "events": [], "provenance": {},
                "change_units": [], "lifecycle_changes": [], "cross_portfolio_seams": [], "findings": [], "assertions": [], "collection_errors": [],
            }
            (root / "docs" / "data" / "latest.json").write_text(json.dumps(current), encoding="utf-8")
            self.assertEqual(validate(root, require_generated=True), [])


if __name__ == "__main__":
    unittest.main()
