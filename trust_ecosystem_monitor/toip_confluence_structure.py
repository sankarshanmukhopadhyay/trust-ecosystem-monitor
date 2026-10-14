"""Diagnostic structural parsing for bounded ToIP Confluence HTML.

This module extracts agenda/table/macro-like structure for review. It does not
admit Confluence content as production evidence and does not infer meetings,
decisions, approvals, adoption or ToIP authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit
import hashlib
import re

RELEVANT_HOSTS = {
    "github.com",
    "lf-toip.atlassian.net",
    "trustoverip.org",
    "w3.org",
    "www.w3.org",
    "identity.foundation",
    "ietf.org",
    "www.ietf.org",
    "datatracker.ietf.org",
}

INTERPRETATION_LIMITS = [
    "diagnostic_structure_only",
    "no_meeting_held_inferred",
    "no_decision_inferred",
    "no_adoption_or_approval_inferred",
    "no_source_publication_rights_inferred",
    "no_toip_authority_inferred",
]

DECISION_WORDS = re.compile(r"\b(decision|decided|approved|resolved|consensus|adopted|agreed)\b", re.I)
MEETING_WORDS = re.compile(r"\b(meeting|agenda|minutes|attendees|recording)\b", re.I)


def canonical_url(url: str | None) -> str | None:
    if not isinstance(url, str) or not url:
        return None
    if url.startswith("/wiki/"):
        url = "https://lf-toip.atlassian.net" + url
    parsed = urlsplit(unescape(url))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    if parsed.hostname not in RELEVANT_HOSTS and not parsed.hostname.endswith(".github.io"):
        return None
    cleaned = unescape(url).split("#", 1)[0]
    if len(cleaned) > 600 or any(ch in cleaned for ch in ('\"', "'", "<", ">", "\n", "\r")):
        return None
    return cleaned


@dataclass
class StructuralBlock:
    block_id: str
    block_kind: str
    heading_path: list[str]
    text_basis_sha256: str
    links: list[str] = field(default_factory=list)
    github_references: list[str] = field(default_factory=list)
    external_references: list[str] = field(default_factory=list)
    language_signals: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    admission_state: str = "diagnostic_only"
    interpretation_limits: list[str] = field(default_factory=lambda: list(INTERPRETATION_LIMITS))

    def to_dict(self) -> dict:
        return asdict(self)


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_stack: list[tuple[int, str]] = []
        self.active: dict | None = None
        self.skip = 0
        self.blocks: list[dict] = []
        self.table_depth = 0
        self.row_open = False
        self.row_cells: list[str] = []
        self.row_links: list[str] = []
        self.cell_buffer: list[str] = []
        self.macro_depth = 0

    def _path(self) -> list[str]:
        return [h for _, h in self.heading_stack] or ["General"]

    def _start_active(self, kind: str) -> None:
        if self.active is None:
            self.active = {"kind": kind, "text": [], "links": [], "heading_path": self._path()}

    def _finish_active(self) -> None:
        if not self.active:
            return
        text = " ".join("".join(self.active["text"]).split())
        if text:
            self.blocks.append({
                "kind": self.active["kind"],
                "heading_path": list(self.active["heading_path"]),
                "text": text,
                "links": list(dict.fromkeys(self.active["links"])),
            })
        self.active = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
            return
        if self.skip:
            return
        cls = " ".join(v for k, v in attrs if k == "class" and v)
        data_macro = attr.get("data-macro-name") or attr.get("ac:name")
        if data_macro or "expand" in cls or "panel" in cls or "macro" in cls:
            self.macro_depth += 1
            self._start_active("macro_like_block")
        if tag == "table":
            self.table_depth += 1
        elif tag == "tr" and self.table_depth:
            self.row_open = True
            self.row_cells = []
            self.row_links = []
        elif tag in ("td", "th") and self.row_open:
            self.cell_buffer = []
        elif tag in ("p", "li") and self.active is None and not self.table_depth:
            self._start_active("paragraph")
        elif tag in ("h1", "h2", "h3", "h4") and self.active is None:
            self._start_active("heading")
            self.active["level"] = int(tag[1])
        if tag == "a":
            url = canonical_url(attr.get("href"))
            if url:
                if self.active is not None:
                    self.active["links"].append(url)
                if self.row_open:
                    self.row_links.append(url)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag in ("td", "th") and self.row_open:
            cell = " ".join("".join(self.cell_buffer).split())
            if cell:
                self.row_cells.append(cell)
            self.cell_buffer = []
        elif tag == "tr" and self.row_open:
            text = " | ".join(self.row_cells)
            if text:
                self.blocks.append({
                    "kind": "table_row",
                    "heading_path": self._path(),
                    "text": text,
                    "links": list(dict.fromkeys(self.row_links)),
                })
            self.row_open = False
            self.row_cells = []
            self.row_links = []
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
        elif self.active and self.active.get("kind") == "heading" and tag in ("h1", "h2", "h3", "h4"):
            text = " ".join("".join(self.active["text"]).split())[:160]
            level = int(self.active.get("level", 2))
            if text:
                self.heading_stack = [(lvl, h) for lvl, h in self.heading_stack if lvl < level]
                self.heading_stack.append((level, text))
            self._finish_active()
        elif self.active and self.active.get("kind") == "paragraph" and tag in ("p", "li"):
            self._finish_active()
        if self.macro_depth and self.active and self.active.get("kind") == "macro_like_block" and tag in ("div", "section", "ac:structured-macro"):
            self.macro_depth -= 1
            if self.macro_depth == 0:
                self._finish_active()

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if self.row_open and self.table_depth:
            self.cell_buffer.append(data)
        if self.active is not None:
            self.active["text"].append(data)


def _signals(text: str) -> tuple[list[str], list[str]]:
    language = []
    unsupported = []
    if DECISION_WORDS.search(text):
        language.append("decision_like_language")
        unsupported.append("decision_or_adoption_not_established")
    if MEETING_WORDS.search(text):
        language.append("meeting_like_language")
        unsupported.append("meeting_occurrence_not_established")
    return language, list(dict.fromkeys(unsupported))


def _github_refs(links: list[str]) -> list[str]:
    return sorted({url.split("?", 1)[0] for url in links
                   if re.fullmatch(r"https://github.com/[^/]+/[^/]+/(?:issues|pull)/\d+", url.split("?", 1)[0])})


def extract_structure(body: str, *, page_id: str, source_url: str, page_version=None, max_blocks: int = 24) -> dict:
    if not isinstance(body, str) or len(body) > 250000 or not body.strip():
        raise ValueError("invalid bounded Confluence content")
    if not str(page_id).isdigit():
        raise ValueError("invalid page id")
    canonical_source = canonical_url(source_url)
    if not canonical_source:
        raise ValueError("invalid source url")
    parser = StructureParser()
    parser.feed(body)
    blocks: list[StructuralBlock] = []
    for index, item in enumerate(parser.blocks[:max_blocks], start=1):
        text = item["text"]
        links = item.get("links", [])
        github_refs = _github_refs(links)
        external_refs = [u for u in links if u not in github_refs]
        language, unsupported = _signals(text)
        blocks.append(StructuralBlock(
            block_id=f"{page_id}:{index}",
            block_kind=item["kind"],
            heading_path=item.get("heading_path") or ["General"],
            text_basis_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            links=links,
            github_references=github_refs,
            external_references=external_refs,
            language_signals=language,
            unsupported_claims=unsupported,
        ))
    return {
        "page_id": str(page_id),
        "source_url": canonical_source,
        "page_version": page_version,
        "admission_state": "diagnostic_only",
        "interpretation_limits": list(INTERPRETATION_LIMITS),
        "blocks": [b.to_dict() for b in blocks],
        "summary_method": "diagnostic_confluence_structure_v1",
        "disclosure": "Structural extraction only; no meeting, decision, adoption, approval, authority or publication-rights claim is inferred.",
    }
