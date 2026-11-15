import unittest

from project_a.compiled import compare_compiled
from project_a.rules import Salary
from project_a.tests.fixtures import expected_salary_only, salary_cases


class CompiledRulesTests(unittest.TestCase):
    def test_expected_salary_cases(self):
        for year in ("2024-25", "2025-26"):
            for gross, age, resident, _ in salary_cases():
                with self.subTest(year=year, gross=gross, age=age, resident=resident):
                    actual = compare_compiled(Salary(gross, age, resident), year)
                    for regime in ("old", "new"):
                        self.assertEqual(
                            actual[regime].payable,
                            expected_salary_only(gross, age, resident, regime == "new", year),
                        )
                        self.assertEqual(actual[regime].taxable, sum(x[1] for x in actual[regime].income_trace))
                        self.assertEqual(actual[regime].payable, sum(x[1] for x in actual[regime].tax_trace))
