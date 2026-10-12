"""Final evaluation: train the chosen model on everything before the test period and score the test period ONCE.

Model: GBM + neighbour features, start-time features only (L28, L37). Opponents: start-only recency rule chosen
on validation (L38, reports/recency_choice.json) and climatology (L31). Horizons 1/3/6 h (L29).

Usage:
    python scripts/final_evaluation.py --dry-run      # stand-in "test" = last validation period; never touches the test
    python scripts/final_evaluation.py --score-test   # THE one real run (needs a clean git tree)
    python scripts/final_evaluation.py --score-test --rerun-reason "..."   # only after a pre-defined bug (see specs/)

Order in the real run: lock file + experiments.md entry -> save predictions -> compute every metric from that file.
"""
import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from d2_target_comparison import CUTOFF, HORIZONS, TEST_FROM, md_table
from drop_active_check import FEATS_FINAL, START_ONLY_RECENCY, gbm, panel
from walk_forward import BLOCK, lookup

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOCK = REPORTS / ".test_scored"
EXPERIMENTS = ROOT / "experiments.md"
CHOICE = REPORTS / "recency_choice.json"
DRY_FROM = TEST_FROM - BLOCK  # last validation period: same window as the 2026-07-12 period in drop_active_check.md


def make_split(p, eval_from, eval_to, h):
    """Train on hours whose label window [T, T+h) ends before eval_from; evaluate on hours whose window ends by eval_to."""
    tr = p[p.hour < eval_from - pd.Timedelta(hours=h)]
    ev = p[(p.hour >= eval_from) & (p.hour < eval_to - pd.Timedelta(hours=h))]
    return tr, ev


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def predict(p, eval_from, eval_to, choice):
    out = []
    for h in HORIZONS:
        y = f"y_{h}h"
        tr, ev = make_split(p, eval_from, eval_to, h)
        assert tr.hour.max() + pd.Timedelta(hours=h) <= ev.hour.min()  # purged
        assert ev.hour.max() + pd.Timedelta(hours=h) <= eval_to
        clim = tr.groupby(["region", "hod", "dow"])[y].mean()
        d = ev[["hour", "region", y]].reset_index(drop=True).rename(columns={y: "y"})  # keeps the UTC timezone
        d.insert(0, "horizon_h", h)
        d["p_model"] = gbm().fit(tr[FEATS_FINAL], tr[y]).predict_proba(ev[FEATS_FINAL])[:, 1]
        d["p_recency"] = lookup(tr, ev, START_ONLY_RECENCY[choice[f"{h}h"]], y)
        d["p_clim"] = ev.set_index(["region", "hod", "dow"]).index.map(clim).fillna(tr[y].mean()).values
        out.append(d)
    return pd.concat(out, ignore_index=True)


def safe_auc(y, p):
    return roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan


def metrics(pred, choice):
    rows = []
    for h, d in pred.groupby("horizon_h"):
        b = {k: brier_score_loss(d.y, d[f"p_{k}"]) for k in ("model", "recency", "clim")}
        per_obl = d.groupby("region").apply(lambda g: safe_auc(g.y, g.p_model), include_groups=False)
        base = d.y.mean()
        rows.append({"horizon": f"{h}h", "recency rule": f"k={choice[f'{h}h']}h", "base rate": base,
                     "Brier model": b["model"], "Brier recency": b["recency"], "Brier clim": b["clim"],
                     "skill vs recency": 1 - b["model"] / b["recency"], "skill vs clim": 1 - b["model"] / b["clim"],
                     "AUC model": roc_auc_score(d.y, d.p_model), "AUC recency": roc_auc_score(d.y, d.p_recency),
                     "mean AUC per oblast": per_obl.mean(),
                     "mean AUC per oblast recency": d.groupby("region").apply(lambda g: safe_auc(g.y, g.p_recency), include_groups=False).mean(),
                     "oblasts without AUC": int(per_obl.isna().sum()),
                     "log-loss model": log_loss(d.y, d.p_model.clip(1e-6, 1 - 1e-6)),
                     "log-loss recency": log_loss(d.y, d.p_recency.clip(1e-6, 1 - 1e-6)),
                     "accuracy@0.5": ((d.p_model >= 0.5) == d.y).mean(), "majority-class acc": max(base, 1 - base)})
    return pd.DataFrame(rows).set_index("horizon")


