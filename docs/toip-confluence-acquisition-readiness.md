# Confluence metadata acquisition readiness (#63)

This is an **offline-tested, authorization-gated** acquisition primitive, not a scheduled collector or a declaration of approved ToIP Confluence scope. It does not run in the Pages workflow and cannot publish records automatically.

The caller must supply both `scope_approved=True` and `reuse_approved=True`, plus an approved numeric space-ID set, after documenting a dated source-owner decision. Neither flag is presently justified by the public `HOME` discovery alone. The implementation issues only bounded GET requests to the verified ToIP Confluence host, with a finite page budget, bounded response size, timeout, constrained pagination, stable page IDs and v2 space identity checks.

The result intentionally reports `coverage=partial`, `historical_completeness_verified=false`, and `publication_admitted=false`. Page bodies, titles, attachments and attendee data are not collected. Page metadata is classified `metadata_only`, never as an adopted decision.

Tests exercise denied approval, metadata minimization, out-of-scope exclusion, unsafe pagination, pagination cycles and failed metadata lookups.

## Before use against live sources

- Obtain and record source-owner scope and reuse decisions, including permissible retention, public summary fields and historical period.
- Verify Confluence CQL query and response pagination semantics against the live endpoint; do not assume fixture success implies real API interoperability.
- Add independent retrieval timestamps, digests and complete enumeration proof before claiming full coverage.
- Review privacy, source links and content licensing before connecting the adapter to the report generator.
- Do not use these metadata records to satisfy #82 cross-source inference acceptance without independent subject-reference evidence.

LFX is deferred under #80. GitHub Pages verification remains #81.
