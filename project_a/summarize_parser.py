"""Compare the saved parser runs using identical scoring."""

import json
from pathlib import Path
from statistics import median

RESULTS = Path(__file__).with_name("results")


def summarize(report, fixtures):
    rows = report["results"]
    assert len(rows) == report["cases"] == len(fixtures)
    errors = sum(row["status"] == "error" for row in rows)
    timings = [row["seconds"] for row in rows if "seconds" in row]
    counts = report["counts"]
    return {
        "cases": len(rows),
        "correct_status": counts.get("correct_status", 0),
        "request_errors": errors,
        "unsafe_completions": counts.get("unsafe_completion", 0),
        "correct_clarification_field": counts.get("correct_clarification", 0),
        "expected_clarifications": sum(case["expect"] == "clarify" for case in fixtures),
        "median_seconds_without_errors": round(median(timings), 3) if timings else None,
        "regression_cases": {str(case): rows[case - 1]["status"] for case in (21, 26, 37)},
    }


def main():
    fixtures = json.loads((RESULTS.parent / "tests" / "plain_language.json").read_text())
    for name in ("parser_baseline", "parser_after_validation"):
        report = json.loads((RESULTS / f"{name}.json").read_text())
        print(json.dumps({name: summarize(report, fixtures)}, indent=2))


if __name__ == "__main__":
    main()
