# Curator-reviewed Confluence evidence qualification

The qualification function `qualify_confluence_metadata(manifest, review)` accepts a quarantined metadata manifest and a human-supplied review object for **one exact page version**. It runs offline and does not access Confluence.

A review requires a named curator, timezone-aware review and event timestamps, explicit page ID/version, an identified subject, factual reviewed summary, page-update event type, review attestation, and HTTPS event/subject evidence URLs on the verified Confluence host. Missing evidence, mismatched versions, non-Confluence links, naive timestamps, unsupported decision classification and implicit publication are rejected.

**Review-ready is not publication-ready.** The returned candidate explicitly has `publication_approved=false`; the existing evidence contract must reject it even when `approved_confluence=True`. The result also retains `source_owner_authority_verified=false`, `publication_admitted=false` and `correlation_eligible=false`. Curator assertions are not proof of authority, and matching subject IDs alone do not establish governance approval or adoption.

The qualification contract is a validation mechanism for curator-supplied assertions, **not independent verification** that the cited URLs substantiate those assertions. The fixture is synthetic. No public Confluence ingestion, real-world review or publication is claimed.

Further work requires a separately evidenced source-owner decision, publication rights, independent substantive source review, and controlled admission into the existing evidence contract. Do not turn the sponsor declaration into a bypass of these gates.
