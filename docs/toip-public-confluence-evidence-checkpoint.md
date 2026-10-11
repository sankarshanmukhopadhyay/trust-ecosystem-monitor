# ToIP Confluence public-source discovery checkpoint (11 October 2026)

**Classification: discovery-only; NOT admitted publication evidence.** This checkpoint records publicly indexed page references found without an Atlassian app or authenticated Confluence session. It is not a complete August/September inventory, a source-use decision, a historical version reconstruction, or a curator's independent review.

## Independently discoverable public page references

| Nominal meeting date | Page ID | Public page URL | Bounded finding |
| --- | --- | --- | --- |
| 2026-08-13 | 1061552129 | https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/1061552129/2026-08-13+AIM+WG+Meeting+Notes | Search-indexed AIM WG meeting-note page; visible title and meeting date; indexed update display is not a verified event timestamp. |
| 2026-09-03 | 1123844097 | https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/1123844097/2026-09-03+AIM+WG+Meeting+Notes | Search-indexed AIM WG meeting-note page; visible title and meeting date; no version-bound change event established. |
| 2026-09-17 | 1168211969 | https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/1168211969/2026-09-17+AIM+WG+Meeting+Notes | Search-indexed AIM WG meeting-note page; visible title and meeting date; no version-bound change event established. |
| 2026-09-24 | 1184464897 | https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/1184464897/2026-09-24+AIM+WG+Meeting+Notes | Search-indexed AIM WG meeting-note page; visible title and meeting date; no version-bound change event established. |

**Source:** Public search-engine indexing of the cited `lf-toip.atlassian.net` pages, inspected 2026-10-11. Some pages are discoverable via search results even when direct REST API requests are inaccessible to a given runtime. The references are *candidates*, not admitted `page_update` events.

## Source-use and access boundary

- Public discoverability of these specific pages is evidence that a no-app research route is plausible, **not** evidence that every HOME page or the REST API is anonymously accessible.
- Atlassian's [Cloud anonymous-access guidance](https://support.atlassian.com/confluence-cloud/docs/set-up-public-access/) explains that site and space permissions jointly govern anonymous access; individual restrictions can still apply.
- Neither sponsor authorization nor search indexing independently proves rights to reproduce page bodies or to automate bulk acquisition.
- This checkpoint deliberately excludes page bodies, meeting attendee lists, author profiles, recordings, credentials, and claims about decisions.
- A nominal meeting date in a title is **not** the timestamp of a page modification. Do not promote these entries into historical change observations without version and event-time evidence.

## Acceptance path without an app

1. Run the existing manual `ToIP public source reachability diagnostic` workflow against the current main commit. Preserve the run URL and sanitized August/September discovery artifacts; do not infer coverage from the four search-indexed examples.
2. Establish actual anonymous page/API access and the applicable reuse/automated-access conditions for this bounded metadata purpose. Document reviewer, date, evidence, scope and exclusions in the source-use dossier. Do not manufacture a positive source-use review record.
3. If permitted, execute the already implemented gated acquisition and curator/independent qualification for version-bound observations in each month; preserve failures and completeness diagnostics.
4. Only feed actual independently admitted manifests into `toip_combined_publication`. If either month remains unadmitted, retain GitHub-only intelligence and describe Confluence as **publicly discoverable, not admitted**.
5. Verify generated and live public combined report URLs, review links, period coverage, and Pages persistence. Close #63/#82 only with the corresponding evidence.

**Current conclusion:** no Atlassian app is demonstrably necessary for finding public candidate pages. An independently admitted two-month Confluence dataset and published combined report have **not** yet been established.
