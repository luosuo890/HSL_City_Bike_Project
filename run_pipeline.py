"""
Master pipeline runner for HSL City Bike project.
Executes raw data download, cleaning, station-month aggregation, and coordinate merging.
"""

import os
import sys
import argparse
import time

from src.download_data import download_season, fetch_station_metadata, fetch_fmi_weather, DEFAULT_RAW_DIR
from src.clean_and_aggregate import process_all_data
from src.aggregate_intraday import run_intraday_aggregation


def main():
    parser = argparse.ArgumentParser(description="Run complete HSL City Bike data pipeline.")
    parser.add_argument(
        "--year",
        "--years",
        dest="years",
        nargs="+",
        default=None,
        help="Season year(s) to process (e.g. --year 2024, --year 2024 2025; default: 2024 and 2025)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download and process all historical seasons (2016-2025)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading and only run processing on existing raw data",
    )
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(project_dir, "data", "raw")
    processed_dir = os.path.join(project_dir, "data", "processed")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Determine target years
    if args.all:
        target_years = list(range(2016, 2026))
    elif args.years:
        target_years = []
        for y_str in args.years:
            for part in str(y_str).split(","):
                part = part.strip()
                if part.isdigit():
                    target_years.append(int(part))
    elif not args.skip_download:
        target_years = [2024, 2025]
    else:
        # --skip-download without --year: process all available raw data
        target_years = None

    t_start = time.time()
    print("=" * 70)
    print("HSL CITY BIKE ALLOCATION: DATA PIPELINE")
    target_str = "All available raw seasons" if target_years is None else f"{target_years}"
    print(f"Target Season(s): {target_str}")
    print("=" * 70)

    # 1. Download phase
    if not args.skip_download:
        print("\n--- STEP 1: DOWNLOADING DATA ---")
        stations_csv = os.path.join(raw_dir, "stations.csv")
        fetch_station_metadata(stations_csv)

        years_to_dl = target_years if target_years is not None else [2024, 2025]
        for y in years_to_dl:
            fetch_fmi_weather(y, raw_dir)
            months = range(5, 11) if y in [2016, 2017] else range(4, 11)
            download_season(y, raw_dir, months)
    else:
        print("\n--- STEP 1: SKIPPING DOWNLOAD (using existing raw data) ---")

    # 2. Processing & Aggregation phase
    print("\n--- STEP 2: CLEANING TRIPS & AGGREGATING STATION-MONTH TABLE ---")
    df_result = process_all_data(raw_dir, processed_dir, year=target_years)

    # 3. Intraday & Hourly Aggregation phase
    print("\n--- STEP 3: AGGREGATING INTRADAY & HOURLY PROFILES ---")
    run_intraday_aggregation(raw_dir, processed_dir)

    total_time = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_time:.1f} seconds!")
    print(f"Primary table : data/processed/station_month.csv ({len(df_result):,} rows)")
    print(f"Intraday table: data/processed/station_intraday_monthly.csv")
    print(f"City hourly   : data/processed/city_hourly_summary.csv")
    print("=" * 70)


if __name__ == "__main__":
    main()

