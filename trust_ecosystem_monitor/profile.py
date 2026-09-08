from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_PATH = Path("organizations/trustoverip/profile.toml")
SUPPORTED_DISCOVERY_SOURCE_TYPES = frozenset({"github_organization", "explicit_repository"})


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
    }
