from __future__ import annotations

import json
from pathlib import Path

from . import core_backend
from .profile import load_profile

REQUIRED_GENERATED_KEYS = (
    "change_units",
    "lifecycle_changes",
    "cross_portfolio_seams",
    "findings",
    "assertions",
    "collection_errors",
)


def validate(root: str | Path = ".", require_generated: bool = False) -> list[str]:
    root = Path(root)
    errors = core_backend.validate(root, require_generated=False)
    if not require_generated:
        return errors

    profiles = sorted((root / "organizations").glob("*/profile.toml"))
    if not profiles:
        errors.append("no organization profiles found")
        return errors

    for profile_path in profiles:
        try:
            profile = load_profile(profile_path)
        except Exception as exc:
            errors.append(f"invalid profile {profile_path}: {exc}")
            continue

        latest = root / "docs" / profile.id / "data" / "latest.json"
        if not latest.exists():
            errors.append(f"missing generated snapshot for profile {profile.id}: {latest}")
            continue
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid generated snapshot JSON for {profile.id}: {exc}")
            continue

        if payload.get("schema_version") != core_backend.CURRENT_SCHEMA_VERSION:
            errors.append(
                f"generated snapshot for {profile.id} uses schema {payload.get('schema_version')!r}; "
                f"expected {core_backend.CURRENT_SCHEMA_VERSION!r}"
            )
        if payload.get("organization") != profile.organization:
            errors.append(
                f"generated snapshot for {profile.id} targets {payload.get('organization')!r}; "
                f"expected {profile.organization!r}"
            )
        metadata = payload.get("ecosystem_profile", {})
        if metadata.get("id") != profile.id:
            errors.append(f"generated snapshot for {profile.id} has mismatched ecosystem profile metadata")
        if payload.get("provenance", {}).get("collector") != "trust-ecosystem-monitor":
            errors.append(f"generated snapshot for {profile.id} has non-canonical collector provenance")
        for key in REQUIRED_GENERATED_KEYS:
            if key not in payload:
                errors.append(f"generated snapshot for {profile.id} missing key: {key}")

    if not (root / "docs" / "index.html").exists():
        errors.append("missing top-level ecosystem catalog: docs/index.html")
    if not (root / "docs" / "ecosystems.json").exists():
        errors.append("missing top-level ecosystem manifest: docs/ecosystems.json")
    relationship_json = root / "docs" / "data" / "relationships.json"
    relationship_html = root / "docs" / "relationships.html"
    if not relationship_json.exists():
        errors.append("missing cross-ecosystem relationship data: docs/data/relationships.json")
    if not relationship_html.exists():
        errors.append("missing cross-ecosystem relationship register: docs/relationships.html")
    if relationship_json.exists():
        try:
            relationships = json.loads(relationship_json.read_text(encoding="utf-8"))
            if relationships.get("authority") != "derived":
                errors.append("cross-ecosystem relationship data must declare authority=derived")
            for item in relationships.get("relationships", []):
                if item.get("evidence_grade") == "C" and item.get("publication_state") == "established":
                    errors.append(f"Grade C relationship published as established: {item.get('id')}")
        except json.JSONDecodeError as exc:
            errors.append(f"invalid cross-ecosystem relationship JSON: {exc}")
    return errors
