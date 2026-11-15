# FireAI AI/ML take-home

Requires Python 3.10+. No third-party Python packages are needed.

Run both projects from the root with one command:

```sh
sh reproduce.sh
```

The first run downloads the official NYC sample into `.fireai-data/`. Supply `--data /path/to/extract.csv` to use a saved extract. Benchmark time varies by machine. The saved reports contain the observed live runs. New Gemini calls can return different answers or hit quota. NYC Open Data updates the dataset in place, so compare the SHA-256 if exact snapshot identity matters.

For a tax calculation:

```sh
python3 -m project_a --facts '{"gross":775100,"age":30,"resident":true}' --fy 2024-25
```

The `--describe` and `--method gemini` options use the configured Gemini API. Export `GEMINI_API_KEY` and `GEMINI_MODEL` in the local shell before making model calls. For the live parser, run `python3 -m project_a.evaluate_parser`. For query-time tax repeatability, run `python3 -m project_a.evaluate_tax --method gemini --case 16 --repeats 10`. Add `--gemini --input-usd-per-million 0.25 --output-usd-per-million 1.50` to `sh reproduce.sh` to rerun the Project B synthetic model comparison with a paid-rate projection.

[Project A results](RESULTS_A.md) · [Project B results](RESULTS_B.md) · [Decision matrix](DECISION_MATRIX.md) · [AI usage](AI_USAGE.md)
