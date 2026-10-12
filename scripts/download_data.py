"""Download the raw data into data/raw/ (skips files that already exist).

- official_data_en.csv  : alerts parsed from the official @air_alert_ua channel (used by the model)
- volunteer_data_en.csv : alerts parsed from the volunteer єТривога channel (only used in the D1 cross-check)
- ukr_admin2.geojson    : district boundaries (used to build the oblast neighbour list)
"""
from pathlib import Path
import urllib.request

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
BASE = "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main"
FILES = {
    "official_data_en.csv": f"{BASE}/datasets/official_data_en.csv",
    "volunteer_data_en.csv": f"{BASE}/datasets/volunteer_data_en.csv",
    "ukr_admin2.geojson": f"{BASE}/example/ukr_admin2.geojson",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        path = RAW / name
        if path.exists():
            print(f"exists, skipping: {name}")
        else:
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(url, path)


if __name__ == "__main__":
    main()
