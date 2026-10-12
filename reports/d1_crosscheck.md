# D1 cross-check: official vs volunteer

## In short

- **What this does:** checks whether the two alert files in the Vadimkin repo ("official", parsed from the @air_alert_ua channel, and "volunteer", parsed from the єТривога channel) contain the same alerts, over the period both cover (2022-03-15 → 2026-09-07).
- **Same alerts?** In the latest year, only **56%** of official alerts have a volunteer alert starting within ±15 min, and only **32%** the other way round (71% / 3% if only whole-oblast official alerts count). The threshold fixed in advance was 90% both ways, so the check **failed**.
- **Start times:** when an alert is in both files, the start times agree closely (typical gap 0.3 min).
- **Made-up end times:** volunteer alerts with no recorded end get start + 30 min; the matching official alerts actually lasted a median of 321 min.
- **Later finding (see `DECISIONS.md`):** the volunteer parser assigns some alerts to the wrong oblast, so the official file was chosen as the data source.

Overlap window: 2022-03-15 16:10:34+00:00 → 2026-09-07 05:28:22+00:00. Regions: 24. Episodes = overlapping alerts merged per region. Match = same region, start within ±tol min.

Volunteer episodes: 109719; official (i) union: 80287; official (ii) oblast-only: 65313.

## Q1. Same alerts? (match rate %, both directions)

| rollup | tol_min | period | off→vol % | vol→off % |
|---|---|---|---|---|
| i_union | 5 | all | 71.0 | 51.9 |
| i_union | 5 | latest 4Q | 47.0 | 26.9 |
| i_union | 15 | all | 76.0 | 55.6 |
| i_union | 15 | latest 4Q | 55.8 | 32.1 |
| i_union | 30 | all | 81.3 | 59.6 |
| i_union | 30 | latest 4Q | 66.9 | 38.8 |
| ii_oblast_only | 5 | all | 79.2 | 47.1 |
| ii_oblast_only | 5 | latest 4Q | 62.8 | 2.5 |
| ii_oblast_only | 15 | all | 83.4 | 49.6 |
| ii_oblast_only | 15 | latest 4Q | 70.9 | 2.8 |
| ii_oblast_only | 30 | all | 87.1 | 52.0 |
| ii_oblast_only | 30 | latest 4Q | 78.3 | 3.2 |

### By quarter — rollup (i), ±15 min

| quarter | off→vol % | vol→off % |
|---|---|---|
| 2022Q1 | 81.2 | 91.3 |
| 2022Q2 | 93.0 | 97.3 |
| 2022Q3 | 96.1 | 94.5 |
| 2022Q4 | 94.7 | 87.9 |
| 2023Q1 | 92.2 | 77.4 |
| 2023Q2 | 91.3 | 76.0 |
| 2023Q3 | 92.1 | 81.9 |
| 2023Q4 | 87.9 | 75.0 |
| 2024Q1 | 81.0 | 68.1 |
| 2024Q2 | 83.1 | 64.2 |
| 2024Q3 | 79.5 | 54.8 |
| 2024Q4 | 67.3 | 45.8 |
| 2025Q1 | 63.4 | 44.0 |
| 2025Q2 | 66.1 | 43.9 |
| 2025Q3 | 63.4 | 39.8 |
| 2025Q4 | 59.1 | 32.4 |
| 2026Q1 | 56.3 | 32.9 |
| 2026Q2 | 58.2 | 33.9 |
| 2026Q3 | 49.7 | 28.9 |

### By region — rollup (i), ±15 min, latest 4Q

| region | off→vol % | vol→off % | n_off | n_vol |
|---|---|---|---|---|
| Dnipropetrovska oblast | 25.9 | 0.2 | 27 | 4257 |
| Donetska oblast | 34.6 | 12.4 | 500 | 1351 |
| Sumska oblast | 36.8 | 20.0 | 1725 | 3177 |
| Chernihivska oblast | 37.9 | 23.2 | 1544 | 2503 |
| Kharkivska oblast | 40.0 | 12.4 | 1421 | 4603 |
| Zaporizka oblast | 44.5 | 35.8 | 1676 | 2103 |
| Khersonska oblast | 55.8 | 47.1 | 1678 | 1979 |
| Zhytomyrska oblast | 57.7 | 52.9 | 504 | 554 |
| Kyivska oblast | 58.7 | 43.4 | 974 | 1321 |
| Rivnenska oblast | 60.4 | 57.4 | 222 | 235 |
| Poltavska oblast | 60.4 | 52.5 | 1676 | 1935 |
| Odeska oblast | 62.0 | 56.8 | 1714 | 1877 |
| Vinnytska oblast | 65.6 | 64.5 | 337 | 341 |
| Khmelnytska oblast | 67.2 | 68.9 | 198 | 193 |
| Cherkaska oblast | 67.9 | 67.8 | 899 | 898 |
| Mykolaivska oblast | 68.8 | 58.0 | 1861 | 2227 |
| Kyiv City | 72.3 | 61.2 | 559 | 657 |
| Kirovohradska oblast | 73.6 | 70.9 | 1181 | 1227 |
| Ternopilska oblast | 75.4 | 78.4 | 130 | 125 |
| Volynska oblast | 75.8 | 10.1 | 149 | 1126 |
| Lvivska oblast | 82.5 | 11.3 | 114 | 850 |
| Chernivetska oblast | 83.9 | 87.7 | 137 | 130 |
| Ivano-Frankivska oblast | 84.1 | 81.9 | 113 | 116 |
| Zakarpatska oblast | 93.3 | 95.1 | 105 | 102 |

