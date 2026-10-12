# D2: target comparison (official data, oblast level)

## In short

- **What this does:** tries three possible things to forecast, each with simple rules and one model, on the same data (official alerts, Dec 2025 → Sep 6 2026, 24 oblasts), checked on the last 6 weeks.
- **(a) Will an alert start in the oblast within 3 hours?** The model's Brier score (how far its probabilities are from what happened; lower is better) is 20% lower than that of the oblast's usual rate for that hour and weekday (climatology), and 9% lower than that of the best "what's happening right now" rule. Clearly predictable.
- **(b) How many alerts start tomorrow?** The model is off by 5.9 alerts per day on average, vs 6.6 for "same as the last 7 days' average". Barely better.
- **(d) How long will an alert last?** The model is within ±15 min for 28% of alerts, the same as just using the oblast's usual duration (28%). Not predictable with these inputs.
- **Caveat:** one 6-week period, no tuning. This period is the **test period**, so looking at it is logged in `experiments.md`.

Data 2025-12-01 → 2026-09-06 21:00:00+00:00 UTC, 24 oblasts, 80389 raion/oblast alert rows. Test = last 6 weeks (from 2026-07-26 21:00:00+00:00). One train/test split, no tuning: these numbers compare targets, they are not final results.

## (a) P(alert starts in oblast within next h hours)

| horizon | method | base rate | Brier | skill vs clim | skill vs best recency | AUC | accuracy@0.5 | majority-class acc |
|---|---|---|---|---|---|---|---|---|
| 1h | climatology | 0.205 | 0.126 | 0.000 | -0.099 | 0.826 | 0.818 | 0.795 |
| 1h | persistence (hard 0/1) | 0.205 | 0.206 | -0.630 | -0.790 | 0.684 | 0.794 | 0.795 |
| 1h | recency k=1h | 0.205 | 0.121 | 0.041 | -0.053 | 0.847 | 0.826 | 0.795 |
| 1h | recency k=3h | 0.205 | 0.119 | 0.061 | -0.032 | 0.854 | 0.835 | 0.795 |
| 1h | recency k=6h | 0.205 | 0.118 | 0.063 | -0.029 | 0.858 | 0.834 | 0.795 |
| 1h | recency 3h + active | 0.205 | 0.115 | 0.090 | 0.000 | 0.865 | 0.838 | 0.795 |
| 1h | GBM | 0.205 | 0.108 | 0.146 | 0.062 | 0.882 | 0.839 | 0.795 |
| 3h | climatology | 0.369 | 0.147 | 0.000 | -0.128 | 0.862 | 0.780 | 0.631 |
| 3h | persistence (hard 0/1) | 0.369 | 0.247 | -0.675 | -0.889 | 0.689 | 0.753 | 0.631 |
| 3h | recency k=1h | 0.369 | 0.140 | 0.049 | -0.073 | 0.874 | 0.778 | 0.631 |
| 3h | recency k=3h | 0.369 | 0.135 | 0.085 | -0.032 | 0.884 | 0.799 | 0.631 |
| 3h | recency k=6h | 0.369 | 0.133 | 0.098 | -0.018 | 0.888 | 0.814 | 0.631 |
| 3h | recency 3h + active | 0.369 | 0.130 | 0.114 | 0.000 | 0.890 | 0.813 | 0.631 |
| 3h | GBM | 0.369 | 0.118 | 0.196 | 0.093 | 0.907 | 0.830 | 0.631 |
| 6h | climatology | 0.465 | 0.143 | 0.000 | -0.108 | 0.872 | 0.803 | 0.535 |
| 6h | persistence (hard 0/1) | 0.465 | 0.300 | -1.093 | -1.320 | 0.680 | 0.700 | 0.535 |
| 6h | recency k=1h | 0.465 | 0.137 | 0.041 | -0.063 | 0.884 | 0.810 | 0.535 |
| 6h | recency k=3h | 0.465 | 0.132 | 0.077 | -0.023 | 0.893 | 0.811 | 0.535 |
| 6h | recency k=6h | 0.465 | 0.129 | 0.098 | 0.000 | 0.898 | 0.814 | 0.535 |
| 6h | recency 3h + active | 0.465 | 0.131 | 0.085 | -0.014 | 0.896 | 0.810 | 0.535 |
| 6h | GBM | 0.465 | 0.122 | 0.146 | 0.053 | 0.907 | 0.828 | 0.535 |

## (b) Alert starts per oblast per day (forecast issued the evening before)

| method | mean actual/day | MAE | within ±20% or ±2 |
|---|---|---|---|
| yesterday | 13.499 | 6.649 | 0.490 |
| 7-day mean | 13.499 | 6.640 | 0.497 |
| GBM (Poisson) | 13.499 | 5.935 | 0.488 |

## (d) Alert duration, predicted at its start

| method | median actual min | MAE min | median abs err min | within ±15 min | within ±25% | >1h correct |
|---|---|---|---|---|---|---|
| global median | 46.117 | 106.944 | 32.833 | 0.202 | 0.172 | 0.590 |
| oblast median | 46.117 | 100.198 | 27.675 | 0.285 | 0.200 | 0.670 |
| GBM | 46.117 | 97.777 | 28.469 | 0.285 | 0.202 | 0.673 |

Label noise in test: test alerts: 13607, share exactly 60 min (possible imputed end): 0.003, share > 24 h (possible missed all-clear): 0.009
