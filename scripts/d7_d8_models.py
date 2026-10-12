"""D7 + D8: logistic regression vs GBM, with and without neighbour features (rules L26/L27).

Same 10 walk-forward folds as walk_forward.py, 3-hour horizon, test period untouched.
Writes reports/d7_d8_models.md.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from d2_target_comparison import DATA_FROM, SEED, hourly_panel, load, md_table
from walk_forward import BLOCK, FEATS, RECENCY_KEYS, folds, lookup

ROOT = Path(__file__).resolve().parents[1]
ADJ = ROOT / "data" / "oblast_adjacency.json"
REPORT = ROOT / "reports" / "d7_d8_models.md"
H = 3
Y = f"y_{H}h"
COUNTS = [f for f in FEATS if f.startswith(("starts_prev", "nat_prev")) or f == "active_at_T"]
NB = ["nb_starts_prev_1h", "nb_starts_prev_3h", "nb_active"]


def add_neighbours(p):
    """Sum of neighbours' recent starts and number of neighbours with an alert active at T (all known at T)."""
    adj = json.loads(ADJ.read_text(encoding="utf-8"))
    regions = sorted(p.region.unique())
    a = pd.DataFrame(0, index=pd.Index(regions, name="region"), columns=regions)  # a[r, k] = 1 if k borders r
    for r, ns in adj.items():
        a.loc[r, ns] = 1
    for src, dst in [("starts_prev_1h", "nb_starts_prev_1h"), ("starts_prev_3h", "nb_starts_prev_3h")]:
        wide = p.pivot(index="hour", columns="region", values=src)[regions]
        p = p.merge((wide @ a.T).stack().rename(dst).reset_index(), on=["hour", "region"])
    wide = (p.pivot(index="hour", columns="region", values="active_at_T")[regions] > 0).astype(int)
    return p.merge((wide @ a.T).stack().rename("nb_active").reset_index(), on=["hour", "region"])


def gbm(feats):
    return feats, HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=SEED,
                                                 categorical_features=[0])


def lr(feats):
    counts = [f for f in feats if f in COUNTS + NB]
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["region", "hod", "dow"]),
        ("num", make_pipeline(FunctionTransformer(np.log1p), StandardScaler()), counts),
    ])
    return ["region", "hod", "dow"] + counts, make_pipeline(pre, LogisticRegression(max_iter=2000))


VARIANTS = {"LR base": (lr, FEATS), "LR + neighbours": (lr, FEATS + NB),
            "GBM base": (gbm, FEATS), "GBM + neighbours": (gbm, FEATS + NB)}


def main():
    df = load()
    p = add_neighbours(hourly_panel(df, sorted(df.region.unique())))
    p = p[p.hour >= DATA_FROM + pd.Timedelta(days=7)]  # warm-up: every look-back window (max 7 days) is complete
    assert not p[FEATS + NB].isna().any().any()
    rows = []
    for fs in folds():
        tr = p[p.hour < fs - pd.Timedelta(hours=H)]
        va = p[(p.hour >= fs) & (p.hour < fs + BLOCK - pd.Timedelta(hours=H))]
        row = {"fold start": str(fs.date()),
               "recency": min(brier_score_loss(va[Y], lookup(tr, va, key, Y)) for key in RECENCY_KEYS.values())}
        for name, (make, feats) in VARIANTS.items():
            cols, model = make(feats)
            row[name] = brier_score_loss(va[Y], model.fit(tr[cols], tr[Y]).predict_proba(va[cols])[:, 1])
        rows.append(row)
    r = pd.DataFrame(rows).set_index("fold start")

    # L26: neighbours kept per model if better in >= 8/10 folds and on mean
    keep, verdict = {}, []
    for m in ["LR", "GBM"]:
        wins = int((r[f"{m} + neighbours"] < r[f"{m} base"]).sum())
        better_mean = r[f"{m} + neighbours"].mean() < r[f"{m} base"].mean()
        keep[m] = wins >= 8 and better_mean
        verdict.append(f"- **{m}: neighbour features {'KEPT' if keep[m] else 'NOT kept'}.** They improved the Brier score "
                       f"in {wins} of {len(r)} periods (rule: at least 8), mean change "
                       f"{1 - r[f'{m} + neighbours'].mean() / r[f'{m} base'].mean():+.1%}.")
    final = {m: f"{m} + neighbours" if keep[m] else f"{m} base" for m in ["LR", "GBM"]}
    skill = {m: (1 - r[v] / r["recency"]) for m, v in final.items()}
    # L27: prefer LR unless GBM is > 1 percentage point better on mean skill vs recency
    gap = skill["GBM"].mean() - skill["LR"].mean()
    chosen = "GBM" if gap > 0.01 else "LR"
    wins_rec = int((skill[chosen] > 0).sum())
    verdict.append(f"- **Model: {final[chosen]}.** Mean improvement over the recency rule: LR {skill['LR'].mean():.1%}, "
                   f"GBM {skill['GBM'].mean():.1%} (gap {gap * 100:+.1f} points; rule: GBM only if more than +1 point).")
    verdict.append(f"- **Still beats the recency rule?** In {wins_rec} of {len(r)} periods (rule L25: at least 9) → "
                   f"{'PASS' if wins_rec >= 9 else 'FAIL'}.")

    table = r.copy()
    for m, v in final.items():
        table[f"{m} skill vs recency"] = skill[m]
    out = ["# D7 + D8: logistic regression vs GBM, with and without neighbour features\n",
           "## In short\n",
           "- **What this does:** compares a simple model (logistic regression, LR) with the more complex one (GBM), "
           "each with and without information about alerts in neighbouring oblasts. 3-hour forecasts, the same "
           f"{len(r)} two-week periods as before; the test period is not used.",
           "- **How it's judged:** Brier score (how far the predicted probabilities are from what happened; lower is better), "
           "with the rules fixed in `DECISIONS.md` (L26, L27) before running.",
           *verdict, "",
           "## Brier score per two-week period (lower is better)\n", md_table(table, "{:.4f}"), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
