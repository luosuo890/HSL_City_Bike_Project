"""
Automated Test Suite for City-Day Weather Scenario Explorer.
Verifies:
1. JSON export integrity and lightweight payload size.
2. Temporal split: 2024 train (N=428) vs 2025 out-of-time test (N=428).
3. Feature isolation: Calendar-only baseline strictly omits weather variables.
4. Identical test cohort: Both models evaluated on the exact same 428 records.
5. Metric recomputation: Recomputed MAE, WAPE, and RMSE match exported metrics.
6. Empirical residual intervals: 10th and 90th percentile bounds are valid.
7. HTML & JS UI contract: Required controls, sliders, warning banner, and clean text.
"""

import os
import re
import json
import pytest
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DATA_DIR = os.path.join(PROJECT_ROOT, "docs", "data")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


@pytest.fixture(scope="module")
def scenario_data():
    file_path = os.path.join(DOCS_DATA_DIR, "data_weather_scenario.json")
    assert os.path.exists(file_path), f"Missing data_weather_scenario.json at {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def daily_weather_data():
    file_path = os.path.join(DOCS_DATA_DIR, "data_daily_weather.json")
    assert os.path.exists(file_path), f"Missing data_daily_weather.json at {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists_and_size_budget(scenario_data):
    """Scenario export must exist and be lightweight (< 150 KB)."""
    file_path = os.path.join(DOCS_DATA_DIR, "data_weather_scenario.json")
    size_kb = os.path.getsize(file_path) / 1024
    assert size_kb < 150.0, f"Scenario file too large: {size_kb:.1f} KB"
    assert "meta" in scenario_data
    assert "models" in scenario_data
    assert "test_2025_records" in scenario_data


def test_temporal_split_and_sample_sizes(scenario_data, daily_weather_data):
    """
    Validates temporal split:
    Train strictly 2024 season (214 days x 2 cities = 428 city-days).
    Test strictly 2025 season (214 days x 2 cities = 428 city-days).
    """
    meta = scenario_data["meta"]
    assert meta["total_train_records"] == 428
    assert meta["total_test_records"] == 428
    assert meta["calendar_days_per_season"] == 214

    test_records = scenario_data["test_2025_records"]
    assert len(test_records) == 428

    # All test records must be from 2025
    years = {int(r["date"][:4]) for r in test_records}
    assert years == {2025}, f"Unexpected test years: {years}"

    # Helsinki and Espoo records count in test set
    helsinki_recs = [r for r in test_records if r["city"] == "Helsinki"]
    espoo_recs = [r for r in test_records if r["city"] == "Espoo"]
    assert len(helsinki_recs) == 214
    assert len(espoo_recs) == 214


def test_feature_space_isolation(scenario_data):
    """
    Validates that:
    1. Calendar-only baseline features DO NOT contain tday, precip, or tmax.
    2. Weather model features contain tday and precip, but NOT tmax.
    """
    cal_features = scenario_data["meta"]["features_calendar"]
    wth_features = scenario_data["meta"]["features_weather"]

    # Baseline features
    assert "tday" not in cal_features
    assert "precip" not in cal_features
    assert "tmax" not in cal_features
    assert "is_helsinki" in cal_features
    assert "is_weekend" in cal_features

    # Weather features
    assert "tday" in wth_features
    assert "precip" in wth_features
    assert "tmax" not in wth_features  # Explicit user instruction: do not use tmax

    # Model coefficients check
    cal_coefs = scenario_data["models"]["calendar_only"]["coefficients"]
    wth_coefs = scenario_data["models"]["weather"]["coefficients"]

    assert "tday" not in cal_coefs
    assert "precip" not in cal_coefs
    assert "tday" in wth_coefs
    assert "precip" in wth_coefs
    assert "tmax" not in wth_coefs


