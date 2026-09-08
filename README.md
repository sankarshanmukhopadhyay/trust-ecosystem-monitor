# Trust Ecosystem Monitor

> An independent, evidence-backed observatory for GitHub-based trust ecosystems.

Trust Ecosystem Monitor discovers repositories from configured ecosystem profiles, applies explicit admission and collection policy, classifies admitted repositories into ecosystem-specific portfolios and lifecycle states, records auditable GitHub activity evidence, consolidates related activity into reviewable change units, and publishes decision-oriented reporting.

It is independently maintained. Monitoring an ecosystem does **not** make this project an official publication of that ecosystem.

## Monitored ecosystems

The current profiles are:

- **Trust Over IP Foundation** — `organizations/trustoverip/profile.toml`
- **Decentralized Identity Foundation (DIF)** — `organizations/decentralized-identity/profile.toml`
- **World Wide Web Consortium (W3C)** — `organizations/w3c/profile.toml`

Each ecosystem retains its own taxonomy, snapshots, dispositions and generated report tree. One ecosystem run cannot overwrite another.

W3C is intentionally different from the organization-wide ToIP and DIF discovery model. The monitor does **not** enumerate the entire W3C GitHub organization. It uses a bounded, evidence-backed repository set under governed admission so W3C organization membership is treated as discovery context, not automatic monitoring authority. See `docs/w3c-onboarding.md`.

## Why this exists

GitHub exposes repository-level activity. It does not naturally answer portfolio questions such as:

- What materially changed across an ecosystem this week?
- Which specifications, workgroups or implementations are advancing?
- Where has new work appeared?
- Which repositories changed lifecycle state?
- Which repositories are in monitoring scope, on watch, under review or explicitly excluded?
- Which repositories are not yet classified by the monitor taxonomy?
- Where are cross-portfolio review seams emerging?
- Which observations require attention, and what evidence supports them?

The monitor adds this portfolio-intelligence layer while keeping interpretation subordinate to traceable evidence.

## Architecture

```text
Trust Ecosystem Monitor
        │
        ├── ecosystem profile
        │     ├── discovery sources
        │     │     ├── GitHub organization
        │     │     └── explicit repositories
        │     ├── display metadata
        │     ├── governed admission policy where required
        │     └── ordered portfolio taxonomy
        │
        ├── admission + tier-aware collection
        │     ├── core / related → full activity evidence
        │     ├── watch          → metadata + release signals
        │     └── inventory      → provenance only
        │
        ├── change-unit and lifecycle analysis
        ├── findings + governed dispositions
        └── profile-scoped publication + scope register

organizations/
├── trustoverip/profile.toml
├── decentralized-identity/profile.toml
└── w3c/
    ├── profile.toml
    └── admission.toml

data/
├── trustoverip/
├── decentralized-identity/
└── w3c/

docs/
├── index.html                 # ecosystem catalog
├── ecosystems.json            # machine-readable catalog
├── trustoverip/
├── decentralized-identity/
└── w3c/
```

Discovery, admission, taxonomy and evidence collection are separate decisions. The core invariant is:

> Ecosystem membership is evidence for discovery, not sufficient authority for monitoring scope.

The original pre-multi-profile ToIP state under `data/snapshots/` is treated as a legacy migration seed. The first scoped ToIP collection carries that history forward rather than resetting lifecycle comparison.

## Evidence and admission model

The monitor keeps several layers distinct:

1. **Discovery provenance** — where and why a repository entered candidate scope.
2. **Admission** — explicit state (`included`, `watch`, `review`, `excluded`) plus collection tier (`core`, `related`, `watch`, `inventory`).
3. **Raw evidence** — repository metadata, commits, issues, pull requests and releases from the GitHub REST API according to collection tier.
4. **Change units** — conservative consolidation of related activity so a single work item is not represented as unrelated noise.
5. **Lifecycle deltas** — changes against the immediately preceding retained observation for the same ecosystem.
6. **Review seams** — evidence-graded reasons to inspect activity across portfolio boundaries. A seam is not automatically a formal dependency.
7. **Findings** — stable observations with separate materiality, urgency and assurance-impact dimensions.
8. **Dispositions** — explicit maintainer decisions such as `accepted`, `resolved` or `suppressed`, with authority, rationale, timestamp and evidence.

Governed profiles fail closed: a repository without sufficient repository-specific admission evidence resolves to `review` / `inventory`, rather than silently expanding monitoring scope.

