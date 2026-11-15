"""Summarize saved tax requests, including metered rejected model replies."""
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).with_name("results")
RUNS = ("tax_rules_repeat", "tax_compiled_repeat", "tax_gemini_repeat",
        "tax_gemini_cases", "tax_gemini_change")


def summarize(report):
    rows = report["results"]
    metered = [row["usage"] for row in rows if row.get("usage")]
    costs = [
        entry.get("promptTokenCount", 0) * 0.25
        + (entry.get("candidatesTokenCount", 0) + entry.get("thoughtsTokenCount", 0)) * 1.50
        for entry in metered
    ]
    return {
        "fy": report["fy"], "requests": report["requests"], "errors": report["errors"],
        "exact_both": report["exact_both"], "model_raw_exact_both": report.get("model_raw_exact_both"),
        "repeatability": report["repeatability"],
        "median_all_seconds": median(row["seconds"] for row in rows),
        "median_accepted_seconds": report["median_success_seconds"],
        "metered_replies": len(metered),
        "projected_paid_usd_per_1000_metered_replies": sum(costs) / len(costs) / 1000 if costs else None,
    }


def main():
    for name in RUNS:
        path = ROOT / f"{name}.json"
        if path.exists() and path.stat().st_size:
            print(json.dumps({name: summarize(json.loads(path.read_text()))}, indent=2))


if __name__ == "__main__":
    main()
