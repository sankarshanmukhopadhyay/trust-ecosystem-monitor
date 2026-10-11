"""Render one completed month without changing the legacy two-month prototype."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .monthly import month_bounds
from .confluence_search import search_month
from .toip_confluence_content_signals import collect
from .toip_experimental_combined import render


def publish_month(month: str, github_dir: Path, site: Path, *,
                  search=search_month, content_collect=collect) -> Path:
    month_bounds(month)
    path = github_dir / (month + ".json")
    gh = json.loads(path.read_text(encoding="utf-8"))
    if gh.get("period") != month:
        raise ValueError("incorrect GitHub reporting month")
    cf = search(month, resolve_missing=True)
    if cf.get("month") != month:
        raise ValueError("incorrect Confluence discovery month")
    contents = content_collect(month)
    if contents.get("month") != month:
        raise ValueError("incorrect Confluence content month")
    # Fail closed, before modifying public artifacts, if evidence unavailable.
    page = render(gh, cf, contents)
    target = site / month / "experimental-combined.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    index = site / "index.html"
    if not index.is_file():
        raise ValueError("missing current ToIP intelligence index")
    original = index.read_text(encoding="utf-8")
    link = ('<li><a href="' + month + '/experimental-combined.html">' + month +
            ' — monthly intelligence</a></li>')
    if ('href="' + month + '/experimental-combined.html"') not in original:
        if "</main>" not in original:
            raise ValueError("missing index main shell")
        index.write_text(original.replace("</main>", '<h2>Completed-month intelligence</h2><ul>' +
                                          link + '</ul></main>', 1), encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True)
    parser.add_argument("--github-dir", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    print("Published completed-month intelligence:", publish_month(args.month, args.github_dir, args.site))


if __name__ == "__main__":
    main()
