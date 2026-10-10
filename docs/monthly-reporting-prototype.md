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

## Bounded two-month prototype

The draft PR includes `.github/workflows/monthly-prototype.yml`, which is intended to collect three explicitly scoped ToIP repositories for August and September 2026, compare their GitHub lifecycle events, and upload six JSON/Markdown artifacts. The workflow does not publish to Pages and cannot be represented as having run until a successful Actions run and artifact are verified.

The scope is **illustrative, not comprehensive**: `dtgwg-rahp-tf`, `dtgwg-cred-spec`, and `tswg-trust-registry-protocol`. These repository names must be validated for continued availability before treating the output as collected evidence.

Run comparison after both manifests exist:

```sh
python -m trust_ecosystem_monitor.monthly_compare reports/prototype/2026-08.json reports/prototype/2026-09.json --output reports/prototype
```

A successful bounded run is not the completion of issue #61. The final ToIP-wide reports require an agreed governed repository scope and available meeting evidence. Coverage must be disclosed separately for each.

## HTML report format

The prototype generates self-contained, responsive HTML files for the August report, September report, and comparison alongside Markdown and JSON. HTML is generated from the same evidence-backed Markdown, with untrusted text escaped and only HTTPS evidence links converted into anchors. It does not require a JavaScript runtime, external CSS, a site generator, or personal infrastructure.

For a standalone local conversion:

```sh
python -m trust_ecosystem_monitor.monthly_html monthly-prototype/2026-08-report.md --output monthly-prototype/2026-08-report.html
```

The GitHub Actions artifact is a preview delivery mechanism; publication to a ToIP-controlled site remains a separate governance and deployment decision.

## Expanded GitHub and LFX evidence scope

The expanded prototype selects public repositories by the ToIP profile's DTG, TSWG, AIMWG, CTWG and EGWG name prefixes, rather than the original three explicit repositories. This is a **prefix-scoped sample**, not a complete inventory of every ToIP GitHub repository; missing portfolios and nonconforming repository names remain out of scope. Collection completeness is assessed only within the selected scope. The GitHub token's permissions and rate limits may produce partial coverage, which must be reported.

LFX meeting data can be incorporated from an authorized JSON export. This does **not** claim a live LFX API integration. The expected export structure is:

```json
{
  "meetings": [
    {
      "started_at": "2026-09-12T14:00:00Z",
      "url": "https://example.org/meeting/1",
      "group": "DTG",
      "title": "Weekly call"
    }
  ]
}
```

The URL above is a schema illustration, not a claim of an actual meeting. Run:

```sh
python -m trust_ecosystem_monitor.monthly_lfx authorized-lfx-export.json --month 2026-09 --output monthly-prototype/2026-09-meetings.json
python -m trust_ecosystem_monitor.monthly_report monthly-prototype/2026-09.json --meetings monthly-prototype/2026-09-meetings.json --output monthly-prototype/2026-09-report.md
python -m trust_ecosystem_monitor.monthly_html monthly-prototype/2026-09-report.md --output monthly-prototype/2026-09-report.html
```

The importer reports LFX coverage as **partial** because a supplied export cannot prove the completeness of all LFX meetings. It records meeting listings as discussions, not decisions or deliverables. Until an authorized export is provided and included in the report-generation workflow, CI-generated reports continue to state LFX `not_checked`. Confluence is likewise not checked.

No credentials, attendance lists, private minutes, or restricted source text should be committed to the repository.

## Confluence metadata import

An authorized Confluence export can be converted into a monthly source manifest. The adapter requires `pages` with `updated_at` (ISO 8601 with timezone), `url` (HTTPS), `group`, `title`, and optional positive integer `version`. For example:

```json
{
  "pages": [
    {
      "updated_at": "2026-09-12T14:00:00Z",
      "url": "https://example.org/wiki/page/1",
      "group": "DTG",
      "title": "Working notes",
      "version": 3
    }
  ]
}
```

The URL is illustrative, not evidence of a real Confluence page.

```sh
python -m trust_ecosystem_monitor.monthly_confluence authorized-confluence-export.json --month 2026-09 --output monthly-prototype/2026-09-confluence.json
```

The adapter reports `partial` coverage and records **page updates**, not independently verified decisions. It does not claim live Confluence API access or a complete historical change log. The existing monthly report accepts a combined meeting manifest; separately imported Confluence and LFX manifests must be combined and validated before use.
