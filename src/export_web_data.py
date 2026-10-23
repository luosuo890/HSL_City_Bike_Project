"""
Data Export Pipeline for GitHub Pages Static Deployment.
Generates lightweight, derived JSON data files in docs/data/ from verified project data.
Strictly adheres to:
- Real project data only (no mock or fabricated values).
- No raw journey CSVs exposed to web clients.
- Unmapped stations preserved in audit records without fake coordinates.
- Exact reproduction of verified model logic and hyperparameters.
- Explicit methodological boundaries and guardrails in metadata.
"""

import os
import sys
import glob
import json
import time
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.clean_and_aggregate import clean_trip_dataframe


def export_stations_data(station_month_path, out_dir):
    """
    Exports data_stations.json:
    Contains all 454 mapped stations with WGS84 coordinates, dock capacity,
    and monthly ridership (departures, returns, net_flow) across 14 months (2024-2025).
    Audits and preserves 7 unmapped stations in a separate unmapped array without fake coordinates.
    """
    print("Exporting data_stations.json...")
    df = pd.read_csv(station_month_path)

    months_list = sorted(df["year_month"].unique().tolist())

    # Identify mapped vs unmapped stations
    unmapped_mask = df["latitude"].isna() | df["longitude"].isna()
    mapped_df = df[~unmapped_mask].copy()
    unmapped_df = df[unmapped_mask].copy()

    stations_dict = {}
    for _, row in mapped_df.iterrows():
        sid = int(row["station_id"])
        ym = str(row["year_month"])
        dep = int(row["departures"])
        ret = int(row["returns"])
        net = int(row["net_flow"])

        if sid not in stations_dict:
            stations_dict[sid] = {
                "id": sid,
                "name": str(row["station_name"]),
                "city": str(row["city"]),
                "lat": round(float(row["latitude"]), 6),
                "lon": round(float(row["longitude"]), 6),
                "cap": int(row["capacity"]) if pd.notna(row["capacity"]) else None,
                "months": {},
                "totals": {
                    "2024": {"dep": 0, "ret": 0, "net": 0},
                    "2025": {"dep": 0, "ret": 0, "net": 0},
                    "all": {"dep": 0, "ret": 0, "net": 0}
                }
            }

        stations_dict[sid]["months"][ym] = [dep, ret, net]
        yr = ym[:4]
        if yr in ["2024", "2025"]:
            stations_dict[sid]["totals"][yr]["dep"] += dep
            stations_dict[sid]["totals"][yr]["ret"] += ret
            stations_dict[sid]["totals"][yr]["net"] += net
        stations_dict[sid]["totals"]["all"]["dep"] += dep
        stations_dict[sid]["totals"]["all"]["ret"] += ret
        stations_dict[sid]["totals"]["all"]["net"] += net

    # Process unmapped stations
    unmapped_dict = {}
    for _, row in unmapped_df.iterrows():
        sid = int(row["station_id"])
        ym = str(row["year_month"])
        dep = int(row["departures"])
        ret = int(row["returns"])
        net = int(row["net_flow"])

        if sid not in unmapped_dict:
            unmapped_dict[sid] = {
                "id": sid,
                "name": str(row["station_name"]) if pd.notna(row["station_name"]) else str(sid),
                "city": "Unknown",
                "lat": None,
                "lon": None,
                "cap": None,
                "months": {},
                "totals": {
                    "2024": {"dep": 0, "ret": 0, "net": 0},
                    "2025": {"dep": 0, "ret": 0, "net": 0},
                    "all": {"dep": 0, "ret": 0, "net": 0}
                },
                "audit_note": "Unmapped station without coordinates in official HSL ArcGIS layer."
            }

        unmapped_dict[sid]["months"][ym] = [dep, ret, net]
        yr = ym[:4]
        if yr in ["2024", "2025"]:
            unmapped_dict[sid]["totals"][yr]["dep"] += dep
            unmapped_dict[sid]["totals"][yr]["ret"] += ret
            unmapped_dict[sid]["totals"][yr]["net"] += net
        unmapped_dict[sid]["totals"]["all"]["dep"] += dep
        unmapped_dict[sid]["totals"]["all"]["ret"] += ret
        unmapped_dict[sid]["totals"]["all"]["net"] += net

    mapped_list = sorted(stations_dict.values(), key=lambda s: s["id"])
    unmapped_list = sorted(unmapped_dict.values(), key=lambda s: s["id"])

    payload = {
        "meta": {
            "description": "Station metadata and monthly ridership profiles (2024-2025)",
            "unit": "completed journeys per station-month",
            "net_flow_definition": "returns minus departures (directional passenger drift, not real-time inventory)",
            "mapped_stations_count": len(mapped_list),
            "unmapped_stations_count": len(unmapped_list),
            "total_stations_count": len(mapped_list) + len(unmapped_list),
            "months_list": months_list
        },
        "stations": mapped_list,
        "unmapped": unmapped_list
    }

    out_file = os.path.join(out_dir, "data_stations.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_file) / 1024
    print(f" -> Generated {out_file} ({size_kb:.1f} KB; {len(mapped_list)} mapped, {len(unmapped_list)} unmapped)")
    return payload


def export_hourly_city_data(city_hourly_summary_path, out_dir):
    """
    Exports data_hourly_city.json:
    Pre-aggregated hourly profiles for Helsinki, Espoo, and Combined across:
    - Overall 2024, Overall 2025, and 2-Year Combined
    - Weekday (is_weekend=0) vs. Weekend (is_weekend=1)
    - Monthly breakdowns (months 4-10 for 2024 and 2025)
    """
    print("Exporting data_hourly_city.json...")
    df = pd.read_csv(city_hourly_summary_path)

    cities = ["Helsinki", "Espoo", "All"]
    day_types = ["weekday", "weekend"]

    # Build weighted helper functions
    def aggregate_hourly_curves(sub_df):
        """Aggregates departures and returns across days to compute exact weighted averages."""
        grp = sub_df.groupby("hour").agg(
            departures=("departures", "sum"),
            returns=("returns", "sum"),
            net_flow=("net_flow", "sum"),
            n_days=("n_days", "sum")
        ).reset_index()

        points = []
        for _, r in grp.iterrows():
            nd = r["n_days"] if r["n_days"] > 0 else 1
            points.append({
                "hour": int(r["hour"]),
                "avg_dep": round(float(r["departures"] / nd), 2),
                "avg_ret": round(float(r["returns"] / nd), 2),
                "net_flow": int(r["net_flow"]),
                "tot_dep": int(r["departures"]),
                "tot_ret": int(r["returns"])
            })
        # Ensure sorted by hour
        return sorted(points, key=lambda p: p["hour"])

    result_data = {
        "Helsinki": {"weekday": {}, "weekend": {}},
        "Espoo": {"weekday": {}, "weekend": {}},
        "All": {"weekday": {}, "weekend": {}}
    }

    months_list = sorted([f"{y}-{m:02d}" for y in [2024, 2025] for m in range(4, 11)])

    for is_wknd in [0, 1]:
        dt_key = "weekend" if is_wknd == 1 else "weekday"
        df_dt = df[df["is_weekend"] == is_wknd]

        for city_name in ["Helsinki", "Espoo"]:
            df_c = df_dt[df_dt["city"] == city_name]
            result_data[city_name][dt_key]["overall_all"] = aggregate_hourly_curves(df_c)
            result_data[city_name][dt_key]["overall_2024"] = aggregate_hourly_curves(df_c[df_c["year"] == 2024])
            result_data[city_name][dt_key]["overall_2025"] = aggregate_hourly_curves(df_c[df_c["year"] == 2025])

            # Monthly curves
            for ym in months_list:
                yr, mo = int(ym[:4]), int(ym[5:7])
                m_sub = df_c[(df_c["year"] == yr) & (df_c["month"] == mo)]
                if len(m_sub) > 0:
                    result_data[city_name][dt_key][ym] = aggregate_hourly_curves(m_sub)

        # "All" combined (Helsinki + Espoo)
        df_all_cities = df_dt[df_dt["city"].isin(["Helsinki", "Espoo"])]
        result_data["All"][dt_key]["overall_all"] = aggregate_hourly_curves(df_all_cities)
        result_data["All"][dt_key]["overall_2024"] = aggregate_hourly_curves(df_all_cities[df_all_cities["year"] == 2024])
        result_data["All"][dt_key]["overall_2025"] = aggregate_hourly_curves(df_all_cities[df_all_cities["year"] == 2025])

        for ym in months_list:
            yr, mo = int(ym[:4]), int(ym[5:7])
            m_sub = df_all_cities[(df_all_cities["year"] == yr) & (df_all_cities["month"] == mo)]
            if len(m_sub) > 0:
                result_data["All"][dt_key][ym] = aggregate_hourly_curves(m_sub)

    payload = {
        "meta": {
            "description": "Pre-aggregated hourly trip profiles by city and day type (2024-2025)",
            "timezone": "Europe/Helsinki local time",
            "hours": list(range(24)),
            "months": months_list,
            "metric_units": {
                "avg_dep": "average departures per operating day",
                "avg_ret": "average returns per operating day",
                "net_flow": "cumulative returns minus departures"
            }
        },
        "profiles": result_data
    }

    out_file = os.path.join(out_dir, "data_hourly_city.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_file) / 1024
    print(f" -> Generated {out_file} ({size_kb:.1f} KB)")
    return payload


def export_commute_peaks_data(station_intraday_path, audit_metrics_path, out_dir):
    """
    Exports data_commute_peaks.json:
    Evaluates commuter tidal reversals across morning rush (07:00-09:00) vs evening rush (16:00-18:00)
    for top commuter hubs on weekdays (is_weekend=0), matching Figure 6.
    Includes intraday data quality audit metrics.
    """
    print("Exporting data_commute_peaks.json...")
    df_intra = pd.read_csv(station_intraday_path)

    # Filter weekdays
    wd = df_intra[df_intra["is_weekend"] == 0].copy()

    # Morning Peak (07:00 - 09:00, hours 7 & 8)
    morn = (
        wd[wd["hour"].isin([7, 8])]
        .groupby(["station_id", "station_name", "city"])
        .agg(
            morn_dep=("departures", "sum"),
            morn_ret=("returns", "sum"),
            morn_net=("net_flow", "sum")
        )
        .reset_index()
    )

    # Evening Peak (16:00 - 18:00, hours 16 & 17)
    eve = (
        wd[wd["hour"].isin([16, 17])]
        .groupby(["station_id", "station_name", "city"])
        .agg(
            eve_dep=("departures", "sum"),
            eve_ret=("returns", "sum"),
            eve_net=("net_flow", "sum")
        )
        .reset_index()
    )

    merged = pd.merge(morn, eve, on=["station_id", "station_name", "city"])
    merged["total_peak_trips"] = merged["morn_dep"] + merged["morn_ret"] + merged["eve_dep"] + merged["eve_ret"]
    merged["tidal_swing"] = (merged["morn_net"] - merged["eve_net"]).abs()

    # Top 10 High-Swing Hubs (matching Figure 6 Panel A)
    top10_swing = merged.sort_values("tidal_swing", ascending=False).head(10).copy()
    top10_list = []
    for _, r in top10_swing.iterrows():
        top10_list.append({
            "station_id": int(r["station_id"]),
            "station_name": str(r["station_name"]),
            "city": str(r["city"]),
            "morn_net": int(r["morn_net"]),
            "eve_net": int(r["eve_net"]),
            "tidal_swing": int(r["tidal_swing"])
        })

    # Top 120 Busiest Commuter Stations (matching Figure 6 Panel B scatter plot)
    top120_stations = merged.sort_values("total_peak_trips", ascending=False).head(120).copy()
    stations_list = []
    for _, r in top120_stations.iterrows():
        stations_list.append({
            "station_id": int(r["station_id"]),
            "station_name": str(r["station_name"]),
            "city": str(r["city"]),
            "morn_dep": int(r["morn_dep"]),
            "morn_ret": int(r["morn_ret"]),
            "morn_net": int(r["morn_net"]),
            "eve_dep": int(r["eve_dep"]),
            "eve_ret": int(r["eve_ret"]),
            "eve_net": int(r["eve_net"]),
            "total_peak_trips": int(r["total_peak_trips"]),
            "tidal_swing": int(r["tidal_swing"])
        })

    # Load intraday audit metrics
    audit_metrics = {}
    if os.path.exists(audit_metrics_path):
        with open(audit_metrics_path, "r", encoding="utf-8") as f:
            audit_metrics = json.load(f)

    payload = {
        "meta": {
            "description": "Morning (07:00-09:00) vs Evening (16:00-18:00) peak rush commuter dynamics (weekdays 2024-2025)",
            "morning_window": "07:00 - 09:00 (hours 7 and 8)",
            "evening_window": "16:00 - 18:00 (hours 16 and 17)",
            "evening_surge_notes": {
                "Helsinki": "+78.4% evening trip surge relative to morning peak",
                "Espoo": "+95.9% evening trip surge relative to morning peak"
            },
            "quadrant_definitions": {
                "Quadrant_II": "Residential Feeder (Morning Deficit, Evening Surplus; e.g. Sompasaari)",
                "Quadrant_IV": "Workplace Center (Morning Surplus, Evening Deficit; e.g. Salmisaarenranta)",
                "Quadrant_III": "Continuous Deficit Sink (All-day net outflow; e.g. Pasila rail hub)"
            }
        },
        "audit": audit_metrics,
        "top_tidal_swing": top10_list,
        "commuter_hubs": stations_list
    }

    out_file = os.path.join(out_dir, "data_commute_peaks.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_file) / 1024
    print(f" -> Generated {out_file} ({size_kb:.1f} KB; {len(top10_list)} top swings, {len(stations_list)} commuter hubs)")
    return payload


def export_daily_weather_data(raw_dir, out_dir):
    """
    Exports data_daily_weather.json:
    Aggregates cleaned 2024 and 2025 raw journey CSVs by (date, city),
    then merges with FMI daily meteorological ground observations from Kaisaniemi & Tapiola.
    Strictly follows FMI conventions: rrday < 0 -> 0.0 mm; is_rainy_day -> precip_mm >= 1.0.
    """
    print("Exporting data_daily_weather.json (aggregating raw trips and FMI weather)...")

    # 1. Load Station Metadata for City Mapping
    stations_path = os.path.join(raw_dir, "stations.csv")
    st_df = pd.read_csv(stations_path)
    city_clean = st_df["city"].fillna("Helsinki").astype(str).str.strip().replace("", "Helsinki")
    st_map = pd.Series(city_clean.values, index=pd.to_numeric(st_df["station_id"], errors="coerce").astype(int)).to_dict()

    # 2. Process Raw Journey CSVs
    trip_files = sorted(glob.glob(os.path.join(raw_dir, "2024-*.csv")) + glob.glob(os.path.join(raw_dir, "2025-*.csv")))
    print(f"  Processing {len(trip_files)} raw journey files...")

    daily_dep_list, daily_ret_list = [], []
    for f in trip_files:
        df_raw = pd.read_csv(f, low_memory=False)
        clean_df, _ = clean_trip_dataframe(df_raw)
        clean_df["dep_date"] = clean_df["Departure"].str[:10]
        clean_df["ret_date"] = clean_df["Return"].str[:10]
        clean_df["dep_city"] = clean_df["dep_id_clean"].map(st_map).fillna("Unknown")
        clean_df["ret_city"] = clean_df["ret_id_clean"].map(st_map).fillna("Unknown")

        d_grp = clean_df.groupby(["dep_date", "dep_city"]).size().reset_index(name="departures")
        d_grp.columns = ["date", "city", "departures"]
        daily_dep_list.append(d_grp)

        r_grp = clean_df.groupby(["ret_date", "ret_city"]).size().reset_index(name="returns")
        r_grp.columns = ["date", "city", "returns"]
        daily_ret_list.append(r_grp)

    all_deps = pd.concat(daily_dep_list, ignore_index=True).groupby(["date", "city"])["departures"].sum().reset_index()
    all_rets = pd.concat(daily_ret_list, ignore_index=True).groupby(["date", "city"])["returns"].sum().reset_index()
    daily_trips = pd.merge(all_deps, all_rets, on=["date", "city"], how="outer").fillna(0)
    daily_trips["departures"] = daily_trips["departures"].astype(int)
    daily_trips["returns"] = daily_trips["returns"].astype(int)
    daily_trips["net_flow"] = daily_trips["returns"] - daily_trips["departures"]

    # 3. Load & Pivot FMI Daily Weather
    weather_24 = pd.read_csv(os.path.join(raw_dir, "weather_daily_2024.csv"))
    weather_25 = pd.read_csv(os.path.join(raw_dir, "weather_daily_2025.csv"))
    weather_raw = pd.concat([weather_24, weather_25], ignore_index=True)
    weather_raw["date"] = weather_raw["time_utc"].str[:10]

    weather_pivoted = weather_raw.pivot_table(
        index=["date", "city"],
        columns="parameter",
        values="value",
        aggfunc="first"
    ).reset_index()

    for col in ["tday", "tmin", "tmax", "rrday", "snow"]:
        if col in weather_pivoted.columns:
            weather_pivoted[col] = pd.to_numeric(weather_pivoted[col], errors="coerce")

    # Apply FMI precipitation conventions
    weather_pivoted["precip_mm"] = np.where(weather_pivoted["rrday"] < 0, 0.0, weather_pivoted["rrday"])
    weather_pivoted["is_rainy_day"] = (weather_pivoted["precip_mm"] >= 1.0).astype(int)
    weather_pivoted["snow_cm"] = np.where(weather_pivoted["snow"] < 0, 0.0, weather_pivoted["snow"])

    # 4. Merge Trips with Weather
    # Restrict to valid operating season days: April 1 to October 31 of 2024 and 2025
    daily_merged = pd.merge(daily_trips, weather_pivoted, on=["date", "city"], how="left")
    daily_merged["date_dt"] = pd.to_datetime(daily_merged["date"])

    # Filter to main cycling seasons
    m_24 = (daily_merged["date"] >= "2024-04-01") & (daily_merged["date"] <= "2024-10-31")
    m_25 = (daily_merged["date"] >= "2025-04-01") & (daily_merged["date"] <= "2025-10-31")
    season_df = daily_merged[m_24 | m_25].copy()

    records = []
    # Retain records for Helsinki and Espoo
    for _, r in season_df[season_df["city"].isin(["Helsinki", "Espoo"])].sort_values(["date", "city"]).iterrows():
        dt = r["date_dt"]
        records.append({
            "date": str(r["date"]),
            "year": int(dt.year),
            "month": int(dt.month),
            "city": str(r["city"]),
            "is_weekend": int(dt.dayofweek >= 5),
            "day_name": dt.day_name(),
            "dep": int(r["departures"]),
            "ret": int(r["returns"]),
            "net": int(r["net_flow"]),
            "tday": round(float(r["tday"]), 1) if pd.notna(r["tday"]) else None,
            "tmin": round(float(r["tmin"]), 1) if pd.notna(r["tmin"]) else None,
            "tmax": round(float(r["tmax"]), 1) if pd.notna(r["tmax"]) else None,
            "precip": round(float(r["precip_mm"]), 1) if pd.notna(r["precip_mm"]) else 0.0,
            "is_rainy": int(r["is_rainy_day"]) if pd.notna(r["is_rainy_day"]) else 0,
            "snow": round(float(r["snow_cm"]), 1) if pd.notna(r["snow_cm"]) else 0.0
        })

    # Summary of unmapped city daily totals
    unmapped_sub = season_df[season_df["city"] == "Unknown"]
    unmapped_dep_total = int(unmapped_sub["departures"].sum()) if len(unmapped_sub) > 0 else 0
    unmapped_ret_total = int(unmapped_sub["returns"].sum()) if len(unmapped_sub) > 0 else 0
    unmapped_days = int(unmapped_sub["date"].nunique()) if len(unmapped_sub) > 0 else 0

    payload = {
        "meta": {
            "description": "Daily city-level ridership matched with FMI historical weather observations (2024-2025)",
            "stations_fmi": {
                "Helsinki": "FMISID 100971 (Helsinki Kaisaniemi)",
                "Espoo": "FMISID 874863 (Espoo Tapiola)"
            },
            "total_records": len(records),
            "calendar_days_per_city": 428,
            "season_coverage": "214 days in 2024 (Apr 1 - Oct 31), 214 days in 2025 (Apr 1 - Oct 31)",
            "methodological_guardrails": [
                "Weather features represent retrospective FMI ground observations, strictly NOT weather forecasts.",
                "Correlation with ridership (+0.74 temp, -0.25 rain) is descriptive seasonal co-movement, NOT causality.",
                "Weather features were strictly excluded from predictive model feature matrices."
            ],
            "unmapped_trips_audit": {
                "total_departures": unmapped_dep_total,
                "total_returns": unmapped_ret_total,
                "days_count": unmapped_days
            }
        },
        "daily_records": records
    }

    out_file = os.path.join(out_dir, "data_daily_weather.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_file) / 1024
    print(f" -> Generated {out_file} ({size_kb:.1f} KB; {len(records)} daily records)")
    return payload


def export_model_data(station_month_path, out_dir):
    """
    Exports:
    1. data_model_summary.json: Overall MAE/WAPE, low-usage subset, monthly WAPE breakdown, and Top-20 deficit overlap.
    2. data_model_predictions_2025.json: Exactly 2,718 test records of 2025 (months 5-10) with actual and predicted values.
    Strictly replicates notebooks/model_comparison.ipynb:
    - 2024 months 5-10 training set; lag-1 feature definition; medians imputation; alpha=10.0; max_depth=6.
    """
    print("Exporting data_model_summary.json & data_model_predictions_2025.json...")

    df = pd.read_csv(station_month_path)
    df["year"] = df["year_month"].str[:4].astype(int)
    df["month"] = df["year_month"].str[5:7].astype(int)

    # Within-season lag: shift month by +1
    df_lags = df[["year", "month", "station_id", "departures", "returns"]].copy()
    df_lags["month"] = df_lags["month"] + 1
    df_lags = df_lags.rename(columns={"departures": "lag_departures", "returns": "lag_returns"})

    df_with_lag = pd.merge(df, df_lags, on=["year", "month", "station_id"], how="left")
    df_m5_10 = df_with_lag[df_with_lag["month"].between(5, 10)].copy()

    # Training Data (2024 months 5-10)
    train_raw = df_m5_10[df_m5_10["year"] == 2024].copy()
    train_data = train_raw[train_raw["lag_departures"].notna()].copy()

    # Test Data (2025 months 5-10)
    test_raw = df_m5_10[df_m5_10["year"] == 2025].copy()
    df24_lookup = df[df["year"] == 2024][["month", "station_id", "departures", "returns"]].rename(
        columns={"departures": "base_departures", "returns": "base_returns"}
    )
    test_merged = pd.merge(test_raw, df24_lookup, on=["month", "station_id"], how="left")
    has_lag = test_merged["lag_departures"].notna()
    has_base = test_merged["base_departures"].notna()
    test_eval = test_merged[has_lag & has_base].copy()

    # Metadata Imputation using training medians
    for c in ["capacity", "latitude", "longitude"]:
        med = train_data[c].median()
        train_data[c] = train_data[c].fillna(med)
        test_eval[c] = test_eval[c].fillna(med)

    train_data["is_helsinki"] = (train_data["city"] == "Helsinki").astype(int)
    test_eval["is_helsinki"] = (test_eval["city"] == "Helsinki").astype(int)

    # One-hot month dummies (May m_5 as reference baseline)
    month_dummies_tr = pd.get_dummies(train_data["month"], prefix="m", drop_first=True, dtype=int)
    month_dummies_te = pd.get_dummies(test_eval["month"], prefix="m", drop_first=True, dtype=int)

    train_data = pd.concat([train_data, month_dummies_tr], axis=1)
    test_eval = pd.concat([test_eval, month_dummies_te], axis=1)

    base_feature_cols = ["capacity", "latitude", "longitude", "is_helsinki"] + list(month_dummies_tr.columns)
    feature_cols_dep = ["lag_departures"] + base_feature_cols
    feature_cols_ret = ["lag_returns"] + base_feature_cols

    # 1. Baseline
    test_eval["pred_dep_base"] = test_eval["base_departures"]
    test_eval["pred_ret_base"] = test_eval["base_returns"]
    test_eval["pred_net_base"] = test_eval["pred_ret_base"] - test_eval["pred_dep_base"]

    # 2. Ridge Regression (alpha=10.0)
    scaler_dep = StandardScaler()
    X_tr_dep_sc = scaler_dep.fit_transform(train_data[feature_cols_dep])
    X_te_dep_sc = scaler_dep.transform(test_eval[feature_cols_dep])
    ridge_dep = Ridge(alpha=10.0)
    ridge_dep.fit(X_tr_dep_sc, train_data["departures"])
    test_eval["pred_dep_ridge"] = np.clip(ridge_dep.predict(X_te_dep_sc), 0, None)

    scaler_ret = StandardScaler()
    X_tr_ret_sc = scaler_ret.fit_transform(train_data[feature_cols_ret])
    X_te_ret_sc = scaler_ret.transform(test_eval[feature_cols_ret])
    ridge_ret = Ridge(alpha=10.0)
    ridge_ret.fit(X_tr_ret_sc, train_data["returns"])
    test_eval["pred_ret_ridge"] = np.clip(ridge_ret.predict(X_te_ret_sc), 0, None)
    test_eval["pred_net_ridge"] = test_eval["pred_ret_ridge"] - test_eval["pred_dep_ridge"]

    # 3. Decision Tree Regressor (max_depth=6, min_samples_leaf=10, random_state=42)
    dt_dep = DecisionTreeRegressor(max_depth=6, min_samples_leaf=10, random_state=42)
    dt_dep.fit(train_data[feature_cols_dep], train_data["departures"])
    test_eval["pred_dep_dt"] = np.clip(dt_dep.predict(test_eval[feature_cols_dep]), 0, None)

    dt_ret = DecisionTreeRegressor(max_depth=6, min_samples_leaf=10, random_state=42)
    dt_ret.fit(train_data[feature_cols_ret], train_data["returns"])
    test_eval["pred_ret_dt"] = np.clip(dt_ret.predict(test_eval[feature_cols_ret]), 0, None)
    test_eval["pred_net_dt"] = test_eval["pred_ret_dt"] - test_eval["pred_dep_dt"]

    # Compute Overall Summary
    model_tags = {
        "base": "1. Same-Month Baseline (2024)",
        "ridge": "2. Ridge Regression (Lag-1)",
        "dt": "3. Decision Tree (Lag-1, max_depth=6)"
    }

    def compute_summary(sub_df):
        out = []
        yt_dep = sub_df["departures"]
        yt_ret = sub_df["returns"]
        for tag, name in model_tags.items():
            yp_dep = sub_df[f"pred_dep_{tag}"]
            yp_ret = sub_df[f"pred_ret_{tag}"]
            mae_dep = float(np.mean(np.abs(yt_dep - yp_dep)))
            wape_dep = float((np.sum(np.abs(yt_dep - yp_dep)) / np.sum(yt_dep)) * 100.0)
            rmse_dep = float(np.sqrt(np.mean((yt_dep - yp_dep) ** 2)))
            mae_ret = float(np.mean(np.abs(yt_ret - yp_ret)))
            wape_ret = float((np.sum(np.abs(yt_ret - yp_ret)) / np.sum(yt_ret)) * 100.0)
            rmse_ret = float(np.sqrt(np.mean((yt_ret - yp_ret) ** 2)))
            out.append({
                "model_id": tag,
                "model_name": name,
                "dep_mae": round(mae_dep, 2),
                "dep_wape": round(wape_dep, 2),
                "dep_rmse": round(rmse_dep, 2),
                "ret_mae": round(mae_ret, 2),
                "ret_wape": round(wape_ret, 2),
                "ret_rmse": round(rmse_ret, 2)
            })
        return out

    overall_metrics = compute_summary(test_eval)

    # Low-Usage Subset (Q1 departures <= 198 trips/month, matching notebook)
    q1_threshold = float(test_eval["departures"].quantile(0.25))
    low_usage_sub = test_eval[test_eval["departures"] <= q1_threshold].copy()
    low_usage_metrics = compute_summary(low_usage_sub)

    # Monthly Breakdown
    monthly_breakdown = []
    for m, grp in test_eval.groupby("month"):
        yt_dep = grp["departures"]
        row = {
            "month": f"2025-{m:02d}",
            "n_stations": len(grp)
        }
        for tag in ["base", "ridge", "dt"]:
            wape = float((np.sum(np.abs(yt_dep - grp[f"pred_dep_{tag}"])) / np.sum(yt_dep)) * 100.0)
            row[f"{tag}_wape"] = round(wape, 2)
        monthly_breakdown.append(row)

    # Top-20 Net Flow Overlap & Spearman Rank Correlation
    overlap_records = []
    for m, grp in test_eval.groupby("month"):
        k = 20
        actual_surplus = set(grp.sort_values("net_flow", ascending=False).head(k)["station_id"])
        actual_deficit = set(grp.sort_values("net_flow", ascending=True).head(k)["station_id"])

        m_dict = {"month": f"2025-{m:02d}"}
        for tag in ["base", "ridge", "dt"]:
            p_surp = set(grp.sort_values(f"pred_net_{tag}", ascending=False).head(k)["station_id"])
            p_def = set(grp.sort_values(f"pred_net_{tag}", ascending=True).head(k)["station_id"])
            rho = float(grp["net_flow"].corr(grp[f"pred_net_{tag}"], method="spearman"))
            m_dict[f"{tag}_surplus_overlap"] = f"{len(actual_surplus & p_surp)}/{k}"
            m_dict[f"{tag}_deficit_overlap"] = f"{len(actual_deficit & p_def)}/{k}"
            m_dict[f"{tag}_spearman_rho"] = round(rho, 3)
        overlap_records.append(m_dict)

    summary_payload = {
        "meta": {
            "description": "Model comparison summary and benchmarking results (2025 out-of-time test)",
            "test_sample_size": len(test_eval),
            "training_sample_size": len(train_data),
            "test_window": "May 2025 - October 2025 (months 5 to 10)",
            "metric_unit": "completed trips per station-month (NOT physical bicycles)",
            "q1_low_usage_threshold_trips": q1_threshold,
            "q1_low_usage_sample_size": len(low_usage_sub),
            "features_used": {
                "departures_model": feature_cols_dep,
                "returns_model": feature_cols_ret,
                "total_dimension": len(feature_cols_dep)
            },
            "hyperparameters": {
                "ridge": {"alpha": 10.0, "scaler": "StandardScaler"},
                "decision_tree": {"max_depth": 6, "min_samples_leaf": 10, "random_state": 42}
            },
            "guardrails": [
                "Baseline achieves lowest volume error (17.58% WAPE) by naturally absorbing Nordic seasonal shifts.",
                "Ridge regression excels at high-deficit station ranking triage (65%-80% Top-20 overlap, Spearman rho = 0.76).",
                "Results reflect a single out-of-time evaluation season (2025), serving as an empirical benchmark without claims of statistical significance."
            ]
        },
        "overall_metrics": overall_metrics,
        "low_usage_metrics": low_usage_metrics,
        "monthly_wape_breakdown": monthly_breakdown,
        "ranking_overlap_metrics": overlap_records
    }

    out_summary_file = os.path.join(out_dir, "data_model_summary.json")
    with open(out_summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, separators=(",", ":"))
    print(f" -> Generated {out_summary_file} ({os.path.getsize(out_summary_file)/1024:.1f} KB)")

    # Export All 2,718 Station-Month Prediction Records for Interactive Scatter
    prediction_records = []
    for _, r in test_eval.sort_values(["month", "station_id"]).iterrows():
        prediction_records.append({
            "sid": int(r["station_id"]),
            "name": str(r["station_name"]),
            "city": str(r["city"]),
            "m": int(r["month"]),
            "ym": f"2025-{int(r['month']):02d}",
            "act_dep": int(r["departures"]),
            "act_ret": int(r["returns"]),
            "act_net": int(r["net_flow"]),
            "base_dep": int(r["pred_dep_base"]),
            "base_ret": int(r["pred_ret_base"]),
            "base_net": int(r["pred_net_base"]),
            "ridge_dep": round(float(r["pred_dep_ridge"]), 1),
            "ridge_ret": round(float(r["pred_ret_ridge"]), 1),
            "ridge_net": round(float(r["pred_net_ridge"]), 1),
            "dt_dep": round(float(r["pred_dep_dt"]), 1),
            "dt_ret": round(float(r["pred_ret_dt"]), 1),
            "dt_net": round(float(r["pred_net_dt"]), 1)
        })

    predictions_payload = {
        "meta": {
            "description": "Out-of-time station-month actuals vs model predictions (2025 months 5-10)",
            "record_count": len(prediction_records),
            "unit": "completed trips per station-month"
        },
        "records": prediction_records
    }

    out_preds_file = os.path.join(out_dir, "data_model_predictions_2025.json")
    with open(out_preds_file, "w", encoding="utf-8") as f:
        json.dump(predictions_payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_preds_file) / 1024
    print(f" -> Generated {out_preds_file} ({size_kb:.1f} KB; {len(prediction_records)} records)")
    return summary_payload, predictions_payload


def export_weather_scenario_data(docs_data_dir, out_dir):
    """
    Exports data_weather_scenario.json:
    Independent City-Day Weather Scenario Explorer data.
    - Target: Daily completed departures aggregated by city and calendar date.
    - Features: city (is_helsinki), is_weekend, month dummies (m_5 to m_10, m_4 reference), tday, precip.
    - Strictly trained on 2024 (214 days x 2 cities = 428 city-days).
    - Strictly tested out-of-time on 2025 (214 days x 2 cities = 428 city-days).
    - Compares Calendar-only baseline vs Weather-augmented Ridge model on identical 2025 records.
    - Exports empirical residual intervals (80% bounds: p10-p90) and historical 2025 records for analog lookup.
    """
    print("Exporting data_weather_scenario.json...")
    weather_json_path = os.path.join(docs_data_dir, "data_daily_weather.json")
    with open(weather_json_path, "r", encoding="utf-8") as f:
        daily_records = json.load(f)["daily_records"]

    df = pd.DataFrame(daily_records)
    df = df.sort_values(["date", "city"]).reset_index(drop=True)

    train_df = df[df["year"] == 2024].copy().reset_index(drop=True)
    test_df = df[df["year"] == 2025].copy().reset_index(drop=True)

    month_cols = [f"m_{m}" for m in range(5, 11)]

    def make_features(d, include_weather=False):
        X = pd.DataFrame()
        X["is_helsinki"] = (d["city"] == "Helsinki").astype(float)
        X["is_weekend"] = d["is_weekend"].astype(float)
        for m in range(5, 11):
            X[f"m_{m}"] = (d["month"] == m).astype(float)
        if include_weather:
            X["tday"] = d["tday"].astype(float)
            X["precip"] = d["precip"].astype(float)
        return X

    X_cal_train = make_features(train_df, False)
    X_cal_test = make_features(test_df, False)
    X_wth_train = make_features(train_df, True)
    X_wth_test = make_features(test_df, True)

    y_train = train_df["dep"].values
    y_test = test_df["dep"].values

    cal_model = Ridge(alpha=1.0, fit_intercept=True)
    cal_model.fit(X_cal_train, y_train)
    cal_preds = np.maximum(0, cal_model.predict(X_cal_test))

    wth_model = Ridge(alpha=1.0, fit_intercept=True)
    wth_model.fit(X_wth_train, y_train)
    wth_preds = np.maximum(0, wth_model.predict(X_wth_test))

    test_df["cal_pred"] = np.round(cal_preds, 1)
    test_df["wth_pred"] = np.round(wth_preds, 1)
    test_df["residual"] = test_df["dep"] - test_df["wth_pred"]
    test_df["abs_error"] = np.abs(test_df["residual"])

    def calc_metrics(actual, pred):
        mae = float(np.mean(np.abs(actual - pred)))
        wape = float(np.sum(np.abs(actual - pred)) / np.sum(actual) * 100)
        rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
        return {
            "n": int(len(actual)),
            "mae": round(mae, 2),
            "wape": round(wape, 2),
            "rmse": round(rmse, 2)
        }

    def calc_residuals(sub_df):
        res = sub_df["residual"].values
        abs_err = sub_df["abs_error"].values
        p10, p50, p90 = np.percentile(res, [10, 50, 90])
        return {
            "p10": round(float(p10), 1),
            "p50": round(float(p50), 1),
            "p90": round(float(p90), 1),
            "med_abs": round(float(np.median(abs_err)), 1),
            "mae": round(float(np.mean(abs_err)), 1)
        }

    # Metrics
    cal_metrics_all = calc_metrics(y_test, cal_preds)
    wth_metrics_all = calc_metrics(y_test, wth_preds)

    h_mask = (test_df["city"] == "Helsinki").values
    e_mask = (test_df["city"] == "Espoo").values

    cal_metrics_helsinki = calc_metrics(y_test[h_mask], cal_preds[h_mask])
    wth_metrics_helsinki = calc_metrics(y_test[h_mask], wth_preds[h_mask])

    cal_metrics_espoo = calc_metrics(y_test[e_mask], cal_preds[e_mask])
    wth_metrics_espoo = calc_metrics(y_test[e_mask], wth_preds[e_mask])

    # Residuals
    residuals_all = calc_residuals(test_df)
    residuals_helsinki = calc_residuals(test_df[test_df["city"] == "Helsinki"])
    residuals_espoo = calc_residuals(test_df[test_df["city"] == "Espoo"])

    # Empirical bounds from 2024-2025
    tday_bounds = {
        "min": round(float(df["tday"].min()), 1),
        "max": round(float(df["tday"].max()), 1),
        "q01": round(float(df["tday"].quantile(0.01)), 1),
        "q99": round(float(df["tday"].quantile(0.99)), 1)
    }
    precip_bounds = {
        "min": round(float(df["precip"].min()), 1),
        "max": round(float(df["precip"].max()), 1),
        "q01": round(float(df["precip"].quantile(0.01)), 1),
        "q99": round(float(df["precip"].quantile(0.99)), 1)
    }

    # Test records for client-side analog day matching
    test_records = []
    for _, r in test_df.iterrows():
        test_records.append({
            "date": str(r["date"]),
            "city": str(r["city"]),
            "month": int(r["month"]),
            "is_weekend": int(r["is_weekend"]),
            "day_name": str(r["day_name"]),
            "dep": int(r["dep"]),
            "tday": round(float(r["tday"]), 1),
            "precip": round(float(r["precip"]), 1),
            "cal_pred": round(float(r["cal_pred"]), 1),
            "wth_pred": round(float(r["wth_pred"]), 1)
        })

    payload = {
        "meta": {
            "description": "City-day weather scenario analysis and out-of-time evaluation",
            "target": "Daily completed departures by city",
            "granularity": "City-calendar date aggregate (Helsinki and Espoo)",
            "train_period": "2024-04-01 to 2024-10-31 (214 days x 2 cities = 428 city-days)",
            "test_period": "2025-04-01 to 2025-10-31 (214 days x 2 cities = 428 city-days)",
            "total_train_records": len(train_df),
            "total_test_records": len(test_df),
            "calendar_days_per_season": 214,
            "features_calendar": ["is_helsinki", "is_weekend"] + month_cols,
            "features_weather": ["is_helsinki", "is_weekend"] + month_cols + ["tday", "precip"],
            "empirical_bounds": {
                "tday": tday_bounds,
                "precip": precip_bounds
            },
            "methodological_boundaries": [
                "City-day aggregate departures only; strictly separate from station-month rebalancing models.",
                "Retrospective out-of-time test using observed FMI ground weather from 2025; web sliders evaluate hypothetical scenarios, not prospective weather forecasts.",
                "Error bands reflect empirical 2025 test residual intervals (10th to 90th percentile bounds), not statistical confidence intervals.",
                "Weather sensitivity represents descriptive empirical co-movement under linear additive assumptions, not causal policy interventions."
            ]
        },
        "models": {
            "calendar_only": {
                "name": "Calendar-Only Baseline (Ridge alpha=1.0)",
                "intercept": round(float(cal_model.intercept_), 4),
                "coefficients": {k: round(float(v), 4) for k, v in zip(X_cal_train.columns, cal_model.coef_)},
                "metrics": {
                    "overall": cal_metrics_all,
                    "helsinki": cal_metrics_helsinki,
                    "espoo": cal_metrics_espoo
                }
            },
            "weather": {
                "name": "Weather-Augmented Model (Ridge alpha=1.0)",
                "intercept": round(float(wth_model.intercept_), 4),
                "coefficients": {k: round(float(v), 4) for k, v in zip(X_wth_train.columns, wth_model.coef_)},
                "metrics": {
                    "overall": wth_metrics_all,
                    "helsinki": wth_metrics_helsinki,
                    "espoo": wth_metrics_espoo
                },
                "empirical_residuals": {
                    "overall": residuals_all,
                    "helsinki": residuals_helsinki,
                    "espoo": residuals_espoo
                }
            }
        },
        "test_2025_records": test_records
    }

    out_file = os.path.join(out_dir, "data_weather_scenario.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(out_file) / 1024
    print(f" -> Generated {out_file} ({size_kb:.1f} KB; {len(test_records)} test records)")
    return payload


def run_all_exports(docs_data_dir=None):
    """Orchestrates all Phase 1 data export functions."""
    t_start = time.time()
    project_dir = PROJECT_ROOT
    if docs_data_dir is None:
        docs_data_dir = os.path.join(project_dir, "docs", "data")

    os.makedirs(docs_data_dir, exist_ok=True)
    raw_dir = os.path.join(project_dir, "data", "raw")
    processed_dir = os.path.join(project_dir, "data", "processed")

    station_month_path = os.path.join(processed_dir, "station_month.csv")
    city_hourly_summary_path = os.path.join(processed_dir, "city_hourly_summary.csv")
    station_intraday_path = os.path.join(processed_dir, "station_intraday_monthly.csv")
    audit_metrics_path = os.path.join(processed_dir, "intraday_audit_metrics.json")

    print("=" * 70)
    print("HSL CITY BIKE: PHASE 1 WEB DATA EXPORT PIPELINE")
    print(f"Destination: {docs_data_dir}")
    print("=" * 70)

    # 1. Stations Data
    export_stations_data(station_month_path, docs_data_dir)

    # 2. Hourly City Curves
    export_hourly_city_data(city_hourly_summary_path, docs_data_dir)

    # 3. Commute Peak Tidal Reversals
    export_commute_peaks_data(station_intraday_path, audit_metrics_path, docs_data_dir)

    # 4. Daily Weather & Ridership
    export_daily_weather_data(raw_dir, docs_data_dir)

    # 5 & 6. Model Comparison Summary & 2025 Predictions
    export_model_data(station_month_path, docs_data_dir)

    # 7. City-Day Weather Scenario Data
    export_weather_scenario_data(docs_data_dir, docs_data_dir)

    # Summary
    print("=" * 70)
    print("EXPORT SUMMARY & FILE SIZES:")
    total_bytes = 0
    exported_files = sorted(glob.glob(os.path.join(docs_data_dir, "*.json")))
    for ef in exported_files:
        sb = os.path.getsize(ef)
        total_bytes += sb
        print(f" - {os.path.basename(ef):<35} : {sb/1024:6.1f} KB")
    print(f"TOTAL WEB DATA PAYLOAD: {total_bytes/1024:.1f} KB ({total_bytes/(1024*1024):.2f} MB)")
    print(f"Pipeline completed in {time.time() - t_start:.2f} seconds.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_exports()
