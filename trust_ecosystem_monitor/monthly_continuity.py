"""Validate evidence coverage and classify month-to-month observed continuity.

These classifications describe evidence only, not organizational delivery.
"""
from __future__ import annotations


def continuity(earlier: dict, later: dict) -> list[dict]:
    if earlier["period"] >= later["period"] or earlier["ecosystem"] != later["ecosystem"]:
        raise ValueError("Comparable manifests require the same ecosystem and ascending periods")
    before: dict[str, set[str]] = {}
    after: dict[str, set[str]] = {}
    for item in earlier["evidence"]:
        before.setdefault(item["repository"], set()).add(item["url"])
    for item in later["evidence"]:
        after.setdefault(item["repository"], set()).add(item["url"])
    entries = []
    for repo in sorted(set(before) | set(after)):
        first = before.get(repo, set())
        second = after.get(repo, set())
        if not earlier["coverage_complete"] or not later["coverage_complete"]:
            classification = "evidence_insufficient"
        elif first & second:
            classification = "continuing_observed"
        elif first and second:
            classification = "new_events_observed"
        elif second:
            classification = "newly_observed"
        else:
            classification = "earlier_only_observed"
        entries.append({
            "repository": repo,
            "classification": classification,
            "shared_item_urls": sorted(first & second),
            "earlier_urls": sorted(first),
            "later_urls": sorted(second),
        })
    return entries
