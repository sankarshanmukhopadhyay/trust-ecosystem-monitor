from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any

from .findings import apply_dispositions, build_findings, load_dispositions

PORTFOLIO_RELATIONSHIPS = {
    "DTG": {"TSWG", "CTWG", "AIMWG", "KERI Suite"},
    "AIMWG": {"DTG", "TSWG", "Governance"},
    "KERI Suite": {"TSWG", "CTWG", "DTG"},
    "CTWG": {"DTG", "KERI Suite", "TSWG"},
    "TSWG": {"DTG", "AIMWG", "KERI Suite", "CTWG", "Governance"},
    "Governance": {"TSWG", "AIMWG"},
}

TOOLING_REPOSITORIES = {"spec-up", "spec-up-t"}

# Ordered from specific/high-signal semantics toward broad fallback categories.
SEMANTIC_CHANGE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("security", ("security", "vulnerability", "cve", "attack", "threat", "exploit")),
    ("privacy", ("privacy", "correlation", "unlinkability", "data minim", "disclosure")),
    ("authority", ("authority", "delegat", "authoriz", "permission", "entitlement", "revocation")),
    ("governance", ("governance", "policy", "charter", "decision right", "work item")),
    ("protocol_semantics", ("protocol", "semantic", "normative", "must ", "should ")),
    ("api", ("api", "endpoint", "openapi", "http", "request", "response")),
    ("schema", ("schema", "json schema", "field", "property", "serialization")),
    ("lifecycle", ("lifecycle", "status", "suspend", "expire", "withdraw", "deprecat")),
    ("dependency", ("depend", "upstream", "downstream", "vendor", "library")),
    ("interop", ("interop", "conformance", "compatib", "profile", "test vector")),
    ("specification", ("spec", "draft", "rfc", "recommendation", "working draft")),
    ("release", ("release", "version", "tag", "publish")),
    ("editorial", ("editorial", "typo", "wording", "readme", "documentation", "docs")),
    ("implementation", ("implement", "code", "refactor", "fix", "feature", "build", "ci")),
)

PROPAGATION_INTERPRETATION = (
    "Temporal monitor observation only. It does not establish causation, formal dependency, "
    "compatibility impact, compliance obligation, recognition, or authority."
)


def _unit_id(repository: str, key: str) -> str:
    digest = hashlib.sha256(f"{repository}|{key}".encode()).hexdigest()[:12]
    return f"toip-change-{digest}"


def _seam_id(left: str, right: str, key: str) -> str:
    pair = "|".join(sorted((left, right)))
    digest = hashlib.sha256(f"{pair}|{key}".encode()).hexdigest()[:12]
    return f"toip-seam-{digest}"


def _relationship_id(source: str, target: str, key: str) -> str:
    digest = hashlib.sha256(f"{source}|{target}|{key}".encode()).hexdigest()[:12]
    return f"tem-relationship-{digest}"


def _propagation_id(source: str, target: str, trigger: str, state: str) -> str:
    digest = hashlib.sha256(f"{source}|{target}|{trigger}|{state}".encode()).hexdigest()[:12]
    return f"tem-propagation-{digest}"


def _reference_key(event: dict[str, Any]) -> str | None:
    number = event.get("number")
    if number is not None:
        return f"number:{number}"
    match = re.search(r"#(\d+)", event.get("title") or "")
    return f"number:{match.group(1)}" if match else None


def _semantic_key(event: dict[str, Any]) -> str:
    title = (event.get("title") or "untitled").lower()
    title = re.sub(r"\b(merge|merged|fix|feat|docs|chore|refactor|test)(\([^)]*\))?:?\s*", "", title)
    title = re.sub(r"[^a-z0-9]+", " ", title)
    words = [w for w in title.split() if len(w) > 2][:8]
    return "semantic:" + "-".join(words or [event.get("kind", "event")])


def classify_semantic_change(unit: dict[str, Any]) -> dict[str, Any]:
    """Classify one change unit using bounded, explainable repository evidence.

    This is intentionally deterministic. It does not claim that the inferred class
    is an upstream project's own characterization of the change.
    """
    text_parts = [str(unit.get("title", ""))]
    text_parts.extend(str(event.get("title", "")) for event in unit.get("events", []))
    text = " ".join(text_parts).lower()

    for change_type, terms in SEMANTIC_CHANGE_RULES:
        matched = [term for term in terms if term in text]
        if matched:
            return {
                "type": change_type,
                "method": "deterministic-keyword-v1",
                "confidence": "moderate",
                "matched_terms": sorted(set(matched)),
                "evidence_state": "derived",
            }

    if "release" in set(unit.get("event_kinds", [])):
        return {
            "type": "release",
            "method": "event-kind-v1",
            "confidence": "high",
            "matched_terms": [],
            "evidence_state": "derived",
        }

    return {
        "type": "unknown",
        "method": "deterministic-keyword-v1",
        "confidence": "low",
        "matched_terms": [],
        "evidence_state": "insufficient",
    }


