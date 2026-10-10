"""
Static Figure Generation Pipeline for HSL City Bike Project.
Generates publication-quality static figures for course presentation and GitHub documentation.
Outputs all figures to reports/figures/ adhering to HSL_City_Bike_Project_Canvas.md specifications.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import TwoSlopeNorm

# Ensure terminal output supports UTF-8 characters on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Configure global matplotlib aesthetics
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["grid.color"] = "#e0e0e0"
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"] = 0.7


def ensure_output_dir(output_dir):
    """Creates output directory if it does not exist."""
    os.makedirs(output_dir, exist_ok=True)


def generate_figure_1(station_month_df, output_dir):
    """
    Figure 1: Monthly Ridership Comparison (2024 vs. 2025).
    Displays monthly departures across the April-October season for both years,
    with municipal breakdown between Helsinki and Espoo.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Aggregation for Panel A: System Total
    monthly_tot = station_month_df.groupby("year_month")["departures"].sum().reset_index()
    monthly_tot["year"] = monthly_tot["year_month"].str[:4].astype(int)
    monthly_tot["month"] = monthly_tot["year_month"].str[5:7].astype(int)

    piv_tot = monthly_tot.pivot(index="month", columns="year", values="departures") / 1000
    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    x = np.arange(len(months))
    width = 0.35

    rects1 = ax1.bar(x - width/2, piv_tot[2024], width, label="2024 Season (Total: 2.51M)", color="#2b5c8f", edgecolor="#1a365d")
    rects2 = ax1.bar(x + width/2, piv_tot[2025], width, label="2025 Season (Total: 2.44M)", color="#e26d5c", edgecolor="#9c27b0")

    ax1.set_title("System-Wide Monthly Departures (2024 vs. 2025)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Cycling Season Month (Calendar)", fontsize=11)
    ax1.set_ylabel("Monthly Completed Trips (Thousands)", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(months)
    ax1.legend(frameon=True, facecolor="white", framealpha=0.9)
    ax1.grid(axis="y")
    ax1.set_ylim(0, 560)

    # Add value labels on top of bars
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}k", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#1a365d")
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}k", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#b71c1c")

    # Aggregation for Panel B: Municipal Comparison (Helsinki vs Espoo)
    muni_df = station_month_df[station_month_df["city"].isin(["Helsinki", "Espoo"])].copy()
    muni_monthly = muni_df.groupby(["year_month", "city"])["departures"].sum().reset_index()
    muni_monthly["year"] = muni_monthly["year_month"].str[:4].astype(int)
    muni_monthly["month"] = muni_monthly["year_month"].str[5:7].astype(int)

    hki_24 = muni_monthly[(muni_monthly["city"] == "Helsinki") & (muni_monthly["year"] == 2024)].set_index("month")["departures"] / 1000
    hki_25 = muni_monthly[(muni_monthly["city"] == "Helsinki") & (muni_monthly["year"] == 2025)].set_index("month")["departures"] / 1000
    esp_24 = muni_monthly[(muni_monthly["city"] == "Espoo") & (muni_monthly["year"] == 2024)].set_index("month")["departures"] / 1000
    esp_25 = muni_monthly[(muni_monthly["city"] == "Espoo") & (muni_monthly["year"] == 2025)].set_index("month")["departures"] / 1000

    ax2.plot(months, hki_24, marker="o", color="#1b4965", linewidth=2.2, label="Helsinki 2024 (2.20M trips)")
    ax2.plot(months, hki_25, marker="s", color="#3a86c8", linewidth=2.2, linestyle="--", label="Helsinki 2025 (2.17M trips)")
    ax2.plot(months, esp_24, marker="^", color="#d90429", linewidth=2.0, label="Espoo 2024 (294k trips)")
    ax2.plot(months, esp_25, marker="d", color="#f77f00", linewidth=2.0, linestyle="--", label="Espoo 2025 (260k trips)")

    ax2.set_title("Municipal Monthly Trends: Helsinki (~89%) vs. Espoo (~11%)", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Cycling Season Month (Calendar)", fontsize=11)
    ax2.set_ylabel("Monthly Departures (Thousands)", fontsize=11)
    ax2.legend(frameon=True, facecolor="white", framealpha=0.9)
    ax2.grid(True)

    fig.suptitle("Figure 1: Monthly Ridership Dynamics Across 2024 and 2025 HSL Cycling Seasons\n"
                 "(Temporal Scope: April 1 - October 31; Granularity: System-wide & Municipality; Unit: Completed Trips in Thousands)",
                 fontsize=14, fontweight="bold", y=1.03)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig1_monthly_ridership_comparison_2024_2025.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 1: {out_path}")


def generate_figure_2(station_month_df, output_dir):
    """
    Figure 2: Station-Month Demand Heatmap.
    Displays demand intensity across all 14 months (2024-04 to 2025-10)
    for the Top 30 busiest bike stations across the regional network.
    """
    # Select Top 30 stations by total departures across all 14 months
    top_stations = (
        station_month_df.groupby(["station_id", "station_name", "city", "capacity"])["departures"]
        .sum()
        .reset_index()
        .sort_values("departures", ascending=False)
        .head(30)
    )

    top_ids = top_stations["station_id"].tolist()
    sub_df = station_month_df[station_month_df["station_id"].isin(top_ids)].copy()

    # Create label: "Station Name (City, Cap: XX)"
    id_to_meta = {
        row["station_id"]: f"{row['station_name']} ({row['city']}, c:{int(row['capacity']) if pd.notna(row['capacity']) else '?'})"
        for _, row in top_stations.iterrows()
    }
    sub_df["station_label"] = sub_df["station_id"].map(id_to_meta)

    # Pivot matrix
    all_months = sorted(station_month_df["year_month"].unique())
    piv = sub_df.pivot(index="station_label", columns="year_month", values="departures").fillna(0)
    # Order rows by total departures descending
    ordered_labels = [id_to_meta[sid] for sid in top_ids]
    piv = piv.reindex(ordered_labels)

    fig, ax = plt.subplots(figsize=(15, 11))

    # Values in thousands
    data_k = piv.values / 1000.0

    im = ax.imshow(data_k, cmap="YlOrRd", aspect="auto")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Monthly Departures (Thousands of Trips)", fontsize=11, fontweight="bold")

    # Ticks
    ax.set_xticks(np.arange(len(all_months)))
    ax.set_xticklabels(all_months, rotation=45, ha="right", fontsize=10, fontweight="bold")
    ax.set_yticks(np.arange(len(ordered_labels)))
    ax.set_yticklabels(ordered_labels, fontsize=9.5)

    # Vertical divider separating 2024 and 2025 seasons
    ax.axvline(6.5, color="black", linewidth=2.0, linestyle="-")
    ax.text(3.0, -1.2, "--- 2024 Cycling Season ---", ha="center", fontsize=11, fontweight="bold", color="#1a365d")
    ax.text(10.0, -1.2, "--- 2025 Cycling Season ---", ha="center", fontsize=11, fontweight="bold", color="#b71c1c")

    # Annotate values inside cells
    for i in range(len(ordered_labels)):
        for j in range(len(all_months)):
            val = data_k[i, j]
            color = "white" if val > 6.0 else "black"
            ax.text(j, i, f"{val:.1f}k", ha="center", va="center", color=color, fontsize=7.5)

    ax.set_title("Figure 2: Station-Month Demand Intensity Heatmap (Top 30 Busiest Stations Across 2024-2025)\n"
                 "(Temporal Scope: 14 Months; Unit: Completed Departures per Station-Month in Thousands)",
                 fontsize=13, fontweight="bold", pad=28)
    ax.set_xlabel("Season & Calendar Month (YYYY-MM)", fontsize=11, labelpad=10)
    ax.set_ylabel("Station Name (Municipality, Dock Capacity)", fontsize=11, labelpad=10)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig2_station_month_demand_heatmap.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 2: {out_path}")


def generate_figure_3(station_month_df, output_dir):
    """
    Figure 3: Station Geographic Net Flow Map (Zero-Centered Colormap).
    Plots all 454 stations with verified WGS84 coordinates.
    Colormap is centered at 0 to delineate persistent bike deficit sinks vs. surplus accumulators.
    Unmapped stations without coordinates are explicitly excluded and documented.
    """
    coords_df = (
        station_month_df.dropna(subset=["latitude", "longitude"])
        .groupby(["station_id", "station_name", "city", "latitude", "longitude", "capacity"])
        .agg(
            total_departures=("departures", "sum"),
            total_returns=("returns", "sum"),
            total_net_flow=("net_flow", "sum"),
            total_trips=("total_trips", "sum"),
        )
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(15, 11))

    vlim = 6000
    norm = TwoSlopeNorm(vmin=-vlim, vcenter=0, vmax=vlim)

    sizes = np.clip(coords_df["total_trips"] / 250.0, 20, 450)

    scatter = ax.scatter(
        coords_df["longitude"],
        coords_df["latitude"],
        c=coords_df["total_net_flow"],
        cmap="coolwarm_r",
        norm=norm,
        s=sizes,
        alpha=0.85,
        edgecolor="#333333",
        linewidth=0.6,
        zorder=3
    )

    cbar = fig.colorbar(scatter, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Cumulative Net Flow (Returns - Departures)\n[Red = Bike Sinks / Deficit; Blue = Bike Sources / Surplus]",
                    fontsize=10.5, fontweight="bold")

    key_annotations = [
        (113, "Pasila railway station\n(Deficit: -11,014)", (-140, 25)),
        (203, "Opastinsilta\n(Deficit: -5,049)", (35, 20)),
        (120, "Mäkelänkatu\n(Deficit: -5,275)", (-110, -35)),
        (11, "Unioninkatu\n(Surplus: +3,474)", (35, -35)),
        (12, "Kanavaranta\n(Surplus: +3,081)", (35, 15)),
        (404, "Sompasaari\n(Surplus: +2,900)", (35, 30)),
        (541, "Aalto Univ. / Otaniemi\n(High Turnover Hub)", (-110, 25)),
        (731, "Leppävaarankäytävä [Espoo]\n(Surplus: +2,082)", (-145, -20)),
        (749, "Vallikatu [Espoo]\n(Deficit: -1,887)", (30, 20)),
    ]

    for sid, label, offset in key_annotations:
        row = coords_df[coords_df["station_id"] == sid]
        if not row.empty:
            r = row.iloc[0]
            ax.annotate(
                label,
                xy=(r["longitude"], r["latitude"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=8.5,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#888888", alpha=0.9),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.1", color="#333333", lw=0.9),
                zorder=5
            )

    ax.axvline(24.85, color="#888888", linestyle=":", linewidth=1.2, alpha=0.7)
    ax.text(24.76, 60.255, "← Espoo Suburbs & Campuses", fontsize=11, fontweight="bold", color="#555555")
    ax.text(24.87, 60.255, "Helsinki Urban Core & Waterfront →", fontsize=11, fontweight="bold", color="#1a365d")

    ax.set_title("Figure 3: Spatial Distribution of Directional Net Flow Across Regional Bike Stations\n"
                 "(Evaluated on 454 Verified Coordinate Stations; Marker Size = Total Turnover Volume; Projection: EPSG:4326)",
                 fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Longitude (Degrees East)", fontsize=11, labelpad=8)
    ax.set_ylabel("Latitude (Degrees North)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout(rect=[0, 0.06, 1, 0.97])

    fig.text(0.12, 0.015,
             "Note: Exactly 7 unmapped docks (e.g. #997 Workshop, #999 Relay Test, and temporary docks) lacking verified coordinates\n"
             "are excluded from geographic plotting (71 station-month rows). Net flow = returns - departures reflects macro directional drift,\n"
             "NOT real-time physical dock inventory or vehicle dispatch volumes.",
             fontsize=9, style="italic", color="#555555")

    out_path = os.path.join(output_dir, "fig3_station_net_flow_map.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 3: {out_path}")


def generate_figure_4(station_month_df, output_dir):
    """
    Figure 4: Top Deficit and Surplus Station Ranking Chart.
    Presents the Top 10 Deficit Stations (systemic trip loss / bike sinks)
    and Top 10 Surplus Stations (systemic trip arrival / dock congestion).
    """
    agg = (
        station_month_df.groupby(["station_id", "station_name", "city", "capacity"])
        .agg(
            total_departures=("departures", "sum"),
            total_returns=("returns", "sum"),
            net_flow=("net_flow", "sum"),
        )
        .reset_index()
    )

    top_deficit = agg.sort_values("net_flow", ascending=True).head(10).copy()
    top_surplus = agg.sort_values("net_flow", ascending=False).head(10).copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 7.5))

    top_deficit = top_deficit.sort_values("net_flow", ascending=False)
    y_pos1 = np.arange(len(top_deficit))
    labels1 = [f"{r['station_name']} ({r['city']}, cap:{int(r['capacity']) if pd.notna(r['capacity']) else '?'})"
               for _, r in top_deficit.iterrows()]

    bars1 = ax1.barh(y_pos1, top_deficit["net_flow"], color="#d90429", edgecolor="#800f2f", alpha=0.85)
    ax1.set_yticks(y_pos1)
    ax1.set_yticklabels(labels1, fontsize=9.5)
    ax1.set_xlim(-13800, 0)
    ax1.set_xlabel("Cumulative Net Flow (Returns - Departures) [Trips]", fontsize=10.5, fontweight="bold")
    ax1.set_title("Top 10 Deficit Stations (Bike Sinks / Outflow Depletion)\n"
                  "Frequent stockouts: Departures vastly exceed Returns", fontsize=12, fontweight="bold", pad=10)
    ax1.axvline(0, color="black", linewidth=1.0)
    ax1.grid(axis="x")

    for bar in bars1:
        w = bar.get_width()
        ax1.annotate(f"{int(w):,} trips", xy=(w, bar.get_y() + bar.get_height()/2),
                     xytext=(-6, 0), textcoords="offset points", ha="right", va="center",
                     fontsize=8.5, fontweight="bold", color="#800f2f")

    top_surplus = top_surplus.sort_values("net_flow", ascending=True)
    y_pos2 = np.arange(len(top_surplus))
    labels2 = [f"{r['station_name']} ({r['city']}, cap:{int(r['capacity']) if pd.notna(r['capacity']) else '?'})"
               for _, r in top_surplus.iterrows()]

    bars2 = ax2.barh(y_pos2, top_surplus["net_flow"], color="#1b4965", edgecolor="#0b2545", alpha=0.85)
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(labels2, fontsize=9.5)
    ax2.set_xlim(0, 4300)
    ax2.set_xlabel("Cumulative Net Flow (Returns - Departures) [Trips]", fontsize=10.5, fontweight="bold")
    ax2.set_title("Top 10 Surplus Stations (Bike Sources / Inflow Saturation)\n"
                  "Frequent dock blocking: Returns vastly exceed Departures", fontsize=12, fontweight="bold", pad=10)
    ax2.axvline(0, color="black", linewidth=1.0)
    ax2.grid(axis="x")

    for bar in bars2:
        w = bar.get_width()
        ax2.annotate(f"+{int(w):,} trips", xy=(w, bar.get_y() + bar.get_height()/2),
                     xytext=(6, 0), textcoords="offset points", ha="left", va="center",
                     fontsize=8.5, fontweight="bold", color="#0b2545")

    fig.suptitle("Figure 4: Persistent Macro Rebalancing Imbalances Across Regional Bike Stations (2024-2025)\n"
                 "(Aggregated over 14 Season Months; Net Flow = Returns - Departures; Unit: Total Trips)",
                 fontsize=14, fontweight="bold", y=1.03)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig4_top_deficit_surplus_stations.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 4: {out_path}")


def generate_figure_5(city_hourly_df, output_dir):
    """
    Figure 5: Hourly Departure Curves (Weekday vs. Weekend).
    Compares diurnal profiles for Helsinki and Espoo normalized by active operating days
    (154 weekdays and 60 weekends per 214-day season).
    Highlights morning (07:00-09:00) vs. evening (16:00-18:00) peak hour asymmetries.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))

    hours = np.arange(24)

    # Process Helsinki
    hki_df = city_hourly_df[city_hourly_df["city"] == "Helsinki"]
    hki_wd_24 = hki_df[(hki_df["year"] == 2024) & (hki_df["is_weekend"] == 0)].groupby("hour")["departures"].sum() / 154.0
    hki_we_24 = hki_df[(hki_df["year"] == 2024) & (hki_df["is_weekend"] == 1)].groupby("hour")["departures"].sum() / 60.0
    hki_wd_25 = hki_df[(hki_df["year"] == 2025) & (hki_df["is_weekend"] == 0)].groupby("hour")["departures"].sum() / 154.0
    hki_we_25 = hki_df[(hki_df["year"] == 2025) & (hki_df["is_weekend"] == 1)].groupby("hour")["departures"].sum() / 60.0

    for ax in (ax1, ax2):
        ax.axvspan(7, 9, color="#ffe8cc", alpha=0.5, label="Morning Peak (07:00 - 09:00)")
        ax.axvspan(16, 18, color="#ffccd5", alpha=0.5, label="Evening Peak (16:00 - 18:00)")

    ax1.plot(hours, hki_wd_24, color="#1b4965", linewidth=2.4, marker="o", markersize=4, label="2024 Weekday (Avg: 10,985 trips/day)")
    ax1.plot(hours, hki_wd_25, color="#2b5c8f", linewidth=2.2, linestyle="--", marker="s", markersize=4, label="2025 Weekday (Avg: 10,708 trips/day)")
    ax1.plot(hours, hki_we_24, color="#d90429", linewidth=2.0, marker="^", markersize=4, label="2024 Weekend (Avg: 8,530 trips/day)")
    ax1.plot(hours, hki_we_25, color="#f77f00", linewidth=2.0, linestyle="--", marker="d", markersize=4, label="2025 Weekend (Avg: 8,679 trips/day)")

    ax1.set_title("Helsinki: Diurnal Demand Curves\n(Classic Bimodal Weekday Commute vs. Unimodal Weekend Plateau)",
                  fontsize=12, fontweight="bold", pad=10)
    ax1.set_xlabel("Local Hour of Day (00:00 - 23:00, Europe/Helsinki EEST)", fontsize=10.5)
    ax1.set_ylabel("Normalized Daily Average Departures (Trips / Hour)", fontsize=10.5)
    ax1.set_xticks(range(0, 24, 2))
    ax1.set_ylim(-30, 1380)
    ax1.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9, fontsize=8.5)
    ax1.grid(True)

    ax1.annotate("Morning Rush: ~643/hr\n(Strict work commute)", xy=(8, 790), xytext=(2, 920),
                 arrowprops=dict(arrowstyle="->", color="#1b4965", lw=1.2), fontsize=8.5, fontweight="bold")
    ax1.annotate("Evening Rush: ~1,136/hr\n(+77% vs Morning; Commute+Leisure)", xy=(16, 1136), xytext=(10, 1240),
                 arrowprops=dict(arrowstyle="->", color="#1b4965", lw=1.2), fontsize=8.5, fontweight="bold")

    # Process Espoo
    esp_df = city_hourly_df[city_hourly_df["city"] == "Espoo"]
    esp_wd_24 = esp_df[(esp_df["year"] == 2024) & (esp_df["is_weekend"] == 0)].groupby("hour")["departures"].sum() / 154.0
    esp_we_24 = esp_df[(esp_df["year"] == 2024) & (esp_df["is_weekend"] == 1)].groupby("hour")["departures"].sum() / 60.0
    esp_wd_25 = esp_df[(esp_df["year"] == 2025) & (esp_df["is_weekend"] == 0)].groupby("hour")["departures"].sum() / 154.0
    esp_we_25 = esp_df[(esp_df["year"] == 2025) & (esp_df["is_weekend"] == 1)].groupby("hour")["departures"].sum() / 60.0

    ax2.plot(hours, esp_wd_24, color="#1b4965", linewidth=2.4, marker="o", markersize=4, label="2024 Weekday (Avg: 1,460 trips/day)")
    ax2.plot(hours, esp_wd_25, color="#2b5c8f", linewidth=2.2, linestyle="--", marker="s", markersize=4, label="2025 Weekday (Avg: 1,287 trips/day)")
    ax2.plot(hours, esp_we_24, color="#d90429", linewidth=2.0, marker="^", markersize=4, label="2024 Weekend (Avg: 1,149 trips/day)")
    ax2.plot(hours, esp_we_25, color="#f77f00", linewidth=2.0, linestyle="--", marker="d", markersize=4, label="2025 Weekend (Avg: 1,030 trips/day)")

    ax2.set_title("Espoo: Diurnal Demand Curves\n(Suburban Hub & Campus Focus, ~2.0× Evening-to-Morning Peak Ratio)",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.set_xlabel("Local Hour of Day (00:00 - 23:00, Europe/Helsinki EEST)", fontsize=10.5)
    ax2.set_ylabel("Normalized Daily Average Departures (Trips / Hour)", fontsize=10.5)
    ax2.set_xticks(range(0, 24, 2))
    ax2.set_ylim(-5, 195)
    ax2.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9, fontsize=8.5)
    ax2.grid(True)

    ax2.annotate("Morning Rush: ~75/hr", xy=(8, 93), xytext=(2, 115),
                 arrowprops=dict(arrowstyle="->", color="#1b4965", lw=1.2), fontsize=8.5, fontweight="bold")
    ax2.annotate("Evening Rush: ~155/hr\n(+105% vs Morning)", xy=(16, 155), xytext=(11, 168),
                 arrowprops=dict(arrowstyle="->", color="#1b4965", lw=1.2), fontsize=8.5, fontweight="bold")

    fig.suptitle("Figure 5: Operating-Day Normalized Hourly Departure Dynamics: Weekday vs. Weekend\n"
                 "(Temporal Scope: 2024 & 2025 Seasons; 154 Weekdays & 60 Weekends per Season; Unit: Departures / Operating Day / Hour)",
                 fontsize=14, fontweight="bold", y=1.03)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig5_hourly_departure_curves_weekday_weekend.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 5: {out_path}")


def generate_figure_6(station_intraday_df, station_month_df, output_dir):
    """
    Figure 6: Morning Peak vs. Evening Peak Station Comparison.
    Demonstrates the commuter tidal reversal phenomenon:
    Stations that suffer severe net outflow deficits during morning rush (07:00-09:00)
    transform into major net inflow surplus accumulators during evening rush (16:00-18:00), and vice versa.
    """
    wd = station_intraday_df[station_intraday_df["is_weekend"] == 0].copy()

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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    merged["tidal_swing"] = np.abs(merged["morn_net"] - merged["eve_net"])
    top_tidal = merged.sort_values("tidal_swing", ascending=False).head(10).copy()
    top_tidal = top_tidal.sort_values("tidal_swing", ascending=True)

    y_pos = np.arange(len(top_tidal))
    bar_h = 0.38

    labels = [f"{r['station_name']} ({r['city']})" for _, r in top_tidal.iterrows()]
    ax1.barh(y_pos - bar_h/2, top_tidal["morn_net"], height=bar_h, color="#f77f00", edgecolor="#b25e00",
             label="Morning Peak Net Flow (07:00 - 09:00)")
    ax1.barh(y_pos + bar_h/2, top_tidal["eve_net"], height=bar_h, color="#2b5c8f", edgecolor="#1a365d",
             label="Evening Peak Net Flow (16:00 - 18:00)")

    ax1.axvline(0, color="black", linestyle="-", linewidth=1.0)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=9.5)
    ax1.set_xlabel("Net Flow = Returns - Departures (Cumulative Weekday Trips)", fontsize=10.5, fontweight="bold")
    ax1.set_title("Commuter Tidal Reversal: Top 10 High-Swing Hubs\n"
                  "(Opposite signs confirm daily flow reversal)", fontsize=12, fontweight="bold", pad=10)
    ax1.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9, fontsize=8.5)
    ax1.grid(axis="x")

    top_100 = merged.sort_values("total_peak_trips", ascending=False).head(120)

    sc = ax2.scatter(
        top_100["morn_net"],
        top_100["eve_net"],
        c=top_100["tidal_swing"],
        cmap="coolwarm",
        s=top_100["total_peak_trips"] / 200.0 + 30,
        alpha=0.8,
        edgecolor="#333333",
        linewidth=0.7
    )

    ax2.axhline(0, color="grey", linestyle="--", linewidth=1.0)
    ax2.axvline(0, color="grey", linestyle="--", linewidth=1.0)
    ax2.set_xlim(-8500, 8500)
    ax2.set_ylim(-6200, 3600)

    ax2.text(-8200, 2700, "Quadrant II: Residential Feeder\n(Morning Deficit → Evening Surplus)\ne.g. Sompasaari, Apollonkatu",
             fontsize=8.5, fontweight="bold", color="#d90429", bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff5f5", edgecolor="#ffcccc"))
    ax2.text(1200, -2200, "Quadrant IV: Employment / Commercial\n(Morning Surplus → Evening Deficit)\ne.g. Salmisaarenranta, Itämerentori",
             fontsize=8.5, fontweight="bold", color="#1b4965", bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0f8ff", edgecolor="#cce5ff"))
    ax2.text(-8200, -5800, "Quadrant III: Structural Sink\n(Deficit all day)\ne.g. Pasila station",
             fontsize=8.5, fontweight="bold", color="#555555", bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5", edgecolor="#dddddd"))

    point_callouts = [
        ("Sompasaari", (-75, -20)),
        ("Salmisaarenranta", (-145, 15)),
        ("Itämerentori", (-125, -20)),
        ("Pasila railway station", (-140, 10)),
        ("Erottajan aukio", (-110, 15)),
    ]
    for name, offset in point_callouts:
        r = top_100[top_100["station_name"] == name]
        if not r.empty:
            row = r.iloc[0]
            ax2.annotate(name, xy=(row["morn_net"], row["eve_net"]), xytext=offset,
                         textcoords="offset points", fontsize=8, fontweight="bold",
                         arrowprops=dict(arrowstyle="->", color="#333333", lw=0.9))

    ax2.set_xlabel("Morning Peak Net Flow (07:00 - 09:00) [Trips]", fontsize=10.5, fontweight="bold")
    ax2.set_ylabel("Evening Peak Net Flow (16:00 - 18:00) [Trips]", fontsize=10.5, fontweight="bold")
    ax2.set_title("Commuter Net Flow Quadrant Analysis (Top 120 Busiest Hubs)\n"
                  "Negative correlation reveals daily commuter tidal cycle", fontsize=12, fontweight="bold", pad=10)
    ax2.grid(True)

    fig.suptitle("Figure 6: Morning Peak vs. Evening Peak Station Comparison: Revealing Diurnal Commuter Tidal Reversal\n"
                 "(Temporal Scope: 154 Weekdays Across 2024-2025; Morning: 07:00-09:00, Evening: 16:00-18:00; Unit: Net Flow Trips)",
                 fontsize=14, fontweight="bold", y=1.03)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig6_morning_vs_evening_peak_station_comparison.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 6: {out_path}")


def generate_figure_7(station_month_df, output_dir):
    """
    Figure 7: 2025 Actual Demand vs. 2024 Historical Same-Month Baseline.
    Evaluates out-of-time forecasting performance across all 3,170 matched test station-months in 2025.
    Presents scatter comparison against 1:1 line and month-by-month MAE/WAPE trajectories.
    """
    df = station_month_df.copy()
    df["year"] = df["year_month"].str[:4].astype(int)
    df["month"] = df["year_month"].str[5:7].astype(int)

    df_2024 = df[df["year"] == 2024][["month", "station_id", "station_name", "city", "departures", "returns"]].rename(
        columns={"departures": "dep_2024", "returns": "ret_2024"}
    )
    df_2025 = df[df["year"] == 2025][["month", "station_id", "station_name", "city", "departures", "returns"]].rename(
        columns={"departures": "dep_2025", "returns": "ret_2025"}
    )

    merged = pd.merge(df_2025, df_2024, on=["month", "station_id"])
    n_total = len(merged)

    # Compute overall metrics
    mae_overall = np.mean(np.abs(merged["dep_2025"] - merged["dep_2024"]))
    wape_overall = np.sum(np.abs(merged["dep_2025"] - merged["dep_2024"])) / np.sum(merged["dep_2025"]) * 100.0

    # Monthly metrics
    monthly_stats = []
    month_names = ["Apr (04)", "May (05)", "Jun (06)", "Jul (07)", "Aug (08)", "Sep (09)", "Oct (10)"]
    for m in range(4, 11):
        sub = merged[merged["month"] == m]
        m_mae = np.mean(np.abs(sub["dep_2025"] - sub["dep_2024"]))
        m_wape = np.sum(np.abs(sub["dep_2025"] - sub["dep_2024"])) / np.sum(sub["dep_2025"]) * 100.0
        monthly_stats.append({"month": m, "mae": m_mae, "wape": m_wape, "n": len(sub)})
    m_df = pd.DataFrame(monthly_stats)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Panel A: Actual vs Baseline Scatter Plot
    max_val = max(merged["dep_2025"].max(), merged["dep_2024"].max()) + 200
    ax1.scatter(merged["dep_2024"] / 1000.0, merged["dep_2025"] / 1000.0,
                alpha=0.35, color="#2b5c8f", edgecolors="none", s=25)

    # 1:1 perfect prediction reference line
    ax1.plot([0, max_val / 1000.0], [0, max_val / 1000.0], color="#d90429", linestyle="--", linewidth=1.8,
             label="Perfect Prediction (1:1 Reference Line)")

    ax1.set_title(f"2025 Actual vs. 2024 Baseline Departures (N = {n_total:,} Station-Months)\n"
                  f"[Full-Season MAE: {mae_overall:.2f} trips/mo; WAPE: {wape_overall:.2f}%]",
                  fontsize=12, fontweight="bold", pad=10)
    ax1.set_xlabel("Predicted Departures: 2024 Same-Month Baseline (Thousands of Trips)", fontsize=10.5, fontweight="bold")
    ax1.set_ylabel("Actual Departures: 2025 Ground Truth (Thousands of Trips)", fontsize=10.5, fontweight="bold")
    ax1.set_xlim(0, max_val / 1000.0)
    ax1.set_ylim(0, max_val / 1000.0)
    ax1.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)
    ax1.grid(True)

    # Callout box on Panel A
    props = dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ced4da", alpha=0.95)
    callout_text = (
        "Evaluation Summary:\n"
        f"• Evaluated Records: {n_total:,} / 3,197 (99.16%)\n"
        "• Excluded Unmatched: 27 records (audited)\n"
        f"• Full-Season MAE: {mae_overall:.2f} trips/station·mo\n"
        f"• Full-Season WAPE: {wape_overall:.2f}%\n"
        "• May-Oct Cohort WAPE: 17.62% (MAE: 142.03)\n"
        "• Low-Demand Stations (Q1) WAPE: 33.83%\n"
        "• Pearson Correlation (r): 0.959"
    )
    ax1.text(0.97, 0.05, callout_text, transform=ax1.transAxes, fontsize=8.5,
             verticalalignment="bottom", horizontalalignment="right", bbox=props)

    # Panel B: Monthly MAE and WAPE Trajectories
    x_pos = np.arange(len(month_names))
    width = 0.45

    ax2_twin = ax2.twinx()
    bars = ax2.bar(x_pos, m_df["mae"], width=width, color="#2b5c8f", alpha=0.75, label="MAE (trips/stn·mo)")
    line = ax2_twin.plot(x_pos, m_df["wape"], color="#d90429", marker="o", linewidth=2.2, label="WAPE (%)")

    ax2.set_xlabel("Season Calendar Month", fontsize=10.5, fontweight="bold")
    ax2.set_ylabel("Mean Absolute Error (Trips / Station-Month)", fontsize=10.5, color="#1a365d", fontweight="bold")
    ax2_twin.set_ylabel("Weighted Absolute Percentage Error (WAPE %)", fontsize=10.5, color="#b71c1c", fontweight="bold")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(month_names, fontsize=9.5)
    ax2.set_ylim(0, 240)
    ax2_twin.set_ylim(0, 42)
    ax2.grid(axis="y")

    # Annotate bars
    for bar in bars:
        h = bar.get_height()
        ax2.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color="#1a365d")
    for i, w in enumerate(m_df["wape"]):
        ax2_twin.annotate(f"{w:.1f}%", xy=(i, w), xytext=(0, 6),
                          textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#b71c1c")

    ax2.set_title("Monthly Error Progression: Spring Shoulder vs. Autumn Stability\n"
                  "(April thaw volatile: WAPE 33.97% → September steady: WAPE 12.61%)", fontsize=12, fontweight="bold", pad=10)

    # Combined legend for Panel B
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True, facecolor="white", framealpha=0.9)

    fig.suptitle("Figure 7: 2025 Out-of-Time Demand Forecasting Performance: Actual vs. Historical Same-Month Baseline\n"
                 "(Evaluated on Complete 2025 Season; Baseline Model: ŷ(s,m,2025) = y(s,m,2024); Unit: Trips / Station-Month)",
                 fontsize=14, fontweight="bold", y=1.03)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "fig7_forecast_evaluation_actual_vs_baseline_2025.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Figure 7: {out_path}")


def main():
    """Main execution function generating all 7 figures."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_dir, "reports", "figures")
    ensure_output_dir(output_dir)

    print("=" * 70)
    print("HSL CITY BIKE PROJECT: GENERATING PUBLICATION FIGURES")
    print("=" * 70)
    print(f"Target Directory: {output_dir}")

    # Load primary datasets
    station_month_path = os.path.join(project_dir, "data", "processed", "station_month.csv")
    city_hourly_path = os.path.join(project_dir, "data", "processed", "city_hourly_summary.csv")
    station_intraday_path = os.path.join(project_dir, "data", "processed", "station_intraday_monthly.csv")

    raw_dir = os.path.join(project_dir, "data", "raw")
    processed_dir = os.path.join(project_dir, "data", "processed")

    if not os.path.exists(city_hourly_path) or not os.path.exists(station_intraday_path):
        print("Intraday tables missing. Checking for raw data to run aggregation...")
        try:
            from src.aggregate_intraday import run_intraday_aggregation
            run_intraday_aggregation(raw_dir, processed_dir)
        except Exception as err:
            print(f"[Warning] Could not auto-generate intraday data: {err}")

    for p in [station_month_path, city_hourly_path, station_intraday_path]:
        if not os.path.exists(p):
            print(f"[Error] Required dataset missing: {p}")
            print("Please execute 'python run_pipeline.py' first to download and build all datasets.")
            sys.exit(1)

    print("Loading datasets...")
    sm_df = pd.read_csv(station_month_path)
    ch_df = pd.read_csv(city_hourly_path)
    si_df = pd.read_csv(station_intraday_path)
    print(f"Datasets loaded successfully ({len(sm_df):,} station-months, {len(ch_df):,} city-hourly rows, {len(si_df):,} intraday rows).")

    # Generate all figures
    generate_figure_1(sm_df, output_dir)
    generate_figure_2(sm_df, output_dir)
    generate_figure_3(sm_df, output_dir)
    generate_figure_4(sm_df, output_dir)
    generate_figure_5(ch_df, output_dir)
    generate_figure_6(si_df, sm_df, output_dir)
    generate_figure_7(sm_df, output_dir)

    print("=" * 70)
    print("ALL 7 FIGURES SUCCESSFULLY GENERATED IN reports/figures/")
    print("=" * 70)


if __name__ == "__main__":
    main()
