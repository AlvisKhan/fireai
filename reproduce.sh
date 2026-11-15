#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m unittest discover -s project_a/tests
python3 -m unittest project_b.test_checks
python3 -m project_a.official_status
python3 -m project_a.summarize_parser
python3 -m project_b.annual
python3 -m project_a.evaluate_tax --method rules --case 16 --repeats 10
python3 -m project_a.evaluate_tax --method rules
python3 -m project_a.evaluate_tax --method compiled
python3 -m project_a.evaluate_tax --method compiled --case 16 --repeats 10
python3 -m project_a.evaluate_tax --method rules --fy 2025-26
python3 -m project_a.evaluate_tax --method compiled --fy 2025-26
python3 -m project_b.evaluate "$@"
