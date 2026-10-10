"""Render an offline, explicitly non-public cross-source assurance preview.

Never infer authorization from a manifest field alone. Preview is restricted to
synthetic fixtures; production publication requires an independently approved
source inventory and a separate deployment integration.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

from .toip_evidence_contract import infer_correlations, validate_observations


def render_preview(manifest: dict) -> str:
    if manifest.get("schema_version") != "1" or manifest.get("fixture_only") is not True:
        raise ValueError("only explicit versioned synthetic fixtures accepted")
    if manifest.get("publication_mode") != "offline_test_only":
        raise ValueError("public publication forbidden")
    records = manifest.get("observations")
    if not isinstance(records, list):
        raise ValueError("observations array required")
    # The synthetic flag authorizes only local contract testing, not source use.
    validate_observations(records, approved_confluence=True)
    findings = infer_correlations(records, approved_confluence=True)
    items = []
    for finding in findings:
        links = []
        for url in finding["source_urls"]:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("unsafe source link")
            links.append('<li><a href="' + escape(url, quote=True) + '">' + escape(url) + "</a></li>")
        items.append("<li><strong>" + escape(finding["subject_id"]) + "</strong>: " +
                     escape(finding["statement"]) + "<ul>" + "".join(links) + "</ul><p>" +
                     escape(finding["limitations"]) + "</p></li>")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'
            'Synthetic ToIP cross-source preview — NOT FOR PUBLICATION</title></head><body>'
            '<h1>Synthetic ToIP cross-source preview — NOT FOR PUBLICATION</h1>'
            '<p>Offline test fixture. No real ToIP evidence, authorization or governance finding is asserted.</p>'
            '<ul>' + "".join(items) + '</ul></body></html>\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    output = render_preview(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
