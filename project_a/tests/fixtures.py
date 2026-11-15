"""Salary tax expectations derived separately from the production calculator."""

from fractions import Fraction as F


def rounded(amount):
    return ((int(amount) + 5) // 10) * 10


def expected_salary_only(gross, age, resident, new, fy="2024-25"):
    """Use changes in marginal rate to calculate the statutory test oracle."""
    income = rounded(max(0, gross - (75_000 if new else 50_000)))
    basic = 250_000
    if resident and age >= 60:
        basic = 500_000 if age >= 80 else 300_000
    changes = (
        ((300_000, 5), (700_000, 5), (1_000_000, 5), (1_200_000, 5), (1_500_000, 10))
        if new else
        ((basic, 5), (500_000, 15), (1_000_000, 10))
    )
    if new and fy == "2025-26":
        changes = tuple((start, 5) for start in range(400_000, 2_400_001, 400_000))
    thresholds = [(5_000_000, 10), (10_000_000, 15), (20_000_000, 25)]
    if not new:
        thresholds.append((50_000_000, 37))

    def slab(value):
        return sum(F(max(0, value - start) * increase, 100) for start, increase in changes)

    tax = slab(income)
    if resident:
        if new:
            threshold = 700_000 if fy == "2024-25" else 1_200_000
            tax = min(tax, max(0, income - threshold))
        elif income <= 500_000:
            tax = 0

    previous = 0
    for threshold, rate in thresholds:
        if income <= threshold:
            break
        tax = min(slab(income) * F(100 + rate, 100),
                  slab(threshold) * F(100 + previous, 100) + income - threshold)
        previous = rate

    return rounded(tax * F(104, 100))


def salary_cases():
    """Probe each side of the threshold, including the §288A rounding boundary."""
    old_thresholds = (0, 250_000, 300_000, 500_000, 1_000_000, 5_000_000,
                      10_000_000, 20_000_000, 50_000_000)
    new_thresholds = (0, 300_000, 700_000, 722_220, 1_000_000, 1_200_000,
                      1_500_000, 5_000_000, 10_000_000, 20_000_000)
    centers = {50_000 + x for x in old_thresholds} | {75_000 + x for x in new_thresholds}
    for gross in sorted({center + offset for center in centers
                         for offset in (-10, -5, -1, 0, 1, 4, 5, 10)}):
        for age, resident in ((30, True), (59, True), (60, True), (79, True),
                              (80, True), (80, False)):
            yield gross, age, resident, tuple(
                expected_salary_only(gross, age, resident, new) for new in (False, True)
            )
