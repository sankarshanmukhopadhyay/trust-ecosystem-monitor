# Change intelligence model

Trust Ecosystem Monitor derives machine-readable intelligence layers from already-admitted GitHub evidence: semantic change classification, observed repository relationships, and bounded temporal change-propagation observations.

These layers are **derived monitor metadata**. They do not replace upstream authority and do not assert that an upstream project uses the same classification, relationship, or propagation terminology.

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

## Change propagation observations

The snapshot carries a `change_propagation` collection derived from change-unit timestamps, current observed-reference edges, and, where available, the immediately preceding snapshot.

Relationship direction remains literal: `source_repository` is the repository that explicitly referenced `target_repository`. Propagation analysis therefore asks a narrow temporal question:

> When the referenced repository changes, is there later observed activity in the referencing repository that retains the explicit reference?

The capability does **not** claim that the referenced repository is an upstream dependency. It does not infer causation from temporal sequence.

### `observed_follow_up`

An `observed_follow_up` requires:

1. an evidence-backed repository reference;
2. a change unit in the referenced repository; and
3. a later change unit in the referencing repository which carries that explicit reference.

Example shape:

```json
{
  "id": "tem-propagation-...",
  "state": "observed_follow_up",
  "referencing_repository": "example/source",
  "referenced_repository": "example/target",
  "relationship_id": "tem-relationship-...",
  "trigger_change_unit": "toip-change-...",
  "responding_change_unit": "toip-change-...",
  "trigger_timestamp": "2026-09-16T23:00:00Z",
  "response_timestamp": "2026-09-17T04:00:00Z",
  "trigger_semantic_change_type": "schema",
  "response_semantic_change_type": "schema",
  "evidence": ["..."],
  "interpretation": "Temporal monitor observation only ..."
}
```

The trigger may come from the immediately preceding retained snapshot. This permits observation across weekly collection windows without constructing an unbounded historical inference engine.

### `no_follow_up_observed`

Absence claims require prior evidence. The monitor emits `no_follow_up_observed` only when:

1. the previous snapshot contained an observed relationship between the repository pair;
2. the referenced repository has a current change unit; and
3. no later current change unit retaining that explicit reference is observed in the referencing repository.

This state means only **no qualifying follow-up was observed in the available evidence window**.

It does not mean:

- follow-up was required;
- the referencing repository is stale;
- an implementation is incompatible;
- a project is non-compliant;
- a dependency has broken; or
- any maintainer has failed to act.

### `insufficient_history`

When a current explicit reference exists but the monitor does not have an earlier referenced-repository change unit that can serve as a trigger, the observation remains `insufficient_history`.

A first baseline cannot produce a `no_follow_up_observed` claim because there is no prior relationship state against which absence can be assessed.

### Temporal ordering

A referencing change that predates a referenced-repository change is never treated as a response to that later change. Timestamps are therefore part of the executable evidence contract, not presentation metadata.

## Publication

Semantic classifications, relationships, and propagation observations are produced by the normal `analyze_snapshot()` path and therefore appear in the complete machine-readable snapshot at `data/latest.json` after collection/publication.

No new upstream write capability is introduced. Collection, admission, disposition and upstream-engagement boundaries remain unchanged.

## Intended extension path

The present model establishes primitives for later capabilities such as:

1. stronger evidence-typed dependency edges;
2. cross-ecosystem relationships where explicit evidence supports them;
3. persistent watch propositions;
4. compatibility-impact propositions;
5. propagation histories across multiple retained observations; and
6. relationship and change-topology visualisation.

Those capabilities should build on the present evidence model rather than infer stronger claims from repository proximity, naming, co-movement, or temporal sequence alone.