Historical `toip-*` stable identifiers are intentionally preserved where they already exist. They are an identifier namespace, not the current product name; rewriting them would break dispositions and longitudinal references.

## Classification boundary

Portfolio taxonomy is profile-specific and deterministic. Classification precedence is:

```text
exact repository override
        ↓
ordered pattern rule
        ↓
Unclassified
```

Overrides are intended for repositories whose own work-item declaration provides stronger evidence than the repository name. Pattern rules remain appropriate for stable repository families. Every newly generated repository record carries classification provenance showing the method, matching rule or override, and profile.

A repository that cannot be classified defensibly remains **`Unclassified`**. This means the monitor taxonomy does not yet classify the repository. It does **not** imply a defect, governance failure or obligation in the upstream project. Zero unclassified repositories is therefore not a design goal.

See `docs/organization-profiles.md`, `docs/dif-onboarding.md`, and `docs/w3c-onboarding.md`.

## Local use

Python 3.11 or later is sufficient; the monitor uses the standard library.

Run tests and source validation:

```bash
python -m unittest discover -s tests
python -m trust_ecosystem_monitor validate
```

Collect one ecosystem, for example W3C:

```bash
GITHUB_TOKEN=... python -m trust_ecosystem_monitor collect \
  --profile organizations/w3c/profile.toml \
  --lookback-days 7
```

Render governed scope registers and the top-level catalog:

```bash
python -m trust_ecosystem_monitor.scope \
  docs/trustoverip \
  docs/decentralized-identity \
  docs/w3c
python -m trust_ecosystem_monitor site
```

Validate that every configured profile has current generated evidence:

```bash
python -m trust_ecosystem_monitor validate --require-generated
```

The former `toip-monitor` / `toip_monitor` entry points remain temporary compatibility aliases; new usage should use the canonical Trust Ecosystem Monitor names.

## Publication and retained state

The **Collect and publish weekly ecosystem briefs** workflow runs:

- manually through `workflow_dispatch`;
- on Sunday at 21:30 UTC; and
- after publication-affecting changes land on `main` under the narrow workflow/profile/collector path filter.

The workflow runs tests, restores the previous generated state, collects TrustOverIP, DIF and bounded W3C evidence, renders governed scope registers and the ecosystem catalog, validates generated state, persists the new generated evidence lineage, and deploys `docs/` through GitHub Pages Actions.

Generated `data/` and `docs/` observations are **not pushed directly to protected `main`**. They are retained on the automation-owned `generated-observations` branch. Source, profile and workflow changes continue to use the normal Issue → PR → validation → merge path on `main`. Pages deployment occurs only after generated observation state has been persisted successfully.

## Pages information architecture

The root Pages site is a catalog of monitored ecosystems. Its headline counts deliberately separate **taxonomy review** from substantive findings, so classification maintenance is not presented as ecosystem operational risk. It also distinguishes first baselines from stateful observations.

Each ecosystem report exposes its own decision and evidence surfaces:

- `index.html` — weekly executive overview;
- `scope.html` — human-readable discovery/admission/collection scope register;
- `findings.html` — stable finding register and disposition state;
- `portfolios.html` — portfolio/repository registry;
- `lifecycle.html` — state changes against the prior retained observation;
- `seams.html` — evidence-graded cross-portfolio review seams;
- `evidence.html` — normalized source evidence;
- `taxonomy.html` — classification method and rule/override provenance for every repository;
- `methodology.html` — method and interpretation boundaries;
- `data/latest.json` — complete machine-readable current state; and
- `data/scope.json` — machine-readable governed scope register.

For governed profiles, the scope register distinguishes discovered repositories from deep-monitored, watch-monitored, inventory-only, review-required and excluded scope.

## Cross-ecosystem boundary

Trust Over IP, DIF and W3C appearing in the same catalog does **not** establish a relationship between them. Cross-ecosystem dependency, convergence or standards-seam analysis is a separate capability and should only be added when supported by explicit evidence.

## Governance boundary

The monitor observes public upstream activity. It does not automatically open issues, submit comments, merge changes or modify monitored upstream repositories. Upstream engagement remains a human governance decision.

## Licensing

This repository uses a dual-license model:

- **Source code:** Apache License 2.0.
- **Documentation, reports, diagrams and other non-code content:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0), unless otherwise stated.

See `LICENSE`, `LICENSE-CONTENT.md`, and `LICENSES.md`.
