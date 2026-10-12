"""Download the raw data into data/raw/ and check it is exactly the data the results were produced with.

Files come from a fixed commit of the upstream repo (it changes daily), and each file's SHA-256 is checked.
- official_data_en.csv  : alerts parsed from the official @air_alert_ua channel (used by the model)
- volunteer_data_en.csv : alerts parsed from the volunteer єТривога channel (only used in the D1 cross-check)
- ukr_admin2.geojson    : district boundaries (used to build the oblast neighbour list)
"""
import hashlib
from pathlib import Path
import urllib.request

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
COMMIT = "d10c80fa696bab42822b9f05b423fc8a30e79d20"  # upstream commit of 2026-10-12 05:05 UTC
BASE = f"https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/{COMMIT}"
FILES = {
    "official_data_en.csv": ("datasets/official_data_en.csv",
                             "b396f87696243069eec0219880e87dcd642b20beb0a7bae0d0e1f61e1ed20ec4"),
    "volunteer_data_en.csv": ("datasets/volunteer_data_en.csv",
                              "b6c0160f0b4e6a83fa0d6f5dfbf1a3c623b6122819d37185f99b57d7587da14b"),
    "ukr_admin2.geojson": ("example/ukr_admin2.geojson",
                           "3812bc231e5558f015c19bc050c0c039f91797e062718931dd08835348b0d494"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, (remote, expected) in FILES.items():
        path = RAW / name
        if not path.exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(f"{BASE}/{remote}", path)
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"{name}: SHA-256 mismatch (got {actual}, expected {expected}). "
                             f"Delete data/raw/{name} and run again.")
        print(f"ok: {name}")


if __name__ == "__main__":
    main()
