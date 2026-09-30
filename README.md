# Seasonal and Weather-Based HSL City Bike Allocation

Student project based on [HSL_City_Bike_Project_Canvas.md](HSL_City_Bike_Project_Canvas.md).

The project studies how city-bike activity changes by station and month. The current
version creates a station-month dataset from the complete 2025 HSL cycling season,
integrates actual historical weather observations from the Finnish Meteorological
Institute (FMI), and highlights stations with large differences between departures and returns.

The intended audience is city-bike operators and HSL transport planners. The current
pipeline serves as a foundation for subsequent exploratory analysis, demand modeling,
and dashboard development.

## Project Status

**Completed:**

- Downloaded HSL city-bike trips for the complete 2025 season (April to October, 7 months).
- Downloaded official station metadata and WGS84 coordinates from HSL ArcGIS Open Data.
- Downloaded official daily weather observations from FMI Open Data for Helsinki Kaisaniemi and Espoo Tapiola.
- Filtered out invalid trip records using documented data quality rules.
- Aggregated departures, returns, net flow, and trip characteristics by station and month.
- Merged monthly weather indicators (mean, min, max temperature, total precipitation, rainy days) by municipality and month.
- Preserved missingness (`NaN`) for stations with unmapped municipality to avoid false precision.
- Validated pipeline integrity with automated unit tests (`tests/test_weather_integration.py`).
- Generated analytical summary charts and an interactive exploration notebook.

**Not implemented yet (out of current project scope):**

- Weather forecasts (the current pipeline strictly uses historical ground-truth actual observations).
- Multi-year comparisons (2024 or earlier data).
- Machine learning or predictive demand models.
- Interactive web dashboard.

---

## 1. Project Directory Structure

```text
HSL_City_Bike_Project/
├── HSL_City_Bike_Project_Canvas.md    # Original workshop mini-project canvas
├── README.md                          # Project documentation, data dictionaries & usage guide
├── requirements.txt                   # Python package dependencies
├── .gitignore                         # Git ignore rules for data and cache
├── run_pipeline.py                    # Master pipeline runner (download -> clean -> aggregate)
├── show_results.py                    # Analytical demonstration and summary chart exporter
├── data/
│   ├── raw/                           # Downloaded raw CSVs (trips, stations, FMI weather); excluded from git
│   └── processed/
│       ├── station_month.csv          # Primary analytical table (3,197 rows)
│       └── season_summary.png         # Analytical summary chart
├── notebooks/
│   └── station_month_demo.ipynb       # Interactive Jupyter notebook for EDA
├── tests/
│   └── test_weather_integration.py    # Unit tests for weather conventions, coverage & merge integrity
└── src/
    ├── __init__.py
    ├── download_data.py               # Downloader for HSL trips, station coordinates & FMI weather
    └── clean_and_aggregate.py         # Data cleaning, weather aggregation & station-month table generation
```

### What Each File Does

- `run_pipeline.py`: Runs downloading, cleaning, weather aggregation, and coordinate merging in one command.
- `src/download_data.py`: Downloads HSL trip CSVs, HSL ArcGIS station metadata, and FMI daily weather observations.
- `src/clean_and_aggregate.py`: Cleans raw trip records, aggregates monthly weather metrics, and builds `station_month.csv`.
- `tests/test_weather_integration.py`: Pytest suite verifying FMI precipitation conventions, field-by-field completeness, key uniqueness, and unmapped station handling.
- `show_results.py`: Prints analytical summaries (fleet activity, hotspots, rebalancing imbalances, weather overview) and exports charts.
- `notebooks/station_month_demo.ipynb`: Interactive Jupyter notebook for exploratory data analysis.
- `data/processed/station_month.csv`: Primary analytical dataset (one row per station and month).

---

## 2. Reliable Data Sources

### 2.1 HSL City Bike Origin-Destination (OD) Journey Data
* **Host / Publisher:** HSL (Helsingin seudun liikenne) & Helsinki Region Infoshare (HRI)
* **Direct Repository URL:** `https://dev.hsl.fi/citybikes/`
* **Format & Naming:** `od-trips-[year]/[year]-[month:02d].csv` (e.g., `https://dev.hsl.fi/citybikes/od-trips-2025/2025-05.csv`)
* **Coverage:** Complete 2025 cycling season (April 1 to October 31, 2025; 2,516,565 raw trips across 7 monthly files).
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).

