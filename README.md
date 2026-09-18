# Seasonal and Weather-Based HSL City Bike Allocation

> **A student course data pipeline project based on [HSL_City_Bike_Project_Canvas.md](HSL_City_Bike_Project_Canvas.md)**  
> **Target Audience:** City bike operators and HSL transport planners.  
> **Key Goal:** Quantify monthly station usage, flow imbalances (departures vs. returns), and identify bike allocation and redistribution priorities across Helsinki and Espoo.

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
│   ├── raw/                           # Raw unmodified CSVs (stations.csv, 2025-04.csv ... 2025-10.csv)
│   └── processed/
│       ├── station_month.csv          # Primary aggregated analytical table
│       └── season_summary.png         # Generated analytical summary visualization
├── notebooks/
│   └── station_month_demo.ipynb       # Interactive Jupyter notebook for EDA
└── src/
    ├── __init__.py
    ├── download_data.py               # Robust multi-source data downloader
    └── clean_and_aggregate.py         # Data quality cleaning and station-month aggregation logic
```

---

## 2. Reliable Data Sources

### 2.1 HSL City Bike Origin-Destination (OD) Journey Data
* **Host / Publisher:** HSL (Helsingin seudun liikenne) & Helsinki Region Infoshare (HRI)
* **Direct Repository URL:** `https://dev.hsl.fi/citybikes/`
* **Format & Naming:** `od-trips-[year]/[year]-[month:02d].csv` (e.g., `https://dev.hsl.fi/citybikes/od-trips-2025/2025-05.csv`)
* **Coverage:** Complete monthly records for all cycling seasons from 2016 through 2025.
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

## 5. How to Run the Pipeline

### Prerequisites
Install Python 3.9+ and required packages:
```powershell
pip install -r requirements.txt
```

### Option A: One-Click End-to-End Execution (Recommended)
Downloads the latest **2025 season (April–October)**, cleans trips, merges station coordinates, and writes `data/processed/station_month.csv`:
```powershell
python run_pipeline.py
```

### Option B: Download Other Years or Full History
To download a specific year (e.g. 2024):
```powershell
python run_pipeline.py --year 2024
```

To download and process all 8 historical cycling seasons (2016–2025, ~1.84 GB):
```powershell
python run_pipeline.py --all
```

### Option C: Re-run Processing Without Re-downloading
If raw data is already downloaded in `data/raw/`:
```powershell
python run_pipeline.py --skip-download
```

### Demonstrating Results & Visualizations
Run the reporting script to view console analytics and generate summary graphs:
```powershell
python show_results.py
```
This generates `data/processed/season_summary.png` featuring monthly ridership, top 10 busiest stations, top rebalancing bottlenecks, and a spatial demand map.

Or launch the interactive Jupyter Notebook:
```powershell
jupyter notebook notebooks/station_month_demo.ipynb
```

---

## 6. Assumptions, Data Licenses & Open Questions

### 6.1 Core Assumptions
1. **Operating Season**: HSL city bike operations run strictly from April 1 to October 31. Zero trips during November to March reflect system closure, not zero latent demand.
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

