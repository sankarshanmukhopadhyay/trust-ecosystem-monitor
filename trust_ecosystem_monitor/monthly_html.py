"""Dependency-free, escaped, accessible HTML presentation of monthly reports.

HTML is derived from report Markdown, not from unverified external markup.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

LINK = re.compile(r"\[([^\]]+)\]\((https://[^\s)]+)\)")


def inline(value: str) -> str:
    """Escape untrusted text before turning safe HTTPS links into anchors."""
    result = []
    pos = 0
    for match in LINK.finditer(value):
        result.append(html.escape(value[pos:match.start()]))
        result.append(
            '<a href="' + html.escape(match.group(2), quote=True)
            + '" rel="noopener noreferrer">' + html.escape(match.group(1)) + "</a>"
        )
        pos = match.end()
    result.append(html.escape(value[pos:]))
    return "".join(result)


def render_html(markdown: str, *, title: str = "ToIP monthly activity report") -> str:
    body = []
    paragraph = []
    table = []
    def flush_paragraph():
        if paragraph:
            body.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()
    def flush_table():
        if table:
            rows = [r.strip().strip("|").split("|") for r in table]
            body.append('<div class="table-scroll"><table>')
            for index, cells in enumerate(rows):
                if index == 1 and all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                    continue
                tag = "th" if index == 0 else "td"
                body.append("<tr>" + "".join(f"<{tag}>" + inline(c.strip()) + f"</{tag}>" for c in cells) + "</tr>")
            body.append("</table></div>")
            table.clear()
    in_list = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            if in_list:
                body.append("</ul>")
                in_list = False
            table.append(line)
            continue
        flush_table()
        if not line:
            flush_paragraph()
            if in_list:
                body.append("</ul>")
                in_list = False
            continue
        if line.startswith("#"):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                flush_paragraph()
                if in_list:
                    body.append("</ul>")
                    in_list = False
                level = len(match.group(1))
                body.append(f"<h{level}>" + inline(match.group(2)) + f"</h{level}>")
                continue
        if line.startswith("- "):
            flush_paragraph()
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append("<li>" + inline(line[2:]) + "</li>")
        elif line.startswith("> "):
            flush_paragraph()
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
        else:
            if in_list:
                body.append("</ul>")
                in_list = False
            paragraph.append(inline(line))
    flush_paragraph()
    flush_table()
    if in_list:
        body.append("</ul>")
    style = """
:root{color-scheme:light dark;font-family:system-ui,-apple-system,sans-serif}
body{max-width:76rem;margin:auto;padding:2rem;line-height:1.6}
main{max-width:100%}a{overflow-wrap:anywhere}
h1,h2,h3{line-height:1.25}li{margin:.4rem 0}
.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%}
th,td{border:1px solid #888;padding:.6rem;text-align:left;vertical-align:top}
blockquote{border-inline-start:4px solid #888;margin-inline:0;padding-inline:1rem}
@media print{body{padding:0}a{color:inherit}}
"""
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>" + html.escape(title) + "</title><style>" + style + "</style>"
        "</head><body><main>" + "\n".join(body) + "</main></body></html>\n"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render portable report HTML from Markdown")
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_html(args.markdown.read_text(encoding="utf-8"), title=args.markdown.stem.replace("-", " ")),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
