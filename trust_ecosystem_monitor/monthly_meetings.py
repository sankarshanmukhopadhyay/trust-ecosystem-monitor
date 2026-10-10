"""Portable source-coverage and curated meeting-evidence adapter.

Input is a local JSON manifest exported by an authorized operator; the module
never attempts to bypass Confluence or LFX permissions.
"""
from __future__ import annotations

import json
from pathlib import Path

STATES = {"complete", "partial", "unavailable", "not_authorized", "not_found", "not_checked"}


def load_meetings(path: Path, period: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1":
        raise ValueError("Unsupported meeting evidence schema")
    if payload.get("period") != period:
        raise ValueError("Meeting manifest period mismatch")
    coverage = payload.get("coverage", {})
    if not isinstance(coverage, dict) or set(coverage) != {"confluence", "lfx"}:
        raise ValueError("Coverage must explicitly specify confluence and lfx")
    if any(value not in STATES for value in coverage.values()):
        raise ValueError("Invalid meeting coverage state")
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Meeting records must be an array")
    seen = set()
    for record in records:
        if record.get("source") not in {"confluence", "lfx"}:
            raise ValueError("Meeting source must be confluence or lfx")
        if not record.get("url", "").startswith("https://"):
            raise ValueError("Meeting evidence requires HTTPS source URL")
        if not record.get("occurred_at", "").startswith(period + "-"):
            raise ValueError("Meeting evidence must belong to report period")
        if record.get("classification") not in {"discussion", "decision", "deliverable", "question"}:
            raise ValueError("Invalid evidence classification")
        if not record.get("group") or not record.get("summary"):
            raise ValueError("Meeting evidence needs group and summary")
        key = (record["source"], record["url"], record["classification"])
        if key in seen:
            raise ValueError("Duplicate meeting evidence record")
        seen.add(key)
    return payload


def empty_manifest(period: str, *, confluence: str = "not_checked", lfx: str = "not_checked") -> dict:
    if confluence not in STATES or lfx not in STATES:
        raise ValueError("Invalid source coverage state")
    return {
        "schema_version": "1",
        "period": period,
        "coverage": {"confluence": confluence, "lfx": lfx},
        "records": [],
    }
