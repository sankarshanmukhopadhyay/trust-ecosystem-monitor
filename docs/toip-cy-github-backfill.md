# ToIP CY GitHub-only backfill

This tranche expands the cumulative ToIP annual report from a two-month proof of structure toward a calendar-year GitHub-observed product without widening the source-authority claim.

## Scope

The backfill command and workflow collect bounded GitHub issue and pull-request lifecycle evidence for missing completed months and ingest those months into the annual state.

The default CY 2026 target is `2026-01` through `2026-09`, because October 2026 is still in progress.

## Boundary

This is deliberately GitHub-only backfill.

It does not:

- retrieve or summarize additional Confluence page bodies;
- admit Confluence-derived findings;
- use LFX Calendar, Zoom, meeting transcripts or recordings;
- infer ToIP decisions, approvals, meeting outcomes or official WG/TF authority;
- change #63, #80 or #82 acceptance status.

Backfilled months use empty Confluence source sets. The annual report can therefore show more monthly GitHub evidence while preserving the existing source-use and authority limitations.

## Operation

Manual workflow:

`Backfill ToIP CY GitHub-only intelligence`

Default inputs:

- `start_month`: `2026-01`
- `end_month`: `2026-09`
- `force`: `false`

`force=false` skips months already present in the annual manifest, preserving immutable first observations for August and September unless the operator deliberately requests reprocessing.

## Evidence retained

The workflow uploads a backfill artifact containing:

- `monthly-prototype/<month>.json`
- `monthly-prototype/<month>.md`
- `monthly-prototype/cy-backfill-summary.json`
- regenerated `docs/intelligence/toip/` output

The generated annual output remains the authoritative publication artifact for the reader-facing CY page.

## Issue synchronization

This advances #122 P2/C1 for GitHub-only CY coverage only. It does not close:

- #63 — Confluence source-use and publication-rights reconciliation;
- #80 — LFX/Zoom/meeting source authority;
- #82 — admitted cross-source findings;
- #81 — broader independent public-route smoke testing.
