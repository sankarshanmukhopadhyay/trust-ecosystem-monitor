# Experimental ToIP monthly knowledge synthesis

Status: **experimental, non-authoritative**. Scope: August and September 2026 only; a calendar-year extension is deliberately deferred until these pages communicate developments and limitations usefully.

## Data-to-knowledge processing

1. Historical GitHub collection emits individually source-linked issue/PR lifecycle observations.
2. `toip_monthly_knowledge.build_developments` consolidates repeated lifecycle events for the **same repository, kind and canonical artifact URL**. This avoids counting an opened-and-merged PR as two distinct developments.
3. The monthly analyzer imports `intelligence_backend.classify_semantic_change`, the **existing weekly TEM deterministic semantic classifier**, instead of creating a new taxonomy. Classification is heuristic, not a project's own authoritative description.
4. Developments are grouped by existing monthly portfolio grouping and semantic classification. Repeated terms are shown as **candidate topical proximity**, not relationships, dependency or shared causation. Top groups are surfaced first; all others remain accessible in the expandable evidence register.
5. A bounded anonymous CQL query locates Confluence pages *last modified during the month*. For each of at most 40 sampled pages, the read-only collector retrieves public v2 storage-format HTML, validates HOME space ID `22970380`, extracts up to eight brief H1–H3 headings, and discards the full content immediately. It retains only title, canonical source URL, version number/time, headings and extraction status **in memory**. Source content, author identities, comments, attachments and bodies are not published or persisted.
6. The combined pages display these headings as **recorded topics**, not summaries of assertions made in the body. They explicitly state when substantive discussion cannot be summarized. A last-modified hit is not a meeting date, a historical event log, a decision, or proof of publication rights.

## Exact limitations and next fidelity increment

This implementation materially improves readability and evidence organization but **is not full content-aware knowledge extraction**: headings cannot establish what participants said, decided, agreed or rejected. Reliable claims about Confluence discussion require an additional reviewed, provenance-linked claim extraction stage and applicable source-use determination. The current public source-use dossier remains NOT CLEARED for assured publication. No experimental evidence is promoted to `publication_admitted=true`.

GitHub source manifests contain titles and lifecycle timestamps but not issue body text, PR patches or linked discussions. Grouping can support observations of merges, closures and topics; it cannot establish why a PR was merged, project adoption, interoperability, or consequences. Related-title terms do not create graph edges. Monthly report completeness is bounded by configured repository prefixes.

## Operator / repeatability

The existing manual workflow `.github/workflows/monthly-prototype.yml` regenerates both months and invokes `python -m trust_ecosystem_monitor.toip_experimental_combined --github-dir monthly-prototype --site docs/intelligence/toip`. The generated pages remain `intelligence/toip/2026-08/experimental-combined.html` and `2026-09/experimental-combined.html`.

The collector is deliberately bounded to one CQL batch, at most 40 page requests per month, and a 1 MB response cap. Unexpected source identity fails individual page extraction, not source admission; unavailable content is explicitly reported. If aggregate HOME provenance fails, the combined page fails closed. The results are snapshots taken at generation time, **not historical reconstruction**. Because a current page body is fetched, it might reflect edits made after the selected month, and must not be represented as a contemporaneous August/September text snapshot.

Local tests: `python -m unittest discover -s tests`. Check output for (a) meaningful grouped GitHub developments, (b) bounded page-heading topic signals and canonical page links, (c) no false governance conclusions, (d) accurate sample/unavailable counts, and (e) source-linked evidence.

## Acceptance assessment

- [x] Multi-event GitHub artifacts consolidated; evidence links retained.
- [x] Weekly TEM semantic taxonomy reused; deterministic explainability.
- [x] Portfolio/topic narratives and full evidence register.
- [x] Bounded content-derived Confluence heading signals with page-level provenance.
- [x] Regression tests for grouping, provenance, HTML escaping, source identity, period binding.
- [ ] Verified page-body discussion summaries; headings are insufficient.
- [ ] Evidence-backed GitHub/Confluence cross-source subject correlation.
- [ ] End-to-end live public page content verification after workflow deployment.
- [ ] Independent Confluence source-use permission/assured record admission.

These unchecked items are substantive, not cosmetic; do not mark the *full* data-to-knowledge goal complete based on this first incremental implementation.
