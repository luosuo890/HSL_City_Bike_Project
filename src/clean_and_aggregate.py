"""
Data Processing and Aggregation Pipeline for HSL City Bike Project.
Cleans raw trips and produces the station-month analytical table with coordinates.
"""

import os
import glob
import re
import pandas as pd
import numpy as np


def clean_trip_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Apply data quality cleaning rules to raw HSL trip records.

    Cleaning rules:
    1. Duration: 10 seconds <= Duration <= 86,400 seconds (24 hours)
    2. Distance: Covered distance >= 10 meters
    3. Speed: Average speed (distance / duration) <= 10.0 m/s (36 km/h)
    4. Non-null: Valid timestamps and station IDs
    5. Chronology: Return timestamp >= Departure timestamp
    """
    total_raw = len(df)
    stats = {"total_raw": total_raw}

    # Standardize column names (strip whitespace and BOM)
    df.columns = [col.strip().replace("\ufeff", "") for col in df.columns]

    # Required column mapping
    col_dep_time = "Departure"
    col_ret_time = "Return"
    col_dep_id = "Departure station id"
    col_dep_name = "Departure station name"
    col_ret_id = "Return station id"
    col_ret_name = "Return station name"
    col_dist = "Covered distance (m)"
    col_dur = "Duration (sec.)"

    # Drop missing required columns
    df = df.dropna(subset=[col_dep_time, col_ret_time, col_dep_id, col_ret_id, col_dist, col_dur]).copy()
    stats["after_null_drop"] = len(df)

    # Convert numeric fields
    df[col_dist] = pd.to_numeric(df[col_dist], errors="coerce")
    df[col_dur] = pd.to_numeric(df[col_dur], errors="coerce")
    df = df.dropna(subset=[col_dist, col_dur]).copy()

    # Normalize station IDs to integer
    def parse_station_id(val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return np.nan

    df["dep_id_clean"] = df[col_dep_id].apply(parse_station_id)
    df["ret_id_clean"] = df[col_ret_id].apply(parse_station_id)
    df = df.dropna(subset=["dep_id_clean", "ret_id_clean"]).copy()
    df["dep_id_clean"] = df["dep_id_clean"].astype(int)
    df["ret_id_clean"] = df["ret_id_clean"].astype(int)
    stats["after_id_parsing"] = len(df)

    # Rule 1: Duration bounds (10s to 24h)
    valid_dur = (df[col_dur] >= 10) & (df[col_dur] <= 86400)

    # Rule 2: Distance bounds (>= 10m)
    valid_dist = df[col_dist] >= 10

    # Rule 3: Speed bound (<= 10 m/s = 36 km/h)
    speed_ms = df[col_dist] / df[col_dur].replace(0, np.nan)
    valid_speed = speed_ms <= 10.0

    # Rule 4: Chronology
    valid_time = df[col_ret_time] >= df[col_dep_time]

    clean_mask = valid_dur & valid_dist & valid_speed & valid_time
    df_clean = df[clean_mask].copy()

    stats["total_clean"] = len(df_clean)
    stats["filtered_count"] = total_raw - len(df_clean)
    stats["retention_rate_pct"] = round((len(df_clean) / total_raw) * 100, 2) if total_raw > 0 else 0.0

    return df_clean, stats


def aggregate_monthly_trips(
    df_clean: pd.DataFrame, year_month: str, stations_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Aggregate cleaned trips by station for a specific month.
    Computes departures, returns, net_flow, and merges station coordinates.
    """
    col_dist = "Covered distance (m)"
    col_dur = "Duration (sec.)"

    # 1. Departures aggregation
    dep_agg = (
        df_clean.groupby("dep_id_clean")
        .agg(
            departures=("dep_id_clean", "count"),
            total_distance_m=(col_dist, "sum"),
            total_duration_sec=(col_dur, "sum"),
        )
        .reset_index()
        .rename(columns={"dep_id_clean": "station_id"})
    )

    # 2. Returns aggregation
    ret_agg = (
        df_clean.groupby("ret_id_clean")
        .agg(returns=("ret_id_clean", "count"))
        .reset_index()
        .rename(columns={"ret_id_clean": "station_id"})
    )

    # 3. Outer merge to capture all active stations in departures or returns
    merged = pd.merge(dep_agg, ret_agg, on="station_id", how="outer")
    merged["year_month"] = year_month
    merged["departures"] = merged["departures"].fillna(0).astype(int)
    merged["returns"] = merged["returns"].fillna(0).astype(int)
    merged["total_trips"] = merged["departures"] + merged["returns"]
    merged["net_flow"] = merged["returns"] - merged["departures"]

    # Calculate average trip distance and duration for departures
    merged["avg_distance_m"] = np.where(
        merged["departures"] > 0,
        (merged["total_distance_m"] / merged["departures"]).round(1),
        0.0,
    )
    merged["avg_duration_sec"] = np.where(
        merged["departures"] > 0,
        (merged["total_duration_sec"] / merged["departures"]).round(1),
        0.0,
    )

    merged = merged.drop(columns=["total_distance_m", "total_duration_sec"])

    # 4. Merge station coordinates and metadata if available
    if stations_df is not None and not stations_df.empty:
        merged = pd.merge(merged, stations_df, on="station_id", how="left")

    # Column ordering
    ordered_cols = [
        "year_month",
        "station_id",
        "station_name",
        "city",
        "capacity",
        "latitude",
        "longitude",
        "departures",
        "returns",
        "net_flow",
        "total_trips",
        "avg_distance_m",
        "avg_duration_sec",
    ]
    existing_cols = [c for c in ordered_cols if c in merged.columns]
    extra_cols = [c for c in merged.columns if c not in existing_cols]
    merged = merged[existing_cols + extra_cols]

    return merged.sort_values(["year_month", "station_id"]).reset_index(drop=True)


