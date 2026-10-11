# Cumulative ToIP calendar-year intelligence (CY 2026)

## Product contract

TEM publishes one canonical year-to-date report at `/intelligence/toip/2026/`, regenerated from **retained machine-readable monthly observations**, rather than HTML append operations. Source-ledger storage resides at `docs/intelligence/toip/2026/data/manifest.json` in the existing `generated-observations` branch. A monthly run adds one immutable first-seen observation for its month and appends new source versions or reconciliation notices. Every annual publication is derived from retained evidence state.

### Retained evidence records

- `months[YYYY-MM]`: immutable initial GitHub lifecycle and Confluence public-source observations, first observation timestamp, reporting month, temporal limitation, and canonical JSON SHA-256 digest.
- `source_ledger[confluence_page_id]`: sequence of observed page versions and evidence fingerprints, observed month and timestamp, bounded derived content descriptions and original source URLs. Page bodies are **not** stored; hashes cannot reconstruct them.
- `revision_notices[]`: dated, explainable source-version or re-observation notices preserving prior digests and links. Changes are **review required**; they do not automatically prove that the original finding was wrong, or that a decision has been superseded.

### Temporal integrity

The Confluence CQL query identifies pages last modified in a reporting month, but the public v2 endpoint provides the *currently available page version*. This implementation cannot reconstruct the text as it existed at month end. First observations are marked `retrospective-current-public-source` explicitly. Tracked pages are re-inspected independently on subsequent runs, even if they are absent from the latest month's CQL results. Re-inspection is not counted as an event in the latest month.

The monthly source re-inspection is bounded to 80 known page IDs; if the tracked source population grows beyond this threshold, the run fails closed rather than claiming total monitoring. Unavailable or inaccessible pages do not prove deletion or correction. The current month extraction remains capped at 40 pages; it is sample-only and must not be described as complete.

### Current year report and monthly chronicle

The annual page has a year-to-date overview, GitHub evidence, Confluence source descriptions, changes to tracked sources and expandable monthly chronicle. The source reference links and original evidence timestamps remain available through retained JSON. Priority is always review attention, not risk-severity or validated organizational decisions. The report remains experimental pending substantive editorial review and Confluence source-use clearance.

### Operation and replay

The scheduled workflow `.github/workflows/monthly-intelligence.yml` runs at 02:40 UTC on day 2 of each month, collects the **previous completed UTC month**, restores the state branch, runs `python -m trust_ecosystem_monitor.toip_annual --month "$MONTH" --github-dir monthly-prototype --site docs/intelligence/toip`, validates site readiness, persists docs and deploys Pages. The legacy August–September historical workflow remains manually dispatched and can seed CY 2026 after the merge; it ingests August followed by September. Repeated runs of the same month do not overwrite its original observation. Differences create review notices.

For deterministic local tests: `python -m unittest discover -s tests`. Fixtures exercise replay, source version advance, unchanged reinspection, source loss, corrupt manifests, chronological cross-month comparisons and single-link annual navigation. Publication verification requires a real workflow artifact review and a public HTTP check.

### Acceptance status

- [x] Immutable monthly source observation manifests.
- [x] Page-specific version/fingerprint ledger.
- [x] Append-only change notices that do not rewrite historical evidence.
- [x] Bounded revisiting of tracked sources independently of current-month search.
- [x] Cumulative annual rendering and monthly sections.
- [x] Scheduled workflow integration with existing manual historical backfill.
- [ ] Independently observed Pages deployment after this merge.
- [ ] Complete substantive natural-language synthesis of Confluence deliberation, with historical source rights/authorization verified.
- [ ] Full CY 2026 backfill; January–July and October are not present merely because annual rendering is enabled.

Source coverage and the remaining editorial limits are integral to the report, not optional footnotes.
