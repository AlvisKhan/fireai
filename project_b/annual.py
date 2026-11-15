"""Reproduce annual missing-field counts from the saved official aggregate."""
import json
from pathlib import Path

SOURCE = Path(__file__).with_name("results") / "annual_source.json"


def main():
    row, = json.loads(SOURCE.read_text())
    total = int(row["total"])
    print(json.dumps({"annual_rows": total, "missing": {
        name.removesuffix("_present"): total - int(value)
        for name, value in row.items() if name != "total"
    }}, indent=2))


if __name__ == "__main__":
    main()
