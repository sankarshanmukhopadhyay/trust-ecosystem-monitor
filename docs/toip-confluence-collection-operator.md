# Bounded Confluence metadata acquisition operator procedure

This is a **read-only, nonpublication** acquisition procedure for #63. The CLI is not a live scheduled pipeline or report integration. It must not be used with fabricated approvals. A reviewer must independently verify the source-use evidence and actual reviewer identity; JSON flags and HTTPS URL strings are not proof.

1. Obtain a dated decision record in the format tested by `tests/test_toip_authorization_decision.py`, with `issuer_role=experiment_sponsor`, issuer `sankarshanmukhopadhyay`, `policy_basis=toip_experiment_2026_10_11`, permitted months, numeric `HOME` space ID `22970380`, permitted uses, effective dates, and independently verified authority and source-use fields. Do not include credentials in this file.
2. Obtain a **separate** reviewer record: `authorization_decision_id`, `source_use_compliance_verified=true`, `reviewer` (distinct from sponsor), and `review_evidence_url` exactly matching the decision's `independent_source_use_review_url`. The reviewer must actually assess source access, reuse, privacy, permitted fields and retention. The code only checks structural consistency.
3. Obtain a current revocation register JSON `{"revoked_ids":[]}`. The CLI cannot verify freshness; operators must independently establish it.
4. Run only after these independent checks, with files kept out of the repository if sensitive:

```sh
python -m trust_ecosystem_monitor.toip_confluence_collect \
  --decision local/decision.json \
  --source-use-review local/review.json \
  --revocation-register local/revocations.json \
  --month 2026-08 --month 2026-09 \
  --output local/confluence-aug-sep-acquisition.json
```

5. Inspect `coverage`, `diagnostics`, `search_pages_fetched`, `metadata_lookups_attempted`, `search_terminated_normally`, and each record's `source_id`, `space_id`, `version`, `url`. This collector deliberately reports **partial** even when pagination terminates; last-modified search is not a complete historical event inventory. Failed collection is **unavailable**.
6. Verify source URLs and versions independently, qualify curator subject mappings, and submit to the independent record-level admission procedure before any publication. This CLI always sets `publication_admitted=false`. Do not interpret a page update as a decision or an implementation.

**Negative tests:** `tests/test_toip_confluence_collect.py` rejects missing/mismatched reviewer records, sponsor self-review, revoked decisions, out-of-scope and duplicate months; unavailable fetch remains nonpublication. Component acquisition tests cover malformed search, duplicate pages, unsafe pagination and response budgets. These do not validate external reviewer authenticity or actual source-use rights.

**Operational limitation:** This command executes from a network-enabled environment and is not triggered automatically. Neither a successful invocation nor an uploaded artifact is a public cross-source report. The remaining report integration and publication assurance is tracked under #63/#82/#81.
