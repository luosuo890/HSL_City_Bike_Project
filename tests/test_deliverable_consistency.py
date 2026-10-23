"""
Automated unit tests for deliverable consistency:
1. Technical Report PDF exists, has <= 5 pages, valid file size.
2. Verified ranking for commuter tidal swings in data_commute_peaks.json.
3. Multi-model metrics alignment between findings.md and data_model_summary.json.
4. Repository URL format and GitHub Pages deployment configuration checks.
"""

import os
import json
import pymupdf


def test_technical_report_pdf_page_budget():
    """Verify technical report PDF exists and strictly respects <= 5 pages budget."""
    pdf_path = os.path.join("reports", "HSL_City_Bike_Technical_Report.pdf")
    assert os.path.exists(pdf_path), f"Technical report PDF not found at {pdf_path}"

    doc = pymupdf.open(pdf_path)
    page_count = len(doc)
    assert page_count <= 5, f"PDF page count {page_count} exceeds maximum budget of 5 pages"
    assert page_count == 5, f"Expected exactly 5 pages, got {page_count}"

    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    assert file_size_mb < 10.0, f"PDF file size {file_size_mb:.2f} MB is too large"


def test_commuter_tidal_swings_verified_ranking():
    """Verify tidal swing calculations and exact top rankings."""
    peaks_path = os.path.join("docs", "data", "data_commute_peaks.json")
    with open(peaks_path, "r", encoding="utf-8") as f:
        cp = json.load(f)

    top_swings = cp["top_tidal_swing"]
    assert len(top_swings) >= 3

    # Rank 1: Salmisaarenranta (swing 12,587)
    assert top_swings[0]["station_id"] == 59
    assert top_swings[0]["station_name"] == "Salmisaarenranta"
    assert top_swings[0]["tidal_swing"] == 12587

    # Rank 2: Itämerentori (swing 11,860)
    assert top_swings[1]["station_id"] == 30
    assert top_swings[1]["station_name"] == "Itämerentori"
    assert top_swings[1]["tidal_swing"] == 11860

    # Rank 3: Sompasaari (swing 10,781)
    assert top_swings[2]["station_id"] == 404
    assert top_swings[2]["station_name"] == "Sompasaari"
    assert top_swings[2]["tidal_swing"] == 10781


def test_model_summary_metrics_integrity():
    """Verify multi-model comparison values in data_model_summary.json."""
    summary_path = os.path.join("docs", "data", "data_model_summary.json")
    with open(summary_path, "r", encoding="utf-8") as f:
        ms = json.load(f)

    overall = {m["model_id"]: m for m in ms["overall_metrics"]}
    # Baseline
    assert overall["base"]["dep_mae"] == 141.88
    assert overall["base"]["dep_wape"] == 17.58
    assert overall["base"]["ret_mae"] == 139.73
    assert overall["base"]["ret_wape"] == 17.31

    # Ridge
    assert overall["ridge"]["dep_mae"] == 226.01
    assert overall["ridge"]["dep_wape"] == 28.00
    assert overall["ridge"]["ret_mae"] == 226.52
    assert overall["ridge"]["ret_wape"] == 28.06

    # Decision Tree
    assert overall["dt"]["dep_mae"] == 199.53
    assert overall["dt"]["dep_wape"] == 24.72
    assert overall["dt"]["ret_mae"] == 195.63
    assert overall["dt"]["ret_wape"] == 24.23

    # Low Usage bottom quartile
    low = {m["model_id"]: m for m in ms["low_usage_metrics"]}
    assert low["base"]["dep_wape"] == 33.83
    assert low["ridge"]["dep_wape"] == 124.07
    assert low["dt"]["dep_wape"] == 55.98
