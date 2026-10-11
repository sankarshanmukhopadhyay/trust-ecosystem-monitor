"""Evidence-first monthly synthesis reusing TEM's weekly semantic change classifier.

The output is deterministic, bounded, and deliberately avoids inferred
governance decisions, maturity, or cross-source causation.
"""
from __future__ import annotations
from collections import defaultdict
from html import escape
import re
from urllib.parse import urlsplit

from .intelligence_backend import classify_semantic_change
from .monthly_overview import portfolio

GITHUB_HOST = "github.com"
STOP = {"the", "and", "for", "with", "from", "into", "this", "that", "update",
        "add", "fix", "docs", "feat", "spec", "issue", "review", "changes",
        "work", "implement", "support", "tests", "test", "toip"}


def _link(url: str, text: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != GITHUB_HOST or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("non-canonical GitHub evidence URL")
    return '<a href="' + escape(url, quote=True) + '">' + escape(text) + '</a>'


def _key(row: dict) -> tuple[str, str, str]:
    return row["repository"], row["kind"], row["url"]


def build_developments(evidence: list[dict]) -> list[dict]:
    """Group lifecycle events by source artifact; classify with weekly TEM rules.

    Same-artifact lifecycle is observed; same-topic grouping is not identity or
    proof of implementation. Each development points to its underlying artifact.
    """
    grouped = defaultdict(list)
    for item in evidence:
        if not isinstance(item, dict) or not all(item.get(k) for k in
                ("repository", "kind", "url", "occurred_at", "title", "event")):
            raise ValueError("incomplete monthly GitHub evidence")
        _link(item["url"], item["title"])
        grouped[_key(item)].append(item)
    developments = []
    for (repository, kind, url), rows in grouped.items():
        rows.sort(key=lambda x: (x["occurred_at"], x["event"]))
        states = set(row["event"] for row in rows)
        title = rows[-1]["title"].strip().replace("\n", " ")
        classification = classify_semantic_change({"title": title, "events": rows, "event_kinds": list(states)})
        if "merged" in states:
            change = "PR merge observed"
        elif "closed" in states:
            change = "Closure observed; resolution not independently verified"
        else:
            change = "Opening observed; subsequent status not determined"
        developments.append({
            "repository": repository, "portfolio": portfolio(repository),
            "kind": kind, "url": url, "title": title, "events": sorted(states),
            "change": change, "semantic": classification["type"],
            "semantic_basis": classification.get("matched_terms", []),
            "last_observed_at": rows[-1]["occurred_at"], "event_count": len(rows),
        })
    priority = {"PR merge observed": 0, "Closure observed; resolution not independently verified": 1,
                "Opening observed; subsequent status not determined": 2}
    return sorted(developments, key=lambda x: (priority[x["change"]], x["portfolio"],
                                               x["repository"], x["title"].lower(), x["url"]))


def topic_groups(developments: list[dict]) -> list[dict]:
    """Explainable thematic grouping; related terms do not assert dependency."""
    groups = defaultdict(list)
    for row in developments:
        groups[(row["portfolio"], row["semantic"])].append(row)
    result = []
    for (portfolio_name, topic), items in groups.items():
        words = defaultdict(set)
        for item in items:
            for word in set(re.findall(r"[a-z0-9]{4,}", item["title"].lower())) - STOP:
                words[word].add(item["url"])
        repeated = sorted((w for w, refs in words.items() if len(refs) >= 2),
                          key=lambda w: (-len(words[w]), w))[:5]
        result.append({
            "portfolio": portfolio_name, "topic": topic, "items": items,
            "shared_terms": repeated, "count": len(items),
            "merged": sum("merged" in i["events"] for i in items),
            "closed": sum("closed" in i["events"] for i in items),
            "opened": sum("opened" in i["events"] for i in items),
        })
    return sorted(result, key=lambda g: (-g["merged"], -g["count"], g["portfolio"], g["topic"]))


def render_developments(evidence: list[dict], *, max_highlights: int = 5) -> str:
    developments = build_developments(evidence)
    topics = topic_groups(developments)
    rows = ['<section><h2>What changed: evidence-backed developments</h2>',
            '<p>Individual lifecycle events are consolidated by GitHub artifact. Themes use '
            'the same deterministic semantic classification rules as the TEM weekly monitor; '
            'shared terms indicate possible topical proximity, not a proven relationship.</p>']
    if not topics:
        rows.append('<p>No GitHub events observed in the selected repositories. '
                    'This is not evidence of inactivity.</p>')
    for group in topics[:max_highlights]:
        description = ("In " + group["portfolio"] + ", " + str(group["count"]) +
                       " distinct GitHub artifacts concern the TEM-derived theme " +
                       group["topic"].replace("_", " ") + ". " +
                       str(group["merged"]) + " PR merges, " + str(group["closed"]) +
                       " closures and " + str(group["opened"]) +
                       " openings were observed among them; events may overlap.")
        rows.append('<article><h3>' + escape(group["portfolio"] + " — " + group["topic"].replace("_", " ")) +
                    '</h3><p>' + escape(description) + '</p>')
        if group["shared_terms"]:
            rows.append('<p>Repeated title terms (candidate topical connections only): ' +
                        escape(", ".join(group["shared_terms"])) + '.</p>')
        rows.append('<ul>')
        for item in group["items"][:8]:
            rows.append('<li>' + _link(item["url"], item["title"]) + " — " +
                        escape(item["change"]) + " (" + escape(item["repository"]) + ")</li>")
        rows.append('</ul></article>')
    remaining = len(topics) - max_highlights
    if remaining > 0:
        rows.append('<p>' + str(remaining) + ' further thematic groups are listed in the evidence register below.</p>')
    rows.append('<h2>Open questions and interpretation boundaries</h2><p>Issue closure does not '
                'prove resolution, PR merge does not establish adoption, and source titles do '
                'not establish substantive impact. The monthly lifecycle collector cannot establish '
                'end-of-month open status or reasons for individual changes.</p>')
    rows.append('<details><summary>All thematic evidence groups (' + str(len(topics)) +
                ' groups; ' + str(len(developments)) + ' distinct artifacts)</summary>')
    for group in topics:
        rows.append('<h3>' + escape(group["portfolio"] + ' / ' + group["topic"]) + '</h3><ul>')
        for item in group["items"]:
            rows.append('<li>' + _link(item["url"], item["title"]) + ' — ' +
                        escape(item["change"]) + '</li>')
        rows.append('</ul>')
    rows.append('</details></section>')
    return "\n".join(rows)
