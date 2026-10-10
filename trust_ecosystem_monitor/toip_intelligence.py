"""Publish conservative, evidence-linked ToIP intelligence pages from monthly manifests."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

MONTHS = ("2026-08", "2026-09")
BASE = "https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor"


def safe_link(url: str, label: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password:
        return escape(label)
    return '<a rel="noopener noreferrer" href="' + escape(url, quote=True) + '">' + escape(label) + "</a>"


def shell(title: str, body: str, *, up: str = "../") -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + escape(title) + '</title><style>'
            'body{max-width:68rem;margin:2rem auto;padding:0 1rem;font:1rem/1.65 system-ui,sans-serif}'
            'nav a{margin-right:1rem}table{border-collapse:collapse;width:100%}'
            'td,th{padding:.6rem;border:1px solid #777;text-align:left;vertical-align:top}'
            'a{overflow-wrap:anywhere} .notice{border-left:4px solid #666;padding:0 1rem}'
            '</style></head><body><nav><a href="' + up + '">Intelligence</a>'
            '<a href="' + up + 'coverage/">Coverage</a><a href="' + up + 'methodology/">Methodology</a>'
            '<a href="' + up + '../../monthly/index.html">GitHub monthly reports</a></nav><main>'
            + body + '</main></body></html>\n')


def month_page(data: dict) -> str:
    month = data["period"]
    if month not in MONTHS:
        raise ValueError("Unexpected period")
    evidence = data.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("Invalid evidence")
    counts = Counter((e.get("kind"), e.get("event")) for e in evidence)
    repositories = {e["repository"] for e in evidence}
    opened = {(e["repository"], e["kind"], e["url"]) for e in evidence if e.get("event") == "opened"}
    merged = [e for e in evidence if e.get("kind") == "pull_requests" and e.get("event") == "merged"]
    both = [e for e in merged if (e["repository"], e["kind"], e["url"]) in opened]
    examples = "".join('<li>' + safe_link(e["url"], e["repository"] + " — " + e.get("title", "PR")) +
                       ': opening and merge both observed within the month. This supports a lifecycle transition, not adoption.</li>'
                       for e in both[:8])
    if not examples:
        examples = "<li>No same-month PR opening-and-merge pairs identified in the available evidence.</li>"
    rows = "".join("<tr><td>" + escape(kind + " / " + event) + "</td><td>" + str(count) + "</td></tr>"
                   for (kind, event), count in sorted(counts.items()) if kind and event)
    body = ('<h1>ToIP ecosystem intelligence — ' + escape(month) + '</h1>'
            '<p class="notice"><strong>Independent evidence-based preview.</strong> GitHub lifecycle observations only; '
            'Confluence source identity is verified but historical page activity is not yet admitted as report evidence. '
            'LFX Calendar/Zoom is pending. This is not an official ToIP governance or adoption report.</p>'
            '<h2>Observed activity</h2><p>' + str(len(evidence)) + ' GitHub lifecycle observations across ' +
            str(len(repositories)) + ' repositories represented in the observed events. '
            'Counts are not distinct deliverables or progress scores.</p>'
            '<table><caption>Observed GitHub lifecycle events</caption><thead><tr><th>Event</th><th>Count</th></tr></thead>'
            '<tbody>' + rows + '</tbody></table>'
            '<h2>Bounded evidence-based inference</h2><p>Same-month issue/PR lifecycle transitions can be '
            'established from linked GitHub records. They cannot establish specification adoption, governance approval, '
            'interoperability or implementation quality.</p><ul>' + examples + '</ul>'
            '<h2>Source coverage</h2><p>GitHub enumeration: <strong>' +
            ('complete for the configured repository selection' if data.get("coverage_complete") else 'partial or unavailable') +
            '</strong>. Scope: ' + escape(str(data.get("collection_scope", "not stated"))) + '.</p>'
            '<p>Confluence: public HOME space identity and bounded historical search metadata verified; '
            'authoritative scope, reuse rights and evidence classification pending. '
            'LFX: explicitly deferred, not zero activity.</p>'
            '<p><a href="../../../monthly/' + month + '-report.html">Underlying GitHub activity report</a> · '
            '<a href="../coverage/">Coverage details</a> · <a href="../methodology/">Inference rules</a></p>')
    return shell("ToIP intelligence " + month, body)


def publish(inputs: list[Path], output: Path) -> None:
    by_month = {}
    for path in inputs:
        data = json.loads(path.read_text(encoding="utf-8"))
        month = data.get("period")
        if month not in MONTHS or month in by_month:
            raise ValueError("Expected one manifest per supported month")
        by_month[month] = data
    if set(by_month) != set(MONTHS):
        raise ValueError("Both August and September manifests required")
    output.mkdir(parents=True, exist_ok=True)
    for month, data in by_month.items():
        folder = output / month
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(month_page(data), encoding="utf-8")
    home = ('<h1>ToIP ecosystem intelligence</h1><p>Independent source-aware monthly evidence and bounded inference. '
            'The current public release uses GitHub issue/PR lifecycle evidence; Confluence discovery is documented '
            'but its records are not yet admitted as historical activity. LFX Calendar/Zoom is deferred.</p>'
            '<h2>Reporting periods</h2><ul>' +
            "".join('<li><a href="' + m + '/">' + m + ' — observed activity and bounded inferences</a></li>' for m in MONTHS) +
            '</ul><p><a href="coverage/">Source coverage</a> · <a href="methodology/">Inference methodology</a></p>')
    (output / "index.html").write_text(shell("ToIP ecosystem intelligence", home, up="./"), encoding="utf-8")
    coverage = ('<h1>ToIP source coverage</h1><table><thead><tr><th>Source</th><th>Current publication status</th>'
                '<th>Limitation</th></tr></thead><tbody>'
                '<tr><td>GitHub</td><td>Observed issue and PR lifecycle events in configured repositories</td>'
                '<td>Does not cover all repositories, commits, decisions or historical state transitions</td></tr>'
                '<tr><td>Confluence</td><td>Technical source discovery only: HOME / 22970380; 22 August and '
                '36 September last-modified CQL matches resolved to HOME</td>'
                '<td>Scope and publication rights not established; page updates are not governance decisions; '
                'these 58 matches are not ingested into monthly activity</td></tr>'
                '<tr><td>LFX Calendar/Zoom</td><td>Pending / deferred</td>'
                '<td>No meeting activity or outcomes inferred</td></tr></tbody></table>'
                '<p>Confluence technical verification: <a href="' + BASE +
                '/actions/runs/38017349744">diagnostic run</a>. Source authorization and reconciliation: '
                '<a href="' + BASE + '/issues/63">issue #63</a>.</p>')
    (output / "coverage").mkdir(exist_ok=True)
    (output / "coverage/index.html").write_text(shell("ToIP coverage", coverage), encoding="utf-8")
    methodology = ('<h1>Evidence and inference methodology</h1>'
                   '<p><strong>Observation:</strong> a source-linked issue/PR lifecycle event with repository, timestamp, '
                   'event type and canonical GitHub URL.</p>'
                   '<p><strong>Bounded inference:</strong> a same-month opened-and-merged PR pair supports the statement '
                   'that a PR moved from opening to merge. It does not establish quality, adoption, approval, '
                   'implementation, interoperability or governance consequence.</p>'
                   '<p><strong>Not established:</strong> Confluence page modification cannot be classified as an '
                   'adopted decision; a calendar listing cannot establish a meeting was held. Missing sources must '
                   'not be treated as zero activity.</p>'
                   '<p>Publication is independent of ToIP. No automated LLM-generated or unreviewed semantic claims '
                   'are made. Source-specific scope, authorization and privacy gates must be satisfied before '
                   'external records are integrated.</p>')
    (output / "methodology").mkdir(exist_ok=True)
    (output / "methodology/index.html").write_text(shell("ToIP methodology", methodology), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    publish(args.manifests, args.output)


if __name__ == "__main__":
    main()
