"""Measure detectors on held-out 311 rows and optional synthetic Gemini batches."""
import argparse
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from random import Random
from time import perf_counter

from project_a.gemini import generate
from project_b.checks import KINDS, Baseline, duplicate_signature, hybrid, inject, llm_review, rules, statistics
from project_b.data import download, load, parse_date, profile


def clean_controls(rows):
    selected = []
    keys = set()
    signatures = set()
    for row in rows:
        created, closed = parse_date(row["created_date"]), parse_date(row["closed_date"])
        lat, lon = row["latitude"], row["longitude"]
        signature = duplicate_signature(row)
        if (not created or closed and closed < created or not row["incident_zip"]
                or not row["descriptor"] or type(lat) is not float or type(lon) is not float
                or not (40.45 <= lat <= 40.95 and -74.30 <= lon <= -73.65)
                or row["unique_key"] in keys or signature in signatures):
            continue
        keys.add(row["unique_key"])
        signatures.add(signature)
        selected.append(row)
    return selected


def synthetic_controls():
    start = datetime(2023, 3, 1)
    return [
        dict(unique_key=str(i), created_date=(start + timedelta(hours=i)).isoformat(),
             closed_date=(start + timedelta(hours=i + 2)).isoformat(), agency="DOT",
             complaint_type="Street Condition", descriptor="Pothole",
             incident_zip="10001", borough="MANHATTAN", status="Closed",
             resolution_description="The case is closed.", latitude=40.75 + i / 10000,
             longitude=-73.99)
        for i in range(20)
    ]


def score(kind, family, detector, clean, changed, labels, usd_input=None, usd_output=None):
    started = perf_counter()
    dirty, usage = detector(kind, changed)
    elapsed = perf_counter() - started
    clean_alerts, _ = detector(kind, clean)
    throughput = len(changed) / elapsed
    cost = None
    if usage is None:
        cost = 0.0
    elif usd_input is not None and usd_output is not None:
        output = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        cost = (usage.get("promptTokenCount", 0) * usd_input + output * usd_output) / len(changed)
    return {"check": kind, "family": family, "rows": len(changed), "injected": len(labels),
            "realized_rate": len(labels) / len(changed),
            "detected": len(dirty.keys() & labels),
            "detection_rate": len(dirty.keys() & labels) / len(labels),
            "control_false_alarm_rate": len(clean_alerts) / len(clean),
            "untouched_alerts_in_corrupted_batch": len(dirty.keys() - labels),
            "seconds": elapsed, "rows_per_second": throughput, "usage": usage,
            "usd_per_million_rows": cost, "example_explanation": next(iter(dirty.values()), None)}


def benchmark(rows, use_gemini=False, usd_input=None, usd_output=None):
    shuffled = list(rows)
    Random(311).shuffle(shuffled)
    split = len(shuffled) // 2
    baseline = Baseline(shuffled[:split])
    clean = clean_controls(shuffled[split:])[:2000]
    if len(clean) < 20:
        raise ValueError("At least 20 held-out controls are required")
    results = []
    rates = (0.05, 0.20)
    for rate in rates:
        for kind in KINDS:
            changed, labels = inject(clean, kind, rate, 311)
            for detector in (rules, statistics, hybrid):
                def local(check, batch):
                    return detector(check, batch, baseline), None
                results.append(score(kind, detector.__name__, local, clean, changed, labels)
                               | {"requested_rate": rate})

    started = perf_counter()
    for kind in KINDS:
        hybrid(kind, clean, baseline)
    elapsed = perf_counter() - started
    llm = []
    if use_gemini:
        fictional = synthetic_controls()
        fictional_baseline = Baseline(fictional)

        def remote(check, batch):
            return llm_review(check, batch, generate)

        for kind in KINDS:
            changed, labels = inject(fictional, kind, 0.20, 312)
            for name, detector in (
                ("rules", lambda check, batch: (rules(check, batch, fictional_baseline), None)),
                ("statistics", lambda check, batch: (statistics(check, batch, fictional_baseline), None)),
                ("gemini", remote),
            ):
                try:
                    llm.append(score(kind, name, detector, fictional, changed, labels,
                                     usd_input, usd_output))
                except (KeyError, ValueError, RuntimeError, OSError) as error:
                    llm.append({"check": kind, "family": name, "error": str(error)})
    return {"profile": profile(rows), "training_rows": split, "control_rows": len(clean),
            "local": results, "synthetic_comparison": llm, "hybrid_pipeline": {
                "seconds": elapsed, "rows_per_second": len(clean) / elapsed,
                "serial_hours_for_50m": 50_000_000 * elapsed / len(clean) / 3600,
                "external_api_usd_per_million": 0.0,
            }}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--data", type=Path, default=Path(".fireai-data/nyc311.csv"))
    cli.add_argument("--gemini", action="store_true")
    cli.add_argument("--input-usd-per-million", type=float)
    cli.add_argument("--output-usd-per-million", type=float)
    args = cli.parse_args()
    if not args.data.exists():
        download(args.data)
    result = benchmark(load(args.data), args.gemini, args.input_usd_per_million, args.output_usd_per_million)
    result["dataset_sha256"] = hashlib.sha256(args.data.read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
