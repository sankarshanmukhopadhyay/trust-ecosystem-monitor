# Evidenced GitHub subject timelines

This document describes the first bounded C4 tranche from #122.

## Identity rule

A timeline exists only for the exact same canonical GitHub issue or pull-request
URL. TEM does not join separate artifacts because titles look similar, because
they share terms, or because events occurred near each other in time.

Supported identities are:

- `https://github.com/<owner>/<repo>/issues/<number>`
- `https://github.com/<owner>/<repo>/pull/<number>`

Query strings, fragments, non-GitHub hosts and other paths fail closed.

## Transition rule

Each transition is one observed GitHub lifecycle event retained in the immutable
annual monthly evidence:

- opening observed;
- closure observed, with resolution **not established**;
- merge observed, with adoption **not established**.

The event timestamp, observation month, source URL and evidence identifier remain
attached to each transition.

No state between observed events is reconstructed.

## Annual rendering

The annual report renders a bounded section for exact artifacts that have at
least two retained lifecycle observations. Every displayed transition links back
to the same canonical GitHub artifact.

The section is intentionally narrow. It does not infer:

- issue resolution from closure;
- specification or governance adoption from merge;
- decision authority;
- dependency or causation;
- equivalence between separate issues/PRs;
- cross-source relationships.

## Relationship to future C4 work

This tranche establishes the conservative identity and transition model.
Broader subject timelines would require an independently reviewed identity basis
stronger than title similarity or temporal proximity. Until such a basis exists,
separate GitHub artifacts remain separate timelines.
