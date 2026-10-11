# ToIP intelligence convergence: navigation and substantive source evidence

## Canonical public route

The **Trust Over IP** monitoring overview at `/trustoverip/index.html` is the primary public entry point. It shows an explicit **Experimental intelligence · WIP** disclosure and one link to `/intelligence/toip/2026/`. The intermediate `/intelligence/toip/` landing now provides only a short disclosure and that year destination. The root ecosystem catalog no longer promotes GitHub-only `/monthly/` and Confluence intelligence as two equivalent destinations. Historical monthly URLs remain resolvable as supporting evidence/bookmarks, not top-level products.

The weekly ToIP site renderer inserts the WIP section when regenerating its overview. Both monthly publication workflows normalize old root navigation before readiness and deployment, so the links cannot drift between weekly and monthly workflows.

## Confluence source fidelity

The former K4 extractor selected the first few keyword-bearing paragraphs. The new `toip_discussion_blocks.extract_discussions` independently parses **the whole bounded page** (maximum 250 KB source), removes obvious repeated administration, scores eligible substantive paragraphs by technical/discussion cues, selects up to 8 relevant blocks, and restores original source order after relevance selection. Each block carries:

- source section and original source block number;
- a short **extractive** evidence statement labelled by question/proposal/action/decision-related *wording*;
- SHA-256 of its full parsed source block;
- up to 8 HTTPS links from that block (GitHub issues/PRs, Confluence, W3C, IETF and explicitly allowed reference domains);
- disclosed limitations: a discussion and referenced resource do **not** establish adoption, decision, assigned owner or a verified relationship.

This is materially more faithful to document content than a list of headings or keywords, **but not a comprehensive editorial summary**: the chosen passage may omit competing alternatives, qualifications or a conclusion elsewhere. Public source rights and source-owner approval remain separately gated.

The annual manifest retains selected bounded evidence and links without persisting full meeting minutes. Its historical monthly observation is immutable, while the displayed interpretation can use a newer inspected version from the source-version ledger, with a visible notice that historical evidence was preserved. A page with the same version but a changed extraction result creates an `interpretation_method_change`, **not** a false claim that the source page itself changed.

## Reproduction and acceptance

1. Run `python -m unittest discover -s tests` and validate the PR through `Validate`.
2. Once merged, manually dispatch `monthly-prototype.yml` **on main** to republish August/September and reconcile previously tracked records. Automated month-end publication remains in `monthly-intelligence.yml`.
3. Verify `/trustoverip/index.html`, `/intelligence/toip/`, and `/intelligence/toip/2026/`. Confirm that the landing links only to the CY report, the root does not present two independent monthly/intelligence destinations, and the CY report includes technical discussion blocks with associated references, not predominantly charters and member welcomes.
4. Review the generated annual manifest and Pages artifact; sample at least five technical discussion blocks against their linked source pages, including at least one external specification URL and one previously versioned Confluence page. Record false-positive or missing-context cases for further refinement.
5. Retain the source-use and deep summarization acceptance gates separately. CI proves deterministic parser and rendering behavior, not that all Confluence deliberations were exhaustively or accurately summarized.

**Backfill:** CY 2026 remains limited to months with collected manifests. January–July are not silently treated as empty and are not included by this navigation/synthesis tranche.