### 2.2 HSL City Bike Station Coordinates & Metadata
* **Host / Publisher:** HSL Open Data / ArcGIS Online REST Feature Service
* **Feature Service Name:** `Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin`
* **Direct Query Endpoint:**
  ```text
  https://services1.arcgis.com/sswNXkUiRoWtrx0t/arcgis/rest/services/Helsingin_ja_Espoon_kaupunkipyöräasemat_avoin/FeatureServer/0/query?where=1%3D1&outFields=*&f=json
  ```
* **Coverage:** 457 active bike stations across Helsinki and Espoo with official IDs, English/Finnish/Swedish names, capacity, and WGS84 geographic coordinates.
* **License:** CC BY 4.0.

### 2.3 FMI Historical Weather Observations (Ilmatieteen laitos)
* **Host / Publisher:** Finnish Meteorological Institute (Ilmatieteen laitos, FMI) Open Data
* **Service Type:** WFS 2.0 Feature Service (`fmi::observations::weather::daily::simple`)
* **Endpoint URL:** `https://opendata.fmi.fi/wfs`
* **Representative Weather Stations:**
  - **Helsinki:** Helsinki Kaisaniemi (FMISID `100971`)
  - **Espoo:** Espoo Tapiola (FMISID `874863`)
* **Observed Daily Parameters:**
  - `tday`: Daily mean temperature (°C)
  - `tmin`: Daily minimum temperature (°C)
  - `tmax`: Daily maximum temperature (°C)
  - `rrday`: Daily precipitation (mm; FMI code `-1.0` = dry / no rain)
  - `snow`: Snow depth (cm; FMI code `-1.0` = no snow)
* **Time Granularity & Period:** Daily observations aggregated to monthly indicators from April 1 to October 31, 2025 (214 calendar days per station; 100% complete across all fields).
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).

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
Primary analytical unit: **Station-Month** (`station_id` × `year_month`). Total rows: **3,197**.

| Column Name | Data Type | Nullable | Description & Calculation |
| :--- | :--- | :---: | :--- |
| `year_month` | string | No | Observation month in format `YYYY-MM` (e.g. `2025-05`) |
| `station_id` | integer | No | Normalized station identifier (integer, leading zeros stripped) |
| `station_name` | string | Yes | Primary English / Finnish station name (from HSL ArcGIS service) |
| `city` | string | Yes | Municipality (`Helsinki` or `Espoo`; `NaN` if station not in official layer) |
| `capacity` | integer | Yes | Total bike docking capacity of the station |
| `latitude` | float | Yes | Station latitude in WGS84 coordinate reference system (EPSG:4326) |
| `longitude` | float | Yes | Station longitude in WGS84 coordinate reference system (EPSG:4326) |
| `departures` | integer | No | Total valid trips departing from this station in the month |
| `returns` | integer | No | Total valid trips returned to this station in the month |
| `net_flow` | integer | No | `returns - departures`. Positive = surplus (dock fill-up); Negative = deficit (bike depletion) |
| `total_trips` | integer | No | `departures + returns`. Overall station activity volume |
| `avg_distance_m` | float | No | Mean covered distance in meters for departing trips |
| `avg_duration_sec` | float | No | Mean duration in seconds for departing trips |
| `weather_station_id`| integer | Yes | FMI station FMISID (`100971` for Helsinki, `874863` for Espoo; `NaN` for unmapped stations) |
| `avg_temperature_c` | float | Yes | Monthly mean of daily average temperatures in °C |
| `min_temperature_c` | float | Yes | Monthly lowest daily minimum temperature in °C |
| `max_temperature_c` | float | Yes | Monthly highest daily maximum temperature in °C |
| `total_precipitation_mm` | float | Yes | Monthly cumulative precipitation in mm (FMI `-1.0` converted to 0.0 mm) |
| `rainy_days_count` | integer | Yes | Number of days in the month with daily precipitation $\ge$ 1.0 mm |

