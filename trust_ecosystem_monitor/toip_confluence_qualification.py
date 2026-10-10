"""Offline curator qualification of quarantined Confluence metadata.

Qualification produces an audit decision, not a published observation.
It never confers source-owner authority or publication rights.
"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit

from .toip_evidence_contract import validate_observations


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timezone-aware timestamp required")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return result


def _evidence_url(value, host):
    if not isinstance(value, str):
        raise ValueError("evidence URL required")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname != host or parsed.username
            or parsed.password or parsed.port is not None or not parsed.path
            or parsed.fragment):
        raise ValueError("invalid evidence URL")
    return value


def qualify_confluence_metadata(manifest: dict, review: dict) -> dict:
    """Validate a curator's assertions against one quarantined page version.

    A successful result is 'review_ready', not publishable. Explicit source
    authority and publication decisions are required separately downstream.
    """
    if not isinstance(manifest, dict) or manifest.get("classification") != "quarantined_metadata":
        raise ValueError("quarantined manifest required")
    if manifest.get("publication_admitted") is not False or manifest.get("correlation_eligible") is not False:
        raise ValueError("manifest must remain quarantined")
    if not isinstance(review, dict):
        raise ValueError("review object required")
    page_id = review.get("source_id")
    version = review.get("version")
    if not isinstance(page_id, str) or not page_id.isdigit() or type(version) is not int:
        raise ValueError("page ID and version required")
    matches = [r for r in manifest.get("records", [])
               if r.get("source_id") == page_id and r.get("version") == version]
    if len(matches) != 1:
        raise ValueError("exactly one matching quarantined page version required")
    page = matches[0]
    if (page.get("source") != "confluence" or page.get("kind") != "page_update"
            or page.get("publication_admitted") is not False
            or page.get("correlation_eligible") is not False):
        raise ValueError("invalid quarantined record")
    _evidence_url(page.get("url"), "lf-toip.atlassian.net")
    _timestamp(page.get("retrieved_at"))
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("named curator required")
    reviewed_at = review.get("reviewed_at")
    _timestamp(reviewed_at)
    occurred_at = review.get("occurred_at")
    _timestamp(occurred_at)
    subject = review.get("subject_id")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("explicit subject required")
    summary = review.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("reviewed factual summary required")
    event_evidence = _evidence_url(review.get("event_evidence_url"), "lf-toip.atlassian.net")
    subject_evidence = _evidence_url(review.get("subject_evidence_url"), "lf-toip.atlassian.net")
    if review.get("event_type") != "page_update":
        raise ValueError("page metadata cannot establish governance decisions")
    if review.get("evidence_checked") is not True:
        raise ValueError("curator must explicitly attest evidence review")
    if review.get("source_owner_authority_verified") is not False:
        raise ValueError("source authority must be determined independently")
    if review.get("publication_approved") is not False:
        raise ValueError("publication must be separately authorized")
    candidate = {
        "source": "confluence", "source_id": page_id, "kind": "page_update",
        "url": page["url"], "occurred_at": occurred_at,
        "subject_id": subject, "subject_evidence_url": subject_evidence,
        "summary": summary, "publication_approved": False,
    }
    # Intentionally do not pass candidate to validate_observations: it is
    # not publication-authorized. Explicitly verify the gate still rejects it.
    try:
        validate_observations([candidate], approved_confluence=True)
    except ValueError as exc:
        if "record-level Confluence publication approval" not in str(exc):
            raise
    else:
        raise AssertionError("publication gate unexpectedly admitted candidate")
    return {
        "schema_version": "1", "status": "review_ready",
        "reviewer": reviewer, "reviewed_at": reviewed_at,
        "page_version": {"source_id": page_id, "version": version},
        "event_evidence_url": event_evidence,
        "candidate": candidate,
        "source_owner_authority_verified": False,
        "publication_admitted": False,
        "correlation_eligible": False,
        "limitations": [
            "curator assertions require independent verification",
            "page update is not a governance decision",
            "source-owner authority and publication rights remain unverified",
            "shared subject is not independently corroborated",
        ],
    }
