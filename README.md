# Seasonal and Weather-Based HSL City Bike Allocation

Student project based on [HSL_City_Bike_Project_Canvas.md](HSL_City_Bike_Project_Canvas.md).
The Technical Report: [reports/HSL_City_Bike_Technical_Final_Report.pdf]

The project investigates how city-bike travel demand changes by station, month, day type, and time of day across the Helsinki Capital Region (Helsinki and Espoo). The current repository creates a unified station-month dataset covering two complete HSL cycling seasons (**2024 and 2025**, April 1 to October 31 each; 14 months total), integrates actual historical weather observations from the Finnish Meteorological Institute (FMI), and generates publication-quality static figures and reports for course presentation and GitHub documentation.

The intended audience is city-bike operators and HSL transport planners. The project serves as an empirical foundation for exploratory analysis, predictive demand modeling, and rebalancing triage.

---

## Project Status

**Completed Deliverables:**

- **Multi-Season Data Pipeline**: Downloaded, filtered, and aggregated HSL journey records across two complete cycling seasons: **2024 and 2025** (~5.10M raw trips, **4,951,245 valid trips**, 97.04% retention).
- **Station Metadata & GIS Mapping**: Integrated official HSL ArcGIS layer covering 457 stations with dock capacity and WGS84 geographic coordinates.
- **FMI Weather Ground Truth**: Downloaded daily historical weather observations for Helsinki Kaisaniemi and Espoo Tapiola across both seasons (428 days per station; 100% complete across mean/min/max temperature, precipitation, and snow depth).
- **Rigorous Data Quality Filters**: Applied documented duration ($10\text{s} \le t \le 24\text{h}$), distance ($\ge 10\text{m}$), speed ($\le 10\text{ m/s}$), and chronology constraints.
- **Audited Unmapped Stations**: 4 stations in 2024 (26 rows) and 7 in 2025 (45 rows) preserved with municipality and coordinates as `NaN` without silent imputation.
- **Automated Integration Tests**: Validated precipitation conventions, completeness, key uniqueness, and metadata joins (`tests/test_weather_integration.py`).
- **Exploratory Data Analysis**:
  - Daily ridership and FMI weather correlations ([`notebooks/weather_eda.ipynb`](notebooks/weather_eda.ipynb)).
  - Weekday vs. weekend diurnal profiles and morning/evening peak asymmetry ([`notebooks/intraday_traffic_eda.ipynb`](notebooks/intraday_traffic_eda.ipynb)).
- **Predictive Demand Modeling**:
  - Historical same-month baseline demand forecasting ([`notebooks/demand_baseline.ipynb`](notebooks/demand_baseline.ipynb)).
  - Methodologically leakage-free within-season model comparison (Baseline vs. Ridge vs. Decision Tree; [`notebooks/model_comparison.ipynb`](notebooks/model_comparison.ipynb)).
- **Static Publication Figures Gallery**: Dedicated script ([`src/generate_figures.py`](src/generate_figures.py)) generating 7 high-resolution static charts in [`reports/figures/`](reports/figures/).
- **Consolidated Findings Report**: End-to-end report documenting research questions, empirical findings, model evaluations, station triage, and limitations ([`reports/findings.md`](reports/findings.md)).

**Methodological Scope & Disclaimers:**

- **Historical Actual Weather, Not Forecasts**: Weather features strictly represent retrospective ground-truth observations from FMI stations, not weather forecasts.
- **Descriptive Associations, Not Causality**: Observed weather correlations reflect seasonal co-movement (daylight, holidays, temperature) and do not establish direct causality.
- **Forecast Error Unit**: Mean Absolute Error (MAE) is measured in **trips per station-month**, not physical bicycles.
- **Macro Directional Drift**: Monthly `net_flow = returns - departures` reflects 30-day directional passenger drift, not real-time dock inventory or required van dispatch workloads.
- **Single Out-of-Time Backtest**: Evaluating on 2025 represents a single backtest sample. Metrics are exploratory reference benchmarks, not formal confidence intervals.
- **Partial Q4 Window**: The cycling season closes on October 31, meaning Q4 contains only October (1 month).

---

## 1. Project Directory Structure

