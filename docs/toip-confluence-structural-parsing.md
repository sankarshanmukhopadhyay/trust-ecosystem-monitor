# ToIP Confluence structural parsing

This document describes the bounded B3 parser work from #122: diagnostic structural parsing for bounded ToIP Confluence HTML and its integration into the content-signal collector.

## Purpose

The parser helps identify structural evidence units such as agenda-like headings, table rows, macro-like panels and linked resources. It is intended to support later review and evidence modelling. It is not source admission and it is not reader-facing synthesis.

## Output boundary

All output is `diagnostic_only` unless a separate source-admission process says otherwise.

The parser does not infer:

- that a meeting was held;
- that a page is an official meeting record;
- that a decision, approval, consensus or adoption occurred;
- that ToIP institutional authority exists for the page or block;
- that Confluence content may be republished;
- that a GitHub link proves implementation, adoption or dependency.

Decision-like or meeting-like wording is recorded only as a language signal and an unsupported claim marker, for example `decision_or_adoption_not_established` or `meeting_occurrence_not_established`.

## Structural block model

Each extracted block carries:

- `block_id`;
- `block_kind`, such as `paragraph`, `table_row` or `macro_like_block`;
- `heading_path`;
- `text_basis_sha256`;
- `links`;
- `github_references`;
- `external_references`;
- `language_signals`;
- `unsupported_claims`;
- `admission_state: diagnostic_only`;
- `interpretation_limits`.

The hash basis allows later comparison without republishing full source text.

## Collector integration

`toip_confluence_content_signals.collect()` attaches parser output under each page as:

```text
structural_diagnostics
```

This field is diagnostic metadata. It is carried next to existing `topic_headings`, `section_abstracts`, `discussion_blocks` and `github_references`, but does not replace them and does not change existing annual reader rendering.

The integration is intentionally conservative:

- existing discussion-block and section-abstract behavior remains intact;
- page classification remains based on existing discussion-block logic;
- structural diagnostics stay `diagnostic_only`;
- decision-like language stays an unsupported diagnostic marker;
- reader pages do not render the diagnostic payload as an admitted finding.

## Relationship to #63 and #82

This parser does not resolve source access, reuse, publication rights or cross-source admission. Those remain owned by #63 and #82.

B3 improves structure extraction so a later reviewed process can decide whether any diagnostic block should become admitted evidence. Until then, the output remains a diagnostic artifact only.

## Relationship to reader pages

This tranche does not change the ToIP annual reader product. Reader-facing synthesis should only use these blocks after source-use, admission and review gates are satisfied.


## Diagnostic evidence-linked synthesis

The parser now exposes a deterministic diagnostic handoff through
`synthesize_diagnostic_evidence()`. The handoff deliberately carries no source
body, excerpt or free-form generated summary. Each item contains only source and
structure metadata required for later review:

- evidence/block identifier;
- page identifier and source URL;
- page version;
- structural block kind and heading path;
- SHA-256 basis hash;
- permitted source references;
- language signals and unsupported-claim markers;
- `admission_state: diagnostic_only`;
- `claim_state: not_admitted`.

The bounded content-signal collector exposes this as
`diagnostic_evidence_synthesis` next to `structural_diagnostics`. Existing
reader rendering does not consume either field as an admitted finding.

## Edge-case coverage

Synthetic parser tests cover:

- table content nested inside macro-like panels;
- multiple references in one structural unit;
- relative Confluence links;
- duplicate GitHub references;
- disallowed external hosts;
- decision-like and meeting-like wording;
- malformed diagnostic handoff input.

This coverage is intentionally synthetic/minimized so parser assurance does not
depend on republishing third-party Confluence bodies.

## Review/admission handoff

B3 parser processing ends at the diagnostic handoff. Promotion beyond
`diagnostic_only` / `not_admitted` requires a separate reviewed process.

- #63 owns source access, reuse, retention and publication-rights questions.
- #82 owns cross-source correlation/admission and the evidentiary basis for any
  record-level relationship or finding.
- Reader-facing publication must not treat parser output alone as evidence that
  a meeting occurred, a decision was made, work was adopted, or institutional
  authority exists.

With the structural parser, collector integration, edge-case fixtures and
diagnostic evidence-linked handoff in place, B3 can be treated as complete **as
a parser capability**. Source admission and public claim authority remain
separate open concerns.
