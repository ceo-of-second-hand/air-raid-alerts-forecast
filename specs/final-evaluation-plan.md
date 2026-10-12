# Plan: shared module, leakage tests, final evaluation

> **What:** the remaining work before submission: shared code module, the three L35 leakage tests, and the final evaluation that scores the test period once.
> **Approved:** 2026-10-12 by Ivanka (third version, cut down after an independent review).
> **Based on:** L7 (no leakage), L13/L14 (score the test once, log every look), L15 (regions), L23/L24/L25 (metric, folds, pass rule), L28 (model), L30/L31 (test period, opponents), L35/L36 (repo, git), L37/L38 (this plan's two decisions). Review findings adopted: H1–H4, M1, M4, M5.

## Bottom line

- Order: **pin data → refactor → prove it changed nothing → drop the "active" features → 3 leakage tests → dry run → checklist → ONE real test run → write up.**
- The H1 leak is fixed by **dropping every feature that uses alert end times**, not by rebuilding them.
- The final model scores the test period **once**. The lock and log are written before any metric is computed.
- Rough effort: **about 3.5 h** (down from 6–7 h).

| Step | What                                | Touches test? | Effort  |
|------|-------------------------------------|---------------|---------|
| 0    | Pin data + fingerprint outputs      | no            | 20 min  |
| 1    | Move shared code to one module      | no            | 45 min  |
| 2    | Prove the refactor changed nothing  | no            | 15 min  |
| 2b   | Drop "active" features, re-validate | no            | 20 min  |
| 3    | 3 leakage tests (L35)               | no            | 45 min  |
| 4    | Final script + dry run              | no            | 1 h     |
| 5    | Pre-flight checklist + commit       | no            | 10 min  |
| 6    | **The one real test run**           | **YES, once** | 5 min   |
| 7    | Write up, log, commit               | reads saved predictions | 30 min |

## Step 0: Pin the data and fingerprint outputs

- Find the upstream commit our local `data/raw` files match. `download_data.py` downloads from that commit's URL and checks each file's SHA-256 (H2).
- Save hashes of the feature table, `reports/walk_forward.md`, `reports/d7_d8_models.md`.

## Step 1: Move shared code into one module

- New `scripts/core.py` with the shared code. `walk_forward.py` and `d7_d8_models.py` import from it.
- `crosscheck_d1.py` keeps its own loader (M4).
- `d2_target_comparison.py` is frozen behind `--i-know-this-scores-the-test-period`.

## Step 2: Prove the refactor changed nothing

- Re-run the two validation scripts. Their reports and the feature-table hash must be **identical** to step 0.

## Step 2b: Drop the features that use end times (H1)

- **Dropped:** `active_at_T` (alerts active in the oblast now) and `nb_active` (neighbours with an alert active now). They are the only features that use end times; every other feature uses start times only.
- **The recency opponent must be leak-free too.** "3h + active" uses end times, so the opponent becomes the best **start-only** variant (k = 1 h / 3 h / 6 h). Which one is picked by lowest mean Brier over the validation periods, before the test.
- **One validation run** (10 periods, 3 h): GBM + neighbours with vs without the active features, plus the start-only recency variants.
- **Rule fixed before running:** the version without active features is adopted **whatever it scores**. The difference is reported as "what we gave up to remove the leak".
- It must still pass L25: beats the (new) recency opponent in ≥ 9 of 10 periods. If not, we stop and decide together; nothing goes back in.
- **Still in the data, not fixable:** if an all-clear is missing and a new alert follows within 3 h, the parser overwrote the first alert's start. That start is gone from the CSV, so this goes into the README limitations.

## Step 3: The three leakage tests (L35)

1. **Future data can't change features:** change or delete alerts after a time T0; every feature at hours ≤ T0 stays identical.
2. **Purging:** for every validation period and the final split, the last training hour + h ≤ the first evaluated hour.
3. **Excluded regions never appear:** no Luhansk / Crimea / Sevastopol after loading.

## Step 4: Final script + dry run

- **Training:** Dec 8 → TEST_FROM − h (purged), per horizon. GBM + neighbours **without active features**, same settings as validation.
- **Opponents:** the start-only recency variant chosen in 2b (main), and climatology.
- **Order inside the real run (H4):**
  1. write `reports/.test_scored` + the `experiments.md` entry;
  2. save `reports/final_predictions.csv`;
  3. compute every metric from that file (per-oblast AUC = NaN when an oblast has only one class).
- **Re-run guard:** if the lock exists, the script refuses unless given `--rerun-reason "..."`. The lock file is committed.
- **Dry run (H3):**
  - the "test" is Jul 12 → Jul 26 − h; training stops at Jul 12 − h;
  - assert `max(evaluated hour) + h ≤ real TEST_FROM`;
  - no lock and no log entry;
  - its 3 h Brier must **exactly** equal the step-2b value for that period.

## Step 5: Pre-flight checklist

- [ ] Data pinned; hashes match.
- [ ] Step 2 identical; step 2b done and logged.
- [ ] 3 tests pass.
- [ ] Dry run matches exactly.
- [ ] **Bug defined (M5):** a crash, a failing test or assert, or predictions not matching the documented setup. "Lower than expected" is not a bug.
- [ ] Working tree committed.

## Step 6: The one real run

- `python scripts/final_evaluation.py --score-test`. Reported as is.

## Step 7: Write up

- README results from saved predictions, next to the earlier d2 test number.
- README wording (M1): "final model scored once; the test period was seen 3× during target selection".
- README limitations: dropped active features (+ what it cost), the overwritten-starts issue, the 623 long alerts.
- Commit, then **ask before pushing**.

## Backlog (later, if time allows)

- **Steps 1–2 (shared `core.py` module + proving it changed nothing):** moved here by Ivanka on 2026-10-12. The refactor doesn't change any result; the final script imports from the existing scripts instead.
- **Reorganise `reports/`** (it mixes reports, data files, images and the lock file), added 2026-10-12.
- **Clean up code comments**, added 2026-10-12.

- Stronger leakage tests:
  - changes at or after T0 (not only after), including neighbour oblasts;
  - training X/y byte-identical when test rows change;
  - exact 24-name region list;
  - an alert with no end counts as active;
  - Kyiv-time calendar across the DST change;
  - warm-up applied.
- Second recency opponent: best variant picked on the test, as a stricter comparison.
- Bring back a leak-free "active" feature (alerts of exactly 60 min stay active until the next start in that oblast).
- LOW items: categorical feature by name, target/merge assert, document GBM early stopping and the walk_forward warm-up difference.

## Decisions taken with this plan

- **L37:** H1 fix = drop both active features, adopted regardless of score.
- **L38:** Recency opponent = best start-only variant, chosen on validation.
