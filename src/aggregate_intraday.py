"""
Intraday and Day-Type Aggregation Pipeline for HSL City Bike Project.
Processes raw 2024 and 2025 journey CSV records into lightweight hourly and day-type analytical tables:
- data/processed/station_intraday_monthly.csv: Station-level hourly profiles by day-type and month
- data/processed/city_hourly_summary.csv: City-level hourly profiles by day-type and month
- data/processed/intraday_audit_metrics.json: Data quality audit metrics (midnight crossings, unmapped docks)
"""

import os
import sys
import glob
import json
import time
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.clean_and_aggregate import clean_trip_dataframe


def run_intraday_aggregation(raw_dir=None, processed_dir=None):
    """
    Executes intraday aggregation across 2024 and 2025 HSL journey records.
    Can be called standalone or imported into run_pipeline.py.
    """
    t_start = time.time()
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if raw_dir is None:
        raw_dir = os.path.join(project_dir, "data", "raw")
    if processed_dir is None:
        processed_dir = os.path.join(project_dir, "data", "processed")

    os.makedirs(processed_dir, exist_ok=True)

    print("=" * 70)
    print("HSL CITY BIKE: INTRADAY & DAY-TYPE AGGREGATION")
    print("=" * 70)

    # 1. Load Station Metadata
    stations_path = os.path.join(raw_dir, "stations.csv")
    if os.path.exists(stations_path):
        st_df = pd.read_csv(stations_path)
        city_clean = st_df["city"].fillna("Helsinki").astype(str).str.strip()
        city_clean = city_clean.replace("", "Helsinki")
        st_map = pd.DataFrame({
            "station_id": pd.to_numeric(st_df["station_id"], errors="coerce").astype(int),
            "station_name": st_df["name"].astype(str),
            "city": city_clean,
            "capacity": pd.to_numeric(st_df["capacity"], errors="coerce"),
            "longitude": pd.to_numeric(st_df["longitude"], errors="coerce"),
            "latitude": pd.to_numeric(st_df["latitude"], errors="coerce"),
        }).drop_duplicates("station_id")
    else:
        st_map = pd.DataFrame(columns=["station_id", "station_name", "city", "capacity", "longitude", "latitude"])

    st_dict = st_map.set_index("station_id").to_dict("index")
    print(f"Loaded {len(st_map):,} official stations.")

    # 2. List Raw Journey Files
    raw_files = sorted(
        glob.glob(os.path.join(raw_dir, "2024-*.csv")) +
        glob.glob(os.path.join(raw_dir, "2025-*.csv"))
    )
    if not raw_files:
        print(f"[Warning] No 2024 or 2025 raw journey files found in {raw_dir}.")
        print("Please run 'python run_pipeline.py' first to download the raw data.")
        return False

    print(f"Found {len(raw_files)} raw journey files. Aggregating intraday trips...")

    audit_summary = {
        "2024": {"raw_trips": 0, "clean_trips": 0, "midnight_crossings": 0, "unmapped_dep_trips": 0, "unmapped_ret_trips": 0},
        "2025": {"raw_trips": 0, "clean_trips": 0, "midnight_crossings": 0, "unmapped_dep_trips": 0, "unmapped_ret_trips": 0},
    }

    station_monthly_records = []
    city_hourly_records = []

    for fpath in raw_files:
        fname = os.path.basename(fpath)
        year_str, month_str = fname.replace(".csv", "").split("-")
        year = int(year_str)
        month = int(month_str)

        t0 = time.time()
        raw_df = pd.read_csv(fpath, low_memory=False)
        clean_df, stats = clean_trip_dataframe(raw_df)

        audit_summary[year_str]["raw_trips"] += stats["total_raw"]
        audit_summary[year_str]["clean_trips"] += stats["total_clean"]

        # Parse timestamps in Europe/Helsinki local time
        clean_df["dep_dt"] = pd.to_datetime(clean_df["Departure"], format="ISO8601")
        clean_df["ret_dt"] = pd.to_datetime(clean_df["Return"], format="ISO8601")

        clean_df["dep_date"] = clean_df["dep_dt"].dt.date
        clean_df["ret_date"] = clean_df["ret_dt"].dt.date
        clean_df["dep_hour"] = clean_df["dep_dt"].dt.hour
        clean_df["ret_hour"] = clean_df["ret_dt"].dt.hour
        clean_df["dep_is_weekend"] = (clean_df["dep_dt"].dt.dayofweek >= 5).astype(int)
        clean_df["ret_is_weekend"] = (clean_df["ret_dt"].dt.dayofweek >= 5).astype(int)

        # Audit midnight crossings
        midnight_count = int((clean_df["dep_date"] != clean_df["ret_date"]).sum())
        audit_summary[year_str]["midnight_crossings"] += midnight_count

        # Map cities
        clean_df["dep_city"] = clean_df["dep_id_clean"].map(lambda sid: st_dict.get(sid, {}).get("city", "Unknown"))
        clean_df["ret_city"] = clean_df["ret_id_clean"].map(lambda sid: st_dict.get(sid, {}).get("city", "Unknown"))

        unmapped_dep = int((clean_df["dep_city"] == "Unknown").sum())
        unmapped_ret = int((clean_df["ret_city"] == "Unknown").sum())
        audit_summary[year_str]["unmapped_dep_trips"] += unmapped_dep
        audit_summary[year_str]["unmapped_ret_trips"] += unmapped_ret

        # Aggregate Departures by (station_id, is_weekend, hour)
        dep_grp = clean_df.groupby(["dep_id_clean", "dep_is_weekend", "dep_hour"]).size().reset_index(name="departures")
        dep_grp.columns = ["station_id", "is_weekend", "hour", "departures"]

        # Aggregate Returns by (station_id, is_weekend, hour)
        ret_grp = clean_df.groupby(["ret_id_clean", "ret_is_weekend", "ret_hour"]).size().reset_index(name="returns")
        ret_grp.columns = ["station_id", "is_weekend", "hour", "returns"]

        # Merge Departures & Returns
        merged_station = pd.merge(dep_grp, ret_grp, on=["station_id", "is_weekend", "hour"], how="outer").fillna(0)
        merged_station["departures"] = merged_station["departures"].astype(int)
        merged_station["returns"] = merged_station["returns"].astype(int)
        merged_station["net_flow"] = merged_station["returns"] - merged_station["departures"]
        merged_station["year"] = year
        merged_station["month"] = month

        # Count active calendar days in this month
        month_dates = pd.date_range(f"{year}-{month:02d}-01", periods=pd.Period(f"{year}-{month:02d}").days_in_month)
        n_weekdays = int((month_dates.dayofweek < 5).sum())
        n_weekends = int((month_dates.dayofweek >= 5).sum())

        merged_station["n_days"] = np.where(merged_station["is_weekend"] == 1, n_weekends, n_weekdays)
        merged_station["avg_daily_departures"] = merged_station["departures"] / merged_station["n_days"]
        merged_station["avg_daily_returns"] = merged_station["returns"] / merged_station["n_days"]

        station_monthly_records.append(merged_station)

        # Aggregate City Hourly
        dep_city = clean_df.groupby(["dep_city", "dep_is_weekend", "dep_hour"]).size().reset_index(name="departures")
        dep_city.columns = ["city", "is_weekend", "hour", "departures"]
        ret_city = clean_df.groupby(["ret_city", "ret_is_weekend", "ret_hour"]).size().reset_index(name="returns")
        ret_city.columns = ["city", "is_weekend", "hour", "returns"]

        merged_city = pd.merge(dep_city, ret_city, on=["city", "is_weekend", "hour"], how="outer").fillna(0)
        merged_city["departures"] = merged_city["departures"].astype(int)
        merged_city["returns"] = merged_city["returns"].astype(int)
        merged_city["net_flow"] = merged_city["returns"] - merged_city["departures"]
        merged_city["year"] = year
        merged_city["month"] = month
        merged_city["n_days"] = np.where(merged_city["is_weekend"] == 1, n_weekends, n_weekdays)
        merged_city["avg_daily_departures"] = merged_city["departures"] / merged_city["n_days"]
        merged_city["avg_daily_returns"] = merged_city["returns"] / merged_city["n_days"]

        city_hourly_records.append(merged_city)

        print(f"Processed {fname} in {time.time()-t0:.2f}s (Clean: {len(clean_df):,}, Midnight crossings: {midnight_count:,})")

    # 3. Concatenate and Attach Station Metadata
    full_station_df = pd.concat(station_monthly_records, ignore_index=True)
    full_station_df = pd.merge(full_station_df, st_map, on="station_id", how="left")
    full_station_df["station_name"] = full_station_df["station_name"].fillna("(Unmapped station)")
    full_station_df["city"] = full_station_df["city"].fillna("Unknown")

    out_station_path = os.path.join(processed_dir, "station_intraday_monthly.csv")
    full_station_df.to_csv(out_station_path, index=False)
    print(f"Saved {out_station_path}: {len(full_station_df):,} rows ({os.path.getsize(out_station_path)/(1024*1024):.1f} MB).")

    # 4. Concatenate City Hourly
    full_city_df = pd.concat(city_hourly_records, ignore_index=True)
    out_city_path = os.path.join(processed_dir, "city_hourly_summary.csv")
    full_city_df.to_csv(out_city_path, index=False)
    print(f"Saved {out_city_path}: {len(full_city_df):,} rows.")

    # 5. Save Quality Audit Summary
    out_audit_path = os.path.join(processed_dir, "intraday_audit_metrics.json")
    with open(out_audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"Saved {out_audit_path}.")
    print(f"Intraday aggregation completed in {time.time()-t_start:.2f}s.")
    return True


if __name__ == "__main__":
    run_intraday_aggregation()
