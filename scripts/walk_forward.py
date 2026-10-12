"""Walk-forward backtest for target (a) on pre-test data (L24/L25). Test period is NOT touched.

Writes reports/walk_forward.md with per-fold Brier for model vs best recency baseline vs climatology.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss

from d2_target_comparison import DATA_FROM, HORIZONS, SEED, TEST_FROM, hourly_panel, load, md_table

REPORT = Path(__file__).resolve().parents[1] / "reports" / "walk_forward.md"
MIN_TRAIN = pd.Timedelta(weeks=12)
BLOCK = pd.Timedelta(weeks=2)
FEATS = ["region_code", "hod", "dow", "active_at_T", "nat_prev_1h", "nat_prev_3h",
         "starts_prev_1h", "starts_prev_3h", "starts_prev_6h", "starts_prev_24h", "starts_prev_168h"]
RECENCY_KEYS = {
    "k=1h": lambda d: [d.region, d.starts_prev_1h > 0],
    "k=3h": lambda d: [d.region, d.starts_prev_3h > 0],
    "k=6h": lambda d: [d.region, d.starts_prev_6h > 0],
    "3h+active": lambda d: [d.region, d.starts_prev_3h > 0, d.active_at_T > 0],
}


def lookup(tr, va, key, y):
    tab = tr.groupby(key(tr))[y].mean()
    return pd.Series(list(zip(*key(va)))).map(tab).fillna(tr[y].mean()).values


def folds():
    starts = []
    s = TEST_FROM - BLOCK
    while s - DATA_FROM >= MIN_TRAIN:
        starts.append(s)
        s -= BLOCK
    return sorted(starts)


def main():
    df = load()
    p = hourly_panel(df, sorted(df.region.unique()))
    out = ["# Walk-forward backtest, target (a), pre-test data only\n",
           f"Folds: {len(folds())} × 2 weeks, expanding window, min train 12 weeks. Test period (from {TEST_FROM}) untouched. "
           "Recency reference = best of 4 variants chosen on each fold's validation data (favours the baseline).\n"]
    summary = []
    for h in HORIZONS:
        y = f"y_{h}h"
        rows = []
        for fs in folds():
            fe = fs + BLOCK
            tr = p[p.hour < fs - pd.Timedelta(hours=h)]
            va = p[(p.hour >= fs) & (p.hour < fe - pd.Timedelta(hours=h))]
            clim = tr.groupby(["region", "hod", "dow"])[y].mean()
            p_clim = va.set_index(["region", "hod", "dow"]).index.map(clim).fillna(tr[y].mean()).values
            rec = {k: brier_score_loss(va[y], lookup(tr, va, key, y)) for k, key in RECENCY_KEYS.items()}
            best_k = min(rec, key=rec.get)
            m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=SEED,
                                               categorical_features=[0]).fit(tr[FEATS], tr[y])
            b_m = brier_score_loss(va[y], m.predict_proba(va[FEATS])[:, 1])
            b_c = brier_score_loss(va[y], p_clim)
            rows.append({"fold start": str(fs.date()), "train weeks": round((fs - DATA_FROM) / pd.Timedelta(weeks=1)),
                         "base rate": va[y].mean(), "Brier model": b_m, "Brier best recency": rec[best_k],
                         "best recency": best_k, "Brier clim": b_c,
                         "skill vs recency": 1 - b_m / rec[best_k], "skill vs clim": 1 - b_m / b_c,
                         "model wins": "yes" if b_m < rec[best_k] else "NO"})
        r = pd.DataFrame(rows).set_index("fold start")
        wins = (r["model wins"] == "yes").sum()
        pval = binomtest(wins, len(r), 0.5, alternative="greater").pvalue
        summary.append({"horizon": f"{h}h", "folds": len(r), "model wins": wins, "sign-test p": pval,
                        "mean skill vs recency": r["skill vs recency"].mean(),
                        "min": r["skill vs recency"].min(), "max": r["skill vs recency"].max(),
                        "mean skill vs clim": r["skill vs clim"].mean()})
        out.append(f"## Horizon {h}h\n\n" + md_table(r) + "\n")
    s3 = next(s for s in summary if s["horizon"] == "3h")
    plain = [
        "## In short\n",
        "- **What this does:** trains the model on everything before a two-week period, then checks its forecasts "
        "for that period. Repeated for each of the "
        f"{s3['folds']} two-week periods before the test period (the test period itself is not used).",
        "- **Compared to:** a simple rule that only looks at what's happening right now: \"how often did an alert start "
        "soon after, when this oblast had an alert in the last few hours / has one active now\" (recency baseline).",
        f"- **Result (3-hour forecasts):** the model was better in **{s3['model wins']} of {s3['folds']}** periods, "
        f"on average by **{s3['mean skill vs recency']:.1%}** (from {s3['min']:.1%} to {s3['max']:.1%}).",
        "- **How \"better\" is measured:** Brier score = how far the predicted probabilities are from what actually "
        "happened (lower is better). \"Skill\" = how much lower the model's Brier score is than the baseline's.",
        "- **Caveat:** for each period the baseline's best version is picked with hindsight, which favours the baseline. "
        "The model is not tuned yet.\n",
    ]
    out[1:1] = plain
    out.insert(len(plain) + 2, "## Summary table\n\n" + md_table(pd.DataFrame(summary).set_index("horizon")) + "\n")
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
