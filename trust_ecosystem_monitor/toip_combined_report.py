"""Compose reviewed GitHub and Confluence observations into a report."""

from .toip_evidence_contract import validate_observations, infer_correlations


def compose(github, confluence):
    if github.get("period") != confluence.get("period"):
        raise ValueError("period mismatch")
    if confluence.get("publication_admitted") is not True:
        raise ValueError("Confluence records are not admitted")
    records = validate_observations(confluence.get("observations"), approved_confluence=True)
    if any(item["source"] != "confluence" or item["kind"] != "page_update" for item in records):
        raise ValueError("only Confluence page updates supported")
    github_events = github.get("evidence")
    if not isinstance(github_events, list):
        raise ValueError("GitHub evidence required")
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
