from __future__ import annotations

import tomllib
from pathlib import Path

from .admission import AdmissionDecision, make_admission_decision


def load_admission_policy(path: str | Path) -> dict[str, AdmissionDecision]:
    path = Path(path)
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if not payload.get("schema_version") or not payload.get("policy_id"):
        raise ValueError(f"admission policy {path} requires schema_version and policy_id")

    decisions: dict[str, AdmissionDecision] = {}
    for raw in payload.get("repositories", []):
        repository = str(raw.get("repository", "")).strip().lower()
        if not repository or "/" not in repository:
            raise ValueError(f"admission policy {path} contains an invalid repository")
        if repository in decisions:
            raise ValueError(f"admission policy {path} contains duplicate repository: {repository}")
        decisions[repository] = make_admission_decision(
            state=str(raw.get("state", "")),
            tier=str(raw.get("tier", "")),
            rationale=raw.get("rationale", []),
            evidence=raw.get("evidence", []),
            method=f"policy:{payload['policy_id']}",
        )
    return decisions
