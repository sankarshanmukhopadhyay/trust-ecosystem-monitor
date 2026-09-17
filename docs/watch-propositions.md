# Persistent watch propositions

Trust Ecosystem Monitor can retain selected unresolved observations across collection windows as **watch propositions**.

A watch proposition is a monitor-owned governance artifact. It records that observed evidence justifies continued observation of a bounded question. It is not an upstream issue, alert, prediction, dependency declaration, compliance requirement, or authorization to act on another repository.

## Why watches exist

A weekly observation can identify a meaningful evidence state, such as a previously observed repository reference followed by a material change in the referenced repository with no later explicit follow-up observed in the referencing repository. Without retained state, the same question must be rediscovered on every run.

A watch gives that unresolved question a stable identity and explicit lifecycle.

## Creation rule

New durable watches are created only from `change_propagation` observations in the state:

```text
no_follow_up_observed
```

That propagation state already requires historical relationship evidence. Therefore a first baseline or `insufficient_history` observation cannot manufacture a durable watch.

The initial proposition type is:

```text
follow_up_after_referenced_change
```

Its meaning is deliberately narrow: continue observing whether the referencing repository later records a change that explicitly retains the reference after an observed change in the referenced repository.

## Stable identity

Watch identity is deterministic over:

```text
watch kind + referencing repository + referenced repository
```

A later collection run may update the watched trigger change or add evidence without creating a duplicate watch. The watch retains its original `created_at` value and accumulates evidence.

## Lifecycle

The bounded watch states are:

| State | Meaning |
| --- | --- |
| `waiting_external` | Sufficient evidence exists to retain the proposition; the observable trigger has not yet been seen. |
| `trigger_observed` | A qualifying later explicit follow-up is now observed. This is evidence to reassess, not automatic resolution. |
| `reassessment_required` | A trigger was retained from the prior observation and the proposition now requires human or separately governed reassessment. |
| `completed` | Reserved for an explicitly governed completion decision; the derivation engine does not auto-complete watches. |
| `insufficient_evidence` | Reserved for a retained watch whose evidence is no longer sufficient to support stronger lifecycle claims. New watches are never created from insufficient history. |

The automatic transition path implemented in this tranche is:

```text
no_follow_up_observed
        ↓
waiting_external
        ↓ qualifying follow-up
trigger_observed
        ↓ next retained observation
reassessment_required
```

There is intentionally no automatic transition from `reassessment_required` to `completed`.

## Machine-readable shape

A watch contains stable identity, proposition, trigger semantics, lifecycle state, provenance and authority boundaries. Example:

```json
{
  "id": "tem-watch-...",
  "kind": "follow_up_after_referenced_change",
  "proposition": "Observe whether example/source records later explicit follow-up after observed changes in example/target.",
  "state": "waiting_external",
  "source_repository": "example/source",
  "target_repository": "example/target",
  "trigger": {
    "type": "explicit_follow_up_observed",
    "condition": "A later change in example/source explicitly references example/target after the watched target change."
  },
  "source_relationship_id": "tem-relationship-...",
  "source_propagation_id": "tem-propagation-...",
  "trigger_change_unit": "toip-change-...",
  "created_at": "2026-09-17T10:00:00Z",
  "last_observed_at": "2026-09-17T12:00:00Z",
  "evidence": ["https://..."],
  "authority": {
    "owner": "trust-ecosystem-monitor",
    "scope": "derived_observation",
    "upstream_action_authorized": false
  }
}
```

## Authority and interpretation boundary

A watch does **not** establish:

- formal dependency;
- causation;
- compatibility impact or breakage;
- compliance or non-compliance;
- recognition or trust;
- authority or delegation;
- a prediction that an upstream repository will react;
- an obligation for an upstream repository to react; or
- authorization for the monitor to open issues, comment, modify or otherwise engage upstream.

Likewise, observing the trigger does not prove that the upstream change was caused by the watched event or that the underlying concern is resolved. It only changes the evidence state from waiting to reassessment.

## Relationship to findings and alerts

A **finding** is a material observation surfaced for review and disposition. A **watch** is retained observation state for a bounded unresolved proposition. They can coexist, but one does not automatically create or resolve the other.

This tranche also does not implement notification delivery. A watch becoming `trigger_observed` or `reassessment_required` is machine-readable state in the retained snapshot, not an external alert or message.

## Publication

`watch_propositions` is added by the normal public intelligence facade after semantic classification, relationship derivation and propagation analysis. It is therefore included in generated `data/latest.json` when the normal collection/publication workflow runs.

The existing admission, collection, finding disposition and upstream-engagement boundaries are unchanged.

## Deferred capability

Future work may add governed notification policy, manually authorized completion/disposition, cross-ecosystem watches, stronger dependency evidence, compatibility propositions and visualization. Those capabilities should consume the explicit watch state rather than infer obligations from repository activity.