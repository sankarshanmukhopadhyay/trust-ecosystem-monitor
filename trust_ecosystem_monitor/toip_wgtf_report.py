"""WG/TF-first rendering helpers for ToIP annual intelligence.

This module uses the curated incomplete registry only as a reader grouping aid.
It does not transform repository observations into official ToIP authority,
meeting outcomes or source-owner-approved findings.
"""
from __future__ import annotations

from collections import defaultdict
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from .toip_monthly_knowledge import build_developments
from .toip_wgtf_registry import load_registry, validate_registry, group_repositories

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "trustoverip" / "wgtf-registry.json"


def _safe_github_link(url: str, label: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("non-canonical GitHub evidence URL")
    return '<a href="' + escape(url, quote=True) + '">' + escape(label) + '</a>'


def _repo_group_index(registry: dict) -> tuple[dict[str, dict], dict[str, list[str]]]:
    validate_registry(registry)
    entities = {entry["id"]: entry for entry in registry["entities"]}
    return entities, group_repositories(registry)


def build_wgtf_development_groups(state: dict, registry: dict) -> list[dict]:
    """Group annual GitHub developments by curated candidate WG/TF mapping.

    The function preserves unmapped evidence and multiple candidate mappings. A
    single GitHub artifact can appear in more than one candidate group where the
    curated registry maps its repository to multiple entities.
    """
    entities, repo_index = _repo_group_index(registry)
    grouped: dict[str, list[dict]] = defaultdict(list)
    repo_confidence: dict[str, set[str]] = defaultdict(set)
    for month, entry in sorted(state.get("months", {}).items()):
        evidence = entry.get("observation", {}).get("github", {}).get("evidence", [])
        for item in build_developments(evidence):
            mapped = repo_index.get(item["repository"], []) or ["unmapped"]
            for entity_id in mapped:
                row = {**item, "month": month, "candidate_entity_id": entity_id,
                       "mapping_multiplicity": len(mapped)}
                grouped[entity_id].append(row)
            if mapped != ["unmapped"]:
                for entity_id in mapped:
                    entity = entities[entity_id]
                    for repo in entity.get("mappings", {}).get("repositories", []):
                        if repo.get("full_name") == item["repository"]:
                            repo_confidence[entity_id].add(repo.get("confidence", "low"))
    groups = []
    for entity_id, items in grouped.items():
        items.sort(key=lambda row: (row["month"], row["repository"], row["url"]))
        if entity_id == "unmapped":
            label = "Unmapped / unknown ToIP body"
            entity_type = "unknown"
            authority_state = "not_verified"
            confidence = "low"
            provenance_state = "not_checked"
        else:
            entity = entities[entity_id]
            label = entity["name"]
            entity_type = entity["entity_type"]
            authority_state = entity["authority_state"]
            confidence = entity["confidence"]
            provenance_state = ", ".join(sorted({p["state"] for p in entity.get("provenance", [])}))
        groups.append({
            "entity_id": entity_id,
            "label": label,
            "entity_type": entity_type,
            "authority_state": authority_state,
            "confidence": confidence,
            "mapping_confidence": ", ".join(sorted(repo_confidence[entity_id])) if repo_confidence[entity_id] else "not_checked",
            "provenance_state": provenance_state,
            "months": sorted({item["month"] for item in items}),
            "repositories": sorted({item["repository"] for item in items}),
            "items": items,
            "multiple_mapping_count": sum(1 for item in items if item["mapping_multiplicity"] > 1),
        })
    return sorted(groups, key=lambda group: (group["entity_id"] == "unmapped", group["label"].lower()))


def render_wgtf_first_section(state: dict, *, registry_path: Path = REGISTRY_PATH) -> str:
    """Render the WG/TF-first annual section.

    If the curated registry cannot be loaded, render an explicit unavailable
    state rather than silently falling back to repository-only reporting.
    """
    try:
        registry = load_registry(registry_path)
    except (OSError, ValueError) as exc:
        return ('<h2>WG/TF-first view</h2><p><strong>Unavailable.</strong> '
                'The curated incomplete WG/TF registry could not be loaded or validated: ' +
                escape(str(exc)) + '. Repository-first sections remain the auditable source of evidence.</p>')
    groups = build_wgtf_development_groups(state, registry)
    rows = []
    for group in groups:
        examples = []
        for item in group["items"][:5]:
            examples.append(_safe_github_link(item["url"], item["title"]) +
                            ' <small>(' + escape(item["month"] + '; ' + item["repository"]) + ')</small>')
        caveats = ["candidate reader grouping"]
        if group["entity_id"] == "unmapped":
            caveats.append("no curated WG/TF mapping")
        if group["multiple_mapping_count"]:
            caveats.append("multiple candidate mappings preserved")
        rows.append('<tr><td>' + escape(group["label"]) + '<br><small>' +
                    escape(group["entity_id"]) + ' · ' + escape(group["entity_type"]) +
                    '</small></td><td>' + escape(group["authority_state"]) +
                    '<br><small>entity confidence: ' + escape(group["confidence"]) +
                    '; mapping confidence: ' + escape(group["mapping_confidence"]) +
                    '</small></td><td>' + escape(", ".join(group["months"])) +
                    '</td><td>' + escape(str(len(group["items"]))) +
                    ' artifacts<br><small>' + escape(", ".join(group["repositories"][:6])) +
                    ('…' if len(group["repositories"]) > 6 else '') +
                    '</small></td><td><ul><li>' + '</li><li>'.join(examples or ["No examples"]) +
                    '</li></ul><small>' + escape("; ".join(caveats)) + '</small></td></tr>')
    table = ('<div class="table-wrap"><table><thead><tr>'
             '<th scope="col">Candidate body</th><th scope="col">Authority boundary</th>'
             '<th scope="col">Observed months</th><th scope="col">Evidence volume</th>'
             '<th scope="col">Representative evidence</th></tr></thead><tbody>' +
             (''.join(rows) if rows else '<tr><td colspan="5">No annual GitHub observations available</td></tr>') +
             '</tbody></table></div>')
    return ('<h2>WG/TF-first candidate view</h2>'
            '<p>This section uses the curated incomplete ToIP WG/TF registry to group '
            'GitHub developments for reader navigation. It is not an official ToIP '
            'inventory, charter assertion, meeting record or source-owner authority claim. '
            'Unmapped evidence remains visible rather than being forced into a body.</p>' + table)
