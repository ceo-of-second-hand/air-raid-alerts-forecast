# Experiments log

Every look at the **test period** (last 6 weeks: 2026-07-26 21:00 → 2026-09-06 21:00 UTC) is logged here (L14),
together with what changed afterwards. Validation-fold results (walk-forward) are logged too, but they don't touch the test.

| # | Date | Data used | What ran | Result | What changed afterwards |
|---|------|-----------|----------|--------|-------------------------|
| 1 | 2026-10-12 | **TEST** | `d2_target_comparison.py`: comparing targets (a)/(b)/(d), GBM vs climatology and hard persistence | (a) 3 h: Brier skill +20% vs climatology | Chose target (a) with a 3 h horizon (L21). ⚠️ The target choice was made using test data, so the test is no longer fully "unseen" for this decision. |
| 2 | 2026-10-12 | **TEST** | Same script + recency baselines (Ivanka's challenge) | 3 h: +9% vs best recency | Main metric = skill vs recency (L23). No model changes. |
| 3 | 2026-10-12 | validation folds | `walk_forward.py`, 10 folds | Model beats recency in 10/10 folds at 1/3/6 h; 3 h mean +3.7% (range +0.7% … +9.3%) | Pass rule L25 met. |
| 4 | 2026-10-12 | **TEST** (re-run, no new information) | `d2_target_comparison.py` re-run twice to add the plain-language summary to the report | Tables identical to #2 (checked with diff) | Nothing; report text only. |
| 5 | 2026-10-12 | validation folds | `d7_d8_models.py`: LR vs GBM, ± neighbour features, 3 h (first 7 days dropped as warm-up) | Neighbours help both (9/10 periods). GBM + neighbours: +5.0% vs recency, 10/10 periods. LR + neighbours: +1.5%, 7/10. | Locked L28: GBM + neighbours. |
| 6 | 2026-10-12 | validation folds | `drop_active_check.py`: GBM + neighbours with vs without the end-time features (L37); start-only recency variants (L38) | Dropping costs +4.6% Brier at 3 h (+6.3% at 1 h, +2.1% at 6 h). New opponent at 3 h: recency k=6h. Without active features the model still wins 10/10 (1 h, 3 h) and 9/10 (6 h) periods; 3 h mean +3.0%. "With active" column reproduces d7_d8 exactly. | Adopted L37/L38; final model has no end-time features. |
| 7 | 2026-10-12 | validation (dry run) | `final_evaluation.py --dry-run`: final code path on the last validation period (Jul 12 → Jul 26) | 3 h Brier 0.1133 = exactly the `drop_active_check` value for that period. Pooled AUC 0.92, but within one oblast only ~0.55 (model) vs ~0.52 (recency). | Report now shows per-oblast AUC next to the pooled one; pooled AUC is not a headline number. |
| 8 | 2026-10-12 | **TEST** | `final_evaluation.py --score-test` (final run), commit 5ae8df2 | see `reports/final_evaluation.md` | Written before any metric was computed. |
| 8 (result) | 2026-10-12 | **TEST** | result of run #8 | 3 h: Brier skill +10.4% vs recency (k=6h), +19.2% vs climatology, better in 6/6 weeks. 1 h +5.8%, 6 h +6.1% vs recency. Pooled AUC 0.907; within-oblast AUC 0.699 (recency 0.630). | None to the model. README reports it next to the validation average (+3.0%). |
| 9 | 2026-10-12 | validation folds | `within_oblast_auc.py`: per-oblast AUC, 10 periods (20 weeks), 3 h, final setup | Within-oblast AUC: model 0.659, recency 0.554, climatology 0.537 (pooled 0.882). The dry run's 0.55 was a weak period. | README AUC paragraph updated. No model change. |