---

## 4. Data Quality, Cleaning Rules & Weather Handling

### 4.1 Trip Record Filtering Rules
Raw journey records are filtered using standard mobility data quality criteria:
1. **Duration Filter**: `10 <= Duration (sec.) <= 86,400 (24h)`  
   * Rationale: Trips <10s represent immediate re-docking due to faulty bikes, flat tires, or user errors. Trips >24h represent unreturned, lost, or maintenance transfers.
2. **Distance Filter**: `Covered distance (m) >= 10`  
   * Rationale: Removes stationary checkout tests or dock-sensor glitches.
3. **Speed Filter**: `Covered distance / Duration <= 10.0 m/s` (~36 km/h)  
   * Rationale: Mechanically powered or pedal-assist bikes exceeding 36 km/h reflect vehicular transport or GPS measurement errors.
4. **Timestamp Chronology**: `Return >= Departure`  
   * Rationale: Discards corrupt records where return precedes departure.
5. **Station ID Normalization**: Leading zeros in IDs (e.g. `"031"` vs `31`) are converted to standard integers to guarantee consistent joins.

### 4.2 FMI Weather Observations Handling
1. **Timezone Conversion**: Raw FMI observation timestamps in UTC are converted to local Finnish time (`Europe/Helsinki`, EEST in summer, EET in shoulder periods) to match trip activity dates.
2. **Official FMI Precipitation Code (`-1.0`)**:  
   * According to official FMI standards, `-1.0` in `rrday` denotes *"ei ole satanut"* (no rain / dry conditions, 0.0 mm).
   * `0.0` represents trace precipitation (< 0.1 mm).
   * Values of `-1.0` are converted to `0.0` mm for cumulative monthly precipitation calculations.
   * Days with daily precipitation $\ge$ 1.0 mm are classified as meteorological rainy days.
   * True missing values (`NaN`) are preserved as `NaN`.
3. **Field-by-Field Coverage Validation**: Completeness is independently checked for every parameter (`tday`, `tmin`, `tmax`, `rrday`, `snow`) for each representative station. In the 2025 season, all 5 parameters have 100% coverage (214/214 days, 0 missing).
4. **Preservation of Missingness for Unmapped Stations**:  
   * Seven stations (IDs 626, 710, 716, 754, 768, 997, 999; representing 45 station-month rows) are not present in the official HSL ArcGIS station layer (often internal workshop, depot, or test stations).
   * Because their municipality and geographic coordinates are unknown, **weather metrics are kept as `NaN`** rather than arbitrarily assigned to Helsinki. This avoids false precision and unwarranted assumptions.
5. **Historical Observations vs. Forecasts (Non-Causal Disclaimer)**:  
   * Weather metrics represent **historical actual observations** from official ground stations, **not weather forecasts**.
   * While seasonal temperature and rainfall patterns correlate with cycling activity, this project **does not claim a direct causal relationship**. Ridership is influenced by multi-factor seasonality, daylight duration, work/vacation schedules, and public transit alternatives.

---

## 5. How to Reproduce Results

### Prerequisites
Ensure Python 3.10+ is installed with the required packages:
```powershell
pip install -r requirements.txt
```

### Full Pipeline Run (Download + Clean + Aggregate)
To download the 2025 raw trip and weather data, clean records, and build `station_month.csv`:
```powershell
python run_pipeline.py
```

### Offline / Fast Processing (Using Existing Raw Data)
If raw CSVs already exist in `data/raw/`:
```powershell
python run_pipeline.py --skip-download
```

### Run Automated Weather Tests
To verify FMI precipitation handling, field completeness, and merge integrity:
```powershell
python -m pytest tests/test_weather_integration.py -v
```

### Display Analytical Results & Export Charts
To print summary statistics and generate [`season_summary.png`](data/processed/season_summary.png):
```powershell
python show_results.py
```

---

## 6. Next Steps

- Explore multi-year comparisons (2024 or earlier seasons).
- Feature engineering for station-level demand forecasting.
- Interactive visualization and planning dashboard for fleet rebalancing.
