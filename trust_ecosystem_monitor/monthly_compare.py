"""Compare two independently collected monthly evidence manifests.

Comparisons describe observed GitHub event differences, not inferred progress.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def compare(earlier: dict, later: dict) -> dict:
    if earlier["ecosystem"] != later["ecosystem"]:
        raise ValueError("Cannot compare different ecosystems")
    if earlier["period"] >= later["period"]:
        raise ValueError("Periods must be in ascending order")
    def group(manifest: dict) -> dict:
        groups: dict[str, dict] = {}
        for item in manifest["evidence"]:
            entry = groups.setdefault(item["repository"], {"opened": 0, "closed": 0, "merged": 0, "evidence": []})
            entry[item["event"]] += 1
            entry["evidence"].append(item["url"])
        return groups
    before, after = group(earlier), group(later)
    names = sorted(set(before) | set(after))
    return {
        "schema_version": "1",
        "ecosystem": earlier["ecosystem"],
        "periods": [earlier["period"], later["period"]],
        "coverage": {
            earlier["period"]: earlier["coverage_complete"],
            later["period"]: later["coverage_complete"],
        },
        "repositories": [
            {"repository": name, "earlier": before.get(name, {}), "later": after.get(name, {})}
            for name in names
        ],
        "interpretation": "Observed lifecycle-event comparison only; absence of events is not inactivity",
    }


def render_markdown(result: dict) -> str:
    first, second = result["periods"]
    lines = [
        f"# {result['ecosystem']} GitHub evidence comparison: {first} → {second}",
        "",
        "> Independent partial evidence. Counts are observed issue/PR events, not measures of organizational progress.",
        "",
        "## Collection coverage",
        "",
        f"- {first}: {'complete for enumerated repositories' if result['coverage'][first] else 'incomplete'}",
        f"- {second}: {'complete for enumerated repositories' if result['coverage'][second] else 'incomplete'}",
        "",
        "## Repository event comparison",
        "",
        "| Repository | Earlier opened / closed / merged | Later opened / closed / merged |",
        "| --- | --- | --- |",
    ]
    for row in result["repositories"]:
        def counts(item: dict) -> str:
            return " / ".join(str(item.get(key, 0)) for key in ("opened", "closed", "merged"))
        lines.append(f"| {row['repository']} | {counts(row['earlier'])} | {counts(row['later'])} |")
    lines.extend(["", "## Interpretation limits", "", "- No inference of decisions, delivery, organizational inactivity or maturity.", "- The same work item can generate multiple lifecycle events.", "- The comparison does not include Confluence or LFX until independently collected and verified.", ""])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compare two monthly evidence manifests")
    parser.add_argument("earlier", type=Path)
    parser.add_argument("later", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    first = json.loads(args.earlier.read_text(encoding="utf-8"))
    second = json.loads(args.later.read_text(encoding="utf-8"))
    result = compare(first, second)
    args.output.mkdir(parents=True, exist_ok=True)
    stem = f"{result['periods'][0]}-to-{result['periods'][1]}"
    (args.output / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output / f"{stem}.md").write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
