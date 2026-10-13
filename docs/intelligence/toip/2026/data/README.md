# ToIP CY 2026 generated data

This directory is the machine-ingestion companion to the rendered ToIP CY 2026 annual intelligence page.

## Canonical files

| File | Purpose |
| --- | --- |
| `manifest.json` | Canonical machine-readable annual intelligence manifest generated on the `generated-observations` branch. |
| `schema.json` | JSON Schema for the `tem-cy-intelligence-v1` manifest shape. |

The public HTML page at `/intelligence/toip/2026/` is a rendered view. ML tooling should ingest `manifest.json`, not scrape the HTML.

## Source branch

The currently deployed generated files live on the `generated-observations` branch under:

```text
docs/intelligence/toip/2026/data/
```

## Contract document

See:

```text
docs/toip-cy-intelligence-data-contract.md
```

for schema semantics, source boundaries, safe ML uses, unsafe inferences, and operational references.

## Interpretation boundary

This data is independent TEM output. It is not an official ToIP inventory, meeting record, source-owner authorization, decision register or cross-source finding surface.

Backfilled CY months are GitHub-only observations and intentionally do not expand Confluence, LFX, Zoom, meeting or cross-source claims.
