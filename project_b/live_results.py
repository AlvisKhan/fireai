"""Summarize the captured Gemini synthetic detector runs."""
import json
from pathlib import Path

ROOT = Path(__file__).with_name("results")


def main():
    all_runs = {}
    for name in ("gemini", "gemini_retry", "gemini_retry_final"):
        path = ROOT / f"{name}.json"
        if not path.exists() or not path.stat().st_size:
            continue
        report = json.loads(path.read_text())
        all_runs[name] = [row for row in report["synthetic_comparison"]
                          if row["family"] == "gemini"]
    print(json.dumps(all_runs, indent=2))


if __name__ == "__main__":
    main()
