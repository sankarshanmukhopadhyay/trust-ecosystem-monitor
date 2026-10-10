"""Fail-closed, offline authorization decision and qualified evidence admission.

This module verifies structural consistency of signed-off decision *records*.
It cannot independently authenticate a source owner's identity or rights.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit

from .toip_evidence_contract import validate_observations


def _instant(value):
    if not isinstance(value, str):
        raise ValueError("timezone-aware ISO 8601 timestamp required")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt


def _https(value):
    if not isinstance(value, str):
        raise ValueError("HTTPS evidence URL required")
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.port is not None or parsed.fragment):
            raise ValueError("unsafe evidence URL")
    except ValueError as exc:
        raise ValueError("unsafe evidence URL") from exc
    return value


def validate_authorization_decision(decision: dict, *, as_of: str,
                                    revoked_ids: set[str] | None = None) -> dict:
    """Check a bounded approval, independently confirmed outside this module."""
    if not isinstance(decision, dict):
        raise ValueError("authorization decision object required")
    if decision.get("schema_version") != "1":
        raise ValueError("unsupported authorization schema")
    for key in ("decision_id", "issuer", "issuer_role", "reviewer", "rationale"):
        if not isinstance(decision.get(key), str) or not decision[key].strip():
            raise ValueError(f"{key} required")
    if decision["issuer_role"] != "source_owner":
        raise ValueError("source-owner authority required")
    if decision.get("authority_independently_verified") is not True:
        raise ValueError("independent authority verification required")
    if decision.get("decision") != "approved":
        raise ValueError("explicit approval required")
    if decision.get("revoked") is not False:
        raise ValueError("revoked or indeterminate authorization")
    if revoked_ids is None:
        raise ValueError("current revocation register required")
    if decision["decision_id"] in revoked_ids:
        raise ValueError("authorization revoked by register")
    scope = decision.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("scope required")
    if scope.get("source") != "confluence" or scope.get("host") != "lf-toip.atlassian.net":
        raise ValueError("source scope mismatch")
    spaces = scope.get("space_ids")
    periods = scope.get("periods")
    uses = scope.get("permitted_uses")
    if (not isinstance(spaces, list) or not spaces
            or any(not isinstance(s, str) or not s.isdigit() for s in spaces)
            or not isinstance(periods, list) or not periods
            or any(p not in ("2026-08", "2026-09") for p in periods)
            or not isinstance(uses, list)
            or not {"metadata_acquisition", "derived_publication"}.issubset(set(uses))):
        raise ValueError("bounded source, period and publication uses required")
    if decision.get("content_categories") != ["page_metadata"]:
        raise ValueError("only page metadata is eligible")
    _https(decision.get("authority_evidence_url"))
    _https(decision.get("permission_evidence_url"))
    issued = _instant(decision.get("issued_at"))
    expires = _instant(decision.get("expires_at"))
    now = _instant(as_of)
    if not issued <= now < expires:
        raise ValueError("authorization not effective")
    return decision


def admit_qualified_confluence(qualification: dict, decision: dict, *,
                               as_of: str, revoked_ids: set[str] | None,
                               independent_review: dict) -> dict:
    """Return a validated observation only after two separate evidence gates.

    The returned record remains metadata-only; no governance decision inference.
    """
    validate_authorization_decision(decision, as_of=as_of, revoked_ids=revoked_ids)
    if not isinstance(qualification, dict) or qualification.get("status") != "review_ready":
        raise ValueError("review-ready qualification required")
    if (qualification.get("publication_admitted") is not False
            or qualification.get("correlation_eligible") is not False):
        raise ValueError("qualification must remain quarantined")
    if not isinstance(independent_review, dict):
        raise ValueError("independent review required")
    if independent_review.get("approved") is not True:
        raise ValueError("independent evidence review approval required")
    reviewer = independent_review.get("reviewer")
    if (not isinstance(reviewer, str) or not reviewer.strip()
            or reviewer == qualification.get("reviewer")):
        raise ValueError("distinct independent reviewer required")
    if independent_review.get("source_links_verified") is not True:
        raise ValueError("independently verified source links required")
    if independent_review.get("subject_mapping_verified") is not True:
        raise ValueError("independently verified subject mapping required")
    _https(independent_review.get("review_evidence_url"))
    reviewed_at = _instant(independent_review.get("reviewed_at"))
    if reviewed_at > _instant(as_of):
        raise ValueError("future independent review")
    page = qualification.get("page_version")
    candidate = qualification.get("candidate")
    if not isinstance(page, dict) or not isinstance(candidate, dict):
        raise ValueError("version-bound candidate required")
    ident = page.get("source_id")
    version = page.get("version")
    if (not isinstance(ident, str) or not ident.isdigit()
            or type(version) is not int or version < 1
            or candidate.get("source_id") != ident
            or candidate.get("source") != "confluence"
            or candidate.get("kind") != "page_update"
            or candidate.get("publication_approved") is not False):
        raise ValueError("invalid version-bound candidate")
    parsed = urlsplit(candidate.get("url", ""))
    if (parsed.scheme != "https" or parsed.netloc != "lf-toip.atlassian.net"
            or parsed.path != f"/wiki/spaces/HOME/pages/{ident}"
            or parsed.query or parsed.fragment):
        raise ValueError("canonical page identity required")
    if "22970380" not in decision["scope"]["space_ids"]:
        raise ValueError("page space outside authorization")
    event = _instant(candidate.get("occurred_at"))
    if event.strftime("%Y-%m") not in decision["scope"]["periods"]:
        raise ValueError("event outside authorized reporting period")
    if _instant(qualification.get("reviewed_at")) > _instant(as_of):
        raise ValueError("future curator review")
    if not isinstance(qualification.get("event_evidence_url"), str):
        raise ValueError("event evidence required")
    _https(qualification["event_evidence_url"])
    _https(candidate.get("subject_evidence_url"))
    approved = dict(candidate, publication_approved=True,
                    authorization_decision_id=decision["decision_id"],
                    page_version=version,
                    independent_review_evidence_url=independent_review["review_evidence_url"])
    return validate_observations([approved], approved_confluence=True)[0]