def consolidate_change_units(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        key = _reference_key(event) or _semantic_key(event)
        buckets[(event["repository"], key)].append(event)
    units: list[dict[str, Any]] = []
    for (repo, key), members in buckets.items():
        members.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
        primary = max(members, key=lambda m: (int(m.get("materiality", 1)), {"release": 4, "pull_request": 3, "issue": 2, "commit": 1}.get(m["kind"], 0)))
        unit = {
            "id": _unit_id(repo, key), "repository": repo, "portfolio": primary["portfolio"], "repo_kind": primary["repo_kind"],
            "title": primary["title"], "timestamp": members[0].get("timestamp"),
            "materiality": max(int(m.get("materiality", 1)) for m in members),
            "event_kinds": sorted({m["kind"] for m in members}), "event_count": len(members),
            "evidence": list(dict.fromkeys(m["url"] for m in members if m.get("url"))), "events": members,
        }
        unit["semantic_change"] = classify_semantic_change(unit)
        units.append(unit)
    units.sort(key=lambda unit: unit.get("timestamp") or "", reverse=True)
    return units


def detect_lifecycle_changes(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old = {r["full_name"]: r for r in previous}
    new = {r["full_name"]: r for r in current}
    changes: list[dict[str, Any]] = []
    for name, repo in new.items():
        if name not in old:
            changes.append({"type": "discovered", "repository": name, "portfolio": repo["portfolio"], "from": None, "to": repo["lifecycle"], "url": repo["url"]})
            continue
        prior = old[name]
        if repo["lifecycle"] != prior.get("lifecycle"):
            changes.append({"type": "lifecycle", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("lifecycle"), "to": repo["lifecycle"], "url": repo["url"]})
        if repo["portfolio"] != prior.get("portfolio"):
            changes.append({"type": "portfolio", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("portfolio"), "to": repo["portfolio"], "url": repo["url"]})
        if repo.get("default_branch") != prior.get("default_branch"):
            changes.append({"type": "default-branch", "repository": name, "portfolio": repo["portfolio"], "from": prior.get("default_branch"), "to": repo.get("default_branch"), "url": repo["url"]})
    for name, repo in old.items():
        if name not in new:
            changes.append({"type": "missing", "repository": name, "portfolio": repo.get("portfolio", "Unclassified"), "from": repo.get("lifecycle"), "to": None, "url": repo.get("url", "")})
    return sorted(changes, key=lambda c: (c["type"], c["repository"]))


def _repo_mentions(unit: dict[str, Any], repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text = " ".join([unit.get("title", "")] + [e.get("title", "") for e in unit.get("events", [])]).lower()
    source = unit["repository"].lower()
    return [repo for repo in repositories if repo["full_name"].lower() != source and (repo["name"].lower() in text or repo["full_name"].lower() in text)]


def build_relationship_graph(units: list[dict[str, Any]], repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Materialize only relationships that have explicit evidence in observed change units.

    An edge records an observed reference. It is deliberately not promoted to a
    dependency, recognition, authority, or interoperability claim without stronger
    evidence supplied by a future capability.
    """
    relationships: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    by_name = {repo["full_name"]: repo for repo in repositories}

    for unit in units:
        source = unit["repository"]
        source_repo = by_name.get(source, {})
        for target in _repo_mentions(unit, repositories):
            key = (source, target["full_name"], unit["id"])
            if key in seen:
                continue
            seen.add(key)
            tooling = target.get("name", "").lower() in TOOLING_REPOSITORIES
            relationships.append({
                "id": _relationship_id(source, target["full_name"], unit["id"]),
                "source_repository": source,
                "target_repository": target["full_name"],
                "source_portfolio": unit.get("portfolio", source_repo.get("portfolio", "Unclassified")),
                "target_portfolio": target.get("portfolio", "Unclassified"),
                "relationship_type": "tooling-publication-reference" if tooling else "observed-reference",
                "claim_strength": "observed",
                "formal_dependency": False,
                "recognition_inferred": False,
                "authority_inferred": False,
                "source_change_unit": unit["id"],
                "semantic_change_type": unit.get("semantic_change", {}).get("type", "unknown"),
                "evidence": unit.get("evidence", []),
                "evidence_state": "observed" if unit.get("evidence") else "insufficient",
            })

    return sorted(
        relationships,
        key=lambda item: (item["source_repository"], item["target_repository"], item["source_change_unit"]),
    )


def _unit_timestamp(unit: dict[str, Any]) -> str:
    return str(unit.get("timestamp") or "")


def detect_change_propagation(
    units: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    previous: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Derive bounded temporal propagation observations.

    Relationship direction means `source_repository` explicitly referenced
    `target_repository`. A later source change that retains the explicit reference
    may be recorded as follow-up to an earlier target change. This is temporal
    evidence only; causation and normative dependency are never inferred.
    """
    previous = previous or {}
    current_by_id = {unit["id"]: unit for unit in units}
    previous_units = previous.get("change_units", [])
    historical_units = previous_units + units
    units_by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in historical_units:
        units_by_repo[unit.get("repository", "")].append(unit)
    for repository_units in units_by_repo.values():
        repository_units.sort(key=_unit_timestamp)

    observations: list[dict[str, Any]] = []
    observed_keys: set[tuple[str, str, str]] = set()

    # Positive evidence: a referencing change occurs after a change in the
    # referenced repository and retains the explicit reference.
    for relationship in relationships:
        responding = current_by_id.get(relationship.get("source_change_unit"))
        if not responding:
            continue
        target = relationship["target_repository"]
        candidates = [
            unit
            for unit in units_by_repo.get(target, [])
            if _unit_timestamp(unit) and _unit_timestamp(unit) < _unit_timestamp(responding)
        ]
        if not candidates:
            observations.append({
                "id": _propagation_id(relationship["source_repository"], target, relationship["id"], "insufficient_history"),
                "state": "insufficient_history",
                "referencing_repository": relationship["source_repository"],
                "referenced_repository": target,
                "relationship_id": relationship["id"],
                "trigger_change_unit": None,
                "responding_change_unit": responding["id"],
                "trigger_timestamp": None,
                "response_timestamp": responding.get("timestamp"),
                "relationship_evidence": relationship.get("evidence", []),
                "evidence": relationship.get("evidence", []),
                "interpretation": PROPAGATION_INTERPRETATION,
            })
            continue

        trigger = candidates[-1]
        key = (relationship["source_repository"], target, trigger["id"])
        if key in observed_keys:
            continue
        observed_keys.add(key)
        observations.append({
            "id": _propagation_id(relationship["source_repository"], target, trigger["id"], "observed_follow_up"),
            "state": "observed_follow_up",
            "referencing_repository": relationship["source_repository"],
            "referenced_repository": target,
            "relationship_id": relationship["id"],
            "trigger_change_unit": trigger["id"],
            "responding_change_unit": responding["id"],
            "trigger_timestamp": trigger.get("timestamp"),
            "response_timestamp": responding.get("timestamp"),
            "trigger_semantic_change_type": trigger.get("semantic_change", {}).get("type", "unknown"),
            "response_semantic_change_type": responding.get("semantic_change", {}).get("type", "unknown"),
            "relationship_evidence": relationship.get("evidence", []),
            "evidence": list(dict.fromkeys(trigger.get("evidence", []) + relationship.get("evidence", []))),
            "interpretation": PROPAGATION_INTERPRETATION,
        })

    # Absence-of-follow-up observations require historical relationship evidence.
    # A first baseline cannot support an absence claim.
    previous_relationships = previous.get("relationships", [])
    if previous_relationships:
        current_pairs = {
            (relationship["source_repository"], relationship["target_repository"]): relationship
            for relationship in relationships
        }
        for prior in previous_relationships:
            source = prior.get("source_repository")
            target = prior.get("target_repository")
            if not source or not target:
                continue
            current_target_units = [unit for unit in units if unit.get("repository") == target]
            for trigger in current_target_units:
                pair = (source, target)
                current_relationship = current_pairs.get(pair)
                if current_relationship:
                    responding = current_by_id.get(current_relationship.get("source_change_unit"))
                    if responding and _unit_timestamp(responding) > _unit_timestamp(trigger):
                        continue
                key = (source, target, trigger["id"])
                if key in observed_keys:
                    continue
                observed_keys.add(key)
                observations.append({
                    "id": _propagation_id(source, target, trigger["id"], "no_follow_up_observed"),
                    "state": "no_follow_up_observed",
                    "referencing_repository": source,
                    "referenced_repository": target,
                    "relationship_id": prior.get("id"),
                    "trigger_change_unit": trigger["id"],
                    "responding_change_unit": None,
                    "trigger_timestamp": trigger.get("timestamp"),
                    "response_timestamp": None,
                    "trigger_semantic_change_type": trigger.get("semantic_change", {}).get("type", "unknown"),
                    "relationship_evidence": prior.get("evidence", []),
                    "evidence": list(dict.fromkeys(trigger.get("evidence", []) + prior.get("evidence", []))),
                    "interpretation": PROPAGATION_INTERPRETATION + " No follow-up observed is not evidence that follow-up was required.",
                })

    state_order = {"observed_follow_up": 0, "no_follow_up_observed": 1, "insufficient_history": 2}
    return sorted(
        observations,
        key=lambda item: (
            state_order.get(item["state"], 9),
            item["referencing_repository"],
            item["referenced_repository"],
            item.get("trigger_timestamp") or "",
        ),
    )


def _explicit_reference_metadata(target: dict[str, Any], source_materiality: int) -> dict[str, Any]:
    if target.get("name", "").lower() in TOOLING_REPOSITORIES:
        return {
            "relationship_class": "tooling-publication",
            "review_materiality": "low",
            "review_required": False,
            "materiality": 1,
            "observed_materiality": source_materiality,
        }
    return {
        "relationship_class": "cross-portfolio",
        "review_materiality": "derived",
        "review_required": True,
        "materiality": source_materiality,
    }


def detect_cross_portfolio_seams(units: list[dict[str, Any]], repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seams: list[dict[str, Any]] = []
    seen: set[str] = set()
    for unit in units:
        for target in _repo_mentions(unit, repositories):
            if target["portfolio"] == unit["portfolio"]:
                continue
            sid = _seam_id(unit["portfolio"], target["portfolio"], unit["id"] + target["full_name"])
            if sid not in seen:
                seen.add(sid)
                metadata = _explicit_reference_metadata(target, int(unit["materiality"]))
                summary = f"{unit['repository']} references {target['full_name']} in a current change unit."
                if not metadata["review_required"]:
                    summary += " Classified as tooling/publication evidence; no material cross-portfolio review is inferred from the reference alone."
                seams.append({
                    "id": sid,
                    "strength": "explicit-reference",
                    "source_portfolio": unit["portfolio"],
                    "target_portfolio": target["portfolio"],
                    "source_repository": unit["repository"],
                    "target_repository": target["full_name"],
                    "summary": summary,
                    "evidence": unit.get("evidence", []),
                    **metadata,
                })
    material_by_portfolio: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        if unit.get("materiality", 0) >= 4:
            material_by_portfolio[unit["portfolio"]].append(unit)
    for left, related in PORTFOLIO_RELATIONSHIPS.items():
        if left not in material_by_portfolio:
            continue
        for right in related:
            if right not in material_by_portfolio or left >= right:
                continue
            left_unit, right_unit = material_by_portfolio[left][0], material_by_portfolio[right][0]
            sid = _seam_id(left, right, "co-movement")
            if sid not in seen:
                seen.add(sid)
                seams.append({"id": sid, "strength": "related-co-movement", "relationship_class": "cross-portfolio", "review_materiality": "derived", "review_required": True, "source_portfolio": left, "target_portfolio": right, "source_repository": left_unit["repository"], "target_repository": right_unit["repository"], "summary": f"Related portfolios {left} and {right} both contain material change units in this observation window; cross-review may be warranted.", "materiality": min(left_unit["materiality"], right_unit["materiality"]), "evidence": list(dict.fromkeys(left_unit.get("evidence", [])[:1] + right_unit.get("evidence", [])[:1]))})
    return sorted(seams, key=lambda s: (-s["materiality"], s["strength"], s["source_portfolio"], s["target_portfolio"]))


def analyze_snapshot(snapshot: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot["change_units"] = consolidate_change_units(snapshot.get("events", []))
    snapshot["lifecycle_changes"] = detect_lifecycle_changes(snapshot.get("repositories", []), (previous or {}).get("repositories", [])) if previous else []
    snapshot["relationships"] = build_relationship_graph(snapshot["change_units"], snapshot.get("repositories", []))
    snapshot["change_propagation"] = detect_change_propagation(snapshot["change_units"], snapshot["relationships"], previous)
    snapshot["cross_portfolio_seams"] = detect_cross_portfolio_seams(snapshot["change_units"], snapshot.get("repositories", []))
    findings = build_findings(snapshot)
    snapshot["findings"] = apply_dispositions(findings, load_dispositions())
    return snapshot
