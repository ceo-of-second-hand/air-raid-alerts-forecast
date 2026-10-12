# Air Raid Alerts in Ukraine — Time Series Forecasting

Forecasting air raid alerts per oblast from the official alert history, with a strict no-leakage setup.

> Work in progress. Full decision log with evidence: [`DECISIONS.md`](DECISIONS.md). Every look at the test period: [`experiments.md`](experiments.md).

## Data
- **Source:** `official_data_en.csv` from [Vadimkin/ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) (MIT), parsed from the official Telegram channel [@air_alert_ua](https://t.me/air_alert_ua).
- **Coverage used:** **2025-12-01 → 2026-09-06 21:00 UTC** (midnight Kyiv), the period with district-level alerts. The channel stopped posting on 2026-09-07, so this is the most recent reliable official data.
- **Why not the other sources** (details and evidence in `reports/d1_crosscheck.md` and `DECISIONS.md`):
  - *Volunteer CSV (єТривога):* in a one-day sample, its parser assigned about 1 in 30 alert messages to an oblast not mentioned in the message (e.g. Кам'янець-Подільський → Lviv, Прилуцький → Volyn) and drops extra oblasts in multi-oblast messages.
  - *alerts.in.ua API:* needs a token, only keeps one month of history, and doesn't overlap with the official file.
- **Cleaning:** exact duplicate rows removed (about 38% of official rows). Luhansk and Crimea excluded (see below).

## Locked decisions
| Area | Decision |
|---|---|
| Leakage | Every input is computed as of forecast time *t*. Intervals are cut at *t*. Statistics are fitted on training data only. Training rows whose label window reaches past *t* are purged. |
| Evaluation | Walk-forward backtest on 10 two-week periods before the test period; the test period (last 6 weeks) is scored **once**. Main metric: Brier skill vs a "what's happening right now" rule (recency baseline); climatology is secondary. |
| Regions | 24 regions (23 oblasts + Kyiv City). **Luhansk and Crimea are excluded** because their alert has been permanent since 2022 and carries no forecastable signal. **This is not a claim that they are safe.** No forecasts are produced for them. |
| Target | **P(an alert starts in the oblast within the next 3 h)**, with 1 h and 6 h also reported, a new forecast every hour. Chosen over daily counts and alert duration by a measured comparison (`reports/d2_target_comparison.md`). |
| Model | Gradient boosting (GBM) with recent-alert, calendar, national and **neighbouring-oblast** features. Chosen over logistic regression by rules fixed before the comparison (`reports/d7_d8_models.md`). |
| Unit | Oblast. Since late 2025 official alerts are raion-level, so an oblast event = any raion- or oblast-level alert in that oblast. |

### Features we decided against
- **Distance to the border / occupied territory.** We planned to test it, then dropped it: the value is fixed for each oblast, so it carries no information beyond *which oblast it is*, and the GBM already gets the oblast identity as an input. Any per-oblast effect it could capture, the model can already learn directly. The "dangerous neighbourhood" idea is covered instead by the neighbouring-oblast features, which change over time.
- **Weather.** Only *forecast* weather available at forecast time would be leak-free (observed weather would leak), and we had no source for it.

## How to run
Run from the repo root, in this order (Python 3.12, `pip install -r requirements.txt`):

| # | Script | Role | What it does | Output |
|---|---|---|---|---|
| 1 | `scripts/download_data.py` | **pipeline** | Downloads the data from a fixed upstream commit and checks each file's SHA-256 | `data/raw/` |
| 2 | `scripts/build_adjacency.py` | **pipeline** | Works out which oblasts share a border, from the district boundaries | `data/oblast_adjacency.json` |
| 3 | `scripts/crosscheck_d1.py` | exploration | Compares the official and volunteer files to choose the data source (D1) | `reports/d1_crosscheck.md` |
| 4 | `scripts/d2_target_comparison.py` | exploration ⚠️ | Compares three possible targets (D2). **Scores the test period**, so it is frozen: it refuses to run without `--i-know-this-scores-the-test-period` | `reports/d2_target_comparison.md` |
| 5 | `scripts/walk_forward.py` | validation | Model vs baselines on 10 two-week periods before the test period (D5) | `reports/walk_forward.md` |
| 6 | `scripts/d7_d8_models.py` | validation | LR vs GBM, with and without neighbour features: chooses the model (D7/D8) | `reports/d7_d8_models.md` |
| 7 | `scripts/drop_active_check.py` | validation | Removes the features that use alert end times (they leak, L37) and picks the start-only recency opponent (L38) | `reports/drop_active_check.md`, `reports/recency_choice.json` |
| 8 | `python -m pytest tests/` | checks | The three leakage tests (future data can't change features, purging, excluded regions) | pass/fail |
| 9 | `scripts/final_evaluation.py --dry-run` | **final model** | The final code path on the last validation period instead of the test (must match script 7 exactly) | `reports/final_evaluation_dryrun.md` |
| 10 | `scripts/final_evaluation.py --score-test` | **final model** | Trains on everything before the test period and scores it **once**. Refuses to run twice (lock file) | `reports/final_evaluation.md`, `reports/final_predictions.csv` |

- **Exploration** scripts were used to make decisions and aren't needed to reproduce the final model. **Validation** scripts justify the model choices. **Pipeline**, **checks** and **final model** are what produces the result.
- Shared code (data loading, the hourly feature table, neighbour features) lives in the exploration/validation scripts and is imported from there. Moving it into one module is in the backlog (`specs/final-evaluation-plan.md`); it doesn't change any result.

## Limitations
- **Data ends 2026-09-06.** The official channel stopped posting on 2026-09-07, so the model hasn't been checked on anything later.
- **Only ~9 months of training data** (the district-level period), because the alert unit changed in late 2025.
- **The target was chosen partly by looking at the test period** (`experiments.md` #1), so the test is not fully "unseen" for that choice.
- **Imperfect end times in the official data:** 623 alerts last over 24 h (possibly missed all-clear messages), and some alerts with a missing all-clear got an end time of start + 1 h without being flagged. The target uses only start times, but the "alert active right now" features use end times. Left as-is in v1.
- **Parsed, not raw, official data:** the file is a third-party parse of the Telegram channel. We checked the parser on the channel's last 1,199 messages (all alert messages parsed), but not over the full period.

## Future work (with more time)
- **Data after 2026-09-07** from the alerts.in.ua API (token), collected daily, also used as a **prospective test** on days after the model is frozen.
- **Own parser of the єТривога channel**: raion-level, keeping red / yellow / threat as separate types, validated raion-by-raion against the official file.
- **Text signals**: launch reports from occupied territory and across the border, which arrive before alerts in target regions.
- **Forecast weather** as a feature, from a source that keeps historical forecasts.
