# Organization profiles

Trust Ecosystem Monitor separates organization-neutral collection and intelligence from ecosystem-specific discovery, admission and classification. Each monitored ecosystem is described by a TOML profile under `organizations/<profile-id>/profile.toml`.

## Current profiles

- `organizations/trustoverip/profile.toml` — Trust Over IP Foundation
- `organizations/decentralized-identity/profile.toml` — Decentralized Identity Foundation (DIF)
- `organizations/w3c/profile.toml` — World Wide Web Consortium (W3C)

W3C also uses `organizations/w3c/admission.toml` because its GitHub organization is materially broader than the intended monitoring scope.

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
- `explicit_repository` — name a specific repository as a bounded discovery source.

Profiles that omit `discovery_sources` remain backward-compatible: the historical `organization` field is treated as an explicit `github_organization` discovery source.

Discovery provenance is retained on generated repository records. Multiple discovery paths for the same repository are deduplicated without discarding the provenance that led to consideration.

A source type is not added merely because an external API exists. A discovery adapter needs an executable provenance, correlation and failure contract before the source can influence monitoring scope.

## Governed admission

Large ecosystems may opt into governed admission. Admission may be declared inline or, as with W3C, in a sibling `admission.toml` policy file whose repository-specific decisions override permissive discovery defaults.

Admission states are:

| State | Meaning |
| --- | --- |
| `included` | Repository is deliberately in monitoring scope. |
| `watch` | Repository is relevant enough for observation but not yet core monitoring scope. |
| `review` | Evidence is insufficient for a monitoring-scope decision. |
| `excluded` | Repository is deliberately outside monitoring scope; the decision may still be retained as inventory provenance. |

Collection tiers are a separate axis:

| Tier | Runtime collection intensity |
| --- | --- |
| `core` | Full repository metadata, commits, issues, pull requests and releases. |
| `related` | Full repository metadata, commits, issues, pull requests and releases. |
| `watch` | Repository metadata plus release signals only. |
| `inventory` | Repository identity/provenance only; no routine activity API calls. |

Tier-aware collection is enforced at runtime. Unsupported state/tier combinations fail rather than silently widening collection.

### Fail-closed scope rule

For governed admission, unresolved repositories default to:

```text
state = review
tier  = inventory
```

Absence of repository-specific evidence therefore creates a review item rather than silently expanding monitoring scope. Explicit `included` and `watch` decisions require rationale and evidence.

This is the core governance invariant:

> Ecosystem membership is evidence for discovery, not sufficient authority for monitoring scope.

### Legacy compatibility

Profiles without a governed admission policy use the historical `all_discovered` behavior with `state = included` and `tier = core`. This preserves the existing Trust Over IP and DIF behavior until those profiles deliberately adopt governed admission.

## W3C proving baseline

The W3C profile intentionally avoids `github_organization` discovery. It currently names six repositories explicitly and admits them through evidence-backed policy:

- core: `w3c/vc-data-model`, `w3c/vc-data-integrity`, `w3c/vc-bitstring-status-list`;
- related: `w3c/cid`, `w3c/vc-di-bbs`, `w3c/webauthn`.

This is a proving baseline, not a claim that these are the only W3C repositories relevant to digital trust. Expansion requires a repository-specific admission decision with rationale and evidence. See `docs/w3c-onboarding.md`.

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

Every newly generated repository record includes monitor-owned classification provenance. `Unclassified` is a monitor-maintainer review state. It means the current taxonomy does not yet place the repository; it does not imply that the upstream repository is deficient or obligated to change.

## Profile-scoped state and publication

Every profile owns separate retained and generated state:

```text
data/<profile-id>/snapshots/
data/<profile-id>/dispositions.json

docs/<profile-id>/index.html
docs/<profile-id>/scope.html
docs/<profile-id>/findings.html
docs/<profile-id>/portfolios.html
docs/<profile-id>/lifecycle.html
docs/<profile-id>/seams.html
docs/<profile-id>/evidence.html
docs/<profile-id>/taxonomy.html
docs/<profile-id>/methodology.html
docs/<profile-id>/data/latest.json
docs/<profile-id>/data/scope.json
```

`scope.html` and `data/scope.json` make discovery, admission and collection intensity auditable repository-by-repository. They distinguish discovered, deep-monitored, watch-monitored, inventory-only, review-required and excluded repositories.

Generated observations are retained on the automation-owned `generated-observations` branch rather than pushed directly to protected `main`. Source, profile, policy and workflow changes continue through the normal PR and validation path. The publication workflow restores prior generated state, collects fresh evidence, persists the new generated state lineage, and only then deploys GitHub Pages.

## TrustOverIP migration compatibility

The project originally retained TrustOverIP observations under the unscoped `data/snapshots/` path. During the first profile-scoped TrustOverIP run, that legacy snapshot set is used as the seed if `data/trustoverip/snapshots/` does not yet exist. This preserves lifecycle continuity.

The same fallback applies to the legacy `data/dispositions.json` ledger. Once scoped state exists, the scoped paths are authoritative.

Historical `toip-*` finding/change/seam identifiers remain stable. They are not renamed because dispositions and longitudinal references depend on them.

## Adding another ecosystem

A new ecosystem should normally be added as another profile rather than by cloning the monitor. Before admission:

1. identify the ecosystem's own governance/work-item/lifecycle vocabulary;
2. declare bounded discovery sources and preserve their provenance;
3. choose governed admission when discovery is materially broader than intended monitoring scope;
4. record repository-specific rationale and evidence for deliberate inclusion/watch decisions;
5. assign collection tiers deliberately and test their runtime behavior;
6. create conservative classification rules grounded in ecosystem vocabulary;
7. allow unresolved admission to remain `review` and unmatched taxonomy to remain `Unclassified` rather than guessing;
8. run a first baseline and inspect admission/classification gaps plus the generated scope register; and
9. keep that ecosystem's evidence and dispositions profile-scoped.

Cross-ecosystem reporting is a separate capability. The existence of multiple profiles is not evidence of a technical dependency, governance relationship or standards alignment.
