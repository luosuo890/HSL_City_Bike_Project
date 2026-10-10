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


FMI_STATIONS = {
    "Helsinki": {"fmisid": 100971, "name": "Helsinki Kaisaniemi"},
    "Espoo": {"fmisid": 874863, "name": "Espoo Tapiola"},
}


def fetch_fmi_weather(year: int, raw_dir: str, start_month: int = 4, end_month: int = 10) -> str:
    """
    Fetch daily observed weather data from FMI WFS API for Helsinki and Espoo.
    Saves raw observations to data/raw/weather_daily_{year}.csv.
    """
    import xml.etree.ElementTree as ET
    import csv

    os.makedirs(raw_dir, exist_ok=True)
    out_csv = os.path.join(raw_dir, f"weather_daily_{year}.csv")

    if os.path.exists(out_csv) and os.path.getsize(out_csv) > 0:
        print(f"  [Skip] weather_daily_{year}.csv already exists ({os.path.getsize(out_csv) / 1024:.1f} KB)")
        return out_csv

    print(f"\nFetching official FMI daily weather observations for {year} (April-October)...")
    starttime = f"{year}-{start_month:02d}-01T00:00:00Z"
    last_day = 31 if end_month in [1, 3, 5, 7, 8, 10, 12] else 30
    endtime = f"{year}-{end_month:02d}-{last_day}T23:59:59Z"

    records = []
    for city, station_info in FMI_STATIONS.items():
        fmisid = station_info["fmisid"]
        s_name = station_info["name"]
        print(f"  Querying FMI station: {s_name} (FMISID {fmisid}) ...")
        url = (
            f"https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature"
            f"&storedquery_id=fmi::observations::weather::daily::simple"
            f"&fmisid={fmisid}&starttime={starttime}&endtime={endtime}"
            f"&parameters=tday,tmin,tmax,rrday,snow"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                root = ET.fromstring(r.read())

            for elem in root.iter("{http://xml.fmi.fi/schema/wfs/2.0}BsWfsElement"):
                t = elem.find("{http://xml.fmi.fi/schema/wfs/2.0}Time")
                p = elem.find("{http://xml.fmi.fi/schema/wfs/2.0}ParameterName")
                v = elem.find("{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue")
                if t is not None and p is not None and v is not None:
                    records.append(
                        {
                            "city": city,
                            "fmisid": fmisid,
                            "station_name": s_name,
                            "time_utc": t.text,
                            "parameter": p.text,
                            "value": v.text,
                        }
                    )
        except Exception as e:
            print(f"  [Error] Failed to fetch weather for {city} ({s_name}): {e}")

    if not records:
        print("  [Error] No weather records retrieved from FMI.")
        return ""

    fieldnames = ["city", "fmisid", "station_name", "time_utc", "parameter", "value"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"  [Done] Saved {len(records)} raw weather observations to {os.path.basename(out_csv)}")
    return out_csv


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
        "--years",
        dest="years",
        nargs="+",
        default=None,
        help="Season year(s) to download (e.g. --year 2024, --year 2024 2025; default: 2024 and 2025)",
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

    # Determine years to download
    if args.all:
        target_years = list(range(2016, 2026))
    elif args.years:
        target_years = []
        for y_str in args.years:
            for part in str(y_str).split(","):
                part = part.strip()
                if part.isdigit():
                    target_years.append(int(part))
    else:
        target_years = [2024, 2025]

    # 2. Download FMI weather observations
    print(f"\nProcessing weather and trips for target seasons: {target_years}")
    for y in target_years:
        fetch_fmi_weather(y, args.output_dir)

    # 3. Download trips
    for y in target_years:
        months = range(5, 11) if y in [2016, 2017] else range(4, 11)
        download_season(y, args.output_dir, months)

    print("\nDownload complete. All files saved to:", args.output_dir)


if __name__ == "__main__":
    main()

