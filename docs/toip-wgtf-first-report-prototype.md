# ToIP WG/TF-first annual report section

This tranche wires the previously tested WG/TF-first report section into the production annual renderer.

## What the annual report now does

`trust_ecosystem_monitor.toip_annual.render()` now calls `trust_ecosystem_monitor.toip_wgtf_report.render_wgtf_first_section()` before the existing prioritized year-to-date developments table.

The section:

- loads `data/trustoverip/wgtf-registry.json`;
- validates that the registry remains curated, incomplete and non-official;
- groups annual GitHub developments by candidate WG/TF mappings;
- preserves unmapped evidence under `Unmapped / unknown ToIP body`;
- preserves multiple candidate mappings instead of forcing one institutional owner;
- renders entity authority state, registry confidence and mapping confidence;
- fails visibly if the registry is invalid or unavailable.

## What it still does not do

It does not:

- assert an official ToIP WG/TF inventory;
- verify current charters, chairs, membership or lifecycle;
- verify LFX Calendar/Zoom meetings;
- admit Confluence records or publication rights;
- publish live GitHub-Confluence findings;
- convert repository activity into institutional decisions.

## Rendering boundary

This is a reader-navigation layer over the existing annual GitHub observations. It is not a new authority source. The annual page still retains the repository-first, cross-source, source-ledger and limitations sections so that grouping does not hide evidence, force unmapped artifacts into a body, or make false completeness claims.

If the registry fails validation, the annual page renders an explicit unavailable state for the WG/TF-first view and leaves the repository-first evidence sections available.

## Evidence

The behavior is tested in `tests/test_toip_wgtf_report.py`:

- mapped DTWG-style evidence appears in a candidate WG group;
- TSWG-style evidence appears in a candidate WG group;
- unmapped evidence remains visible;
- non-authority language is rendered;
- invalid registry input produces an explicit unavailable state, not silent fallback;
- annual HTML includes the WG/TF-first section and still includes the existing evidence/limitations sections.

## Issue synchronization

- #122: advanced by wiring the tested WG/TF-first reader grouping into the annual report render path.
- #80: not advanced; no LFX/Zoom acquisition or meeting verification.
- #63: not advanced; no Confluence source-use or publication-rights decision.
- #82: not advanced; no admitted cross-source findings.

## Next tranche

A later tranche should verify the deployed Pages output after the scheduled/manual workflow regenerates the annual page, and then update #81 if the live route is confirmed.
