"""Compare hand-written rules and query-time Gemini on the same salary cases."""

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from statistics import median
from time import perf_counter

from project_a.compiled import compare_compiled
from project_a.tests.fixtures import expected_salary_only
from project_a.llm_tax import read_tax, request_calculation
from project_a.rules import Salary, compare

FIXTURES = Path(__file__).parent / "tests" / "official_calculator_cases.json"


def run(cases, method, repeats, fy="2024-25"):
    rows = []
    for index, case in enumerate(cases, 1):
        salary = Salary(case["gross"], case["age"], case["resident"])
        expected = (
            [case["expected_old"], case["expected_new"]] if fy == "2024-25" else
            [expected_salary_only(salary.gross, salary.age, salary.resident, new, fy)
             for new in (False, True)]
        )
        for attempt in range(1, repeats + 1):
            started = perf_counter()
            row = {"case": index, "attempt": attempt, "expected": expected}
            try:
                if method == "rules":
                    result = compare(salary, fy=fy)
                elif method == "compiled":
                    result = compare_compiled(salary, fy=fy)
                else:
                    reply = request_calculation(salary, fy=fy)
                    row.update(model=reply.model, usage=reply.usage)
                    row["model_payable"] = [reply.value[regime]["payable"] for regime in ("old", "new")]
                    result = {regime: read_tax(reply.value[regime]) for regime in ("old", "new")}
                row["payable"] = [result[regime].payable for regime in ("old", "new")]
                row["correct"] = row["payable"] == expected
            except (ValueError, TypeError, KeyError, OSError, RuntimeError, ZeroDivisionError) as error:
                row["error"] = str(error)
            row["seconds"] = perf_counter() - started
            rows.append(row)
    successful = [row for row in rows if "payable" in row]
    outcomes = Counter(tuple(row["payable"]) for row in successful)
    return {
        "method": method,
        "fy": fy,
        "requests": len(rows),
        "errors": len(rows) - len(successful),
        "exact_both": sum(row["correct"] for row in successful),
        "model_raw_exact_both": sum(row.get("model_payable") == row["expected"] for row in rows)
        if method == "gemini" else None,
        "median_success_seconds": median(row["seconds"] for row in successful) if successful else None,
        "repeatability": ([
            {"payable": list(payable), "count": count} for payable, count in outcomes.items()
        ] if len(cases) == 1 else None),
        "results": rows,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--method", choices=("rules", "compiled", "gemini"), default="rules")
    cli.add_argument("--limit", type=int, default=30)
    cli.add_argument("--case", type=int, help="Select one fixture by its 1-based index.")
    cli.add_argument("--fy", choices=("2024-25", "2025-26"), default="2024-25")
    cli.add_argument("--repeats", type=int, default=1)
    args = cli.parse_args()
    cases = json.loads(FIXTURES.read_text())
    if args.repeats < 1 or not 1 <= args.limit <= len(cases):
        cli.error("Invalid repeat count or case limit.")
    if args.case is not None and not 1 <= args.case <= len(cases):
        cli.error("Invalid case number.")
    if args.method == "gemini" and not (os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")):
        cli.error("Set GEMINI_API_KEY and GEMINI_MODEL before running Gemini.")
    selected = cases[args.case - 1:args.case] if args.case else cases[:args.limit]
    report = run(selected, args.method, args.repeats, fy=args.fy)
    if args.case:
        report["fixture_index"] = args.case
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