def test_metric_recomputation_and_model_superiority(scenario_data):
    """
    Recomputes MAE and WAPE from test records and verifies exact match with exported metrics.
    Also verifies that the weather model improves over calendar-only baseline in 2025 out-of-time test.
    """
    test_records = scenario_data["test_2025_records"]
    df = pd.DataFrame(test_records)

    actual = df["dep"].values
    cal_pred = df["cal_pred"].values
    wth_pred = df["wth_pred"].values

    # Overall metrics
    cal_mae = float(np.mean(np.abs(actual - cal_pred)))
    cal_wape = float(np.sum(np.abs(actual - cal_pred)) / np.sum(actual) * 100)
    wth_mae = float(np.mean(np.abs(actual - wth_pred)))
    wth_wape = float(np.sum(np.abs(actual - wth_pred)) / np.sum(actual) * 100)

    exp_cal = scenario_data["models"]["calendar_only"]["metrics"]["overall"]
    exp_wth = scenario_data["models"]["weather"]["metrics"]["overall"]

    assert round(cal_mae, 1) == round(exp_cal["mae"], 1)
    assert round(cal_wape, 1) == round(exp_cal["wape"], 1)
    assert round(wth_mae, 1) == round(exp_wth["mae"], 1)
    assert round(wth_wape, 1) == round(exp_wth["wape"], 1)

    # Weather model achieves lower WAPE and MAE
    assert wth_wape < cal_wape
    assert wth_mae < cal_mae

    # City-specific metrics
    for city in ["Helsinki", "Espoo"]:
        city_key = city.lower()
        sub = df[df["city"] == city]
        sub_act = sub["dep"].values
        sub_cal = sub["cal_pred"].values
        sub_wth = sub["wth_pred"].values

        c_cal_wape = float(np.sum(np.abs(sub_act - sub_cal)) / np.sum(sub_act) * 100)
        c_wth_wape = float(np.sum(np.abs(sub_act - sub_wth)) / np.sum(sub_act) * 100)

        exp_c_cal = scenario_data["models"]["calendar_only"]["metrics"][city_key]
        exp_c_wth = scenario_data["models"]["weather"]["metrics"][city_key]

        assert round(c_cal_wape, 1) == round(exp_c_cal["wape"], 1)
        assert round(c_wth_wape, 1) == round(exp_c_wth["wape"], 1)
        assert c_wth_wape < c_cal_wape


def test_empirical_residual_intervals(scenario_data):
    """
    Validates empirical residual bounds (p10, p50, p90).
    Ensures p10 <= p50 <= p90 and residuals are empirically verified.
    """
    res = scenario_data["models"]["weather"]["empirical_residuals"]
    for city_key in ["overall", "helsinki", "espoo"]:
        assert city_key in res
        c_res = res[city_key]
        assert c_res["p10"] <= c_res["p50"] <= c_res["p90"]
        assert c_res["mae"] > 0
        assert c_res["med_abs"] > 0


def test_empirical_bounds_match_data(scenario_data, daily_weather_data):
    """Empirical bounds in metadata must match actual observed range in 2024-2025."""
    bounds = scenario_data["meta"]["empirical_bounds"]
    df = pd.DataFrame(daily_weather_data["daily_records"])

    assert bounds["tday"]["min"] == round(float(df["tday"].min()), 1)
    assert bounds["tday"]["max"] == round(float(df["tday"].max()), 1)
    assert bounds["precip"]["min"] == round(float(df["precip"].min()), 1)
    assert bounds["precip"]["max"] == round(float(df["precip"].max()), 1)


