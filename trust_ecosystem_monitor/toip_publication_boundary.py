"""Publication-boundary checks for bounded ToIP Confluence metadata outputs.

The acquisition path may collect only allowlisted page metadata. This module
makes that boundary executable so a later collector or renderer cannot silently
promote page bodies, titles, excerpts, author information or other content-like
fields into public artifacts.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

ALLOWED_RESULT_KEYS = {
    "schema_version",
    "period",
    "source",
    "space_ids",
    "records",
    "diagnostics",
    "retrieved_at",
    "search_pages_fetched",
    "metadata_lookups_attempted",
    "search_terminated_normally",
    "coverage",
    "scope_verified",
    "scope_caller_approved",
    "historical_completeness_verified",
    "publication_admitted",
}

ALLOWED_RECORD_KEYS = {
    "source",
    "source_id",
    "space_id",
    "version",
    "url",
    "kind",
    "classification",
}

DISALLOWED_KEY_TOKENS = {
    "title",
    "body",
    "content",
    "excerpt",
    "text",
    "storage",
    "html",
    "macro",
    "author",
    "creator",
    "owner",
    "account",
    "accountid",
    "email",
    "displayname",
    "attachment",
    "comment",
    "transcript",
    "recording",
    "attendee",
    "speaker",
    "roster",
    "avatar",
}

ALLOWED_COVERAGE = {"partial", "unavailable", "not_authorized", "not_checked"}


def _path(parent: str, child: str) -> str:
    return f"{parent}.{child}" if parent else child


def _key_tokens(key: str) -> set[str]:
    """Return semantic key tokens without treating authorization as author."""
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", key).lower()
    parts = {part for part in normalized.split("_") if part}
    parts.add(normalized)
    return parts


def _contains_disallowed_key_token(key: str) -> bool:
    return bool(_key_tokens(key) & DISALLOWED_KEY_TOKENS)


def _walk_for_disallowed_keys(value, *, path: str, violations: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                violations.append(f"{path}: non-string key")
                continue
            child_path = _path(path, key)
            if _contains_disallowed_key_token(key):
                violations.append(f"{child_path}: content-like or personal-data field is outside metadata boundary")
            _walk_for_disallowed_keys(child, path=child_path, violations=violations)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_for_disallowed_keys(child, path=f"{path}[{index}]", violations=violations)


def _validate_canonical_page_url(value: str, source_id: str, path: str, violations: list[str]) -> None:
    if not isinstance(value, str):
        violations.append(f"{path}: canonical HTTPS page URL required")
        return
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.netloc != "lf-toip.atlassian.net"
            or parsed.path != f"/wiki/spaces/HOME/pages/{source_id}"
            or parsed.query or parsed.fragment):
        violations.append(f"{path}: canonical HOME page URL required")


def audit_metadata_publication_boundary(payload: dict) -> list[str]:
    """Return publication-boundary violations for a nonpublication acquisition artifact.

    This is intentionally stricter than a general JSON schema. It protects the
    public/reporting seam before record-level admission by requiring Confluence
    records to remain page metadata only and by rejecting content-like fields
    anywhere in the payload.
    """
    violations: list[str] = []
    if not isinstance(payload, dict):
        return ["payload: object required"]
    _walk_for_disallowed_keys(payload, path="payload", violations=violations)
    if payload.get("publication_admitted") is not False:
        violations.append("payload.publication_admitted: must remain false before record-level admission")
    results = payload.get("results")
    if not isinstance(results, list):
        violations.append("payload.results: list required")
        return violations
    for index, result in enumerate(results):
        base = f"payload.results[{index}]"
        if not isinstance(result, dict):
            violations.append(f"{base}: object required")
            continue
        unknown = set(result) - ALLOWED_RESULT_KEYS
        if unknown:
            violations.append(f"{base}: unexpected result fields {sorted(unknown)}")
        if result.get("source") != "confluence":
            violations.append(f"{base}.source: confluence required")
        if result.get("publication_admitted") is not False:
            violations.append(f"{base}.publication_admitted: must remain false before record-level admission")
        if result.get("coverage") not in ALLOWED_COVERAGE:
            violations.append(f"{base}.coverage: explicit bounded coverage state required")
        records = result.get("records")
        if not isinstance(records, list):
            violations.append(f"{base}.records: list required")
            continue
        for record_index, record in enumerate(records):
            record_path = f"{base}.records[{record_index}]"
            if not isinstance(record, dict):
                violations.append(f"{record_path}: object required")
                continue
            unknown_record_keys = set(record) - ALLOWED_RECORD_KEYS
            if unknown_record_keys:
                violations.append(f"{record_path}: unexpected record fields {sorted(unknown_record_keys)}")
            if record.get("source") != "confluence":
                violations.append(f"{record_path}.source: confluence required")
            source_id = record.get("source_id")
            if not isinstance(source_id, str) or not source_id.isdigit():
                violations.append(f"{record_path}.source_id: numeric string required")
                source_id = ""
            if record.get("classification") != "metadata_only":
                violations.append(f"{record_path}.classification: metadata_only required")
            if record.get("kind") != "page_update":
                violations.append(f"{record_path}.kind: page_update required")
            if record.get("space_id") != "22970380":
                violations.append(f"{record_path}.space_id: approved HOME space ID required")
            if type(record.get("version")) is not int or record.get("version") < 1:
                violations.append(f"{record_path}.version: positive integer required")
            if source_id:
                _validate_canonical_page_url(record.get("url"), source_id, f"{record_path}.url", violations)
    return violations


def assert_metadata_publication_boundary(payload: dict) -> dict:
    """Raise ValueError when a Confluence acquisition artifact crosses the boundary."""
    violations = audit_metadata_publication_boundary(payload)
    if violations:
        raise ValueError("publication boundary violation: " + "; ".join(violations))
    return payload
