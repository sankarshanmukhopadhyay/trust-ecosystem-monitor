"""Render source-aware historical monthly activity reports.

The report explicitly separates observed events, curated meeting claims,
and evidence gaps. It does not promote discussions into decisions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .monthly_meetings import empty_manifest, load_meetings


def render(github: dict, meetings: dict) -> str:
    if github["period"] != meetings["period"]:
        raise ValueError("Report period mismatch")
    period = github["period"]
    groups: dict[str, list[dict]] = {}
    for record in meetings["records"]:
        groups.setdefault(record["group"], []).append(record)
    lines = [
        f"# ToIP monthly activity report — {period}",
        "",
        "> Independent evidence-based report, not an official ToIP decision record.",
        "",
        "## Source coverage",
        "",
        f"- GitHub: {'complete for enumerated repositories' if github['coverage_complete'] else 'partial or unavailable'}",
        f"- GitHub scope: {github['collection_scope']}",
        f"- Confluence: {meetings['coverage']['confluence']}",
        f"- LFX: {meetings['coverage']['lfx']}",
        "",
        "## Observed GitHub activity",
        "",
    ]
    if github["evidence"]:
        for item in github["evidence"]:
            lines.append(f"- {item['occurred_at'][:10]}: {item['repository']} {item['kind']} {item['event']} — [{item['title'].replace(chr(10), ' ')}]({item['url']})")
    else:
        lines.append("No events observed in collected GitHub evidence. This does not establish inactivity.")
    lines.extend(["", "## Meeting-derived observations by WG/TF", ""])
    if not groups:
        lines.append("No authorized meeting evidence was supplied; no conclusions about meeting activity are possible.")
    for group in sorted(groups):
        lines.extend([f"### {group}", ""])
        for item in sorted(groups[group], key=lambda r: (r["occurred_at"], r["url"])):
            lines.append(f"- **{item['classification']}** ({item['occurred_at'][:10]}, {item['source']}): {item['summary']} ([source]({item['url']}))")
        lines.append("")
    lines.extend([
        "## Unresolved evidence questions",
        "",
        "- What meeting records are publicly available and authorized for reuse?",
        "- Which GitHub repositories are within the governed reporting scope?",
        "- Which reported discussions resulted in independently documented decisions?",
        "",
        "## Limitations",
        "",
        "- Event counts are not measures of progress or organizational maturity.",
        "- GitHub lifecycle snapshots do not reconstruct every historical transition.",
        "- Missing meeting records must not be interpreted as missing meetings.",
        "- No deliverable or decision is asserted without a source record.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render a monthly evidence-backed ToIP report")
    parser.add_argument("github_manifest", type=Path)
    parser.add_argument("--meetings", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    github = json.loads(args.github_manifest.read_text(encoding="utf-8"))
    meetings = load_meetings(args.meetings, github["period"]) if args.meetings else empty_manifest(github["period"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(github, meetings), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
