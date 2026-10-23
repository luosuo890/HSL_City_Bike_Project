"""
Automated Test Suite for Phase 1 Web Data Exports.
Verifies data integrity, key uniqueness, geographic validity, model reproducibility,
and methodological guardrails across all 6 JSON files in docs/data/.
"""

import os
import json
import pytest
import numpy as np

DOCS_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")


def load_json(filename):
    filepath = os.path.join(DOCS_DATA_DIR, filename)
    assert os.path.exists(filepath), f"Export file missing: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class TestWebDataExports:

    def test_all_files_exist(self):
        """Verifies that all 6 required derived JSON files exist in docs/data/."""
        expected_files = [
            "data_stations.json",
            "data_hourly_city.json",
            "data_commute_peaks.json",
            "data_daily_weather.json",
            "data_model_summary.json",
            "data_model_predictions_2025.json"
        ]
        for fname in expected_files:
            fpath = os.path.join(DOCS_DATA_DIR, fname)
            assert os.path.exists(fpath), f"Missing expected export: {fname}"
            assert os.path.getsize(fpath) > 0, f"Export file is empty: {fname}"

    def test_total_payload_size(self):
        """Ensures total uncompressed web data payload stays lightweight (< 2.0 MB)."""
        total_size = sum(
            os.path.getsize(os.path.join(DOCS_DATA_DIR, f))
            for f in os.listdir(DOCS_DATA_DIR) if f.endswith(".json")
        )
        assert total_size < 2.0 * 1024 * 1024, f"Total payload too large: {total_size / (1024*1024):.2f} MB"

    def test_stations_data_integrity(self):
        """Validates station metadata, geographic coordinates, and unmapped station audit."""
        data = load_json("data_stations.json")
        assert "stations" in data
        assert "unmapped" in data
        assert "meta" in data

        stations = data["stations"]
        unmapped = data["unmapped"]

        # 454 mapped and 7 unmapped stations
        assert len(stations) == 454, f"Expected 454 mapped stations, got {len(stations)}"
        assert len(unmapped) == 7, f"Expected 7 unmapped stations, got {len(unmapped)}"

        # Verify key uniqueness
        all_ids = [s["id"] for s in stations] + [u["id"] for u in unmapped]
        assert len(all_ids) == len(set(all_ids)), "Station IDs are not unique!"

        # Coordinate checks for mapped stations (Helsinki capital region bounds)
        for s in stations:
            assert s["city"] in ["Helsinki", "Espoo"], f"Unexpected city: {s['city']}"
            assert 60.10 <= s["lat"] <= 60.30, f"Latitude out of bounds for station {s['id']}: {s['lat']}"
            assert 24.60 <= s["lon"] <= 25.25, f"Longitude out of bounds for station {s['id']}: {s['lon']}"
            assert s["cap"] is None or (8 <= s["cap"] <= 60), f"Capacity unusual: {s['cap']}"
            assert len(s["months"]) >= 1, f"Station {s['id']} has no monthly records"

            # Check monthly record format [dep, ret, net]
            for ym, vals in s["months"].items():
                assert len(vals) == 3
                assert vals[0] >= 0  # departures >= 0
                assert vals[1] >= 0  # returns >= 0
                assert vals[2] == vals[1] - vals[0]  # net_flow = returns - departures

        # Audit checks for unmapped stations
        for u in unmapped:
            assert u["lat"] is None, "Unmapped station must not have fake latitude!"
            assert u["lon"] is None, "Unmapped station must not have fake longitude!"
            assert "audit_note" in u

    def test_hourly_city_curves_integrity(self):
        """Validates diurnal hourly curves across cities and day types."""
        data = load_json("data_hourly_city.json")
        profiles = data["profiles"]

        for city in ["Helsinki", "Espoo", "All"]:
            assert city in profiles
            for dt in ["weekday", "weekend"]:
                assert dt in profiles[city]
                assert "overall_all" in profiles[city][dt]
                assert "overall_2024" in profiles[city][dt]
                assert "overall_2025" in profiles[city][dt]

                curve = profiles[city][dt]["overall_all"]
                assert len(curve) == 24, f"Expected 24 hours in curve, got {len(curve)}"
                hours_seen = [p["hour"] for p in curve]
                assert hours_seen == list(range(24))

                for p in curve:
                    assert p["avg_dep"] >= 0
                    assert p["avg_ret"] >= 0
                    assert p["net_flow"] == p["tot_ret"] - p["tot_dep"]

    def test_commute_peaks_integrity(self):
        """Validates commuter peak tidal reversal metrics matching Figure 6."""
        data = load_json("data_commute_peaks.json")
        assert "top_tidal_swing" in data
        assert "commuter_hubs" in data
        assert "audit" in data

        top10 = data["top_tidal_swing"]
        assert len(top10) == 10
        for hub in top10:
            assert "station_name" in hub
            assert "morn_net" in hub
            assert "eve_net" in hub
            # Verify tidal opposition in high swing stations
            assert hub["tidal_swing"] == abs(hub["morn_net"] - hub["eve_net"])

        hubs = data["commuter_hubs"]
        assert len(hubs) == 120
        for h in hubs:
            assert h["morn_dep"] >= 0
            assert h["eve_dep"] >= 0
            assert h["total_peak_trips"] == h["morn_dep"] + h["morn_ret"] + h["eve_dep"] + h["eve_ret"]

        # Audit checks
        assert "2024" in data["audit"]
        assert "2025" in data["audit"]
        assert data["audit"]["2024"]["midnight_crossings"] == 21532
        assert data["audit"]["2025"]["midnight_crossings"] == 19957

    def test_daily_weather_integrity(self):
        """Validates daily weather and trip merge coverage across 2024 and 2025."""
        data = load_json("data_daily_weather.json")
        records = data["daily_records"]

        # Exactly 428 days per city (214 in 2024 + 214 in 2025) * 2 cities = 856 records
        assert len(records) == 856, f"Expected 856 daily records, got {len(records)}"

        helsinki_recs = [r for r in records if r["city"] == "Helsinki"]
        espoo_recs = [r for r in records if r["city"] == "Espoo"]
        assert len(helsinki_recs) == 428
        assert len(espoo_recs) == 428

        for r in records:
            assert r["year"] in [2024, 2025]
            assert 4 <= r["month"] <= 10
            assert r["dep"] >= 0
            assert r["ret"] >= 0
            assert r["net"] == r["ret"] - r["dep"]

            # Weather validity
            assert -10.0 <= r["tday"] <= 35.0, f"Abnormal temperature: {r['tday']}"
            assert r["precip"] >= 0.0, f"Negative precipitation: {r['precip']}"
            assert r["is_rainy"] in [0, 1]
            if r["precip"] >= 1.0:
                assert r["is_rainy"] == 1
            else:
                assert r["is_rainy"] == 0

    def test_model_summary_integrity(self):
        """Verifies exact reproducibility of model evaluation metrics from model_comparison.ipynb."""
        data = load_json("data_model_summary.json")
        assert "overall_metrics" in data
        assert "monthly_wape_breakdown" in data
        assert "ranking_overlap_metrics" in data
        assert "low_usage_metrics" in data

        overall = {m["model_id"]: m for m in data["overall_metrics"]}

        # Exact reproduction assertions
        assert overall["base"]["dep_wape"] == 17.58
        assert overall["base"]["dep_mae"] == 141.88
        assert overall["ridge"]["dep_wape"] == 28.00
        assert overall["ridge"]["dep_mae"] == 226.01
        assert overall["dt"]["dep_wape"] == 24.72
        assert overall["dt"]["dep_mae"] == 199.53

        # Monthly breakdown covers exactly months 5 to 10
        months = [m["month"] for m in data["monthly_wape_breakdown"]]
        assert months == ["2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"]

        # Ranking overlap covers months 5 to 10
        assert len(data["ranking_overlap_metrics"]) == 6

    def test_model_predictions_integrity(self):
        """Verifies 2,718 out-of-time test predictions and residuals."""
        data = load_json("data_model_predictions_2025.json")
        records = data["records"]

        assert len(records) == 2718, f"Expected 2,718 records, got {len(records)}"

        actual_deps = np.array([r["act_dep"] for r in records])
        base_deps = np.array([r["base_dep"] for r in records])
        ridge_deps = np.array([r["ridge_dep"] for r in records])
        dt_deps = np.array([r["dt_dep"] for r in records])

        # Residual MAE checks against overall summary
        base_mae = np.mean(np.abs(actual_deps - base_deps))
        ridge_mae = np.mean(np.abs(actual_deps - ridge_deps))
        dt_mae = np.mean(np.abs(actual_deps - dt_deps))

        assert abs(base_mae - 141.88) < 0.1
        assert abs(ridge_mae - 226.01) < 0.1
        assert abs(dt_mae - 199.53) < 0.1

        # Non-negative checks
        assert np.all(base_deps >= 0)
        assert np.all(ridge_deps >= 0)
        assert np.all(dt_deps >= 0)
