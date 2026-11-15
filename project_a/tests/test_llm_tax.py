import unittest

from project_a.gemini import Reply
from project_a.llm_tax import compare_live
from project_a.rules import Salary


class QueryTimeTaxTests(unittest.TestCase):
    def test_reads_balanced_reply_with_the_selected_year(self):
        def ask(prompt, schema):
            self.assertIn("threshold 1200000", prompt)
            self.assertIn('"gross": 775100', prompt)
            self.assertEqual(schema["required"], ["old", "new"])
            return Reply({"old": self.regime(725_100, 59_820),
                          "new": self.regime(700_100, 0)}, {}, "test")

        result, reply = compare_live(Salary(775_100), fy="2025-26", ask=ask)
        self.assertEqual(result["old"].payable, 59_820)
        self.assertEqual(result["new"].payable, 0)
        self.assertEqual(reply.model, "test")

    def test_rejects_unbalanced_tax_trace(self):
        bad = self.regime(700_100, 100)
        bad["tax_trace"][0]["amount"] = "104"
        with self.assertRaisesRegex(ValueError, "does not reconcile"):
            compare_live(Salary(775_100), ask=lambda *_: Reply({"old": bad}, {}, "test"))

    @staticmethod
    def regime(taxable, payable):
        return {
            "taxable": taxable,
            "payable": payable,
            "income_trace": [{"provision": "Test income", "amount": str(taxable)}],
            "tax_trace": [{"provision": "Test tax", "amount": str(payable)}],
        }
