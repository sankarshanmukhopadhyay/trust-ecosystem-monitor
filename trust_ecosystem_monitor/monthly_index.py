"""Build a discoverable, explicitly partial monthly HTML preview index."""
from __future__ import annotations

import argparse
import html
from datetime import datetime, timezone
from pathlib import Path

REPORTS = (
    ("August 2026 — activity", "2026-08-report.html"),
    ("August 2026 — portfolio overview", "2026-08-overview.html"),
    ("September 2026 — activity", "2026-09-report.html"),
    ("September 2026 — portfolio overview", "2026-09-overview.html"),
    ("August–September 2026 comparison", "2026-08-to-2026-09.html"),
)


def render_index(generated_at: str) -> str:
    links = "\n".join(
        f'<li><a href="{html.escape(path, quote=True)}">{html.escape(label)}</a></li>'
        for label, path in REPORTS
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ToIP monthly evidence previews</title>
<style>body{{max-width:54rem;margin:2rem auto;padding:0 1rem;font:1rem/1.6 system-ui,sans-serif;color:#182334}}a{{color:#075985}}.notice{{border-left:4px solid #64748b;padding:.6rem 1rem;background:#f1f5f9}}</style>
</head><body><nav><a href="../index.html">Ecosystem monitor</a> · <a href="../trustoverip/reports/latest.html">ToIP weekly report</a></nav>
<h1>TrustOverIP historical monthly evidence previews</h1>
<p>Generated {html.escape(generated_at)} UTC.</p>
<section class="notice" aria-label="Evidence coverage"><h2>Coverage and interpretation</h2>
<p><strong>GitHub-only partial evidence.</strong> LFX meeting and Confluence records have not been incorporated.
The reports describe observed repository lifecycle events, not confirmed meetings, decisions, governance outcomes or organizational completeness.
Missing source evidence must not be interpreted as zero activity. These are independent experimental previews, not ToIP-authoritative reports.</p></section>
<h2>HTML reports</h2><ul>{links}</ul>
<p>Source acquisition remains tracked in <a href="https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/63">issue #63</a>.
Publication depends on a successful evidence collection; failed GitHub quota-limited runs must not overwrite valid reports.</p>
</body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--link-home", type=Path)
    args = parser.parse_args()
    if bool(args.output) == bool(args.link_home):
        parser.error("choose exactly one of --output or --link-home")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_index(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")), encoding="utf-8")
    else:
        if not args.link_home.is_file():
            raise FileNotFoundError(args.link_home)
        source = args.link_home.read_text(encoding="utf-8")
        link = '<p><a href="monthly/index.html">Historical ToIP monthly HTML previews (GitHub-only partial evidence)</a></p>'
        if 'href="monthly/index.html"' not in source:
            if "</main>" not in source:
                raise ValueError("homepage has no main section")
            source = source.replace("</main>", link + "</main>", 1)
            args.link_home.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
