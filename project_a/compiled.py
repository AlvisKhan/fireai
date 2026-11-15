"""Reviewed version of Gemini's generated FY 2025-26 calculator.

The original generator output is preserved under results/generated. This version
repairs the identified failures and carries the FY 2024-25 slab table forward.
"""
from dataclasses import asdict
from fractions import Fraction as F

from project_a.rules import Tax

# Gemini's FY 2024-25 draft expressed brackets as widths.
BANDS = {
    "2024-25": ((300_000, 0), (700_000, 5), (1_000_000, 10),
                (1_200_000, 15), (1_500_000, 20)),
    "2025-26": ((400_000, 0), (800_000, 5), (1_200_000, 10),
                (1_600_000, 15), (2_000_000, 20), (2_400_000, 25)),
}
REBATE = {"2024-25": (700_000, 25_000), "2025-26": (1_200_000, 60_000)}


def round_nearest_10(value):
    value = int(value)
    remainder = value % 10
    return value - remainder if remainder < 5 else value + (10 - remainder)


def get_tax(inputs, year, regime):
    resident = inputs["resident"]
    age = inputs["age"]
    gross = inputs["gross"]
    taxable = F(gross)
    income_trace = [("§17 gross salary", taxable)]

    standard = min(taxable, 50_000 if regime == "old" else 75_000)
    taxable -= standard
    income_trace.append(("§16(ia) standard deduction", -standard))
    if regime == "old":
        eligible = inputs["hra_salary"]
        hra = min(inputs["hra_received"], eligible * F(50 if inputs["metro"] else 40, 100),
                  max(0, inputs["rent_paid"] - F(eligible, 10)))
        interest = min(inputs["home_interest"], 200_000 if inputs["higher_home_cap"] else 30_000)
        d_self = min(inputs["family_premium"], 50_000 if inputs["senior_family"] else 25_000)
        d_parent = min(inputs["parent_premium"], 50_000 if inputs["senior_parent"] else 25_000)
        adjustments = [
            ("§10(13A) and Rule 2A HRA", hra),
            ("§24(b) and §71(3A) home interest", interest),
            ("§80C investments", min(inputs["investments_80c"], 150_000)),
            ("§80CCD(1B) NPS", min(inputs["nps_80ccd"], 50_000)),
            ("§80D family premium", d_self),
            ("§80D parent premium", d_parent),
        ]
        for provision, amount in adjustments:
            taxable -= amount
            income_trace.append((provision, -F(amount)))

    rounded_taxable = round_nearest_10(max(0, taxable))
    income_trace.append(("§288A rounding and zero floor", rounded_taxable - taxable))

    if regime == "old":
        basic = 250_000
        if resident and age >= 60:
            basic = 500_000 if age >= 80 else 300_000
        slabs = ((basic, 0), (500_000, 5), (1_000_000, 20))
        threshold, maximum_rebate = 500_000, 12_500
    else:
        slabs = BANDS[year]
        threshold, maximum_rebate = REBATE[year]

    def slab_amount(amount):
        previous = 0
        result = F(0)
        for limit, rate in slabs:
            if amount > previous:
                result += F((min(amount, limit) - previous) * rate, 100)
            previous = limit
        return result + F(max(0, amount - previous) * 30, 100)

    slab = slab_amount(rounded_taxable)
    rebate = F(0)
    if resident and rounded_taxable <= threshold:
        rebate = min(slab, maximum_rebate)
    elif resident and regime == "new":
        rebate = max(0, slab - (rounded_taxable - threshold))

    tax = slab - rebate
    surcharge = F(0)
    relief = F(0)
    surcharge_rates = [(5_000_000, 10), (10_000_000, 15), (20_000_000, 25)]
    if regime == "old":
        surcharge_rates.append((50_000_000, 37))
    previous_rate = 0
    for cutoff, rate in surcharge_rates:
        if rounded_taxable <= cutoff:
            break
        surcharge = tax * F(rate, 100)
        maximum = slab_amount(cutoff) * F(100 + previous_rate, 100) + rounded_taxable - cutoff
        relief = max(0, tax + surcharge - maximum)
        previous_rate = rate

    total_before_cess = tax + surcharge - relief
    cess = total_before_cess * F(4, 100)
    payable = round_nearest_10(total_before_cess + cess)
    tax_trace = (
        ("§115BAC slab tax" if regime == "new" else "Finance Act slab tax", slab),
        ("§87A rebate or marginal relief", -rebate),
        ("Finance Act surcharge", surcharge),
        ("Finance Act surcharge marginal relief", -relief),
        ("Finance Act health and education cess", cess),
        ("§288B payable rounding", payable - total_before_cess - cess),
    )
    return Tax(rounded_taxable, payable, tuple(income_trace), tax_trace)


def compare_compiled(salary, fy="2024-25"):
    if fy not in BANDS:
        raise ValueError(f"Unsupported financial year: {fy}")
    inputs = asdict(salary)
    return {regime: get_tax(inputs, fy, regime) for regime in ("old", "new")}
