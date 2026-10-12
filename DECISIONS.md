# Air Raid Alerts — Time Series Pet Project: Decisions

_Started 2026-10-12. Status legend: 🔒 locked · 🟡 to discuss_

---

## 🔒 Locked decisions

These come straight from the brief (or follow from it with no real alternative). We don't revisit them.

### Problem and stack
| # | Decision | Source |
|---|----------|--------|
| L1 | **Domain:** time series analysis and forecasting of **air raid alerts in Ukraine**. | Brief |
| L2 | **Language:** Python. | Brief |
| L3 | **Artifact:** a public **GitHub repository** with final, *working* code. It has to run end to end from a clean clone. | Brief |
| L4 | **AI is the main engineering tool.** This Claude Code session is the AI log. | Brief |

### Data and evaluation rules
| # | Decision | What it means in practice |
|---|----------|---------------------------|
| L5 | **Use the most recent data available.** | Pull data up to roughly today (Oct 2026) and record the snapshot date and source version in the repo. |
| L6 | **Evaluate on the latest period.** | Split by time, never at random. The test set is the most recent slice. |
| L7 | **No data leakage.** Nothing used for training or as an input may come from after the forecast time *t*. | Every feature is computed "as of *t*". Watch out for: (a) alerts that started before *t* but ended after *t*, because at *t* their end time and duration are still unknown; (b) rolling or normalising statistics fitted on the full series; (c) hyperparameter tuning on the test period; (d) external data that is revised after publication; (e) training labels whose horizon window reaches past *t* (purge the last *h* hours before *t*). |
| L8 | **Optional text/media data follows the same rule.** | Only use content whose *publication timestamp* is before *t*. |

### Tuning and evaluation protocol (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L13 | **Walk-forward CV on pre-test data**: several timestamp-based cutoffs, each with purging (drop training rows whose label window reaches past the cutoff); tune on these folds, then **score the test period once**. | Only option that measures how much results vary between periods; the loop is needed anyway for purging and refitting baselines, so the extra code is small. |
| L14 | **Log every look at the test score** in `experiments.md` (what was run, the score, what changed afterwards). | Keeps the final number honest and records material for the reflection. |

### Regions in scope (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L15 | **24 regions** (23 oblasts + Kyiv City). **Luhansk and Crimea are excluded** at load time from training, features and evaluation, with a test that fails if either appears. | Their alert has been permanent since 2022 and is not in the data. Including them would add fake "no alert" rows. |
| L16 | README states: excluded because their alert status is constant and has no forecastable signal, **not because they are safe**. The model gives no forecasts for them. | Honest scope statement. |
| L17 | Don't use their alert columns as features. Express "dangerous neighbourhood" as a **fixed geographic feature** (e.g. distance to the Russian/Belarusian border or occupied territory) and **keep it only if it improves the walk-forward backtest**. | Varies across all 24 regions. The model may already capture it via region identity, so it has to prove itself. A moving front line would need date-stamped map data (leakage). |

### Data source and unit (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L18 | **Data = official file only** (Vadimkin repo, parsed from @air_alert_ua), de-duplicated, **cut at 2026-09-06 21:00 UTC** (midnight Kyiv). "Most recent data available" = the latest reliable official data; the gap to today is stated in the README. | Authoritative source, exact-hashtag parser that we verified. The volunteer CSV assigns alerts to the wrong regions; alerts.in.ua needs a token and has no overlap with the official file; there's no time for our own parser. |
| L19 | **Unit = oblast** (24 regions, L15). | Decided by Ivanka. Since late 2025 the official data is raion-level, so an oblast event has to be defined from raion rows (see D2). |
| L20 | **Future work (not in v1):** alerts.in.ua API for data after Sep 7, own єТривога parser (raion-level, red/yellow/threat), prospective test, text data (launch reports). | Recorded so the README shows what we'd do with more time. |

### Forecast target (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L21 | **Target (a): P(an alert starts in oblast *r* within the next *h* hours)**. Oblast event = start of any raion- or oblast-level alert row (hromada rows excluded). **Main horizon 3 h**, with 1 h and 6 h reported alongside. (b) counts and (d) duration are not v1 targets. | `reports/d2_target_comparison.md`: at 3 h the model reaches AUC 0.91 and Brier +20% vs climatology. (b) is barely better than naive. (d) is no better than the oblast median and depends on unreliable end times. |

### Training window (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L22 | **Use only the raion-level period: 2025-12-01 → 2026-09-06 21:00 UTC** (~9 months). | The brief asks for recent data, and the alert unit changed in late 2025, so older rows define "events" differently. |

