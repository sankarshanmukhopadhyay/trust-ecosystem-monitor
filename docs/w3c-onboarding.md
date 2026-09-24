# W3C monitoring onboarding and scope

This note records why and how the World Wide Web Consortium (W3C) is monitored by Trust Ecosystem Monitor. It is monitor governance documentation, not a W3C publication or an assertion of W3C endorsement.

## Why W3C requires bounded discovery

The W3C GitHub organization contains far more repositories than this monitor can justify treating as trust-infrastructure monitoring scope. Organization membership therefore cannot be used as an automatic admission rule.

The W3C profile deliberately uses `explicit_repository` discovery sources only. It does not enumerate `w3c/*` through the GitHub organization API. Repository inclusion is separately governed by `organizations/w3c/admission.toml`.

> Ecosystem membership is evidence for discovery, not sufficient authority for monitoring scope.

## Current governed baseline

The 24 September 2026 baseline expands the proving set from six to sixteen repositories because the newly admitted work has direct, evidenced intersection with monitored DIF and/or TrustOverIP work.

| Repository | Portfolio | Admission | Tier |
| --- | --- | --- | --- |
| `w3c/vc-data-model` | Verifiable Credentials | included | core |
| `w3c/vc-data-integrity` | Verifiable Credentials | included | core |
| `w3c/vc-bitstring-status-list` | Verifiable Credentials | included | core |
| `w3c/vc-jose-cose` | Verifiable Credentials | included | core |
| `w3c/vc-json-schema` | Verifiable Credentials | included | related |
| `w3c/vcalm` | Verifiable Credentials | included | related |
| `w3c/vc-recognized-entities` | Trust & Recognition | included | core |
| `w3c/cid` | Identifiers & Control | included | related |
| `w3c/did` | Identifiers & Control | included | core |
| `w3c/did-resolution` | Identifiers & Control | included | core |
| `w3c/did-extensions` | Identifiers & Control | included | related |
| `w3c/did-rubric` | Identifiers & Control | watch | watch |
| `w3c/vc-di-bbs` | Privacy & Applied Cryptography | included | related |
| `w3c/vc-di-eddsa` | Privacy & Applied Cryptography | included | related |
| `w3c/vc-di-ecdsa` | Privacy & Applied Cryptography | included | related |
| `w3c/webauthn` | Authentication | included | related |

The set remains intentionally bounded. It is not a statement that other W3C repositories are irrelevant.

## Why these additions matter

The DID and DID Resolution repositories add the normative identifier/resolution surface that DIF DID Methods and Universal Resolver build against. Recognized Entities adds a distinct trust-and-recognition surface that intersects ToIP trust-registry and governance work. JOSE/COSE, JSON Schema, VCALM and the additional cryptosuites fill material VC interoperability seams that were not represented by the original Data Integrity/BBS-only baseline.

`w3c/did-rubric` is deliberately watch-tier: rubric evolution can change evaluation context, but the rubric is not treated as an implementation dependency.

## Admission and expansion rule

Adding another W3C repository requires all of the following in repository-owned configuration:

1. an explicit discovery source;
2. an admission state and collection tier;
3. a monitor rationale explaining why the repository belongs in scope;
4. evidence from an authoritative W3C workgroup, publication or tool record; and
5. a portfolio classification that is defensible from the evidence.

If the evidence is insufficient, the fail-closed result is `review` / `inventory`.

## Cross-ecosystem use

W3C is an independently collected profile. Its inclusion does not itself assert that a W3C artifact is a dependency of DIF or TrustOverIP work. Cross-ecosystem relationships are derived separately and must retain relationship type, directionality, evidence grade, provenance and review state.

This separation allows the monitor to distinguish, for example:

- a normative dependency on a W3C specification;
- an informative reference such as a resolver implementation listed by a W3C specification;
- a shared external primitive used independently by two ecosystems; and
- a merely topical similarity that remains a candidate rather than a published dependency.

## Runtime collection semantics

- `core` and `related`: repository metadata plus commits, issues, pull requests and releases;
- `watch`: repository metadata plus release signals only;
- `inventory`: repository identity and discovery/admission provenance only.

## Published assurance surfaces

Every W3C run publishes human-readable and machine-readable scope evidence under `docs/w3c/`. Cross-ecosystem publication is generated separately at the catalog root so profile-local evidence remains the source of truth.

## Operational evidence

Generated `data/` and `docs/` state is retained on the automation-owned `generated-observations` branch; `main` remains the PR-governed source/configuration branch. Pages deploys only after generated observation state has been persisted.

## Review boundary

W3C scope should be expanded only when evidence justifies it. A large organization is not a reason to collect everything, and a low repository count is not a reason to force expansion. The monitor should prefer a small explainable scope over a comprehensive but unauditable one.
