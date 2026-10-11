# TEM monthly intelligence: K4–K7 operational release

Status: **experimental, source-linked and non-authoritative**. The target is a reader-useful monthly product, not event-volume reporting. Prior benchmark: August/September 2026 run #38113703306, which was source-rich but insufficiently prioritized and repetitive.

## Implementation and acceptance

- **K4 content selection:** `toip_content_interpretation.extract` filters recurring antitrust/IPR, licensing, Zoom, logistics and administrative passages before composing concise descriptions of propositions, questions and topics. It retains a SHA-256 hash for every interpreted source section, never the full source body. `toip_confluence_content_signals.collect` records whether each page is substantive, administrative or content-poor. These are *conservative lexical interpretations*, not verified meeting minutes, outcomes or decisions.
- **K5 prioritization:** `toip_monthly_editorial.priority` uses TEM's existing weekly semantic classification of GitHub change units. 'Review first' requires both a directly observed cross-source hyperlink and a consequential topic; 'Notable' requires an observed merge in a non-editorial topic. Other activity is contextual. This is **attention order, not severity, risk acceptance, approval, implementation completeness or consequence**. Only explicitly linked GitHub artifacts are used to strengthen a review signal.
- **K6 presentation:** `toip_monthly_editorial.present` imports the existing `site_backend.STYLE`, renders an executive brief, TEM metric panels, prioritized-development table, substantive Confluence source/version table, cross-source review seam table and workstream pulse. Full underlying activity is retained as an expandable audit appendix. Tables have labelled header cells and responsive horizontal overflow.
- **K7 operations:** new `.github/workflows/monthly-intelligence.yml` runs once monthly (02:40 UTC, second day), computes the **previous completed month** from UTC's first-of-month boundary, and collects it once. The workflow validates code, restores the generated site, renders the selected month, runs the publication readiness gate, persists the generated site and deploys Pages. Manual dispatch remains available. The expensive historical August/September prototype remains manual, respecting its pre-existing execution-budget policy. All scheduled runs share the Pages concurrency group.

## Bounded interpretation and information rights

Current public Confluence bodies can postdate their nominal CQL last-modified reporting month. The software cannot infer the actual date of discussion or recreate version-at-month-end from today's page content. Every source includes its current page/version link; the report visibly warns about temporal ambiguity. It does not claim a source is freely licensed just because anonymously accessible. Independently verified source-use permission and richer review of high-materiality content remain separate publication/assurance concerns.

No LLM claims are automatically inferred or accepted in CI. Source material and instructions are never executed. Substantive descriptions intentionally state that a record contains a proposal, question or discussion rather than asserting a decision. They are *provisional subject-oriented abstracts*, not yet the same as a fully reviewed narrative synthesis.

## Testing

Run `python -m unittest discover -s tests`. The new tests cover boilerplate suppression, generated language provenance, priority interpretation, shared TEM table styling, cross-source evidence, schedule cadence and idempotent index updates. Existing K1–K3 tests must remain green.

For acceptance, manually run `monthly-prototype.yml` on main after merge to regenerate August and September; inspect both generated HTML pages, especially whether the Confluence main table excludes antitrust/IPR notices, and audit at least one high-priority item against GitHub + Confluence sources. CI and readiness checks alone cannot certify substantive editorial quality. The monthly schedule will first collect the most recently completed month when it fires; it does **not** backfill CY 2026.

## Exclusions and remaining diligence

- Not a validated formal severity scoring framework; review priority remains heuristic.
- No historical Confluence version reconstruction or definitive attribution of meeting decisions.
- No source owner's independent rights clearance; assured cross-source publication remains gated.
- Not an automatic external editorial endorsement. Human evaluation of sampled high-materiality summaries is necessary before treating the intelligence as actionable governance evidence.
