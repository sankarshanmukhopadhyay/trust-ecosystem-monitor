"""Read-only, bounded Confluence page metadata discovery.

Only records page IDs, canonical links, creation/update timestamps and
pagination metadata. Does not retrieve page bodies, comments or user records.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

BASE = "https://lf-toip.atlassian.net"
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_PAGES = 50
MAX_BATCHES = 5


def discover(*, opener=urlopen, limit: int = 25, max_batches: int = 1, month: str | None = None) -> dict:
    if not 1 <= limit <= MAX_PAGES or not 1 <= max_batches <= MAX_BATCHES:
        raise ValueError("discovery bounds exceeded")
    month_start = month_end = None
    if month is not None:
        try:
            month_start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
            month_end = datetime(month_start.year + (month_start.month == 12), month_start.month % 12 + 1, 1, tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError("month must be YYYY-MM") from exc
    url = BASE + "/wiki/api/v2/pages?" + urlencode({"limit": limit})
    result = {"source": "confluence_v2_public_pages", "endpoint": url, "coverage": "not_checked", "pages": [], "batches_fetched": 0}
    visited = set()
    seen_ids = set()
    while url and result["batches_fetched"] < max_batches:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != urlsplit(BASE).netloc or not parsed.path.startswith("/wiki/api/v2/pages"):
            return {**result, "coverage": "unavailable", "reason": "unsafe_next_page_url"}
        if url in visited:
            return {**result, "coverage": "unavailable", "reason": "pagination_cycle"}
        visited.add(url)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "TEM-Public-Metadata-Discovery/1.0"})
        try:
            with opener(request, timeout=15) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
                if len(payload) > MAX_RESPONSE_BYTES:
                    return {**result, "coverage": "unavailable", "reason": "response_limit_exceeded"}
                data = json.loads(payload)
        except HTTPError as exc:
            return {**result, "coverage": "unavailable", "http_status": exc.code}
        except (URLError, TimeoutError, OSError, ValueError, UnicodeError) as exc:
            return {**result, "coverage": "unavailable", "reason": type(exc).__name__}
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            return {**result, "coverage": "unavailable", "reason": "unexpected_schema"}
        result["batches_fetched"] += 1
        for item in data["results"][:limit]:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            identifier = str(item["id"])
            if identifier in seen_ids:
                continue
            seen_ids.add(identifier)
            result["pages"].append({
                "id": identifier,
                "space_id": str(item.get("spaceId", "")),
                "created_at": item.get("createdAt"),
                "version_created_at": (item.get("version") or {}).get("createdAt") if isinstance(item.get("version"), dict) else None,
                "web_url": (item.get("_links") or {}).get("webui") if isinstance(item.get("_links"), dict) else None,
            })
        links = data.get("_links") if isinstance(data.get("_links"), dict) else {}
        next_link = links.get("next")
        url = urljoin(BASE, next_link) if isinstance(next_link, str) and next_link else None
    result["next_page_present"] = bool(url)
    if month_start is not None:
        selected = []
        unknown = 0
        for page in result["pages"]:
            stamp = page.get("version_created_at") or page.get("created_at")
            try:
                parsed_date = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else None
                if parsed_date is None or parsed_date.tzinfo is None:
                    unknown += 1
                    continue
                if month_start <= parsed_date.astimezone(timezone.utc) < month_end:
                    selected.append(page)
            except ValueError:
                unknown += 1
        result["month_filter"] = month
        result["month_match_count"] = len(selected)
        result["unknown_timestamp_count"] = unknown
        result["pages"] = selected
        result["filter_semantics"] = "latest-version-created-at or page-created-at; not an activity event history"

    result["coverage"] = "sample_only"
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--month", default=None)
    args = parser.parse_args()
    result = discover(limit=args.limit, max_batches=args.max_batches, month=args.month)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
