"""L37/L38: drop the features that use alert end times, and pick a start-only recency opponent.

Validation periods only (same 10 two-week periods, 7-day warm-up as in d7_d8_models.py); the test period is not used.
- GBM + neighbours WITH the active features (as chosen in L28) vs WITHOUT them (L37: adopted regardless).
- Start-only recency variants (k = 1/3/6 h) per horizon; the one with the lowest mean Brier is the opponent (L38).
Writes reports/drop_active_check.md and reports/recency_choice.json (read by final_evaluation.py).
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss

from d2_target_comparison import DATA_FROM, HORIZONS, SEED, hourly_panel, load, md_table
from d7_d8_models import NB, add_neighbours
from walk_forward import BLOCK, FEATS, folds, lookup

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "drop_active_check.md"
CHOICE = ROOT / "reports" / "recency_choice.json"

FEATS_WITH = FEATS + NB
FEATS_FINAL = [f for f in FEATS if f != "active_at_T"] + [f for f in NB if f != "nb_active"]  # start times only
START_ONLY_RECENCY = {k: (lambda d, k=k: [d.region, d[f"starts_prev_{k}h"] > 0]) for k in (1, 3, 6)}


def panel():
    df = load()
    p = add_neighbours(hourly_panel(df, sorted(df.region.unique())))
    return p[p.hour >= DATA_FROM + pd.Timedelta(days=7)]  # warm-up, as in d7_d8_models.py


def gbm():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=SEED, categorical_features=[0])


def main():
    p = panel()
    assert FEATS_FINAL[0] == "region_code"  # categorical_features=[0] relies on this
    out = ["# L37/L38: dropping the features that use alert end times\n"]
    choice, summary, fold_tables = {}, [], []
    for h in HORIZONS:
        y = f"y_{h}h"
        rows = []
        for fs in folds():
            tr = p[p.hour < fs - pd.Timedelta(hours=h)]
            va = p[(p.hour >= fs) & (p.hour < fs + BLOCK - pd.Timedelta(hours=h))]
            row = {"period start": str(fs.date())}
            for k, key in START_ONLY_RECENCY.items():
                row[f"recency k={k}h"] = brier_score_loss(va[y], lookup(tr, va, key, y))
            for name, feats in [("with active", FEATS_WITH), ("without active", FEATS_FINAL)]:
                row[name] = brier_score_loss(va[y], gbm().fit(tr[feats], tr[y]).predict_proba(va[feats])[:, 1])
            rows.append(row)
        r = pd.DataFrame(rows).set_index("period start")
        rec_cols = [f"recency k={k}h" for k in START_ONLY_RECENCY]
        best = r[rec_cols].mean().idxmin()
        choice[f"{h}h"] = int(best.split("=")[1].rstrip("h"))
        r["skill vs recency"] = 1 - r["without active"] / r[best]
        wins = int((r["without active"] < r[best]).sum())
        summary.append({"horizon": f"{h}h", "recency opponent": best,
                        "cost of dropping (mean Brier change)": r["without active"].mean() / r["with active"].mean() - 1,
                        "periods won vs recency": f"{wins}/{len(r)}",
                        "mean skill vs recency": r["skill vs recency"].mean()})
        fold_tables.append(f"## {h}h, per period (Brier, lower is better)\n\n" + md_table(r, "{:.4f}") + "\n")
    s = pd.DataFrame(summary).set_index("horizon")
    s3 = s.loc["3h"]
    wins3 = int(s3["periods won vs recency"].split("/")[0])
    out += ["## In short\n",
            "- **What this does:** removes the two features that depend on alert end times (alerts active in the oblast now, "
            "neighbours with an alert active now). The official data sets some end times using later alerts, so these "
            "features leak. Same 10 two-week validation periods as before; the test period is not used.",
            f"- **What we gave up (3 h):** the mean Brier score changed by **{s3['cost of dropping (mean Brier change)']:+.1%}** "
            "(positive = worse). Adopted regardless (L37).",
            f"- **New opponent (3 h):** the best recency rule that uses only alert starts is **{s3['recency opponent']}** (L38).",
            f"- **Still better than that rule?** In **{wins3} of 10** periods, by {s3['mean skill vs recency']:.1%} on average "
            f"(rule L25: at least 9) → **{'PASS' if wins3 >= 9 else 'FAIL'}**.\n",
            "## Summary\n", md_table(s, "{:.4f}"), "", *fold_tables]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    CHOICE.write_text(json.dumps(choice, indent=1), encoding="utf-8")
    print(f"report written to {REPORT}; recency choice {choice}")


if __name__ == "__main__":
    main()
