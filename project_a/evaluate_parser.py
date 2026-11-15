"""Run the parser against the 50 labeled synthetic descriptions."""

import argparse
import json
from collections import Counter
from pathlib import Path
from time import perf_counter

from project_a.gemini import generate
from project_a.parser import parse

FIXTURES = Path(__file__).parent / "tests" / "plain_language.json"
FIELD_ALIASES = {"residency": "resident", "rental_city": "metro"}


def evaluate(cases, ask=generate):
    counts = Counter()
    rows = []
    for index, case in enumerate(cases, 1):
        started = perf_counter()
        try:
            parsed = parse(case["text"], ask=ask)
        except (ValueError, RuntimeError, OSError) as error:
            counts["error"] += 1
            rows.append({"case": index, "status": "error", "error": str(error)})
            continue

        status_matches = parsed.status == case["expect"]
        counts["correct_status"] += status_matches
        counts["unsafe_completion"] += parsed.status == "complete" and case["expect"] != "complete"
        expected_field = case.get("field")
        actual_field = FIELD_ALIASES.get(parsed.field, parsed.field)
        if expected_field:
            counts["correct_clarification"] += (
                parsed.status == "clarify"
                and actual_field == FIELD_ALIASES.get(expected_field, expected_field)
            )
        rows.append({
            "case": index,
            "expected": case["expect"],
            "status": parsed.status,
            "field": parsed.field,
            "expected_field": expected_field,
            "seconds": round(perf_counter() - started, 6),
        })
    return {"cases": len(rows), "counts": dict(counts), "results": rows}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--limit", type=int, default=50)
    args = cli.parse_args()
    if not 1 <= args.limit <= 50:
        cli.error("--limit must be between 1 and 50.")
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(cases[:args.limit]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
