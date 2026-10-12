# Walk-forward backtest, target (a), pre-test data only

## In short

- **What this does:** trains the model on everything before a two-week period, then checks its forecasts for that period. Repeated for each of the 10 two-week periods before the test period (the test period itself is not used).
- **Compared to:** a simple rule that only looks at what's happening right now: "how often did an alert start soon after, when this oblast had an alert in the last few hours / has one active now" (recency baseline).
- **Result (3-hour forecasts):** the model was better in **10 of 10** periods, on average by **3.7%** (from 0.7% to 9.3%).
- **How "better" is measured:** Brier score = how far the predicted probabilities are from what actually happened (lower is better). "Skill" = how much lower the model's Brier score is than the baseline's.
- **Caveat:** for each period the baseline's best version is picked with hindsight, which favours the baseline. The model is not tuned yet.

Folds: 10 × 2 weeks, expanding window, min train 12 weeks. Test period (from 2026-07-26 21:00:00+00:00) untouched. Recency reference = best of 4 variants chosen on each fold's validation data (favours the baseline).

## Summary table

| horizon | folds | model wins | sign-test p | mean skill vs recency | min | max | mean skill vs clim |
|---|---|---|---|---|---|---|---|
| 1h | 10 | 10 | 0.001 | 0.047 | 0.021 | 0.064 | 0.111 |
| 3h | 10 | 10 | 0.001 | 0.037 | 0.007 | 0.093 | 0.112 |
| 6h | 10 | 10 | 0.001 | 0.029 | 0.006 | 0.085 | 0.102 |

## Horizon 1h

| fold start | train weeks | base rate | Brier model | Brier best recency | best recency | Brier clim | skill vs recency | skill vs clim | model wins |
|---|---|---|---|---|---|---|---|---|---|
| 2026-03-08 | 14 | 0.182 | 0.099 | 0.104 | 3h+active | 0.116 | 0.043 | 0.141 | yes |
| 2026-03-22 | 16 | 0.212 | 0.124 | 0.132 | 3h+active | 0.143 | 0.064 | 0.138 | yes |
| 2026-04-05 | 18 | 0.165 | 0.094 | 0.097 | 3h+active | 0.106 | 0.036 | 0.113 | yes |
| 2026-04-19 | 20 | 0.178 | 0.103 | 0.105 | 3h+active | 0.114 | 0.021 | 0.095 | yes |
| 2026-05-03 | 22 | 0.168 | 0.104 | 0.107 | 3h+active | 0.114 | 0.030 | 0.090 | yes |
| 2026-05-17 | 24 | 0.207 | 0.112 | 0.119 | 3h+active | 0.126 | 0.058 | 0.114 | yes |
| 2026-05-31 | 26 | 0.195 | 0.102 | 0.108 | 3h+active | 0.114 | 0.054 | 0.107 | yes |
| 2026-06-14 | 28 | 0.193 | 0.105 | 0.110 | 3h+active | 0.117 | 0.045 | 0.098 | yes |
| 2026-06-28 | 30 | 0.190 | 0.102 | 0.108 | 3h+active | 0.114 | 0.056 | 0.107 | yes |
| 2026-07-12 | 32 | 0.222 | 0.114 | 0.122 | 3h+active | 0.128 | 0.062 | 0.110 | yes |

## Horizon 3h

| fold start | train weeks | base rate | Brier model | Brier best recency | best recency | Brier clim | skill vs recency | skill vs clim | model wins |
|---|---|---|---|---|---|---|---|---|---|
| 2026-03-08 | 14 | 0.345 | 0.113 | 0.117 | 3h+active | 0.130 | 0.026 | 0.127 | yes |
| 2026-03-22 | 16 | 0.419 | 0.161 | 0.170 | 3h+active | 0.190 | 0.050 | 0.151 | yes |
| 2026-04-05 | 18 | 0.319 | 0.116 | 0.119 | 3h+active | 0.131 | 0.023 | 0.118 | yes |
| 2026-04-19 | 20 | 0.346 | 0.126 | 0.127 | 3h+active | 0.136 | 0.007 | 0.078 | yes |
| 2026-05-03 | 22 | 0.331 | 0.136 | 0.142 | k=6h | 0.154 | 0.037 | 0.112 | yes |
| 2026-05-17 | 24 | 0.393 | 0.145 | 0.151 | 3h+active | 0.163 | 0.041 | 0.112 | yes |
| 2026-05-31 | 26 | 0.364 | 0.123 | 0.126 | 3h+active | 0.132 | 0.027 | 0.070 | yes |
| 2026-06-14 | 28 | 0.363 | 0.138 | 0.139 | 3h+active | 0.148 | 0.008 | 0.068 | yes |
| 2026-06-28 | 30 | 0.353 | 0.114 | 0.121 | 3h+active | 0.129 | 0.058 | 0.122 | yes |
| 2026-07-12 | 32 | 0.401 | 0.108 | 0.119 | 3h+active | 0.128 | 0.093 | 0.157 | yes |

## Horizon 6h

| fold start | train weeks | base rate | Brier model | Brier best recency | best recency | Brier clim | skill vs recency | skill vs clim | model wins |
|---|---|---|---|---|---|---|---|---|---|
| 2026-03-08 | 14 | 0.450 | 0.108 | 0.110 | 3h+active | 0.123 | 0.015 | 0.118 | yes |
| 2026-03-22 | 16 | 0.560 | 0.163 | 0.166 | k=6h | 0.190 | 0.019 | 0.144 | yes |
| 2026-04-05 | 18 | 0.424 | 0.119 | 0.122 | 3h+active | 0.133 | 0.030 | 0.108 | yes |
| 2026-04-19 | 20 | 0.466 | 0.128 | 0.129 | 3h+active | 0.135 | 0.006 | 0.047 | yes |
| 2026-05-03 | 22 | 0.450 | 0.137 | 0.140 | k=6h | 0.154 | 0.021 | 0.110 | yes |
| 2026-05-17 | 24 | 0.528 | 0.156 | 0.162 | k=6h | 0.170 | 0.036 | 0.081 | yes |
| 2026-05-31 | 26 | 0.483 | 0.119 | 0.123 | 3h+active | 0.128 | 0.028 | 0.067 | yes |
| 2026-06-14 | 28 | 0.485 | 0.146 | 0.149 | 3h+active | 0.160 | 0.017 | 0.089 | yes |
| 2026-06-28 | 30 | 0.460 | 0.109 | 0.113 | 3h+active | 0.122 | 0.031 | 0.106 | yes |
| 2026-07-12 | 32 | 0.505 | 0.084 | 0.092 | 3h+active | 0.099 | 0.085 | 0.154 | yes |
