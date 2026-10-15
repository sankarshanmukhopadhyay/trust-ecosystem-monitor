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
import time
from typing import Callable


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


def previous_completed_month(now: dt.datetime | None = None) -> str:
    """Return the previous completed UTC calendar month."""
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        raise ValueError("timezone-aware UTC reference required")
    current = current.astimezone(dt.timezone.utc)
    first = dt.datetime(current.year, current.month, 1, tzinfo=dt.timezone.utc)
    previous_day = first - dt.timedelta(days=1)
    return previous_day.strftime("%Y-%m")


def in_month(value: str | None, bounds: tuple[dt.datetime, dt.datetime]) -> bool:
    if not value:
        return False
    timestamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return bounds[0] <= timestamp.astimezone(dt.timezone.utc) < bounds[1]


def github_pages(url: str, token: str, *, max_pages: int = 100,
                 progress: Callable[[dict], None] | None = None):
    """Iterate GitHub REST pages with bounded traversal diagnostics."""
    if not token:
        raise ValueError("GITHUB_TOKEN is required for historical collection")
    started = time.monotonic()
    for page in range(1, max_pages + 1):
        page_started = time.monotonic()
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
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                items = json.load(response)
            if not isinstance(items, list):
                raise ValueError("Expected GitHub REST array")
        except Exception:
            if progress:
                progress({
                    "page": page, "items": 0, "status": "failed",
                    "page_elapsed_seconds": round(time.monotonic() - page_started, 3),
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                })
            raise
        if progress:
            progress({
                "page": page, "items": len(items), "status": "complete",
                "page_elapsed_seconds": round(time.monotonic() - page_started, 3),
                "elapsed_seconds": round(time.monotonic() - started, 3),
            })
        yield from items
        if len(items) < 100:
            return
    raise RuntimeError(f"GitHub pagination safety limit reached: {url}")


def collect_month(org: str, month: str, token: str, repositories: list[str] | None = None,
                  prefixes: list[str] | None = None, max_pages: int = 100,
                  log: Callable[[str], None] | None = None) -> dict:
    bounds = month_bounds(month)
    if not isinstance(max_pages, int) or not 1 <= max_pages <= 100:
        raise ValueError("max_pages must be between 1 and 100")
    root = f"https://api.github.com/orgs/{urllib.parse.quote(org, safe='')}/repos?type=public"
    evidence = []
    coverage = []
    seen_repositories = set()
    traversal = []
    collection_started = time.monotonic()
    emit = log or (lambda message: None)

    def progress_for(repository: str, endpoint: str):
        record = {
            "repository": repository, "endpoint": endpoint, "pages_fetched": 0,
            "items_fetched": 0, "last_page": 0, "elapsed_seconds": 0.0,
            "status": "not_started",
        }
        traversal.append(record)

        def update(event: dict) -> None:
            record["pages_fetched"] = max(record["pages_fetched"], int(event.get("page", 0)))
            record["items_fetched"] += int(event.get("items", 0))
            record["last_page"] = int(event.get("page", 0))
            record["elapsed_seconds"] = float(event.get("elapsed_seconds", 0.0))
            record["status"] = str(event.get("status", "unknown"))
            emit(
                "TEM GitHub traversal: "
                f"repo={repository} endpoint={endpoint} page={record['last_page']} "
                f"items={event.get('items', 0)} elapsed={record['elapsed_seconds']:.3f}s "
                f"status={record['status']}"
            )
        return update
    if repositories is not None:
        for name in repositories:
            if not name.startswith(org + "/") or name.count("/") != 1:
                raise ValueError(f"Repository outside configured organization: {name}")
        repo_source = ({"full_name": name} for name in repositories)
    else:
        repo_source = None
    try:
        discovered = list(
            repo_source if repo_source is not None else
            github_pages(root, token, max_pages=max_pages,
                         progress=progress_for(org + "/*", "repositories"))
        )
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
        return {
            "schema_version": "1", "ecosystem": org, "period": month,
            "methodology": "Historical GitHub issue and PR lifecycle events; discovery failed",
            "evidence": [], "coverage": [{"repository": org + "/*", "issues": "not_checked", "pull_requests": "not_checked", "discovery": f"unavailable: {type(exc).__name__}: {exc}"}],
            "coverage_complete": False, "external_sources": {"confluence": "not_checked", "lfx": "not_checked"},
            "collection_scope": "repository discovery failed; no claim of completeness",
            "collection_budget": {"max_pages_per_endpoint": max_pages, "page_size": 100},
            "traversal_diagnostics": traversal,
            "collection_elapsed_seconds": round(time.monotonic() - collection_started, 3),
        }
    for repo_index, repo in enumerate(discovered, start=1):
        name = repo["full_name"]
        if prefixes and not any(name.split("/", 1)[1].startswith(prefix) for prefix in prefixes):
            continue
        if name in seen_repositories:
            continue
        seen_repositories.add(name)
        emit(f"TEM GitHub traversal: repository [{repo_index}/{len(discovered)}] {name}")
        base = f"https://api.github.com/repos/{name}"
        status = {"repository": name, "issues": "complete", "pull_requests": "complete"}
        for kind, endpoint in (("issues", "issues?state=all"), ("pull_requests", "pulls?state=all")):
            try:
                for item in github_pages(
                    f"{base}/{endpoint}", token, max_pages=max_pages,
                    progress=progress_for(name, kind),
                ):
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
        "coverage_complete": bool(coverage) and all(entry["issues"] == "complete" and entry["pull_requests"] == "complete" for entry in coverage),
        "external_sources": {"confluence": "not_checked", "lfx": "not_checked"},
        "collection_scope": ("explicit repositories: " + ", ".join(repositories)) if repositories is not None else ("public organization repositories matching prefixes: " + ", ".join(prefixes) if prefixes else "all public organization repositories; admission-tier filtering not yet applied"),
        "collection_budget": {"max_pages_per_endpoint": max_pages, "page_size": 100},
        "traversal_diagnostics": traversal,
        "collection_elapsed_seconds": round(time.monotonic() - collection_started, 3),
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
    lines.append(f"Collection scope: {result['collection_scope']}.")
    lines.append("")
    for item in result["evidence"]:
        lines.append(f"- {item['occurred_at'][:10]} — {item['repository']}: {item['kind']} #{item['id'].split(':')[-2]} {item['event']} — [{item['title'].replace(chr(10), ' ')}]({item['url']})")
    lines.extend(["", "## Source coverage", ""])
    for entry in result["coverage"]:
        lines.append(f"- {entry['repository']}: issues={entry['issues']}; PRs={entry['pull_requests']}")
    lines.extend(["- Confluence: not checked", "- LFX: not checked", "", "## Interpretation limits", "", "- No inference of inactivity from absent evidence.", "- No inference of decisions, deliverables, or completion from GitHub event counts.", "- Historical issue/PR state transitions may be incomplete.", ""])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Collect bounded monthly GitHub evidence")
    parser.add_argument("--org", default="trustoverip")
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", action="append", dest="repos", help="Bound collection to explicit owner/repository; repeat as needed")
    parser.add_argument("--prefix", action="append", dest="prefixes", help="Select public organization repositories by name prefix; repeatable")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum GitHub REST pages per endpoint (1-100)")
    args = parser.parse_args(argv)
    result = collect_month(args.org, args.month, os.environ.get("GITHUB_TOKEN", ""), repositories=args.repos, prefixes=args.prefixes, max_pages=args.max_pages)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{args.month}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output / f"{args.month}.md").write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
