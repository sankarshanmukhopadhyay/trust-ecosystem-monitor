# External source acquisition plan for monthly ToIP reporting

Tracking: #61 and PR #62. This plan distinguishes a functioning GitHub-only historical report from an authoritative cross-source ToIP report.

## Objective and boundaries

Provide read-only, reproducible LFX and Confluence acquisition without implying that a scheduled meeting proves a decision or that an edited page proves adoption. The existing authorized JSON importers are a fallback, **not** evidence that live endpoints have been integrated.

## Gate A — discover and establish authority

- [ ] Identify authoritative ToIP LFX service/project, meeting endpoints, accessible records and retention limits.
- [ ] Identify authoritative Confluence base URL, spaces and page/version APIs.
- [ ] Document whether each endpoint is public, requires a token, or requires administrator consent. Do not assume generic API credentials confer authorization to publish content.
- [ ] Define group-to-source mappings and minimum historical window for August and September 2026.
- [ ] Record rate limits, pagination, stable record IDs, timezones, modification semantics, and licensing/access constraints.

**Exit evidence:** real source URLs and access decision; documented source inventory. If authorization is missing, mark source `not_authorized` and retain the export path.

## Gate B — implement bounded read-only clients

- [ ] Introduce explicit source adapter interfaces and versioned normalized records.
- [ ] Implement authenticated GET-only acquisition with retry/backoff for 429/5xx, bounded pagination, timeout, and incremental cursor/window.
- [ ] Keep credentials in runtime secrets; never print them, persist them in artifacts, or put them in issue comments.
- [ ] Store retrieval timestamps, source IDs, canonical URLs, page versions or meeting IDs, and raw-response digests.
- [ ] Make adapters idempotent; avoid silent truncation and duplicate counting.
- [ ] Unit-test pagination, authorization errors, missing timestamps, malformed records, and partial failure.

**Exit evidence:** testable real-source retrieval with no mutation and source-specific incomplete coverage on failures.

## Gate C — classify and assure evidence

- [ ] Distinguish meeting scheduled/held from discussion, decision, action, and deliverable.
- [ ] Distinguish Confluence page modification from adopted decisions and published specifications.
- [ ] Cite specific source records and, where appropriate, stable page versions.
- [ ] Prevent source duplicates and GitHub/Confluence references to the same deliverable from becoming two deliverables.
- [ ] Expose explicit states: complete, partial, unavailable, not_authorized, not_found, not_checked. `complete` requires demonstrated source enumeration for the stated scope and time window.
- [ ] Ensure private source content cannot enter public HTML or Markdown artifacts by default.

**Exit evidence:** provenance checks and privacy review; no unsupported outcome claims.

## Gate D — deploy and reconcile August/September reports

- [ ] Run both adapters for August and September 2026, with an authorized export fallback when required.
- [ ] Compare source coverage against the agreed ToIP group inventory; document excluded groups.
- [ ] Produce source-aware monthly Markdown and HTML, comparison, and a separate coverage/provenance appendix.
- [ ] Independently spot-check a sample of source links and classified decisions.
- [ ] Confirm report generation works with one or both external sources absent.

**Exit evidence:** reproducible source-linked reports and an explicit residual limitations register.

## Sequencing and ownership of decisions

GitHub-only reporting can be merged once its own CI and evidence acceptance checks pass. Live source adapters should be tracked in a distinct bounded follow-up issue/PR rather than forcing an unrelated access dependency into the existing PR. The only intervention needed is when authoritative service discovery or access approval cannot be established through public sources. No credentials should be requested in issue comments or this chat.

## Source status at plan creation

- GitHub: working historical issue/PR lifecycle acquisition across configured repository prefixes.
- LFX: authorized local JSON importer; live API not verified.
- Confluence: authorized local JSON importer; live API not verified.
- Cross-source classification: conservative normalization, not yet verified against real LFX or Confluence data.
