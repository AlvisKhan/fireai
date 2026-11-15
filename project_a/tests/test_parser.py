import json
import unittest

from project_a.evaluate_parser import FIXTURES, evaluate
from project_a.gemini import Reply
from project_a.parser import CLAIMS, parse, validate
from project_a.rules import compare


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.facts = dict.fromkeys(CLAIMS, 0)
        self.facts.update(gross=775_100, age=30, resident=True)

    def payload(self):
        return {"status": "complete", "fy": "2024-25", "facts": self.facts}

    def test_parse_then_calculate(self):
        def fake_model(prompt, schema):
            self.assertIn("775100", prompt)
            self.assertIn("facts", schema["properties"])
            return Reply(self.payload(), {}, "test")

        result = parse("FY24-25, resident, age 30, annual gross salary 775100, no claims.", ask=fake_model)
        self.assertEqual(result.status, "complete")
        self.assertEqual(compare(result.salary, result.fy)["new"].payable, 100)

    def test_does_not_use_age_or_deduction_defaults(self):
        del self.facts["age"]
        self.assertEqual(validate(self.payload()).field, "age")
        self.facts["age"] = 30
        del self.facts["investments_80c"]
        self.assertEqual(validate(self.payload()).field, "investments_80c")

    def test_hra_requires_rental_city(self):
        self.facts.update(hra_received=100_000, hra_salary=300_000, rent_paid=120_000)
        self.assertEqual(validate(self.payload()).field, "metro")

    def test_contradictory_figures_do_not_reach_calculator(self):
        self.facts.update(hra_received=900_000, hra_salary=0, rent_paid=0, metro=False)
        self.assertEqual(validate(self.payload()).status, "clarify")

    def test_out_of_scope(self):
        self.assertIsNone(validate({"status": "out_of_scope"}).salary)

    def test_evaluation_counts_unsafe_completion(self):
        results = evaluate(
            [{"text": "Resident in FY24-25", "expect": "clarify", "field": "gross"}],
            ask=lambda prompt, schema: Reply(self.payload(), {}, "test"),
        )
        self.assertEqual(results["counts"]["unsafe_completion"], 1)
        self.assertEqual(results["counts"]["correct_status"], 0)

    def test_live_false_acceptances_now_require_clarification(self):
        cases = json.loads(FIXTURES.read_text())
        for case_number, expected in ((21, "resident"), (26, "pay_period"), (37, "year")):
            with self.subTest(case=case_number):
                result = parse(cases[case_number - 1]["text"],
                               ask=lambda prompt, schema: Reply(self.payload(), {}, "test"))
                self.assertEqual(result.status, "clarify")
                self.assertEqual(result.field, expected)
                self.assertIsNone(result.salary)

    def test_matching_financial_and_assessment_years(self):
        text = "FY 2024–25 / AY 2025-26. Resident, age 30, annual gross 70k. No claims."
        result = parse(text, ask=lambda prompt, schema: Reply(self.payload(), {}, "test"))
        self.assertEqual(result.status, "complete")

    def test_nonresident_cannot_be_read_as_resident(self):
        result = parse("FY24-25, non-resident, age 30, annual gross 775100, no claims.",
                       ask=lambda prompt, schema: Reply(self.payload(), {}, "test"))
        self.assertEqual(result.field, "resident")
