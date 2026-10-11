# ToIP Confluence acquisition readiness (#63)

## Current status

A bounded, read-only, offline-tested **metadata** acquisition primitive exists; it is not an automatically scheduled or publication-admitted collector. The current project sponsor authorization is documented in [the experimental authorization decision](toip-confluence-experimental-authorization.md). A separate ToIP source-owner approval is **not** a project prerequisite, but source-use compliance and independent evidence qualification still are.

The initial candidate scope is public `lf-toip.atlassian.net` space `HOME` (`22970380`), August and September 2026. It is not a verified complete ToIP source inventory. Public last-modified matches (22/36) do not establish full history.

The collector requires `scope_approved=True`, `reuse_approved=True`, and a bounded numeric space-ID allowlist. These are caller assertions, **not** evidence that third-party rights exist. A live operator must record the sponsor decision and separately review applicable source terms, licensing, privacy and permissible metadata reuse before asserting them. Do not treat the source's public availability as blanket republication rights.

The primitive performs bounded GET requests to the expected host, constrains pagination, validates stable page IDs and space identity, limits response size and lookups, and reports incomplete coverage. It does not fetch page bodies, titles, attachments or attendee data. Metadata remains `page_update` / `metadata_only`, not a governance decision. Collection does not automatically admit records to reports.

## Production-readiness checklist

- [ ] Record dated source-use compliance review, permitted metadata fields, exclusions and retention; do not assert compliance solely from sponsor authorization.
- [ ] Verify live CQL response and pagination semantics, source IDs, page versions and historical date windows against real endpoint responses.
- [ ] Run bounded August/September retrieval with retrieval timestamps, safe URLs, duplicate detection, terminal-page diagnostics and explicit partial coverage.
- [ ] Independently verify representative links and subject mapping; quarantine denied, missing or unreviewed records.
- [ ] Add end-to-end negative tests for missing/denied/partial source, malformed payloads, duplicates, unsupported inference and unsafe publication.
- [ ] Wire **admitted** records to reproducible JSON/Markdown/HTML reporting without exposing restricted data, secrets or source payloads.
- [ ] Complete Pages verification (#81) and operational quota acceptance (#65).

Unit tests exercise denied approval, out-of-scope records, unsafe or backward pagination, pagination cycles, oversized pages and failed lookups. These are structural controls, **not** evidence of live historical acquisition or rights verification. Cross-source findings remain #82; LFX is deferred (#80).
