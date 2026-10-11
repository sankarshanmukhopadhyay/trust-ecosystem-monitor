"""Compose reviewed GitHub and Confluence observations into a report."""

from .toip_evidence_contract import validate_observations, infer_correlations
from .monthly import month_bounds, in_month
from html import escape
import json
import argparse
from pathlib import Path


def compose(github, confluence):
    if github.get("period") != confluence.get("period"):
        raise ValueError("period mismatch")
    if confluence.get("publication_admitted") is not True:
        raise ValueError("Confluence records are not admitted")
    if confluence.get("fixture_only") is True:
        raise ValueError("synthetic fixture cannot be used for publication")
    if confluence.get("coverage") not in ("partial", "complete"):
        raise ValueError("source coverage disclosure required")
    bounds = month_bounds(github["period"])
    records = validate_observations(confluence.get("observations"), approved_confluence=True)
    if any(item["source"] != "confluence" or item["kind"] != "page_update" for item in records):
        raise ValueError("only Confluence page updates supported")
    if any(not in_month(item["occurred_at"], bounds) for item in records):
        raise ValueError("Confluence record outside month")
    if any(not item.get("authorization_decision_id") or not item.get("independent_review_evidence_url") for item in records):
        raise ValueError("independent admission provenance required")
    github_events = github.get("evidence")
    if not isinstance(github_events, list):
        raise ValueError("GitHub evidence required")
    if any(not isinstance(event, dict) or not in_month(event.get("occurred_at"), bounds) for event in github_events):
        raise ValueError("GitHub event outside month")
    mapped = confluence.get("reviewed_github_observations", [])
    if not isinstance(mapped, list):
        raise ValueError("reviewed mappings must be an array")
    observed_urls = {event.get("url") for event in github_events}
    if any(item.get("source") != "github" or item.get("url") not in observed_urls for item in mapped):
        raise ValueError("reviewed GitHub mapping is not collected")
    return {
        "period": github["period"],
        "github_events": github_events,
        "confluence_observations": records,
        "findings": infer_correlations(mapped + records, approved_confluence=True),
        "coverage": {
            "github_complete": github.get("coverage_complete") is True,
            "confluence": confluence.get("coverage", "partial"),
        },
        "limitations": "Independent experimental evidence; page updates are not decisions.",
    }

def markdown(report):
    lines = [
        "# ToIP cross-source evidence — " + report["period"],
        "",
        "Independent experiment, not an official ToIP determination.",
        "",
        "## Coverage",
        "",
        "- GitHub complete for enumerated repositories: " + str(report["coverage"]["github_complete"]),
        "- Confluence: " + report["coverage"]["confluence"],
        "",
        "## GitHub activity",
        "",
    ]
    for event in report["github_events"]:
        lines.append("- " + event["occurred_at"][:10] + ": " + event["title"] + " (" + event["url"] + ")")
    lines.extend(["", "## Admitted Confluence page updates", ""])
    for item in report["confluence_observations"]:
        lines.append("- " + item["occurred_at"][:10] + ": " + item["summary"] + " (" + item["url"] + ")")
    lines.extend(["", "## Reviewed cross-source references", ""])
    for item in report["findings"]:
        lines.append("- " + item["subject_id"] + ": " + item["statement"])
    if not report["findings"]:
        lines.append("No independently supported cross-source relationship established.")
    lines.extend(["", "## Limitations", "", report["limitations"], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--github", type=Path, required=True)
    parser.add_argument("--admitted-confluence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compose(json.loads(args.github.read_text()), json.loads(args.admitted_confluence.read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    name = report["period"]
    (args.output / (name + ".json")).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    md = markdown(report)
    (args.output / (name + ".md")).write_text(md)
    (args.output / (name + ".html")).write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>ToIP cross-source evidence</title></head><body><main><pre>'
        + escape(md, quote=True) + '</pre></main></body></html>\n')


if __name__ == "__main__":
    main()
