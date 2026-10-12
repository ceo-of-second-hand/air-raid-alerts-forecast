# D7 + D8: logistic regression vs GBM, with and without neighbour features

## In short

- **What this does:** compares a simple model (logistic regression, LR) with the more complex one (GBM), each with and without information about alerts in neighbouring oblasts. 3-hour forecasts, the same 10 two-week periods as before; the test period is not used.
- **How it's judged:** Brier score (how far the predicted probabilities are from what happened; lower is better), with the rules fixed in `DECISIONS.md` (L26, L27) before running.
- **LR: neighbour features KEPT.** They improved the Brier score in 9 of 10 periods (rule: at least 8), mean change +1.3%.
- **GBM: neighbour features KEPT.** They improved the Brier score in 9 of 10 periods (rule: at least 8), mean change +1.6%.
- **Model: GBM + neighbours.** Mean improvement over the recency rule: LR 1.5%, GBM 5.0% (gap +3.5 points; rule: GBM only if more than +1 point).
- **Still beats the recency rule?** In 10 of 10 periods (rule L25: at least 9) → PASS.

## Brier score per two-week period (lower is better)

| fold start | recency | LR base | LR + neighbours | GBM base | GBM + neighbours | LR skill vs recency | GBM skill vs recency |
|---|---|---|---|---|---|---|---|
| 2026-03-08 | 0.1163 | 0.1176 | 0.1163 | 0.1134 | 0.1128 | 0.0001 | 0.0303 |
| 2026-03-22 | 0.1695 | 0.1682 | 0.1632 | 0.1632 | 0.1579 | 0.0368 | 0.0680 |
| 2026-04-05 | 0.1186 | 0.1185 | 0.1180 | 0.1161 | 0.1138 | 0.0048 | 0.0407 |
| 2026-04-19 | 0.1266 | 0.1312 | 0.1300 | 0.1249 | 0.1231 | -0.0270 | 0.0278 |
| 2026-05-03 | 0.1415 | 0.1376 | 0.1331 | 0.1353 | 0.1310 | 0.0593 | 0.0745 |
| 2026-05-17 | 0.1507 | 0.1533 | 0.1518 | 0.1455 | 0.1432 | -0.0072 | 0.0494 |
| 2026-05-31 | 0.1262 | 0.1262 | 0.1248 | 0.1232 | 0.1213 | 0.0106 | 0.0384 |
| 2026-06-14 | 0.1394 | 0.1419 | 0.1407 | 0.1387 | 0.1366 | -0.0091 | 0.0201 |
| 2026-06-28 | 0.1202 | 0.1186 | 0.1168 | 0.1133 | 0.1117 | 0.0287 | 0.0708 |
| 2026-07-12 | 0.1183 | 0.1119 | 0.1124 | 0.1075 | 0.1092 | 0.0498 | 0.0771 |
