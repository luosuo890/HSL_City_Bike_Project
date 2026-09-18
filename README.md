# Seasonal and Weather-Based HSL City Bike Allocation

Student project based on [HSL_City_Bike_Project_Canvas.md](HSL_City_Bike_Project_Canvas.md).

The project studies how city-bike activity changes by station and month. The current
version creates a station-month dataset from the complete 2025 HSL cycling season and
highlights stations with large differences between departures and returns.

The intended audience is city-bike operators and HSL transport planners. The current
pipeline is a foundation for the later weather analysis, forecasting, and dashboard
work described in the canvas.

## Project Status

Completed:

- Downloaded HSL city-bike trips for April-October 2025.
- Downloaded official station metadata and coordinates.
- Removed clearly invalid trip records using documented rules.
- Aggregated departures and returns by station and month.
- Calculated station activity and net flow measures.
- Generated a summary chart and an interactive exploration notebook.

Not implemented yet:

- FMI weather data and weather forecasts.
- Comparison with additional years such as 2024.
- Machine-learning or next-month demand forecasting.
- Interactive planning dashboard.

---

## 1. Project Directory Structure

```text
HSL_City_Bike_Project/
├── HSL_City_Bike_Project_Canvas.md    # Original workshop mini-project canvas
├── README.md                          # Project documentation, data dictionary & usage guide
├── requirements.txt                   # Python package dependencies
├── .gitignore                         # Git ignore rules for data and cache
├── run_pipeline.py                    # Master pipeline runner (download -> clean -> aggregate)
├── show_results.py                    # Analytical demonstration and summary chart exporter
├── data/
│   ├── raw/                           # Downloaded data; excluded from GitHub
│   └── processed/                     # Generated outputs; excluded by default
├── notebooks/
│   └── station_month_demo.ipynb       # Interactive Jupyter notebook for EDA
└── src/
    ├── __init__.py
    ├── download_data.py               # Robust multi-source data downloader
    └── clean_and_aggregate.py         # Data quality cleaning and station-month aggregation logic
```

## What Each File Does

- `run_pipeline.py`: runs downloading, cleaning, aggregation, and coordinate merging.
- `src/download_data.py`: downloads HSL trip files and station metadata.
- `src/clean_and_aggregate.py`: cleans trip records and creates the station-month table.
- `show_results.py`: prints summary statistics and exports charts.
- `notebooks/station_month_demo.ipynb`: provides an interactive exploration of the output.
- `data/processed/station_month.csv`: one row per station and month after processing.

---

## 2. Reliable Data Sources

### 2.1 HSL City Bike Origin-Destination (OD) Journey Data
* **Host / Publisher:** HSL (Helsingin seudun liikenne) & Helsinki Region Infoshare (HRI)
* **Direct Repository URL:** `https://dev.hsl.fi/citybikes/`
* **Format & Naming:** `od-trips-[year]/[year]-[month:02d].csv` (e.g., `https://dev.hsl.fi/citybikes/od-trips-2025/2025-05.csv`)
* **Coverage:** The current checked dataset uses April-October 2025. Other available seasons can be downloaded with the pipeline.
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).

### 2.2 HSL City Bike Station Coordinates & Metadata
* **Host / Publisher:** HSL Open Data / ArcGIS Online REST Feature Service
* **Feature Service Name:** `Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin`
* **Direct Query Endpoint:**
  ```
  https://services1.arcgis.com/sswNXkUiRoWtrx0t/arcgis/rest/services/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin/FeatureServer/0/query?where=1%3D1&outFields=*&f=json
  ```
* **Coverage:** 457 active bike stations across Helsinki and Espoo with official IDs, English/Finnish/Swedish names, capacity, and WGS84 geographic coordinates.
* **License:** CC BY 4.0.

---

## 3. Data Dictionaries

