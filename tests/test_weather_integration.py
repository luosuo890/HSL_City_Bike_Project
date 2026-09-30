"""
Unit tests for FMI Weather Data Integration in HSL City Bike project.
Verifies data cleaning conventions, field-by-field raw coverage, aggregation correctness,
merge row integrity, and missingness preservation for unmapped stations.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from src.clean_and_aggregate import load_and_aggregate_weather


@pytest.fixture
def project_dirs():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    processed_dir = os.path.join(base_dir, "data", "processed")
    return {"base": base_dir, "raw": raw_dir, "processed": processed_dir}


def test_precipitation_fmi_convention():
    """
    Test FMI precipitation convention:
    -1.0 represents 'no precipitation / dry' (converted to 0.0 mm).
    0.0 represents trace precipitation (<0.1 mm).
    Values >= 1.0 mm count as rainy days.
    True NaNs remain NaN.
    """
    sample_rrday = pd.Series([-1.0, 0.0, 0.5, 1.0, 15.2, np.nan])
    cleaned_precip = np.where(sample_rrday < 0, 0.0, sample_rrday)
    is_rainy = cleaned_precip >= 1.0

    assert cleaned_precip[0] == 0.0, "-1.0 must be converted to 0.0 mm"
    assert cleaned_precip[1] == 0.0, "0.0 trace precipitation stays 0.0 mm"
    assert cleaned_precip[2] == 0.5, "Positive values must remain unchanged"
    assert cleaned_precip[3] == 1.0
    assert cleaned_precip[4] == 15.2
    assert np.isnan(cleaned_precip[5]), "True NaN must remain NaN"

    assert not is_rainy[0], "Dry day (-1.0) must not be counted as rainy"
    assert not is_rainy[1], "Trace day (0.0) must not be counted as rainy"
    assert not is_rainy[2], "Sub-1mm day (0.5) must not be counted as rainy"
    assert is_rainy[3], "1.0mm must be counted as rainy"
    assert is_rainy[4], "15.2mm must be counted as rainy"


def test_raw_daily_weather_field_coverage(project_dirs):
    """
    Verify field-by-field completeness of raw FMI daily weather observations:
    Every field (tday, tmin, tmax, rrday, snow) must be checked independently
    and have 100% coverage (214/214 days in April-October 2025) for each station.
    """
    raw_csv = os.path.join(project_dirs["raw"], "weather_daily_2025.csv")
    assert os.path.exists(raw_csv), "weather_daily_2025.csv does not exist"

    df_raw = pd.read_csv(raw_csv)
    pivoted = df_raw.pivot_table(
        index=["time_utc", "city", "station_name"],
        columns="parameter",
        values="value",
        aggfunc="first",
    ).reset_index()

    expected_days = 214  # April 1 to October 31: 30+31+30+31+31+30+31
    expected_fields = ["tday", "tmin", "tmax", "rrday", "snow"]

    for city in ["Helsinki", "Espoo"]:
        city_df = pivoted[pivoted["city"] == city]
        assert len(city_df) == expected_days, f"Expected {expected_days} days for {city}, got {len(city_df)}"

        for field in expected_fields:
            assert field in city_df.columns, f"Field '{field}' missing from {city} observations"
            non_null_count = city_df[field].notna().sum()
            assert non_null_count == expected_days, (
                f"{city} field '{field}' has missing observations: {non_null_count}/{expected_days}"
            )


def test_weather_aggregation_completeness(project_dirs):
    """
    Verify that raw daily weather observations aggregate to exactly 14 records
    (7 months x 2 cities) with no missing values.
    """
    raw_dir = project_dirs["raw"]
    weather_df = load_and_aggregate_weather(raw_dir, year=2025)

    assert weather_df is not None, "Weather aggregation returned None"
    assert len(weather_df) == 14, f"Expected 14 monthly weather rows, got {len(weather_df)}"

    expected_months = [f"2025-{m:02d}" for m in range(4, 11)]
    assert sorted(weather_df["year_month"].unique()) == expected_months

    expected_cities = {"Helsinki", "Espoo"}
    assert set(weather_df["city"].unique()) == expected_cities

    # Check that core weather metrics contain no NaNs
    metrics = ["avg_temperature_c", "min_temperature_c", "max_temperature_c", "total_precipitation_mm", "rainy_days_count"]
    for col in metrics:
        assert weather_df[col].isna().sum() == 0, f"Column {col} has unexpected null values"


def test_station_month_merge_integrity(project_dirs):
    """
    Verify the merged station_month.csv:
    1. Row count is strictly preserved (3,197 rows).
    2. Primary key (year_month, station_id) remains strictly unique.
    3. Weather columns exist.
    4. Mapped stations (Helsinki, Espoo) have 100% complete weather metrics.
    5. Stations with unmapped city (45 rows) retain NaN for weather (no false assumptions).
    6. Weather values satisfy physical sanity bounds.
    """
    processed_path = os.path.join(project_dirs["processed"], "station_month.csv")
    assert os.path.exists(processed_path), "station_month.csv does not exist"

    df = pd.read_csv(processed_path)
    assert len(df) == 3197, f"Expected 3,197 rows, got {len(df)}"

    # Key uniqueness
    duplicates = df.duplicated(subset=["year_month", "station_id"]).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate (year_month, station_id) keys"

    # Weather columns presence
    weather_cols = [
        "weather_station_id",
        "avg_temperature_c",
        "min_temperature_c",
        "max_temperature_c",
        "total_precipitation_mm",
        "rainy_days_count",
    ]
    for col in weather_cols:
        assert col in df.columns, f"Missing weather column {col}"

    # Mapped stations must have complete weather data
    mapped_mask = df["city"].isin(["Helsinki", "Espoo"])
    assert mapped_mask.sum() == 3152, f"Expected 3,152 mapped station-month rows, got {mapped_mask.sum()}"
    for col in weather_cols:
        assert df.loc[mapped_mask, col].isna().sum() == 0, f"Column {col} has nulls for mapped stations"

    # Unmapped stations (45 rows) must retain NaN for weather (avoiding false precision)
    unmapped_mask = df["city"].isna()
    assert unmapped_mask.sum() == 45, f"Expected 45 unmapped station-month rows, got {unmapped_mask.sum()}"
    for col in weather_cols:
        assert df.loc[unmapped_mask, col].isna().sum() == 45, (
            f"Unmapped stations should have NaN weather for {col}, but found non-null values"
        )

    # Physical bounds check on mapped records
    valid_weather = df[mapped_mask]
    assert valid_weather["avg_temperature_c"].between(-10.0, 35.0).all()
    assert (valid_weather["min_temperature_c"] <= valid_weather["avg_temperature_c"]).all()
    assert (valid_weather["avg_temperature_c"] <= valid_weather["max_temperature_c"]).all()
    assert (valid_weather["total_precipitation_mm"] >= 0.0).all()
    assert valid_weather["rainy_days_count"].between(0, 31).all()

    # Station ID mapping check
    helsinki_fmisid = df[df["city"] == "Helsinki"]["weather_station_id"].unique()
    assert list(helsinki_fmisid) == [100971], "Helsinki stations must map to Kaisaniemi (100971)"

    espoo_fmisid = df[df["city"] == "Espoo"]["weather_station_id"].unique()
    assert list(espoo_fmisid) == [874863], "Espoo stations must map to Tapiola (874863)"
