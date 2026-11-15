"""Summarize actual calculator observations without counting blank entries."""
import json
from decimal import Decimal
from pathlib import Path

PATH = Path(__file__).parent / "tests" / "official_calculator_cases.json"


def main():
    cases = json.loads(PATH.read_text())
    observed = [case for case in cases
                if type(case["official_old"]) is int and type(case["official_new"]) is int]
    mismatches = []
    for case in observed:
        for regime in ("old", "new"):
            raw = Decimal(case[f"official_{regime}_raw"])
            rounded = (int(raw) + 5) // 10 * 10
            if rounded != case[f"official_{regime}"] or rounded != case[f"expected_{regime}"]:
                mismatches.append({"gross": case["gross"], "regime": regime,
                                   "expected": case[f"expected_{regime}"], "official": rounded})
    print(json.dumps({"available_cases": len(cases), "officially_checked": len(observed),
                      "mismatches": mismatches}, indent=2))


if __name__ == "__main__":
    main()
