"""Conservative, offline-verifiable cross-source evidence and inference contract.

No network acquisition or publication authorization is implied by this module.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from urllib.parse import urlsplit

SOURCES = {"github", "confluence"}
KINDS = {"proposal", "discussion", "page_update", "implementation", "decision", "deliverable"}
COVERAGE = {"complete", "partial", "unavailable", "not_authorized", "not_checked"}


def _date(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be ISO 8601")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO 8601 timestamp") from exc
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return dt


def validate_observations(records: list[dict], *, approved_confluence: bool = False) -> list[dict]:
    """Validate provenance and reject duplicate or unauthorized external records."""
    if not isinstance(records, list):
        raise ValueError("observations must be an array")
    seen = set()
    result = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("observation must be an object")
        source = record.get("source")
        if source not in SOURCES or record.get("kind") not in KINDS:
            raise ValueError("invalid source or observation kind")
        if source == "confluence" and not approved_confluence:
            raise ValueError("Confluence source approval required")
        url = record.get("url")
        if not isinstance(url, str):
            raise ValueError("canonical URL required")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname:
            raise ValueError("HTTPS canonical source URL required")
        if source == "github" and parsed.hostname != "github.com":
            raise ValueError("GitHub URL must use github.com")
        if source == "confluence" and parsed.hostname != "lf-toip.atlassian.net":
            raise ValueError("Confluence URL must use verified host")
        if not isinstance(record.get("source_id"), str) or not record["source_id"].strip():
            raise ValueError("stable source_id required")
        if not isinstance(record.get("subject_id"), str) or not record["subject_id"].strip():
            raise ValueError("explicit subject_id required for correlation")
        _date(record.get("occurred_at"))
        if not isinstance(record.get("summary"), str) or not record["summary"].strip():
            raise ValueError("nonempty summary required")
        if source == "confluence":
            if record.get("publication_approved") is not True:
                raise ValueError("record-level Confluence publication approval required")
            if record.get("kind") == "decision" and not record.get("decision_evidence_url"):
                raise ValueError("decision requires explicit decision evidence")
        key = (source, record["source_id"], record["kind"])
        if key in seen:
            raise ValueError("duplicate source observation")
        seen.add(key)
        result.append(record)
    return result


def infer_correlations(records: list[dict], *, approved_confluence: bool = False) -> list[dict]:
    """Infer only cross-source corroboration for an explicitly shared subject ID.

    Shared subject IDs must be supplied by an authorized curator after inspecting
    source references; the function does not infer identity from timestamps or text.
    """
    valid = validate_observations(records, approved_confluence=approved_confluence)
    groups = defaultdict(list)
    for record in valid:
        groups[record["subject_id"]].append(record)
    findings = []
    for subject, group in sorted(groups.items()):
        github = [r for r in group if r["source"] == "github"]
        confluence = [r for r in group if r["source"] == "confluence"]
        if not github or not confluence:
            continue
        findings.append({
            "type": "cross_source_reference",
            "subject_id": subject,
            "source_urls": sorted({r["url"] for r in group}),
            "observation_count": len(group),
            "statement": "GitHub and authorized Confluence observations reference the same curator-identified subject.",
            "limitations": "Shared subject is curator-asserted; this does not establish governance approval, adoption, interoperability or causation.",
        })
    return findings
