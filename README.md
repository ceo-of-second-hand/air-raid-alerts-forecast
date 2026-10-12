# Air Raid Alerts in Ukraine — Time Series Forecasting

Forecasting air raid alerts per oblast from the official alert history, with a strict no-leakage setup.

Full decision log with evidence: [`DECISIONS.md`](DECISIONS.md). Every look at the test period: [`experiments.md`](experiments.md). Plan for the final steps: [`specs/final-evaluation-plan.md`](specs/final-evaluation-plan.md).

## Start here
- **To understand the result:** read [Results](#results) below, then `reports/final_evaluation.md`. Every choice behind it, with evidence, is in `DECISIONS.md` (the L-rules).
- **To check it:** `pip install -r requirements.txt`, then `python scripts/download_data.py`, `python scripts/build_adjacency.py`, `python -m pytest tests/`, `python scripts/final_evaluation.py --dry-run`.
- **The test period has already been scored once** (`reports/.test_scored`). `final_evaluation.py --score-test` refuses to run again unless given `--rerun-reason "..."`, which is logged in `experiments.md`.
- **`.claude/skills/`** is the AI tooling Ivanka set up and used in this Claude Code session (how long outputs and script results are presented). It isn't part of the model.

## Results

Final model scored once on the test period (2026-07-26 → 2026-09-06, 24 oblasts, every hour), `reports/final_evaluation.md`.

**Main number: Brier skill** (how much lower the model's Brier score is than the opponent's; Brier = how far predicted probabilities are from what happened).

| Horizon | vs recency rule | vs climatology | Weeks better than recency |
|---|---|---|---|
| 1 h | +5.8% | +11.5% | — |
| **3 h** | **+10.4%** | **+19.2%** | **6 of 6** |
| 6 h | +6.1% | +15.4% | — |

- **How to read +10.4%:** on the 10 validation periods before the test, the same model averaged **+3.0%** (better in 10 of 10). The test result is at the high end, driven by the last two weeks (+12% and +26%); our judgement is that a realistic expectation lies somewhere between the two, not at +10%.
- **Calibration** is good: when the model says x%, alerts started in about x% of hours (`reports/calibration_test.png`).
- **AUC is not our main number, and within an oblast it is weak.** Over all oblasts together the AUC is 0.91, but that mostly measures *which oblast* is active. **Within a single oblast** the average is **0.70** (recency rule 0.63) in the test period, and **0.66** (recency 0.55, climatology 0.54) over 20 weeks of validation (`reports/within_oblast_auc.md`). The 0.55 seen in one 2-week validation period was a weak stretch, not the norm. So the model is much better at estimating *how likely* an alert is than at telling *which hours* within an oblast will have one.

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
| Evaluation | Walk-forward backtest on 10 two-week periods before the test period. The **final model scored the test period (last 6 weeks) once**; the test period had been seen 3× before, during target selection (`experiments.md` #1, #2, #4). Main metric: **Brier skill vs a "recent alert starts" rule** (recency baseline); climatology is secondary. |
| Regions | 24 regions (23 oblasts + Kyiv City). **Luhansk and Crimea are excluded** because their alert has been permanent since 2022 and carries no forecastable signal. **This is not a claim that they are safe.** No forecasts are produced for them. |
| Target | **P(an alert starts in the oblast within the next 3 h)**, with 1 h and 6 h also reported, a new forecast every hour. Chosen over daily counts and alert duration by a measured comparison (`reports/d2_target_comparison.md`). |
| Model | Gradient boosting (GBM) with recent alert starts, calendar, national and **neighbouring-oblast** features, **start times only**. Chosen over logistic regression by rules fixed before the comparison (`reports/d7_d8_models.md`). Features using alert end times were removed because they leak (`reports/drop_active_check.md`). |
| Unit | Oblast. Since late 2025 official alerts are raion-level, so an oblast event = any raion- or oblast-level alert in that oblast. |

### Features we decided against
- **Distance to the border / occupied territory.** We planned to test it, then dropped it: the value is fixed for each oblast, so it carries no information beyond *which oblast it is*, and the GBM already gets the oblast identity as an input. Any per-oblast effect it could capture, the model can already learn directly. The "dangerous neighbourhood" idea is covered instead by the neighbouring-oblast features, which change over time.
- **Weather.** Only *forecast* weather available at forecast time would be leak-free (observed weather would leak), and we had no source for it.

## How to run
Run from the repo root (Python 3.12, `pip install -r requirements.txt`). Scripts are grouped by role; within a group, run them in the order listed.

### Final pipeline (produces the result)
| Script | What it does | Output |
|---|---|---|
| `scripts/download_data.py` | Downloads the data from a fixed upstream commit and checks each file's SHA-256 | `data/raw/` |
| `scripts/build_adjacency.py` | Works out which oblasts share a border, from the district boundaries | `data/oblast_adjacency.json` |
| `python -m pytest tests/` | The three leakage tests (future data can't change features, purging, excluded regions) | pass/fail |
| `scripts/final_evaluation.py --dry-run` | The final code path on the last validation period instead of the test (matches `drop_active_check` exactly) | `reports/final_evaluation_dryrun.md` |
| `scripts/final_evaluation.py --score-test` | Trains on everything before the test period and scores it **once** (already done; lock file) | `reports/final_evaluation.md`, `reports/final_predictions.csv` |

### Validation (justifies the model choices; test period not used)
| Script | What it does | Output |
|---|---|---|
| `scripts/walk_forward.py` | Model vs baselines on 10 two-week periods before the test period (D5) | `reports/walk_forward.md` |
| `scripts/d7_d8_models.py` | LR vs GBM, with and without neighbour features: chooses the model (D7/D8) | `reports/d7_d8_models.md` |
| `scripts/drop_active_check.py` | Removes the features that use alert end times (they leak, L37) and picks the start-only recency opponent (L38) | `reports/drop_active_check.md`, `reports/recency_choice.json` |
| `scripts/within_oblast_auc.py` | Per-oblast AUC over all 10 validation periods | `reports/within_oblast_auc.md` |

### Exploration (used to make early decisions; not needed to reproduce the result)
| Script | What it does | Output |
|---|---|---|
| `scripts/crosscheck_d1.py` | Compares the official and volunteer files to choose the data source (D1) | `reports/d1_crosscheck.md` |
| `scripts/d2_target_comparison.py` ⚠️ | Compares three possible targets (D2). **Scores the test period**, so it is frozen: it refuses to run without `--i-know-this-scores-the-test-period` | `reports/d2_target_comparison.md` |

**How the code connects:** there is no shared module yet. Each script imports shared code from the one before it, in a chain: `d2_target_comparison` (data loading, hourly feature table) → `walk_forward` (periods, baselines) → `d7_d8_models` (neighbour features) → `drop_active_check` (final feature set, model settings) → `final_evaluation`. So the final model depends on the frozen exploration script for its core code. A shared module is in the backlog (`specs/final-evaluation-plan.md`) and wouldn't change any result.

## Limitations
- **Data ends 2026-09-06.** The official channel stopped posting on 2026-09-07, so the model hasn't been checked on anything later.
- **Only ~9 months of training data** (the district-level period), because the alert unit changed in late 2025.
- **The target was chosen partly by looking at the test period** (`experiments.md` #1), so the test is not fully "unseen" for that choice.
- **Imperfect end times in the official data:** 623 alerts last over 24 h (possibly missed all-clear messages), and some alerts with a missing all-clear got an end time of start + 1 h without being flagged. The target and the final model's features use only start times (the end-time features were removed, L37), so this affects the cleaned data but not the final model's inputs.
- **The leak fix cost accuracy:** removing the features that use alert end times made the Brier score 4.6% worse in validation (3 h). Also, when an all-clear is missing and a new alert follows within 3 h, the parser overwrote the first alert's start; those starts are lost from the data.
- **Last days of the test period:** alerts still open when the channel stopped (2026-09-07 06:09 UTC) were never written, so the final hours may miss some alert starts.
- **Parsed, not raw, official data:** the file is a third-party parse of the Telegram channel. We checked the parser on the channel's last 1,199 messages (all alert messages parsed), but not over the full period.

## Future work (with more time)
- **Data after 2026-09-07** from the alerts.in.ua API (token), collected daily, also used as a **prospective test** on days after the model is frozen.
- **Own parser of the єТривога channel**: raion-level, keeping red / yellow / threat as separate types, validated raion-by-raion against the official file.
- **Text signals**: launch reports from occupied territory and across the border, which arrive before alerts in target regions.
- **Forecast weather** as a feature, from a source that keeps historical forecasts.
