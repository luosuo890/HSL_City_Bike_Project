"""
Data Downloader for HSL City Bike Project.
Downloads raw trip data from dev.hsl.fi and station coordinates from HSL's ArcGIS service.
"""

import os
import sys
import argparse
import urllib.request
import urllib.parse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL_OD = "https://dev.hsl.fi/citybikes/od-trips-{year}/{year}-{month:02d}.csv"
ARCGIS_STATION_URL = (
    "https://services1.arcgis.com/sswNXkUiRoWtrx0t/arcgis/rest/services/"
    + urllib.parse.quote("Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin")
    + "/FeatureServer/0/query?where=1%3D1&outFields=*&f=json"
)

DEFAULT_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")


def download_file(url: str, dest_path: str, timeout: int = 60) -> bool:
    """Download a file with progress reporting."""
    filename = os.path.basename(dest_path)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"  [Skip] {filename} already exists ({os.path.getsize(dest_path) / (1024*1024):.1f} MB)")
        return True

    print(f"  [Downloading] {filename} from {url} ...")
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            with open(dest_path, "wb") as f:
                f.write(data)
        elapsed = time.time() - t0
        mb = len(data) / (1024 * 1024)
        speed = mb / elapsed if elapsed > 0 else 0
        print(f"  [Done] {filename}: {mb:.1f} MB in {elapsed:.1f}s ({speed:.1f} MB/s)")
        return True
    except Exception as e:
        print(f"  [Error] Failed to download {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def fetch_station_metadata(output_path: str) -> bool:
    """Fetch official station metadata and coordinates from HSL ArcGIS Open Data."""
    print("\nFetching official station coordinates from HSL ArcGIS service...")
    try:
        req = urllib.request.Request(ARCGIS_STATION_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw_data = json.loads(r.read().decode("utf-8"))

        features = raw_data.get("features", [])
        if not features:
            print("  [Error] No features returned from ArcGIS station service.")
            return False

        import csv

        fieldnames = [
            "station_id",
            "name",
            "name_fi",
            "name_se",
            "address",
            "city",
            "operator",
            "capacity",
            "longitude",
            "latitude",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for feat in features:
                attr = feat.get("attributes", {})
                writer.writerow(
                    {
                        "station_id": int(attr.get("ID")) if str(attr.get("ID", "")).isdigit() else attr.get("ID"),
                        "name": attr.get("Name", ""),
                        "name_fi": attr.get("Nimi", ""),
                        "name_se": attr.get("Namn", ""),
                        "address": attr.get("Osoite", ""),
                        "city": attr.get("Kaupunki", ""),
                        "operator": attr.get("Operaattor", ""),
                        "capacity": attr.get("Kapasiteet", ""),
                        "longitude": attr.get("x", ""),
                        "latitude": attr.get("y", ""),
                    }
                )

        print(f"  [Done] Saved {len(features)} stations to {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"  [Error] Failed to fetch station coordinates: {e}")
        return False


def download_season(year: int, raw_dir: str, months=range(4, 11)) -> list:
    """Download all monthly trip CSVs for a given cycling season."""
    os.makedirs(raw_dir, exist_ok=True)
    print(f"\nDownloading HSL trip data for season {year} (months {list(months)})...")

    downloaded = []
    for m in months:
        url = BASE_URL_OD.format(year=year, month=m)
        dest = os.path.join(raw_dir, f"{year}-{m:02d}.csv")
        if download_file(url, dest):
            downloaded.append(dest)
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Download HSL City Bike raw data.")
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Season year to download (default: 2025)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all historical seasons (2016-2025)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_RAW_DIR,
        help=f"Directory to store raw data (default: {DEFAULT_RAW_DIR})",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Download station metadata
    stations_csv = os.path.join(args.output_dir, "stations.csv")
    fetch_station_metadata(stations_csv)

    # 2. Download trips
    if args.all:
        years = range(2016, 2026)
        print(f"\nInitiating download for all years: {list(years)}")
        for y in years:
            # 2016-2017 started in May (month 5), others in April (month 4)
            months = range(5, 11) if y in [2016, 2017] else range(4, 11)
            download_season(y, args.output_dir, months)
    else:
        download_season(args.year, args.output_dir)

    print("\nDownload complete. All files saved to:", args.output_dir)


if __name__ == "__main__":
    main()

