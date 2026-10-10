# Offline cross-source assurance rehearsal (#63 / #82)

The module `python -m trust_ecosystem_monitor.toip_cross_source_preview INPUT.json --output preview.html` accepts only explicitly marked **synthetic** fixtures with `schema_version=1`, `fixture_only=true` and `publication_mode=offline_test_only`. It produces a clearly marked **NOT FOR PUBLICATION** HTML preview. It is not invoked from the GitHub Pages workflow.

The fixture contains `observations` conforming to the cross-source evidence contract. Correlation requires authorized-record test flags, a shared curated subject ID and reviewable HTTPS source references. The preview never asserts that real Confluence scope or rights have been established. Its synthetic approval flag exists only to exercise the code path; it must not be interpreted as a production authorization mechanism.

Deterministic tests cover a synthetic two-source finding, unrelated records, GitHub-only coverage, rejected public mode, rejected nonfixture input, record-level denial and HTML escaping.

## Outstanding real-evidence integration

- Authoritative, dated Confluence scope and reuse decision (#63).
- Independently verified source-to-subject mapping and historical completeness/provenance (#63/#82).
- A **separate**, explicitly authorized production ingestion and publication path with approval provenance, coverage states, privacy review and representative link checks (#82).
- Live Pages verification (#81).

This increment validates rendering mechanics and failure behavior without prematurely publishing or misclassifying Confluence metadata.
