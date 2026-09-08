# Organization profiles

Trust Ecosystem Monitor separates organization-neutral collection and intelligence from ecosystem-specific discovery, admission and classification. Each monitored ecosystem is described by a TOML profile under `organizations/<profile-id>/profile.toml`.

## Current profiles

- `organizations/trustoverip/profile.toml` — Trust Over IP Foundation
- `organizations/decentralized-identity/profile.toml` — Decentralized Identity Foundation (DIF)

## Profile contract

A profile defines:

- a stable profile identifier;
- one or more discovery sources;
- ecosystem display metadata and disclaimer text;
- an optional repository admission policy;
- optional exact repository-to-portfolio overrides; and
- ordered portfolio rules using repository-name prefixes and contained fragments.

These concerns are deliberately separate:

```text
discovery source
      ↓
candidate repository
      ↓
admission decision + collection tier
      ↓
portfolio classification
      ↓
evidence pipeline
```

Discovery answers **where a candidate was observed**. Admission answers **whether and how deeply the monitor should observe it**. Portfolio classification answers **where the admitted repository belongs in the ecosystem taxonomy**. None of these decisions establishes an upstream governance relationship by itself.

## Discovery sources

Profiles may declare `[[discovery_sources]]` entries. The executable source types are currently:

- `github_organization` — discover repositories published by a GitHub organization;
- `explicit_repository` — name a repository that is outside the primary organization boundary.

Profiles that omit `discovery_sources` remain backward-compatible: the historical `organization` field is treated as an explicit `github_organization` discovery source.

A source type is not added merely because an external API exists. A discovery adapter needs an executable provenance, correlation and failure contract before the source can influence monitoring scope.

## Governed admission

Large ecosystems may opt into governed admission:

```toml
[admission]
mode = "governed"

[[admission.repositories]]
repository = "example-spec"
state = "included"
tier = "core"
rationale = "The ecosystem governance record identifies this as an active specification repository."
evidence = ["https://example.org/governance/example-spec"]
```

Admission states are:

| State | Meaning |
| --- | --- |
| `included` | Repository is deliberately in monitoring scope. |
| `watch` | Repository is relevant enough for observation but not yet core monitoring scope. |
| `review` | Evidence is insufficient for a monitoring-scope decision. |
| `excluded` | Repository is deliberately outside monitoring scope; the decision may still be retained as inventory provenance. |

Collection tiers are a separate axis:

| Tier | Intended collection intensity |
| --- | --- |
| `core` | Full evidence collection for primary standards/work items. |
| `related` | Full or near-full evidence for materially related work. |
| `watch` | Reduced observation intended to detect material movement. |
| `inventory` | Shallow identity/provenance sufficient to preserve discovery or review state. |

The admission contract does not yet alter collector depth; tier-aware collection is a separate implementation tranche. Recording the tier first makes that future behavior explicit and testable rather than embedding scope judgments in collector code.

### Fail-closed scope rule

For `mode = "governed"`, the defaults are fixed:

```text
state = review
tier  = inventory
```

A governed profile cannot configure a more permissive default. Absence of repository-specific evidence therefore creates a review item rather than silently expanding monitoring scope. Explicit `included` and `watch` overrides require evidence as well as a rationale.

This is the core governance invariant:

> Ecosystem membership is evidence for discovery, not sufficient authority for monitoring scope.

### Legacy compatibility

Profiles without an `[admission]` table use `mode = "all_discovered"` with `state = "included"` and `tier = "core"`. This preserves the existing Trust Over IP and DIF behavior until those profiles deliberately adopt governed admission.

## Portfolio classification

Classification precedence is:

```text
exact repository override
        ↓
ordered pattern rule
        ↓
Unclassified
```

An override should be used when the repository's own README, work-item declaration or governance material provides stronger evidence than its name. Pattern rules should cover stable repository families. Broad rules should not be introduced merely to drive the unclassified count toward zero.

Every newly generated repository record includes monitor-owned classification provenance:

```json
{
  "portfolio": "Claims & Credentials",
  "classification": {
    "method": "override",
    "rule": "credential-schemas",
    "profile": "decentralized-identity"
  }
}
```

For pattern matches, `method` is `rule` and `rule` identifies the matching prefix or contained fragment. For unmatched repositories, `method` is `unclassified` and `rule` is null.

`Unclassified` is a monitor-maintainer review state. It means the current taxonomy does not yet place the repository; it does not imply that the upstream repository is deficient or obligated to change.

## Profile-scoped state

Every profile owns separate retained and generated state:

```text
data/<profile-id>/snapshots/
data/<profile-id>/dispositions.json

docs/<profile-id>/index.html
docs/<profile-id>/findings.html
docs/<profile-id>/portfolios.html
docs/<profile-id>/lifecycle.html
docs/<profile-id>/seams.html
docs/<profile-id>/evidence.html
docs/<profile-id>/taxonomy.html
docs/<profile-id>/methodology.html
docs/<profile-id>/data/latest.json
```

The `taxonomy.html` surface makes the profile decision auditable repository-by-repository. It describes how the monitor classified the repository; it is not an upstream governance assertion.

The root `docs/index.html` is an ecosystem catalog. Taxonomy-review items are counted separately from substantive findings so classification maintenance does not read as ecosystem operational risk. The catalog also distinguishes a first baseline from a stateful observation based on whether a previous retained snapshot was available.

## TrustOverIP migration compatibility

The project originally retained TrustOverIP observations under the unscoped `data/snapshots/` path. During the first profile-scoped TrustOverIP run, that legacy snapshot set is used as the seed if `data/trustoverip/snapshots/` does not yet exist. This preserves lifecycle continuity.

The same fallback applies to the legacy `data/dispositions.json` ledger. Once scoped state exists, the scoped paths are authoritative.

Historical `toip-*` finding/change/seam identifiers remain stable. They are not renamed because dispositions and longitudinal references depend on them.

## Adding another ecosystem

A new ecosystem should normally be added as another profile rather than by cloning the monitor. Before admission:

1. identify the ecosystem's own governance/work-item/lifecycle vocabulary;
2. declare bounded discovery sources and preserve their provenance;
3. choose `governed` admission when discovery is materially broader than intended monitoring scope;
4. record repository-specific rationale and evidence for deliberate inclusion/watch decisions;
5. create conservative classification rules grounded in ecosystem vocabulary;
6. use exact classification overrides only where repository-specific evidence justifies them;
7. allow unresolved admission to remain `review` and unmatched taxonomy to remain `Unclassified` rather than guessing;
8. run a first baseline and inspect admission and classification gaps; and
9. keep that ecosystem's evidence and dispositions profile-scoped.

Cross-ecosystem reporting is a separate capability. The existence of two profiles is not evidence of a technical dependency, governance relationship or standards alignment.
