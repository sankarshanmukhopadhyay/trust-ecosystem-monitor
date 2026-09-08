import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trust_ecosystem_monitor import engine
from trust_ecosystem_monitor.profile import load_profile


class FakeClient(engine.GitHubClient):
    def __init__(self, responses=None):
        super().__init__(None)
        self.responses = responses or {}
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        response = self.responses.get(path, [])
        return response() if callable(response) else response


def repository(full_name):
    name = full_name.split("/", 1)[1]
    return {
        "id": abs(hash(full_name)) % 100000,
        "name": name,
        "full_name": full_name,
        "html_url": f"https://github.com/{full_name}",
        "description": None,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-09-08T00:00:00Z",
        "pushed_at": "2026-09-08T00:00:00Z",
        "archived": False,
        "fork": False,
        "default_branch": "main",
    }


class TierAwareCollectionTests(unittest.TestCase):
    def test_w3c_uses_explicit_discovery_and_external_admission_policy(self):
        profile_path = Path("organizations/w3c/profile.toml")
        profile = load_profile(profile_path)
        engine.configure_core(profile, profile_path)
        responses = {
            f"/repos/{source.value}": repository(source.value)
            for source in profile.discovery_sources
        }
        client = FakeClient(responses)

        discovered = client.org_repositories()

        self.assertEqual(len(discovered), 6)
        self.assertFalse(any(path.startswith("/orgs/w3c/repos") for path, _ in client.calls))
        for repo in discovered:
            with self.subTest(repository=repo["full_name"]):
                self.assertEqual(repo["_admission"]["state"], "included")
                self.assertIn(repo["_admission"]["tier"], {"core", "related"})
                self.assertEqual(repo["_discovery_sources"][0]["type"], "explicit_repository")

    def test_duplicate_discovery_retains_both_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / "profile.toml"
            profile_path.write_text(
                '''
schema_version = "1"
id = "example"
organization = "example"
display_name = "Example"
monitor_title = "Example"
weekly_brief_title = "Example"
disclaimer = "Independent."

[[discovery_sources]]
type = "github_organization"
value = "example"

[[discovery_sources]]
type = "explicit_repository"
value = "example/core-spec"

[[portfolio_rules]]
portfolio = "Core"
prefixes = ["core-"]
''',
                encoding="utf-8",
            )
            profile = load_profile(profile_path)
            engine.configure_core(profile, profile_path)
            repo = repository("example/core-spec")
            client = FakeClient(
                {
                    "/orgs/example/repos": [repo],
                    "/repos/example/core-spec": repo,
                }
            )

            discovered = client.org_repositories()

            self.assertEqual(len(discovered), 1)
            self.assertEqual(len(discovered[0]["_discovery_sources"]), 2)

    def test_inventory_tier_performs_no_activity_collection(self):
        client = FakeClient()
        repo = repository("example/inventory")
        repo.update(
            {
                "portfolio": "Core",
                "kind": "repository",
                "admission": {"state": "review", "tier": "inventory"},
            }
        )

        events, errors = engine._collect_repo_activity(
            client,
            repo,
            datetime.now(timezone.utc) - timedelta(days=7),
        )

        self.assertEqual(events, [])
        self.assertEqual(errors, [])
        self.assertEqual(client.calls, [])

    def test_watch_tier_collects_only_releases(self):
        client = FakeClient({"/repos/example/watch/releases": []})
        repo = repository("example/watch")
        repo.update(
            {
                "portfolio": "Core",
                "kind": "repository",
                "admission": {"state": "watch", "tier": "watch"},
            }
        )

        engine._collect_repo_activity(
            client,
            repo,
            datetime.now(timezone.utc) - timedelta(days=7),
        )

        self.assertEqual([path for path, _ in client.calls], ["/repos/example/watch/releases"])

    def test_core_tier_preserves_full_activity_collection(self):
        client = FakeClient()
        repo = repository("example/core")
        repo.update(
            {
                "portfolio": "Core",
                "kind": "repository",
                "admission": {"state": "included", "tier": "core"},
            }
        )

        engine._collect_repo_activity(
            client,
            repo,
            datetime.now(timezone.utc) - timedelta(days=7),
        )

        self.assertEqual(
            [path for path, _ in client.calls],
            [
                "/repos/example/core/commits",
                "/repos/example/core/issues",
                "/repos/example/core/pulls",
                "/repos/example/core/releases",
            ],
        )


if __name__ == "__main__":
    unittest.main()
