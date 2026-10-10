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
import re

BASE = "https://lf-toip.atlassian.net/wiki/rest/api/search"
MAX_BYTES = 1024 * 1024
MAX_LOOKUPS = 50
PAGE_ID = re.compile(r"[0-9]{1,20}$")


def resolve_space(page_id: str, *, opener=urlopen) -> tuple[str | None, str]:
    """Fetch public v2 page metadata only; never fetch bodies or follow redirects."""
    if not PAGE_ID.fullmatch(page_id):
        return None, "invalid_id"
    url = f"https://lf-toip.atlassian.net/wiki/api/v2/pages/{page_id}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "TEM-Public-Space-Resolver/1.0"})
    try:
        with opener(request, timeout=15) as response:
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                return None, "response_limit"
            data = json.loads(payload)
    except HTTPError as exc:
        return None, "not_authorized" if exc.code in (401, 403) else "http_error"
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError):
        return None, "unavailable"
    if not isinstance(data, dict) or str(data.get("id")) != page_id:
        return None, "identity_mismatch"
    space_id = data.get("spaceId")
    if not isinstance(space_id, (str, int)) or isinstance(space_id, bool) or not str(space_id).isdigit():
        return None, "missing_space_id"
    return str(space_id), "resolved"


def search_month(month: str, *, opener=urlopen, limit: int = 25, max_batches: int = 3, resolve_missing: bool = False) -> dict:
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
    observed_shapes = set()
    space_sources = set()
    resolved_space_ids = set()
    lookup_status = {}
    lookup_cache = {}
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
            if not isinstance(item, dict):
                missing_space += 1
                continue
            # Field-name diagnostics only: never store titles, IDs or bodies.
            observed_shapes.add(",".join(sorted(
                k for k in item if k in {"content", "space", "spaceId", "entity", "resultGlobalContainer"}
            )) or "none")
            content = item.get("content") if isinstance(item.get("content"), dict) else {}
            candidates = [
                ("content.space", content.get("space")),
                ("result.space", item.get("space")),
            ]
            key = None
            for origin, candidate in candidates:
                if isinstance(candidate, dict) and isinstance(candidate.get("key"), str):
                    key = candidate["key"]
                    space_sources.add(origin)
                    break
            if isinstance(key, str) and 0 < len(key) <= 100:
                space_keys.add(key)
            else:
                if resolve_missing:
                    identifier = content.get("id")
                    if not isinstance(identifier, (str, int)) or isinstance(identifier, bool):
                        status = "missing_page_id"
                    else:
                        identifier = str(identifier)
                        if identifier not in lookup_cache and len(lookup_cache) < MAX_LOOKUPS:
                            lookup_cache[identifier] = resolve_space(identifier, opener=opener)
                        space_id, status = lookup_cache.get(identifier, (None, "lookup_limit"))
                        if space_id is not None:
                            resolved_space_ids.add(space_id)
                    lookup_status[status] = lookup_status.get(status, 0) + 1
                    if status == "resolved":
                        continue
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
    result["observed_field_shapes"] = sorted(observed_shapes)
    result["space_key_origins"] = sorted(space_sources)
    result["observed_space_keys"] = sorted(space_keys)
    result["resolved_space_ids"] = sorted(resolved_space_ids)
    result["metadata_lookup_status"] = dict(sorted(lookup_status.items()))
    result["metadata_lookup_attempted"] = len(lookup_cache)
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
    parser.add_argument("--resolve-missing", action="store_true", help="Bounded public v2 page metadata lookups for missing space keys")
    args = parser.parse_args()
    report = search_month(args.month, max_batches=args.max_batches, resolve_missing=args.resolve_missing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
