import unittest

from trust_ecosystem_monitor.monthly_html import inline, render_html


class MonthlyHtmlTests(unittest.TestCase):
    def test_escapes_untrusted_source_text(self):
        output = render_html("# <script>alert(1)</script>\n\n- [Evidence](https://example.org/x)")
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn('href="https://example.org/x"', output)
        self.assertIn('rel="noopener noreferrer"', output)

    def test_renders_headings_lists_and_comparison_table(self):
        output = render_html("# Report\n\n## Activity\n\n- one\n- two\n\n| A | B |\n| --- | --- |\n| 1 | 2 |")
        self.assertIn("<h1>Report</h1>", output)
        self.assertIn("<h2>Activity</h2>", output)
        self.assertIn("<ul>", output)
        self.assertIn("<table>", output)
        self.assertNotIn("<td>---</td>", output)

    def test_only_https_urls_become_links(self):
        output = inline("[unsafe](javascript:alert(1)) [safe](https://example.org)")
        self.assertNotIn('href="javascript:', output)
        self.assertIn('href="https://example.org"', output)


if __name__ == "__main__":
    unittest.main()
