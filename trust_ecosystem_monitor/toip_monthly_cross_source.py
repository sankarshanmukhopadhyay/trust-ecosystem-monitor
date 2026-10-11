"""Experimental cross-source reference propositions, never assured admission."""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from .toip_monthly_knowledge import build_developments

COMMON = frozenset(("the and with from update changes support issue issues github toip group "
                    "meeting specification working discussion review new documentation about "
                    "implementation proposal report").split())


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z0-9]{3,}", text.lower()) if w not in COMMON}


def correlate(github: dict, content: dict, *, max_candidates: int = 12) -> list[dict]:
    """Return explicit exact artifact links and low-confidence lexical candidates.

    A reference to the artifact is verified *as a link*, never as evidence
    of substantive equivalence, temporal causation or a governance decision.
    """
    if github.get("period") != content.get("month"):
        raise ValueError("cross-source reporting period mismatch")
    if not 0 <= max_candidates <= 50:
        raise ValueError("candidate limit invalid")
    developments = build_developments(github.get("evidence", []))
    by_url = {row["url"].split("#", 1)[0].split("?", 1)[0]: row for row in developments}
    results, seen = [], set()
    for page in content.get("pages", []):
        identifier = str(page.get("id", ""))
        if not identifier.isdigit():
            raise ValueError("Confluence page ID required")
        source_url = "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/" + identifier
        for target in page.get("github_references", []):
            if target not in by_url:
                continue
            key = (identifier, target)
            if key in seen:
                continue
            seen.add(key)
            results.append({"state": "explicit_reference", "page": source_url,
                            "page_version": page.get("version"), "github": target,
                            "subject": by_url[target]["title"],
                            "basis": "Canonical GitHub artifact URL appears in retrieved public Confluence page content.",
                            "limitations": "A hyperlink is not a determination of agreement, adoption, causality, or meeting date."})
        # Candidate matching is intentionally weak, transparent and non-authoritative.
        page_terms = _terms(str(page.get("title", "")) + " " +
                            " ".join(str(x.get("section", "")) + " " + str(x.get("abstract", ""))
                                     for x in page.get("section_abstracts", [])))
        for target, dev in by_url.items():
            if (identifier, target) in seen:
                continue
            overlap = sorted(page_terms & _terms(dev["title"]))
            if len(overlap) < 3:
                continue
            key = (identifier, target)
            seen.add(key)
            results.append({"state": "candidate_topic_overlap", "page": source_url,
                            "page_version": page.get("version"), "github": target,
                            "subject": dev["title"], "basis": "Overlapping terms: " + ", ".join(overlap[:6]),
                            "limitations": "Lexical proximity only; no established subject identity or relationship."})
    explicit = [r for r in results if r["state"] == "explicit_reference"]
    candidates = [r for r in results if r["state"] != "explicit_reference"][:max_candidates]
    return sorted(explicit, key=lambda r: (r["page"], r["github"])) + sorted(
        candidates, key=lambda r: (r["page"], r["github"]))