### 3.1 Raw Trip CSV Schema
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `Departure` | string (ISO 8601) | Timestamp when the bike was unlocked from the origin dock (e.g. `2025-05-31T23:59:58`) |
| `Return` | string (ISO 8601) | Timestamp when the bike was locked into the destination dock (e.g. `2025-06-01T00:03:23`) |
| `Departure station id` | string / int | Numeric ID of the departure station (e.g. `511`, `018`) |
| `Departure station name` | string | Station name in Finnish / Swedish (e.g. `Sateentie`, `Porthania`) |
| `Return station id` | string / int | Numeric ID of the return station (e.g. `519`, `012`) |
| `Return station name` | string | Return station name in Finnish / Swedish |
| `Covered distance (m)` | float / int | Distance traversed during the trip measured in meters |
| `Duration (sec.)` | int | Total trip duration measured in seconds |

### 3.2 Processed Analytical Table: `data/processed/station_month.csv`
Primary analytical unit: **Station-Month** (`station_id` × `year_month`).

| Column Name | Data Type | Description & Calculation |
| :--- | :--- | :--- |
| `year_month` | string | Observation month in format `YYYY-MM` (e.g. `2025-05`) |
| `station_id` | integer | Unique identifier of the bike station (normalized without leading zeros) |
| `station_name` | string | Official English / primary name of the station |
| `city` | string | Municipality (`Helsinki` or `Espoo`) |
| `capacity` | integer | Total bike docking capacity of the station |
| `latitude` | float | Latitude in WGS84 coordinate reference system (EPSG:4326) |
| `longitude` | float | Longitude in WGS84 coordinate reference system (EPSG:4326) |
| `departures` | integer | Total valid completed trips departing from this station in the month |
| `returns` | integer | Total valid completed trips returned to this station in the month |
| `net_flow` | integer | `returns - departures`. **Positive** = bike accumulation (surplus); **Negative** = bike depletion (deficit) |
| `total_trips` | integer | `departures + returns`. Overall activity volume indicator |
| `avg_distance_m` | float | Mean covered distance in meters for departing trips |
| `avg_duration_sec` | float | Mean duration in seconds for departing trips |

---

## 4. Data Quality & Trip Cleaning Rules

The raw trip records are filtered using industry-standard HSL mobility data criteria:

1. **Duration Filter**: `10 <= Duration (sec.) <= 86,400 (24h)`  
   * Rationale: Trips <10s represent immediate re-docking due to faulty bikes, flat tires, or user errors. Trips >24h represent unreturned, lost, or maintenance transfers.
2. **Distance Filter**: `Covered distance (m) >= 10`  
   * Rationale: Filters out stationary checkout tests or dock-sensor glitches.
3. **Speed Filter**: `Covered distance / Duration <= 10.0 m/s` (~36 km/h)  
   * Rationale: City bikes are pedal-assist or mechanical; sustained speeds above 36 km/h indicate motorized vehicle transport or GPS measurement errors.
4. **Timestamp Chronology**: `Return >= Departure`  
   * Rationale: Discards any corrupt records where arrival precedes departure.
5. **ID Normalization**: Leading zeros in IDs (e.g. `"031"` vs `31`) are stripped into integers to guarantee 100% join consistency with station coordinates.

---

## 5. Reproduce the Current Results

### Prerequisites
Install Python 3.9+ and required packages:
The commands below reproduce the current 2025 station-month result from a fresh clone.

### Prerequisites

Use Python 3.9 or newer. From the project root, create and activate a virtual environment:

```
python -m venv .venv
.venv\Scripts\Activate.ps1

### Option A: One-Click End-to-End Execution (Recommended)
Downloads the latest **2025 season (April–October)**, cleans trips, merges station coordinates, and writes `data/processed/station_month.csv`:
If PowerShell blocks script activation, run the pipeline with the virtual environment's
Python directly instead:

```powershell
.venv\Scripts\python.exe run_pipeline.py
```

### Run the 2025 pipeline

This downloads April-October 2025, cleans the trips, merges station coordinates, and
writes `data/processed/station_month.csv`:

```

