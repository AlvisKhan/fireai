"""Compare regimes from either confirmed inputs or a salary description."""
import argparse
import json
from dataclasses import asdict

from project_a.compiled import compare_compiled
from project_a.llm_tax import compare_live
from project_a.parser import parse
from project_a.rules import Salary, compare


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    inputs = cli.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--facts", help="Confirmed Salary fields as a JSON object.")
    inputs.add_argument("--describe", help="Free text for Gemini extraction.")
    cli.add_argument("--fy", choices=("2024-25", "2025-26"), default="2024-25")
    cli.add_argument("--method", choices=("rules", "compiled", "gemini"), default="rules")
    args = cli.parse_args()
    if args.describe is not None:
        parsed = parse(args.describe)
        if parsed.status != "complete":
            print(json.dumps(asdict(parsed), ensure_ascii=False, indent=2))
            return
        salary, fy = parsed.salary, parsed.fy
    else:
        salary, fy = Salary(**json.loads(args.facts)), args.fy

    if args.method == "gemini":
        results, _ = compare_live(salary, fy)
    else:
        calculator = compare_compiled if args.method == "compiled" else compare
        results = calculator(salary, fy)
    old, new = results["old"].payable, results["new"].payable
    print(json.dumps({
        "fy": fy,
        "recommended_regime": "tie" if old == new else min(results, key=lambda name: results[name].payable),
        "savings_rupees": abs(old - new),
        "results": {name: asdict(result) for name, result in results.items()},
    }, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
