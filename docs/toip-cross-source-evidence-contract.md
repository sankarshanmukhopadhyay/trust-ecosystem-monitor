# ToIP Confluence and cross-source evidence contract (v0.1)

Tracking: [#63](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/63), [#82](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/82).

## Admission gates

The `toip_evidence_contract` module provides an offline validation and bounded correlation primitive. It does **not** fetch Confluence content, confer publication permission, assert ToIP authority or modify existing GitHub-only publication.

1. **Source inventory:** the public `HOME` space identity is verified, but authoritative ToIP coverage and permitted reuse are not. Keep `scope_verified=false`; 22/36 last-modified search hits are metadata matches, not admitted observations.
2. **Explicit approval:** a calling workflow must supply `approved_confluence=True` only after a dated, evidenced source-scope/reuse decision. Each Confluence record separately requires `publication_approved=True`. Do not set these flags to force tests or bypass owner review.
3. **Provenance:** every observation needs source, stable source ID, canonical HTTPS URL, timezone-aware occurrence time, kind, summary and an explicit curator-verified subject ID. Duplicates are rejected.
4. **Semantic restraint:** `page_update` is distinct from `decision`. Decisions require explicit decision evidence; no page revision or meeting listing is promoted to approval or adoption.
5. **Inference:** a cross-source reference requires **both** GitHub and approved Confluence records with the same curated subject ID. Temporal proximity, similar words, and shared repository/group alone are insufficient. The result does not claim causal sequence or governance approval.
6. **Privacy:** this primitive does not store raw source bodies or credentials. Downstream renderers must separately HTML-escape user-provided summaries, enforce publication allowlists, and preserve source coverage.

## Work remaining before public cross-source findings

- Confirm authoritative ToIP Confluence source scope and permitted metadata/record reuse, with a dated decision register (#63).
- Build and verify bounded authorized Confluence acquisition, version provenance, completeness states and privacy filtering (#63).
- Bind validated records to a reviewable curator subject-mapping file; extend the contract to require evidence of the subject relationship, not only its asserted ID (#82).
- Integrate approved findings into monthly Markdown/HTML with reproducibility, representative link checks, and negative fixtures (#82).
- Confirm the public Pages deployment independently (#81). LFX remains deferred (#80).

**Current release:** GitHub-only bounded inference is implemented; cross-source publication is blocked until these gates are satisfied.

## Reviewable subject mapping requirement (next increment)

A common `subject_id` alone is insufficient for a public cross-source finding. Both source records must now provide an HTTPS `subject_evidence_url` for review. If either reference is absent or unsafe, inference is suppressed, not guessed. This is an additional mechanical gate, **not independent proof that the linked records refer to the same subject**. Human verification and the source-owner rights decision remain mandatory before publication. Existing GitHub-only pages are unchanged.
