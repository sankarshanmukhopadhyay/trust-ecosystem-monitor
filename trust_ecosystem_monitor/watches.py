from __future__ import annotations

import hashlib
from typing import Any

WATCH_KIND = "follow_up_after_referenced_change"
WATCH_INTERPRETATION = (
    "Monitor-owned observation proposition only. A watch does not establish dependency, causation, "
    "compatibility impact, compliance, recognition, authority, prediction, breakage, or an upstream obligation. "
    "Trigger observation requires reassessment; it does not automatically resolve the proposition."
)


def _watch_id(source: str, target: str, kind: str = WATCH_KIND) -> str:
    digest = hashlib.sha256(f"{kind}|{source}|{target}".encode()).hexdigest()[:12]
    return f"tem-watch-{digest}"


def _latest_timestamp(*values: str | None) -> str | None:
    present = [str(value) for value in values if value]
    return max(present) if present else None


def _pair(item: dict[str, Any]) -> tuple[str, str] | None:
    source = item.get("referencing_repository") or item.get("source_repository")
    target = item.get("referenced_repository") or item.get("target_repository")
    if not source or not target:
        return None
    return str(source), str(target)


def _base_watch(observation: dict[str, Any], observed_at: str | None) -> dict[str, Any]:
    source = str(observation["referencing_repository"])
    target = str(observation["referenced_repository"])
    trigger_timestamp = observation.get("trigger_timestamp")
    created_at = trigger_timestamp or observed_at
    return {
        "id": _watch_id(source, target),
        "kind": WATCH_KIND,
        "proposition": f"Observe whether {source} records later explicit follow-up after observed changes in {target}.",
        "state": "waiting_external",
        "source_repository": source,
        "target_repository": target,
        "trigger": {
            "type": "explicit_follow_up_observed",
            "condition": f"A later change in {source} explicitly references {target} after the watched target change.",
        },
        "source_relationship_id": observation.get("relationship_id"),
        "source_propagation_id": observation.get("id"),
        "trigger_change_unit": observation.get("trigger_change_unit"),
        "trigger_timestamp": trigger_timestamp,
        "response_change_unit": None,
        "response_timestamp": None,
        "created_at": created_at,
        "last_observed_at": observed_at or trigger_timestamp,
        "evidence": list(dict.fromkeys(observation.get("evidence", []))),
        "authority": {
            "owner": "trust-ecosystem-monitor",
            "scope": "derived_observation",
            "upstream_action_authorized": False,
        },
        "interpretation": WATCH_INTERPRETATION,
    }


def build_watch_propositions(
    propagation: list[dict[str, Any]],
    previous: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> list[dict[str, Any]]:
    """Reconcile persistent watch propositions from bounded propagation evidence.

    New durable watches require `no_follow_up_observed`, which itself requires prior
    relationship evidence. `insufficient_history` never manufactures a watch.
    Existing watches retain stable identity across runs. Trigger evidence moves a
    waiting watch to `trigger_observed`; a retained triggered watch becomes
    `reassessment_required` on the next run rather than being auto-completed.
    """
    previous = previous or {}
    prior_watches = previous.get("watch_propositions", [])

    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for observation in propagation:
        pair = _pair(observation)
        if pair:
            by_pair.setdefault(pair, []).append(observation)

    prior_by_id = {watch.get("id"): watch for watch in prior_watches if watch.get("id")}
    results: dict[str, dict[str, Any]] = {}

    for prior in prior_watches:
        pair = _pair(prior)
        if not pair:
            continue
        source, target = pair
        watch_id = str(prior.get("id") or _watch_id(source, target))
        current = by_pair.get(pair, [])
        follow_ups = [item for item in current if item.get("state") == "observed_follow_up"]
        absences = [item for item in current if item.get("state") == "no_follow_up_observed"]
        state = str(prior.get("state") or "insufficient_evidence")
        watch = dict(prior)
        watch["id"] = watch_id
        watch["last_observed_at"] = observed_at or prior.get("last_observed_at")
        watch["interpretation"] = WATCH_INTERPRETATION

        if state == "completed":
            results[watch_id] = watch
            continue
        if state == "trigger_observed":
            watch["state"] = "reassessment_required"
            results[watch_id] = watch
            continue
        if state in {"reassessment_required", "insufficient_evidence"}:
            results[watch_id] = watch
            continue

        if follow_ups:
            response = max(follow_ups, key=lambda item: str(item.get("response_timestamp") or ""))
            watch["state"] = "trigger_observed"
            watch["source_propagation_id"] = response.get("id")
            watch["response_change_unit"] = response.get("responding_change_unit")
            watch["response_timestamp"] = response.get("response_timestamp")
            watch["last_observed_at"] = _latest_timestamp(observed_at, response.get("response_timestamp"), prior.get("last_observed_at"))
            watch["evidence"] = list(dict.fromkeys(prior.get("evidence", []) + response.get("evidence", [])))
        elif absences:
            absence = max(absences, key=lambda item: str(item.get("trigger_timestamp") or ""))
            watch["state"] = "waiting_external"
            watch["source_relationship_id"] = absence.get("relationship_id") or prior.get("source_relationship_id")
            watch["source_propagation_id"] = absence.get("id")
            watch["trigger_change_unit"] = absence.get("trigger_change_unit")
            watch["trigger_timestamp"] = absence.get("trigger_timestamp")
            watch["last_observed_at"] = _latest_timestamp(observed_at, absence.get("trigger_timestamp"), prior.get("last_observed_at"))
            watch["evidence"] = list(dict.fromkeys(prior.get("evidence", []) + absence.get("evidence", [])))
        else:
            watch["state"] = "waiting_external"
        results[watch_id] = watch

    # Only bounded absence observations create new durable watches. Positive
    # follow-up without a prior watch is evidence, not a reason to invent a watch.
    for observation in propagation:
        if observation.get("state") != "no_follow_up_observed":
            continue
        pair = _pair(observation)
        if not pair:
            continue
        source, target = pair
        watch_id = _watch_id(source, target)
        if watch_id in results or watch_id in prior_by_id:
            continue
        results[watch_id] = _base_watch(observation, observed_at)

    state_order = {
        "reassessment_required": 0,
        "trigger_observed": 1,
        "waiting_external": 2,
        "insufficient_evidence": 3,
        "completed": 4,
    }
    return sorted(
        results.values(),
        key=lambda item: (
            state_order.get(str(item.get("state")), 9),
            str(item.get("source_repository", "")),
            str(item.get("target_repository", "")),
            str(item.get("id", "")),
        ),
    )
