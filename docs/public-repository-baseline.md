# Public repository baseline

This record captures controls reviewed under issue #27 and subsequent operational evidence. It is repository assurance evidence, not external certification.

| Control | State | Evidence | Residual risk |
|---|---|---|---|
| Purpose/adoption/taxonomy boundaries | PASS | `README.md`, organization profiles, W3C onboarding note, generated scope registers | Monitor taxonomy and admission policy are monitor-owned judgments, not upstream authority. |
| Licensing | PASS | `LICENSE`, `LICENSE-CONTENT.md`, `LICENSES.md` | None identified. |
| Security reporting | PASS | `SECURITY.md` | Hosted private-reporting enablement remains platform evidence. |
| Contribution/community/support | PASS | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, issue/PR templates | None identified. |
| Dependency updates | PASS | `.github/dependabot.yml`; Dependabot PR #30 validated and merged on 2026-09-08 | Major action updates still require green workflow evidence before merge. |
| Default-branch protection | PASS | `main` is protected; on 2026-09-08 the ruleset rejected an automation push that bypassed the required PR/`validate` path | Hosted ruleset configuration remains external platform state, but enforcement has direct observed evidence. |
| Governed monitoring scope | PASS | `organizations/w3c/admission.toml`, tier-aware runtime tests, `scope.html`, `data/scope.json` | Scope expansion remains a maintainer governance decision and must carry repository-specific evidence. |
| Tests/evidence/publication | PASS | validation workflow; production collect/persist/deploy run on 2026-09-08; `generated-observations` lineage | Workflow green does not make external taxonomy or admission claims authoritative. |
| Versioning | PASS | `VERSION` | Publication remains maintainer judgment. |

## Completion boundary

Repository-owned baseline controls are currently evidenced. GitHub-hosted settings remain external platform controls, but default-branch protection is no longer merely asserted: enforcement was observed when a direct automation push to `main` was rejected, and the publication design was corrected to preserve PR-only source governance.
