"""Converge experimental ToIP intelligence navigation on explicit reader journeys.

Keep old technical routes for bookmarks; the public intelligence landing pages
make the canonical ToIP entry point, annual report, coverage/methodology pages
and machine-ingestion data route visible without weakening source boundaries.
"""
from __future__ import annotations
from html import escape
from pathlib import Path
from .site_backend import STYLE

NOTICE = ("Work in progress. This independently maintained ToIP intelligence "
          "experiment combines public GitHub and bounded Confluence observations. "
          "It is not an official ToIP publication; summaries, relationships, "
          "historical coverage and source rights remain provisional.")
PRIMARY = '<a href="../intelligence/toip/">ToIP intelligence entry point</a>'
YEAR = 2026


def _page(title: str, body: str, *, nav_prefix: str = "") -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + escape(title) + '</title><style>' + STYLE + '</style></head>'
            '<body><header><div class="bar"><span class="brand">Trust Ecosystem Monitor</span>'
            '<a href="' + nav_prefix + '../trustoverip/index.html">ToIP overview</a>'
            '<a href="' + nav_prefix + 'toip/">ToIP intelligence</a>'
            '<a href="' + nav_prefix + 'toip/' + str(YEAR) + '/">CY ' + str(YEAR) + '</a>'
            '<a href="' + nav_prefix + 'toip/coverage/">Coverage</a>'
            '<a href="' + nav_prefix + 'toip/methodology/">Methodology</a>'
            '</div></header><main>' + body + '</main></body></html>\n')


def add_to_toip_overview(path: Path):
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    marker = 'href="../intelligence/toip/"'
    if marker in content:
        return False
    card = ('<section class="card" aria-label="Experimental intelligence">'
            '<h2>Experimental intelligence · WIP</h2><p>' + escape(NOTICE) + '</p>'
            '<p>' + PRIMARY + '</p>'
            '<ul>'
            '<li><a href="../intelligence/toip/' + str(YEAR) + '/">CY ' + str(YEAR) + ' annual report</a></li>'
            '<li><a href="../intelligence/toip/coverage/">Coverage and source limits</a></li>'
            '<li><a href="../intelligence/toip/methodology/">Evidence and inference methodology</a></li>'
            '<li><a href="../intelligence/toip/' + str(YEAR) + '/data/manifest.json">Machine-ingestion manifest</a></li>'
            '</ul></section>')
    if "</main>" not in content:
        raise ValueError("ToIP overview requires main content")
    path.write_text(content.replace("</main>", card + "</main>", 1), encoding="utf-8")
    return True


def replace_intelligence_root(site: Path, year=YEAR):
    target = site / "intelligence" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = ('<h1>Ecosystem intelligence</h1>'
            '<p class="lede">Independent evidence-based ecosystem reporting. '
            'This route is the cross-ecosystem index; the current public intelligence product is the ToIP WIP surface.</p>'
            '<section class="card"><h2>Trust over IP intelligence</h2>'
            '<p>Start with the ToIP intelligence entry point for reader guidance, source boundaries and links to annual, coverage, methodology and machine-ingestion routes.</p>'
            '<p><a href="toip/">Open ToIP intelligence entry point</a></p></section>'
            '<section class="card"><h2>Human pages and data routes</h2>'
            '<p>Human pages explain evidence and limits. Machine consumers should use the annual manifest rather than scrape rendered HTML.</p>'
            '<ul><li><a href="toip/' + str(year) + '/">Human CY ' + str(year) + ' report</a></li>'
            '<li><a href="toip/' + str(year) + '/data/manifest.json">Machine-ingestion manifest</a></li>'
            '</ul></section>')
    target.write_text(_page("TEM · Ecosystem intelligence", body, nav_prefix=""), encoding="utf-8")
    return target


def replace_intelligence_landing(site: Path, year=YEAR):
    target = site / "intelligence" / "toip" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = ('<h1>ToIP intelligence · reader entry point</h1>'
            '<p class="lede"><strong>Work in progress.</strong> ' + escape(NOTICE) + '</p>'
            '<section class="card"><h2>Read first</h2>'
            '<p>This page is the canonical ToIP intelligence entry point. It distinguishes the human annual report from the machine-ingestion data route and keeps source-boundary disclosures visible.</p>'
            '<ol><li><a href="' + str(year) + '/">Open the CY ' + str(year) + ' human report</a></li>'
            '<li><a href="coverage/">Check coverage and source limits</a></li>'
            '<li><a href="methodology/">Read evidence and inference methodology</a></li>'
            '<li><a href="' + str(year) + '/data/manifest.json">Use the machine-ingestion manifest</a></li></ol></section>'
            '<section class="card"><h2>Human report vs machine data</h2>'
            '<p><strong>Human HTML:</strong> rendered reader pages for context, limitations and navigation.</p>'
            '<p><strong>Machine data:</strong> generated annual manifest for tooling; do not scrape HTML when `manifest.json` is available.</p>'
            '</section>'
            '<section class="card"><h2>Boundaries</h2>'
            '<p>LFX meeting and Zoom records are not admitted to the combined intelligence. Public Confluence discovery is bounded and cannot establish complete ToIP meeting coverage. Missing evidence is not evidence of inactivity.</p>'
            '<p>Legacy monthly evidence routes are retained for audit and citation, but are not separate primary reports.</p>'
            '</section>')
    target.write_text(_page("TEM · ToIP intelligence entry point", body, nav_prefix="../"), encoding="utf-8")
    return target


def converge(site: Path):
    add_to_toip_overview(site / "trustoverip" / "index.html")
    replace_intelligence_root(site)
    replace_intelligence_landing(site)
    index = site / "index.html"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        import re
        # Historically added top-level preview links should not compete with
        # the ToIP ecosystem card.
        text = re.sub(r'<p><a href="(?:monthly/index\.html|intelligence/toip/)">[^<]*</a></p>', "", text)
        index.write_text(text, encoding="utf-8")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True, type=Path)
    args = p.parse_args()
    converge(args.site)

if __name__ == "__main__":
    main()
