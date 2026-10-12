# Within-oblast AUC over 20 weeks of validation (3 h)

## In short

- **What this does:** for each oblast separately, measures how well each method ranks hours with an alert start above hours without one (AUC; 0.5 = coin flip, 1 = perfect), over all 10 validation periods (3330 hours per oblast). The test period is not used.
- **Average over 24 oblasts:** model **0.659**, recency rule 0.554, climatology 0.537.
- **Pooled over all oblasts**, for comparison: model 0.882.

## Per oblast (sorted by base rate)

| region | base rate | quiet hours | AUC model | AUC recency | AUC clim |
|---|---|---|---|---|---|
| Zakarpatska oblast | 0.035 | 3213 | 0.674 | 0.508 | 0.522 |
| Ivano-Frankivska oblast | 0.039 | 3200 | 0.672 | 0.506 | 0.546 |
| Lvivska oblast | 0.040 | 3197 | 0.693 | 0.551 | 0.504 |
| Ternopilska oblast | 0.045 | 3179 | 0.676 | 0.492 | 0.501 |
| Chernivetska oblast | 0.050 | 3163 | 0.705 | 0.556 | 0.484 |
| Volynska oblast | 0.051 | 3161 | 0.701 | 0.506 | 0.513 |
| Khmelnytska oblast | 0.071 | 3095 | 0.738 | 0.581 | 0.476 |
| Rivnenska oblast | 0.083 | 3055 | 0.731 | 0.581 | 0.505 |
| Vinnytska oblast | 0.125 | 2913 | 0.654 | 0.603 | 0.477 |
| Kyiv City | 0.174 | 2749 | 0.607 | 0.562 | 0.510 |
| Zhytomyrska oblast | 0.196 | 2676 | 0.664 | 0.590 | 0.506 |
| Donetska oblast | 0.305 | 2315 | 0.674 | 0.516 | 0.694 |
| Cherkaska oblast | 0.317 | 2275 | 0.616 | 0.574 | 0.524 |
| Kyivska oblast | 0.371 | 2094 | 0.655 | 0.596 | 0.505 |
| Kirovohradska oblast | 0.427 | 1909 | 0.623 | 0.596 | 0.505 |
| Zaporizka oblast | 0.501 | 1662 | 0.637 | 0.496 | 0.623 |
| Khersonska oblast | 0.535 | 1547 | 0.608 | 0.534 | 0.540 |
| Odeska oblast | 0.549 | 1501 | 0.642 | 0.544 | 0.535 |
| Mykolaivska oblast | 0.587 | 1376 | 0.640 | 0.599 | 0.565 |
| Poltavska oblast | 0.645 | 1182 | 0.611 | 0.582 | 0.526 |
| Chernihivska oblast | 0.808 | 640 | 0.632 | 0.566 | 0.523 |
| Sumska oblast | 0.892 | 360 | 0.633 | 0.552 | 0.592 |
| Dnipropetrovska oblast | 0.916 | 280 | 0.626 | 0.575 | 0.565 |
| Kharkivska oblast | 0.959 | 137 | 0.700 | 0.538 | 0.653 |
