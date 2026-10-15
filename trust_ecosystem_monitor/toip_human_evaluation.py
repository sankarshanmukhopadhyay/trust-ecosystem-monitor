"""Prepare deterministic packets for independent human evaluation of TEM ToIP output.

This module selects retained source-linked evidence. It does not perform the
human review, verify meeting occurrence, or admit new source claims.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .toip_annual_state import validate
from .toip_subject_timeline import canonical_subject

DEFAULT_MONTHS = ("2026-08", "2026-09")
RUBRIC = [
    {
        "dimension": "relevance",
        "question": "Does the TEM presentation surface the evidence that matters for understanding the observed work?",
    },
    {
        "dimension": "important_omission",
        "question": "Is important source-linked context absent or materially underrepresented?",
    },
    {
        "dimension": "unsupported_claims",
        "question": "Does any wording imply a decision, resolution, adoption, meeting occurrence or authority not established by the cited evidence?",
    },
    {
        "dimension": "traceability",
        "question": "Can a reviewer trace each substantive statement or lifecycle transition back to the cited source?",
    },
    {
        "dimension": "reader_comprehension",
        "question": "Can a careful reader distinguish observation, interpretation, uncertainty and authority boundaries?",
    },
]


def _github_sample(evidence: list[dict], limit: int) -> list[dict]:
    grouped = {}
    for row in evidence:
        subject = canonical_subject(row.get("url"))
        key = subject["url"]
        item = grouped.setdefault(key, {
            "url": key,
            "repository": subject["repository"],
            "kind": subject["kind"],
            "number": subject["number"],
            "title": str(row.get("title", "")).strip().replace("\n", " "),
            "events": [],
        })
        item["events"].append({
            "event": row.get("event"),
            "occurred_at": row.get("occurred_at"),
            "evidence_id": row.get("id"),
        })
    result = []
    for item in grouped.values():
        item["events"].sort(key=lambda event: (
            str(event.get("occurred_at") or ""),
            str(event.get("event") or ""),
            str(event.get("evidence_id") or ""),
        ))
        result.append(item)
    result.sort(key=lambda item: (item["repository"], item["kind"], item["number"]))
    return result[:limit]


def _confluence_sample(sources: list[dict], limit: int) -> list[dict]:
    sample = []
    for page in sorted(sources, key=lambda p: str(p.get("id", ""))):
        page_id = str(page.get("id", ""))
        if not page_id.isdigit():
            raise ValueError("invalid Confluence source id")
        url = page.get("url") or (
            "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/" + page_id
        )
        sample.append({
            "id": page_id,
            "url": url,
            "title": str(page.get("title", ""))[:160],
            "version": page.get("version"),
            "page_kind": page.get("page_kind", "unknown"),
            "github_references": list(page.get("github_references", []))[:8],
            "meeting_status": "not_established",
            "authority_status": "not_established",
            "body_republished": False,
        })
        if len(sample) >= limit:
            break
    return sample


def build_packet(
    state: dict,
    *,
    months: tuple[str, ...] = DEFAULT_MONTHS,
    max_github_per_month: int = 5,
    max_confluence_per_month: int = 3,
) -> dict:
    """Select deterministic evidence samples without performing the review."""
    validate(state)
    if not months or max_github_per_month < 1 or max_confluence_per_month < 1:
        raise ValueError("invalid evaluation sampling bounds")
    selected = []
    for month in months:
        entry = state["months"].get(month)
        if entry is None:
            selected.append({
                "month": month,
                "status": "not_retained",
                "github_artifacts": [],
                "confluence_sources": [],
            })
            continue
        observation = entry["observation"]
        selected.append({
            "month": month,
            "status": "retained",
            "observed_at": entry["observed_at"],
            "github_artifacts": _github_sample(
                observation["github"].get("evidence", []), max_github_per_month
            ),
            "confluence_sources": _confluence_sample(
                observation["confluence"].get("sources", []), max_confluence_per_month
            ),
        })
    return {
        "schema": "tem-human-evaluation-packet-v1",
        "annual_schema": state["schema"],
        "year": state["year"],
        "review_status": "awaiting_independent_human_review",
        "meeting_evidence_status": "not_established_by_packet",
        "source_admission_status": "unchanged",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sampling": {
            "months": list(months),
            "max_github_per_month": max_github_per_month,
            "max_confluence_per_month": max_confluence_per_month,
            "method": "deterministic_sorted_source_metadata",
        },
        "samples": selected,
        "rubric": RUBRIC,
        "reviewer": {
            "identifier": None,
            "reviewed_at": None,
            "independence_basis": None,
            "overall_disposition": None,
            "findings": [],
        },
        "boundary": (
            "Packet preparation is not independent human evaluation. Confluence bodies are "
            "not republished, meeting occurrence and authority are not established, and "
            "source admission remains governed separately."
        ),
    }


def render_markdown(packet: dict) -> str:
    if packet.get("schema") != "tem-human-evaluation-packet-v1":
        raise ValueError("invalid human evaluation packet")
    lines = [
        "# TEM ToIP independent human evaluation packet",
        "",
        f"Status: **{packet['review_status']}**",
        "",
        "> Packet preparation is not the independent review. Meeting occurrence, decisions, "
        "adoption and authority remain unestablished unless independently evidenced.",
        "",
        "## Reviewer record",
        "",
        "- Reviewer identifier:",
        "- Reviewed at:",
        "- Independence basis:",
        "- Overall disposition:",
        "",
        "## Review rubric",
        "",
    ]
    for row in packet["rubric"]:
        lines.append(f"- **{row['dimension']}** — {row['question']}")
    for sample in packet["samples"]:
        lines.extend(["", f"## {sample['month']} sample", ""])
        if sample["status"] != "retained":
            lines.append("No retained annual observation is available for this month.")
            continue
        lines.append("### GitHub artifacts")
        if not sample["github_artifacts"]:
            lines.append("- None selected.")
        for artifact in sample["github_artifacts"]:
            events = ", ".join(
                f"{event.get('event')} @ {event.get('occurred_at')}"
                for event in artifact["events"]
            )
            lines.append(
                f"- [{artifact['repository']} #{artifact['number']}]({artifact['url']}) — "
                f"{artifact['title']} — {events}"
            )
        lines.extend(["", "### Confluence source metadata", ""])
        if not sample["confluence_sources"]:
            lines.append("- None selected.")
        for source in sample["confluence_sources"]:
            lines.append(
                f"- [{source['title']}]({source['url']}) — version {source['version']}; "
                f"page kind={source['page_kind']}; meeting_status={source['meeting_status']}; "
                "body_republished=false"
            )
        lines.extend([
            "",
            "### Reviewer findings for this sample",
            "",
            "- Relevance:",
            "- Important omissions:",
            "- Unsupported claims:",
            "- Traceability:",
            "- Reader comprehension:",
            "- Required corrections:",
        ])
    lines.extend([
        "",
        "## Completion rule",
        "",
        "C5 is not complete until an independent human reviewer fills the reviewer record, "
        "evaluates the sampled outputs against the rubric, records findings/corrections, and "
        "the resulting disposition is linked back to the umbrella issue.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--month", action="append", dest="months")
    args = parser.parse_args(argv)
    state = json.loads(args.manifest.read_text(encoding="utf-8"))
    packet = build_packet(state, months=tuple(args.months or DEFAULT_MONTHS))
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(packet) + "\n", encoding="utf-8")
    print("Human evaluation packet:", args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
