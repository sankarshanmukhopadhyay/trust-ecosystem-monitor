"""Guard the Pages handoff between monthly and weekly deployment workflows."""
import unittest
from pathlib import Path


class ToIPPagesPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.monthly = Path(".github/workflows/monthly-prototype.yml").read_text()
        cls.weekly = Path(".github/workflows/collect-weekly.yml").read_text()

    def test_monthly_persists_after_readiness_before_deploy(self):
        readiness = self.monthly.index("Verify local Pages publication readiness")
        persist = self.monthly.index("Persist public intelligence pages")
        deploy = self.monthly.index("actions/deploy-pages")
        self.assertLess(readiness, persist)
        self.assertLess(persist, deploy)

    def test_both_workflows_share_serial_pages_concurrency(self):
        for workflow in (self.monthly, self.weekly):
            self.assertIn("group: pages", workflow)
            self.assertIn("cancel-in-progress: false", workflow)

    def test_generated_branch_is_the_handoff(self):
        self.assertIn('git push origin "$commit:refs/heads/generated-observations"', self.monthly)
        self.assertIn("git checkout origin/generated-observations -- data docs", self.weekly)
        self.assertIn('git read-tree "$parent"', self.monthly)
        self.assertIn("git add -A -- docs", self.monthly)
        self.assertIn('git rev-parse "${parent}^{tree}"', self.monthly)
        self.assertIn("contents: write", self.monthly)

    def test_no_main_branch_publication_push(self):
        self.assertNotIn("git push origin main", self.monthly)
        self.assertNotIn("git push origin HEAD:main", self.monthly)


if __name__ == "__main__":
    unittest.main()
