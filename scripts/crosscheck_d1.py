"""D1 cross-check: official vs volunteer air raid alert data.

Answers Q1-Q6 from DECISIONS.md (D1 cross-check plan) and writes reports/d1_crosscheck.md.

Usage:
    python scripts/crosscheck_d1.py            # downloads data to data/raw if missing
"""
from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORT = ROOT / "reports" / "d1_crosscheck.md"
BASE_URL = "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/d10c80fa696bab42822b9f05b423fc8a30e79d20/datasets"
FILES = {"official": "official_data_en.csv", "volunteer": "volunteer_data_en.csv"}

EXCLUDED = {"Luhanska oblast", "Crimea", "Avtonomna Respublika Krym", "Sevastopol"}  # L15
TOLERANCES_MIN = [5, 15, 30]
MAIN_TOL = 15
RAION_SWITCH = pd.Timestamp("2025-12-01", tz="UTC")  # official alerts mostly raion-level from here
LATEST_FROM = pd.Timestamp("2025-10-01", tz="UTC")   # latest 4 quarters: 2025Q4..2026Q3


def download():
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES.values():
        path = RAW / name
        if not path.exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(f"{BASE_URL}/{name}", path)


def load():
    off = pd.read_csv(RAW / FILES["official"], parse_dates=["started_at", "finished_at"])
    vol = pd.read_csv(RAW / FILES["volunteer"], parse_dates=["started_at", "finished_at"])
    off = off.drop_duplicates()  # ~38% of official rows are exact duplicates
    off = off.rename(columns={"oblast": "region"})
    off = off[~off.region.isin(EXCLUDED)]
    vol = vol[~vol.region.isin(EXCLUDED)]
    # overlap window: both sources present
    lo = max(off.started_at.min(), vol.started_at.min())
    hi = min(off.started_at.max(), vol.started_at.max())
    off = off[(off.started_at >= lo) & (off.started_at <= hi)]
    vol = vol[(vol.started_at >= lo) & (vol.started_at <= hi)]
    return off, vol, lo, hi


def merge_intervals(df, flag_col=None):
    """Merge overlapping intervals per region into episodes (start, end[, any flag])."""
    out = []
    for region, g in df.sort_values("started_at").groupby("region"):
        s_cur = f_cur = None
        flag = False
        for s, f, fl in zip(g.started_at, g.finished_at,
                            g[flag_col] if flag_col else [False] * len(g)):
            if f_cur is None or s > f_cur:
                if f_cur is not None:
                    out.append((region, s_cur, f_cur, flag))
                s_cur, f_cur, flag = s, f, bool(fl)
            else:
                f_cur, flag = max(f_cur, f), flag or bool(fl)
        if f_cur is not None:
            out.append((region, s_cur, f_cur, flag))
    ep = pd.DataFrame(out, columns=["region", "start", "end", "naive"])
    ep["dur_min"] = (ep.end - ep.start).dt.total_seconds() / 60
    return ep


def match(a, b, tol_min):
    """For each episode in a, nearest episode start in b (same region) within tolerance."""
    a = a.sort_values("start").reset_index(drop=True)
    b = b.sort_values("start").rename(columns=lambda c: f"{c}_b" if c != "region" else c)
    b["start_key"] = b["start_b"]
    m = pd.merge_asof(a, b, left_on="start", right_on="start_key", by="region",
                      direction="nearest", tolerance=pd.Timedelta(minutes=tol_min))
    m["matched"] = m.start_b.notna()
    return m


def hourly_starts(ep, hours, regions):
    """Region x hour boolean: did an episode start in this hour."""
    h = ep.assign(hour=ep.start.dt.floor("h"))[["region", "hour"]].drop_duplicates()
    h["flag"] = True
    idx = pd.MultiIndex.from_product([regions, hours], names=["region", "hour"])
    return h.set_index(["region", "hour"]).flag.reindex(idx, fill_value=False)


def kappa(x, y):
    x, y = np.asarray(x, bool), np.asarray(y, bool)
    po = (x == y).mean()
    pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def time_share(ep, lo, hi):
    e = ep[(ep.end > lo) & (ep.start < hi)]
    covered = (e.end.clip(upper=hi) - e.start.clip(lower=lo)).dt.total_seconds()
    return covered.groupby(e.region).sum() / (hi - lo).total_seconds() * 100


