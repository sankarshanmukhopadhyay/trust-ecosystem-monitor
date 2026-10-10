"""Portable, bounded GitHub evidence collector for historical monthly reporting.

This module is intentionally independent of the weekly observation state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


def month_bounds(month: str) -> tuple[dt.datetime, dt.datetime]:
    try:
        year, number = (int(part) for part in month.split("-"))
        first = dt.datetime(year, number, 1, tzinfo=dt.timezone.utc)
    except (ValueError, TypeError) as exc:
        raise ValueError("month must be YYYY-MM") from exc
    if month != first.strftime("%Y-%m"):
        raise ValueError("month must be YYYY-MM")
    if number == 12:
        following = dt.datetime(year + 1, 1, 1, tzinfo=dt.timezone.utc)
    else:
        following = dt.datetime(year, number + 1, 1, tzinfo=dt.timezone.utc)
    return first, following


def in_month(value: str | None, bounds: tuple[dt.datetime, dt.datetime]) -> bool:
    if not value:
        return False
    timestamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return bounds[0] <= timestamp.astimezone(dt.timezone.utc) < bounds[1]


def github_pages(url: str, token: str, *, max_pages: int = 100):
    """Iterate GitHub REST pages; fail visibly rather than silently truncate."""
    if not token:
        raise ValueError("GITHUB_TOKEN is required for historical collection")
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in url else "?"
        request = urllib.request.Request(
            f"{url}{separator}per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "trust-ecosystem-monitor-monthly",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            items = json.load(response)
        if not isinstance(items, list):
            raise ValueError("Expected GitHub REST array")
        yield from items
        if len(items) < 100:
            return
    raise RuntimeError(f"GitHub pagination safety limit reached: {url}")


def collect_month(org: str, month: str, token: str) -> dict:
    bounds = month_bounds(month)
    root = f"https://api.github.com/orgs/{urllib.parse.quote(org, safe='')}/repos?type=public"
    evidence = []
    coverage = []
    seen_repositories = set()
    for repo in github_pages(root, token):
        name = repo["full_name"]
        if name in seen_repositories:
            continue
        seen_repositories.add(name)
        base = f"https://api.github.com/repos/{name}"
        status = {"repository": name, "issues": "complete", "pull_requests": "complete"}
        for kind, endpoint in (("issues", "issues?state=all"), ("pull_requests", "pulls?state=all")):
            try:
                for item in github_pages(f"{base}/{endpoint}", token):
                    if kind == "issues" and "pull_request" in item:
                        continue
                    for event, field in (("opened", "created_at"), ("closed", "closed_at"), ("merged", "merged_at")):
                        if event == "merged" and kind != "pull_requests":
                            continue
                        if in_month(item.get(field), bounds):
                            evidence.append({
                                "id": f"github:{name}:{kind}:{item['number']}:{event}",
                                "source": "github",
                                "repository": name,
                                "kind": kind,
                                "event": event,
                                "occurred_at": item[field],
                                "url": item["html_url"],
                                "title": item.get("title", ""),
                            })
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, RuntimeError, KeyError) as exc:
                status[kind] = f"unavailable: {type(exc).__name__}: {exc}"
        coverage.append(status)
    evidence = list({entry["id"]: entry for entry in evidence}.values())
    evidence.sort(key=lambda e: (e["occurred_at"], e["id"]))
    return {
        "schema_version": "1",
        "ecosystem": org,
        "period": month,
        "methodology": "Historical GitHub issue and PR lifecycle events; not a complete record of work or decisions",
        "evidence": evidence,
        "coverage": coverage,
        "coverage_complete": all(entry["issues"] == "complete" and entry["pull_requests"] == "complete" for entry in coverage),
        "external_sources": {"confluence": "not_checked", "lfx": "not_checked"},
    }


def render_markdown(result: dict) -> str:
    month = result["period"]
    lines = [
        f"# {result['ecosystem']} activity evidence — {month}",
        "",
        "> Independent prototype. GitHub issue/PR lifecycle events are not proof of organizational decisions or completed deliverables.",
        "",
        f"Observed events: **{len(result['evidence'])}**.",
        "",
        "## Evidence",
        "",
    ]
    lines.append(f"GitHub collection complete for enumerated repositories: **{result['coverage_complete']}**.")
    lines.append("")
    for item in result["evidence"]:
        lines.append(f"- {item['occurred_at'][:10]} — {item['repository']}: {item['kind']} #{item['id'].split(':')[-2]} {item['event']} — [{item['title'].replace(chr(10), ' ')}]({item['url']})")
    lines.extend(["", "## Source coverage", ""])
    for entry in result["coverage"]:
        lines.append(f"- {entry['repository']}: issues={entry['issues']}; PRs={entry['pull_requests']}")
    lines.extend(["- Confluence: not checked", "- LFX: not checked", ""])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Collect bounded monthly GitHub evidence")
    parser.add_argument("--org", default="trustoverip")
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = collect_month(args.org, args.month, os.environ.get("GITHUB_TOKEN", ""))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{args.month}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output / f"{args.month}.md").write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
