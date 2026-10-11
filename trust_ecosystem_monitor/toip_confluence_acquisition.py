"""Bounded read-only Confluence metadata acquisition; never admits content by itself.

Caller must supply a dated approved scope/reuse decision before invoking.
Only allowlisted metadata is retained. No page bodies, titles or credentials.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
import json
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HOST = "lf-toip.atlassian.net"
BASE = "https://" + HOST
MAX_PAGES = 10
PAGE_SIZE = 50
MAX_BYTES = 1024 * 1024


class AcquisitionError(RuntimeError):
    pass


def acquire_metadata(month: str, *, approved_space_ids: set[str],
                     scope_approved: bool = False, reuse_approved: bool = False,
                     fetch=None, max_pages: int = MAX_PAGES,
                     retrieved_at: str | None = None) -> dict:
    """Return metadata observations and explicit incomplete-coverage diagnostics.

    Search is scoped by approved space key HOME, then each hit's spaceId is
    checked against approved numeric space IDs. The result is not a license to
    republish records, and it never marks historical completeness on its own.
    """
    if not isinstance(month, str) or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("month must be YYYY-MM")
    if not scope_approved or not reuse_approved or not approved_space_ids:
        raise PermissionError("dated scope and metadata reuse approvals required")
    if not all(str(v).isdigit() for v in approved_space_ids):
        raise ValueError("approved space IDs must be numeric")
    if not 1 <= max_pages <= MAX_PAGES:
        raise ValueError("invalid pagination budget")
    if retrieved_at is None:
        retrieved_at = datetime.now(timezone.utc).isoformat()
    else:
        try:
            parsed_at = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError("retrieved_at must be timezone-aware ISO 8601") from exc
        if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware ISO 8601")
    if fetch is None:
        fetch = _fetch_json
    year, mm = map(int, month.split("-"))
    if not 1 <= mm <= 12:
        raise ValueError("invalid month")
    next_month = f"{year+1}-01" if mm == 12 else f"{year}-{mm+1:02d}"
    cql = f'space = HOME AND lastmodified >= "{month}-01" AND lastmodified < "{next_month}-01"'
    path = "/wiki/rest/api/content/search?" + urlencode({"cql": cql, "limit": PAGE_SIZE, "start": 0})
    expected_query = {"cql": [cql], "limit": [str(PAGE_SIZE)]}
    seen_pages = set()
    previous_start = -1
    seen_ids = set()
    records = []
    diagnostics = []
    search_pages_fetched = 0
    metadata_lookups_attempted = 0
    terminal_page_seen = False
    for page_no in range(max_pages):
        if path in seen_pages:
            diagnostics.append("pagination_cycle")
            break
        seen_pages.add(path)
        current_start = int(parse_qs(urlsplit(path).query)["start"][0])
        if current_start <= previous_start:
            diagnostics.append("non_monotonic_pagination")
            break
        previous_start = current_start
        try:
            data = fetch(path)
        except (AcquisitionError, ValueError, KeyError, TypeError):
            diagnostics.append("retrieval_error")
            break
        search_pages_fetched += 1
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            diagnostics.append("malformed_response")
            break
        for hit in data["results"]:
            if not isinstance(hit, dict) or not str(hit.get("id", "")).isdigit():
                diagnostics.append("malformed_hit")
                continue
            ident = str(hit["id"])
            if ident in seen_ids:
                diagnostics.append("duplicate_hit")
                continue
            seen_ids.add(ident)
            metadata_lookups_attempted += 1
            try:
                page = fetch("/wiki/api/v2/pages/" + ident)
            except (AcquisitionError, ValueError, KeyError, TypeError):
                diagnostics.append("metadata_lookup_error")
                continue
            if not isinstance(page, dict) or str(page.get("id")) != ident:
                diagnostics.append("identity_mismatch")
                continue
            if str(page.get("spaceId")) not in approved_space_ids:
                diagnostics.append("out_of_scope")
                continue
            version = page.get("version")
            if (not isinstance(version, dict) or type(version.get("number")) is not int
                    or version["number"] < 1):
                diagnostics.append("missing_version_provenance")
                continue
            records.append({
                "source": "confluence", "source_id": ident,
                "space_id": str(page["spaceId"]),
                "version": version["number"],
                "url": BASE + "/wiki/spaces/HOME/pages/" + ident,
                "kind": "page_update",
                "classification": "metadata_only",
            })
        nxt = data.get("_links", {}).get("next") if isinstance(data.get("_links"), dict) else None
        if not nxt:
            if data.get("size") == PAGE_SIZE:
                diagnostics.append("possible_truncation")
            terminal_page_seen = True
            break
        if nxt in seen_pages:
            diagnostics.append("pagination_cycle")
            break
        parsed = urlsplit(nxt)
        try:
            params = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
            valid = (not parsed.scheme and not parsed.netloc and not parsed.fragment
                     and parsed.path == "/wiki/rest/api/content/search"
                     and set(params) == {"cql", "limit", "start"}
                     and all(len(values) == 1 for values in params.values())
                     and params["cql"] == expected_query["cql"]
                     and params["limit"] == expected_query["limit"]
                     and params["start"][0].isdigit()
                     and int(params["start"][0]) > current_start)
        except (ValueError, KeyError):
            valid = False
        if not valid:
            diagnostics.append("unsafe_pagination")
            break
        path = nxt
    else:
        diagnostics.append("page_budget_exhausted")
    return {
        "schema_version": "1", "period": month,
        "source": "confluence", "space_ids": sorted(approved_space_ids),
        "records": records, "diagnostics": sorted(set(diagnostics)),
        "retrieved_at": retrieved_at,
        "search_pages_fetched": search_pages_fetched,
        "metadata_lookups_attempted": metadata_lookups_attempted,
        "search_terminated_normally": terminal_page_seen,
        "coverage": "partial" if search_pages_fetched else "unavailable",
        "scope_verified": False, "scope_caller_approved": True,
        "historical_completeness_verified": False,
        "publication_admitted": False,
    }


def _fetch_json(path: str) -> dict:
    if not path.startswith(("/wiki/rest/api/content/search?", "/wiki/api/v2/pages/")):
        raise AcquisitionError("path outside allowlist")
    url = BASE + path
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=12) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise AcquisitionError("response budget exceeded")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise AcquisitionError("Confluence metadata unavailable") from exc
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AcquisitionError("invalid JSON") from exc
