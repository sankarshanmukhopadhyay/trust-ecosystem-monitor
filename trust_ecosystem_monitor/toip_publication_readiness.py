"""Offline release gate for the ToIP intelligence Pages publication.

Run after the monthly workflow has staged docs/, before uploading Pages.
This checks locally generated artifacts; it does not claim public deployment.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

REQUIRED = (
    "index.html",
    "monthly/index.html",
    "monthly/2026-08-report.html",
    "monthly/2026-09-report.html",
    "intelligence/index.html",
    "intelligence/toip/index.html",
    "intelligence/toip/coverage/index.html",
    "intelligence/toip/methodology/index.html",
    "intelligence/toip/2026-08/index.html",
    "intelligence/toip/2026-09/index.html",
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.links.append(href)


def check(root: Path) -> list[str]:
    errors = []
    root = root.resolve()
    for name in REQUIRED:
        path = root / name
        if not path.is_file():
            errors.append("Missing required page: " + name)
            continue
        content = path.read_text(encoding="utf-8")
        if "<html" not in content.lower() or "</html>" not in content.lower():
            errors.append("Invalid HTML shell: " + name)
        if name.startswith("intelligence/toip/"):
            if "LFX" not in content:
                errors.append("Missing LFX coverage disclosure: " + name)
        links = Links()
        links.feed(content)
        for href in links.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or href.startswith("#"):
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root):
                errors.append("Link escapes Pages root: " + name + " -> " + href)
                continue
            if destination.is_dir():
                destination /= "index.html"
            if not destination.is_file():
                errors.append("Broken local link: " + name + " -> " + href)
    if (root / "intelligence/toip/coverage/index.html").is_file():
        coverage = (root / "intelligence/toip/coverage/index.html").read_text(encoding="utf-8")
        for marker in ("Confluence", "GitHub", "Pending / deferred", "publication rights"):
            if marker.lower() not in coverage.lower():
                errors.append("Missing coverage marker: " + marker)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("docs"))
    args = parser.parse_args()
    errors = check(args.site)
    for error in errors:
        print("ERROR: " + error)
    if errors:
        print(f"FAIL: {len(errors)} publication readiness errors")
        return 1
    print("PASS: ToIP intelligence local publication readiness (not live deployment)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
