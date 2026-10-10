# Confluence metadata to evidence-contract boundary

The offline adapter `stage_confluence_metadata` takes the acquisition result from `acquire_metadata` and produces a **quarantined metadata manifest**, not a validated observation or public intelligence finding.

| Acquired field | Treatment |
| --- | --- |
| `source_id`, `space_id`, `version`, `url` | Retained as page identity and version provenance |
| `retrieved_at` | Retained as acquisition time, **not** an event time |
| `kind=page_update` | Retained as technical page metadata; never promoted to `decision` |
| `scope_verified=false`, `publication_admitted=false` | Required fail-closed preconditions |
| `occurred_at`, `subject_id`, `subject_evidence_url`, `summary` | Not inferred or synthesized |
| `publication_approved` | Never inferred from sponsor approval or public accessibility |

An authorized curator would need independently reviewable source evidence, a defensible event timestamp, an explicitly evidenced shared subject, a factual reviewed summary, and source-owner/publication decisions before constructing a separate `toip_evidence_contract.validate_observations`-eligible record. The adapter deliberately does not offer that promotion path.

A Confluence last-modified match cannot establish that a governance decision occurred. Even a valid GitHub–Confluence subject reference is not evidence of governance approval, adoption, causation or interoperability.

This increment uses synthetic/offline fixtures only; it does not call the live Confluence API, change workflow wiring, or authorize public reporting.
