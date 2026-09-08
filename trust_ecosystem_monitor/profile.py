from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_PATH = Path("organizations/trustoverip/profile.toml")
SUPPORTED_DISCOVERY_SOURCE_TYPES = frozenset({"github_organization", "explicit_repository"})
SUPPORTED_ADMISSION_MODES = frozenset({"all_discovered", "governed"})
SUPPORTED_ADMISSION_STATES = frozenset({"included", "watch", "review", "excluded"})
SUPPORTED_COLLECTION_TIERS = frozenset({"core", "related", "watch", "inventory"})


@dataclass(frozen=True)
class PortfolioRule:
    portfolio: str
    prefixes: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoverySource:
    type: str
    value: str


@dataclass(frozen=True)
class AdmissionOverride:
    repository: str
    state: str
    tier: str
    rationale: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissionPolicy:
    mode: str = "all_discovered"
    default_state: str = "included"
    default_tier: str = "core"
    repository_overrides: tuple[AdmissionOverride, ...] = ()

    @property
    def overrides(self) -> dict[str, AdmissionOverride]:
        return {override.repository: override for override in self.repository_overrides}


@dataclass(frozen=True)
class AdmissionDecision:
    state: str
    tier: str
    rationale: str
    evidence: tuple[str, ...]
    method: str


@dataclass(frozen=True)
class OrganizationProfile:
    schema_version: str
    id: str
    organization: str
    display_name: str
    monitor_title: str
    weekly_brief_title: str
    disclaimer: str
    portfolio_rules: tuple[PortfolioRule, ...]
    repository_overrides: tuple[tuple[str, str], ...] = ()
    discovery_sources: tuple[DiscoverySource, ...] = ()
    admission_policy: AdmissionPolicy = AdmissionPolicy()

    @property
    def overrides(self) -> dict[str, str]:
        return dict(self.repository_overrides)


def _load_discovery_sources(payload: dict[str, Any], path: Path) -> tuple[DiscoverySource, ...]:
    raw_sources = payload.get("discovery_sources")
    if raw_sources is None:
        # Schema v1 compatibility: the historical organization field is an
        # explicit GitHub discovery source, not an implicit monitoring policy.
        return (DiscoverySource(type="github_organization", value=str(payload["organization"])),)
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError(f"organization profile {path} discovery_sources must be a non-empty array of tables")

    sources: list[DiscoverySource] = []
    for raw in raw_sources:
        if not isinstance(raw, dict):
            raise ValueError(f"organization profile {path} contains an invalid discovery source")
        source_type = str(raw.get("type", "")).strip()
        value = str(raw.get("value", "")).strip()
        if source_type not in SUPPORTED_DISCOVERY_SOURCE_TYPES:
            raise ValueError(f"organization profile {path} contains unsupported discovery source type: {source_type or '<empty>'}")
        if not value:
            raise ValueError(f"organization profile {path} contains a discovery source without a value")
        sources.append(DiscoverySource(type=source_type, value=value))
    return tuple(sources)


def _load_admission_policy(payload: dict[str, Any], path: Path) -> AdmissionPolicy:
    raw_policy = payload.get("admission")
    if raw_policy is None:
        # Backward compatibility is explicit: existing profiles continue to
        # monitor every discovered repository at the historical collection depth.
        return AdmissionPolicy()
    if not isinstance(raw_policy, dict):
        raise ValueError(f"organization profile {path} admission must be a TOML table")

    mode = str(raw_policy.get("mode", "governed")).strip()
    if mode not in SUPPORTED_ADMISSION_MODES:
        raise ValueError(f"organization profile {path} contains unsupported admission mode: {mode or '<empty>'}")

    if mode == "all_discovered":
        default_state = str(raw_policy.get("default_state", "included")).strip()
        default_tier = str(raw_policy.get("default_tier", "core")).strip()
    else:
        # Governed admission is fail-closed with respect to monitoring scope:
        # missing evidence creates a review item, never implicit inclusion.
        default_state = str(raw_policy.get("default_state", "review")).strip()
        default_tier = str(raw_policy.get("default_tier", "inventory")).strip()

    if default_state not in SUPPORTED_ADMISSION_STATES:
        raise ValueError(f"organization profile {path} contains unsupported default admission state: {default_state or '<empty>'}")
    if default_tier not in SUPPORTED_COLLECTION_TIERS:
        raise ValueError(f"organization profile {path} contains unsupported default collection tier: {default_tier or '<empty>'}")
    if mode == "governed" and (default_state != "review" or default_tier != "inventory"):
        raise ValueError(
            f"organization profile {path} governed admission must default to state=review and tier=inventory"
        )

    raw_overrides = raw_policy.get("repositories", [])
    if not isinstance(raw_overrides, list):
        raise ValueError(f"organization profile {path} admission.repositories must be an array of tables")

    overrides: list[AdmissionOverride] = []
    seen: set[str] = set()
    for raw in raw_overrides:
        if not isinstance(raw, dict):
            raise ValueError(f"organization profile {path} contains an invalid admission repository override")
        repository = str(raw.get("repository", "")).strip().lower()
        state = str(raw.get("state", "")).strip()
        tier = str(raw.get("tier", "")).strip()
        rationale = str(raw.get("rationale", "")).strip()
        raw_evidence = raw.get("evidence", [])
        if not repository or not rationale:
            raise ValueError(f"organization profile {path} admission override requires repository and rationale")
        if repository in seen:
            raise ValueError(f"organization profile {path} contains duplicate admission override for {repository}")
        if state not in SUPPORTED_ADMISSION_STATES:
            raise ValueError(f"organization profile {path} contains unsupported admission state for {repository}: {state or '<empty>'}")
        if tier not in SUPPORTED_COLLECTION_TIERS:
            raise ValueError(f"organization profile {path} contains unsupported collection tier for {repository}: {tier or '<empty>'}")
        if not isinstance(raw_evidence, list) or any(not str(item).strip() for item in raw_evidence):
            raise ValueError(f"organization profile {path} admission evidence for {repository} must be an array of non-empty strings")
        evidence = tuple(str(item).strip() for item in raw_evidence)
        if mode == "governed" and state in {"included", "watch"} and not evidence:
            raise ValueError(f"organization profile {path} governed admission for {repository} requires evidence")
        seen.add(repository)
        overrides.append(
            AdmissionOverride(
                repository=repository,
                state=state,
                tier=tier,
                rationale=rationale,
                evidence=evidence,
            )
        )

    return AdmissionPolicy(
        mode=mode,
        default_state=default_state,
        default_tier=default_tier,
        repository_overrides=tuple(sorted(overrides, key=lambda item: item.repository)),
    )


