"""Converge experimental ToIP intelligence navigation on one annual destination.

Keep old technical routes for bookmarks; the public intelligence landing page
only advertises the annual report and explicitly discloses WIP status.
"""
from __future__ import annotations
from html import escape
from pathlib import Path
from .site_backend import STYLE

NOTICE = ("Work in progress. This independently maintained ToIP intelligence "
          "experiment combines public GitHub and Confluence observations. "
          "It is not an official ToIP publication; summaries, relationships, "
          "historical coverage and source rights remain provisional.")
PRIMARY = '<a href="../intelligence/toip/2026/">CY 2026 experimental intelligence (WIP)</a>'

def add_to_toip_overview(path: Path):
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    marker = 'href="../intelligence/toip/2026/"'
    if marker in content:
        return False
    card = ('<section class="card" aria-label="Experimental intelligence">'
            '<h2>Experimental intelligence · WIP</h2><p>' +
            escape(NOTICE) + '</p><p>' + PRIMARY + '</p></section>')
    if "</main>" not in content:
        raise ValueError("ToIP overview requires main content")
    path.write_text(content.replace("</main>", card + "</main>", 1), encoding="utf-8")
    return True

def replace_intelligence_landing(site: Path, year=2026):
    target = site / "intelligence" / "toip" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>TEM · Experimental ToIP intelligence</title><style>' +
            STYLE + '</style></head><body><header><div class="bar">'
            '<span class="brand">Trust Ecosystem Monitor</span>'
            '<a href="../../trustoverip/index.html">ToIP overview</a></div></header>'
            '<main><h1>Experimental ToIP intelligence</h1>'
            '<p class="lede"><strong>Work in progress.</strong> ' + escape(NOTICE) +
            '</p><div class="card"><h2>Calendar-year ' + str(year) + '</h2>'
            '<p>One cumulative report, updated as month-end observations and '
            'subsequent source revisions become available.</p>'
            '<p><a href="' + str(year) + '/">Open the CY ' + str(year) +
            ' intelligence report</a></p></div>'
            '<p class="muted">Legacy monthly evidence routes are retained '
            'for audit and citation, but are not separate primary reports.</p>'
            '</main></body></html>\n')
    target.write_text(page, encoding="utf-8")
    return target

def converge(site: Path):
    add_to_toip_overview(site / "trustoverip" / "index.html")
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
