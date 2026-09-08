from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ADMISSION_STATES = frozenset({"included", "watch", "review", "excluded"})
COLLECTION_TIERS = frozenset({"core", "related", "watch", "inventory"})

ALLOWED_TIER_BY_ADMISSION = {
    "included": frozenset({"core", "related"}),
    "watch": frozenset({"watch"}),
    "review": frozenset({"inventory"}),
    "excluded": frozenset({"inventory"}),
}


@dataclass(frozen=True)
class AdmissionDecision:
    state: str
    tier: str
    rationale: tuple[str, ...]
    evidence: tuple[str, ...]
    method: str

    @property
    def deep_collection_allowed(self) -> bool:
        return self.state == "included" and self.tier in {"core", "related"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "tier": self.tier,
            "rationale": list(self.rationale),
            "evidence": list(self.evidence),
            "method": self.method,
            "deep_collection_allowed": self.deep_collection_allowed,
        }


def make_admission_decision(
    *,
    state: str,
    tier: str,
    rationale: tuple[str, ...] | list[str],
    evidence: tuple[str, ...] | list[str] = (),
    method: str = "policy",
) -> AdmissionDecision:
    state = state.strip().lower()
    tier = tier.strip().lower()
    rationale_values = tuple(str(value).strip() for value in rationale if str(value).strip())
    evidence_values = tuple(str(value).strip() for value in evidence if str(value).strip())
    method = method.strip()

    if state not in ADMISSION_STATES:
        raise ValueError(f"unsupported admission state: {state or '<empty>'}")
    if tier not in COLLECTION_TIERS:
        raise ValueError(f"unsupported collection tier: {tier or '<empty>'}")
    if tier not in ALLOWED_TIER_BY_ADMISSION[state]:
        raise ValueError(f"collection tier {tier} is not permitted for admission state {state}")
    if not rationale_values:
        raise ValueError("admission decision requires at least one rationale")
    if not method:
        raise ValueError("admission decision requires a method")
    if state == "included" and not evidence_values:
        raise ValueError("included admission requires evidence")

    return AdmissionDecision(
        state=state,
        tier=tier,
        rationale=rationale_values,
        evidence=evidence_values,
        method=method,
    )


def unresolved_admission(*, rationale: str = "insufficient admission evidence") -> AdmissionDecision:
    """Fail closed: discovery alone never grants deep-monitoring authority."""
    return make_admission_decision(
        state="review",
        tier="inventory",
        rationale=(rationale,),
        method="unresolved",
    )
