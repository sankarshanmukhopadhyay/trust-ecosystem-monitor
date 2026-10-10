# ToIP external-source scope reconciliation (10 October 2026)

**Status: provisional public-source evidence register; NOT an authorized collection or publication allowlist.** Related: [issue #63](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/63).

## What has been verified

- [Public diagnostic run #38017349744](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/runs/38017349744) verified the Confluence v2 space identity `22970380` → key `HOME`, name `Home` (`identity_verified=true`). The run also associated 22 August and 36 September 2026 **last-modified CQL matches** with this space. These are search matches, not governance events, and the unscoped search does not establish completeness.
- The [ToIP Steering Committee page](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22994826/Steering+Committee) is publicly under `HOME` and describes oversight of WG creation and approval of official deliverables. This is **public source evidence**, not API-level certification of the whole space.
- The [DTGWG page](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/257785857) and [AI & Human Trust WG page](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22982892/AI+Human+Trust+Working+Group) also use `HOME` paths, supporting its relevance to WG documentation.
- The [ToIP WG/TF formation guidance](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22974852/How+to+Propose+a+New+Task+Force+or+Working+Group) describes creating TF pages beneath parent WG/Steering Committee pages and WG home pages after approval. Thus page hierarchy and governance status cannot be inferred solely from a space key.
- The [ToIP calendar documentation](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22983578/Calendar+of+ToIP+Meetings) points to LFX for recurring All Member, Steering Committee, WG and TF meetings. It includes participation/IPR caveats. Public calendar availability does not establish meeting occurrence, minutes or publication rights.

## Candidate scope register

| Candidate | Public evidence | Technical verification | Authority/completeness | Permission to publish records | Decision |
| --- | --- | --- | --- | --- | --- |
| Confluence `HOME` (`22970380`) | Steering Committee and WG public pages | Space ID, key and name verified by live v2 metadata; 58 bounded CQL matches resolved | **Not established** as exhaustive ToIP scope | **Not established** for automated republication | Candidate for reconciliation only |
| Other ToIP Confluence spaces | Not yet enumerated exhaustively | Not checked | Unknown | Unknown | Do not presume absent |
| LFX ToIP calendar | Linked by official ToIP wiki | Public calendar HTTP 200 | Calendar/group membership and historic completeness not established | Not established | Reachability only |
| LFX meeting notes, recordings, attendance | Calendar and wiki describe meeting-related resources | No authorized machine-readable historic acquisition | Not established | Not established; possible restricted content | Exclude from public ingestion |

## Required source-owner reconciliation

1. Obtain an authoritative, dated ToIP inventory of Confluence spaces and relevant Steering Committee/WG/TF hierarchies, including archived/migrated records and the applicability period for August–September 2026.
2. Determine whether `HOME` is the sole in-scope space, whether there are separate spaces or restricted areas, and which are publicly accessible versus member-only.
3. Confirm authorized LFX ToIP organization/group/calendar identifiers, API/export support, and historical coverage. Treat scheduled, held, recorded and minuted meetings separately.
4. Establish rights for automated acquisition, storage, retention, derived reporting and **public republication**, distinguishing page metadata from bodies, attachments, recordings, attendee data and minutes. WG-specific IPR terms do not automatically license every item in the wiki or calendar.
5. Record an approved source inventory with issuer, date, evidence links, scope, exclusions, access mechanism and expiry/review condition. Only then use it to filter historical acquisition and publish external-source findings.

## Interim operating rules

- Continue **GitHub-only** monthly publication; do not integrate unapproved external-source records.
- Keep `scope_verified=false` and `coverage=sample_only` for historical CQL search even though technical page-to-space mapping succeeded.
- Do not classify a page update as a decision or a calendar listing as a held meeting.
- Do not upload page bodies, personal records, access tokens, meeting links containing access codes, or restricted documents into public CI artifacts.
- If owner confirmation cannot be obtained, publish a precise **coverage limitation** rather than manufacturing source completeness.

## Next evidence gate

The next executable step is an **inventory and authorization decision**, not further unconstrained scraping. A bounded public inventory can aid candidate discovery, but source-owner confirmation is needed to declare the ToIP source scope authoritative. Track owner responses and explicit blockers in [#63](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/issues/63).
