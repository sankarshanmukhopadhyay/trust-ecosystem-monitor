# Confluence retrieval provenance and coverage

The metadata collector records a timezone-aware `retrieved_at` timestamp, search pages fetched, metadata lookups attempted, and whether it reached a terminal search page. These are **collection diagnostics**, not evidence of historical completeness.

A caller's `scope_approved=True` and `reuse_approved=True` flags represent a precondition asserted by the caller; the output now uses `scope_caller_approved=true` and `scope_verified=false` to avoid misrepresenting external authority. The sponsor declaration in PR #87 does not itself satisfy source-owner or republication requirements.

If the first search fails, `coverage=unavailable`. If any search response was received, `coverage=partial`, including normal termination: a last-modified query does not enumerate all historical changes or inaccessible records. A malformed or missing positive integer page version excludes the record with `missing_version_provenance`; a page update remains **metadata only**, not a governance decision. The returned timestamp is the acquisition instant, **not** the page-change timestamp. No source content, titles or access credentials are retained.

The collector remains disconnected from public report admission. Do not set publication flags based on these diagnostics.
