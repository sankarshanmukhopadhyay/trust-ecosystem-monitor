"""Import an authorized LFX meeting export into bounded monthly source evidence.

The input is a locally provided, already authorized JSON export. No private
API endpoints or authentication flows are assumed. Imported meeting entries
are observations, never automatically classified as decisions or deliverables.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from .monthly_meetings import empty_manifest, load_meetings


def convert_lfx_export(payload: dict, period: str) -> dict:
    meetings = payload.get("meetings")
    if not isinstance(meetings, list):
        raise ValueError("LFX export must contain a meetings array")
    result = empty_manifest(period, lfx="partial")
    seen = set()
    for meeting in meetings:
        if not isinstance(meeting, dict):
            raise ValueError("LFX meeting must be an object")
        occurred = meeting.get("started_at")
        if not isinstance(occurred, str):
            raise ValueError("LFX meeting requires started_at")
        try:
            when = dt.datetime.fromisoformat(occurred.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid LFX meeting timestamp") from exc
        if when.tzinfo is None:
            raise ValueError("LFX meeting timestamp must include timezone")
        if when.astimezone(dt.timezone.utc).strftime("%Y-%m") != period:
            continue
        url = meeting.get("url")
        group = meeting.get("group")
        title = meeting.get("title")
        if not all(isinstance(v, str) and v.strip() for v in (url, group, title)):
            raise ValueError("LFX meeting requires URL, group and title")
        if not url.startswith("https://"):
            raise ValueError("LFX evidence URL must be HTTPS")
        key = (url, when.isoformat())
        if key in seen:
            continue
        seen.add(key)
        result["records"].append({
            "source": "lfx",
            "url": url,
            "occurred_at": when.astimezone(dt.timezone.utc).isoformat(),
            "group": group,
            "classification": "discussion",
            "summary": "Meeting listed: " + title,
        })
    result["records"].sort(key=lambda item: (item["occurred_at"], item["url"]))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Import authorized LFX meeting export")
    parser.add_argument("export", type=Path)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.export.read_text(encoding="utf-8"))
    result = convert_lfx_export(payload, args.month)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    load_meetings(args.output, args.month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
