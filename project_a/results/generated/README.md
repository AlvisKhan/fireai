# Gemini drafts and review

Each JSON file contains the exact generated Python source, its SHA-256, the Gemini model and token counts, and the observed wall-clock generation time. The files are evidence and are not loaded by the calculator.

The first draft silently mapped gross salary to the HRA salary base, set a regular citizen's zero-rate band to ₹5 lakh, reversed the marginal relief subtraction, and omitted surcharge. The second used the taxpayer's age for parent insurance and also omitted surcharge. Both had incomplete traces.

The reviewed implementation in `project_a/compiled.py` retains the generated year-specific slab schedule and stage-by-stage calculation. The review fixed field mapping, old-regime age and residency logic, HRA and separate medical insurance caps, rational arithmetic, surcharge, relief, and audit totals. The repair time was not separately timed. The reviewed version is separately implemented from the hand-written calculator and uses the same confirmed input and result types.