### Metrics and reference baseline (locked 2026-10-12)
| # | Decision | Why |
|---|----------|-----|
| L23 | **Main metric: Brier skill vs the best *recency* baseline**, a lookup of P(start within h \| oblast, start in last k h [, alert active now]) fitted on train. Skill vs climatology is reported as a secondary number. Also reported: AUC (overall + per oblast), log-loss, calibration plot. Accuracy only next to the majority-class reference. | Ivanka: climatology ignores the current situation, so it's too easy to beat. Measured: recency baselines beat climatology by 9–11%. Against them, the GBM's skill drops from **+20% to +9%** (3 h), and from +15% to +6% / +5% at 1 h / 6 h. A hard 0/1 persistence baseline is not a fair opponent under Brier (−63%). |

### Walk-forward folds (locked 2026-10-12, rule fixed BEFORE running)
| # | Decision | Why |
|---|----------|-----|
| L24 | **11 folds** on pre-test data: expanding training window (min 12 weeks from 2025-12-01), each validating on the next **2 weeks** (Feb 23 → Jul 26). Purged by *h*. Baselines refitted per fold. Recency reference = best of 4 variants **chosen on the fold's validation data** (favours the baseline). The test period (last 6 weeks) stays untouched. | 2-week blocks give enough folds to count wins. 12 weeks gives at least 12 samples per hour-of-week per oblast. |
| L24-note | ⚠️ **Correction after running:** the pre-test span is 33.98 weeks, not 34, so there are **10 folds** (first one Mar 8, 14 training weeks), not 11. My arithmetic error. The equivalent of "≥ 9/11" is **≥ 9/10** (p ≈ 0.011). The result (10/10) passes under either reading, so the conclusion doesn't depend on the error. | Disclosed, not silently fixed. |
| L25 | **Pass rule:** at 3 h, the model is "genuinely better" than recency if it **wins ≥ 9 of 11 folds** on Brier (sign test p ≈ 0.03, approximate because neighbouring folds are correlated). Per-fold results are reported, not just the mean. | Ivanka: show how many folds it wins, not just an average. |

