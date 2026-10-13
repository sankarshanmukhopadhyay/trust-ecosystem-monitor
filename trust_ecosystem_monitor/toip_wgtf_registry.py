"""Curated ToIP WG/TF identity registry validation.

The registry is deliberately curator-scoped and incomplete. It provides a
stable internal model for reader-facing grouping without claiming ToIP source
owner authority, complete working-group inventory, meeting coverage or formal
organizational status.
"""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit
import json
import re
from pathlib import Path

SCHEMA_VERSION = "1"
ALLOWED_REGISTRY_STATUS = {"curated_incomplete"}
ALLOWED_ENTITY_TYPES = {"working_group", "task_force", "committee", "community"}
ALLOWED_AUTHORITY_STATES = {"not_official", "not_verified"}
ALLOWED_LIFECYCLE_STATES = {"active", "unknown", "inactive", "historical"}
ALLOWED_SOURCE_STATES = {"not_checked", "candidate", "verified_public_reference", "unavailable"}
ALLOWED_MAPPING_STATES = {"candidate", "curated", "not_checked", "unavailable"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
SAFE_HOSTS = {
    "github.com",
    "lf-toip.atlassian.net",
    "trustoverip.org",
    "www.trustoverip.org",
}
ENTITY_ID = re.compile(r"^toip:[a-z0-9][a-z0-9-]{2,80}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _https(value: str, field: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field}: HTTPS URL required")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port is not None or parsed.fragment):
        raise ValueError(f"{field}: safe HTTPS URL required")
    if parsed.hostname not in SAFE_HOSTS and not parsed.hostname.endswith(".github.io"):
        raise ValueError(f"{field}: host outside ToIP registry allowlist")


def _required_text(obj: dict, key: str, path: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}.{key}: non-empty string required")
    return value


def _state(value: str, allowed: set[str], field: str) -> None:
    if value not in allowed:
        raise ValueError(f"{field}: unsupported value {value!r}")


def validate_registry(registry: dict) -> dict:
    """Validate the curated WG/TF registry and return it unchanged.

    Validation is intentionally conservative: every entity must carry provenance,
    explicit incompleteness, non-official authority state and candidate mappings.
    """
    if not isinstance(registry, dict):
        raise ValueError("registry object required")
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported registry schema")
    if registry.get("registry_status") not in ALLOWED_REGISTRY_STATUS:
        raise ValueError("registry_status must remain curated_incomplete")
    if registry.get("official_toip_inventory") is not False:
        raise ValueError("registry must not claim official ToIP inventory status")
    if registry.get("source_owner_authority_verified") is not False:
        raise ValueError("source owner authority is not verified by this registry")
    if registry.get("complete_group_inventory") is not False:
        raise ValueError("complete group inventory must not be claimed")
    entries = registry.get("entities")
    if not isinstance(entries, list) or not entries:
        raise ValueError("entities: non-empty list required")
    ids = []
    names = []
    for index, entry in enumerate(entries):
        path = f"entities[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: object required")
        ident = _required_text(entry, "id", path)
        if not ENTITY_ID.fullmatch(ident):
            raise ValueError(f"{path}.id: invalid ToIP entity id")
        ids.append(ident)
        name = _required_text(entry, "name", path)
        names.append(name.lower())
        _state(entry.get("entity_type"), ALLOWED_ENTITY_TYPES, f"{path}.entity_type")
        _state(entry.get("authority_state"), ALLOWED_AUTHORITY_STATES, f"{path}.authority_state")
        _state(entry.get("lifecycle_state"), ALLOWED_LIFECYCLE_STATES, f"{path}.lifecycle_state")
        _state(entry.get("confidence"), ALLOWED_CONFIDENCE, f"{path}.confidence")
        if entry.get("official_status_asserted") is not False:
            raise ValueError(f"{path}.official_status_asserted: must be false")
        rationale = _required_text(entry, "curator_rationale", path)
        if len(rationale) < 20:
            raise ValueError(f"{path}.curator_rationale: substantive rationale required")
        provenance = entry.get("provenance")
        if not isinstance(provenance, list) or not provenance:
            raise ValueError(f"{path}.provenance: non-empty list required")
        for pindex, prov in enumerate(provenance):
            ppath = f"{path}.provenance[{pindex}]"
            if not isinstance(prov, dict):
                raise ValueError(f"{ppath}: object required")
            _required_text(prov, "label", ppath)
            _state(prov.get("state"), ALLOWED_SOURCE_STATES, f"{ppath}.state")
            url = prov.get("url")
            if url is not None:
                _https(url, f"{ppath}.url")
        mappings = entry.get("mappings")
        if not isinstance(mappings, dict):
            raise ValueError(f"{path}.mappings: object required")
        repos = mappings.get("repositories", [])
        if not isinstance(repos, list):
            raise ValueError(f"{path}.mappings.repositories: list required")
        for rindex, repo in enumerate(repos):
            rpath = f"{path}.mappings.repositories[{rindex}]"
            if not isinstance(repo, dict):
                raise ValueError(f"{rpath}: object required")
            full_name = _required_text(repo, "full_name", rpath)
            if not REPO.fullmatch(full_name):
                raise ValueError(f"{rpath}.full_name: owner/name required")
            _state(repo.get("mapping_state"), ALLOWED_MAPPING_STATES, f"{rpath}.mapping_state")
            _state(repo.get("confidence"), ALLOWED_CONFIDENCE, f"{rpath}.confidence")
            if "url" in repo:
                _https(repo["url"], f"{rpath}.url")
        confluence = mappings.get("confluence", [])
        if not isinstance(confluence, list):
            raise ValueError(f"{path}.mappings.confluence: list required")
        for cindex, item in enumerate(confluence):
            cpath = f"{path}.mappings.confluence[{cindex}]"
            if not isinstance(item, dict):
                raise ValueError(f"{cpath}: object required")
            _state(item.get("mapping_state"), ALLOWED_MAPPING_STATES, f"{cpath}.mapping_state")
            if "space_id" in item and not str(item["space_id"]).isdigit():
                raise ValueError(f"{cpath}.space_id: numeric string required")
            if "url" in item:
                _https(item["url"], f"{cpath}.url")
        meeting = mappings.get("meeting_series", [])
        if not isinstance(meeting, list):
            raise ValueError(f"{path}.mappings.meeting_series: list required")
        for mindex, item in enumerate(meeting):
            mpath = f"{path}.mappings.meeting_series[{mindex}]"
            if not isinstance(item, dict):
                raise ValueError(f"{mpath}: object required")
            _state(item.get("mapping_state"), ALLOWED_MAPPING_STATES, f"{mpath}.mapping_state")
            _state(item.get("held_state"), {"not_checked", "unknown", "scheduled_only", "held_verified"}, f"{mpath}.held_state")
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        raise ValueError(f"duplicate entity ids: {duplicate_ids}")
    duplicate_names = [item for item, count in Counter(names).items() if count > 1]
    if duplicate_names:
        raise ValueError(f"duplicate entity names: {duplicate_names}")
    return registry


def load_registry(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_registry(data)


def group_repositories(registry: dict) -> dict[str, list[str]]:
    """Return repo full_name to candidate ToIP entity IDs.

    Multiple mappings are preserved rather than collapsed because the registry is
    curated and incomplete.
    """
    validate_registry(registry)
    grouped: dict[str, list[str]] = {}
    for entity in registry["entities"]:
        for repo in entity.get("mappings", {}).get("repositories", []):
            grouped.setdefault(repo["full_name"], []).append(entity["id"])
    return grouped