```text
HSL_City_Bike_Project/
├── HSL_City_Bike_Project_Canvas.md    # Original workshop mini-project canvas
├── README.md                          # Project documentation, data dictionaries & reproduction guide
├── requirements.txt                   # Python dependencies (pandas, scikit-learn, matplotlib, etc.)
├── .gitignore                         # Git ignore rules for raw data and cache
├── run_pipeline.py                    # Master pipeline runner (download -> clean -> aggregate)
├── show_results.py                    # Analytical demonstration and summary chart exporter
├── data/
│   ├── raw/                           # Raw CSVs (trips 2024/2025, stations, weather); excluded from git
│   └── processed/
│       ├── station_month.csv          # Primary analytical table (6,395 rows, 14 months)
│       ├── station_intraday_monthly.csv # Hourly profile by station & day-type (270k rows)
│       ├── city_hourly_summary.csv    # City-level hourly breakdown
│       ├── intraday_audit_metrics.json# Data quality audit for intraday trips
│       └── season_summary.png         # Analytical summary chart
├── reports/
│   ├── findings.md                    # Comprehensive findings report for course presentation & GitHub
│   └── figures/                       # Publication-quality static figures gallery
│       ├── fig1_monthly_ridership_comparison_2024_2025.png
│       ├── fig2_station_month_demand_heatmap.png
│       ├── fig3_station_net_flow_map.png
│       ├── fig4_top_deficit_surplus_stations.png
│       ├── fig5_hourly_departure_curves_weekday_weekend.png
│       ├── fig6_morning_vs_evening_peak_station_comparison.png
│       └── fig7_forecast_evaluation_actual_vs_baseline_2025.png
├── notebooks/
│   ├── station_month_demo.ipynb       # Interactive notebook for single-season EDA
│   ├── weather_eda.ipynb              # Daily trip volume & weather correlation analysis notebook
│   ├── demand_baseline.ipynb          # Historical same-month baseline demand forecasting
│   ├── model_comparison.ipynb         # Leakage-free within-season model comparison (Solution B)
│   └── intraday_traffic_eda.ipynb     # Weekday/weekend & peak-hour intraday analysis notebook
├── tests/
│   └── test_weather_integration.py    # Unit tests for weather conventions, coverage & merge integrity
└── src/
    ├── __init__.py
    ├── download_data.py               # Downloader for HSL trips, station coordinates & FMI weather
    ├── clean_and_aggregate.py         # Data cleaning, weather aggregation & station-month table generation
    └── generate_figures.py            # Static figure generation pipeline for presentation and reports
```

### What Each File Does

- `run_pipeline.py`: Downloads, cleans, and aggregates HSL journeys and FMI weather across 2024 and 2025 into `station_month.csv`.
- `src/generate_figures.py`: Generates all 7 publication-quality static figures in `reports/figures/`.
- `reports/findings.md`: Comprehensive project report structured by research questions, methodology, empirical findings, models, triage, and limitations.
- `src/download_data.py`: Downloads HSL trip CSVs (2024 & 2025), ArcGIS station metadata, and FMI daily weather observations.
- `src/clean_and_aggregate.py`: Cleans raw trip records, aggregates monthly weather metrics, and builds analytical tables.
- `tests/test_weather_integration.py`: Pytest suite verifying FMI precipitation conventions, parameter completeness, key uniqueness, and unmapped station handling.
- `show_results.py`: Prints analytical summaries across 14 months and exports `season_summary.png`.
- `notebooks/weather_eda.ipynb`: Daily ridership vs. FMI weather observations.
- `notebooks/demand_baseline.ipynb`: 2024 same-month baseline predicting 2025 out-of-time demand.
- `notebooks/model_comparison.ipynb`: Compares Same-Month Baseline, Ridge Regression, and Decision Tree under causal within-season lag features (months 5–10).
- `notebooks/intraday_traffic_eda.ipynb`: Evaluates weekday vs. weekend ridership, morning/evening peak asymmetry, and municipal differences.

---

## 2. Reliable Data Sources

### 2.1 HSL City Bike Origin-Destination (OD) Journey Data
* **Host / Publisher:** HSL (Helsingin seudun liikenne) & Helsinki Region Infoshare (HRI)
* **Direct Repository URL:** `https://dev.hsl.fi/citybikes/`
* **Format & Naming:** `od-trips-[year]/[year]-[month:02d].csv`
* **Coverage:** Complete 2024 and 2025 cycling seasons (April 1 to October 31 each year; 14 monthly files total).
  - **2024 Season:** 2,585,668 raw trips $\rightarrow$ 2,507,175 clean trips (96.96% retention).
  - **2025 Season:** 2,516,565 raw trips $\rightarrow$ 2,444,070 clean trips (97.12% retention).
  - **Total:** 5,102,233 raw trips $\rightarrow$ **4,951,245 clean trips** (97.04% retention).
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).

### 2.2 HSL City Bike Station Coordinates & Metadata
* **Host / Publisher:** HSL Open Data / ArcGIS Online REST Feature Service
* **Feature Service Name:** `Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin`
* **Direct Query Endpoint:**
  ```text
  https://services1.arcgis.com/sswNXkUiRoWtrx0t/arcgis/rest/services/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin/FeatureServer/0/query?where=1%3D1&outFields=*&f=json
  ```
