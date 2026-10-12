"""Build the oblast neighbour list from district boundaries (repo's example/ukr_admin2.geojson).

Two oblasts are neighbours if their boundaries come within ~1 km (0.01°) of each other, which
absorbs small gaps between the district polygons. Writes data/oblast_adjacency.json using the
region names of the alert data. Excluded regions (L15) are dropped.
"""
import json
from pathlib import Path
import urllib.request

from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / "data" / "raw" / "ukr_admin2.geojson"
OUT = ROOT / "data" / "oblast_adjacency.json"
URL = "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/example/ukr_admin2.geojson"
EXCLUDED = {"Autonomous Republic of Crimea", "Sevastopol", "Luhanska"}


def to_alert_name(adm1):
    return "Kyiv City" if adm1 == "Kyiv" else f"{adm1} oblast"


def main():
    if not GEOJSON.exists():
        GEOJSON.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, GEOJSON)
    parts = {}
    for f in json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]:
        adm1 = f["properties"]["adm1_name"]
        if adm1 not in EXCLUDED:
            # simplify (~300 m) first: full-detail unions take minutes and don't change adjacency
            parts.setdefault(adm1, []).append(shape(f["geometry"]).simplify(0.003).buffer(0))
    shapes = {k: unary_union(v) for k, v in parts.items()}
    adj = {to_alert_name(a): sorted(to_alert_name(b) for b in shapes if b != a and shapes[a].distance(shapes[b]) < 0.01)
           for a in sorted(shapes)}
    OUT.write_text(json.dumps(adj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(adj)} regions written to {OUT}")


if __name__ == "__main__":
    main()
