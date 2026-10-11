# Reviewed cross-source report composition (#63, #82)

`python -m trust_ecosystem_monitor.toip_combined_report --github local/2026-08.json --admitted-confluence local/2026-08-admitted.json --output local/reports`

This **offline** command composes previously collected GitHub monthly evidence with independently admitted Confluence page-update observations for the same period, producing JSON, Markdown and HTML. HTML is rendered as semantic headings and lists, with escaped text and clickable allowlisted HTTPS source/review links. The command does not fetch sources, review legal rights, authenticate reviewers, qualify raw Confluence records or publish a Pages site.

The admitted Confluence manifest must have `period`, `publication_admitted=true`, `coverage` (`partial` or `complete`), and `observations` already approved by the independent admission process. Every observation must carry `authorization_decision_id` and `independent_review_evidence_url`. Optional `reviewed_github_observations` must refer to GitHub URLs present in the supplied monthly evidence. Cross-source references remain curator-asserted, not proof of causation or governance decisions.

**Critical trust boundary:** This composer checks structural assertions, not signatures, authenticity or external review evidence. Do not manufacture admission manifests or set `publication_admitted=true` simply to run the tool. Independently validate the reviewer and source-use records, page/version and subject mapping before creating the admitted manifest. The raw acquisition bundle from `toip_confluence_collect` always has `publication_admitted=false` and is intentionally rejected here.

Negative tests cover missing admission, synthetic flag, period mismatch, out-of-month observations, missing independent-review provenance, unsupported mapping, missing coverage and HTML injection. A positive synthetic fixture exercises composition only; it does not establish a real report. Public Pages deployment and live August/September verification remain #63/#81.

The HTML renderer permits only github.com and lf-toip.atlassian.net source links, and rejects unsafe schemes, embedded credentials, ports and fragments. Review links must be from these same hosts under the current renderer policy; any other review-evidence host requires a separately reviewed allowlist policy and tests before public use.