* **Coverage:** 457 active bike stations across Helsinki and Espoo with official IDs, English/Finnish/Swedish names, capacity, and WGS84 coordinates.
* **License:** CC BY 4.0.

### 2.3 FMI Historical Weather Observations (Ilmatieteen laitos)
* **Host / Publisher:** Finnish Meteorological Institute (Ilmatieteen laitos, FMI) Open Data
* **Service Type:** WFS 2.0 Feature Service (`fmi::observations::weather::daily::simple`)
* **Endpoint URL:** `https://opendata.fmi.fi/wfs`
* **Representative Stations:** Helsinki Kaisaniemi (FMISID `100971`) and Espoo Tapiola (FMISID `874863`).
* **Observed Daily Parameters:** Mean temperature (`tday`), minimum temperature (`tmin`), maximum temperature (`tmax`), precipitation (`rrday`), snow depth (`snow`).
* **Time Granularity & Coverage:** Daily observations from April 1 to October 31 for both 2024 and 2025 (428 total days per station; 100% complete across all 5 parameters).
* **License:** CC BY 4.0.

---

## 3. Processed Analytical Tables & Schema

### `data/processed/station_month.csv`
Primary analytical unit: **Station-Month** (`station_id` × `year_month`). Total rows: **6,395** (3,198 in 2024, 3,197 in 2025).

| Column Name | Data Type | Nullable | Description & Calculation |
| :--- | :--- | :---: | :--- |
| `year_month` | string | No | Observation month in format `YYYY-MM` (14 months: `2024-04` to `2025-10`) |
| `station_id` | integer | No | Normalized station identifier (integer, leading zeros stripped) |
| `station_name` | string | Yes | Primary English / Finnish station name |
| `city` | string | Yes | Municipality (`Helsinki` or `Espoo`; `NaN` if station not in official layer) |
| `capacity` | integer | Yes | Total bike docking capacity of the station |
| `latitude` | float | Yes | Station latitude in WGS84 coordinate reference system (EPSG:4326) |
| `longitude` | float | Yes | Station longitude in WGS84 coordinate reference system (EPSG:4326) |
| `departures` | integer | No | Total valid trips departing from this station in the month |
| `returns` | integer | No | Total valid trips returned to this station in the month |
| `net_flow` | integer | No | `returns - departures`. Positive = surplus; Negative = deficit |
| `total_trips` | integer | No | `departures + returns`. Overall station activity volume |
| `avg_distance_m` | float | No | Mean covered distance in meters for departing trips |
| `avg_duration_sec` | float | No | Mean duration in seconds for departing trips |
| `weather_station_id`| integer | Yes | FMI station FMISID (`100971` for Helsinki, `874863` for Espoo; `NaN` for unmapped) |
| `avg_temperature_c` | float | Yes | Monthly mean of daily average temperatures in °C |
| `min_temperature_c` | float | Yes | Monthly lowest daily minimum temperature in °C |
| `max_temperature_c` | float | Yes | Monthly highest daily maximum temperature in °C |
| `total_precipitation_mm` | float | Yes | Monthly cumulative precipitation in mm (FMI `-1.0` converted to 0.0 mm) |
| `rainy_days_count` | integer | Yes | Number of days in the month with daily precipitation $\ge$ 1.0 mm |

---

## 4. How to Reproduce Results

### Prerequisites
Install Python 3.10+ and the required packages:
```powershell
pip install -r requirements.txt
```

### 1. Execute Full Automated Data Pipeline
Downloads missing 2024 and 2025 raw trip and weather data, cleans records, and builds `station_month.csv`, `station_intraday_monthly.csv`, and `city_hourly_summary.csv`:
```powershell
python run_pipeline.py
```
*(Use `python run_pipeline.py --skip-download` to skip re-downloading existing raw files. You can also run `python src/aggregate_intraday.py` independently to regenerate intraday tables.)*

### 2. Run Automated Integration & Integrity Tests
Verifies FMI precipitation conventions, completeness across both seasons, key uniqueness, and unmapped dock audit:
```powershell
python -m pytest tests/test_weather_integration.py -v
```

### 3. Generate Publication-Quality Static Figures
Generates all 7 presentation figures in `reports/figures/`:
```powershell
python src/generate_figures.py
```

### 4. Display Summary Analytics
Prints summary tables and exports `season_summary.png`:
```powershell
python show_results.py
```

