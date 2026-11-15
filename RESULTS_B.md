# Project B — NYC 311 quality checks

NYC Open Data returned 3,224,723 requests created in calendar 2023. The source aggregate found 38,520 missing ZIPs, 48,579 missing latitudes and longitudes each, 39,318 missing descriptors, 46,062 missing resolution descriptions, and 61,872 missing close dates. A missing close date can be legitimate for an open request. Missing coordinate examples in the local extract include keys 56408061, 56412433, and 56412494.

The local detector benchmark used the first 12,000 rows ordered by source request key. It shuffled with seed 311, fit references on 6,000 records, and used 2,000 held-out rows after filtering obvious issues. Control false alarms are alerts on this curated set. Some may be genuine inconsistencies. The sample is not representative of the entire year. Run logs include 5% and 20% target rates. A rename changes the whole batch schema. The null spike can only affect an agency's eligible rows.

The table shows recall and control false-alarm rate at the 20% target.

| Check | Rule recall / false alarm | Statistical recall / false alarm | Hybrid choice |
|---|---:|---:|---|
| Schema drift | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| Column type change | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| Date-format switch | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| Swapped coordinates | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| Exact duplicate | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| Near duplicate | 100.0% / 0.30% | 100.0% / 0.75% | Rule |
| Agency null spike | 100.0% / 0.00% | 100.0% / 0.00% | Statistical |
| Closed before created | 100.0% / 0.00% | 100.0% / 0.00% | Rule |
| ZIP versus borough | 99.2% / 0.00% | 99.2% / 0.00% | Rule |
| Complaint versus descriptor | 99.2% / 1.55% | 97.8% / 2.55% | Rule |
| Resolution versus status | 100.0% / 0.20% | 0.0% / 0.00% | Rule |
| Personal data in text | 100.0% / 1.85% | 68.5% / 0.00% | Rule |

The hybrid runs each selected check locally. Statistical agency rates can distinguish a spike from routine missingness, which a row-level presence rule cannot. Some other statistical baselines resemble rules (for example duration below zero). Resolution-template frequencies missed novel contradictions, and regex contact patterns produced more control alerts but caught the injected examples. Injected labels measure sensitivity to these particular corruptions. A separate labeled set is needed to estimate production false alarms.

The full hybrid passed 2,000 rows through all twelve checks at about 65,799 rows/s in one laptop run. At that rate 50 million rows take 12.7 minutes of serial detector compute. This excludes I/O, reference fitting, partition boundaries, and alerts. Local detector API spend is zero. If one worker costs USD 1/hour, this compute-only rate implies about USD 0.0042 per million rows. Workers should keep per-customer schema contracts and references. Duplicate state crosses batch boundaries, while null-rate baselines should remain local to each agency or customer. Recheck throughput and recall under those partitions before committing to an SLA.

Gemini scores are from matched synthetic batches only. Real text can contain unexpected identifiers. Synthetic results show capability on known perturbations and do not estimate real-world alert quality.

| Synthetic check | Rule recall / false alarm | Statistical recall / false alarm | Gemini recall / false alarm | Gemini USD / M rows | Gemini rows/s |
|---|---:|---:|---:|---:|---:|
| schema | 100% / 0% | 100% / 0% | 100% / 0% | 78.86 | 8.74 |
| type | 100% / 0% | 100% / 0% | 100% / 0% | 47.50 | 6.62 |
| date_format | 100% / 0% | 100% / 0% | 100% / 0% | 47.38 | 13.29 |
| swapped_coordinates | 100% / 0% | 100% / 0% | 100% / 0% | 46.02 | 8.13 |
| duplicate | 100% / 0% | 100% / 0% | 100% / 0% | 45.96 | 2.00 |
| near_duplicate | 100% / 0% | 100% / 0% | 100% / 0% | 46.89 | 6.64 |
| null_spike | 100% / 0% | 100% / 0% | 100% / 0% | 47.62 | 1.35 |
| chronology | 100% / 0% | 100% / 0% | 100% / 0% | 46.30 | 15.90 |
| zip_borough | 100% / 0% | 100% / 0% | 100% / 0% | 49.40 | 1.17 |
| descriptor | 100% / 0% | 100% / 0% | 0% / 0% | 38.17 | 7.45 |
| resolution | 100% / 0% | 0% / 0% | 0% / 0% | 38.33 | 16.06 |
| personal_data | 100% / 0% | 50% / 0% | 100% / 0% | 47.35 | 10.40 |

The Gemini figures use one 20-row corrupted and one control batch per check. Seven checks returned both batches on the first pass. Retrying the five failures returned three more. The ten checks scored by that point had 100% injected recall and no control alerts. The remaining two initially returned HTTP 503 twice. On the final retry, both returned valid responses but missed every injected contradiction. Control alerts were zero for all twelve. Paid standard-rate projections use token counts from the corrupted batch, at USD 0.25 per million input tokens and USD 1.50 per million output tokens. The run used the free tier. Local screening is the default because the model produced no measured recall gain over the rule baseline across the synthetic checks, and contributes request errors and latency. [Gemini pricing](https://aistudio.google.com/docs/pricing#gemini-3.1-flash-lite)

[NYC Open Data source](https://data.cityofnewyork.us/Social-Services/311-Service-Requests/erm2-nwe9) · [Local metrics](project_b/results/local.json) · [Annual aggregate](project_b/results/annual_source.json)
