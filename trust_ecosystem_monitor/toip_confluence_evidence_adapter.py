"""Offline, non-publishable adaptation of Confluence acquisition metadata.

Acquisition records lack event timestamps, subject evidence, semantic decisions,
and publication rights. This adapter must not manufacture those fields.
"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit


def stage_confluence_metadata(batch: dict) -> dict:
    """Produce a quarantine manifest, never publishable observations."""
    if not isinstance(batch, dict) or batch.get("source") != "confluence":
        raise ValueError("Confluence acquisition batch required")
    if batch.get("publication_admitted") is not False:
        raise ValueError("batch must explicitly deny publication admission")
    if batch.get("scope_verified") is not False:
        raise ValueError("external source authority must remain unverified")
    if batch.get("historical_completeness_verified") is not False:
        raise ValueError("historical completeness must remain unverified")
    period = batch.get("period")
    if not isinstance(period, str) or len(period) != 7:
        raise ValueError("period required")
    try:
        datetime.strptime(period, "%Y-%m")
    except ValueError as exc:
        raise ValueError("invalid period") from exc
    timestamp = batch.get("retrieved_at")
    try:
        retrieved = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if retrieved.tzinfo is None or retrieved.utcoffset() is None:
            raise ValueError("timezone required")
    except (AttributeError, ValueError) as exc:
        raise ValueError("timezone-aware retrieval timestamp required") from exc
    records = batch.get("records")
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    allowed_spaces = batch.get("space_ids")
    if not isinstance(allowed_spaces, list) or not allowed_spaces or any(
        not isinstance(v, str) or not v.isdigit() for v in allowed_spaces
    ):
        raise ValueError("numeric space IDs required")
    staged = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid metadata record")
        ident = record.get("source_id")
        version = record.get("version")
        space = record.get("space_id")
        url = record.get("url")
        if (record.get("source") != "confluence" or record.get("kind") != "page_update"
                or record.get("classification") != "metadata_only"
                or not isinstance(ident, str) or not ident.isdigit()
                or type(version) is not int or version < 1
                or space not in allowed_spaces
                or not isinstance(url, str)):
            raise ValueError("invalid metadata provenance")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != "lf-toip.atlassian.net"
                or parsed.path != f"/wiki/spaces/HOME/pages/{ident}"
                or parsed.query or parsed.fragment):
            raise ValueError("invalid canonical page URL")
        key = (ident, version)
        if key in seen:
            raise ValueError("duplicate metadata version")
        seen.add(key)
        staged.append({
            "source": "confluence", "source_id": ident, "space_id": space,
            "version": version, "url": url, "kind": "page_update",
            "classification": "metadata_only", "retrieved_at": timestamp,
            "evidence_status": "unclassified", "publication_admitted": False,
            "correlation_eligible": False,
            "missing_evidence": [
                "occurred_at", "subject_id", "subject_evidence_url",
                "reviewed_summary", "source_owner_authority", "publication_approval",
            ],
        })
    return {
        "schema_version": "1", "period": period, "source": "confluence",
        "records": staged, "coverage": batch.get("coverage"),
        "diagnostics": batch.get("diagnostics", []),
        "classification": "quarantined_metadata",
        "publication_admitted": False, "correlation_eligible": False,
    }
