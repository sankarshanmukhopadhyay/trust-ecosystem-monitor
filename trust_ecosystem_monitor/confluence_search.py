"""Bounded, unauthenticated Confluence CQL historical-search diagnostic.

Records only counts and status. CQL search results are not activity histories;
absence of matches cannot establish inactivity or complete coverage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BASE = "https://lf-toip.atlassian.net/wiki/rest/api/search"
MAX_BYTES = 1024 * 1024


def search_month(month: str, *, opener=urlopen, limit: int = 25, max_batches: int = 3) -> dict:
    try:
        start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("month must be YYYY-MM") from exc
    if not 1 <= max_batches <= 5:
        raise ValueError("max_batches must be 1..5")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be 1..50")
    end = datetime(start.year + (start.month == 12), start.month % 12 + 1, 1, tzinfo=timezone.utc)
    cql = f'type = page AND lastmodified >= "{start:%Y-%m-%d}" AND lastmodified < "{end:%Y-%m-%d}"'
    url = BASE + "?" + urlencode({"cql": cql, "limit": limit})
    result = {"source": "confluence_cql_public_search", "month": month, "query_semantics": "page lastmodified; not event history", "coverage": "not_checked"}
    seen = set()
    count = 0
    batches = 0
    total = None
    space_keys = set()
    missing_space = 0
    while url and batches < max_batches:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "lf-toip.atlassian.net" or parsed.path not in ("/wiki/rest/api/search", "/wiki/rest/api/content/search", "/rest/api/search"):
            return {**result, "coverage": "unavailable", "reason": "unsafe_pagination_url", "rejected_path": parsed.path, "batches_fetched": batches}
        if url in seen:
            return {**result, "coverage": "unavailable", "reason": "pagination_cycle", "batches_fetched": batches}
        seen.add(url)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "TEM-Public-Historical-Search/1.0"})
        try:
            with opener(request, timeout=15) as response:
                payload = response.read(MAX_BYTES + 1)
                if len(payload) > MAX_BYTES:
                    return {**result, "coverage": "unavailable", "reason": "response_limit_exceeded", "batches_fetched": batches}
                data = json.loads(payload)
        except HTTPError as exc:
            return {**result, "coverage": "unavailable", "http_status": exc.code, "batches_fetched": batches}
        except (URLError, TimeoutError, OSError, ValueError, UnicodeError) as exc:
            return {**result, "coverage": "unavailable", "reason": type(exc).__name__, "batches_fetched": batches}
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            return {**result, "coverage": "unavailable", "reason": "unexpected_schema", "batches_fetched": batches}
        batches += 1
        count += min(len(data["results"]), limit)
        # Collect only aggregate public space identifiers, not page data.
        for item in data["results"]:
            content = item.get("content") if isinstance(item, dict) else None
            space = content.get("space") if isinstance(content, dict) else None
            key = space.get("key") if isinstance(space, dict) else None
            if isinstance(key, str) and 0 < len(key) <= 100:
                space_keys.add(key)
            else:
                missing_space += 1
        if isinstance(data.get("totalSize"), int):
            total = data["totalSize"]
        links = data.get("_links") if isinstance(data.get("_links"), dict) else {}
        next_link = links.get("next")
        if isinstance(next_link, str) and next_link:
            candidate = urljoin("https://lf-toip.atlassian.net", next_link)
            candidate_parts = urlsplit(candidate)
            # Confluence may return /wiki/rest/api/content/search as its
            # canonical next-page URL for /wiki/rest/api/search.
            if (candidate_parts.scheme != "https"
                    or candidate_parts.netloc != "lf-toip.atlassian.net"
                    or candidate_parts.path not in ("/wiki/rest/api/search", "/wiki/rest/api/content/search", "/rest/api/search")):
                return {**result, "coverage": "unavailable", "reason": "unsafe_pagination_url", "rejected_path": candidate_parts.path, "batches_fetched": batches}
            # Atlassian emits a context-relative /rest/api/search link,
            # but the public Cloud site serves this API beneath /wiki.
            if candidate_parts.path == "/rest/api/search":
                candidate = urlunsplit((candidate_parts.scheme, candidate_parts.netloc,
                                      "/wiki/rest/api/search", candidate_parts.query, ""))
            url = candidate
        else:
            url = None
    result["observed_space_keys"] = sorted(space_keys)
    result["missing_space_count"] = missing_space
    result["scope_verified"] = False
    result["sample_count"] = count
    result["total_size"] = total
    result["batches_fetched"] = batches
    result["next_page_present"] = bool(url)
    result["coverage"] = "sample_only"
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-batches", type=int, default=3)
    args = parser.parse_args()
    report = search_month(args.month, max_batches=args.max_batches)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
