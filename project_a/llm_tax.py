"""Project A's query-time Gemini calculator.

Gemini receives the year-specific rule digest and performs the arithmetic.
Python checks the result format and reconciles its reported amounts.
"""

import json
from dataclasses import asdict
from fractions import Fraction

from project_a.gemini import generate
from project_a.rules import Tax

COMMON = """
Salary only. Inputs are whole rupees. Section 16(ia): subtract the smaller of
gross salary and the standard deduction (old 50000, new 75000).
Old regime only: Section 10(13A) / Rule 2A HRA exemption is the least of HRA
received, 50% of eligible salary if metro (40% otherwise), and rent minus
10% of eligible salary floored at zero. Sections 24(b) and 71(3A): set off
eligible self-occupied interest capped at 200000 if higher_home_cap else
30000. Section 80C is capped at 150000; Section 80CCD(1B) at 50000. Section
80D separately caps eligible family and parent premiums at 25000 each, or
50000 in the corresponding group with eligible senior status. None of
these exemptions, interest or claims apply under the new regime.
Floor taxable income at zero. Section 288A: discard fractional rupees then
round taxable income to nearest 10, ties upward, before applying brackets.

Old-regime slabs: zero to 250000 (resident ages 60–79: 300000; resident age
80+: 500000), then 5% to 500000, 20% to 1000000, then 30%. Old Section
87A: resident at or below 500000 receives the lesser of slab tax and 12500.
New Section 87A: for residents at or below the year threshold, rebate is the
lesser of slab tax and the year cap; above threshold, subtract any excess
of slab tax over the income above that threshold as marginal relief.
Nonresidents receive no Section 87A relief under either regime.

Surcharge: strictly above 5000000: 10%, 10000000: 15%, 20000000: 25%,
50000000: 37% (old only; new stays at 25%). Apply only the highest applicable
rate to tax after rebate. At that band's threshold, compute slab tax plus
surcharge at the prior rate (zero for the first threshold). Subtract surcharge
marginal relief to cap tax plus surcharge at that threshold amount plus the
income above the threshold. Cess is 4% of tax after all relief and surcharge.
Section 288B: discard fractional rupees and round payable to nearest 10,
ties upward. Report signed amounts for each income and tax step including
rounding so they separately sum to taxable and payable. Use exact numbers
as decimal or fraction strings. Explain each step by its specific provision.
"""
NEW_RULES = {
    "2024-25": """New slabs: 0% to 300000, 5% to 700000, 10% to 1000000,
15% to 1200000, 20% to 1500000, then 30%. Section 87A threshold 700000,
cap 25000. Source: Finance (No. 2) Act 2024 and CBDT AY 2025-26 guide.""",
    "2025-26": """New slabs: 0% to 400000, 5% to 800000, 10% to 1200000,
15% to 1600000, 20% to 2000000, 25% to 2400000, then 30%. Section 87A
threshold 1200000, cap 60000, limited to slab-rate tax (all tax here).
Source: Finance Act 2025 and CBDT AY 2026-27 guide.""",
}
LINE = {
    "type": "object",
    "properties": {"provision": {"type": "string"}, "amount": {"type": "string"}},
    "required": ["provision", "amount"],
}
REGIME = {
    "type": "object",
    "properties": {
        "taxable": {"type": "integer"},
        "payable": {"type": "integer"},
        "income_trace": {"type": "array", "items": LINE},
        "tax_trace": {"type": "array", "items": LINE},
    },
    "required": ["taxable", "payable", "income_trace", "tax_trace"],
}
SCHEMA = {"type": "object", "properties": {"old": REGIME, "new": REGIME},
          "required": ["old", "new"]}


def read_trace(lines, total):
    if not isinstance(lines, list) or not lines:
        raise ValueError("Gemini must provide a trace.")
    trace = []
    for line in lines:
        label = line["provision"]
        if not isinstance(label, str) or not label.strip():
            raise ValueError("Each trace entry needs a provision.")
        trace.append((label, Fraction(line["amount"])))
    if sum(amount for _, amount in trace) != total:
        raise ValueError("Gemini trace does not reconcile to its reported total.")
    return tuple(trace)


def read_tax(value):
    taxable, payable = value["taxable"], value["payable"]
    if any(type(x) is not int or x < 0 or x % 10 for x in (taxable, payable)):
        raise ValueError("Gemini totals must be nonnegative multiples of ten.")
    return Tax(taxable, payable, read_trace(value["income_trace"], taxable),
               read_trace(value["tax_trace"], payable))


def request_calculation(salary, fy="2024-25", ask=generate):
    if fy not in NEW_RULES:
        raise ValueError(f"Unsupported financial year: {fy}")
    prompt = f"Calculate both tax regimes for FY {fy}.\n{COMMON}\n{NEW_RULES[fy]}"
    prompt += "\nConfirmed inputs: " + json.dumps(asdict(salary))
    return ask(prompt, SCHEMA)


def compare_live(salary, fy="2024-25", ask=generate):
    reply = request_calculation(salary, fy, ask)
    return {regime: read_tax(reply.value[regime]) for regime in ("old", "new")}, reply
