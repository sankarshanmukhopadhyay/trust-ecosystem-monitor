"""Source-oriented Confluence discussion extraction for TEM.

This is *extractive evidence*, not an LLM-authored decision summary.
Select substantive blocks across the whole bounded page, not the first six.
Associate references with their containing passage, qualify interpretation and
avoid reprinting complete meeting minutes.
"""
from __future__ import annotations
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlsplit
from collections import Counter
import hashlib
import re

BOILER = re.compile(r"antitrust|intellectual property|\bipr\b|code of conduct|"
                    r"zoom|calendar invite|copyright|license|membership|"
                    r"roll call|attendance|attendees|apologies|meeting logistics|"
                    r"new members|introductions|housekeeping", re.I)
MATTERS = re.compile(r"\b(proposal|propose|proposed|question|discuss|concern|"
                     r"issue|risk|decision|decided|agreed|resolved|action|"
                     r"follow.up|assigned|next steps?|open question|"
                     r"architecture|credential|delegation|protocol|schema|"
                     r"interoperability|implementation|test|specification|"
                     r"authorization|verification|governance|assurance)\b", re.I)
DECISION = re.compile(r"\b(decided|agreed|approved|resolved|consensus)\b", re.I)
QUESTION = re.compile(r"\?|\b(question|whether|clarif(?:y|ication)|unresolved)\b", re.I)
PROPOSAL = re.compile(r"\b(propos(?:e|al|ed)|suggest|option|alternative)\b", re.I)
ACTION = re.compile(r"\b(action|follow.up|next step|assigned|todo)\b", re.I)
RELEVANT = {"github.com", "lf-toip.atlassian.net", "trustoverip.org",
            "w3.org", "www.w3.org", "identity.foundation", "ietf.org", "www.ietf.org", "datatracker.ietf.org"}

def canonical(url):
    if not isinstance(url, str):
        return None
    if url.startswith("/wiki/"):
        url = "https://lf-toip.atlassian.net" + url
    parsed = urlsplit(unescape(url))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    if parsed.hostname not in RELEVANT and not parsed.hostname.endswith(".github.io"):
        return None
    if len(url) > 600 or any(ch in url for ch in ('"', "'", "<", ">", "\n", "\r")):
        return None
    return unescape(url).split("#", 1)[0]

class DiscussionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = "General"
        self.active = None
        self.depth = 0
        self.buf = []
        self.links = []
        self.blocks = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ("h1", "h2", "h3", "p", "li", "td") and self.active is None:
            self.active = tag
            self.depth = 1
            self.buf, self.links = [], []
        elif self.active and tag == self.active:
            self.depth += 1
        if tag == "a" and self.active:
            url = canonical(dict(attrs).get("href"))
            if url:
                self.links.append(url)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
            return
        if self.skip or tag != self.active:
            return
        self.depth -= 1
        if self.depth:
            return
        text = " ".join("".join(self.buf).split())[:5000]
        if self.active in ("h1", "h2", "h3"):
            self.heading = text[:120] or "General"
        elif text:
            plain = re.findall(r"https://[^\s<>]+", text)
            references = [canonical(u.rstrip(".,;)")) for u in plain]
            self.blocks.append((self.heading, text, list(dict.fromkeys(
                u for u in self.links + references if u))))
        self.active = None
        self.buf = []
        self.links = []

    def handle_data(self, data):
        if self.active and not self.skip:
            self.buf.append(data)

def _score(heading, text, links):
    if len(text) < 35 or BOILER.search(heading) or BOILER.search(text[:150]):
        return 0
    hits = len(MATTERS.findall(text))
    if not hits:
        return 0
    score = min(hits, 6) * 2 + (2 if links else 0)
    score += 3 if (QUESTION.search(text) or PROPOSAL.search(text)) else 0
    score += 2 if (DECISION.search(text) or ACTION.search(text)) else 0
    return score

def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if len(x.strip()) > 20]

def _signal(text):
    signals = []
    for name, rx in (("question_language", QUESTION), ("proposal_language", PROPOSAL),
                     ("decision_language", DECISION), ("action_language", ACTION)):
        if rx.search(text):
            signals.append(name)
    return signals

def extract_discussions(body, *, max_blocks=8):
    if not isinstance(body, str) or len(body) > 250000 or not 1 <= max_blocks <= 12:
        raise ValueError("invalid bounded Confluence content")
    parser = DiscussionParser()
    parser.feed(body)
    ranked = []
    for position, (heading, text, links) in enumerate(parser.blocks):
        score = _score(heading, text, links)
        if score:
            ranked.append((score, position, heading, text, links))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    selected = []
    for score, position, heading, text, links in ranked[:max_blocks]:
        sentences = _sentences(text)
        # Identify the strongest complete source sentence, rather than
        # hallucinate a summary of a possibly longer discussion.
        best = max(sentences or [text], key=lambda x: (_score(heading, x, links), len(x)))
        excerpt = best[:200].rstrip()
        if len(best) > 200:
            excerpt = excerpt.rsplit(" ", 1)[0] + "…"
        language = _signal(text)
        kind = ("Question / clarification" if "question_language" in language else
                "Proposal / alternative" if "proposal_language" in language else
                "Action / follow-up wording" if "action_language" in language else
                "Decision-related wording (unverified)" if "decision_language" in language else
                "Technical discussion")
        selected.append({
            "section": heading, "abstract": kind + ": " + excerpt,
            "brief_source_excerpt": excerpt[:160],
            "language_signals": language,
            "basis_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "evidence_basis": "selected_substantive_source_passage",
            "rank": score, "source_block_number": position + 1,
            "references": links[:8],
        })
    # Preserve source-document order after relevance selection.
    selected.sort(key=lambda x: x["source_block_number"])
    github_refs = sorted({url.split("?", 1)[0] for item in parser.blocks
                         for url in item[2]
                         if re.fullmatch(r"https://github.com/[^/]+/[^/]+/(?:issues|pull)/\d+", url.split("?", 1)[0])})
    return {
        "sections": selected, "github_references": github_refs,
        "text_sections_inspected": len(parser.blocks),
        "summary_method": "evidence_sentence_selection_scored_v3",
        "disclosure": "Extractive, selected passages; no approval or outcome inferred.",
    }
