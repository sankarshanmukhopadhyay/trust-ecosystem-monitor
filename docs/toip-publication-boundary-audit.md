# ToIP publication boundary audit

This note records the first implementation tranche from umbrella issue #122 for the ToIP cumulative-intelligence workstream. It narrows the next build step to a mechanically enforceable publication boundary for bounded Confluence acquisition artifacts.

## Proposition

A bounded Confluence acquisition artifact may be generated only as **metadata-only, nonpublication evidence** before record-level admission. The artifact must not silently carry page bodies, titles, excerpts, author/account fields, attachments, comments, meeting rosters, transcripts, recordings or other content-like material into a public reporting path.

This is deliberately narrower than source-use approval. It does not determine lawful access, copyright, reuse permission, ToIP endorsement, historical completeness or source-owner authority. Those remain owned by #63/#80/#82 and the source-use dossier.

## Implemented control

`trust_ecosystem_monitor.toip_publication_boundary` provides two functions:

- `audit_metadata_publication_boundary(payload)` returns boundary violations without mutating the payload.
- `assert_metadata_publication_boundary(payload)` raises `ValueError` if the artifact crosses the boundary.

`trust_ecosystem_monitor.toip_confluence_collect.collect()` now applies `assert_metadata_publication_boundary()` before returning or writing the acquisition artifact.

## Allowed Confluence record fields before admission

Only these per-record fields are allowed:

| Field | Meaning |
| --- | --- |
| `source` | Must be `confluence`. |
| `source_id` | Numeric Confluence page ID as a string. |
| `space_id` | Approved candidate HOME space ID `22970380`. |
| `version` | Positive integer page version. |
| `url` | Canonical `https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/{source_id}` URL without query or fragment. |
| `kind` | Must be `page_update`. |
| `classification` | Must be `metadata_only`. |

The acquisition artifact and each monthly result must also retain `publication_admitted=false`.

## Explicitly rejected before admission

The audit rejects content-like or personal-data fields such as:

- page titles;
- page bodies, storage bodies, HTML, macros or excerpts;
- author, creator, owner, account, email, display-name or avatar fields;
- attachments, comments, transcripts, recordings, speakers, attendees or rosters;
- noncanonical page URLs that include query or fragment data;
- any result-level or artifact-level `publication_admitted=true` state.

## Tests

`tests/test_toip_publication_boundary.py` covers:

- acceptance of a metadata-only, nonpublication artifact;
- rejection of top-level publication admission;
- rejection of page title, body/excerpt and author/account fields;
- rejection of non-metadata classification;
- rejection of noncanonical page URLs.

Existing collector tests continue to exercise the source-use review gate, revocation gate, unavailable-source behavior and nonpublication status.

## Residual limits

This tranche does not:

- verify external reviewer authenticity;
- approve any source-use condition;
- publish live cross-source findings;
- model WG/TF identity;
- improve discussion synthesis quality;
- verify live Pages deployment.

Its value is narrower but important: it turns one #122/#63 risk into executable evidence. If future code expands Confluence acquisition from metadata toward content extraction, that expansion must be a separate reviewed change with explicit source-use, privacy, publication and admission evidence.
