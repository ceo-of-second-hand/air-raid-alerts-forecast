"""The three leakage tests from L35. Run from the repo root: python -m pytest tests/ -v

They use the real (pinned) data but never score anything, so they don't touch the test period.
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from d2_target_comparison import CUTOFF, HORIZONS, TEST_FROM, hourly_panel, load  # noqa: E402
from d7_d8_models import add_neighbours  # noqa: E402
from drop_active_check import FEATS_FINAL  # noqa: E402
from final_evaluation import DRY_FROM, make_split  # noqa: E402
from walk_forward import BLOCK, folds  # noqa: E402

EXPECTED_REGIONS = {
    "Cherkaska oblast", "Chernihivska oblast", "Chernivetska oblast", "Dnipropetrovska oblast", "Donetska oblast",
    "Ivano-Frankivska oblast", "Kharkivska oblast", "Khersonska oblast", "Khmelnytska oblast", "Kirovohradska oblast",
    "Kyiv City", "Kyivska oblast", "Lvivska oblast", "Mykolaivska oblast", "Odeska oblast", "Poltavska oblast",
    "Rivnenska oblast", "Sumska oblast", "Ternopilska oblast", "Vinnytska oblast", "Volynska oblast",
    "Zakarpatska oblast", "Zaporizka oblast", "Zhytomyrska oblast",
}
T0 = pd.Timestamp("2026-05-01 12:00", tz="UTC")


@pytest.fixture(scope="module")
def data():
    df = load()
    regions = sorted(df.region.unique())
    return df, regions, add_neighbours(hourly_panel(df, regions))


def test_future_data_cannot_change_features(data):
    """L7: delete every alert starting at or after T0 and push later end times even later; features up to T0 must not move."""
    df, regions, p = data
    past = df[df.started_at < T0].copy()
    late_end = past.finished_at > T0
    past.loc[late_end, "finished_at"] += pd.Timedelta(hours=5)
    p_past = add_neighbours(hourly_panel(past, regions))
    cols = ["region", "hour"] + FEATS_FINAL
    a = p[p.hour <= T0][cols].sort_values(["region", "hour"]).reset_index(drop=True)
    b = p_past[p_past.hour <= T0][cols].sort_values(["region", "hour"]).reset_index(drop=True)
    assert len(a) > 0
    pd.testing.assert_frame_equal(a, b)


@pytest.mark.parametrize("h", HORIZONS)
def test_purging(data, h):
    """L7 (e): in every validation period, the dry run and the final split, no training label window reaches evaluation."""
    p = data[2]
    windows = [(fs, fs + BLOCK) for fs in folds()] + [(DRY_FROM, TEST_FROM), (TEST_FROM, CUTOFF)]
    for eval_from, eval_to in windows:
        tr, ev = make_split(p, eval_from, eval_to, h)
        assert len(tr) and len(ev)
        assert tr.hour.max() + pd.Timedelta(hours=h) <= eval_from <= ev.hour.min()
        assert ev.hour.max() + pd.Timedelta(hours=h) <= eval_to


def test_excluded_regions_never_appear(data):
    """L15: exactly the 24 in-scope regions, in the alerts, the feature table and the neighbour list."""
    df, regions, p = data
    adjacency = json.loads((ROOT / "data" / "oblast_adjacency.json").read_text(encoding="utf-8"))
    assert set(df.region) == EXPECTED_REGIONS
    assert set(p.region) == EXPECTED_REGIONS
    assert set(adjacency) == EXPECTED_REGIONS
    assert all(set(ns) <= EXPECTED_REGIONS for ns in adjacency.values())
