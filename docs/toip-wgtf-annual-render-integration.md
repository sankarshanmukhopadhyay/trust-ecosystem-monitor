# WG/TF-first annual render integration

This note records the production integration of the WG/TF-first reader grouping into the ToIP annual report renderer.

## Integration point

`trust_ecosystem_monitor.toip_annual.render()` calls `render_wgtf_first_section(state)` immediately after the annual metrics and before the existing prioritized year-to-date developments table.

This placement is intentional:

- the report first establishes annual scope and evidence volume;
- the WG/TF-first section gives readers an early candidate body-oriented navigation layer;
- the existing repository-first, cross-source, source-ledger and limitation sections remain visible and auditable.

## Preserved boundary

The integration does not change the evidentiary status of the report. The WG/TF section remains:

- candidate reader grouping;
- based on the curated incomplete registry;
- non-official;
- non-authoritative;
- not a charter, meeting, source-owner or decision record.

Unmapped evidence remains visible. Multiple candidate mappings are preserved. If the registry cannot be loaded or validated, the annual page renders the WG/TF section as unavailable rather than silently falling back to a misleading grouping.

## Validation

Regression coverage lives in `tests/test_toip_wgtf_report.py` and verifies that the annual HTML now includes:

- `WG/TF-first candidate view`;
- mapped DTWG and TSWG candidate groups;
- unmapped evidence;
- non-authority language;
- the existing prioritized and evidence/limitations sections.

## Issue synchronization

This advances #122 by wiring the tested WG/TF-first reader model into the annual render path.

It does not complete #80, #63 or #82 because it does not verify LFX/Zoom meetings, resolve Confluence source-use/publication rights or admit live cross-source findings.
