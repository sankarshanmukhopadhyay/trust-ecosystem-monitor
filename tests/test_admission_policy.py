from pathlib import Path

import pytest

from trust_ecosystem_monitor.profile import admission_decision, load_profile


BASE = '''
schema_version = "1"
id = "example"
organization = "example-org"
display_name = "Example"
monitor_title = "Example Monitor"
weekly_brief_title = "Example Brief"
disclaimer = "Independent observation."

[[portfolio_rules]]
portfolio = "Example"
prefixes = ["example-"]
'''


def write_profile(tmp_path: Path, suffix: str = "") -> Path:
    path = tmp_path / "profile.toml"
    path.write_text(BASE + suffix, encoding="utf-8")
    return path


def test_legacy_profile_admits_every_discovered_repository(tmp_path: Path) -> None:
    profile = load_profile(write_profile(tmp_path))

    decision = admission_decision("unclassified-repository", profile)

    assert decision.state == "included"
    assert decision.tier == "core"
    assert decision.method == "all_discovered"


def test_governed_profile_defaults_unknown_repository_to_review_inventory(tmp_path: Path) -> None:
    profile = load_profile(write_profile(tmp_path, '''

[admission]
mode = "governed"
'''))

    decision = admission_decision("unknown-repository", profile)

    assert decision.state == "review"
    assert decision.tier == "inventory"
    assert decision.method == "default_review"


def test_governed_override_records_inclusion_evidence(tmp_path: Path) -> None:
    profile = load_profile(write_profile(tmp_path, '''

[admission]
mode = "governed"

[[admission.repositories]]
repository = "example-spec"
state = "included"
tier = "core"
rationale = "The ecosystem governance record identifies this as an active specification repository."
evidence = ["https://example.invalid/governance/example-spec"]
'''))

    decision = admission_decision("EXAMPLE-SPEC", profile)

    assert decision.state == "included"
    assert decision.tier == "core"
    assert decision.method == "override"
    assert decision.evidence == ("https://example.invalid/governance/example-spec",)


def test_governed_exclusion_can_retain_inventory_provenance(tmp_path: Path) -> None:
    profile = load_profile(write_profile(tmp_path, '''

[admission]
mode = "governed"

[[admission.repositories]]
repository = "historical-example"
state = "excluded"
tier = "inventory"
rationale = "Historical repository retained only so the exclusion decision remains auditable."
'''))

    decision = admission_decision("historical-example", profile)

    assert decision.state == "excluded"
    assert decision.tier == "inventory"


@pytest.mark.parametrize(
    "suffix, message",
    [
        ('\n[admission]\nmode = "guess"\n', "unsupported admission mode"),
        ('\n[admission]\nmode = "governed"\ndefault_state = "included"\n', "must default to state=review"),
        ('\n[admission]\nmode = "governed"\ndefault_tier = "core"\n', "must default to state=review"),
        ('\n[admission]\nmode = "governed"\n\n[[admission.repositories]]\nrepository = "x"\nstate = "maybe"\ntier = "core"\nrationale = "reason"\n', "unsupported admission state"),
        ('\n[admission]\nmode = "governed"\n\n[[admission.repositories]]\nrepository = "x"\nstate = "included"\ntier = "deep"\nrationale = "reason"\n', "unsupported collection tier"),
        ('\n[admission]\nmode = "governed"\n\n[[admission.repositories]]\nrepository = "x"\nstate = "included"\ntier = "core"\nrationale = "reason"\n', "requires evidence"),
        ('\n[admission]\nmode = "governed"\n\n[[admission.repositories]]\nrepository = "x"\nstate = "excluded"\ntier = "inventory"\nrationale = ""\n', "requires repository and rationale"),
    ],
)
def test_invalid_admission_policy_is_rejected(tmp_path: Path, suffix: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_profile(write_profile(tmp_path, suffix))
