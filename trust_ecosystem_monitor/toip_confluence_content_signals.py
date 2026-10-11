"""Bounded public Confluence page content signals for experimental summaries.

No bodies, user identities, or original content are persisted. Only limited,
source-linked descriptive signals are returned; never claim governance decisions.
"""
from __future__ import annotations
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlencode, urlsplit, urljoin
from urllib.request import Request, urlopen
from .confluence_search import BASE as SEARCH_URL
from .toip_content_interpretation import extract
from .toip_discussion_blocks import extract_discussions

HOST = "lf-toip.atlassian.net"
HOME = "22970380"
MAX_BYTES = 1_000_000
MAX_ITEMS = 40


class TextSections(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading_depth = 0
        self.heading = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3"):
            self.heading_depth += 1
            self.heading = []

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3") and self.heading_depth:
            value = " ".join(" ".join(self.heading).split())
            if value and len(value) <= 120 and value not in self.headings:
                self.headings.append(value)
            self.heading_depth -= 1

    def handle_data(self, data):
        if self.heading_depth:
            self.heading.append(data)


def _get(url: str, *, opener=urlopen) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != HOST or not (
        parsed.path in ("/wiki/rest/api/search", "/wiki/rest/api/content/search")
        or re.fullmatch(r"/wiki/api/v2/pages/[0-9]{1,20}", parsed.path)
    ):
        raise ValueError("unsafe Confluence endpoint")
    request = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "TEM-Experimental-Content-Signals/1.0"})
    with opener(request, timeout=15) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Confluence response exceeds bound")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("unexpected Confluence response")
    return payload


def _safe_title(title) -> str:
    if not isinstance(title, str):
        return "Untitled public page"
    return " ".join(title.split())[:160]


def collect(month: str, *, opener=urlopen, max_items: int = MAX_ITEMS) -> dict:
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
    if start.strftime("%Y-%m") != month or not 1 <= max_items <= MAX_ITEMS:
        raise ValueError("invalid monthly public content bounds")
    end = datetime(start.year + (start.month == 12), start.month % 12 + 1, 1, tzinfo=timezone.utc)
    cql = 'type = page AND lastmodified >= "' + start.strftime("%Y-%m-%d") + (
        '" AND lastmodified < "' + end.strftime("%Y-%m-%d") + '"')
    url = SEARCH_URL + "?" + urlencode({"cql": cql, "limit": max_items})
    result = {"month": month, "coverage": "sample_only", "content_use": "experimental_section_abstracts",
              "pages": [], "unavailable_count": 0, "next_page_present": False,
              "retrieved_at": datetime.now(timezone.utc).isoformat()}
    data = _get(url, opener=opener)
    if not isinstance(data.get("results"), list):
        raise ValueError("unexpected CQL search schema")
    result["reported_total"] = data.get("totalSize")
    links = data.get("_links") or {}
    result["next_page_present"] = bool(links.get("next"))
    ids = []
    for entry in data["results"][:max_items]:
        candidate = (entry.get("content") or {}).get("id") if isinstance(entry, dict) else None
        if isinstance(candidate, (str, int)) and str(candidate).isdigit():
            ids.append(str(candidate))
    for identifier in dict.fromkeys(ids):
        try:
            page = _get("https://" + HOST + "/wiki/api/v2/pages/" + identifier +
                        "?body-format=storage", opener=opener)
            if str(page.get("id")) != identifier or str(page.get("spaceId")) != HOME:
                result["unavailable_count"] += 1
                continue
            title = _safe_title(page.get("title"))
            storage = ((page.get("body") or {}).get("storage") or {})
            body = storage.get("value", "")
            if not isinstance(body, str) or len(body) > 250_000:
                body = ""
            parser = TextSections()
            parser.feed(body)
            interpreted = extract(body)
            discussions = extract_discussions(body)
            page_kind = ("administrative" if re.search(
                r"template|calendar|standing agenda|meeting logistics|home page|"
                r"index of meeting|instructions|code of conduct", title, re.I)
                else "substantive" if discussions["sections"] else "content_poor")
            result["pages"].append({
                "id": identifier, "title": title, "page_kind": page_kind,
                "url": "https://" + HOST + "/wiki/spaces/HOME/pages/" + identifier,
                "version": (page.get("version") or {}).get("number"),
                "version_created_at": (page.get("version") or {}).get("createdAt"),
                "topic_headings": parser.headings[:8],
                "section_abstracts": interpreted["sections"],
                "discussion_blocks": discussions["sections"],
                "github_references": interpreted["github_references"],
                "summary_method": interpreted["summary_method"],
                "text_sections_inspected": interpreted["text_sections_inspected"],
                "content_signal": "headings_only" if parser.headings else "no_extractable_headings",
            })
        except (OSError, ValueError, UnicodeError, TimeoutError, json.JSONDecodeError):
            result["unavailable_count"] += 1
    return result
