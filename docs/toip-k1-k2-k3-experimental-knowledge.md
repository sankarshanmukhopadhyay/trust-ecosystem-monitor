# K1–K3: Experimental August–September knowledge publication

## Scope and decision

The purpose of these increments is to make TEM's already-collected evidence intelligible to readers. **This is an independent, non-authoritative experiment**, not a replacement for source-use review, an assured report, or a reconstruction of historical decisions. Calendar-year expansion is deferred.

- **K1 — Content-grounded Confluence descriptions:** The anonymous public collector reads a bounded page-body representation from the HOME space, parses short section-level text, and emits *original, deterministic lexical abstracts* identifying recurring terms and distinguishing question/proposal/action/decision **wording cues**. It neither republishes body text nor concludes that a decision/action was approved. Each abstract carries the SHA-256 of the underlying parsed source section and the page's canonical URL, version and timestamp. Source bodies are discarded; only derived descriptions enter rendered pages.
- **K2 — Cross-source links:** A GitHub artifact hyperlink explicitly found in Confluence content is marked `explicit_reference` only when that exact GitHub URL appears among the collected monthly lifecycle artifacts. A shared-title/section vocabulary overlap of at least three specific terms is marked `candidate_topic_overlap` with the matching terms disclosed. Absence of a link is not absence of a relation. Neither kind establishes governance approval, causation, common authority, or even contemporaneous activity.
- **K3 — Monthly publication/readiness:** The August/September experimental combined page keeps TEM weekly classifier-derived grouped workstream developments, adds Confluence descriptions and explicit/candidate links, and surfaces a complete GitHub evidence register. HTML escaping and schema checks are enforced; the Pages readiness gate verifies all three knowledge sections when the combined pages are present. Run `python -m unittest discover -s tests` before deployment.

## Technical boundaries

The Confluence search is based on **last-modified pages** and current public page-body versions. Consequently, a current body may contain post-August/September edits. Text, source headings and relationship references **must not** be presented as contemporaneous historical meeting evidence unless a version-qualified historical body is separately obtained.

The content extraction is lexical, not deep semantic summarization. A phrase containing “decision” or “agreed” is a **language signal**, not a validated decision. Extracted keyword lists convey subject matter but cannot reliably reconstruct the argument, dissent, conclusion, parties or follow-ups. Detailed substantive summaries, if required, need a separate source-grounded, reviewed claim-extraction method. SHA-256 supports provenance checks against the same parsed source content; hashes alone do not establish historical authenticity.

The collector bounds responses to 1 MB, bodies to 250 KB, and monthly discovery to at most 40 pages with at most six section abstracts per page. HTTP acquisition is allowlisted to the named Confluence host, CQL search endpoint and numeric page endpoints. Unavailable pages are disclosed. Retrieved content is untrusted; HTML is escaped in output and no retrieved instructions are executed. Current source-use terms are **not independently verified**; experimental output should be reviewed before wider reuse.

## Acceptance ledger

- [x] K1: bounded page content interpretation, page links/version, section text hashes, evidence-wording classification.
- [x] K2: exact-link observed references and separately labelled contextual candidates.
- [x] K3: renderer and local readiness checks integrated, regression tests supplied.
- [ ] K3: post-merge monthly manual workflow run successful on main.
- [ ] K3: public Pages routes retrieved and individually inspected for meaningful August/September content and accurate source links.
- [ ] Deep content claims: reviewed summaries of substantive meeting discussion and validated decisions/actions.
- [ ] Assured admission: third-party source-use and publication eligibility confirmed separately.

## Runbook

1. Verify PR CI passes the entire test suite. Squash-merge.
2. To honor the repository's Actions budget policy, dispatch [Historical ToIP monthly evidence prototype](https://github.com/sankarshanmukhopadhyay/trust-ecosystem-monitor/actions/workflows/monthly-prototype.yml) **once on main**. The workflow collects the two GitHub months, performs bounded public Confluence sampling, invokes K1/K2 rendering, validates the local Pages publication and deploys.
3. Verify `/intelligence/toip/2026-08/experimental-combined.html` and `/intelligence/toip/2026-09/experimental-combined.html` by HTTP GET; inspect sections, page-level citations, source timestamps and number of missing records. Correct any discrepancies through a new PR and re-verify.
4. Keep #63 (source-use), #82 (correlation), and #81 (Pages) open for independently outstanding evidence; record hashes and workflow URLs in the issues.

**Do not mark the entire knowledge-generation objective complete merely because CI passes.** The reports need a source-grounded editorial quality review against actual GitHub/Confluence contents.
