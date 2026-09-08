import unittest
from pathlib import Path


WORKFLOW = Path(".github/workflows/collect-weekly.yml")


class WorkflowGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_generated_state_uses_dedicated_branch(self):
        self.assertIn("generated-observations", self.text)
        self.assertIn("Restore generated observation state", self.text)
        self.assertIn("Persist generated observation state", self.text)

    def test_weekly_workflow_does_not_push_current_branch(self):
        self.assertNotIn("git push\n", self.text)
        self.assertNotIn("git push origin main", self.text)
        self.assertNotIn("git push origin HEAD:main", self.text)

    def test_persistence_is_explicitly_scoped_to_generated_branch(self):
        self.assertIn('git push origin "$commit:refs/heads/generated-observations"', self.text)


if __name__ == "__main__":
    unittest.main()
