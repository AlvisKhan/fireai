"""Summarize actual calculator observations without counting blank entries."""
import json
from pathlib import Path

PATH = Path(__file__).parent / "tests" / "official_calculator_cases.json"


def main():
    cases = json.loads(PATH.read_text())
    observed = [case for case in cases
                if type(case["official_old"]) is int and type(case["official_new"]) is int]
    mismatches = [case for case in observed if
                  (case["official_old"], case["official_new"]) !=
                  (case["expected_old"], case["expected_new"])]
    print(json.dumps({"available_cases": len(cases), "officially_checked": len(observed),
                      "mismatches": mismatches}, indent=2))


if __name__ == "__main__":
    main()
