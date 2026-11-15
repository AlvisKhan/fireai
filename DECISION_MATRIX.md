# Decision matrix

| Component or check | Approach | Evidence |
|---|---|---|
| Text to tax facts | Hybrid | Python checks on model output raised correct clarification fields from 7/24 to 13/24. Two incorrect acceptances remain. |
| Tax, relief and comparison | Rule | 30/30 local expectations, 10/10 identical supported boundary results, and signed clause traces. |
| Budget rule drafting | Hybrid | Both generated Python drafts omitted surcharge. Review and regression checks are required before using model-derived policy. |
| Schema drift | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Column type change | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Date-format switch | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Swapped coordinates | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Exact duplicate | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Near duplicate | Rule | 100.0% recall and 0.30% control false alarms on the held-out benchmark. |
| Agency null spike | Statistical | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| Closed before created | Rule | 100.0% recall and 0.00% control false alarms on the held-out benchmark. |
| ZIP versus borough | Rule | 99.2% recall and 0.00% control false alarms on the held-out benchmark. |
| Complaint versus descriptor | Rule | 99.2% recall and 1.55% control false alarms on the held-out benchmark. |
| Resolution versus status | Rule | 100.0% recall and 0.20% control false alarms on the held-out benchmark. |
| Personal data in text | Rule | 100.0% recall and 1.85% control false alarms on the held-out benchmark. |
