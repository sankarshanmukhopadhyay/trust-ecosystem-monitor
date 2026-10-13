# ToIP WG/TF-first report prototype

This tranche adds a tested WG/TF-first annual report section prototype without changing the production annual publication path.

## What the prototype does

`trust_ecosystem_monitor.toip_wgtf_report.render_wgtf_first_section()`:

- loads `data/trustoverip/wgtf-registry.json`;
- validates that the registry remains curated, incomplete and non-official;
- groups annual GitHub developments by candidate WG/TF mappings;
- preserves unmapped evidence under `Unmapped / unknown ToIP body`;
- preserves multiple candidate mappings instead of forcing one institutional owner;
- renders entity authority state, registry confidence and mapping confidence;
- fails visibly if the registry is invalid or unavailable.

## What the prototype does not do

It does not:

- assert an official ToIP WG/TF inventory;
- verify current charters, chairs, membership or lifecycle;
- verify LFX Calendar/Zoom meetings;
- admit Confluence records or publication rights;
- publish live GitHub-Confluence findings;
- alter the scheduled annual report renderer.

## Why not wire it into production immediately?

The annual report is already an operational publication surface. The WG/TF-first model is a reader-experience improvement, but it sits on a deliberately incomplete and non-authoritative registry. Keeping this as a tested prototype first avoids making the public CY report appear more institutionally authoritative than the evidence supports.

## Evidence

The behavior is tested in `tests/test_toip_wgtf_report.py`:

- mapped DTWG-style evidence appears in a candidate WG group;
- TSWG-style evidence appears in a candidate WG group;
- unmapped evidence remains visible;
- non-authority language is rendered;
- invalid registry input produces an explicit unavailable state, not silent fallback.

## Issue synchronization

- #122: advanced by adding a tested WG/TF-first reader grouping prototype.
- #80: not advanced; no LFX/Zoom acquisition or meeting verification.
- #63: not advanced; no Confluence source-use or publication-rights decision.
- #82: not advanced; no admitted cross-source findings.

## Next tranche

Wire `render_wgtf_first_section()` into `toip_annual.render()` after review of the prototype output, preserving the current limitations and ensuring existing annual report tests still pass.