def load_and_aggregate_weather(raw_dir: str, year: int | list[int] = None) -> pd.DataFrame:
    """
    Load raw FMI daily weather observations from data/raw/weather_daily_*.csv,
    validate field-by-field completeness, process precipitation and temperatures,
    and aggregate into a monthly weather table.

    FMI Data Handling Specifications:
    - Timezone: Raw timestamps in UTC are converted to local Finnish time ('Europe/Helsinki', EEST/EET).
    - Precipitation (-1.0): Official FMI standard defines -1.0 as 'ei ole satanut' (no precipitation / dry).
      Trace precipitation (<0.1 mm) is represented by 0.0. Values of -1.0 are converted to 0.0 mm.
      True missing values are represented as NaN and preserved.
    - Rainy Days: Count of days with daily precipitation >= 1.0 mm (standard meteorological rain day).
    - Field-by-field Coverage: Independently checks completeness of tday, tmin, tmax, rrday, and snow.
    """
    pattern = os.path.join(raw_dir, "weather_daily_*.csv")
    weather_files = glob.glob(pattern)
    if year is not None:
        if isinstance(year, (int, str)):
            year_list = [int(year)]
        else:
            year_list = [int(y) for y in year]
        weather_files = [
            f for f in weather_files
            if any(f"weather_daily_{y}.csv" in f for y in year_list)
        ]

    if not weather_files:
        print("  [Warning] No raw weather files (weather_daily_*.csv) found. Skipping weather aggregation.")
        return None

    dfs = [pd.read_csv(f, encoding="utf-8") for f in weather_files]
    df_raw = pd.concat(dfs, ignore_index=True)

    # Convert timestamps to local Finnish time
    df_raw["dt_utc"] = pd.to_datetime(df_raw["time_utc"], utc=True)
    df_raw["dt_local"] = df_raw["dt_utc"].dt.tz_convert("Europe/Helsinki")
    df_raw["year_month"] = df_raw["dt_local"].dt.strftime("%Y-%m")

    # Pivot parameters
    pivoted = df_raw.pivot_table(
        index=["year_month", "city", "fmisid", "station_name", "dt_local"],
        columns="parameter",
        values="value",
        aggfunc="first",
    ).reset_index()

    # Convert parameter columns to numeric
    for col in ["tday", "tmin", "tmax", "rrday", "snow"]:
        if col in pivoted.columns:
            pivoted[col] = pd.to_numeric(pivoted[col], errors="coerce")

    # Field-by-field completeness validation
    print("\nValidating FMI daily observation coverage by field:")
    for param in ["tday", "tmin", "tmax", "rrday", "snow"]:
        if param in pivoted.columns:
            for city in sorted(pivoted["city"].unique()):
                city_subset = pivoted[pivoted["city"] == city]
                non_null = city_subset[param].notna().sum()
                total = len(city_subset)
                pct = (non_null / total * 100) if total > 0 else 0
                print(f"  - [{city}] Field '{param}': {non_null}/{total} observations ({pct:.1f}%)")
        else:
            print(f"  [Warning] Expected field '{param}' not found in weather observations.")

    # Official FMI precipitation handling:
    # -1.0 = no rain (0.0 mm), 0.0 = trace (<0.1 mm), >0 = measured mm, NaN = missing
    if "rrday" in pivoted.columns:
        pivoted["precip_mm"] = np.where(pivoted["rrday"] < 0, 0.0, pivoted["rrday"])
        pivoted["is_rainy_day"] = pivoted["precip_mm"] >= 1.0
    else:
        pivoted["precip_mm"] = np.nan
        pivoted["is_rainy_day"] = False

    # Monthly aggregation
    monthly = (
        pivoted.groupby(["year_month", "city", "fmisid"])
        .agg(
            avg_temperature_c=("tday", lambda x: round(x.mean(), 1) if x.notna().any() else np.nan),
            min_temperature_c=("tmin", lambda x: round(x.min(), 1) if x.notna().any() else np.nan),
            max_temperature_c=("tmax", lambda x: round(x.max(), 1) if x.notna().any() else np.nan),
            total_precipitation_mm=("precip_mm", lambda x: round(x.sum(), 1) if x.notna().any() else np.nan),
            rainy_days_count=("is_rainy_day", lambda x: int(x.sum()) if x.notna().any() else 0),
        )
        .reset_index()
        .rename(columns={"fmisid": "weather_station_id"})
    )

    print(f"  Aggregated {len(monthly)} monthly weather records across {monthly['year_month'].nunique()} months.")
    return monthly


