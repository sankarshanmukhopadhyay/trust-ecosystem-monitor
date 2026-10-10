"""Compact, cited monthly portfolio overview from GitHub lifecycle evidence."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

PREFIXES = {"dtgwg-": "DTG", "tswg-": "TSWG", "aimwg-": "AIMWG", "ctwg-": "CTWG", "egwg-": "EGWG"}


def portfolio(repository: str) -> str:
    name = repository.split("/", 1)[-1].lower()
    return next((label for prefix, label in PREFIXES.items() if name.startswith(prefix)), "Other / unclassified")


def render(manifest: dict, *, examples_per_portfolio: int = 8) -> str:
    evidence = manifest["evidence"]
    buckets = defaultdict(list)
    scoped_groups = {portfolio(row["repository"]) for row in manifest["coverage"] if row["repository"].count("/") == 1}
    for item in evidence:
        buckets[portfolio(item["repository"])].append(item)
    lines = [
        f"# ToIP GitHub portfolio activity overview — {manifest['period']}", "",
        "> Independent evidence overview. Event counts are not distinct work items or proof of delivery, decisions or impact.", "",
        f"**Scope:** {manifest['collection_scope']}.", "",
        f"**Coverage:** {'complete within selected repositories' if manifest['coverage_complete'] else 'incomplete; consult source manifest'}.", "",
        f"**Repositories checked:** {len(manifest['coverage'])}. **Observed lifecycle events:** {len(evidence)}.", "",
        "## Portfolio overview", "",
        "| Portfolio | Repositories with events | Opened | Closed | Merged |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for group in sorted(scoped_groups | set(buckets)):
        items = buckets[group]
        counts = Counter(item["event"] for item in items)
        lines.append(f"| {group} | {len(set(item['repository'] for item in items))} | {counts['opened']} | {counts['closed']} | {counts['merged']} |")
    if not buckets:
        lines.append("| No observed events | 0 | 0 | 0 | 0 |")
    lines.extend(["", "## Selected source-linked observations", ""])
    for group in sorted(scoped_groups | set(buckets)):
        items = buckets[group]
        lines.extend([f"### {group}", ""])
        if not items:
            lines.extend(["No lifecycle events observed in the selected repositories for this portfolio. This does not establish inactivity.", ""])
            continue
        # A merged PR is an observable transition, not an independently verified deliverable.
        priority = {"merged": 0, "closed": 1, "opened": 2}
        chosen = sorted(items, key=lambda x: (priority.get(x["event"], 3), x["occurred_at"], x["id"]))[:examples_per_portfolio]
        for item in chosen:
            title = item.get("title", "").replace("\n", " ").replace("|", "-")
            lines.append(f"- {item['occurred_at'][:10]}: {item['repository']} {item['kind']} {item['event']} — [{title}]({item['url']})")
        lines.append("")
    lines.extend([
        "## Evidence and interpretation limits", "",
        "- This overview samples linked observations; consult the complete monthly JSON and Markdown evidence registers.",
        "- A merged PR may also be counted as a closed PR. Do not sum event counts as unique items.",
        "- Issue and PR lifecycle events do not establish discussions, decisions, meeting attendance, or verified outcomes.",
        "- LFX and Confluence evidence are not included unless independently imported and validated.",
        "- No inference of inactivity from missing events or of maturity from event volume.", "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render a bounded monthly GitHub portfolio overview")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = render(json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
