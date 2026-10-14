# ToIP monthly replay, idempotence and revision notices

This note defines the safe replay behavior for ToIP monthly intelligence publication. It implements the first bounded C2 tranche from #122 and is tracked by #140.

## Scope

This guidance applies to reruns of the ToIP monthly and annual publication path that write or re-render annual state from previously collected monthly GitHub evidence and bounded Confluence-derived content signals.

It does not expand the source model. Replay must not introduce new Confluence admission, LFX, Zoom, meeting-transcript or cross-source authority claims.

## Expected replay behavior

### Same-month rerun

Rerunning a completed month must be idempotent when the collected observation is identical.

Expected behavior:

- the first monthly observation remains unchanged;
- the observation digest remains unchanged;
- no duplicate month record is created;
- no duplicate source-ledger entry is created for the same source version and content fingerprint;
- no revision notice is emitted for an identical replay.

### Same-month changed reobservation

If a rerun of the same month produces a different observation, the first monthly observation must not be silently overwritten.

Expected behavior:

- the first monthly observation remains immutable;
- the changed observation is represented through a `month_reobservation` revision notice;
- source-version or extraction-method changes are represented through source-ledger entries and revision notices where applicable;
- the impact remains `review_required` until reviewed.

### Later-month source reinspection

A later monthly run may re-inspect pages that were observed earlier. Reinspection must not recast the earlier source into the later month as new monthly activity unless the source is actually part of the later month observation.

Expected behavior:

- previously tracked pages can update the source ledger;
- the later month does not count those pages as newly observed monthly Confluence sources unless they are part of the new month content collection;
- revision notices explain the source-version or extraction-method change;
- first observations remain intact.

## Operator procedure

### Before replay

1. Identify the month being replayed.
2. Confirm whether the replay is an identical rerun, an exact-month recovery, or a current-source reinspection.
3. Confirm that the run remains inside the GitHub-only / bounded-source policy for the relevant workflow.
4. Avoid direct writes to `main`; all implementation changes must go through protected-branch PR flow.

### During replay

1. Use the existing monthly publication workflow or bounded backfill workflow.
2. For CY backfill recovery, prefer exact-month mode when a single month must be rerun.
3. Preserve generated-observations promotion semantics.
4. Do not treat a successful HTTP fetch, CI success or rendered page as source-owner authorization.

### After replay

1. Inspect the annual manifest for the replayed month.
2. Confirm that unchanged months were not duplicated.
3. Confirm that changed observations produced revision notices rather than silent overwrite.
4. Confirm that rendered annual pages still avoid false full-year completeness, official ToIP authority, meeting, Confluence, LFX, Zoom or cross-source claims.
5. Record the workflow run, commit SHA and any revision-notice impact in the relevant issue.

## Current test coverage

The repository currently exercises these invariants in `tests/test_toip_annual.py`:

- same-month idempotent replay does not rewrite the immutable monthly record;
- later source-version changes preserve the old record and append revision notices;
- tracked reinspection is not counted as new month activity;
- same-month changed reobservation records review-required notices without overwriting the original observation;
- publish replay keeps a single annual index link and records tracked source changes.

## Boundary statement

Replay/idempotence hardening is operational assurance work. It does not establish official ToIP endorsement, normative decision authority, complete source coverage, source-owner publication rights, LFX/Zoom/meeting authority or admitted cross-source findings.
