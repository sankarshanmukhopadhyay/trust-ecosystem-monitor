"""Experimental public GitHub + Confluence discovery views, never admission."""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
from .confluence_search import search_month

MONTHS = ("2026-08", "2026-09")
SOURCE = "https://lf-toip.atlassian.net/wiki/spaces/HOME/overview"
RUN = "https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/workflows/monthly-prototype.yml"


def render(github: dict, confluence: dict) -> str:
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
    rows = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid GitHub event")
        url = event.get("url")
        if not isinstance(url, str) or not url.startswith("https://github.com/"):
            raise ValueError("unsafe GitHub evidence URL")
        rows.append("<li>" + escape(str(event.get("occurred_at", ""))[:10]) + " — <a href=\"" +
                    escape(url, quote=True) + "\">" + escape(str(event.get("title", "GitHub event"))) +
                    "</a></li>")
    body = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Experimental ToIP combined evidence — " + month + "</title></head><body><main>"
            "<nav><a href=\"../\">Monthly intelligence</a> · <a href=\"../coverage/\">Coverage</a></nav>"
            "<h1>Experimental combined ToIP intelligence — " + month + "</h1>"
            "<p><strong>Experimental; non-authoritative.</strong> GitHub lifecycle observations and public "
            "Confluence last-modified discovery counts are presented together, not correlated as governance decisions.</p>"
            "<h2>GitHub lifecycle evidence</h2><p>" + str(len(rows)) + " observed events in the configured "
            "repository set; not a complete ToIP activity inventory.</p><ul>" + "".join(rows) + "</ul>"
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
        prepared[month] = render(github, cf)
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
