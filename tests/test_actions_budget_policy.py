"""Keep Actions execution triggers bounded to the intended budget policy."""
import unittest
from pathlib import Path


class ActionsBudgetPolicyTests(unittest.TestCase):
    def text(self, name):
        return (Path(".github/workflows") / name).read_text(encoding="utf-8")

    def test_validate_once_per_pr_unless_manually_dispatched(self):
        content = self.text("validate.yml")
        self.assertIn("pull_request:", content)
        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("  push:", content)
        self.assertNotIn("  schedule:", content)

    def test_public_smoke_test_only_on_demand(self):
        content = self.text("verify-monthly-pages.yml")
        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("  push:", content)
        self.assertNotIn("  schedule:", content)

    def test_expensive_monthly_and_probe_are_manual(self):
        for workflow in ("monthly-prototype.yml", "toip-source-probe.yml"):
            content = self.text(workflow)
            self.assertIn("workflow_dispatch:", content)
            self.assertNotIn("  push:", content)
            self.assertNotIn("  schedule:", content)

    def test_weekly_remains_scheduled_and_scoped(self):
        content = self.text("collect-weekly.yml")
        self.assertIn("schedule:", content)
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("'organizations/**'", content)
        self.assertNotIn("'trust_ecosystem_monitor/**'", content)


if __name__ == "__main__":
    unittest.main()
