"""Exact-identity longitudinal timelines for observed GitHub artifacts.

Timelines group only the same canonical GitHub issue or pull-request URL.
They do not infer topic identity, resolution, adoption, dependency or decisions.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
import re
from urllib.parse import urlsplit

from .toip_annual_state import validate

SUBJECT_PATH = re.compile(r"^/([^/]+)/([^/]+)/(issues|pull)/(\d+)$")
EVENT_LABELS = {
    "opened": "Opening observed",
    "closed": "Closure observed; resolution not established",
    "merged": "Merge observed; adoption not established",
}


def canonical_subject(url: str) -> dict:
    if not isinstance(url, str):
        raise ValueError("GitHub subject URL required")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "github.com" or
            parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("non-canonical GitHub subject URL")
    match = SUBJECT_PATH.fullmatch(parsed.path)
    if not match:
        raise ValueError("unsupported GitHub subject path")
    owner, repository, path_kind, number = match.groups()
    return {
        "url": url,
        "repository": owner + "/" + repository,
        "kind": "issues" if path_kind == "issues" else "pull_requests",
        "number": int(number),
    }


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("event timestamp required")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid event timestamp") from exc
    if stamp.tzinfo is None:
        raise ValueError("timezone-aware event timestamp required")
    return stamp


def build_timelines(state: dict) -> list[dict]:
    """Build exact-artifact timelines from immutable annual observations."""
    validate(state)
    grouped = defaultdict(list)
    for month, entry in sorted(state["months"].items()):
        evidence = entry["observation"]["github"].get("evidence", [])
        for row in evidence:
            if not isinstance(row, dict):
                raise ValueError("invalid GitHub evidence row")
            subject = canonical_subject(row.get("url"))
            if row.get("repository") and row["repository"] != subject["repository"]:
                raise ValueError("repository does not match GitHub subject URL")
            if row.get("kind") and row["kind"] != subject["kind"]:
                raise ValueError("artifact kind does not match GitHub subject URL")
            event = row.get("event")
            if event not in EVENT_LABELS:
                raise ValueError("unsupported GitHub lifecycle event")
            occurred_at = row.get("occurred_at")
            _timestamp(occurred_at)
            title = str(row.get("title", "")).strip().replace("\n", " ")
            if not title:
                raise ValueError("GitHub evidence title required")
            grouped[subject["url"]].append({
                "evidence_id": row.get("id"),
                "month": month,
                "event": event,
                "event_label": EVENT_LABELS[event],
                "occurred_at": occurred_at,
                "title": title,
                **subject,
            })

    timelines = []
    for url, rows in grouped.items():
        rows.sort(key=lambda row: (_timestamp(row["occurred_at"]), row["event"], str(row.get("evidence_id") or "")))
        unique = []
        seen = set()
        for row in rows:
            key = (row.get("evidence_id"), row["event"], row["occurred_at"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
        first = unique[0]
        timelines.append({
            "subject_url": url,
            "repository": first["repository"],
            "kind": first["kind"],
            "number": first["number"],
            "title": unique[-1]["title"],
            "transition_count": len(unique),
            "first_observed_at": unique[0]["occurred_at"],
            "last_observed_at": unique[-1]["occurred_at"],
            "transitions": unique,
            "identity_basis": "exact_canonical_github_artifact_url",
            "interpretation_limits": [
                "no_topic_similarity_identity",
                "no_resolution_inferred",
                "no_adoption_inferred",
                "no_decision_inferred",
                "no_cross_source_causation_inferred",
            ],
        })
    return sorted(timelines, key=lambda row: (
        row["first_observed_at"], row["repository"], row["kind"], row["number"]
    ))


def render_timelines(state: dict, *, max_timelines: int = 20) -> str:
    if not isinstance(max_timelines, int) or max_timelines < 1:
        raise ValueError("max_timelines must be positive")
    timelines = [row for row in build_timelines(state) if row["transition_count"] >= 2]
    rows = [
        '<section><h2>Observed GitHub artifact timelines</h2>',
        '<p>These timelines join only lifecycle events for the exact same canonical GitHub '
        'issue or pull-request URL. Similar titles, shared terms and temporal proximity do '
        'not establish identity. Closure does not prove resolution; merge does not prove adoption.</p>',
    ]
    if not timelines:
        rows.append(
            '<p>No GitHub artifact has multiple observed lifecycle transitions in the retained months.</p>'
        )
    for timeline in timelines[:max_timelines]:
        label = timeline["repository"] + " #" + str(timeline["number"])
        rows.append(
            '<article><h3><a href="' + escape(timeline["subject_url"], quote=True) + '">' +
            escape(label) + '</a></h3><p>' + escape(timeline["title"]) + '</p><ol>'
        )
        for transition in timeline["transitions"]:
            rows.append(
                '<li><time datetime="' + escape(transition["occurred_at"], quote=True) + '">' +
                escape(transition["occurred_at"]) + '</time> — <a href="' +
                escape(transition["url"], quote=True) + '">' +
                escape(transition["event_label"]) + '</a> <small>(' +
                escape(transition["month"]) + ')</small></li>'
            )
        rows.append('</ol></article>')
    if len(timelines) > max_timelines:
        rows.append(
            '<p>' + str(len(timelines) - max_timelines) +
            ' additional multi-event artifact timelines are omitted from this bounded view.</p>'
        )
    rows.append('</section>')
    return "".join(rows)
