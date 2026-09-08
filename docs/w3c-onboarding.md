# W3C monitoring onboarding and scope

This note records why and how the World Wide Web Consortium (W3C) is monitored by Trust Ecosystem Monitor. It is monitor governance documentation, not a W3C publication or an assertion of W3C endorsement.

## Why W3C requires bounded discovery

The W3C GitHub organization contains far more repositories than this monitor can justify treating as trust-infrastructure monitoring scope. Organization membership therefore cannot be used as an automatic admission rule.

The W3C profile deliberately uses `explicit_repository` discovery sources only. It does not enumerate `w3c/*` through the GitHub organization API. Repository inclusion is separately governed by `organizations/w3c/admission.toml`.

The governing rule is:

> Ecosystem membership is evidence for discovery, not sufficient authority for monitoring scope.

## Current proving baseline

The September 2026 baseline contains six repositories. Each has an explicit admission decision, rationale, portfolio and W3C evidence source.

| Repository | Portfolio | Admission | Tier |
| --- | --- | --- | --- |
| `w3c/vc-data-model` | Verifiable Credentials | included | core |
| `w3c/vc-data-integrity` | Verifiable Credentials | included | core |
| `w3c/vc-bitstring-status-list` | Verifiable Credentials | included | core |
| `w3c/cid` | Identifiers & Control | included | related |
| `w3c/vc-di-bbs` | Privacy & Applied Cryptography | included | related |
| `w3c/webauthn` | Authentication | included | related |

The baseline is intentionally small. It is a proving set for governed monitoring, not a statement that other W3C repositories are irrelevant.

## Admission and expansion rule

Adding another W3C repository requires all of the following in repository-owned configuration:

1. an explicit discovery source;
2. an admission state and collection tier;
3. a monitor rationale explaining why the repository belongs in scope;
4. evidence from an authoritative W3C workgroup, publication or tool record; and
5. a portfolio classification that is defensible from the evidence.

If the evidence is insufficient, the fail-closed result is `review` / `inventory`. That state preserves provenance without authorizing routine activity collection.

## Runtime collection semantics

Collection depth is enforced by tier:

- `core` and `related`: repository metadata plus commits, issues, pull requests and releases;
- `watch`: repository metadata plus release signals only;
- `inventory`: repository identity and discovery/admission provenance only, with no routine activity API calls.

Discovery therefore does not imply deep monitoring, and admission policy is executable rather than descriptive.

## Published assurance surfaces

Every W3C run publishes both human-readable and machine-readable scope evidence:

- `w3c/scope.html` — repository-level discovery, admission, tier, rationale, evidence and provenance;
- `w3c/data/scope.json` — machine-readable scope register;
- `w3c/data/latest.json` — current generated evidence state; and
- the standard ecosystem report surfaces for findings, portfolios, lifecycle, seams, evidence, taxonomy and methodology.

The scope register distinguishes discovered, deep-monitored, watch-monitored, inventory-only, review-required and excluded repositories.

## Operational evidence

The first production W3C publication run on 8 September 2026 completed successfully after the generated-state persistence model was corrected for protected `main`. The workflow now retains generated `data/` and `docs/` state on the automation-owned `generated-observations` branch and deploys Pages only after that state has been persisted.

This operational design keeps source authority and observation authority separate:

- `main` remains the PR-governed source/configuration branch;
- `generated-observations` is the append-only operational evidence lineage maintained by automation; and
- GitHub Pages publishes the generated `docs/` artifact from the validated collection run.

## Review boundary

W3C scope should be expanded only when the evidence justifies it. A large organization is not a reason to collect everything, and a low repository count is not a reason to force expansion. The monitor should prefer a small explainable scope over a comprehensive but unauditable one.