### D7 + D8 experiment rules (fixed 2026-10-12 BEFORE running)
Same 10 walk-forward folds as L24; test period untouched. Four variants, all trained on the same rows in every fold:
**LR** and **GBM**, each with the **base** features and with **base + neighbour** features.
Neighbour features (as of *T*, from oblasts sharing a border, computed from the repo's `ukr_admin2.geojson`): alert starts in neighbours in the last 1 h and 3 h, and neighbours with an alert active at *T*.
LR = logistic regression with one-hot oblast, hour and weekday, log1p counts, scaling fitted inside each fold (pipeline).

| # | Rule |
|---|------|
| L26 | **Neighbour features are kept** if, for the chosen model, they improve Brier in **≥ 8 of 10 folds** and the mean Brier improves. |
| L27 | **Model choice:** LR is preferred (simpler, easier to explain) **unless GBM's mean skill vs recency is more than 1 percentage point higher**. Either way, the chosen model must still meet L25 (beats recency in ≥ 9/10 folds at 3 h). |

**Result (2026-10-12, `reports/d7_d8_models.md`):**
| # | Decision | Evidence |
|---|----------|----------|
| L28 | **Model = GBM + neighbour features** (neighbours from `data/oblast_adjacency.json`, built from map data by `scripts/build_adjacency.py`). | Neighbours improved both models in 9/10 periods (LR +1.3%, GBM +1.6% mean Brier). GBM beats recency by 5.0% on average vs LR 1.5% (gap 3.5 points > 1-point rule). GBM + neighbours beats recency in 10/10 periods. LR alone beats recency in only 7/10, so it would fail L25. |

### Remaining defaults (locked 2026-10-12)
| # | Decision |
|---|----------|
| L29 (D4) | Hourly time steps, a new forecast every hour, horizons 1/3/6 h, 3 h main. |
| L30 (D5) | Final test = last 6 weeks (2026-07-26 21:00 → 2026-09-06 21:00 UTC), scored once. |
| L31 (D6) | Final report: recency rule = main opponent, climatology = secondary; hard 0/1 persistence only as a warning example. |
| L32 (D8a) | **Distance-to-border feature dropped (supersedes the test planned in L17).** It's fixed per oblast, so it is a function of the oblast identity the GBM already uses. README explains why. |
| L33 (D8b) | No weather in v1 (only forecast weather would be leak-free; no source). Future work. |
| L34 (D11) | Long alerts (623 over 24 h) left as-is in v1; listed as a limitation in the README. |
| L35 (D12) | `scripts/` + `requirements.txt` (exact versions) + README section on what each script does, its output, run order, exploration vs final + `tests/` with leakage tests. `data/raw/` not in git (downloaded by script). |
| L36 (D13) | Public GitHub repo `air-raid-alerts-forecast`. Commits include a Co-Authored-By: Claude line. **Nothing is pushed without Ivanka's confirmation.** AI log via `/export` at the end. |

### Submission
| # | Decision |
|---|----------|
| L9 | Three parts: **repo link** + **full AI log export** (plain text) + **~100-word reflection** (plain text). |
| L10 | The reflection answers: *What went wrong? How did you adjust? Why is the final version better than the first?* So we need to **keep track of failed attempts as we go**, not just the final result. |
| L11 | **The process is graded, not just the result.** The log should show iteration, pushback on AI hallucinations, error fixes and architecture steering. Don't accept first outputs without checking them. |
| L12 | Stage 3 is an interview about the solution, so **every choice must be one Ivanka can explain and defend.** |

---

## 🟡 Open decisions (to discuss)

Each item lists the options and a **suggested default**. Nothing here is decided yet.

### D1. Data source
- Options: a community-maintained GitHub dataset of historical alerts (e.g. the *ukrainian-air-raid-sirens-dataset*), the alerts.in.ua API (needs a token), other public alert APIs, or our own collection.
- **Checked 2026-10-12** (Vadimkin/ukrainian-air-raid-sirens-dataset, MIT, repo commits daily):
  - `official_data_en.csv`: 299k rows, 2022-03-15 → **2026-09-07 (stale, ~5 weeks behind)**. Mostly **raion level since late 2025** (2026 Q3: 22k raion rows vs 171 oblast rows).
  - `volunteer_data_en.csv` (eTryvoga Telegram channel): 116k rows, 2022-02-25 → **2026-10-12 (today)**. **Oblast level only**, 25 regions. 4–10% of rows have `naive=True` (end time imputed as start + 30 min). ⚠️ Corrected: **5.0% over all time**, 0.3–9.6% by quarter; the 9.6% is from only Oct 1–12. Per region: 1.2% (Chernivtsi) to **16.5% (Kherson)**. Since late Sept the daily share is ~10–12%.
  - Permanent alerts in Luhansk and Crimea are **not** in either file.
  - ⚠️ **Provenance (checked in the repo code):** neither file is a government dataset. Both are produced by **one developer's Telegram scraper** (`process.py`, Telethon).
    - "Official" = parsed from **@air_alert_ua** ("Повітряна Тривога", whose channel description says the information comes from executive authorities). Locations come from hashtags. A message with any hashtag not in `states.json` is **skipped entirely**, so a missed start means a missing alert and a missed end means a too-long alert.
    - "Volunteer" = parsed from **@UkraineAlarmSignal** (єТривога). Region is guessed from words in the text. **"загроза" (threat), "небезпека", "до укриттів" count as alert starts.** A new start more than 3 h after an alert with no end message gives `naive=True`, end = start + 30 min.
    - So "official vs volunteer" is really "parser A on channel A vs parser B on channel B".
    - **єТривога raw messages (800 posts, 2026-10-12 02:28–16:49 UTC, via t.me/s):** message types are 🔴 red alert per raion, 🟡 yellow alert per raion, 🟢 all-clear per raion, threat warnings per town ("Загроза застосування БПЛА / КАБів / обстрілу") and "media report explosions". **88% of threat messages come while an alert is already active in the same oblast** (39% red, 49% yellow-only), and 12% with no alert. **25% of alert messages name more than one oblast.** The volunteer parser keys by oblast and returns one region per message, so threats overwrite or restart alerts, one raion's all-clear closes the whole oblast, and multi-oblast messages lose regions.
    - **Volunteer parser, verified by full code read + replaying its exact matching logic on the 800 messages** (no repo code executed):
      - Region = **first substring match in a fixed dictionary order**, so one region per message.
      - Of 737 messages with oblast tags: 622 assigned correctly; **90 name several oblasts, and 107 oblast mentions are lost**; **25 are assigned to an oblast not in the message at all**.
      - Substring bugs: Lviv's keyword "Подільський" matches Кам'янець-Подільський (Khmelnytskyi), Могилів-Подільський (Vinnytsia) and Подільський район (Odesa), so these go to **Lviv**. Volyn's "Луцьк" matches **Прилуцький** район (Chernihiv), so it goes to **Volyn**. This is consistent with the Lviv/Volyn surpluses.
      - Parser code unchanged since 2024-06 (git history). The channel's switch to raion-named messages likely made the old keywords collide; this is an inference.
      - This information can't be repaired from the CSV afterwards, because the original message isn't kept.
    - **Official parser, verified by code read + replay on the channel's last 1,199 messages (2026-09-05 11:24 → 09-07 06:09 UTC):**
      - Locations come from **exact hashtags**, not keyword guesses. **All alert and all-clear messages were parsed.** Skipped: 67 🟠 "KAB direction" info posts (not alerts) and 3 announcements.
      - Replay gives 736 alert starts vs 631 CSV rows in the window. Not fully reconciled; likely restarts within 3 h are merged, and alerts still open when the channel stopped are never written.
      - Known caveats: 38% exact duplicate rows. A missing all-clear followed by a new start more than 3 h later is closed at start + 1 h **with no flag**; otherwise it gives very long alerts (623 rows over 24 h). The "🔴🔴 Загроза ударних БпЛА" posts count as hromada-level starts. The renamed-hromada fix (2026-01-25) may not apply to older rows. The last hours before Sep 7 are incomplete.
    - **@air_alert_ua's last post was 2026-09-07 06:09 UTC** (checked via t.me/s/air_alert_ua: channel exists, 234K subscribers, last post is an ordinary alert with no announcement). So the official file stopped because **the channel stopped**, not the scraper. Parsing it ourselves can't provide recent data. A web-search summary said the channel "continued working"; the direct check contradicts it.
  - alerts.in.ua API: token required (request form), history only `month_ago`, 2 req/min on the history endpoint.
- Options: (A) volunteer only · (B) official only (stale) · (C) official + API to fill the gap · (D) volunteer as primary, official as cross-check.
- Suggested: **(D)**.

#### D1 cross-check plan (official vs volunteer), locked before running
Overlap period: 2022-03-15 → 2026-09-07, 24 in-scope regions (L15).
Official raion/hromada alerts are rolled up to oblast in **two ways**, and both are compared:
**(i) any sub-region alert = oblast alert** (union of intervals) and **(ii) oblast-level alerts only**.
Match rule: same region, start times within **±15 min** (also checked at ±5 and ±30 min).

| # | Question | Measured as | Why it matters |
|---|----------|-------------|----------------|
| Q1 | Does the volunteer file contain the same alerts? | % of official alerts matched in volunteer, and the reverse; per region and per quarter | Missing or extra alerts would mean wrong labels |
| Q2 | Do start times agree? | For matched pairs: median and p90 of the start difference | The target is start-based (likely D2a) |
| Q3 | Do durations agree, and how wrong are the imputed 30-min ends? | Duration difference for matched pairs, split by `naive` | How to treat `naive` rows |
| Q4 | Do the two files give the same **hourly labels**? | Region × hour "alert starts in this hour": agreement % and Cohen's kappa; also % time under alert per region | This is the level the model actually sees |
| Q5 | What does a volunteer "oblast alert" mean **after the switch to raion-level alerts (late 2025)**? | Q1/Q4 before vs after, under roll-ups (i) and (ii) | Decides what "alert in oblast" means for the target |
| Q6 | Are the anomalies real? | Volyn vs Rivne time under alert; Kherson's 16.5% `naive`; Kyiv City vs Kyiv oblast | Data artefact or real pattern |

**Decision rules (fixed before running, so the results can't move them):**
- Q1 match ≥ 90% both ways and Q2 median ≤ 5 min, in the latest 4 quarters → **lock (D)**.
- Agreement fails only in some regions or periods → keep (D), document it, and flag or exclude those slices.
- Agreement fails broadly → reconsider (C) official + API.

Output: `scripts/crosscheck_d1.py` + `reports/d1_crosscheck.md` in the repo, so the evidence is part of the submission.

**Result (2026-10-12): the rule for "fails broadly" was triggered → (D) is NOT locked; reconsider D1.**
Latest 4Q match: 56% / 32% (union roll-up), 71% / 3% (oblast-only), against a 90% threshold. Start times agree well when alerts do match (median 0.3 min).
Agreement has been falling since 2024, well before the raion switch. Western oblasts (Volyn, Lviv) have about 10× more volunteer alerts than official ones.
**Bug hunt (same day):** timezones (both UTC, no ±1–3 h offset peak), region names (identical) and volunteer duplicates (none) are fine. 38% of official rows are exact duplicates; removing them leaves the report unchanged. One display bug in my debug script, fixed.
Volyn monthly counts are **identical in both files until 2025-07** and split suddenly in **Aug–Sep 2025** (volunteer jumps from 27–30 to 86/month, official stays at about 13). **Which file is right is NOT established**; it needs a third source.
Dnipro 99.8% is not a code bug: official Synelnykivskyi raion has 1,197 alerts with a median of 3.8 h, up to 115 h (623 official rows over 24 h nationally since 2025-10). Whether those are real or missed "all clear" messages is unknown.
Official file outage is a known open issue in the repo (opened 2026-09-21 and 2026-09-25).

### D2. Forecast target (the core question)
- **(a)** P(alert starts in region *r* within the next *h* hours): binary or probabilistic, and the most useful operationally.
- **(b)** Number of alerts per day/hour (count regression).
- **(c)** Total alert duration per region per day.
- **(d)** Duration of an alert that is already active (survival-style).
- Suggested: **(a)**, with (b) as an aggregate side analysis.

### D3. Spatial granularity
- National / **oblast (~25 + Kyiv city)** / raion / hromada.
- Suggested: **oblast**. It gives enough signal per series and makes neighbour-region features simple.

### D4. Time resolution and forecast horizon
- Bin size: 15 min / **1 h** / 1 day. Horizon: next 1 h / 6 h / **24 h**.
- Suggested: hourly bins with a next-24h horizon, issued once a day. Open: a fixed daily issue time, or a rolling hourly issue time?

### D5. Evaluation protocol
- Holdout: the last N weeks (e.g. 4–8) as the test set.
- Suggested: **walk-forward (rolling-origin) backtest** on an expanding window for validation, then one final evaluation on the latest period.
- Metrics if the target is (a): **Brier score, log-loss, PR-AUC, calibration plot**. If (b): MAE / MASE.

### D6. Baselines (they must be beaten, and they must be in the repo)
- Climatology (historical rate per region × hour-of-week), persistence (last-period state), seasonal naive.
- Suggested: all three. They are cheap and they make our results credible.

### D7. Models
- Statistical: logistic regression, Poisson GLM, SARIMA/ETS for aggregates.
- ML: **gradient boosting (LightGBM)** on lag and calendar features.
- Deep learning (LSTM, TFT, etc.): probably overkill for a mini-project and harder to defend.
- Suggested: baselines → logistic regression → LightGBM. Stop there unless the results justify going further.

### D8. Features
- Lags and rolling counts per region, time since the last alert, hour/day-of-week, **alerts in neighbouring regions** (spatial spillover), national activity level.
- Weather is a real driver for drones, but only **forecast weather available at *t*** would be leak-free. Observed weather would leak.
- Open: include weather at all?

### D9. Text/media data (optional)
- Ideas: public Telegram monitoring channels, official statements, news.
- Trade-offs: possibly strong signal, but scraping effort, ToS/ethics, timestamp reliability and Ukrainian-language NLP.
- Suggested: **leave it out of v1.** Add it only as a v2 experiment if time allows.
- Most promising v2 signal: **launch reports from occupied territory / across the border** (e.g. "drones launched from Crimea"). They come *before* the alerts in target regions.

### D10. Regime changes and training window
- Attack patterns changed over time (missiles → mass drones, seasonal campaigns, possible ceasefire periods).
- Options: full history / last N months / full history with recency weighting.
- Suggested: try different window lengths in the backtest and pick one based on the results.

### D11. Data-quality quirks
- Occupied or front-line regions with near-permanent alerts (e.g. Luhansk, Crimea): exclude them or model them separately?
- Kyiv city vs Kyiv oblast, overlapping or duplicate alerts, missing gaps, **timezone and DST** (store UTC, derive Kyiv-local features).

### D12. Repo structure and tooling
- Script pipeline (`src/` package + CLI) vs notebooks. Suggested: **a `src/` package with notebooks only for EDA/plots**.
- Environment: `uv` / `pip + requirements.txt` / conda.
- Tests: at least **leakage tests** (assert that no feature uses data after *t*).
- README with results table, plots and instructions to reproduce.

### D13. Git and AI-log logistics
- Repo name, and when to `git init` and push.
- Commit attribution: include `Co-Authored-By: Claude` lines or not? Since AI use is expected and graded, including them is consistent with that.
- How to export the log: Claude Code `/export` at the end. Keep everything in one session if possible, or export each session.

---

## Next step
Go through D1 → D2 → D3/D4 first. Most of the other decisions depend on them.
