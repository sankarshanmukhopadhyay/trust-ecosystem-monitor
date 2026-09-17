from __future__ import annotations

from typing import Any

from .intelligence_backend import *  # noqa: F401,F403
from .intelligence_backend import analyze_snapshot as _analyze_snapshot_without_watches
from .watches import build_watch_propositions


def analyze_snapshot(snapshot: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Analyze a snapshot and compose persistent monitor-owned watch propositions."""
    result = _analyze_snapshot_without_watches(snapshot, previous)
    result["watch_propositions"] = build_watch_propositions(
        result.get("change_propagation", []),
        previous=previous,
        observed_at=result.get("generated_at"),
    )
    return result
