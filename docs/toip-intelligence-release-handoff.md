# ToIP Ecosystem Intelligence — release handoff and acceptance

Tracking: [#63](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/63). LFX Calendar/Zoom is deferred from the first release.

## Implemented, independently of GitHub Pages availability

- Historical GitHub issue/PR monthly evidence, reports and comparison for August/September 2026.
- Independent `/intelligence/` and `/intelligence/toip/` pages, per-month pages, coverage and methodology.
- Bounded, source-linked GitHub PR lifecycle inferences; no implied governance adoption.
- Public Confluence technical discovery: HOME (22970380), 22 August and 36 September page-last-modified search matches resolved to HOME. These are **not** authorized historical activity records.
- Confluence JSON export adapter and source-aware monthly report infrastructure (not equivalent to verified historical Confluence acquisition).
- Local, fail-closed HTML publication readiness gate in the manual monthly Pages workflow.

## Required final operational verification

1. Dispatch **a fresh run** of `Historical ToIP monthly evidence prototype` on `main`. Do **not** rerun failed run 38018188455: its duplicate `github-pages` artifacts make same-run retries unsafe.
2. Confirm validation, historical collection, HTML rendering and **Verify local Pages publication readiness** all pass.
3. Confirm `actions/deploy-pages` completes and provides a deployment URL. An uploaded artifact is **not** a successful deployment.
4. Open the public site at `/intelligence/toip/`, `/intelligence/toip/2026-08/`, `/intelligence/toip/2026-09/`, `/intelligence/toip/coverage/` and `/intelligence/toip/methodology/`. Check navigation and linked monthly reports.
5. Record workflow ID, deployed commit SHA, accessible URLs, and timestamp in #63.

## Remaining #63 external evidence gates

These are **not** waived by successful Pages deployment:

- Establish authoritative Confluence scope/space allowlist and publication/reuse conditions. Public reachability is not permission to republish.
- Acquire bounded, authorized August/September Confluence records, normalize provenance and verify representative records.
- Produce combined GitHub + Confluence reports and at least one genuinely corroborated cross-source inference; fail closed when a source is absent or denied.
- Preserve privacy, deduplication, and distinction between a page edit, discussion, decision and deliverable.

If the source owner cannot confirm scope or rights, record an explicit blocked disposition and retain GitHub-only publication. Do not mark cross-source acceptance as passed.

## Closure decision

**The initial GitHub-only intelligence publication may be implementation-ready without being live-verified. Issue #63 cannot truthfully be marked complete while its Confluence acquisition and cross-source reporting acceptance criteria remain unmet.** A narrower replacement issue and a documented scope reduction are permissible, but do not silently claim that the original objective was delivered.
