# ToIP cross-source evidence contract (v0.1)

**Tracking:** #63 (source use, acquisition, reports), #82 (correlation and inference), #81 (Pages), #65 (GitHub quota).

## Governance and source admission

The project sponsor `sankarshanmukhopadhyay` authorizes the bounded ToIP experiment under [the 2026-10-11 decision](toip-confluence-experimental-authorization.md). Separate ToIP organizational approval is not a project acceptance requirement. **This does not grant third-party reuse rights or establish official ToIP endorsement.** Applicable access/reuse conditions must be reviewed independently and recorded before asserting approval.

The existing `toip_evidence_contract` validates observations and conservative correlations offline. The `toip_confluence_admission` module adds structural authorization and independent review bindings. They do **not** fetch external review evidence, authenticate a declarant, certify source rights or perform production collection.

## Required evidence properties

1. **Source and scope:** A numeric approved Confluence space ID and bounded reporting period; candidate `HOME` ID `22970380` is not a complete inventory. Historical 22/36 last-modified matches are diagnostic search results, not admitted observations.
2. **Authorization:** `approved_confluence=True` and record `publication_approved=True` must be consequences of a dated sponsor decision **plus** independently reviewed applicable source-use compliance and qualified record evidence. They are not switches to bypass admission. Sponsor policy `toip_experiment_2026_10_11` requires a review-evidence URL.
3. **Provenance:** Stable source ID, canonical HTTPS URL, timezone-aware occurrence time, retrieval provenance, page version, record kind, summary, subject ID and reviewable subject-evidence URL. Duplicates must not inflate counts.
4. **Semantics:** `page_update` means page activity only. A modification, meeting listing or contemporaneous GitHub PR does not establish a governance decision, adoption or causal implementation.
5. **Correlation:** Require both GitHub and independently admitted Confluence records with the same curator-reviewed subject, supported by a verifiable link on each side. Similar names, timestamps or shared groups alone are insufficient.
6. **Publication:** Preserve per-source coverage, unavailable/partial states, exclusions and uncertainty. Escape HTML; never include raw page bodies, secrets or restricted material by default.

## Negative tests and assurance limitations

Current component tests cover invalid authorization/revocation, wrong source or period, missing review, mismatched page/version/subject, duplicate/unsafe references, absent Confluence, unsupported decisions and offline-renderer publication-mode rejection. These prove **structural rejection**, not the authenticity of human review assertions or the accuracy of live source content.

## Work outstanding before a public combined report

- [ ] Independently document source-use conditions and approved metadata fields; complete real August/September bounded acquisition with version and coverage evidence.
- [ ] Curate and independently verify representative source URLs and subject mappings; admit only reviewed records.
- [ ] Integrate admitted observations into reproducible source-aware JSON/Markdown/HTML with coverage appendix.
- [ ] Test real/sanitized end-to-end positive and negative cases, publication safety and GitHub-only regression.
- [ ] Verify public Pages routes and source links (#81). LFX is deferred (#80).

The synthetic-only HTML preview is **NOT FOR PUBLICATION**. No genuine cross-source finding has yet been verified or published.
