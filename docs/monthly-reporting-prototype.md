# Historical monthly activity prototype

This experimental collector is independent of the existing weekly monitoring pipeline. It does not modify the retained weekly observation branch or publish to Pages.

## Run

Python 3.11+ and a GitHub token with read access to public repositories:

```sh
GITHUB_TOKEN=... python -m trust_ecosystem_monitor.monthly --org trustoverip --month 2026-08 --output reports/prototype
GITHUB_TOKEN=... python -m trust_ecosystem_monitor.monthly --org trustoverip --month 2026-09 --output reports/prototype
```

The collector writes one JSON evidence manifest and one Markdown listing per month. These are **GitHub-only partial evidence listings**, not completed organizational activity reports.

## Known limitations / next increment

- Collection currently scans the GitHub organization's public repositories and all issue/PR pages. It is not yet aligned with TEM's governed admission tiers and may be expensive for large repositories.
- Historical issue/PR open, close and merge timestamps are collected; comments, commits, review events, release events, and reopened history are not yet collected.
- Issue and PR endpoints expose current state and may not reconstruct historical intermediate transitions.
- GitHub API failures are surfaced per repository, but repository discovery failure stops collection.
- Confluence and LFX are explicitly `not_checked`; access and record availability must be verified before declaring coverage.
- No decision, deliverable, completion or WG/TF status should be inferred from event counts alone.
- Do not publish or circulate these reports as ToIP-authoritative publications.
- Before merge, verify DCO authorship/sign-off, run tests and review pagination/rate-limit behavior.

## Portability contract

Collection requires only an organization name, reporting month, output directory, and GitHub token. No maintainer-hosted service is required. The next increment should support ecosystem profile configuration and meeting-source adapters without changing existing weekly report semantics.