def md_table(df, floatfmt="{:.1f}"):
    df = df.reset_index() if df.index.name or isinstance(df.index, pd.MultiIndex) else df
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = [floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    download()
    off, vol, lo, hi = load()
    regions = sorted(vol.region.unique())
    rollups = {
        "i_union": merge_intervals(off),
        "ii_oblast_only": merge_intervals(off[off.level == "oblast"]),
    }
    v_ep = merge_intervals(vol, flag_col="naive")
    out = [f"# D1 cross-check: official vs volunteer\n",
           f"Overlap window: {lo} → {hi}. Regions: {len(regions)}. "
           f"Episodes = overlapping alerts merged per region. Match = same region, start within ±tol min.\n",
           f"Volunteer episodes: {len(v_ep)}; official (i) union: {len(rollups['i_union'])}; "
           f"official (ii) oblast-only: {len(rollups['ii_oblast_only'])}.\n"]

    # Q1 — match rates
    out.append("## Q1. Same alerts? (match rate %, both directions)\n")
    rows = []
    for name, o_ep in rollups.items():
        for tol in TOLERANCES_MIN:
            for period, since in [("all", lo), ("latest 4Q", LATEST_FROM)]:
                o_p, v_p = o_ep[o_ep.start >= since], v_ep[v_ep.start >= since]
                rows.append({"rollup": name, "tol_min": tol, "period": period,
                             "off→vol %": match(o_p, v_p, tol).matched.mean() * 100,
                             "vol→off %": match(v_p, o_p, tol).matched.mean() * 100})
    out.append(md_table(pd.DataFrame(rows)) + "\n")

    best = "i_union"
    o_ep = rollups[best]
    o2v = match(o_ep, v_ep, MAIN_TOL)
    v2o = match(v_ep, o_ep, MAIN_TOL)
    o2v["q"] = o2v.start.dt.tz_localize(None).dt.to_period("Q").astype(str)
    v2o["q"] = v2o.start.dt.tz_localize(None).dt.to_period("Q").astype(str)
    by_q = pd.DataFrame({"off→vol %": o2v.groupby("q").matched.mean() * 100,
                         "vol→off %": v2o.groupby("q").matched.mean() * 100})
    by_q.index.name = "quarter"
    out.append(f"### By quarter — rollup (i), ±{MAIN_TOL} min\n\n" + md_table(by_q) + "\n")
    lat_o, lat_v = o2v[o2v.start >= LATEST_FROM], v2o[v2o.start >= LATEST_FROM]
    by_r = pd.DataFrame({"off→vol %": lat_o.groupby("region").matched.mean() * 100,
                         "vol→off %": lat_v.groupby("region").matched.mean() * 100,
                         "n_off": lat_o.groupby("region").size(),
                         "n_vol": lat_v.groupby("region").size()}).sort_values("off→vol %")
    by_r.index.name = "region"
    out.append(f"### By region — rollup (i), ±{MAIN_TOL} min, latest 4Q\n\n" + md_table(by_r) + "\n")

    # Q2 — start time agreement
    mm = v2o[v2o.matched].copy()
    mm["diff_min"] = (mm.start - mm.start_b).dt.total_seconds() / 60  # volunteer − official
    q2 = []
    for period, since in [("all", lo), ("latest 4Q", LATEST_FROM)]:
        d = mm[mm.start >= since].diff_min
        q2.append({"period": period, "n": len(d), "median signed (vol−off) min": d.median(),
                   "median |diff| min": d.abs().median(), "p90 |diff| min": d.abs().quantile(0.9)})
    out.append(f"## Q2. Start-time agreement (matched pairs, rollup (i), ±{MAIN_TOL} min)\n\n"
               + md_table(pd.DataFrame(q2)) + "\n")

    # Q3 — duration agreement, split by naive
    mm["dur_diff"] = mm.dur_min - mm.dur_min_b
    q3 = mm.groupby("naive").agg(n=("dur_diff", "size"),
                                 vol_median_dur=("dur_min", "median"),
                                 off_median_dur=("dur_min_b", "median"),
                                 median_diff_vol_minus_off=("dur_diff", "median"),
                                 p90_abs_diff=("dur_diff", lambda s: s.abs().quantile(0.9)))
    out.append("## Q3. Duration agreement by `naive` (minutes, matched pairs)\n\n" + md_table(q3) + "\n")

    # Q4 — hourly labels
    hours = pd.date_range(lo.floor("h"), hi.floor("h"), freq="h")
    hv = hourly_starts(v_ep, hours, regions)
    q4 = []
    for name, ep in rollups.items():
        ho = hourly_starts(ep, hours, regions)
        for period, since in [("all", lo), ("latest 4Q", LATEST_FROM)]:
            mask = hv.index.get_level_values("hour") >= since.floor("h")
            x, y = ho[mask], hv[mask]
            q4.append({"rollup": name, "period": period, "agree %": (x == y).mean() * 100,
                       "kappa": kappa(x, y), "off pos %": x.mean() * 100, "vol pos %": y.mean() * 100})
    out.append("## Q4. Hourly label 'alert starts in this hour' (region × hour)\n\n"
               + md_table(pd.DataFrame(q4), "{:.3f}") + "\n")
    ts = pd.DataFrame({"official (i) %": time_share(rollups["i_union"], LATEST_FROM, hi),
                       "official (ii) %": time_share(rollups["ii_oblast_only"], LATEST_FROM, hi),
                       "volunteer %": time_share(v_ep, LATEST_FROM, hi)}).fillna(0)
    ts.index.name = "region"
    out.append("### % time under alert, latest 4Q\n\n" + md_table(ts.sort_values("volunteer %")) + "\n")

    # Q5 — before vs after raion switch
    q5 = []
    for name, ep in rollups.items():
        ho = hourly_starts(ep, hours, regions)
        for period, (a, b) in {"before switch": (lo, RAION_SWITCH), "after switch": (RAION_SWITCH, hi)}.items():
            o_p = ep[(ep.start >= a) & (ep.start < b)]
            v_p = v_ep[(v_ep.start >= a) & (v_ep.start < b)]
            hh = ho.index.get_level_values("hour")
            mask = (hh >= a.floor("h")) & (hh < b.floor("h"))
            q5.append({"rollup": name, "period": period,
                       "off→vol %": match(o_p, v_p, MAIN_TOL).matched.mean() * 100,
                       "vol→off %": match(v_p, o_p, MAIN_TOL).matched.mean() * 100,
                       "hourly kappa": kappa(ho[mask], hv[mask])})
    out.append(f"## Q5. Before vs after the raion switch ({RAION_SWITCH.date()})\n\n"
               + md_table(pd.DataFrame(q5), "{:.3f}") + "\n")

    # Q6 — anomalies
    q6 = ts.loc[[r for r in ["Volynska oblast", "Rivnenska oblast", "Khersonska oblast",
                             "Kyiv City", "Kyivska oblast"] if r in ts.index]].copy()
    naive_share = v_ep[v_ep.start >= LATEST_FROM].groupby("region").naive.mean() * 100
    q6["vol naive %"] = naive_share.reindex(q6.index)
    q6["off→vol match %"] = by_r["off→vol %"].reindex(q6.index)
    q6["vol→off match %"] = by_r["vol→off %"].reindex(q6.index)
    out.append("## Q6. Anomalies (latest 4Q)\n\n" + md_table(q6) + "\n")

    q1 = pd.DataFrame(rows).set_index(["rollup", "tol_min", "period"])
    u = q1.loc[("i_union", MAIN_TOL, "latest 4Q")]
    o = q1.loc[("ii_oblast_only", MAIN_TOL, "latest 4Q")]
    q2_latest = next(r for r in q2 if r["period"] == "latest 4Q")
    out[1:1] = [
        "## In short\n",
        "- **What this does:** checks whether the two alert files in the Vadimkin repo (\"official\", parsed from the "
        "@air_alert_ua channel, and \"volunteer\", parsed from the єТривога channel) contain the same alerts, "
        f"over the period both cover ({lo.date()} → {hi.date()}).",
        f"- **Same alerts?** In the latest year, only **{u['off→vol %']:.0f}%** of official alerts have a volunteer alert "
        f"starting within ±{MAIN_TOL} min, and only **{u['vol→off %']:.0f}%** the other way round "
        f"({o['off→vol %']:.0f}% / {o['vol→off %']:.0f}% if only whole-oblast official alerts count). "
        "The threshold fixed in advance was 90% both ways, so the check **failed**.",
        f"- **Start times:** when an alert is in both files, the start times agree closely "
        f"(typical gap {q2_latest['median |diff| min']:.1f} min).",
        f"- **Made-up end times:** volunteer alerts with no recorded end get start + 30 min; the matching official "
        f"alerts actually lasted a median of {q3.loc[True, 'off_median_dur']:.0f} min.",
        "- **Later finding (see `DECISIONS.md`):** the volunteer parser assigns some alerts to the wrong oblast, "
        "so the official file was chosen as the data source.\n",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"report written to {REPORT}")


if __name__ == "__main__":
    main()