### 5. Execute Analysis & Modeling Notebooks
```powershell
jupyter nbconvert --to notebook --execute notebooks/weather_eda.ipynb
jupyter nbconvert --to notebook --execute notebooks/demand_baseline.ipynb
jupyter nbconvert --to notebook --execute notebooks/model_comparison.ipynb
jupyter nbconvert --to notebook --execute notebooks/intraday_traffic_eda.ipynb
```

---

## 5. Static Figures Gallery

All figures are saved in [`reports/figures/`](reports/figures/) with clear titles, axis labels, statistical granularity, and units:

| Figure File | Title & Description | Key Insights & Theme |
| :--- | :--- | :--- |
| [`fig1_monthly_ridership_comparison_2024_2025.png`](reports/figures/fig1_monthly_ridership_comparison_2024_2025.png) | **Monthly Ridership Dynamics Across 2024 and 2025** | System-wide monthly departures and municipal trajectory (Helsinki ~89% vs. Espoo ~11%). |
| [`fig2_station_month_demand_heatmap.png`](reports/figures/fig2_station_month_demand_heatmap.png) | **Station-Month Demand Intensity Heatmap** | Matrix heatmap tracking the Top 30 busiest bike stations across all 14 months. |
| [`fig3_station_net_flow_map.png`](reports/figures/fig3_station_net_flow_map.png) | **Spatial Distribution of Directional Net Flow** | Zero-centered diverging map of 454 coordinate stations showing macro deficit sinks vs. surplus sources. |
| [`fig4_top_deficit_surplus_stations.png`](reports/figures/fig4_top_deficit_surplus_stations.png) | **Persistent Macro Rebalancing Imbalances** | Top 10 Deficit Stations (bike sinks) vs. Top 10 Surplus Stations (dock saturation) with dock capacity. |
| [`fig5_hourly_departure_curves_weekday_weekend.png`](reports/figures/fig5_hourly_departure_curves_weekday_weekend.png) | **Hourly Departure Dynamics: Weekday vs. Weekend** | Operating-day normalized diurnal curves for Helsinki and Espoo; morning vs. evening rush asymmetry. |
| [`fig6_morning_vs_evening_peak_station_comparison.png`](reports/figures/fig6_morning_vs_evening_peak_station_comparison.png) | **Morning Peak vs. Evening Peak Station Comparison** | Diurnal commuter tidal reversal: residential feeders vs. employment/transit centers. |
| [`fig7_forecast_evaluation_actual_vs_baseline_2025.png`](reports/figures/fig7_forecast_evaluation_actual_vs_baseline_2025.png) | **2025 Demand Forecasting Performance (Actual vs. Baseline)** | Scatter plot against 1:1 line ($N=3,170$, MAE 147.60 trips/mo, WAPE 19.23%) and monthly error curves. |

---

## 6. Key Project Findings Summary

1. **Intraday Commuter Asymmetry**:
   - Weekday demand is **23%–29% higher** than weekend demand (Helsinki: 10,708–10,985 vs. 8,530–8,679 trips/day).
   - Weekdays exhibit a classic bimodal commute curve, while weekends follow a unimodal midday plateau (12:00–17:00).
   - **The evening peak (16:00–18:00) is 70%–105% higher than the morning peak (07:00–09:00)** across both cities, consistent with homeward commutes coinciding with social and leisure trips. This suggests an operational hypothesis for planners to consider pre-staging rebalancing operations prior to the afternoon surge (e.g., before 15:30), though definitive dispatch rules require real-time dock occupancy data.
2. **Commuter Tidal Reversal**:
   - Stations in residential clusters (e.g., *Sompasaari*) face severe deficits in the morning as residents leave, but reverse into massive surplus accumulators in the evening as riders return.
   - Employment hubs (e.g., *Salmisaarenranta*) accumulate bikes in the morning and experience severe deficits in the evening.
3. **Forecasting Model Benchmark**:
   - **Historical Same-Month Baseline achieves the lowest volume error in this evaluation** (Full Season: MAE 147.60 trips/mo, WAPE 19.23%; May–Oct Cohort: MAE 141.88 trips/mo, WAPE 17.58%). Preceding-month lag models suffer from transitional delay across Nordic seasonal shifts.
   - **Ridge Regression excels at early/mid-season deficit rank ordering** (capturing 65%–80% of top deficit stations in May–August, $\rho$ up to 0.761), but severely overpredicts low-volume stations (124% WAPE on Q1).
   - No single model is universally best; planners should use the baseline for fleet sizing and Ridge rankings for commuter sink triage.
4. **Detailed Analysis Report**:
   - For complete methodological discussions, data audits, station triage tables, and limitations, refer to [`reports/findings.md`](reports/findings.md).
