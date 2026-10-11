"""Bounded, inspectable content interpretation; source text is never published.

Generates original topic descriptions and lexical signal categories, not
purported meeting decisions, recommendations or LLM-generated assertions.
"""
from __future__ import annotations
from collections import Counter
from html.parser import HTMLParser
import hashlib
import re
from urllib.parse import urlsplit

STOP = frozenset(("about after again against also been being between could does each from have into "
                  "more most only other over same should some such than that their there these this "
                  "those through under using were what when where which while with would your "
                  "meeting notes agenda minutes action discussion update group working toip").split())
URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:issues|pull)/[0-9]+(?:[/?#][^\s<\"']*)?")
CUES = {
    "question_language": re.compile(r"\?|\b(question|clarif(?:y|ication)|unclear|whether)\b", re.I),
    "proposal_language": re.compile(r"\b(propos(?:e|al|ed)|suggest(?:ion|ed)?|consider)\b", re.I),
    "action_language": re.compile(r"\b(action item|follow[ -]?up|todo|next steps?|assigned)\b", re.I),
    "decision_language": re.compile(r"\b(decid(?:ed|e)|agreed|approved|resolution|consensus)\b", re.I),
}


class Sections(HTMLParser):
    """Read p/li and headings; ignore script/styles and user info."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.heading = "General"
        self._tag = None
        self._bits = []
        self._skip = 0
        self._links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if self._skip:
            return
        if tag in ("h1", "h2", "h3", "p", "li") and self._tag is None:
            self._tag = tag
            self._bits = []
        if tag == "a":
            href = dict(attrs).get("href")
            if isinstance(href, str):
                self._links.append(href)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
            return
        if tag != self._tag or self._skip:
            return
        text = " ".join("".join(self._bits).split())
        if self._tag in ("h1", "h2", "h3"):
            self.heading = text[:120] or "General"
        elif text and len(text) >= 20:
            self.sections.append((self.heading, text[:3500]))
        self._tag = None
        self._bits = []

    def handle_data(self, data):
        if self._tag and not self._skip:
            self._bits.append(data)


def _terms(value: str, limit: int = 6) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9-]{3,}", value.lower())
    return [word for word, _ in Counter(w for w in words if w not in STOP).most_common(limit)]


def _canonical_github(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.username or parsed.password:
        return None
    m = re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:issues|pull)/[0-9]+", parsed.path.rstrip("/"))
    return "https://github.com" + parsed.path.rstrip("/") if m else None


def extract(body: str, *, max_sections: int = 6) -> dict:
    if not isinstance(body, str) or len(body) > 250_000 or not 1 <= max_sections <= 10:
        raise ValueError("unbounded or invalid Confluence body")
    parser = Sections()
    parser.feed(body)
    summaries = []
    for heading, passage in parser.sections:
        if len(summaries) >= max_sections:
            break
        terms = _terms(passage)
        if not terms:
            continue
        categories = sorted(cue for cue, regex in CUES.items() if regex.search(passage))
        # Interpretive language is deliberately bounded: no assertion that an
        # action was assigned, an answer was resolved or a decision authorized.
        summaries.append({
            "section": heading,
            "abstract": "Text under this section addresses " + ", ".join(terms[:5]) + ".",
            "language_signals": categories,
            "basis_sha256": hashlib.sha256(passage.encode("utf-8")).hexdigest(),
            "evidence_basis": "current_public_page_section_text",
        })
    links = set()
    for link in parser._links + URL.findall(body):
        url = _canonical_github(link)
        if url:
            links.add(url)
    return {"sections": summaries, "github_references": sorted(links),
            "text_sections_inspected": len(parser.sections),
            "summary_method": "deterministic_term_and_cue_extraction_v1"}
