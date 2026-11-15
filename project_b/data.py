"""Load a reproducible window of NYC 311 records and report observed issues."""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

API = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
FIELDS = ("unique_key", "created_date", "closed_date", "agency", "complaint_type",
          "descriptor", "incident_zip", "borough", "status", "resolution_description",
          "latitude", "longitude")
WINDOW = "created_date >= '2023-01-01T00:00:00' AND created_date < '2024-01-01T00:00:00'"


def download(path, limit=12000):
    params = {"$select": ",".join(FIELDS), "$where": WINDOW,
              "$order": "unique_key", "$limit": limit}
    path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(API + "?" + urlencode(params), timeout=90) as response:
        payload = response.read()
    path.write_bytes(payload)


def load(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if set(FIELDS) - set(reader.fieldnames or []):
            raise ValueError("Missing columns in NYC 311 extract")
        rows = list(reader)
    for row in rows:
        for field in ("latitude", "longitude"):
            try:
                row[field] = float(row[field]) if row[field] else None
            except ValueError:
                pass
    return rows


def parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def profile(rows):
    counts = Counter()
    examples = {}
    ids = set()
    nulls = Counter()
    for row in rows:
        key = row["unique_key"]
        created = parse_date(row["created_date"])
        closed = parse_date(row["closed_date"])
        lat, lon = row["latitude"], row["longitude"]
        issues = {
            "duplicate_key": key in ids,
            "closed_before_created": bool(closed and created and closed < created),
            "invalid_created_date": created is None,
            "missing_coordinates": lat is None or lon is None,
            "outside_nyc_coordinate_bounds": type(lat) is float and type(lon) is float
                and not (40.45 <= lat <= 40.95 and -74.30 <= lon <= -73.65),
            "closed_status_missing_close_date": row["status"].lower() == "closed" and not row["closed_date"],
        }
        ids.add(key)
        for label, present in issues.items():
            if present:
                counts[label] += 1
                if len(examples.setdefault(label, [])) < 3:
                    examples[label].append(key)
        for field in FIELDS:
            if row[field] is None or row[field] == "":
                nulls[field] += 1
    return {"rows": len(rows), "missing": dict(nulls), "issue_counts": dict(counts),
            "examples_unique_key": examples}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("path", type=Path)
    cli.add_argument("--download", action="store_true")
    args = cli.parse_args()
    if args.download:
        download(args.path)
    print(json.dumps(profile(load(args.path)), indent=2))


if __name__ == "__main__":
    main()
