"""
Master pipeline runner for HSL City Bike project.
Executes raw data download, cleaning, station-month aggregation, and coordinate merging.
"""

import os
import sys
import argparse
import time

from src.download_data import download_season, fetch_station_metadata, DEFAULT_RAW_DIR
from src.clean_and_aggregate import process_all_data


def main():
    parser = argparse.ArgumentParser(description="Run complete HSL City Bike data pipeline.")
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Season year to process (default: 2025)",
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

    t_start = time.time()
    print("=" * 70)
    print("HSL CITY BIKE ALLOCATION: DATA PIPELINE")
    print(f"Target Season: {args.year if not args.all else 'All seasons (2016-2025)'}")
    print("=" * 70)

    # 1. Download phase
    if not args.skip_download:
        print("\n--- STEP 1: DOWNLOADING DATA ---")
        stations_csv = os.path.join(raw_dir, "stations.csv")
        fetch_station_metadata(stations_csv)

        if args.all:
            for y in range(2016, 2026):
                months = range(5, 11) if y in [2016, 2017] else range(4, 11)
                download_season(y, raw_dir, months)
        else:
            download_season(args.year, raw_dir)
    else:
        print("\n--- STEP 1: SKIPPING DOWNLOAD (using existing raw data) ---")

    # 2. Processing & Aggregation phase
    print("\n--- STEP 2: CLEANING TRIPS & AGGREGATING STATION-MONTH TABLE ---")
    target_year = None if args.all else args.year
    df_result = process_all_data(raw_dir, processed_dir, year=target_year)

    total_time = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_time:.1f} seconds!")
    print(f"Aggregated table: data/processed/station_month.csv ({len(df_result):,} rows)")
    print("=" * 70)


if __name__ == "__main__":
    main()

