"""
Results Demonstration Script for HSL City Bike Project.
Loads data/processed/station_month.csv, displays analytical insights, and exports summary plots.
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure terminal output supports UTF-8 characters on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_dir, "data", "processed", "station_month.csv")

    if not os.path.exists(data_path):
        print(f"[Error] {data_path} does not exist. Please run 'python run_pipeline.py' first.")
        sys.exit(1)

    df = pd.read_csv(data_path)

    print("=" * 75)
    print("HSL CITY BIKE: STATION-MONTH DATASET OVERVIEW")
    print("=" * 75)
    print(f"File Path           : data/processed/station_month.csv")
    print(f"Total Rows          : {len(df):,}")
    print(f"Unique Stations     : {df['station_id'].nunique():,}")
    print(f"Months Covered      : {sorted(df['year_month'].unique())}")
    print(f"Total Completed Trips: {df['departures'].sum():,}")

    coords_coverage = (df["latitude"].notna().sum() / len(df)) * 100
    print(f"Coordinate Coverage : {coords_coverage:.1f}% ({df['latitude'].notna().sum():,} / {len(df):,})")
    print("-" * 75)

    # 1. Monthly Trends
    print("\n[1] MONTHLY ACTIVITY SUMMARY:")
    monthly = (
        df.groupby("year_month")
        .agg(
            active_stations=("station_id", "nunique"),
            total_departures=("departures", "sum"),
            total_returns=("returns", "sum"),
            avg_distance_km=("avg_distance_m", lambda x: (x.mean() / 1000).round(2)),
            avg_duration_min=("avg_duration_sec", lambda x: (x.mean() / 60).round(1)),
        )
        .reset_index()
    )
    print(monthly.to_string(index=False))

    # 2. Top 10 Departure Hotspots
    print("\n[2] TOP 10 BUSIEST STATIONS (BY TOTAL DEPARTURES):")
    top_stations = (
        df.groupby(["station_id", "station_name", "city", "capacity"])
        .agg(
            total_departures=("departures", "sum"),
            total_returns=("returns", "sum"),
            net_flow=("net_flow", "sum"),
        )
        .reset_index()
        .sort_values("total_departures", ascending=False)
        .head(10)
    )
    print(top_stations.to_string(index=False))

    # 3. Allocation / Rebalancing Priorities
    print("\n[3] REBALANCING IMBALANCES (NET FLOW = RETURNS - DEPARTURES):")
    all_station_totals = (
        df.groupby(["station_id", "station_name", "city"])
        .agg(
            total_departures=("departures", "sum"),
            total_returns=("returns", "sum"),
            net_flow=("net_flow", "sum"),
        )
        .reset_index()
    )

    surplus = all_station_totals.sort_values("net_flow", ascending=False).head(5)
    print("\n  >> Top 5 Surplus Stations (Bikes accumulate -> Requires removal):")
    for _, row in surplus.iterrows():
        print(f"     * Station {row['station_id']:3d} ({row['station_name']}, {row['city']}): +{row['net_flow']:,} bikes")

    deficit = all_station_totals.sort_values("net_flow", ascending=True).head(5)
    print("\n  >> Top 5 Deficit Stations (Bikes deplete -> Requires restocking):")
    for _, row in deficit.iterrows():
        print(f"     * Station {row['station_id']:3d} ({row['station_name']}, {row['city']}): {row['net_flow']:,} bikes")

    # 4. Weather Observations Summary
    if "avg_temperature_c" in df.columns:
        print("\n[4] OBSERVED WEATHER SUMMARY (FMI ACTUAL OBSERVATIONS):")
        weather_summary = (
            df.groupby(["year_month", "city"])
            .agg(
                station_count=("station_id", "nunique"),
                avg_temp=("avg_temperature_c", "first"),
                min_temp=("min_temperature_c", "first"),
                max_temp=("max_temperature_c", "first"),
                precip_mm=("total_precipitation_mm", "first"),
                rainy_days=("rainy_days_count", "first"),
            )
            .reset_index()
        )
        print(weather_summary.to_string(index=False))


    # 4. Export visualization chart
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 2, figsize=(16, 11))
        fig.suptitle("HSL City Bike 2025: Season & Station Flow Analysis", fontsize=16, fontweight="bold")

        # Chart 1: Monthly Departures
        axs[0, 0].bar(monthly["year_month"], monthly["total_departures"] / 1000, color="#2b5c8f", edgecolor="black")
        axs[0, 0].set_title("Total Trips per Month (Thousands)", fontweight="bold")
        axs[0, 0].set_ylabel("Trips (in thousands)")
        axs[0, 0].grid(axis="y", linestyle="--", alpha=0.6)

        # Chart 2: Top 10 Stations
        top10_plot = top_stations.sort_values("total_departures", ascending=True)
        axs[0, 1].barh(
            top10_plot["station_name"].fillna(top10_plot["station_id"].astype(str)),
            top10_plot["total_departures"] / 1000,
            color="#2ca02c",
            edgecolor="black",
        )
        axs[0, 1].set_title("Top 10 Busiest Stations (Total Departures in Thousands)", fontweight="bold")
        axs[0, 1].set_xlabel("Trips (in thousands)")
        axs[0, 1].grid(axis="x", linestyle="--", alpha=0.6)

        # Chart 3: Extreme Rebalancing Imbalances
        imbalances = pd.concat([deficit.head(5), surplus.head(5)]).sort_values("net_flow")
        colors = ["#d62728" if v < 0 else "#1f77b4" for v in imbalances["net_flow"]]
        axs[1, 0].barh(
            imbalances["station_name"].fillna(imbalances["station_id"].astype(str)),
            imbalances["net_flow"],
            color=colors,
            edgecolor="black",
        )
        axs[1, 0].axvline(0, color="black", linestyle="--", linewidth=1)
        axs[1, 0].set_title("Top Rebalancing Imbalances (Net Flow = Returns - Departures)", fontweight="bold")
        axs[1, 0].set_xlabel("Net Bike Flow")
        axs[1, 0].grid(axis="x", linestyle="--", alpha=0.6)

        # Chart 4: Geographic Scatter of Station Demand
        has_coords = df.dropna(subset=["latitude", "longitude"]).groupby(["station_id", "latitude", "longitude"])[
            "departures"
        ].sum().reset_index()
        sc = axs[1, 1].scatter(
            has_coords["longitude"],
            has_coords["latitude"],
            c=has_coords["departures"],
            cmap="viridis",
            s=has_coords["departures"] / 150 + 10,
            alpha=0.75,
            edgecolor="none",
        )
        axs[1, 1].set_title("Station Locations & Total Demand (Helsinki & Espoo)", fontweight="bold")
        axs[1, 1].set_xlabel("Longitude")
        axs[1, 1].set_ylabel("Latitude")
        plt.colorbar(sc, ax=axs[1, 1], label="Total Departures")

        plt.tight_layout()
        plot_path = os.path.join(project_dir, "data", "processed", "season_summary.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"\n[Done] Summary charts exported to {plot_path}")
    except Exception as e:
        print(f"\n[Warning] Could not generate plots: {e}")

    print("\n" + "=" * 75)


if __name__ == "__main__":
    main()

