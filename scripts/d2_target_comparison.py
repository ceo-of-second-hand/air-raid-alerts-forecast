"""D2: compare candidate forecast targets on the official data, at oblast level.

(a) P(alert starts in oblast within next h hours), h in {1, 3, 6}
(b) number of alert starts in oblast tomorrow (Kyiv date)
(d) duration of an alert, predicted at the moment it starts

Each target gets naive baselines + one light model (HistGradientBoosting), same train/test split,
so the numbers show how predictable each target is. Writes reports/d2_target_comparison.md.

Oblast event definition: every raion- or oblast-level alert row is an event of its oblast
(hromada-level rows are excluded: they are mostly strike-drone threat posts).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "official_data_en.csv"
REPORT = ROOT / "reports" / "d2_target_comparison.md"

EXCLUDED = {"Luhanska oblast", "Crimea", "Avtonomna Respublika Krym", "Sevastopol"}
DATA_FROM = pd.Timestamp("2025-12-01", tz="UTC")   # raion-level era
CUTOFF = pd.Timestamp("2026-09-06 21:00", tz="UTC")  # L18
TEST_FROM = CUTOFF - pd.Timedelta(weeks=6)
HORIZONS = [1, 3, 6]
SEED = 0


def load():
    df = pd.read_csv(RAW, parse_dates=["started_at", "finished_at"]).drop_duplicates()
    df = df[~df.oblast.isin(EXCLUDED) & df.level.isin(["raion", "oblast"])]
    df = df[(df.started_at >= DATA_FROM) & (df.started_at < CUTOFF)].copy()
    df["dur_min"] = (df.finished_at - df.started_at).dt.total_seconds() / 60
    return df.rename(columns={"oblast": "region"})


def md_table(df, fmt="{:.3f}"):
    df = df.reset_index()
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt.format(v) if isinstance(v, (float, np.floating)) else str(v)
                                       for v in row) + " |")
    return "\n".join(lines)


def kyiv_calendar(ts):
    local = ts.dt.tz_convert("Europe/Kyiv")
    return local.dt.hour, local.dt.dayofweek


# ---------- (a) hourly panel ----------
def hourly_panel(df, regions):
    hours = pd.date_range(DATA_FROM, CUTOFF, freq="h", inclusive="left")
    starts = (df.assign(hour=df.started_at.dt.floor("h")).groupby(["region", "hour"]).size()
              .reindex(pd.MultiIndex.from_product([regions, hours], names=["region", "hour"]), fill_value=0))
    p = starts.rename("n").reset_index()
    g = p.groupby("region").n
    # features at time T = start of the hour: only starts strictly before T
    for w in [1, 3, 6, 24, 168]:
        p[f"starts_prev_{w}h"] = g.transform(lambda s: s.shift(1).rolling(w, min_periods=1).sum())
    nat = p.groupby("hour").n.sum().shift(1)
    p["nat_prev_1h"] = p.hour.map(nat)
    p["nat_prev_3h"] = p.hour.map(nat.rolling(3, min_periods=1).sum())
    # alerts active at T: started before T and not finished by T (known at T)
    act = []
    for r, d in df.groupby("region"):
        s, f = d.started_at.values, d.finished_at.values
        h = hours.values
        act.append(pd.DataFrame({"region": r, "hour": hours,
                                 "active_at_T": ((s[None, :] < h[:, None]) & (f[None, :] > h[:, None])).sum(1)}))
    p = p.merge(pd.concat(act), on=["region", "hour"], how="left").fillna({"active_at_T": 0})
    # targets: any start in [T, T+h)
    for h in HORIZONS:
        p[f"y_{h}h"] = g.transform(lambda s: s[::-1].rolling(h, min_periods=1).sum()[::-1]).gt(0).astype(int)
    p["hod"], p["dow"] = kyiv_calendar(p.hour)
    p["region_code"] = p.region.astype("category").cat.codes
    return p


def eval_a(p):
    feats = ["region_code", "hod", "dow", "active_at_T", "nat_prev_1h", "nat_prev_3h"] + \
            [c for c in p.columns if c.startswith("starts_prev_")]
    rows = []
    for h in HORIZONS:
        y = f"y_{h}h"
        tr = p[p.hour < TEST_FROM - pd.Timedelta(hours=h)]  # purge: label window must end before test
        te = p[(p.hour >= TEST_FROM) & (p.hour < CUTOFF - pd.Timedelta(hours=h))]
        clim = tr.groupby(["region", "hod", "dow"])[y].mean()
        p_clim = te.set_index(["region", "hod", "dow"]).index.map(clim).fillna(tr[y].mean()).values
        p_pers = (te.starts_prev_1h > 0).astype(float).values
        # recency baselines: P(y | oblast, any start in last k hours [, alert active at T]) from train
        recency = {}
        for k in [1, 3, 6]:
            key = lambda d: [d.region, d[f"starts_prev_{k}h"] > 0]
            tab = tr.groupby(key(tr))[y].mean()
            recency[f"recency k={k}h"] = pd.Series(list(zip(*key(te)))).map(tab).fillna(tr[y].mean()).values
        key = lambda d: [d.region, d.starts_prev_3h > 0, d.active_at_T > 0]
        tab = tr.groupby(key(tr))[y].mean()
        recency["recency 3h + active"] = pd.Series(list(zip(*key(te)))).map(tab).fillna(tr[y].mean()).values
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=SEED,
                                           categorical_features=[0]).fit(tr[feats], tr[y])
        p_gbm = m.predict_proba(te[feats])[:, 1]
        base = te[y].mean()
        preds = {"climatology": p_clim, "persistence (hard 0/1)": p_pers, **recency, "GBM": p_gbm}
        b_clim = brier_score_loss(te[y], p_clim)
        b_rec = min(brier_score_loss(te[y], p) for p in recency.values())  # best recency baseline (picked on test: favours the baseline)
        for name, pr in preds.items():
            b = brier_score_loss(te[y], pr)
            rows.append({"horizon": f"{h}h", "method": name, "base rate": base, "Brier": b,
                         "skill vs clim": 1 - b / b_clim, "skill vs best recency": 1 - b / b_rec,
                         "AUC": roc_auc_score(te[y], pr),
                         "accuracy@0.5": ((pr >= 0.5) == te[y]).mean(),
                         "majority-class acc": max(base, 1 - base)})
    return pd.DataFrame(rows).set_index(["horizon", "method"])


# ---------- (b) daily counts ----------
def eval_b(df, regions):
    day = df.started_at.dt.tz_convert("Europe/Kyiv").dt.date
    days = pd.date_range(DATA_FROM.tz_convert("Europe/Kyiv").date(), (CUTOFF - pd.Timedelta(hours=1)).tz_convert("Europe/Kyiv").date())
    c = (df.assign(day=pd.to_datetime(day)).groupby(["region", "day"]).size()
         .reindex(pd.MultiIndex.from_product([regions, days], names=["region", "day"]), fill_value=0)
         .rename("n").reset_index())
    g = c.groupby("region").n
    for k in range(1, 8):
        c[f"lag{k}"] = g.shift(k)  # forecast for day D issued at end of D-1
    c["mean7"] = g.transform(lambda s: s.shift(1).rolling(7).mean())
    c["mean28"] = g.transform(lambda s: s.shift(1).rolling(28).mean())
    c["dow"] = c.day.dt.dayofweek
    c["region_code"] = c.region.astype("category").cat.codes
    c = c.dropna()
    test_day = pd.Timestamp(TEST_FROM.tz_convert("Europe/Kyiv").date())
    tr, te = c[c.day < test_day], c[c.day >= test_day]
    feats = ["region_code", "dow", "mean7", "mean28"] + [f"lag{k}" for k in range(1, 8)]
    m = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05, random_state=SEED,
                                      categorical_features=[0]).fit(tr[feats], tr.n)
    rows = []
    for name, pr in [("yesterday", te.lag1), ("7-day mean", te.mean7), ("GBM (Poisson)", m.predict(te[feats]))]:
        err = np.abs(pr - te.n)
        rows.append({"method": name, "mean actual/day": te.n.mean(), "MAE": err.mean(),
                     "within ±20% or ±2": (err <= np.maximum(2, 0.2 * te.n)).mean()})
    return pd.DataFrame(rows).set_index("method")


# ---------- (d) duration at start ----------
def eval_d(df):
    d = df.sort_values("started_at").reset_index(drop=True)
    d["hod"], d["dow"] = kyiv_calendar(d.started_at)
    d["region_code"] = d.region.astype("category").cat.codes
    # context known at start time t: active alerts in oblast / nationally, recent completed durations
    s, f = d.started_at.values, d.finished_at.values
    t = s
    d["active_obl"] = 0
    d["nat_active"] = 0
    d["recent_med_dur"] = np.nan
    for r, idx in d.groupby("region").groups.items():
        idx = np.asarray(idx)
        rs, rf, rdur = s[idx], f[idx], d.dur_min.values[idx]
        for j, i in enumerate(idx):
            prior = slice(0, j)
            d.at[i, "active_obl"] = int(((rs[prior] <= t[i]) & (rf[prior] > t[i])).sum())
            done = (rf[prior] <= t[i]) & (rf[prior] > t[i] - np.timedelta64(7, "D"))  # completed before t only
            if done.any():
                d.at[i, "recent_med_dur"] = np.median(rdur[prior][done])
    fs = np.sort(f)
    d["nat_active"] = np.arange(len(d)) - np.searchsorted(fs, t, side="right")  # started before t minus finished by t
    d["imputed_1h"] = np.isclose(d.dur_min, 60, atol=0.01)
    tr = d[d.finished_at < TEST_FROM]           # label (end) must be known before test start
    te = d[d.started_at >= TEST_FROM]
    feats = ["region_code", "hod", "dow", "active_obl", "nat_active", "recent_med_dur"]
    m = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.05, random_state=SEED,
                                      categorical_features=[0]).fit(tr[feats], tr.dur_min)
    med = tr.groupby("region").dur_min.median()
    rows = []
    for name, pr in [("global median", np.full(len(te), tr.dur_min.median())),
                     ("oblast median", te.region.map(med).values), ("GBM", m.predict(te[feats]))]:
        err = np.abs(pr - te.dur_min.values)
        rows.append({"method": name, "median actual min": te.dur_min.median(), "MAE min": err.mean(),
                     "median abs err min": np.median(err), "within ±15 min": (err <= 15).mean(),
                     "within ±25%": (err <= 0.25 * te.dur_min.values).mean(),
                     ">1h correct": ((pr > 60) == (te.dur_min.values > 60)).mean()})
    noise = {"test alerts": len(te), "share exactly 60 min (possible imputed end)": te.imputed_1h.mean(),
             "share > 24 h (possible missed all-clear)": (te.dur_min > 1440).mean()}
    return pd.DataFrame(rows).set_index("method"), noise


def main():
    df = load()
    regions = sorted(df.region.unique())
    out = ["# D2: target comparison (official data, oblast level)\n",
           f"Data {DATA_FROM.date()} → {CUTOFF} UTC, {len(regions)} oblasts, {len(df)} raion/oblast alert rows. "
           f"Test = last 6 weeks (from {TEST_FROM}). One train/test split, no tuning: these numbers compare "
           f"targets, they are not final results.\n"]
    res_a, res_b = eval_a(hourly_panel(df, regions)), eval_b(df, regions)
    res_d, noise = eval_d(df)
    a3 = res_a.loc["3h"]
    out[1:1] = [
        "## In short\n",
        "- **What this does:** tries three possible things to forecast, each with simple rules and one model, "
        "on the same data (official alerts, Dec 2025 → Sep 6 2026, 24 oblasts), checked on the last 6 weeks.",
        f"- **(a) Will an alert start in the oblast within 3 hours?** The model's Brier score (how far its probabilities "
        f"are from what happened; lower is better) is {a3.loc['GBM', 'skill vs clim']:.0%} lower than that of the oblast's usual rate "
        f"for that hour and weekday (climatology), and {a3.loc['GBM', 'skill vs best recency']:.0%} lower than that of the best "
        "\"what's happening right now\" rule. Clearly predictable.",
        f"- **(b) How many alerts start tomorrow?** The model is off by {res_b.loc['GBM (Poisson)', 'MAE']:.1f} alerts per day on average, "
        f"vs {res_b.loc['7-day mean', 'MAE']:.1f} for \"same as the last 7 days' average\". Barely better.",
        f"- **(d) How long will an alert last?** The model is within ±15 min for {res_d.loc['GBM', 'within ±15 min']:.0%} of alerts, "
        f"the same as just using the oblast's usual duration ({res_d.loc['oblast median', 'within ±15 min']:.0%}). Not predictable with these inputs.",
        "- **Caveat:** one 6-week period, no tuning. This period is the **test period**, so looking at it is logged in `experiments.md`.\n",
    ]
    out.append("## (a) P(alert starts in oblast within next h hours)\n\n" + md_table(res_a) + "\n")
    out.append("## (b) Alert starts per oblast per day (forecast issued the evening before)\n\n" + md_table(res_b) + "\n")
    out.append("## (d) Alert duration, predicted at its start\n\n" + md_table(res_d) + "\n\n"
               + "Label noise in test: " + ", ".join(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}"
                                                      for k, v in noise.items()) + "\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
