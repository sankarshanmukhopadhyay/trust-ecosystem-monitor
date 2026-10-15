# ToIP CY intelligence data contract

Status: machine-ingestion guidance for `tem-cy-intelligence-v1`.

Related issues: #122, #130. Related operational verification: #81. Source-use and authority gates remain tracked in #63, #80 and #82.

## 1. Canonical ingestion source

The canonical machine-ingestion source for the ToIP CY 2026 intelligence page is the generated JSON manifest:

```text
generated-observations:docs/intelligence/toip/2026/data/manifest.json
```

The rendered public page:

```text
https://sankarshanmukhopadhyay.github.io/trust-ecosystem-monitor/intelligence/toip/2026/
```

is a human-facing HTML view generated from that manifest. ML tooling should prefer the JSON manifest and should not scrape the rendered HTML unless it is explicitly testing presentation output.

The companion schema is:

```text
docs/intelligence/toip/2026/data/schema.json
```

## 2. Product boundary

This data contract describes an independent Trust Ecosystem Monitor (TEM) observation surface for ToIP-related GitHub activity and bounded source-observation metadata.

The data is not:

- not an official ToIP inventory;
- not a ToIP, LFDT, Linux Foundation, WG or TF statement;
- not a meeting record;
- not a decision register;
- not evidence of adoption, approval, implementation quality or interoperability;
- not source-owner authorization to republish Confluence, LFX, Zoom or meeting content;
- not an admitted cross-source intelligence finding surface.

The annual manifest is suitable for ML tooling that needs to inspect observed GitHub lifecycle activity, candidate WG/TF reader grouping, annual chronology, evidence URLs and provenance boundaries.

## 3. Schema identifier

The manifest schema identifier is:

```text
tem-cy-intelligence-v1
```

The top-level document has this shape:

```json
{
  "schema": "tem-cy-intelligence-v1",
  "year": 2026,
  "months": {},
  "source_ledger": {},
  "revision_notices": []
}
```

## 4. Top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema` | string | Must be `tem-cy-intelligence-v1`. |
| `year` | integer | Calendar year represented by the report. |
| `months` | object | Map of `YYYY-MM` to immutable first monthly observation records. |
| `source_ledger` | object | Map of tracked source identifiers to append-only observed source states. |
| `revision_notices` | array | Append-only notices for later source changes or re-observation mismatches. |

## 5. Monthly record model

Each `months[YYYY-MM]` record contains:

| Field | Type | Description |
| --- | --- | --- |
| `period` | string | Same `YYYY-MM` month key. |
| `observed_at` | string | Offset-aware timestamp when the observation was recorded. |
| `observation` | object | Monthly observation payload. |
| `observation_digest` | string | SHA-256 digest over the canonicalized `observation` object. |
| `temporal_basis` | string | Temporal interpretation of the observation. Existing values include `retrospective-current-public-source`. |

Monthly observations are immutable. Reruns that produce different evidence must create notices rather than silently rewriting the original monthly observation.

## 6. Observation payload

Each monthly `observation` contains two source families:

```json
{
  "github": {
    "scope": {},
    "coverage_complete": true,
    "evidence": []
  },
  "confluence": {
    "coverage": "sample_only",
    "source_count": 0,
    "unavailable_count": 0,
    "sources": []
  }
}
```

### 6.1 GitHub observation model

`github.evidence` contains observed issue and pull-request lifecycle records from configured ToIP repositories. Expected fields include, when present:

| Field | Interpretation |
| --- | --- |
| `repository` | GitHub repository full name. |
| `url` | Canonical GitHub URL for the observed issue or pull request. |
| `title` | GitHub issue or PR title. |
| `event` | Observed lifecycle event or state used by the collector. |
| `kind` / `type` | Issue/PR classification when emitted by the collector. |
| `created_at`, `updated_at`, `closed_at`, `merged_at` | GitHub timestamps when available. |
| `number` | GitHub issue or PR number when available. |

Consumers should treat GitHub evidence as observed repository activity. It does not prove ToIP governance decisions, adoption, implementation quality, interoperability or WG/TF authority.

### 6.2 Confluence observation model

