"""Re-inspect bounded previously observed public HOME pages.

Re-checks do not retroactively assign activity to the current month.
"""
from __future__ import annotations
from datetime import datetime, timezone
from .toip_confluence_content_signals import _get, HOST, HOME, TextSections
from .toip_content_interpretation import extract
from .toip_discussion_blocks import extract_discussions
import re

MAX_TRACKED = 80

def inspect(ids, *, opener=None):
    if not isinstance(ids, list) or len(ids) > MAX_TRACKED:
        raise ValueError("tracked source bound exceeded")
    pages, errors = [], []
    for identifier in dict.fromkeys(str(x) for x in ids):
        if not identifier.isdigit() or len(identifier) > 20:
            raise ValueError("invalid tracked source ID")
        try:
            url = "https://" + HOST + "/wiki/api/v2/pages/" + identifier + "?body-format=storage"
            payload = _get(url, opener=opener) if opener else _get(url)
            if str(payload.get("id")) != identifier or str(payload.get("spaceId")) != HOME:
                raise ValueError("tracked page not verified in HOME")
            body = ((payload.get("body") or {}).get("storage") or {}).get("value", "")
            if not isinstance(body, str) or len(body) > 250000:
                raise ValueError("tracked page content invalid")
            text = TextSections()
            text.feed(body)
            interpreted = extract(body)
            discussions = extract_discussions(body)
            title = " ".join(str(payload.get("title", "")).split())[:160]
            kind = ("administrative" if re.search(r"template|calendar|standing agenda|meeting logistics", title, re.I)
                    else "substantive" if discussions["sections"] else "content_poor")
            pages.append({
                "id": identifier, "title": title, "page_kind": kind,
                "url": "https://" + HOST + "/wiki/spaces/HOME/pages/" + identifier,
                "version": (payload.get("version") or {}).get("number"),
                "version_created_at": (payload.get("version") or {}).get("createdAt"),
                "topic_headings": text.headings[:8],
                "section_abstracts": interpreted["sections"],
                "discussion_blocks": discussions["sections"],
                "github_references": interpreted["github_references"],
            })
        except (OSError, TimeoutError, ValueError, UnicodeError) as exc:
            errors.append({"id": identifier, "reason": type(exc).__name__})
    return {"pages": pages, "unavailable": errors,
            "checked_at": datetime.now(timezone.utc).isoformat()}