### Option B: Download Other Years or Full History
To download a specific year (e.g. 2024):
Generate the console summary and chart:

```powershell
python show_results.py
```

The main outputs are:

```text
data/processed/station_month.csv
data/processed/season_summary.png
```

### Process another year

To download and process a specific year, for example 2024:

```

To download and process all 8 historical cycling seasons (2016–2025, ~1.84 GB):
```powershell
To process already downloaded raw files without downloading again:

```powershell
python run_pipeline.py --skip-download
```

To download and process all available seasons from 2016 to 2025:

```

### Option C: Re-run Processing Without Re-downloading
If raw data is already downloaded in `data/raw/`:
The `--all` option downloads a large amount of data. It is not necessary for the
current student-project result.

### Open the notebook

```powershell
jupyter notebook notebooks/station_month_demo.ipynb
```

## Data Policy and GitHub Repository

Raw HSL CSV files are not included in this repository because they are large. The
pipeline downloads them from the official HSL source when it is run. The `data/raw/`
and `data/processed/` directories are ignored by Git by default.

This means that a new user should run `python run_pipeline.py` before opening the
notebook or running `show_results.py`. If a small processed result is intentionally
shared as a reference output, it can be added explicitly with:
```

git add -f data/processed/station_month.csv data/processed/season_summary.png
Run the reporting script to view console analytics and generate summary graphs:
```powershell
Do not commit raw CSV files, virtual environments, API keys, passwords, or local
absolute paths.

### 6.1 Core Assumptions
1. **Operating Season**: The current dataset covers the months available in the 2025 files (April-October). Months without an operating file must not be interpreted as zero demand.
2. **Rebalancing Flow Interpretation**: `net_flow = returns - departures`. A station with a strongly negative net flow consistently runs out of bikes (commuter origins), while a station with strongly positive net flow runs out of empty docks (commuter destinations).
3. **Spatial Homogeneity**: Stations without GPS coordinates in historical years will be retained with null coordinates rather than dropped, preserving aggregate trip counts.

### 6.2 Data Licenses & Privacy
* **License**: Data is provided by **City Bike Finland** and **HSL** under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
* **Attribution**: "Source: HSL, City Bike Finland, Helsinki Region Infoshare".
* **Data Privacy**: Only station-level and monthly aggregated statistics are stored in processed datasets. Individual rider trajectories or personal identifiable information (PII) are never stored or exposed.

### 6.3 Open Questions & Future Roadmap (Per Canvas)
* **Weather Data Integration**: Next step is to fetch FMI (Finnish Meteorological Institute) weather observation parameters (`t2m` air temperature, `r_1h` precipitation, `ws_10min` wind speed) and join them to `station_month.csv`.
* **Predictive Modeling**: Implement baseline models (previous year same-month) and tree-based regression (e.g. Random Forest / LightGBM) to forecast next-month departures and returns.
* **Allocation Dashboard**: Build a Streamlit / Dash web interface allowing planners to inspect priority lists for truck redistribution.

## Limitations

- The current analysis uses one complete season, 2025.
- `net_flow` describes the difference between recorded returns and departures; it is
   not a direct measurement of the number of bikes physically available at a station.
- The current station metadata represents the latest downloaded station information,
   so historical station changes are not yet versioned.
- Weather effects and future demand are not included in the current output.

## Suggested Team Workflow

1. Start with the 2025 pipeline and verify the generated station-month table.
2. Add 2024 data for a year-over-year comparison.
3. Add FMI weather observations and document the date/time matching method.
4. Compare a simple previous-year baseline with a regression model.
5. Build the dashboard and allocation-priority explanation after the data pipeline is stable.

When adding a new analysis, please document the data source, assumptions, and command
needed to reproduce it in this README or in the `notebooks/` folder.

