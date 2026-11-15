"""Generate and save a candidate Python calculator for human review."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

from project_a.gemini import generate
from project_a.llm_tax import COMMON, NEW_RULES


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fy", choices=tuple(NEW_RULES))
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    if args.output.exists():
        cli.error("Choose a new output path to preserve the previous candidate.")
    prompt = (
        "Translate the tax specification below into standalone Python 3.10 code. "
        "Expose compare(salary), taking a dictionary of inputs and returning old and new "
        "dictionaries, each with integer taxable and payable plus income_trace and tax_trace "
        "lists of objects with provision and amount (exact rational string). "
        "Use only fractions from the standard library and no I/O. Include all statutory steps. "
        "Return the full source in the source field.\n" + COMMON + NEW_RULES[args.fy]
    )
    reply = generate(prompt, {"type": "object", "properties": {"source": {"type": "string"}},
                              "required": ["source"]})
    source = reply.value["source"]
    ast.parse(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source + "\n", encoding="utf-8")
    print(json.dumps({"model": reply.model, "usage": reply.usage, "fy": args.fy,
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
