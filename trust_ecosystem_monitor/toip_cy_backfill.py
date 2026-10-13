"""Backfill missing ToIP calendar-year months with GitHub-only evidence.

This module intentionally does not expand Confluence, LFX, Zoom, meeting or
cross-source claims. It fills missing annual months from bounded GitHub issue
and pull-request lifecycle observations, then renders the annual report with
empty Confluence source sets for those backfilled months.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .monthly import collect_month, month_bounds, render_markdown
from .toip_annual import publish
from .toip_annual_state import read

DEFAULT_PREFIXES = ["dtgwg-", "tswg-", "aimwg-", "ctwg-", "egwg-"]


def _month_tuple(month: str) -> tuple[int, int]:
    month_bounds(month)
    year, number = month.split("-", 1)
    return int(year), int(number)


def month_range(start: str, end: str) -> list[str]:
    """Return inclusive YYYY-MM range after validating both endpoints."""
    sy, sm = _month_tuple(start)
    ey, em = _month_tuple(end)
    if (ey, em) < (sy, sm):
        raise ValueError("end month must not precede start month")
    months: list[str] = []
    year, month = sy, sm
    while (year, month) <= (ey, em):
        months.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return months


def previous_completed_month(now: datetime | None = None) -> str:
    """Return the last closed UTC calendar month as YYYY-MM."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("current time must be timezone-aware")
    current = current.astimezone(timezone.utc)
    year, month = current.year, current.month
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def github_only_content(month: str) -> dict:
    """Create an explicit empty-Confluence observation for GitHub-only backfill.

    The annual publisher currently accepts `sample_only` Confluence coverage.
    We therefore represent the gated source set as an empty sample while the
    backfill summary and workflow/docs carry the explicit GitHub-only boundary.
    """
    month_bounds(month)
    return {
        "month": month,
        "coverage": "sample_only",
        "pages": [],
        "unavailable_count": 0,
        "boundary": (
            "CY backfill intentionally records GitHub-only evidence. "
            "It does not retrieve, summarize or admit Confluence, LFX, Zoom, "
            "meeting or cross-source evidence."
        ),
    }


def _month_present(site: Path, month: str) -> bool:
    year = int(month[:4])
    manifest = site / str(year) / "data" / "manifest.json"
    if not manifest.exists():
        return False
    return month in read(manifest, year)["months"]


def _write_github_result(output: Path, month: str, result: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{month}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output / f"{month}.md").write_text(render_markdown(result), encoding="utf-8")


def backfill(
    *,
    org: str,
    start: str,
    end: str,
    github_dir: Path,
    site: Path,
    token: str,
    prefixes: list[str] | None = None,
    force: bool = False,
    collector=collect_month,
    publisher=publish,
    observed_at: str | None = None,
) -> dict:
    """Collect and publish missing months, returning a machine-readable summary."""
    selected_prefixes = prefixes if prefixes is not None else list(DEFAULT_PREFIXES)
    summary = {
        "org": org,
        "start": start,
        "end": end,
        "scope": "github_only_backfill_no_confluence_or_lfx",
        "prefixes": selected_prefixes,
        "processed": [],
        "skipped_existing": [],
        "github_unavailable": [],
    }
    for month in month_range(start, end):
        if _month_present(site, month) and not force:
            summary["skipped_existing"].append(month)
            continue
        result = collector(org, month, token, prefixes=selected_prefixes)
        if not result.get("coverage_complete"):
            summary["github_unavailable"].append(month)
        _write_github_result(github_dir, month, result)
        publisher(
            month,
            github_dir,
            site,
            content_collect=github_only_content,
            tracked_collect=lambda ids: {"pages": [], "unavailable": []},
            observed_at=observed_at,
        )
        summary["processed"].append(month)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill missing ToIP CY GitHub-only evidence")
    parser.add_argument("--org", default="trustoverip")
    parser.add_argument("--start", default="2026-01")
    parser.add_argument("--end", default=None, help="Inclusive YYYY-MM end; defaults to last closed UTC month")
    parser.add_argument("--github-dir", required=True, type=Path)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--prefix", action="append", dest="prefixes", help="Repository prefix to include; repeatable")
    parser.add_argument("--force", action="store_true", help="Reprocess months already present in the annual manifest")
    parser.add_argument("--summary", type=Path, help="Optional JSON summary output path")
    args = parser.parse_args(argv)

    end = args.end or previous_completed_month()
    summary = backfill(
        org=args.org,
        start=args.start,
        end=end,
        github_dir=args.github_dir,
        site=args.site,
        token=os.environ.get("GITHUB_TOKEN", ""),
        prefixes=args.prefixes,
        force=args.force,
    )
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
