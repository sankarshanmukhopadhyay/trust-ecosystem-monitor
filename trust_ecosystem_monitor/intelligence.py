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


def _unit_id(repository: str, key: str) -> str:
    digest = hashlib.sha256(f"{repository}|{key}".encode()).hexdigest()[:12]
    return f"toip-change-{digest}"


def _seam_id(left: str, right: str, key: str) -> str:
    pair = "|".join(sorted((left, right)))
    digest = hashlib.sha256(f"{pair}|{key}".encode()).hexdigest()[:12]
    return f"toip-seam-{digest}"


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


def consolidate_change_units(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        key = _reference_key(event) or _semantic_key(event)
        buckets[(event["repository"], key)].append(event)
    units: list[dict[str, Any]] = []
    for (repo, key), members in buckets.items():
        members.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
        primary = max(members, key=lambda m: (int(m.get("materiality", 1)), {"release": 4, "pull_request": 3, "issue": 2, "commit": 1}.get(m["kind"], 0)))
        units.append({
            "id": _unit_id(repo, key), "repository": repo, "portfolio": primary["portfolio"], "repo_kind": primary["repo_kind"],
            "title": primary["title"], "timestamp": members[0].get("timestamp"),
            "materiality": max(int(m.get("materiality", 1)) for m in members),
            "event_kinds": sorted({m["kind"] for m in members}), "event_count": len(members),
            "evidence": list(dict.fromkeys(m["url"] for m in members if m.get("url"))), "events": members,
        })
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
    snapshot["cross_portfolio_seams"] = detect_cross_portfolio_seams(snapshot["change_units"], snapshot.get("repositories", []))
    findings = build_findings(snapshot)
    snapshot["findings"] = apply_dispositions(findings, load_dispositions())
    return snapshot
