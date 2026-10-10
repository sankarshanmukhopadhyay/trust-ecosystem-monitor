# ToIP public Confluence discovery: bounded acquisition evidence

This document records the scope of the read-only public diagnostic added under issue #63.
It does **not** certify the completeness of ToIP historical evidence.

## Verified on GitHub Actions (2026-10-10)

- Confluence public page listing returned 75 metadata records in three bounded batches, with more pages indicated.
- Unscoped Confluence CQL searches for page `lastmodified` in August and September 2026 reported 22 and 36 matches, respectively. The bounded pagination diagnostic retrieved all 22 and 36 result entries in its observed run.
- The public CQL API emits a context-relative `/rest/api/search` next-page link. The collector normalizes that **specific** path to the same-host `/wiki/rest/api/search` endpoint. Arbitrary hosts and paths are rejected.
- The HTTP checks for public LFX and Confluence endpoints succeeded. This does **not** establish authenticated access, historical meeting coverage or authorization to republish content.

Verification: workflow runs [38013735555](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/runs/38013735555) and [38013741720](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/runs/38013741720).

## Evidence boundaries

1. CQL results are page **last-modified** matches, not a change-event history, minutes, meeting records, approved decisions or project deliverables.
2. Queries are **not restricted to an independently verified ToIP space allowlist**. No assertion is made that every returned page is ToIP-relevant.
3. A count equal to the API's reported total is evidence that the bounded query returned that many entries at retrieval time; it is **not** proof of authoritative completeness, absence of inaccessible pages, historical correctness or pagination consistency.
4. No page bodies, comments, author profiles, meeting contents or secrets are collected by these diagnostics. The CQL collector emits counts and coverage status, not titles or search-result records.
5. Source status remains `sample_only` even where pagination terminates. No external source is currently promoted into combined historical reports.
6. The workflow is a manual diagnostic. Artifacts are retained for seven days and should not be treated as durable archival evidence.

## Next bounded implementation

- Verify the authoritative ToIP Confluence space IDs and LFX group/calendar scope, including publication rights.
- Add source-scoped historical acquisition with stable IDs, canonical links, timestamp and provenance validation; distinguish page updates from decisions.
- Build LFX meeting evidence with separate classifications for listed, held, minutes available and decision recorded.
- Integrate authorized evidence into the August/September reports with source-aware coverage and privacy controls.
- Keep issue #63 open until its remaining acceptance criteria are satisfied; do not close it on the strength of reachability or CQL counts alone.

## Space-scope observation (subsequent increment)

The historical CQL diagnostic now emits **observed public space keys** and
a count of entries with no usable space key. The manual diagnostic workflow
prints these aggregates for August and September, without page titles,
bodies, author profiles or identifiers.

Observed keys are **candidates for scope reconciliation**, not an authoritative
ToIP allowlist. The query remains unscoped, and `scope_verified=false` even
when all pages returned by the bounded query are enumerated. A source owner
must confirm which spaces and groups belong in the reporting inventory and
what reuse rights apply before records can enter public historical reports.
