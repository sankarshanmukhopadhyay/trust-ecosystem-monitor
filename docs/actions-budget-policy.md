# GitHub Actions budget and workflow policy

Review date: 2026-10-11. Related delivery trackers: #63, #65, #81, #82.

## Inventory and intended execution

| Workflow | Trigger policy | Purpose |
| --- | --- | --- |
| Validate | pull_request; workflow_dispatch | Required quality gate before merge. No automatic duplicate validation of the merged main commit. |
| Collect and publish weekly ecosystem briefs | weekly cron; manual dispatch; narrowly scoped changes to collection workflow, organization or relationship configuration | Only regular expensive GitHub API collector; also publishes weekly Pages. Shared serialized Pages concurrency. |
| Historical ToIP monthly evidence prototype | manual dispatch | Expensive two-month historical collection, render, generated-state persistence and Pages deployment. Execute for release verification, not on each merge. |
| ToIP public source reachability diagnostic | manual dispatch | Bounded public-source discovery only when a source decision requires new evidence; no admission or publication. |
| Verify published monthly HTML | manual dispatch | Verify *after* successful Pages deployment, not when code changes but published site has not changed. |

## Findings and constraints

- Recent history showed repeated Validate runs for both PR and immediately following main pushes; these are redundant for a squash-merge workflow with passing required PR checks.
- Preserve required branch protection on Validate. If main is updated without a PR, run manual validation or restore main-push validation before permitting such a practice.
- A successful weekly collection was observed in Actions on 2026-10-10; inspect its output and Pages deployment before treating #65's full acceptance as closed.
- Monthly and weekly Pages jobs share `group: pages` and `cancel-in-progress: false`. Monthly Pages state persists to `generated-observations`; weekly restores it. The generated branch is not a trigger for Validate.
- Weekly's selected-main-push trigger is **intentionally retained** for configuration changes; it can cause additional GitHub API consumption when those files change. Reassess if configuration changes become frequent.
- `workflow_dispatch` allows bounded, deliberate operational runs without automatic historical re-collection.
- Avoid re-running a failed Pages job attempt if the run already uploaded a `github-pages` artifact; dispatch a new run instead.

## Further optimization requiring measurement

Collect 30 days of Actions run count, elapsed duration, and failure/retry distribution by workflow, including GitHub API request/rate-limit telemetry. Distinguish **Actions runner minutes** from **GitHub API quota**: reducing PR validation duplicates saves runner starts but does not directly resolve installation API rate limits. Only after measurement consider caching, conditional weekly collection by changed source, repository-list snapshots, or separate collect/deploy stages. Do not skip provenance, fail-closed validation or publication checks to save minutes.

## Operational release checklist

1. PR validation succeeds and branch protection enforces it.
2. Run weekly collection only on schedule, approved configuration change or explicit dispatch.
3. Run monthly prototype for intended historical release; verify local readiness, generated-state preservation and Pages deployment.
4. Dispatch public verification only after deployment; record actual public routes in #81.
5. Synchronize #63/#65/#81/#82 with real workflow URLs, results, acceptance evidence and unresolved conditions.
