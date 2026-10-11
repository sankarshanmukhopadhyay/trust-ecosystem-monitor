# ToIP Confluence source-use review dossier — pending independent determination

**Status:** NOT CLEARED. Prepared 2026-10-11 for issue #63. This is a review packet, not a legal opinion, authorization record, or assertion that source-use compliance has been independently verified.

## Proposed bounded source and use

- Source: `https://lf-toip.atlassian.net`, candidate Confluence `HOME` space ID `22970380`.
- Periods: August and September 2026, based on *last-modified* search, not complete historical version reconstruction.
- Fields: numeric page ID, space ID, canonical page URL, version number, retrieved timestamp, limited change timestamp where verifiable, and retrieval diagnostics.
- Output: original analytical summary, source citation and coverage/uncertainty; no page title/body, author profile, attachment, comment, meeting roster, access token or nonpublic content.
- Purpose: independent ToIP activity research. No ToIP endorsement, organizational approval or decision is inferred.
- Sponsor project authorization: `docs/toip-confluence-experimental-authorization.md`. This is **not** a grant of rights from Confluence content owners.

## Relevant external platform documentation (not a determination)

1. Atlassian: [Control whether spaces can allow public links](https://support.atlassian.com/confluence-cloud/docs/set-up-and-manage-public-links/). Allowing links at site/space level does **not** make every page public. Content-level public links are off by default.
2. Atlassian: [How secure are public links?](https://support.atlassian.com/confluence-cloud/docs/how-secure-are-public-links/). Public links can be accessible without login and can override view restrictions. This is a distinct feature from anonymous space access; a reachable URL is not automatically a public-link grant.
3. Atlassian: [Confluence permissions](https://support.atlassian.com/confluence-cloud/docs/what-are-confluence-cloud-permissions-and-restrictions/). Global, space and content restrictions affect who can view content.
4. Atlassian: [Product-specific terms](https://www.atlassian.com/legal/product-terms). Platform terms are distinct from a content owner's copyright or license. Applicability to this collection and the ToIP space must be assessed.
5. Atlassian: [Sharing with public links](https://support.atlassian.com/confluence-cloud/docs/share-content-externally-with-public-links/). Ordinary browser page URLs and special public-link URLs need not be interchangeable.

**These are general platform sources, not evidence that the specific ToIP space or every page is open for reuse.**

## Independent review decision record (to be completed by a real reviewer)

| Check | Required evidence | State |
| --- | --- | --- |
| Site/space access model | Anonymous-access or public-link policy for the actual HOME space and sampled pages, dated links | NOT VERIFIED |
| Source owner reuse conditions | ToIP/space license, terms or documented applicable exception permitting the *specific metadata reuse* | NOT VERIFIED |
| Platform/API conditions | Applicable Atlassian service/API restrictions, automated-access rules, limits and attribution | NOT VERIFIED |
| Metadata field minimization | Sample output checked for PII, titles, bodies, protected URLs and unexpected fields | NOT VERIFIED |
| Publication boundary | Confirm linkability of source URLs for intended public audience; remove inaccessible or restricted links | NOT VERIFIED |
| Retention and removal | Time-bound raw artifact retention, redaction, takedown/revocation process | NOT VERIFIED |
| Reviewer independence | Identified reviewer, role, dated decision, evidence URLs, scope, rationale and conflict check | NOT VERIFIED |
| Decision freshness | Approval effective dates and current revocation register | NOT VERIFIED |

### Required final review output

A separate, attributable, dated review must record **approved / denied / conditional**; exact site, space, periods, permitted fields and uses; conditions and exclusions; evidence URLs; retention and withdrawal mechanism; and reviewer identity. Only then may the operator consider `source_use_compliance_verified=true` in the separate decision/review records. A checked box or the presence of this dossier is **not** verification.

## Acceptance execution after review

1. If denied/indeterminate: preserve GitHub-only reporting and publish explicit Confluence `not_authorized` or `unavailable` coverage. Do not bypass the gate.
2. If approved for metadata: execute the bounded collector with reviewed scope, revocation register and retrieval timestamp; preserve diagnostic output without expanding to page bodies.
3. Independently verify source URLs/versions and curator subject mapping; run record-level admission with reviewer evidence.
4. Compose the actual August/September GitHub + admitted Confluence reports. Re-run negative tests, verify public links, publish via Pages only after release checks.
5. Link actual review, acquisition, qualification, CI, Pages and release evidence in #63 before closure.

**Current finding:** There is not yet an independently completed source-use decision in this dossier; no live cross-source publication is authorized by this document.
