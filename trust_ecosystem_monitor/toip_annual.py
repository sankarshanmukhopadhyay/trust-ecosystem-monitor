"""Single annual intelligence page, regenerated from immutable monthly evidence."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from .monthly import month_bounds
from .site_backend import STYLE
from .toip_annual_state import read, ingest, write, validate
from .toip_confluence_content_signals import collect
from .toip_tracked_sources import inspect
from .toip_monthly_knowledge import build_developments, topic_groups
from .toip_monthly_editorial import priority
from .toip_monthly_cross_source import correlate
from .toip_wgtf_report import render_wgtf_first_section
from .toip_subject_timeline import render_timelines

def link(url, label):
    if not (url.startswith("https://github.com/") or
            url.startswith("https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/")):
        raise ValueError("invalid source URL")
    return '<a href="' + escape(url, quote=True) + '">' + escape(str(label)) + '</a>'

def reference_link(url):
    """Only safe, supported external citation hosts may be rendered."""
    from urllib.parse import urlsplit
    if not isinstance(url, str):
        return ""
    parsed = urlsplit(url)
    allowed = {"github.com", "lf-toip.atlassian.net", "trustoverip.org",
               "w3.org", "www.w3.org", "identity.foundation", "ietf.org", "datatracker.ietf.org"}
    if (parsed.scheme != "https" or not parsed.hostname or
        (parsed.hostname not in allowed and not parsed.hostname.endswith(".github.io")) or
        parsed.username or parsed.password or len(url) > 600):
        return ""
    return '<a rel="noopener noreferrer" href="' + escape(url, quote=True) + '">' + escape(parsed.hostname) + '</a>'

def table(columns, rows):
    return ('<div class="table-wrap"><table><thead><tr>' +
            ''.join('<th scope="col">' + escape(x) + '</th>' for x in columns) +
            '</tr></thead><tbody>' + (''.join(rows) if rows else
            '<tr><td colspan="' + str(len(columns)) + '">No observations available</td></tr>') +
            '</tbody></table></div>')

def render(state):
    validate(state)
    year = state["year"]
    monthly, sources, chronicle = [], [], []
    ranked, relations = [], []
    unique_sources, events = set(), 0
    for month, entry in sorted(state["months"].items()):
        snapshot = entry["observation"]
        github = {x["url"]: x for x in snapshot["github"]["evidence"] if x.get("url")}
        events += len(github)
        recovered = [{"id": p["id"], "title": p["title"],
                      "github_references": p.get("github_references", []),
                      "section_abstracts": [{"section": x["heading"],
                          "abstract": x["abstract"]} for x in p["evidence"]]}
                     for p in snapshot["confluence"]["sources"]]
        relationships = correlate({"period": month, "evidence": list(snapshot["github"]["evidence"])},
                                  {"month": month, "pages": recovered})
        explicit = {x["github"] for x in relationships if x["state"] == "explicit_reference"}
        for item in build_developments(snapshot["github"]["evidence"]):
            (grade, reason) = priority(item, item["url"] in explicit)
            ranked.append(({"Review first": 0, "Notable": 1, "Context": 2}[grade], month, grade, reason, item))
        for rel in relationships:
            relations.append('<tr><td>' + escape(month) + '</td><td>' +
                             escape("Explicit link" if rel["state"] == "explicit_reference" else "Candidate") +
                             '</td><td>' + escape(rel["subject"]) + '</td><td>' +
                             link(rel["page"], "Confluence") + ' · ' +
                             link(rel["github"], "GitHub") + '</td></tr>')
        rows = []
        for row in github.values():
            representation = link(row["url"], row.get("title", "GitHub observation"))
            monthly.append('<tr><td>' + escape(month) + '</td><td>' +
                           representation + '</td><td>' + escape(str(row.get("event", ""))) + '</td></tr>')
            rows.append('<li>' + representation + '</li>')
        for observed_page in snapshot["confluence"]["sources"]:
            unique_sources.add(observed_page["id"])
            # Original month evidence remains immutable. Display the newest
            # inspected interpretation with an explicit observed-version label.
            ledger = state["source_ledger"].get(observed_page["id"], [])
            page = ledger[-1] if ledger else observed_page
            blocks = page.get("discussions", [])
            if blocks and page.get("page_kind") != "administrative":
                details = []
                for block in blocks[:5]:
                    references = block.get("references", [])[:5]
                    refs = ' '.join(reference_link(url) for url in references)
                    details.append('<div class="discussion"><strong>' +
                                   escape(block.get("heading", "Discussion")) + '</strong>: ' +
                                   escape(block.get("summary", "")) +
                                   ('<p><small>References: ' + refs + '</small></p>' if refs else '') +
                                   '<small>Evidence block ' +
                                   escape(str(block.get("source_block_number", "unknown"))) +
                                   '; classification is provisional</small></div>')
                summary = ''.join(details)
            else:
                summary = escape('; '.join(v.get("abstract", "") for v in page.get("evidence", [])[:2]) or
                                 "No defensible substantive discussion available; re-inspection required.")
            is_later = (page.get("version") != observed_page.get("version") or
                        page.get("content_fingerprint") != observed_page.get("content_fingerprint"))
            sources.append('<tr><td>' + escape(month) + '</td><td>' +
                           link(page["url"], page["title"]) + ' <small>(observed version ' +
                           escape(str(page["version"])) + ')</small>' +
                           (' <small>Updated interpretation; original month evidence preserved.</small>' if is_later else '') +
                           '</td><td>' + summary + '</td></tr>')
        chronicle.append('<section id="month-' + escape(month) + '"><h3>' + escape(month) +
                         '</h3><p>First collected ' + escape(entry["observed_at"]) +
                         '; ' + str(len(github)) + ' distinct GitHub artifacts and ' +
                         str(len(snapshot["confluence"]["sources"])) +
                         ' Confluence pages observed retrospectively.</p><details><summary>Monthly artifact evidence</summary><ul>' +
                         ''.join(rows) + '</ul></details></section>')
    ranked.sort(key=lambda x: (x[0], x[1], x[4]["portfolio"], x[4]["url"]))
    attention_rows = []
    for _, month, grade, reason, item in ranked[:80]:
        attention_rows.append('<tr><td>' + escape(grade) + '</td><td>' +
                              escape(month) + '</td><td>' + escape(item["portfolio"]) +
                              ' / ' + escape(item["semantic"].replace("_", " ")) +
                              '</td><td>' + link(item["url"], item["title"]) + '</td><td>' +
                              escape(reason) + '</td></tr>')
    revisions = []
    for notice in reversed(state["revision_notices"]):
        source = notice["source"]
        label = link(source, "Source") if source.startswith(
            "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/") else escape(source)
        revisions.append('<tr><td>' + escape(notice["observed_at"]) + '</td><td>' +
                         label + '</td><td>' + escape(notice["kind"].replace("_", " ")) +
                         '</td><td>' + escape(notice["explanation"]) +
                         '</td><td>' + escape(notice["impact"]) + '</td></tr>')
    body = ('<header><div class="bar"><strong class="brand">Trust Ecosystem Monitor</strong>'
            '<a href="../">ToIP intelligence</a><a href="../coverage/">Coverage</a></div></header>'
            '<main><h1>ToIP calendar-year intelligence · ' + str(year) + '</h1>'
            '<p class="lede">A cumulative, source-linked account of recorded developments and '
            'subsequent evidence revisions. Historical observations are immutable.</p>'
            '<p><strong>Independent experimental report.</strong> Retrospective source observations '
            'do not establish meeting dates, decisions, publication rights or formal authority.</p>'
            '<div class="metrics"><div class="metric"><strong>' + str(len(state["months"])) +
            '</strong><span>months retained</span></div><div class="metric"><strong>' +
            str(events) + '</strong><span>monthly GitHub artifacts</span></div><div class="metric"><strong>' +
            str(len(unique_sources)) + '</strong><span>Confluence pages</span></div>'
            '<div class="metric"><strong>' + str(len(revisions)) +
            '</strong><span>revision notices</span></div></div>' +
            render_wgtf_first_section(state) +
            '<h2>Prioritized year-to-date developments</h2>'
            '<p>Attention ranking reuses TEM monthly semantic classifications. '
            'It is a review ordering rather than institutional severity or a '
            'validated conclusion about adoption.</p>' +
            table(["Review order", "Month", "Workstream", "Development", "Basis"],
                  attention_rows) +
            '<h2>Cross-source relationships</h2><p>Direct links are observed '
            'references; lexical candidates remain unverified.</p>' +
            table(["Month", "Strength", "Subject", "Evidence"], relations[:100]) +
            '<h2>Year-to-date observed developments</h2>' +
            table(["Month", "GitHub source", "Observed lifecycle"], monthly[:120]) +
            '<h2>Substantive Confluence discussion and references</h2><p>Selected evidence passages '
            'derive from bounded text sections of the public version retrieved when observed, '
            'which may be newer than the stated reporting month.</p>' +
            table(["Observed month", "Page and version", "Discussion and linked references"], sources[:120]) +
            '<h2>Subsequent source revisions</h2><p>Changed versions and content '
            'fingerprints trigger review notices; TEM does not automatically '
            'invalidate or rewrite a historical finding.</p>' +
            table(["Observed", "Source", "Change", "Reason", "Disposition"], revisions) +
            '<h2>Monthly chronicle</h2>' + ''.join(chronicle) +
            '<h2>Evidence and limitations</h2><p>First observations are preserved in '
            'the annual manifest. Missing historical source versions cannot be reconstructed. '
            'Absence of observations does not prove inactivity. Source-use permission '
            'and review of substantive interpretation remain separate requirements.</p></main>'
            '<footer>Independent TEM annual intelligence; non-authoritative</footer>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>TEM calendar year ' + str(year) + '</title><style>' + STYLE +
            '.table-wrap{overflow-x:auto}</style></head><body>' + body + '</body></html>\n')

def publish(month, github_dir: Path, site: Path, *,
            content_collect=collect, tracked_collect=inspect, observed_at=None):
    month_bounds(month)
    year = int(month[:4])
    when = observed_at or datetime.now(timezone.utc).isoformat()
    annual = site / str(year)
    manifest = annual / "data" / "manifest.json"
    state = read(manifest, year)
    github = json.loads((github_dir / (month + ".json")).read_text(encoding="utf-8"))
    if github.get("period") != month:
        raise ValueError("GitHub period mismatch")
    content = content_collect(month)
    if content.get("month") != month or content.get("coverage") != "sample_only":
        raise ValueError("Confluence month or coverage mismatch")
    ids = sorted(state["source_ledger"], key=int)
    tracked = tracked_collect(ids) if ids else {"pages": [], "unavailable": []}
    updated = ingest(state, github, content, observed_at=when, tracked_pages=tracked["pages"])
    page = render(updated)
    index = site / "index.html"
    if not index.is_file():
        raise ValueError("missing ToIP index")
    old = index.read_text(encoding="utf-8")
    marker = 'href="' + str(year) + '/"'
    if marker not in old:
        if "</main>" not in old:
            raise ValueError("missing ToIP main shell")
        old = old.replace("</main>", '<p><a ' + marker + '>CY ' + str(year) +
                          ' cumulative intelligence</a></p></main>', 1)
    write(manifest, updated)
    (annual / "index.html").write_text(page, encoding="utf-8")
    index.write_text(old, encoding="utf-8")
    return annual / "index.html"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--month", required=True)
    p.add_argument("--github-dir", required=True, type=Path)
    p.add_argument("--site", required=True, type=Path)
    args = p.parse_args()
    print("Cumulative intelligence:", publish(args.month, args.github_dir, args.site))

if __name__ == "__main__":
    main()
