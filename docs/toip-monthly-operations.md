# ToIP monthly scheduled operations

This guide covers the second bounded C2 operational tranche from #122 and #150.

## Scheduled month selection

The scheduled workflow resolves the target month through
`trust_ecosystem_monitor.monthly.previous_completed_month()`.

The function uses the UTC calendar boundary. A run at any point in October
targets September; a run at any point in January targets December of the prior
year. The workflow does not infer the target from local runner time.

## Collection budget

Scheduled GitHub collection passes `--max-pages 25`.

The collector records this bound in `collection_budget` and applies it to
repository discovery and each issue/PR endpoint. Reaching the pagination safety
limit is a visible incomplete-coverage condition rather than silent truncation.

This is a request-volume safety bound, not a completeness claim. Lowering the
bound may produce incomplete coverage and must remain visible in the collection
result.

## Current-source reinspection

Previously tracked Confluence pages are re-inspected by
`toip_tracked_sources.inspect()`. Reinspection is bounded by
`MAX_TRACKED = 80`.

Reinspection does not assign an old source to the newly collected month. It may
append a source-version or interpretation-change notice to the source ledger.
The immutable first monthly observation remains unchanged.

## Generated-observations promotion

All current workflow writers that promote validated `docs/` state to
`generated-observations`:

1. fetch the current generated branch;
2. record its commit as `parent`;
3. construct a new commit with exactly that parent;
4. push with an explicit
   `--force-with-lease=refs/heads/generated-observations:$parent`.

The lease is a compare-and-swap guard. If another writer updates the branch
after the fetch, promotion fails rather than replacing that newer state.

GitHub Actions also uses the shared `pages` concurrency group with
`cancel-in-progress: false`. The lease is still required because it protects
against writers outside that workflow concurrency queue.

## Retention

Transient GitHub Actions evidence/site bundles are retained for 30 days.
Durable annual observations and append-only revision/source ledger state remain
in the generated publication state and are governed by the annual manifest
semantics rather than transient artifact retention.

No source body retention or source-admission policy is expanded by this
operational tranche.

## Retry and restart procedure

When a scheduled run fails:

1. Inspect whether failure occurred during collection, validation or promotion.
2. If collection hit a pagination/request bound, treat coverage as incomplete;
   do not manually relabel it complete.
3. If promotion failed because the lease was stale, restart the workflow so it
   restores the latest `generated-observations` parent before regenerating.
4. A same-month retry must preserve the first observation. If newly collected
   evidence differs, the annual state records a `month_reobservation` notice
   rather than overwriting the original snapshot.
5. Do not force-push `generated-observations` manually to bypass the lease.

## Boundary

This work does not change Confluence/LFX/Zoom admission, WG/TF authority,
cross-source finding semantics or reader-facing intelligence claims.
