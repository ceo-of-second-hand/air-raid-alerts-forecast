# Final evaluation (TEST period)

## In short

- **What this does:** trains the final model (GBM + neighbour features, start times only) on all data before 2026-07-26 and forecasts every hour of the test period (2026-07-26 21:00 → 2026-09-06 20:00 UTC, 24 oblasts).
- **3-hour forecasts vs the "recent alert starts" rule (recency, k=6h):** the model's Brier score (how far its probabilities are from what happened; lower is better) is **10.4% lower**. Better in **6 of 6** weeks.
- **vs the oblast's usual rate for that hour and weekday (climatology):** 19.2% lower.
- **Ranking (AUC: chance that an hour with an alert start gets a higher score than one without; 0.5 = random):** model 0.907 vs recency 0.888 over all oblasts together. **This mostly measures which oblast is active.** Within a single oblast the average is model 0.699 vs recency 0.630 (0 oblasts had no alert starts or no quiet hours, so no AUC).
- **Calibration:** see `calibration_test.png` and the table below (when the model says x%, how often did an alert start).

## All metrics

| metric | 1h | 3h | 6h |
|---|---|---|---|
| recency rule | k=3h | k=6h | k=6h |
| base rate | 0.2049 | 0.3692 | 0.4651 |
| Brier model | 0.1116 | 0.1185 | 0.1208 |
| Brier recency | 0.1185 | 0.1322 | 0.1287 |
| Brier clim | 0.1262 | 0.1467 | 0.1429 |
| skill vs recency | 0.0577 | 0.1037 | 0.0610 |
| skill vs clim | 0.1154 | 0.1920 | 0.1542 |
| AUC model | 0.8744 | 0.9070 | 0.9094 |
| AUC recency | 0.8546 | 0.8884 | 0.8975 |
| mean AUC per oblast | 0.6965 | 0.6989 | 0.6909 |
| mean AUC per oblast recency | 0.5800 | 0.6297 | 0.6717 |
| oblasts without AUC | 0 | 0 | 0 |
| log-loss model | 0.3416 | 0.3721 | 0.3858 |
| log-loss recency | 0.3653 | 0.4074 | 0.4053 |
| accuracy@0.5 | 0.8312 | 0.8312 | 0.8284 |
| majority-class acc | 0.7951 | 0.6308 | 0.5349 |

## 3 h, week by week

| week | from | Brier model | Brier recency | skill vs recency | model better |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | 0.1221 | 0.1265 | 0.0351 | yes |
| 2 | 2026-08-02 | 0.1270 | 0.1381 | 0.0802 | yes |
| 3 | 2026-08-09 | 0.1088 | 0.1147 | 0.0515 | yes |
| 4 | 2026-08-16 | 0.1262 | 0.1324 | 0.0465 | yes |
| 5 | 2026-08-23 | 0.1188 | 0.1352 | 0.1213 | yes |
| 6 | 2026-08-30 | 0.1079 | 0.1466 | 0.2639 | yes |

## 3 h, per oblast (sorted by skill vs recency)

| region | base rate | Brier model | Brier recency | AUC model | AUC recency | skill vs recency |
|---|---|---|---|---|---|---|
| Lvivska oblast | 0.0090 | 0.0116 | 0.0099 | 0.7075 | 0.4910 | -0.1724 |
| Ivano-Frankivska oblast | 0.0119 | 0.0146 | 0.0126 | 0.6211 | 0.4879 | -0.1559 |
| Chernivetska oblast | 0.0269 | 0.0299 | 0.0260 | 0.5955 | 0.5891 | -0.1508 |
| Zakarpatska oblast | 0.0090 | 0.0105 | 0.0096 | 0.5762 | 0.4910 | -0.0990 |
| Rivnenska oblast | 0.0627 | 0.0585 | 0.0552 | 0.7084 | 0.6692 | -0.0604 |
| Volynska oblast | 0.0279 | 0.0296 | 0.0289 | 0.5832 | 0.4902 | -0.0210 |
| Khmelnytska oblast | 0.0706 | 0.0606 | 0.0609 | 0.7554 | 0.6847 | 0.0042 |
| Chernihivska oblast | 0.7592 | 0.1390 | 0.1426 | 0.7281 | 0.7148 | 0.0258 |
| Ternopilska oblast | 0.0299 | 0.0285 | 0.0296 | 0.7462 | 0.5036 | 0.0380 |
| Donetska oblast | 0.1861 | 0.1528 | 0.1598 | 0.5943 | 0.5436 | 0.0438 |
| Kirovohradska oblast | 0.4975 | 0.2295 | 0.2413 | 0.6468 | 0.6456 | 0.0487 |
| Kyivska oblast | 0.4537 | 0.2265 | 0.2393 | 0.6612 | 0.6196 | 0.0532 |
| Zhytomyrska oblast | 0.2030 | 0.1471 | 0.1565 | 0.7164 | 0.6070 | 0.0602 |
| Vinnytska oblast | 0.1791 | 0.1336 | 0.1431 | 0.7254 | 0.6291 | 0.0661 |
| Cherkaska oblast | 0.3851 | 0.2140 | 0.2297 | 0.6978 | 0.6362 | 0.0682 |
| Kyiv City | 0.2985 | 0.1965 | 0.2132 | 0.7532 | 0.6705 | 0.0784 |
| Khersonska oblast | 0.6149 | 0.2038 | 0.2276 | 0.6740 | 0.6210 | 0.1046 |
| Zaporizka oblast | 0.3493 | 0.2138 | 0.2416 | 0.6452 | 0.5647 | 0.1148 |
| Poltavska oblast | 0.6667 | 0.1869 | 0.2113 | 0.6890 | 0.6358 | 0.1153 |
| Mykolaivska oblast | 0.7532 | 0.1574 | 0.1976 | 0.7141 | 0.6987 | 0.2035 |
| Odeska oblast | 0.7323 | 0.1681 | 0.2128 | 0.6531 | 0.6722 | 0.2098 |
| Kharkivska oblast | 0.8746 | 0.0584 | 0.0749 | 0.9004 | 0.8792 | 0.2209 |
| Sumska oblast | 0.8169 | 0.0959 | 0.1361 | 0.8103 | 0.7596 | 0.2954 |
| Dnipropetrovska oblast | 0.8438 | 0.0770 | 0.1131 | 0.8716 | 0.8076 | 0.3189 |

## 3 h calibration table (model)

| predicted bin | mean predicted | observed rate | hours |
|---|---|---|---|
| (-0.001, 0.1] | 0.036 | 0.027 | 8258 |
| (0.1, 0.2] | 0.148 | 0.126 | 2543 |
| (0.2, 0.3] | 0.249 | 0.255 | 1844 |
| (0.3, 0.4] | 0.349 | 0.361 | 1566 |
| (0.4, 0.5] | 0.450 | 0.473 | 1519 |
| (0.5, 0.6] | 0.551 | 0.591 | 1448 |
| (0.6, 0.7] | 0.653 | 0.694 | 1610 |
| (0.7, 0.8] | 0.748 | 0.802 | 1732 |
| (0.8, 0.9] | 0.854 | 0.844 | 1630 |
| (0.9, 1.0] | 0.951 | 0.951 | 1970 |
