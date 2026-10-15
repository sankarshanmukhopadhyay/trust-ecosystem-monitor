# C5 independent human evaluation

C5 evaluates whether TEM's source-linked intelligence is useful and safe for a
reader. The software prepares the evidence packet; it does **not** perform the
independent human review.

## Generate the packet

Use the retained annual manifest as input:

```bash
python -m trust_ecosystem_monitor.toip_human_evaluation \
  --manifest docs/intelligence/toip/2026/data/manifest.json \
  --json review/toip-human-evaluation.json \
  --markdown review/toip-human-evaluation.md
```

By default the packet samples August and September 2026. Selection is
deterministic for a given manifest.

## What the packet contains

The packet includes bounded GitHub artifact references and Confluence source
metadata. It does not copy Confluence source bodies or excerpts.

Confluence records are labelled `meeting_status=not_established` and
`authority_status=not_established` unless those questions are separately
resolved through the source-authority work.

## Human reviewer task

The reviewer records identity/date/independence basis and assesses each sample
for:

1. relevance;
2. important omission;
3. unsupported decision/adoption/meeting/authority claims;
4. source traceability;
5. reader comprehension.

The reviewer should record concrete corrections when a criterion is not
satisfied.

## Completion

C5 remains open until a genuinely independent human reviewer completes the
packet and the disposition is linked to #122. Model-generated commentary,
automated tests, or the packet generator itself are not substitutes for that
review.

#63, #80 and #82 remain authoritative for source rights, WG/TF/meeting
authority and cross-source admission respectively.
