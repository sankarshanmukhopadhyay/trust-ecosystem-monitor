"""Combine independently sourced monthly meeting manifests without inflating coverage."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .monthly_meetings import empty_manifest, load_meetings

ORDER = {"not_checked": 0, "not_found": 1, "unavailable": 2, "not_authorized": 3, "partial": 4, "complete": 5}


def combine(period: str, manifests: list[dict]) -> dict:
    combined = empty_manifest(period)
    seen = set()
    for manifest in manifests:
        if manifest.get("period") != period:
            raise ValueError("Cannot combine different periods")
        if set(manifest.get("coverage", {})) != {"lfx", "confluence"}:
            raise ValueError("Manifest must declare both source coverage states")
        for source, status in manifest["coverage"].items():
            if status not in ORDER:
                raise ValueError("Invalid coverage state")
            previous = combined["coverage"][source]
            if status == "complete" and previous not in {"not_checked", "complete"}:
                combined["coverage"][source] = "partial"
            elif previous == "complete" and status not in {"not_checked", "complete"}:
                combined["coverage"][source] = "partial"
            elif ORDER[status] > ORDER[previous]:
                combined["coverage"][source] = status
        for record in manifest.get("records", []):
            key = (record["source"], record["url"], record["classification"])
            if key not in seen:
                seen.add(key)
                combined["records"].append(record)
    combined["records"].sort(key=lambda r: (r["occurred_at"], r["source"], r["url"]))
    return combined


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Combine LFX and Confluence monthly evidence manifests")
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("manifests", nargs="+", type=Path)
    args = parser.parse_args(argv)
    inputs = [load_meetings(path, args.month) for path in args.manifests]
    result = combine(args.month, inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    load_meetings(args.output, args.month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
