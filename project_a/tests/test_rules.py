import unittest

from project_a.rules import Salary, compare
from project_a.tests.fixtures import salary_cases


class TaxTests(unittest.TestCase):
    def assert_tax(self, inputs, expected):
        result = compare(inputs)
        self.assertEqual((result["old"].payable, result["new"].payable), expected)

    def test_rebate_and_marginal_relief(self):
        self.assert_tax(Salary(775_000), (59_800, 0))
        self.assert_tax(Salary(775_100), (59_820, 100))
        self.assert_tax(Salary(550_005), (13_000, 0))

    def test_thresholds(self):
        cases = list(salary_cases())
        self.assertGreaterEqual(len(cases), 200)
        for gross, age, resident, expected in cases:
            with self.subTest(gross=gross, age=age, resident=resident):
                self.assert_tax(Salary(gross, age, resident), expected)

    def test_old_regime_deductions(self):
        # HRA: min(300k, 300k, 240k) = 240k. Taxable: 1.5m - 765k = 735k.
        self.assert_tax(Salary(1_500_000, hra_received=300_000, hra_salary=600_000,
                               rent_paid=300_000, metro=True, investments_80c=160_000,
                               nps_80ccd=55_000, family_premium=26_000,
                               parent_premium=60_000, senior_parent=True,
                               home_interest=220_000), (61_880, 130_000))

    def test_deduction_cap_boundaries(self):
        for field, limit, options in (
            ("investments_80c", 150_000, {}),
            ("nps_80ccd", 50_000, {}),
            ("family_premium", 25_000, {}),
            ("family_premium", 50_000, {"senior_family": True}),
            ("parent_premium", 25_000, {}),
            ("parent_premium", 50_000, {"senior_parent": True}),
            ("home_interest", 30_000, {"higher_home_cap": False}),
            ("home_interest", 200_000, {}),
        ):
            for delta in (-10, 0, 10):
                with self.subTest(field=field, limit=limit, delta=delta):
                    result = compare(Salary(1_500_000, **options, **{field: limit + delta}))
                    allowed = limit + min(delta, 0)
                    self.assertEqual(result["old"].taxable, 1_450_000 - allowed)
                    self.assertEqual(result["new"].taxable, 1_425_000)

    def test_hra_switches_at_each_limit(self):
        for metro, rent, received, exemption in (
            (False, 59_990, 350_000, 0),
            (False, 60_010, 350_000, 10),
            (False, 300_010, 350_000, 240_000),
            (True, 360_010, 350_000, 300_000),
            (True, 360_010, 299_990, 299_990),
        ):
            with self.subTest(metro=metro, rent=rent, received=received):
                result = compare(Salary(1_500_000, hra_salary=600_000,
                                        hra_received=received, rent_paid=rent, metro=metro))
                self.assertEqual(result["old"].taxable, 1_450_000 - exemption)
                self.assertEqual(result["new"].taxable, 1_425_000)

    def test_finance_act_2025(self):
        for gross, new_payable in ((1_275_000, 0), (1_275_100, 100),
                                   (1_400_000, 81_900), (2_475_000, 312_000)):
            with self.subTest(gross=gross):
                result = compare(Salary(gross), fy="2025-26")
                self.assertEqual(result["new"].payable, new_payable)
                self.assertEqual(result["old"], compare(Salary(gross))["old"])

    def test_trace_reconciles_income_and_tax(self):
        for result in compare(Salary(5_075_100)).values():
            self.assertEqual(sum(amount for _, amount in result.income_trace), result.taxable)
            self.assertEqual(sum(amount for _, amount in result.tax_trace), result.payable)
