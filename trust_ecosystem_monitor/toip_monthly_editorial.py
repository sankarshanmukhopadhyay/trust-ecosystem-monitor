"""Monthly TEM intelligence: conservative priority, useful content and shared visual language."""
from __future__ import annotations
from collections import Counter
from html import escape
from .site_backend import STYLE
from .toip_monthly_knowledge import build_developments, topic_groups
from .toip_monthly_cross_source import correlate

def _a(url, label):
    if not (url.startswith("https://github.com/") or url.startswith("https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/")):
        raise ValueError("untrusted evidence link")
    return '<a href="' + escape(url, quote=True) + '">' + escape(str(label)) + '</a>'

def _table(headers, rows, empty):
    return ('<div class="table-wrap"><table><thead><tr>' +
            ''.join('<th scope="col">' + escape(h) + '</th>' for h in headers) +
            '</tr></thead><tbody>' + (''.join(rows) if rows else
            '<tr><td colspan="' + str(len(headers)) + '">' + escape(empty) +
            '</td></tr>') + '</tbody></table></div>')

def priority(change, refs):
    """Priority = review order, not severity or claim of project defect."""
    if refs and change["semantic"] in {"security", "privacy", "authority", "governance", "interop", "protocol_semantics"}:
        return "Review first", "Cross-source reference and consequential TEM-derived topic"
    if change["change"] == "PR merge observed" and change["semantic"] not in {"unknown", "editorial"}:
        return "Notable", "Observed merge in a substantive topic"
    return "Context", "Other observed activity; consequence unassessed"

