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
- Comparison with 2024 or earlier data. **This is an option for discussion, not a current project requirement.**
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

The current result uses the 2025 season. If Python and the required packages are
already available, collaborators only need to run these commands from the project
root:

```powershell
python run_pipeline.py
python show_results.py
```

`run_pipeline.py` downloads the 2025 data, cleans it, and creates:

```text
data/processed/station_month.csv
```

`show_results.py` prints the summary and creates:

```text
data/processed/season_summary.png
```

If the required packages are not installed, run this once first:

```powershell
pip install -r requirements.txt
```

If the raw data has already been downloaded, use:

```powershell
python run_pipeline.py --skip-download
python show_results.py
```

The raw CSV files are large and are not uploaded to GitHub. Running the pipeline
downloads them from the official HSL source.

## Next Steps

- Discuss whether to add 2024 or earlier data.
- Consider adding FMI weather data.
- Consider a simple demand prediction model and an interactive dashboard.

Data source: HSL, City Bike Finland, and Helsinki Region Infoshare. The project uses
station-level and monthly aggregated data and does not publish individual rider
identities.

