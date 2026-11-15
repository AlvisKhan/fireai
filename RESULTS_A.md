# Project A — Salary tax comparison

The calculator returns both regimes and the signed amounts behind taxable income and payable tax. In the boundary example, FY 2024–25 gross salary of ₹7,75,100 produces ₹59,820 old and ₹100 new. With the same inputs in FY 2025–26, new-regime tax is ₹0. The model meets the salary-only brief for the claims represented in the input schema. Section 80D inputs cover eligible insurance premiums. A single HRA tuple covers a period with one applicable city rate.

| Approach | FY 2024–25 evidence | Repeatability | Traceability |
|---|---|---|---|
| Hand-written rules | 912 salary threshold cases plus deduction and trace tests. 30/30 matches on the local comparison file. | ₹59,820 and ₹100 on all ten boundary runs. | Exact arithmetic, statutory labels and reconcilable amounts. |
| Gemini at query time | The initial ten boundary replies were rejected because the returned breakdown did not reconcile. | Zero accepted replies. Numerical repeatability cannot be inferred from that run. | Model-provided labels are claims. The sum check cannot establish statutory correctness. |
| Gemini-compiled rules | Initial Python drafts for both years failed review. See the generated drafts and review findings below. | The reviewed Python implementation passed the 912 salary cases under each year and returned the same two totals in ten repeats. | Runs locally and returns signed clause amounts. Its arithmetic is implemented separately from the hand-written path. |

The 30 cases in the comparison file have locally established expectations. Official portal results are recorded only when observed and are currently missing. The portal loads a JavaScript calculator. [Official reference](https://eportal.incometax.gov.in/iec/foservices/#/TaxCalc/calculator)

The parser gained deterministic checks for stated residency, conflicting year references, and selected ambiguous salary expressions. On the same 50 descriptions, expected status moved from 35 to 37, correct clarification field from 7 to 13 out of 24, incorrect acceptances from 3 to 2, and request errors from 10 to 9. The follow-up accepted one CTC input and one contradiction about gross pay. The latency medians including only completed cases were 3.060 s and 4.256 s. These runs do not establish extraction accuracy for every amount.

## Change review

The 2025 change affects new-regime slabs and Section 87A. Existing code was built across both years, so there is no controlled elapsed migration time for the hand-written or query-time versions. The initial Gemini Python generation ran in 7.235 s and 8.795 s for the respective FYs in the observed shell runs. These are generation times and exclude subsequent review. Review found missing surcharge, incorrect old slabs, incorrect HRA base, and malformed traces. In FY 2025–26, the generated parent insurance cap also used the taxpayer's age. Each could yield wrong answers without a Python exception.

## Deployment design

I would use Gemini for extraction, then ask the taxpayer to confirm the year, residence, gross pay and deductions before evaluating versioned local rules. Clarifications belong at the boundary because the parser accepted incomplete inputs twice even after validation. The query-time tax experiment had no accepted responses on its first repeated case. The local engine returns a clause-linked breakdown and uses no external API requests. Gemini-generated tables can accelerate a draft update, with human source review and the regression suite as release gates.

For a Budget update, preserve the old policy file, introduce a version tied to the effective financial year, and run both versions on threshold fixtures before deployment. Record the official calculator observations and investigate discrepancies before approving the change. The test oracle implements slabs as marginal-rate changes. Official portal verification remains a separate check.

Sources: [Finance (No. 2) Act 2024](https://incometaxindia.gov.in/Documents/Finance-No.2-Act-2024.pdf), [AY 2025–26](https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-3), [AY 2026–27](https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1), [official sections 288A](https://www.incometaxindia.gov.in/w/section-288a-58) and [288B](https://www.incometaxindia.gov.in/w/section-288b-59).