def admission_decision(repository: str, profile: OrganizationProfile) -> AdmissionDecision:
    repository_name = repository.strip().lower()
    override = profile.admission_policy.overrides.get(repository_name)
    if override:
        return AdmissionDecision(
            state=override.state,
            tier=override.tier,
            rationale=override.rationale,
            evidence=override.evidence,
            method="override",
        )

    policy = profile.admission_policy
    if policy.mode == "all_discovered":
        return AdmissionDecision(
            state=policy.default_state,
            tier=policy.default_tier,
            rationale="Legacy-compatible policy admits every discovered repository.",
            evidence=(),
            method="all_discovered",
        )
    return AdmissionDecision(
        state=policy.default_state,
        tier=policy.default_tier,
        rationale="No repository-specific admission evidence has been recorded; maintainer review is required.",
        evidence=(),
        method="default_review",
    )


def load_profile(path: str | Path = DEFAULT_PROFILE_PATH) -> OrganizationProfile:
    path = Path(path)
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    required = ("schema_version", "id", "organization", "display_name", "monitor_title", "weekly_brief_title", "disclaimer")
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ValueError(f"organization profile {path} missing required fields: {', '.join(missing)}")

    rules: list[PortfolioRule] = []
    for raw in payload.get("portfolio_rules", []):
        portfolio = str(raw.get("portfolio", "")).strip()
        if not portfolio:
            raise ValueError(f"organization profile {path} contains a portfolio rule without a portfolio name")
        rules.append(
            PortfolioRule(
                portfolio=portfolio,
                prefixes=tuple(str(value).lower() for value in raw.get("prefixes", [])),
                contains=tuple(str(value).lower() for value in raw.get("contains", [])),
            )
        )

    if not rules:
        raise ValueError(f"organization profile {path} must define at least one portfolio rule")

    overrides_payload = payload.get("repository_overrides", {})
    if not isinstance(overrides_payload, dict):
        raise ValueError(f"organization profile {path} repository_overrides must be a TOML table")
    overrides: list[tuple[str, str]] = []
    for repository, portfolio in overrides_payload.items():
        repository_name = str(repository).strip().lower()
        portfolio_name = str(portfolio).strip()
        if not repository_name or not portfolio_name:
            raise ValueError(f"organization profile {path} contains an invalid repository override")
        overrides.append((repository_name, portfolio_name))

    return OrganizationProfile(
        schema_version=str(payload["schema_version"]),
        id=str(payload["id"]),
        organization=str(payload["organization"]),
        display_name=str(payload["display_name"]),
        monitor_title=str(payload["monitor_title"]),
        weekly_brief_title=str(payload["weekly_brief_title"]),
        disclaimer=str(payload["disclaimer"]),
        portfolio_rules=tuple(rules),
        repository_overrides=tuple(sorted(overrides)),
        discovery_sources=_load_discovery_sources(payload, path),
        admission_policy=_load_admission_policy(payload, path),
    )


def classify_portfolio_details(name: str, profile: OrganizationProfile) -> dict[str, str | None]:
    lowered = name.lower()
    override = profile.overrides.get(lowered)
    if override:
        return {"portfolio": override, "method": "override", "rule": lowered}

    for index, rule in enumerate(profile.portfolio_rules):
        for prefix in rule.prefixes:
            if lowered.startswith(prefix):
                return {
                    "portfolio": rule.portfolio,
                    "method": "rule",
                    "rule": f"portfolio_rules[{index}].prefix:{prefix}",
                }
        for fragment in rule.contains:
            if fragment in lowered:
                return {
                    "portfolio": rule.portfolio,
                    "method": "rule",
                    "rule": f"portfolio_rules[{index}].contains:{fragment}",
                }

    return {"portfolio": "Unclassified", "method": "unclassified", "rule": None}


def classify_portfolio(name: str, profile: OrganizationProfile) -> str:
    return str(classify_portfolio_details(name, profile)["portfolio"])


def profile_metadata(profile: OrganizationProfile) -> dict[str, Any]:
    return {
        "schema_version": profile.schema_version,
        "id": profile.id,
        "organization": profile.organization,
        "display_name": profile.display_name,
        "monitor_title": profile.monitor_title,
        "weekly_brief_title": profile.weekly_brief_title,
        "disclaimer": profile.disclaimer,
        "repository_override_count": len(profile.repository_overrides),
        "discovery_sources": [
            {"type": source.type, "value": source.value} for source in profile.discovery_sources
        ],
        "admission": {
            "mode": profile.admission_policy.mode,
            "default_state": profile.admission_policy.default_state,
            "default_tier": profile.admission_policy.default_tier,
            "repository_override_count": len(profile.admission_policy.repository_overrides),
        },
    }