def weekly(pred, start):
    d = pred[pred.horizon_h == 3].copy()
    d["week"] = ((d.hour - start) // pd.Timedelta(weeks=1)).astype(int) + 1
    w = d.groupby("week").apply(lambda g: pd.Series({
        "from": str(g.hour.min().date()), "Brier model": brier_score_loss(g.y, g.p_model),
        "Brier recency": brier_score_loss(g.y, g.p_recency)}), include_groups=False)
    w["skill vs recency"] = 1 - w["Brier model"] / w["Brier recency"]
    w["model better"] = np.where(w["Brier model"] < w["Brier recency"], "yes", "NO")
    return w


def per_oblast(pred):
    d = pred[pred.horizon_h == 3]
    r = d.groupby("region").apply(lambda g: pd.Series({
        "base rate": g.y.mean(), "Brier model": brier_score_loss(g.y, g.p_model),
        "Brier recency": brier_score_loss(g.y, g.p_recency), "AUC model": safe_auc(g.y, g.p_model),
        "AUC recency": safe_auc(g.y, g.p_recency)}),
        include_groups=False)
    r["skill vs recency"] = 1 - r["Brier model"] / r["Brier recency"]
    return r.sort_values("skill vs recency")


def calibration(pred, png, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = pred[pred.horizon_h == 3]
    bins = np.linspace(0, 1, 11)
    tab = {}
    for col in ("p_model", "p_recency"):
        g = d.groupby(pd.cut(d[col], bins, include_lowest=True), observed=True)
        tab[col] = pd.DataFrame({"mean predicted": g[col].mean(), "observed rate": g.y.mean(), "hours": g.size()})
    surface, ink, muted = "#fcfcfb", "#0b0b0b", "#52514e"
    fig, ax = plt.subplots(figsize=(6, 6), facecolor=surface)
    ax.set_facecolor(surface)
    ax.plot([0, 1], [0, 1], color=muted, lw=1, ls="--", label="perfect calibration")
    for col, color, name in [("p_model", "#2a78d6", "model"), ("p_recency", "#eb6834", "recency rule")]:
        t = tab[col]
        ax.plot(t["mean predicted"], t["observed rate"], color=color, lw=2, marker="o", ms=8,
                markeredgecolor=surface, markeredgewidth=2, label=name)
    ax.set_xlim(0, 1), ax.set_ylim(0, 1)
    ax.set_xlabel("predicted probability (bin average)", color=muted)
    ax.set_ylabel("share of hours where an alert started", color=muted)
    ax.set_title(f"Calibration, 3-hour forecasts, {title}", color=ink, loc="left", fontsize=10)
    ax.grid(color="#e6e5e0", lw=0.8)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=muted)
    ax.legend(frameon=False, labelcolor=ink, loc="upper left")
    fig.tight_layout()
    fig.savefig(png, dpi=150)
    plt.close(fig)
    return tab["p_model"]


def write_report(pred, choice, label, title, start, path, png):
    m, w, o = metrics(pred, choice), weekly(pred, start), per_oblast(pred)
    cal = calibration(pred, png, title)
    m3 = m.loc["3h"]
    wins = int((w["model better"] == "yes").sum())
    out = [f"# Final evaluation ({label})\n", "## In short\n",
           f"- **What this does:** trains the final model (GBM + neighbour features, start times only) on all data before "
           f"{start.date()} and forecasts every hour of {title} ({start:%Y-%m-%d %H:%M} → {pred.hour.max() + pd.Timedelta(hours=1):%Y-%m-%d %H:%M} UTC, 24 oblasts).",
           f"- **3-hour forecasts vs the \"recent alert starts\" rule (recency, k={choice['3h']}h):** the model's Brier score "
           f"(how far its probabilities are from what happened; lower is better) is **{m3['skill vs recency']:.1%} lower**. "
           f"Better in **{wins} of {len(w)}** weeks.",
           f"- **vs the oblast's usual rate for that hour and weekday (climatology):** {m3['skill vs clim']:.1%} lower.",
           f"- **Ranking (AUC: chance that an hour with an alert start gets a higher score than one without; 0.5 = random):** "
           f"model {m3['AUC model']:.3f} vs recency {m3['AUC recency']:.3f} over all oblasts together. **This mostly measures which "
           f"oblast is active.** Within a single oblast the average is model {m3['mean AUC per oblast']:.3f} vs recency "
           f"{m3['mean AUC per oblast recency']:.3f} ({int(m3['oblasts without AUC'])} oblasts had no alert starts or no quiet hours, so no AUC).",
           f"- **Calibration:** see `{png.name}` and the table below (when the model says x%, how often did an alert start).\n",
           "## All metrics\n", md_table(m.T.rename_axis("metric"), "{:.4f}"), "",
           "## 3 h, week by week\n", md_table(w, "{:.4f}"), "",
           "## 3 h, per oblast (sorted by skill vs recency)\n", md_table(o, "{:.4f}"), "",
           "## 3 h calibration table (model)\n", md_table(cal.rename_axis("predicted bin"), "{:.3f}"), ""]
    path.write_text("\n".join(out), encoding="utf-8")
    return m


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--score-test", action="store_true")
    ap.add_argument("--rerun-reason")
    a = ap.parse_args()
    choice = json.loads(CHOICE.read_text(encoding="utf-8"))
    p = panel()

    if a.dry_run:
        pred = predict(p, DRY_FROM, TEST_FROM, choice)
        label_end = pred.hour + pd.to_timedelta(pred.horizon_h, unit="h")
        assert label_end.max() <= TEST_FROM, "dry run must not reach the test period"
        pred.to_csv(REPORTS / "dryrun_predictions.csv", index=False)
        m = write_report(pred, choice, "DRY RUN on the last validation period", "the last validation period (dry run)", DRY_FROM,
                         REPORTS / "final_evaluation_dryrun.md", REPORTS / "calibration_dryrun.png")
        print(f"dry run 3h Brier model = {m.loc['3h', 'Brier model']:.6f} (no lock written)")
        return

    # ---- the real run ----
    if LOCK.exists() and not a.rerun_reason:
        raise SystemExit(f"The test period was already scored ({LOCK.read_text(encoding='utf-8').strip()}). "
                         "Re-run only for a pre-defined bug, with --rerun-reason.")
    if git("status", "--porcelain"):
        raise SystemExit("Commit everything first: the run records the git commit it was made from.")
    commit, now = git("rev-parse", "HEAD"), dt.datetime.now().isoformat(timespec="seconds")
    n = sum(1 for line in EXPERIMENTS.read_text(encoding="utf-8").splitlines() if line.startswith("| ") and line[2].isdigit()) + 1
    what = "RE-RUN: " + a.rerun_reason if a.rerun_reason else "final run"
    LOCK.write_text(json.dumps({"time": now, "commit": commit, "what": what}), encoding="utf-8")
    with open(EXPERIMENTS, "a", encoding="utf-8") as f:
        f.write(f"| {n} | {now[:10]} | **TEST** | `final_evaluation.py --score-test` ({what}), commit {commit[:7]} "
                f"| see `reports/final_evaluation.md` | Written before any metric was computed. |\n")
    pred = predict(p, TEST_FROM, CUTOFF, choice)
    pred.to_csv(REPORTS / "final_predictions.csv", index=False)
    pred = pd.read_csv(REPORTS / "final_predictions.csv", parse_dates=["hour"])  # metrics come from the saved file
    m = write_report(pred, choice, "TEST period", "the test period", TEST_FROM,
                     REPORTS / "final_evaluation.md", REPORTS / "calibration_test.png")
    print(f"test scored once. 3h skill vs recency = {m.loc['3h', 'skill vs recency']:.4f}")


if __name__ == "__main__":
    main()
