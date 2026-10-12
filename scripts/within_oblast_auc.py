"""Within-oblast AUC over all 10 validation periods (20 weeks), 3-hour horizon, final model setup.

Checks whether the weak within-oblast ranking seen in the dry run (2 weeks) is typical. Validation only:
the test period is not used. Writes reports/within_oblast_auc.md.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from d2_target_comparison import md_table
from drop_active_check import FEATS_FINAL, START_ONLY_RECENCY, gbm, panel
from final_evaluation import make_split
from walk_forward import BLOCK, folds, lookup

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "within_oblast_auc.md"
H, Y = 3, "y_3h"


def main():
    k = json.loads((ROOT / "reports" / "recency_choice.json").read_text(encoding="utf-8"))["3h"]
    p = panel()
    preds = []
    for fs in folds():
        tr, ev = make_split(p, fs, fs + BLOCK, H)
        clim = tr.groupby(["region", "hod", "dow"])[Y].mean()
        preds.append(pd.DataFrame({
            "region": ev.region.values, "y": ev[Y].values,
            "model": gbm().fit(tr[FEATS_FINAL], tr[Y]).predict_proba(ev[FEATS_FINAL])[:, 1],
            "recency": lookup(tr, ev, START_ONLY_RECENCY[k], Y),
            "clim": ev.set_index(["region", "hod", "dow"]).index.map(clim).fillna(tr[Y].mean()).values}))
    d = pd.concat(preds, ignore_index=True)
    rows = []
    for reg, g in d.groupby("region"):
        two = g.y.nunique() == 2
        rows.append({"region": reg, "base rate": g.y.mean(), "quiet hours": int((g.y == 0).sum()),
                     **{f"AUC {m}": roc_auc_score(g.y, g[m]) if two else np.nan for m in ("model", "recency", "clim")}})
    t = pd.DataFrame(rows).set_index("region").sort_values("base rate")
    mean = t[["AUC model", "AUC recency", "AUC clim"]].mean()
    out = ["# Within-oblast AUC over 20 weeks of validation (3 h)\n", "## In short\n",
           "- **What this does:** for each oblast separately, measures how well each method ranks hours with an alert start "
           "above hours without one (AUC; 0.5 = coin flip, 1 = perfect), over all 10 validation periods "
           f"({len(d) // 24} hours per oblast). The test period is not used.",
           f"- **Average over {t['AUC model'].notna().sum()} oblasts:** model **{mean['AUC model']:.3f}**, "
           f"recency rule {mean['AUC recency']:.3f}, climatology {mean['AUC clim']:.3f}.",
           f"- **Pooled over all oblasts**, for comparison: model {roc_auc_score(d.y, d.model):.3f}.\n",
           "## Per oblast (sorted by base rate)\n", md_table(t, "{:.3f}"), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
