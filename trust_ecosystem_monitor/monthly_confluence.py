"""Import authorized Confluence page metadata into monthly evidence manifests.

This adapter does not scrape private spaces or infer decisions from page titles.
It requires an authorized, curated JSON export with stable HTTPS page URLs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from .monthly_meetings import empty_manifest, load_meetings


def convert_confluence_export(payload: dict, period: str) -> dict:
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ValueError("Confluence export must contain a pages array")
    result = empty_manifest(period, confluence="partial")
    seen = set()
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Confluence page must be an object")
        updated = page.get("updated_at")
        if not isinstance(updated, str):
            raise ValueError("Confluence page requires updated_at")
        try:
            when = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid Confluence page timestamp") from exc
        if when.tzinfo is None:
            raise ValueError("Confluence timestamp must include timezone")
        if when.astimezone(dt.timezone.utc).strftime("%Y-%m") != period:
            continue
        url, group, title = (page.get(key) for key in ("url", "group", "title"))
        if not all(isinstance(value, str) and value.strip() for value in (url, group, title)):
            raise ValueError("Confluence page requires URL, group and title")
        if not url.startswith("https://"):
            raise ValueError("Confluence evidence URL must be HTTPS")
        version = page.get("version")
        if version is not None and (not isinstance(version, int) or isinstance(version, bool) or version < 1):
            raise ValueError("Confluence version must be a positive integer")
        key = (url, version)
        if key in seen:
            continue
        seen.add(key)
        summary = "Page updated: " + title
        if version is not None:
            summary += f" (version {version})"
        result["records"].append({
            "source": "confluence",
            "url": url,
            "occurred_at": when.astimezone(dt.timezone.utc).isoformat(),
            "group": group,
            "classification": "discussion",
            "summary": summary,
        })
    result["records"].sort(key=lambda item: (item["occurred_at"], item["url"]))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Import authorized Confluence page metadata")
    parser.add_argument("export", type=Path)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.export.read_text(encoding="utf-8"))
    result = convert_confluence_export(payload, args.month)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    load_meetings(args.output, args.month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