def process_all_data(raw_dir: str, processed_dir: str, year: int | list[int] = None) -> pd.DataFrame:
    """
    Find monthly CSVs in raw_dir, clean trips, aggregate by station-month,
    merge weather data and station coordinates, and save result to processed_dir/station_month.csv.
    If specific years are processed, existing data for other years in station_month.csv is safely preserved.
    """
    os.makedirs(processed_dir, exist_ok=True)

    # 1. Load stations metadata
    stations_path = os.path.join(raw_dir, "stations.csv")
    stations_df = None
    if os.path.exists(stations_path):
        print(f"Loading station metadata from {stations_path} ...")
        st_raw = pd.read_csv(stations_path, encoding="utf-8")
        st_raw["station_id"] = pd.to_numeric(st_raw["station_id"], errors="coerce").astype("Int64")
        city_clean = st_raw["city"].fillna("Helsinki").astype(str).str.strip()
        city_clean = city_clean.replace("", "Helsinki")
        stations_df = pd.DataFrame(
            {
                "station_id": st_raw["station_id"],
                "station_name": st_raw["name"].fillna(st_raw["name_fi"]),
                "city": city_clean,
                "capacity": pd.to_numeric(st_raw["capacity"], errors="coerce"),
                "latitude": pd.to_numeric(st_raw["latitude"], errors="coerce"),
                "longitude": pd.to_numeric(st_raw["longitude"], errors="coerce"),
            }
        ).dropna(subset=["station_id"])
        stations_df["station_id"] = stations_df["station_id"].astype(int)
        print(f"  Loaded {len(stations_df)} station coordinates.")
    else:
        print("  [Warning] stations.csv not found. Coordinates will not be merged.")

    # 2. Find all monthly trip CSVs
    pattern = os.path.join(raw_dir, "*.csv")
    csv_files = [
        f
        for f in glob.glob(pattern)
        if os.path.basename(f) != "stations.csv" and not os.path.basename(f).startswith("weather_")
    ]
    csv_files = [f for f in csv_files if re.match(r"^\d{4}-\d{2}\.csv$", os.path.basename(f))]

    if year is not None:
        if isinstance(year, (int, str)):
            year_list = [int(year)]
        else:
            year_list = [int(y) for y in year]
        csv_files = [
            f for f in csv_files
            if any(os.path.basename(f).startswith(f"{y}-") for y in year_list)
        ]

    csv_files = sorted(csv_files)
    if not csv_files:
        raise FileNotFoundError(f"No monthly trip CSV files found in {raw_dir}")

    print(f"\nProcessing {len(csv_files)} monthly trip files...")
    monthly_aggregates = []
    overall_stats = []

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        year_month = filename.replace(".csv", "")
        print(f"\nProcessing {year_month} ({filename})...")

        df_raw = pd.read_csv(file_path, low_memory=False, encoding="utf-8")
        df_clean, stats = clean_trip_dataframe(df_raw)
        stats["year_month"] = year_month
        overall_stats.append(stats)

        print(
            f"  Raw: {stats['total_raw']:,} trips | Clean: {stats['total_clean']:,} trips "
            f"| Filtered: {stats['filtered_count']:,} ({100 - stats['retention_rate_pct']:.1f}%)"
        )

        monthly_agg = aggregate_monthly_trips(df_clean, year_month, stations_df)
        monthly_aggregates.append(monthly_agg)

    final_df = pd.concat(monthly_aggregates, ignore_index=True)

    # 3. Load and integrate FMI weather data
    print("\nIntegrating FMI weather observations...")
    weather_df = load_and_aggregate_weather(raw_dir, year)
    if weather_df is not None and not weather_df.empty:
        orig_len = len(final_df)
        # Left join on year_month and city.
        # Stations with unmapped city (NaN) naturally retain NaN for weather metrics
        # to avoid false precision and unwarranted assumptions.
        final_df = pd.merge(
            final_df,
            weather_df,
            on=["year_month", "city"],
            how="left",
        )

        # Verify integrity
        assert len(final_df) == orig_len, f"Row count changed after weather join: {len(final_df)} vs {orig_len}"
        assert final_df.duplicated(subset=["year_month", "station_id"]).sum() == 0, "Duplicate station-month keys found"
        print(f"  [Success] Weather observations successfully merged. Row count preserved: {len(final_df):,}")

    # Reorder columns
    ordered_cols = [
        "year_month",
        "station_id",
        "station_name",
        "city",
        "capacity",
        "latitude",
        "longitude",
        "departures",
        "returns",
        "net_flow",
        "total_trips",
        "avg_distance_m",
        "avg_duration_sec",
        "weather_station_id",
        "avg_temperature_c",
        "min_temperature_c",
        "max_temperature_c",
        "total_precipitation_mm",
        "rainy_days_count",
    ]
    existing_cols = [c for c in ordered_cols if c in final_df.columns]
    extra_cols = [c for c in final_df.columns if c not in existing_cols]
    final_df = final_df[existing_cols + extra_cols]

    output_file = os.path.join(processed_dir, "station_month.csv")

    # If processing a subset of years and output_file already exists, preserve records from other years
    if os.path.exists(output_file) and year is not None:
        try:
            existing_df = pd.read_csv(output_file)
            new_months = set(final_df["year_month"].unique())
            other_existing = existing_df[~existing_df["year_month"].isin(new_months)]
            if not other_existing.empty:
                print(
                    f"  Preserving {len(other_existing):,} existing records for months "
                    f"{sorted(other_existing['year_month'].unique())} from {os.path.basename(output_file)}"
                )
                final_df = pd.concat([other_existing, final_df], ignore_index=True)
                final_df = final_df.sort_values(["year_month", "station_id"]).reset_index(drop=True)
        except Exception as e:
            print(f"  [Warning] Could not merge with existing {output_file}: {e}")

    assert final_df.duplicated(subset=["year_month", "station_id"]).sum() == 0, "Duplicate station-month keys found in final table"
    final_df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"\n[Success] Final station-month table saved to {output_file}")
    print(f"Total station-month rows: {len(final_df):,} across {final_df['year_month'].nunique()} months.")

    return final_df


if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.dirname(__file__))
    raw = os.path.join(project_dir, "data", "raw")
    proc = os.path.join(project_dir, "data", "processed")
    process_all_data(raw, proc)

