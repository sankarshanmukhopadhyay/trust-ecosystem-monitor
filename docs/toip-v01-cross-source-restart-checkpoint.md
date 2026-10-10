# ToIP v0.1 cross-source release — restart checkpoint (2026-10-10)

## Binding release decision

**Wait for the full GitHub + Confluence cross-source release.** Do not substitute a GitHub-only v0.1 release and do not claim cross-source readiness from synthetic tests. The already available GitHub-only pages may remain visible as historical prototypes, with explicit Confluence coverage limitations. LFX Calendar/Zoom is deferred (#80). DIF–ToIP cross-ecosystem analysis (#24), relationship discovery (#58), and A2A admission (#25) are outside this release.

## Current engineering state

The main branch contains the following merged increments:

| PR | Capability |
| --- | --- |
| #78/#79 | Source-aware historical site generator and offline readiness gate |
| #83 | Conservative observation and correlation contract |
| #84 | Bounded read-only Confluence metadata acquisition |
| #85 | Reviewable subject evidence URLs |
| #86 | Synthetic-only cross-source HTML rehearsal |
| #87 | Sponsor authorization declaration (not source-owner rights) |
| #88/#89 | Pagination integrity, version/retrieval provenance, conservative coverage |
| #90 | Metadata quarantine adapter |
| #91 | Curator review-ready qualification, not publication admission |

**Open PR #92** contains a first implementation of the source authorization decision and independent evidence admission gates. The branch is `feat/toip-release-gates-checkpoint`; do not treat it as merged or independently reviewed. The code checks declared source-owner role, independent-authority flag, space/period/use scope, expiry, revocation register, evidence URLs, and distinct reviewer assertions. These are *structural* checks only: no issuer authentication, URL dereferencing, or substantive evidence validation is provided. Synthetic tests cannot establish real rights.

## Release gates and progress

| Gate | Current state | Required closure evidence |
| --- | --- | --- |
| Authorization decision contract (WP1) | PR #92 open | Review design, test edge cases, passing CI, merge |
| Qualified evidence admission (WP2) | PR #92 open | Verify version/scope binding, fail-closed tests, independent review semantics, passing CI |
| Confluence source authority | BLOCKED, #63 | Dated source-owner confirmation, approved space/page inventory, reporting period, permitted acquisition/retention/reuse/publication, exclusions, revocation/expiry |
| Historical Confluence retrieval | Offline-tested only, #63 | Rights-compliant August/September replay, pagination and time-window reconciliation, duplicates, URL/version checks, truthful coverage |
| Evidence correlation (WP4) | Basic conservative reference correlation, #82 | Independently review mapped subjects; lifecycle/implementation/dependency/evidence-gap types where justified; deduplication, grading, negative tests |
| Report integration (WP5) | Synthetic renderer only, #63/#82 | Source-aware JSON/Markdown/HTML using only admitted records; no false zero activity |
| Release assurance (WP6) | Not complete | Full CI, security/privacy/retention tests, rollback, stable release artifacts |
| Public Pages verification (WP7) | #81 OPEN | Fresh main workflow, all specified public routes, navigation, a11y basics, source links, run SHA/date |
| Release disposition (WP8) | Not complete | Release notes, operator runbook, acceptance links, version/tag, issue disposition |
| GitHub quota hardening | #65 OPEN | Bounded rate-limit classification/retry and successful weekly evidence run |

## Source facts and limitations

The public Confluence v2 space lookup associated candidate numeric ID `22970380` with `HOME`. Diagnostic August/September CQL searches returned 22/36 last-modified matches, and mapped them to this space. These are **search matches**, not an authoritative inventory, complete history, distinct governance events, or proof of reuse rights. `scope_verified=false`, and historical completeness is not established.

Sponsor `sankarshanmukhopadhyay` approved bounded experimental research on lawfully accessible public metadata; this is not ToIP source-owner permission for automated acquisition or republication. No real Confluence evidence should be admitted or published before independently verified source-owner decisions. A page update does not establish a governance decision; subject correlation does not establish adoption or causation.

## Restart sequence (dependency ordered)

1. Review PR #92 code and tests, check CI, repair defects, and merge only when green. Pay special attention to externally supplied authorization assertions, scope binding, revocation freshness, decision evidence, and duplicate-version handling.
2. Independently complete #81 public verification; keep issue open if public pages cannot be verified.
3. Resolve #63 source-owner scope/rights or document the exact external blocker. Do not relax rights gates to meet a release target.
4. After authorization, execute bounded historical acquisition for both months; reconcile results and independently verify representative source URLs.
5. Harden #82: explicit reviewed subject mapping, evidence grading, duplicate suppression, unsupported-inference negative tests. Publish no fabricated cross-source findings.
6. Integrate admitted observations with source-aware monthly JSON/Markdown/HTML, preserving historical GitHub-only views and truthful missing-source disclosures.
7. Finish #65 operational quota handling; run full validation, release smoke tests and public Pages checks; publish a versioned full cross-source release only after acceptance evidence is linked.

## Issue ownership

#63 is the source scope/rights, acquisition and combined-report parent. #82 owns cross-source inference and correlation. #81 owns public Pages verification; #65 owns quota resilience. #80 is deferred. Keep #63/#82 open until full release acceptance; keep checkboxes unchecked when tests are synthetic or rights are unverified.

## Definition of done

A full release requires authenticated source-owner rights, authorized bounded historical acquisition, independently reviewed source mappings, actual supported cross-source findings where evidence exists (or an explicit evidence-unavailable disposition), integrated reproducible reports, privacy and retention controls, green CI, public Pages verification, and linked release evidence. No external approval or live publication is implied by this checkpoint.