def present(github, content, legacy_html: str) -> str:
    """Prepend decision-first intelligence; retain full legacy inventory as evidence appendix."""
    period = github["period"]
    developments = build_developments(github.get("evidence", []))
    links = correlate(github, content)
    explicit = {x["github"] for x in links if x["state"] == "explicit_reference"}
    assessments = [(priority(d, d["url"] in explicit), d) for d in developments]
    order = {"Review first": 0, "Notable": 1, "Context": 2}
    assessments.sort(key=lambda x: (order[x[0][0]], x[1]["portfolio"], x[1]["url"]))
    review = sum(p[0] == "Review first" for p, d in assessments)
    pages = content.get("pages", [])
    usable = [p for p in pages if p.get("page_kind", "substantive") == "substantive" and p.get("section_abstracts")]
    administrative = len(pages) - len(usable)
    source_rows = []
    for page in usable:
        for section in page.get("section_abstracts", [])[:3]:
            if not section.get("basis_sha256"):
                raise ValueError("untraceable Confluence statement")
            cues = ", ".join(section.get("language_signals", [])) or "none"
            label = section.get("abstract", "No supported content interpretation.")
            source_rows.append('<tr><td>' + _a(page.get("url") or "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/" + str(page["id"]), page["title"]) +
                '<br><small>Page version ' + escape(str(page.get("version", "unknown"))) +
                ' · retrieved version may postdate reporting month</small></td><td>' +
                escape(section.get("section", "General")) + '</td><td>' +
                escape(label) + '</td><td>' + escape(cues) +
                '<br><small>Wording cues only; no decision inferred</small></td></tr>')
    development_rows = []
    for (level, reason), d in assessments:
        development_rows.append('<tr><td><span class="pill">' + escape(level) +
            '</span></td><td>' + escape(d["portfolio"]) + ' / ' +
            escape(d["semantic"].replace("_", " ")) + '</td><td>' +
            _a(d["url"], d["title"]) + '<br><small>' +
            escape(d["change"]) + '</small></td><td>' +
            escape(reason) + '</td><td>' + _a(d["url"], "GitHub record") + '</td></tr>')
    relation_rows = []
    for item in links:
        relation_rows.append('<tr><td>' +
            escape("Explicit link" if item["state"] == "explicit_reference" else "Candidate: lexical") +
            '</td><td>' + escape(item["subject"]) + '</td><td>' +
            escape(item["basis"]) + '</td><td>' +
            _a(item["page"], "Confluence") + ' · ' +
            _a(item["github"], "GitHub") + '</td></tr>')
    topic_rows = []
    for g in topic_groups(developments):
        topic_rows.append('<tr><td>' + escape(g["portfolio"]) + '</td><td>' +
            escape(g["topic"].replace("_", " ")) + '</td><td>' + str(g["count"]) +
            '</td><td>' + str(g["merged"]) +
            '</td><td>' + escape(", ".join(g["shared_terms"]) or "No repeated topic terms") + '</td></tr>')
    top_developments = [(p, d) for p, d in assessments if p[0] != "Context"][:5]
    brief = '<ul>' + ''.join(
        '<li><strong>' + escape(d["portfolio"]) + ':</strong> ' +
        _a(d["url"], d["title"]) + ' — ' + escape(d["change"]) +
        '; ' + escape(p[1].lower()) + '.</li>' for p, d in top_developments) + '</ul>'
    if not top_developments:
        brief = '<p>No evidence-supported notable developments identified in the bounded event inventory.</p>'
    metrics = ((len(developments), "distinct GitHub artifacts"),
               (len(usable), "substantive Confluence pages"),
               (sum(x["state"] == "explicit_reference" for x in links), "explicit cross-source links"),
               (review, "review-first observations"))
    summary = ('<header><div class="bar"><span class="brand">Trust Ecosystem Monitor</span>'
               '<a href="../">ToIP intelligence</a><a href="../coverage/">Coverage</a>'
               '<a href="../methodology/">Method</a></div></header>'
               '<main><h1>Monthly ToIP intelligence · ' + escape(period) + '</h1>'
               '<p class="lede">Independent evidence-based monthly brief. '
               'Attention rankings are editorial review order, not project severity. '
               'No automatic adoption, governance or causation inference.</p>'
               '<div class="metrics">' + ''.join('<div class="metric"><strong>' + str(n) +
               '</strong><span>' + escape(label) + '</span></div>' for n, label in metrics) +
               '</div><h2>Executive intelligence brief</h2>' + brief +
               '<h2>Prioritized developments</h2>' +
               _table(["Attention", "Portfolio / topic", "Observed development", "Basis", "Evidence"],
                      development_rows[:40], "No observed developments.") +
               '<h2>What substantive Confluence records describe</h2>'
               '<p>Compact source-grounded descriptions from substantive page sections. '
               'Dates of page modifications do not establish the dates of meetings or decisions. '
               'Wording signals are not validated actions or decisions.</p>' +
               _table(["Source and version", "Section", "Content-grounded summary", "Signals"],
                      source_rows[:60], "No substantive Confluence text could be summarized.") +
               '<p class="muted">' + str(administrative) +
               ' pages excluded from the main discussion summary as administrative, template or content-poor. '
               'They remain subject to review.</p>' +
               '<h2>Cross-source review seams</h2>' +
               _table(["Strength", "Subject", "Why linked", "Evidence"], relation_rows,
                      "No explicit cross-source links or candidate relationships established.") +
               '<h2>Workstream pulse</h2>' +
               _table(["Portfolio", "Semantic topic", "Artifacts", "PR merges", "Shared title terms"], topic_rows,
                      "No thematic developments.") +
               '<h2>Evidence, method and limitations</h2>'
               '<p>Source use and authority remain unverified. The underlying collection is bounded '
               'and incomplete; current Confluence versions may not reflect historical month-end state. '
               'See the full audit-oriented evidence appendix below.</p>')
    # Preserve source inventory behind a disclosure, but never expose its old
    # competing header, scripts, CSS or navigation.
    begin = legacy_html.find("<main>")
    end = legacy_html.rfind("</main>")
    appendix = legacy_html[begin+len("<main>"):end] if begin >= 0 and end > begin else ""
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Monthly ToIP intelligence ' + escape(period) + '</title><style>' +
            STYLE + '.table-wrap{overflow-x:auto} details{margin-top:1.5rem}'
            '</style></head><body>' + summary +
            '<details><summary>Full source activity and experimental evidence register</summary>' +
            appendix + '</details></main><footer>Independent TEM experimental intelligence · ' +
            escape(period) + '</footer></body></html>\n')
    return page
