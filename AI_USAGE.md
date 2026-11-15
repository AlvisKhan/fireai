# AI usage

Codex assisted with fixture design, Python implementation, tests, benchmark commands, and reporting. Gemini 3.1 Flash-Lite extracted tax facts, attempted live tax calculations, generated candidate offline calculators, and reviewed synthetic quality-check batches. The real 311 text stayed local. API credentials were supplied to the shell through a hidden prompt.

An initial parser evaluation caught Gemini accepting a salary description with no residency. The validator could prove the returned field existed, but the input did not supply it. The regression test deliberately returns that same kind of structurally valid response. The updated parser checks the description and asks a residency question. Another generated calculator omitted surcharge. We identified the omission in review and retained its source as an example of a silent failure.
