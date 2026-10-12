# Final evaluation (DRY RUN on the last validation period)

## In short

- **What this does:** trains the final model (GBM + neighbour features, start times only) on all data before 2026-07-12 and forecasts every hour of the last validation period (dry run) (2026-07-12 21:00 → 2026-07-26 20:00 UTC, 24 oblasts).
- **3-hour forecasts vs the "recent alert starts" rule (recency, k=6h):** the model's Brier score (how far its probabilities are from what happened; lower is better) is **5.1% lower**. Better in **2 of 2** weeks.
- **vs the oblast's usual rate for that hour and weekday (climatology):** 10.8% lower.
- **Ranking (AUC: chance that an hour with an alert start gets a higher score than one without; 0.5 = random):** model 0.921 vs recency 0.921 over all oblasts together. **This mostly measures which oblast is active.** Within a single oblast the average is model 0.553 vs recency 0.519 (7 oblasts had no alert starts or no quiet hours, so no AUC).
- **Calibration:** see `calibration_dryrun.png` and the table below (when the model says x%, how often did an alert start).

## All metrics

| metric | 1h | 3h | 6h |
|---|---|---|---|
| recency rule | k=3h | k=6h | k=6h |
| base rate | 0.2224 | 0.4008 | 0.5047 |
| Brier model | 0.1201 | 0.1133 | 0.0891 |
| Brier recency | 0.1243 | 0.1194 | 0.0917 |
| Brier clim | 0.1281 | 0.1270 | 0.0984 |
| skill vs recency | 0.0338 | 0.0507 | 0.0286 |
| skill vs clim | 0.0624 | 0.1078 | 0.0950 |
| AUC model | 0.8669 | 0.9208 | 0.9527 |
| AUC recency | 0.8628 | 0.9208 | 0.9543 |
| mean AUC per oblast | 0.5759 | 0.5526 | 0.4880 |
| mean AUC per oblast recency | 0.5114 | 0.5185 | 0.5094 |
| oblasts without AUC | 7 | 7 | 10 |
| log-loss model | 0.3608 | 0.3527 | 0.2950 |
| log-loss recency | 0.3734 | 0.3686 | 0.3043 |
| accuracy@0.5 | 0.8174 | 0.8348 | 0.8779 |
| majority-class acc | 0.7776 | 0.5992 | 0.5047 |

## 3 h, week by week

| week | from | Brier model | Brier recency | skill vs recency | model better |
|---|---|---|---|---|---|
| 1 | 2026-07-12 | 0.1105 | 0.1180 | 0.0637 | yes |
| 2 | 2026-07-19 | 0.1162 | 0.1208 | 0.0378 | yes |

## 3 h, per oblast (sorted by skill vs recency)

| region | base rate | Brier model | Brier recency | AUC model | AUC recency | skill vs recency |
|---|---|---|---|---|---|---|
| Khmelnytska oblast | 0.0000 | 0.0118 | 0.0030 | nan | nan | -2.9678 |
| Zakarpatska oblast | 0.0000 | 0.0025 | 0.0008 | nan | nan | -1.9631 |
| Ternopilska oblast | 0.0000 | 0.0043 | 0.0015 | nan | nan | -1.9480 |
| Chernivetska oblast | 0.0000 | 0.0039 | 0.0014 | nan | nan | -1.7960 |
| Lvivska oblast | 0.0000 | 0.0032 | 0.0012 | nan | nan | -1.6987 |
| Ivano-Frankivska oblast | 0.0000 | 0.0028 | 0.0011 | nan | nan | -1.4895 |
| Volynska oblast | 0.0000 | 0.0048 | 0.0023 | nan | nan | -1.1094 |
| Rivnenska oblast | 0.0090 | 0.0204 | 0.0132 | 0.3768 | 0.4909 | -0.5496 |
| Vinnytska oblast | 0.1141 | 0.1014 | 0.0991 | 0.6012 | 0.5927 | -0.0232 |
| Kyiv City | 0.2252 | 0.1778 | 0.1752 | 0.5533 | 0.5675 | -0.0150 |
| Zhytomyrska oblast | 0.1982 | 0.1708 | 0.1687 | 0.5118 | 0.4888 | -0.0128 |
| Zaporizka oblast | 0.4565 | 0.2470 | 0.2463 | 0.5667 | 0.5628 | -0.0028 |
| Khersonska oblast | 0.6757 | 0.2390 | 0.2390 | 0.4349 | 0.4878 | 0.0000 |
| Cherkaska oblast | 0.4595 | 0.2543 | 0.2615 | 0.5828 | 0.5930 | 0.0274 |
| Kyivska oblast | 0.4745 | 0.2517 | 0.2589 | 0.5762 | 0.5322 | 0.0279 |
| Poltavska oblast | 0.7417 | 0.2009 | 0.2127 | 0.5719 | 0.5124 | 0.0553 |
| Sumska oblast | 0.9339 | 0.0637 | 0.0687 | 0.5532 | 0.5000 | 0.0728 |
| Dnipropetrovska oblast | 0.9489 | 0.0495 | 0.0538 | 0.5961 | 0.5000 | 0.0801 |
| Kirovohradska oblast | 0.6156 | 0.2576 | 0.2804 | 0.4810 | 0.4644 | 0.0813 |
| Chernihivska oblast | 0.9039 | 0.0944 | 0.1036 | 0.4973 | 0.4950 | 0.0892 |
| Kharkivska oblast | 0.9700 | 0.0288 | 0.0322 | 0.7854 | 0.5000 | 0.1051 |
| Donetska oblast | 0.2613 | 0.1709 | 0.1934 | 0.6925 | 0.5320 | 0.1164 |
| Mykolaivska oblast | 0.7868 | 0.1873 | 0.2182 | 0.5449 | 0.4912 | 0.1415 |
| Odeska oblast | 0.8438 | 0.1709 | 0.2290 | 0.4681 | 0.5043 | 0.2536 |

## 3 h calibration table (model)

| predicted bin | mean predicted | observed rate | hours |
|---|---|---|---|
| (-0.001, 0.1] | 0.037 | 0.010 | 2681 |
| (0.1, 0.2] | 0.147 | 0.145 | 650 |
| (0.2, 0.3] | 0.248 | 0.250 | 572 |
| (0.3, 0.4] | 0.349 | 0.398 | 475 |
| (0.4, 0.5] | 0.452 | 0.503 | 515 |
| (0.5, 0.6] | 0.551 | 0.604 | 560 |
| (0.6, 0.7] | 0.651 | 0.726 | 736 |
| (0.7, 0.8] | 0.743 | 0.806 | 510 |
| (0.8, 0.9] | 0.860 | 0.906 | 449 |
| (0.9, 1.0] | 0.948 | 0.949 | 844 |
