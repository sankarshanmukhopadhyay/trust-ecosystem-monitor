"""Publish only explicitly admitted Confluence observations alongside GitHub evidence.

Inputs are curator-reviewed, non-fixture JSON manifests. This stage neither
obtains Confluence permissions nor converts raw metadata into admissible records.
"""
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

from .toip_combined_report import compose, html as combined_html, markdown
from .toip_intelligence import MONTHS


def publish(github_dir: Path, admitted_dir: Path, site_dir: Path) -> list[str]:
    """Add both months' cross-source reports after validating *all* inputs.

    Fails closed before writing files if either month is absent/unadmitted.
    Existing GitHub-only site output remains the default when not invoked.
    """
    reports = {}
    for month in MONTHS:
        gh_path = github_dir / (month + ".json")
        cf_path = admitted_dir / (month + ".json")
        gh = json.loads(gh_path.read_text(encoding="utf-8"))
        cf = json.loads(cf_path.read_text(encoding="utf-8"))
        if gh.get("period") != month or cf.get("period") != month:
            raise ValueError("wrong period in combined publication manifest")
        if not cf.get("observations"):
            raise ValueError("real admitted Confluence observations required for " + month)
        reports[month] = compose(gh, cf)
    for month, report in reports.items():
        folder = site_dir / month
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "cross-source.html").write_text(combined_html(report), encoding="utf-8")
        (folder / "cross-source.md").write_text(markdown(report), encoding="utf-8")
        # Link reports into existing monthly intelligence pages, preserving
        # GitHub lifecycle evidence and the explicitly bounded interpretation.
        index = folder / "index.html"
        original = index.read_text(encoding="utf-8")
        link = '<p><a href="cross-source.html">Admitted GitHub + Confluence evidence</a></p>'
        if 'href="cross-source.html"' not in original:
            if "</main>" not in original:
                raise ValueError("missing monthly intelligence HTML shell")
            index.write_text(original.replace("</main>", link + "</main>", 1), encoding="utf-8")
    home = site_dir / "index.html"
    original = home.read_text(encoding="utf-8")
    links = '<section><h2>Admitted cross-source reports</h2><ul>' + "".join(
        '<li><a href="' + escape(month) + '/cross-source.html">' +
        escape(month) + ' — GitHub + Confluence</a></li>' for month in MONTHS
    ) + '</ul></section>'
    if 'href="2026-08/cross-source.html"' not in original:
        if "</main>" not in original:
            raise ValueError("missing intelligence index HTML shell")
        home.write_text(original.replace("</main>", links + "</main>", 1), encoding="utf-8")
    return list(reports)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-dir", type=Path, required=True)
    parser.add_argument("--admitted-dir", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    print("Published admitted cross-source months:", ", ".join(
        publish(args.github_dir, args.admitted_dir, args.site)))


if __name__ == "__main__":
    main()
