"""Deterministic salary tax calculation for FY 2024–25 and FY 2025–26."""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Salary:
    gross: int
    age: int = 30
    resident: bool = True
    hra_received: int = 0
    hra_salary: int = 0
    rent_paid: int = 0
    metro: bool = False
    investments_80c: int = 0
    nps_80ccd: int = 0
    family_premium: int = 0
    parent_premium: int = 0
    senior_family: bool = False
    senior_parent: bool = False
    home_interest: int = 0
    higher_home_cap: bool = True

    def __post_init__(self):
        for name, value in vars(self).items():
            if isinstance(getattr(type(self), name, None), bool):
                if type(value) is not bool:
                    raise ValueError(f"{name} must be a boolean")
            elif type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.hra_salary + self.hra_received > self.gross:
            raise ValueError("HRA salary and HRA received together cannot exceed gross salary")


@dataclass(frozen=True)
class Tax:
    taxable: int
    payable: int
    income_trace: tuple[tuple[str, Fraction], ...]
    tax_trace: tuple[tuple[str, Fraction], ...]


def round_to_ten(amount):
    """Sections 288A and 288B, applied separately to income and tax."""
    return (int(amount) + 5) // 10 * 10


def slab_tax(income, brackets):
    lower = 0
    tax = Fraction()
    for upper, percent in brackets:
        portion = max(0, min(income, upper) - lower)
        tax += Fraction(portion * percent, 100)
        lower = upper
    return tax + Fraction(max(0, income - lower) * 30, 100)


def calculate(salary, new, fy="2024-25"):
    if fy not in ("2024-25", "2025-26"):
        raise ValueError(f"Unsupported financial year: {fy}")
    rebate_threshold, rebate_cap = (700_000, 25_000) if fy == "2024-25" else (1_200_000, 60_000)
    gross = salary.gross
    standard = min(gross, 75_000 if new else 50_000)
    deductions = [("§16(ia) standard deduction", Fraction(standard))]
    if new:
        brackets = ((300_000, 0), (700_000, 5), (1_000_000, 10),
                    (1_200_000, 15), (1_500_000, 20))
        if fy == "2025-26":
            brackets = ((400_000, 0), (800_000, 5), (1_200_000, 10),
                        (1_600_000, 15), (2_000_000, 20), (2_400_000, 25))
    else:
        hra = min(salary.hra_received,
                  Fraction(salary.hra_salary * (50 if salary.metro else 40), 100),
                  max(0, salary.rent_paid - Fraction(salary.hra_salary, 10)))
        interest = min(salary.home_interest, 200_000 if salary.higher_home_cap else 30_000)
        deductions.extend([
            ("§10(13A) and Rule 2A HRA", Fraction(hra)),
            ("§24(b) home interest set-off under §71(3A)", Fraction(interest)),
            ("§80C investment", Fraction(min(salary.investments_80c, 150_000))),
            ("§80CCD(1B) NPS", Fraction(min(salary.nps_80ccd, 50_000))),
            ("§80D family premium", Fraction(min(salary.family_premium, 50_000 if salary.senior_family else 25_000))),
            ("§80D parent premium", Fraction(min(salary.parent_premium, 50_000 if salary.senior_parent else 25_000))),
        ])
        basic = 250_000
        if salary.resident and salary.age >= 60:
            basic = 500_000 if salary.age >= 80 else 300_000
        brackets = ((basic, 0), (500_000, 5), (1_000_000, 20))

    unrounded_income = max(0, gross - sum(amount for _, amount in deductions))
    income = round_to_ten(unrounded_income)
    base_tax = slab_tax(income, brackets)
    rebate = Fraction()
    if salary.resident:
        if new and income <= rebate_threshold:
            rebate = min(base_tax, rebate_cap)
        elif new:
            rebate = max(0, base_tax - (income - rebate_threshold))
        elif income <= 500_000:
            rebate = min(base_tax, 12_500)

    tax = base_tax - rebate
    surcharge_bands = [(5_000_000, 10), (10_000_000, 15), (20_000_000, 25)]
    if not new:
        surcharge_bands.append((50_000_000, 37))
    surcharge = Fraction()
    relief = Fraction()
    for index in range(len(surcharge_bands) - 1, -1, -1):
        threshold, percent = surcharge_bands[index]
        if income > threshold:
            prior_percent = surcharge_bands[index - 1][1] if index else 0
            surcharge = tax * Fraction(percent, 100)
            cap = slab_tax(threshold, brackets) * Fraction(100 + prior_percent, 100)
            cap += income - threshold
            relief = max(0, tax + surcharge - cap)
            break
    cess = (tax + surcharge - relief) * Fraction(4, 100)
    total = tax + surcharge - relief + cess
    payable = round_to_ten(total)
    income_trace = (
        ("§17 gross salary", Fraction(gross)),
        *((label, -amount) for label, amount in deductions),
        ("§288A income rounding and zero floor", income - (gross - sum(a for _, a in deductions))),
    )
    tax_trace = (
        ("§115BAC slab tax" if new else "Finance Act slab tax", base_tax),
        ("§87A rebate or marginal relief", -rebate),
        ("Finance Act surcharge", surcharge),
        ("Finance Act surcharge marginal relief", -relief),
        ("Finance Act 4% health and education cess", cess),
        ("§288B payable rounding", payable - total),
    )
    return Tax(income, payable, income_trace, tax_trace)


def compare(salary, fy="2024-25"):
    return {regime: calculate(salary, new=(regime == "new"), fy=fy)
            for regime in ("old", "new")}
