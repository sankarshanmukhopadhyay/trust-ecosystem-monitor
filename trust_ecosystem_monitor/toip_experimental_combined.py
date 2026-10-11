"""Experimental public GitHub + Confluence discovery views, never admission."""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
from .confluence_search import search_month
from .toip_confluence_content_signals import collect as collect_content
from .toip_monthly_knowledge import render_developments

MONTHS = ("2026-08", "2026-09")
SOURCE = "https://lf-toip.atlassian.net/wiki/spaces/HOME/overview"
RUN = "https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/workflows/monthly-prototype.yml"


def render(github: dict, confluence: dict, content: dict | None = None) -> str:
    month = github.get("period")
    if month not in MONTHS or confluence.get("month") != month:
        raise ValueError("reporting period mismatch")
    events = github.get("evidence")
    if not isinstance(events, list):
        raise ValueError("GitHub event list required")
    if confluence.get("coverage") != "sample_only" or confluence.get("resolved_space_ids") != ["22970380"]:
        raise ValueError("verified HOME public discovery sample required")
    count = confluence.get("sample_count")
    total = confluence.get("total_size")
    if type(count) is not int or count < 0 or type(total) is not int or total < count:
        raise ValueError("invalid Confluence sample counts")
    if confluence.get("missing_space_count") != 0:
        raise ValueError("unresolved Confluence space identity")
    developments = render_developments(events)
    content = content or {"month": month, "pages": [], "unavailable_count": 0}
    if content.get("month") != month or not isinstance(content.get("pages"), list):
        raise ValueError("Confluence content period or schema mismatch")
    page_rows = []
    for page in content["pages"]:
        if not isinstance(page, dict) or not str(page.get("id", "")).isdigit():
            raise ValueError("invalid public page provenance")
        link = "https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/" + str(page["id"])
        headings = page.get("topic_headings") or []
        if not isinstance(headings, list) or not all(isinstance(h, str) for h in headings):
            raise ValueError("invalid Confluence headings")
        summary = ("Headings identify these recorded topics: " + ", ".join(headings[:5]) +
                   ".") if headings else "No substantive heading-based summary can be supported from available page content."
        page_rows.append('<li><a href="' + escape(link, quote=True) + '">' +
                         escape(str(page.get("title") or "Confluence page")) + '</a> — ' +
                         escape(summary) + ' <small>(version ' +
                         escape(str(page.get("version") or "unknown")) + ')</small></li>')
    confluence_knowledge = (
        '<section><h2>What Confluence records describe</h2>'
        '<p>Page headings are extracted from public page content as <strong>descriptive topic signals</strong>, '
        'not semantic abstracts, approved decisions, or evidence that discussions occurred during this month. '
        'Historical CQL finds pages last modified in the period, possibly describing earlier meetings.</p>' +
        ('<ul>' + "".join(page_rows) + '</ul>' if page_rows else
         '<p>No page-level content signals could be extracted. No account of the recorded discussion can be substantiated.</p>') +
        '<p>Page content available for topic extraction: ' + str(len(page_rows)) +
        '; unavailable or out-of-scope records: ' +
        escape(str(content.get("unavailable_count", 0))) +
        '. The source collection is bounded and may be incomplete.</p></section>')
    body = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Experimental ToIP combined evidence — " + month + "</title></head><body><main>"
            "<nav><a href=\"../\">Monthly intelligence</a> · <a href=\"../coverage/\">Coverage</a></nav>"
            "<h1>Experimental combined ToIP intelligence — " + month + "</h1>"
            "<p><strong>Experimental; non-authoritative.</strong> GitHub lifecycle observations and public "
            "Confluence last-modified discovery counts are presented together, not correlated as governance decisions.</p>"
            "<p>" + str(len(events)) + " observed GitHub lifecycle events in the configured repository set.</p>" + developments + confluence_knowledge
            "<h2>Confluence public discovery</h2><p><a href=\"" + SOURCE + "\">ToIP HOME space</a> "
            "(space ID 22970380). Public CQL search returned " + str(count) +
            " matching results (reported total " + str(total) + ") for pages last modified in " + month +
            ". All sampled space identities resolved to HOME. Coverage: <strong>sample only</strong>; "
            "not historical version reconstruction, independent admission, or proof of publication rights.</p>"
            "<p>Discovery query semantics: page last-modified month, not creation or meeting date. "
            "A page may have multiple historical updates; this view does not assert their number or contents.</p>"
            "<h2>Cross-source interpretation</h2><p>No verified page-to-GitHub subject-level "
            "correlation is established by these aggregate Confluence counts. The two source "
            "signals are shown together solely to test the reporting and information architecture.</p>"
            "<h2>Reproducibility and limitations</h2><p><a href=\"" + RUN +
            "\">Workflow and source code</a>. Public endpoints are accessed without an Atlassian app. "
            "Missing or inaccessible data is not zero activity. This is not a ToIP endorsement, "
            "decision record, or assured report.</p></main></body></html>\n")
    return body


def publish(github_dir: Path, site: Path, *, search=search_month) -> list[str]:
    prepared = {}
    for month in MONTHS:
        github = json.loads((github_dir / (month + ".json")).read_text(encoding="utf-8"))
        cf = search(month, resolve_missing=True)
        try:
            signals = collect_content(month)
        except (OSError, ValueError, UnicodeError, TimeoutError) as exc:
            signals = {"month": month, "pages": [], "unavailable_count": "collection unavailable: " + type(exc).__name__}
        prepared[month] = render(github, cf, signals)
    for month, page in prepared.items():
        dest = site / month
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "experimental-combined.html").write_text(page, encoding="utf-8")
        index = dest / "index.html"
        source = index.read_text(encoding="utf-8")
        link = '<p><a href="experimental-combined.html">Experimental GitHub + Confluence combined view</a></p>'
        if 'href="experimental-combined.html"' not in source:
            if "</main>" not in source:
                raise ValueError("missing monthly shell")
            index.write_text(source.replace("</main>", link + "</main>", 1), encoding="utf-8")
    home = site / "index.html"
    source = home.read_text(encoding="utf-8")
    link = '<section><h2>Experimental combined views</h2><ul>' + "".join(
        '<li><a href="' + m + '/experimental-combined.html">' + m + ' — GitHub + Confluence discovery</a></li>'
        for m in MONTHS) + '</ul></section>'
    if 'href="2026-08/experimental-combined.html"' not in source:
        if "</main>" not in source:
            raise ValueError("missing intelligence shell")
        home.write_text(source.replace("</main>", link + "</main>", 1), encoding="utf-8")
    return list(prepared)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-dir", required=True, type=Path)
    parser.add_argument("--site", required=True, type=Path)
    args = parser.parse_args()
    print("Experimental combined views:", ", ".join(publish(args.github_dir, args.site)))


if __name__ == "__main__":
    main()
