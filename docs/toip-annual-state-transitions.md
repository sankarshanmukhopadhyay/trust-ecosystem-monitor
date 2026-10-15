# ToIP annual-state schema transitions

The durable annual manifest currently uses the published machine-ingestion
identifier `tem-cy-intelligence-v1`.

Repository history does not establish a published predecessor schema. TEM
therefore does not invent a synthetic v0→v1 migration merely to exercise a
migration mechanism.

## Runtime policy

All persisted annual state is read through
`toip_annual_state.migrate_to_current()`.

The transition rules are:

1. current `tem-cy-intelligence-v1` state validates and passes through;
2. missing schema identifiers fail closed;
3. unknown or future schema identifiers fail closed with
   `MigrationRequiredError`;
4. a future transition must be explicitly registered by source schema;
5. each transition must advance the schema identifier;
6. migration cycles fail closed;
7. a migration may not silently alter or remove an existing month's immutable
   first `observation` or `observation_digest`.

The public v1 data contract is not changed by this framework.

## Compatibility check

Operators can inspect a persisted manifest without mutating it:

```bash
python -m trust_ecosystem_monitor.toip_state_compatibility \
  --manifest docs/intelligence/toip/2026/data/manifest.json
```

Exit status is zero for a current compatible manifest and non-zero when an
explicit migration is required.

## Adding a future migration

A future schema change should be handled as a reviewed, testable work item.

The change should:

1. define the new public/runtime schema and compatibility rationale;
2. implement a pure migration callable from the previous schema;
3. register that callable explicitly when reading the predecessor state;
4. prove that immutable first observations and their digests are unchanged;
5. test repeated migration/replay behavior;
6. update the machine-ingestion schema and documentation when the public
   contract itself changes;
7. run publication readiness and public-route verification before promotion.

A migration must not be used to reinterpret historical evidence or to rewrite
first observations. New interpretation belongs in append-only revision notices
or a separately versioned derived surface.

## C2 completion boundary

With replay/idempotence, bounded collection/reinspection, lease-guarded
promotion and explicit state-transition handling implemented, the remaining C2
evidence is operational rather than architectural: a real post-hardening
scheduled monthly run must succeed from `main` and publish without violating
the existing completeness/authority boundaries.