The manifest structure can hold bounded Confluence source observations, but the CY GitHub-only backfill deliberately writes empty Confluence source sets for backfilled months.

For backfilled months, consumers should expect:

```json
{
  "coverage": "sample_only",
  "source_count": 0,
  "unavailable_count": 0,
  "sources": []
}
```

Do not infer that zero Confluence sources means no ToIP activity occurred. It only means that Confluence evidence was not admitted into that month by this ingestion path.

## 7. Source ledger

`source_ledger` is keyed by source identifier. Entries are append-only observed states for tracked sources. Ledger entries may include:

| Field | Description |
| --- | --- |
| `observed_at` | Time at which this state was observed. |
| `observed_in` | Reporting month in which the source state was observed. |
| `id` | Source identifier. |
| `url` | Canonical source URL. |
| `title` | Source title when available. |
| `version` | Source version when available. |
| `version_created_at` | Source version timestamp when available. |
| `page_kind` | Classification such as `unknown` or `administrative`. |
| `github_references` | GitHub URLs found in the bounded source representation. |
| `content_fingerprint` | Digest of the bounded extracted source representation. |
| `discussions` | Bounded discussion blocks when admitted. |
| `evidence` | Bounded evidence abstractions when admitted. |

Ledger entries are not a license or authority assertion. They only record observed source states under the current source-use boundary.

## 8. Revision notices

`revision_notices` records later changes, re-observation mismatches or interpretation changes. A revision notice normally includes:

| Field | Description |
| --- | --- |
| `key` | Stable notice key. |
| `kind` | Notice type, such as `month_reobservation`, `source_version_change` or `interpretation_method_change`. |
| `period` | Reporting period affected by the notice. |
| `observed_at` | Time the notice was recorded. |
| `source` | Source or run identifier. |
| `prior_digest`, `current_digest` | Digest transition where applicable. |
| `impact` | Expected disposition, normally `review_required`. |
| `explanation` | Human-readable explanation. |

A revision notice does not automatically rewrite a prior observation.

## 9. WG/TF candidate grouping

The rendered annual page includes a WG/TF-first candidate view. That view is derived from a curated incomplete registry and GitHub repository mappings.

For ML use:

- treat WG/TF group labels as reader-navigation aids;
- preserve unmapped evidence;
- preserve multiple candidate mappings where present;
- do not convert candidate grouping into official ToIP authority;
- do not infer meeting outcomes or decisions from group membership.

The registry and grouping code intentionally use non-authoritative wording such as candidate body, authority boundary, confidence and unmapped/unknown ToIP body.

## 10. Safe ML uses

Recommended uses:

- extract annual GitHub-observed activity by month;
- build issue/PR timelines;
- cluster observed GitHub artifacts by repository, candidate WG/TF grouping or topic;
- identify evidence URLs for human review;
- detect gaps, unavailable sources and required manual review;
- compare future manifests by month, digest and revision notice.

## 11. Unsafe inferences

Do not infer:

- official ToIP WG/TF structure;
- meeting occurrence or attendance;
- formal decision, approval, adoption or rejection;
- implementation quality or interoperability;
- source-owner authorization;
- completeness of ToIP activity;
- absence of activity from absence of observations.

## 12. Example extraction patterns

```text
$.schema
$.year
$.months.*.period
$.months.*.observed_at
$.months.*.observation.github.evidence[*].url
$.months.*.observation.github.evidence[*].repository
$.months.*.observation.confluence.sources[*]
$.source_ledger.*[*]
$.revision_notices[*]
```

## 13. Versioning policy

Changes that only add optional fields can remain `tem-cy-intelligence-v1` if existing consumers remain compatible.

Changes that rename, remove or reinterpret required fields should use a new schema identifier and a migration note.

## 14. Operational references

- #122: umbrella architecture, source authority, knowledge quality and roadmap.
- #81: public Pages verification.
- #63: Confluence source-use and publication boundary.
- #80: LFX/meeting authority.
- #82: cross-source admission.
- #128: CY GitHub-only annual backfill.
- #129: backfill observability/resumability hardening.
- #130: this data-contract tranche.