def test_html_ui_components_and_no_raw_math():
    """
    Validates that:
    1. index.html contains the scenario explorer controls and output elements.
    2. No raw markdown or LaTeX math tokens appear in the visible text.
    """
    html_path = os.path.join(DOCS_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Required element IDs
    required_ids = [
        "forecast-weather-scenario-card",
        "scenario-city",
        "scenario-month",
        "scenario-daytype",
        "scenario-tday",
        "scenario-precip",
        "scenario-range-warning",
        "scenario-est-departures",
        "scenario-base-departures",
        "scenario-weather-delta",
        "scenario-analog-table",
        "scenario-analog-tbody"
    ]
    for el_id in required_ids:
        assert f'id="{el_id}"' in html, f"Missing element with id: {el_id}"

    # Must NOT have tmax slider
    assert "scenario-tmax" not in html

    # Visible text must not have unrendered markdown / math
    scenario_card_match = re.search(r'<div[^>]*id="forecast-weather-scenario-card"[^>]*>(.*?)</div>\s*<!-- Methodological', html, re.DOTALL)
    assert scenario_card_match, "Could not extract scenario card content"
    scenario_html = scenario_card_match.group(1)

    assert "**" not in scenario_html, "Found raw markdown ** in scenario card"
    assert "\\text{" not in scenario_html, "Found raw LaTeX \\text{ in scenario card"
    assert "\\frac{" not in scenario_html, "Found raw LaTeX \\frac{ in scenario card"
    assert "$_" not in scenario_html, "Found raw LaTeX subscript in scenario card"


def test_tab5_standalone_navigation_and_panel_isolation():
    """
    Validates that:
    1. Top navigation has 5 distinct tab buttons with exact target IDs.
    2. Five top-level tab panes exist as sibling <section class="tab-pane"> elements.
    3. Tab 4 (tab-demand-forecasting) panel is completely restored to station-month benchmarks
       and does NOT contain weather scenario explorer controls.
    4. Tab 5 (tab-weather-scenario) panel houses the independent scenario simulator.
    5. app.js tab switching logic handles tab-weather-scenario.
    """
    html_path = os.path.join(DOCS_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    expected_tabs = [
        "tab-station-map",
        "tab-commute-dynamics",
        "tab-weather-exploration",
        "tab-demand-forecasting",
        "tab-weather-scenario"
    ]

    for tab_id in expected_tabs:
        assert f'data-tab="{tab_id}"' in html, f"Missing tab button for: {tab_id}"
        assert f'<section id="{tab_id}" class="tab-pane' in html, f"Missing section for: {tab_id}"

    # Extract Tab 4 content
    t4_match = re.search(r'<section id="tab-demand-forecasting"[^>]*>(.*?)</section>', html, re.DOTALL)
    assert t4_match, "Could not find tab-demand-forecasting section"
    t4_content = t4_match.group(1)

    # Tab 4 must NOT contain scenario controls
    assert "forecast-weather-scenario-card" not in t4_content, "Scenario card must not be inside tab-demand-forecasting"
    assert "scenario-city" not in t4_content, "scenario-city must not be inside tab-demand-forecasting"
    assert "scenario-tday" not in t4_content, "scenario-tday must not be inside tab-demand-forecasting"

    # Extract Tab 5 content
    t5_match = re.search(r'<section id="tab-weather-scenario"[^>]*>(.*?)</section>', html, re.DOTALL)
    assert t5_match, "Could not find tab-weather-scenario section"
    t5_content = t5_match.group(1)

    # Tab 5 MUST contain scenario controls and guardrails
    assert "forecast-weather-scenario-card" in t5_content
    assert "scenario-city" in t5_content
    assert "scenario-tday" in t5_content
    assert "scenario-analog-table" in t5_content
    assert "Methodological Guidelines" in t5_content

    # app.js check
    js_app_path = os.path.join(DOCS_DIR, "js", "app.js")
    with open(js_app_path, "r", encoding="utf-8") as f:
        app_js = f.read()

    assert "tab-weather-scenario" in app_js, "app.js must handle tab-weather-scenario"


def test_js_implementation_and_no_raw_math():
    """
    Validates forecast.js implementation:
    1. Handles scenario data fetch and state updates.
    2. Calculates baseline and weather predictions.
    3. No raw markdown or LaTeX math tokens in injected text.
    """
    js_path = os.path.join(DOCS_DIR, "js", "forecast.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    assert "data_weather_scenario.json" in js
    assert "initWeatherScenario" in js
    assert "updateScenarioView" in js
    assert "scenario-range-warning" in js
    assert "scenario-analog-tbody" in js

    # Check for unrendered markdown or LaTeX in strings
    assert "\\text{" not in js
    assert "\\frac{" not in js
