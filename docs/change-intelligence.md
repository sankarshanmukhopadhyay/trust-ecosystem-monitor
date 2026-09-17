# Change intelligence model

Trust Ecosystem Monitor derives two additional machine-readable intelligence layers from already-admitted GitHub evidence: semantic change classification and observed repository relationships.

These layers are **derived monitor metadata**. They do not replace upstream authority and do not assert that an upstream project uses the same classification or relationship terminology.

## Semantic change classification

Each consolidated change unit carries a `semantic_change` object.

The initial vocabulary is intentionally bounded:

- `specification`
- `protocol_semantics`
- `api`
- `schema`
- `governance`
- `authority`
- `security`
- `privacy`
- `lifecycle`
- `dependency`
- `interop`
- `implementation`
- `release`
- `editorial`
- `unknown`

Classification is deterministic and explainable. The current classifier records:

```json
{
  "type": "authority",
  "method": "deterministic-keyword-v1",
  "confidence": "moderate",
  "matched_terms": ["delegat"],
  "evidence_state": "derived"
}
```

If the available change-unit evidence does not support one of the bounded classes, the result remains `unknown` with `evidence_state: insufficient`. Unknown is not converted into a more convenient category.

The classifier is a routing and review aid, not a normative interpretation of the monitored project.

## Observed relationship graph

The snapshot also carries a `relationships` collection. A relationship is created only when an observed change unit references another repository already present in the same monitored profile.

Example shape:

```json
{
  "id": "tem-relationship-...",
  "source_repository": "example/source",
  "target_repository": "example/target",
  "relationship_type": "observed-reference",
  "claim_strength": "observed",
  "formal_dependency": false,
  "recognition_inferred": false,
  "authority_inferred": false,
  "source_change_unit": "toip-change-...",
  "semantic_change_type": "interop",
  "evidence": ["https://github.com/example/source/issues/10"],
  "evidence_state": "observed"
}
```

The graph deliberately separates **observation** from stronger claims.

An observed reference does not establish:

- a formal dependency;
- recognition or trust;
- authority or delegation;
- interoperability;
- conformance;
- transitivity;
- an obligation on either upstream project.

Those claims require stronger evidence and, where added later, should be represented as distinct relationship types with their own evidence rules.

## Co-movement is not a graph edge

The existing review-seam capability may flag related portfolios that both contain material activity in the same observation window. This remains useful as a review prompt.

However, simultaneous activity or a configured portfolio relationship does **not** create a repository relationship edge. The relationship graph requires observed repository-specific evidence.

This distinction prevents the monitor from turning review heuristics into unsupported ecosystem topology.

## Publication

Both structures are produced by the normal `analyze_snapshot()` path and therefore appear in the complete machine-readable snapshot at `data/latest.json` after collection/publication.

No new upstream write capability is introduced. Collection, admission, disposition and upstream-engagement boundaries remain unchanged.

## Intended extension path

This tranche establishes primitives for later capabilities such as:

1. stronger evidence-typed dependency edges;
2. cross-ecosystem relationships where explicit evidence supports them;
3. upstream-to-downstream change propagation;
4. persistent watch propositions;
5. compatibility-impact propositions;
6. relationship and change-topology visualisation.

Those capabilities should build on the present evidence model rather than infer stronger claims from repository proximity, naming, or co-movement.
