# L37/L38: dropping the features that use alert end times

## In short

- **What this does:** removes the two features that depend on alert end times (alerts active in the oblast now, neighbours with an alert active now). The official data sets some end times using later alerts, so these features leak. Same 10 two-week validation periods as before; the test period is not used.
- **What we gave up (3 h):** the mean Brier score changed by **+4.6%** (positive = worse). Adopted regardless (L37).
- **New opponent (3 h):** the best recency rule that uses only alert starts is **recency k=6h** (L38).
- **Still better than that rule?** In **10 of 10** periods, by 3.0% on average (rule L25: at least 9) → **PASS**.

## Summary

| horizon | recency opponent | cost of dropping (mean Brier change) | periods won vs recency | mean skill vs recency |
|---|---|---|---|---|
| 1h | recency k=3h | 0.0627 | 10/10 | 0.0273 |
| 3h | recency k=6h | 0.0463 | 10/10 | 0.0301 |
| 6h | recency k=6h | 0.0209 | 9/10 | 0.0194 |

## 1h, per period (Brier, lower is better)

| period start | recency k=1h | recency k=3h | recency k=6h | with active | without active | skill vs recency |
|---|---|---|---|---|---|---|
| 2026-03-08 | 0.1080 | 0.1078 | 0.1083 | 0.0993 | 0.1068 | 0.0097 |
| 2026-03-22 | 0.1369 | 0.1360 | 0.1365 | 0.1220 | 0.1321 | 0.0290 |
| 2026-04-05 | 0.1011 | 0.1010 | 0.1009 | 0.0931 | 0.0989 | 0.0208 |
| 2026-04-19 | 0.1100 | 0.1097 | 0.1098 | 0.1007 | 0.1063 | 0.0302 |
| 2026-05-03 | 0.1098 | 0.1091 | 0.1094 | 0.1008 | 0.1067 | 0.0220 |
| 2026-05-17 | 0.1235 | 0.1221 | 0.1230 | 0.1112 | 0.1173 | 0.0390 |
| 2026-05-31 | 0.1102 | 0.1103 | 0.1102 | 0.1007 | 0.1067 | 0.0327 |
| 2026-06-14 | 0.1137 | 0.1133 | 0.1140 | 0.1048 | 0.1101 | 0.0279 |
| 2026-06-28 | 0.1109 | 0.1106 | 0.1105 | 0.1000 | 0.1075 | 0.0275 |
| 2026-07-12 | 0.1240 | 0.1243 | 0.1242 | 0.1143 | 0.1201 | 0.0338 |

## 3h, per period (Brier, lower is better)

| period start | recency k=1h | recency k=3h | recency k=6h | with active | without active | skill vs recency |
|---|---|---|---|---|---|---|
| 2026-03-08 | 0.1198 | 0.1187 | 0.1197 | 0.1128 | 0.1169 | 0.0240 |
| 2026-03-22 | 0.1768 | 0.1735 | 0.1733 | 0.1579 | 0.1692 | 0.0237 |
| 2026-04-05 | 0.1248 | 0.1227 | 0.1222 | 0.1138 | 0.1202 | 0.0163 |
| 2026-04-19 | 0.1323 | 0.1324 | 0.1327 | 0.1231 | 0.1298 | 0.0217 |
| 2026-05-03 | 0.1462 | 0.1437 | 0.1415 | 0.1310 | 0.1368 | 0.0334 |
| 2026-05-17 | 0.1571 | 0.1547 | 0.1560 | 0.1432 | 0.1482 | 0.0504 |
| 2026-05-31 | 0.1290 | 0.1289 | 0.1280 | 0.1213 | 0.1263 | 0.0132 |
| 2026-06-14 | 0.1431 | 0.1424 | 0.1431 | 0.1366 | 0.1409 | 0.0156 |
| 2026-06-28 | 0.1251 | 0.1236 | 0.1238 | 0.1117 | 0.1174 | 0.0517 |
| 2026-07-12 | 0.1225 | 0.1212 | 0.1194 | 0.1092 | 0.1133 | 0.0507 |

## 6h, per period (Brier, lower is better)

| period start | recency k=1h | recency k=3h | recency k=6h | with active | without active | skill vs recency |
|---|---|---|---|---|---|---|
| 2026-03-08 | 0.1112 | 0.1107 | 0.1113 | 0.1079 | 0.1107 | 0.0057 |
| 2026-03-22 | 0.1724 | 0.1671 | 0.1653 | 0.1610 | 0.1654 | -0.0004 |
| 2026-04-05 | 0.1261 | 0.1243 | 0.1232 | 0.1183 | 0.1223 | 0.0075 |
| 2026-04-19 | 0.1307 | 0.1316 | 0.1329 | 0.1261 | 0.1291 | 0.0286 |
| 2026-05-03 | 0.1474 | 0.1430 | 0.1401 | 0.1334 | 0.1371 | 0.0209 |
| 2026-05-17 | 0.1637 | 0.1620 | 0.1620 | 0.1581 | 0.1587 | 0.0209 |
| 2026-05-31 | 0.1245 | 0.1242 | 0.1230 | 0.1191 | 0.1216 | 0.0115 |
| 2026-06-14 | 0.1511 | 0.1500 | 0.1503 | 0.1459 | 0.1466 | 0.0248 |
| 2026-06-28 | 0.1153 | 0.1145 | 0.1148 | 0.1068 | 0.1095 | 0.0463 |
| 2026-07-12 | 0.0949 | 0.0927 | 0.0917 | 0.0870 | 0.0891 | 0.0286 |