## Q2. Start-time agreement (matched pairs, rollup (i), ±15 min)

| period | n | median signed (vol−off) min | median |diff| min | p90 |diff| min |
|---|---|---|---|---|
| all | 61037 | 0.3 | 0.3 | 3.0 |
| latest 4Q | 10872 | 0.3 | 0.3 | 8.6 |

## Q3. Duration agreement by `naive` (minutes, matched pairs)

| naive | n | vol_median_dur | off_median_dur | median_diff_vol_minus_off | p90_abs_diff |
|---|---|---|---|---|---|
| False | 60438 | 33.6 | 34.9 | -0.0 | 4.4 |
| True | 599 | 30.0 | 321.3 | -291.3 | 664.4 |

## Q4. Hourly label 'alert starts in this hour' (region × hour)

| rollup | period | agree % | kappa | off pos % | vol pos % |
|---|---|---|---|---|---|
| i_union | all | 93.798 | 0.647 | 8.289 | 11.134 |
| i_union | latest 4Q | 86.992 | 0.418 | 9.480 | 15.895 |
| ii_oblast_only | all | 93.671 | 0.614 | 6.779 | 11.134 |
| ii_oblast_only | latest 4Q | 84.460 | 0.050 | 0.676 | 15.895 |

### % time under alert, latest 4Q

| region | official (i) % | official (ii) % | volunteer % |
|---|---|---|---|
| Ivano-Frankivska oblast | 1.3 | 0.2 | 0.9 |
| Rivnenska oblast | 3.7 | 0.0 | 2.2 |
| Vinnytska oblast | 4.9 | 0.1 | 2.5 |
| Zakarpatska oblast | 2.5 | 0.2 | 3.0 |
| Ternopilska oblast | 1.6 | 0.2 | 3.8 |
| Khmelnytska oblast | 2.7 | 0.0 | 3.9 |
| Chernivetska oblast | 1.8 | 0.2 | 4.3 |
| Kyiv City | 6.7 | 6.7 | 4.6 |
| Zhytomyrska oblast | 9.2 | 0.4 | 5.5 |
| Cherkaska oblast | 12.6 | 0.3 | 7.0 |
| Kyivska oblast | 19.4 | 0.2 | 7.7 |
| Lvivska oblast | 1.4 | 0.2 | 8.3 |
| Odeska oblast | 19.2 | 0.7 | 9.0 |
| Kirovohradska oblast | 16.8 | 0.1 | 9.2 |
| Mykolaivska oblast | 22.0 | 1.2 | 13.4 |
| Khersonska oblast | 27.3 | 1.0 | 13.9 |
| Poltavska oblast | 33.0 | 0.0 | 14.8 |
| Volynska oblast | 1.9 | 0.2 | 15.7 |
| Dnipropetrovska oblast | 99.8 | 0.5 | 17.7 |
| Zaporizka oblast | 70.7 | 3.6 | 20.2 |
| Donetska oblast | 94.5 | 8.8 | 20.3 |
| Sumska oblast | 78.0 | 0.0 | 20.3 |
| Kharkivska oblast | 90.3 | 0.1 | 21.3 |
| Chernihivska oblast | 66.2 | 0.0 | 21.4 |

## Q5. Before vs after the raion switch (2025-12-01)

| rollup | period | off→vol % | vol→off % | hourly kappa |
|---|---|---|---|---|
| i_union | before switch | 81.592 | 64.190 | 0.714 |
| i_union | after switch | 55.069 | 31.906 | 0.417 |
| ii_oblast_only | before switch | 83.452 | 67.150 | 0.743 |
| ii_oblast_only | after switch | 70.551 | 1.138 | 0.020 |

## Q6. Anomalies (latest 4Q)

| region | official (i) % | official (ii) % | volunteer % | vol naive % | off→vol match % | vol→off match % |
|---|---|---|---|---|---|---|
| Volynska oblast | 1.9 | 0.2 | 15.7 | 3.8 | 75.8 | 10.1 |
| Rivnenska oblast | 3.7 | 0.0 | 2.2 | 3.8 | 60.4 | 57.4 |
| Khersonska oblast | 27.3 | 1.0 | 13.9 | 12.8 | 55.8 | 47.1 |
| Kyiv City | 6.7 | 6.7 | 4.6 | 16.9 | 72.3 | 61.2 |
| Kyivska oblast | 19.4 | 0.2 | 7.7 | 4.3 | 58.7 | 43.4 |
