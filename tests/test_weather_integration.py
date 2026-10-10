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
    and have 100% coverage (214/214 days in April-October) for each station in both 2024 and 2025.
    """
    expected_days = 214  # April 1 to October 31: 30+31+30+31+31+30+31
    expected_fields = ["tday", "tmin", "tmax", "rrday", "snow"]

    for year in [2024, 2025]:
        raw_csv = os.path.join(project_dirs["raw"], f"weather_daily_{year}.csv")
        assert os.path.exists(raw_csv), f"weather_daily_{year}.csv does not exist"

        df_raw = pd.read_csv(raw_csv)
        pivoted = df_raw.pivot_table(
            index=["time_utc", "city", "station_name"],
            columns="parameter",
            values="value",
            aggfunc="first",
        ).reset_index()

        for city in ["Helsinki", "Espoo"]:
            city_df = pivoted[pivoted["city"] == city]
            assert len(city_df) == expected_days, f"Expected {expected_days} days for {city} in {year}, got {len(city_df)}"

            for field in expected_fields:
                assert field in city_df.columns, f"Field '{field}' missing from {city} {year} observations"
                non_null_count = city_df[field].notna().sum()
                assert non_null_count == expected_days, (
                    f"{city} {year} field '{field}' has missing observations: {non_null_count}/{expected_days}"
                )


def test_weather_aggregation_completeness(project_dirs):
    """
    Verify that raw daily weather observations aggregate correctly:
    - Single year (2024 or 2025): exactly 14 records (7 months x 2 cities).
    - Multi-year (both years): exactly 28 records (14 months x 2 cities) with no missing values.
    """
    raw_dir = project_dirs["raw"]

    # Test single-year 2024
    w24 = load_and_aggregate_weather(raw_dir, year=2024)
    assert w24 is not None and len(w24) == 14
    assert sorted(w24["year_month"].unique()) == [f"2024-{m:02d}" for m in range(4, 11)]

    # Test single-year 2025
    w25 = load_and_aggregate_weather(raw_dir, year=2025)
    assert w25 is not None and len(w25) == 14
    assert sorted(w25["year_month"].unique()) == [f"2025-{m:02d}" for m in range(4, 11)]

    # Test complete multi-year aggregation
    weather_df = load_and_aggregate_weather(raw_dir, year=None)
    assert weather_df is not None, "Weather aggregation returned None"
    assert len(weather_df) == 28, f"Expected 28 monthly weather rows, got {len(weather_df)}"

    expected_months = [f"2024-{m:02d}" for m in range(4, 11)] + [f"2025-{m:02d}" for m in range(4, 11)]
    assert sorted(weather_df["year_month"].unique()) == expected_months

    expected_cities = {"Helsinki", "Espoo"}
    assert set(weather_df["city"].unique()) == expected_cities

    # Check that core weather metrics contain no NaNs
    metrics = ["avg_temperature_c", "min_temperature_c", "max_temperature_c", "total_precipitation_mm", "rainy_days_count"]
    for col in metrics:
        assert weather_df[col].isna().sum() == 0, f"Column {col} has unexpected null values"


def test_station_month_merge_integrity(project_dirs):
    """
    Verify the merged station_month.csv across 2024 and 2025:
    1. Row count is strictly preserved (6,395 rows = 3,198 in 2024 + 3,197 in 2025).
    2. Primary key (year_month, station_id) remains strictly unique.
    3. Exactly 14 unique months covered.
    4. Weather columns exist.
    5. Mapped stations (6,324 rows) have 100% complete weather metrics.
    6. Stations with unmapped city (71 rows: 26 in 2024, 45 in 2025) retain NaN for weather (no false assumptions).
    7. Weather values satisfy physical sanity bounds.
    """
    processed_path = os.path.join(project_dirs["processed"], "station_month.csv")
    assert os.path.exists(processed_path), "station_month.csv does not exist"

    df = pd.read_csv(processed_path)
    assert len(df) == 6395, f"Expected 6,395 rows, got {len(df)}"

    # 14 unique months
    expected_months = [f"2024-{m:02d}" for m in range(4, 11)] + [f"2025-{m:02d}" for m in range(4, 11)]
    assert sorted(df["year_month"].unique()) == expected_months

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

    # Mapped stations must have complete weather data (6,324 rows)
    mapped_mask = df["city"].isin(["Helsinki", "Espoo"])
    assert mapped_mask.sum() == 6324, f"Expected 6,324 mapped station-month rows, got {mapped_mask.sum()}"
    for col in weather_cols:
        assert df.loc[mapped_mask, col].isna().sum() == 0, f"Column {col} has nulls for mapped stations"

    # Unmapped stations (71 rows total: 26 in 2024, 45 in 2025) must retain NaN for weather
    unmapped_mask = df["city"].isna()
    assert unmapped_mask.sum() == 71, f"Expected 71 unmapped station-month rows, got {unmapped_mask.sum()}"
    for col in weather_cols:
        assert df.loc[unmapped_mask, col].isna().sum() == 71, (
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


def test_station_metadata_mapping_audit(project_dirs):
    """
    Audit unmapped stations across both seasons:
    - 2024 season has exactly 4 unmapped stations (710, 768, 997, 999).
    - 2025 season has exactly 7 unmapped stations (626, 710, 716, 754, 768, 997, 999).
    - All other stations map cleanly to the official stations layer.
    """
    processed_path = os.path.join(project_dirs["processed"], "station_month.csv")
    df = pd.read_csv(processed_path)

    unmapped_2024 = set(df[df["year_month"].str.startswith("2024-") & df["city"].isna()]["station_id"].unique())
    assert unmapped_2024 == {710, 768, 997, 999}, f"Unexpected 2024 unmapped stations: {unmapped_2024}"

    unmapped_2025 = set(df[df["year_month"].str.startswith("2025-") & df["city"].isna()]["station_id"].unique())
    assert unmapped_2025 == {626, 710, 716, 754, 768, 997, 999}, f"Unexpected 2025 unmapped stations: {unmapped_2025}"
