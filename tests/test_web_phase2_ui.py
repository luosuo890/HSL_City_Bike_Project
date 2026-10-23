"""
Automated Test Suite for Phase 2 Web UI & Interactive Map Skeleton.
Validates HTML structure, relative asset paths, Leaflet integration,
CSS responsiveness, HTTP server serving, and commute tidal rankings.
"""

import os
import re
import json
import pytest
import http.server
import socketserver
import threading
import urllib.request

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


class TestPhase2WebUI:

    def test_html_structure_and_assets(self):
        """Verifies that index.html contains all necessary elements and relative paths."""
        index_path = os.path.join(DOCS_DIR, "index.html")
        assert os.path.exists(index_path), "index.html is missing!"

        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Responsive viewport
        assert '<meta name="viewport"' in html, "Missing viewport meta tag for mobile responsiveness"

        # Leaflet 1.9.4 integration
        assert "leaflet@1.9.4/dist/leaflet.css" in html, "Missing Leaflet CSS"
        assert "leaflet@1.9.4/dist/leaflet.js" in html, "Missing Leaflet JS"

        # Strictly relative local paths
        assert 'href="./css/style.css"' in html, "Must use strictly relative path for style.css"
        assert 'src="./js/map.js"' in html, "Must use strictly relative path for map.js"
        assert 'src="./js/commute.js"' in html, "Must use strictly relative path for commute.js"
        assert 'src="./js/weather.js"' in html, "Must use strictly relative path for weather.js"
        assert 'src="./js/forecast.js"' in html, "Must use strictly relative path for forecast.js"
        assert 'src="./js/app.js"' in html, "Must use strictly relative path for app.js"

        # Chart.js library
        assert "chart.js" in html.lower(), "Chart.js must be loaded for commute visualizations"

        # Correct repository link with safe rel="noopener noreferrer"
        assert 'https://github.com/luosuo890/HSL_City_Bike_Project' in html, "Repository link must point to luosuo890/HSL_City_Bike_Project"
        for m in re.finditer(r'<a\s+[^>]*target=["\']_blank["\'][^>]*>', html):
            anchor = m.group(0)
            assert 'rel="noopener noreferrer"' in anchor or "rel='noopener noreferrer'" in anchor, f"target='_blank' link missing rel='noopener noreferrer': {anchor}"

        # 4 Tab panes exist and are properly labeled
        for tab_id in ["tab-station-map", "tab-commute-dynamics", "tab-weather-exploration", "tab-demand-forecasting"]:
            assert f'id="{tab_id}"' in html, f"Missing tab pane: {tab_id}"

        # Module status indicators and error handling banners
        for status_elem in [
            "map-loading-overlay", "error-banner",
            "commute-loading-overlay", "commute-error-banner",
            "weather-loading-overlay", "weather-error-banner",
            "forecast-loading-overlay", "forecast-error-banner"
        ]:
            assert f'id="{status_elem}"' in html, f"Missing status indicator element: {status_elem}"

        # Core interactive controls
        required_ids = [
            "map-container",
            "filter-year",
            "filter-month",
            "filter-city",
            "station-search",
            "station-ranking-table",
            "station-table-body",
            "btn-reset-view",
            "btn-export-csv",
            "btn-unmapped-audit",
            "unmapped-modal",
            "unmapped-table-body",
            "kpi-active-stations",
            "kpi-net-flow",
            "kpi-total-departures",
            "kpi-total-returns",
            "commute-filter-city",
            "commute-filter-timeframe",
            "commute-filter-mode",
            "chart-hourly-profile",
            "chart-tidal-swing",
            "chart-commute-quadrant",
            "commuter-table-body",
            # Phase 4 Weather exploration controls
            "filter-weather-year",
            "filter-weather-city",
            "filter-weather-param",
            "filter-weather-daytype",
            "kpi-weather-samples",
            "kpi-weather-corr",
            "kpi-weather-slope",
            "kpi-weather-rainydays",
            "kpi-weather-unmapped",
            "chart-weather-scatter",
            "chart-weather-rain-bars",
            "chart-weather-timeseries",
            # Phase 5 Demand forecasting controls
            "filter-forecast-month",
            "filter-forecast-model",
            "filter-forecast-metric",
            "filter-forecast-city",
            "filter-forecast-segment",
            "filter-forecast-search",
            "chart-forecast-scatter",
            "chart-forecast-monthly-wape",
            "chart-forecast-ranking-overlap",
            "forecast-scorecard-table",
            "forecast-scorecard-tbody",
            "forecast-triage-table",
            "forecast-triage-tbody",
            "slice-sample-count",
            "slice-mae-val",
            "slice-wape-val"
        ]
        for rid in required_ids:
            assert f'id="{rid}"' in html, f"Missing required element id: {rid}"

        # Methodological guardrails present
        assert "Net Flow" in html
        assert "real-time bicycle inventory" in html.lower() or "not real-time dock stock" in html.lower()
        assert "retrospective" in html.lower()
        assert "not weather forecasts" in html.lower()

        # Day-type labels explicitly distinguish Mon-Fri vs Sat-Sun
        assert "Weekday (Mon–Fri)" in html or "Weekday (Mon-Fri)" in html
        assert "Weekend (Sat–Sun)" in html or "Weekend (Sat-Sun)" in html

        # No unrendered LaTeX or Markdown markers in visible HTML
        assert "$" not in html, "HTML contains unrendered LaTeX dollar markers"
        assert "\\text{" not in html, "HTML contains unrendered LaTeX text macros"
        assert "**" not in html, "HTML contains unrendered Markdown bold asterisks"

        # Explicit plain English definitions
        assert "Net flow equals returns minus departures" in html
        assert "MAE measures trips, not bicycles" in html

    def test_commute_js_implementation(self):
        """Verifies commute.js logic, relative data fetches, and absence of raw CSV loads."""
        js_path = os.path.join(DOCS_DIR, "js", "commute.js")
        assert os.path.exists(js_path), "commute.js is missing!"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Relative fetch of derived small JSONs only
        assert '"./data/data_hourly_city.json"' in js or "'./data/data_hourly_city.json'" in js
        assert '"./data/data_commute_peaks.json"' in js or "'./data/data_commute_peaks.json'" in js
        assert "station_intraday_monthly.csv" not in js, "Must never load large 30MB CSV in browser"

        # Explicit day-type labels in chart datasets
        assert "Weekday (Mon–Fri)" in js or "Weekday (Mon-Fri)" in js
        assert "Weekend (Sat–Sun)" in js or "Weekend (Sat-Sun)" in js

    def test_css_responsive_design(self):
        """Validates stylesheet colors, responsive breakpoints, and classes."""
        css_path = os.path.join(DOCS_DIR, "css", "style.css")
        assert os.path.exists(css_path), "style.css is missing!"

        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Color palette variables
        assert "--coral-deficit" in css
        assert "--blue-surplus" in css
        assert "--primary-teal" in css

        # Responsive media queries
        assert "@media" in css
        assert "max-width" in css

        # Loading animation
        assert "@keyframes spin" in css

    def test_map_js_implementation(self):
        """Verifies map.js logic, relative data fetch, and zero-centered net flow colors."""
        js_path = os.path.join(DOCS_DIR, "js", "map.js")
        assert os.path.exists(js_path), "map.js is missing!"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Tile layer configuration: Standard OpenStreetMap (no API key required)
        assert "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" in js
        assert "cartocdn.com" not in js, "CARTO basemaps require an API key and must be removed"
        assert "OpenStreetMap" in js
        assert "contributors" in js

        # Relative fetch
        assert '"./data/data_stations.json"' in js or "'./data/data_stations.json'" in js, \
            "map.js must fetch using strictly relative path ./data/data_stations.json"

        # Zero-centered diverging scale
        assert "net_flow" in js
        assert "interpolateColor" in js

        # CSV export feature
        assert "exportCurrentTableCsv" in js

        # Unmapped stations handling
        assert "renderUnmappedModalContent" in js

    def test_local_http_serving(self):
        """Starts a temporary local HTTP server on docs/ and probes all static files."""
        PORT = 8912
        cwd_orig = os.getcwd()
        try:
            os.chdir(DOCS_DIR)
            Handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)

            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            test_urls = [
                f"http://127.0.0.1:{PORT}/",
                f"http://127.0.0.1:{PORT}/index.html",
                f"http://127.0.0.1:{PORT}/css/style.css",
                f"http://127.0.0.1:{PORT}/js/map.js",
                f"http://127.0.0.1:{PORT}/js/commute.js",
                f"http://127.0.0.1:{PORT}/js/weather.js",
                f"http://127.0.0.1:{PORT}/js/forecast.js",
                f"http://127.0.0.1:{PORT}/js/app.js",
                f"http://127.0.0.1:{PORT}/data/data_stations.json",
                f"http://127.0.0.1:{PORT}/data/data_hourly_city.json",
                f"http://127.0.0.1:{PORT}/data/data_commute_peaks.json",
                f"http://127.0.0.1:{PORT}/data/data_daily_weather.json",
                f"http://127.0.0.1:{PORT}/data/data_model_summary.json",
                f"http://127.0.0.1:{PORT}/data/data_model_predictions_2025.json"
            ]

            for url in test_urls:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=3) as res:
                    assert res.status == 200, f"Expected 200 for {url}, got {res.status}"
                    body = res.read()
                    assert len(body) > 0, f"Empty response from {url}"

            httpd.shutdown()
            httpd.server_close()
        finally:
            os.chdir(cwd_orig)

    def test_commute_peaks_verified_ranking(self):
        """Verifies the exact tidal swing calculation and rank ordering in data_commute_peaks.json."""
        peaks_path = os.path.join(DOCS_DIR, "data", "data_commute_peaks.json")
        with open(peaks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        top10 = data["top_tidal_swing"]
        assert len(top10) == 10

        # Verified Rank 1: Salmisaarenranta (Swing: 12,587)
        assert top10[0]["station_name"] == "Salmisaarenranta"
        assert top10[0]["tidal_swing"] == 12587
        assert top10[0]["morn_net"] == 7343
        assert top10[0]["eve_net"] == -5244

        # Verified Rank 2: Itämerentori (Swing: 11,860)
        assert top10[1]["station_name"] == "Itämerentori"
        assert top10[1]["tidal_swing"] == 11860

        # Verified Rank 3: Sompasaari (Swing: 10,781)
        assert top10[2]["station_name"] == "Sompasaari"
        assert top10[2]["tidal_swing"] == 10781
        assert top10[2]["morn_net"] == -7973
        assert top10[2]["eve_net"] == 2808

        # Swings must be strictly monotonically non-increasing
        swings = [x["tidal_swing"] for x in top10]
        assert swings == sorted(swings, reverse=True), "Top 10 tidal swings not sorted descending!"

    def test_weather_js_and_data_integrity(self):
        """Validates Phase 4 FMI weather module, data structures, and correlation guardrails."""
        js_path = os.path.join(DOCS_DIR, "js", "weather.js")
        assert os.path.exists(js_path), "weather.js is missing!"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Strictly relative fetch
        assert '"./data/data_daily_weather.json"' in js or "'./data/data_daily_weather.json'" in js

        # Parameter configuration contains all required parameters
        for p in ["tday", "tmax", "tmin", "precip", "snow"]:
            assert p in js, f"Missing parameter {p} in weather.js"

        # Separate dual Y-axes configured with physical units
        assert 'yAxisID: "y"' in js
        assert 'yAxisID: "y1"' in js
        assert "drawOnChartArea: false" in js, "Right axis must not duplicate grid lines"

        # Descriptive correlation without p-values or significance claims
        assert "p-value" not in js.lower()
        assert not re.search(r'\bp\s*<\s*0\.\d+', js, re.IGNORECASE), "Must not display statistical p-value threshold"
        assert "statistically significant" not in js.lower()

        # Verify underlying JSON data integrity
        weather_json_path = os.path.join(DOCS_DIR, "data", "data_daily_weather.json")
        with open(weather_json_path, "r", encoding="utf-8") as f:
            wdata = json.load(f)

        meta = wdata["meta"]
        assert meta["total_records"] == 856
        assert meta["calendar_days_per_city"] == 428
        assert "FMISID 100971" in meta["stations_fmi"]["Helsinki"]
        assert "FMISID 874863" in meta["stations_fmi"]["Espoo"]

        # Audit of unmapped trips
        audit = meta["unmapped_trips_audit"]
        assert audit["total_departures"] == 23981
        assert audit["total_returns"] == 26490
        assert audit["days_count"] == 428

        records = wdata["daily_records"]
        assert len(records) == 856

        helsinki_recs = [r for r in records if r["city"] == "Helsinki"]
        espoo_recs = [r for r in records if r["city"] == "Espoo"]
        assert len(helsinki_recs) == 428
        assert len(espoo_recs) == 428

        # Numerical verification of descriptive Pearson correlation
        import numpy as np

        h_dep = np.array([r["dep"] for r in helsinki_recs])
        h_tday = np.array([r["tday"] for r in helsinki_recs])
        h_precip = np.array([r["precip"] for r in helsinki_recs])
        r_h_tday = np.corrcoef(h_tday, h_dep)[0, 1]
        r_h_precip = np.corrcoef(h_precip, h_dep)[0, 1]

        assert 0.75 <= r_h_tday <= 0.82, f"Expected Helsinki r(tday) ~ +0.78, got {r_h_tday}"
        assert -0.32 <= r_h_precip <= -0.20, f"Expected Helsinki r(precip) ~ -0.26, got {r_h_precip}"

        e_dep = np.array([r["dep"] for r in espoo_recs])
        e_tday = np.array([r["tday"] for r in espoo_recs])
        e_precip = np.array([r["precip"] for r in espoo_recs])
        r_e_tday = np.corrcoef(e_tday, e_dep)[0, 1]
        r_e_precip = np.corrcoef(e_precip, e_dep)[0, 1]

        assert 0.70 <= r_e_tday <= 0.78, f"Expected Espoo r(tday) ~ +0.73, got {r_e_tday}"
        assert -0.35 <= r_e_precip <= -0.22, f"Expected Espoo r(precip) ~ -0.29, got {r_e_precip}"

    def test_forecast_js_and_cohort_integrity(self):
        """Validates Phase 5 Demand Forecasting module, cohort separation, and metric accuracy."""
        js_path = os.path.join(DOCS_DIR, "js", "forecast.js")
        assert os.path.exists(js_path), "forecast.js is missing!"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Strictly relative fetch of verified JSONs
        assert '"./data/data_model_summary.json"' in js or "'./data/data_model_summary.json'" in js
        assert '"./data/data_model_predictions_2025.json"' in js or "'./data/data_model_predictions_2025.json'" in js

        # No in-browser training or fitting
        assert "fit(" not in js and "train(" not in js

        # No p-values or significance claims
        assert "p-value" not in js.lower()
        assert not re.search(r'\bp\s*<\s*0\.\d+', js, re.IGNORECASE)
        assert "statistically significant" not in js.lower()

        # Flow terminology: net outflow / net inflow used, no truck dispatch command
        assert "Net Outflow" in js or "net outflow" in js.lower()
        assert "dispatch order" not in js.lower()

        # Check data_model_summary.json integrity
        summary_path = os.path.join(DOCS_DIR, "data", "data_model_summary.json")
        with open(summary_path, "r", encoding="utf-8") as f:
            sdata = json.load(f)

        meta = sdata["meta"]
        assert meta["test_sample_size"] == 2718
        assert meta["q1_low_usage_sample_size"] == 681

        # Check overall multi-model metrics (N=2,718)
        overall = {m["model_id"]: m for m in sdata["overall_metrics"]}
        assert overall["base"]["dep_wape"] == 17.58
        assert overall["base"]["dep_mae"] == 141.88
        assert overall["ridge"]["dep_wape"] == 28.00
        assert overall["ridge"]["dep_mae"] == 226.01
        assert overall["dt"]["dep_wape"] == 24.72
        assert overall["dt"]["dep_mae"] == 199.53

        # Check low-usage Q1 metrics (N=681)
        low_usage = {m["model_id"]: m for m in sdata["low_usage_metrics"]}
        assert low_usage["base"]["dep_wape"] == 33.83
        assert low_usage["ridge"]["dep_wape"] == 124.07
        assert low_usage["dt"]["dep_wape"] == 55.98

        # Check monthly breakdown (6 months: May to Oct 2025)
        monthly = sdata["monthly_wape_breakdown"]
        assert len(monthly) == 6
        assert monthly[0]["month"] == "2025-05"
        assert monthly[-1]["month"] == "2025-10"

        # Check ranking overlap (June Peak Ridge = 16/20)
        overlap = sdata["ranking_overlap_metrics"]
        assert len(overlap) == 6
        assert overlap[1]["ridge_deficit_overlap"] == "16/20"
        assert overlap[1]["ridge_spearman_rho"] == 0.713

        # Check predictions JSON record integrity
        preds_path = os.path.join(DOCS_DIR, "data", "data_model_predictions_2025.json")
        with open(preds_path, "r", encoding="utf-8") as f:
            pdata = json.load(f)

        records = pdata["records"]
        assert len(records) == 2718

        # Ensure all models have departures, returns, net flow
        first = records[0]
        for prefix in ["act_", "base_", "ridge_", "dt_"]:
            for metric in ["dep", "ret", "net"]:
                assert f"{prefix}{metric}" in first, f"Missing key {prefix}{metric}"

        # Verify cohort differentiation is clearly documented in index.html
        index_path = os.path.join(DOCS_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert "2,718" in html, "Multi-model test cohort N=2,718 must be stated in HTML"
        assert "3,170" in html, "Full-season reference cohort N=3,170 must be distinguished"
        assert "trips" in html.lower(), "MAE unit of trips must be explained"

    def test_github_pages_subpath_serving(self):
        """Validates that all assets and data files resolve properly when hosted on a repo subpath like /HSL_City_Bike_Project/."""
        import urllib.parse
        PORT = 8935
        SUBPATH = "/HSL_City_Bike_Project"

        class SubpathHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                # Map /HSL_City_Bike_Project/* -> DOCS_DIR/*
                if path == SUBPATH or path == f"{SUBPATH}/":
                    path = f"{SUBPATH}/index.html"
                if path.startswith(f"{SUBPATH}/"):
                    rel = path[len(SUBPATH) + 1 :]
                    return os.path.join(DOCS_DIR, rel)
                # Any request outside subpath returns 404 to ensure no accidental root leaks
                return os.path.join(DOCS_DIR, "__non_existent_outside_subpath__")

        httpd = socketserver.TCPServer(("127.0.0.1", PORT), SubpathHandler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            # 1. Probe the subpath index
            index_url = f"http://127.0.0.1:{PORT}{SUBPATH}/index.html"
            req = urllib.request.Request(index_url)
            with urllib.request.urlopen(req, timeout=3) as res:
                assert res.status == 200
                html = res.read().decode("utf-8")

            # 2. Extract all local script src, link href, and verify they resolve to HTTP 200 under the subpath
            import re
            import urllib.parse
            local_refs = re.findall(r'(?:href|src)=["\'](\./[^"\']+)["\']', html)
            assert len(local_refs) >= 5, f"Expected multiple relative asset links, got {local_refs}"

            for ref in local_refs:
                resolved_url = urllib.parse.urljoin(index_url, ref)
                assert f"{SUBPATH}/" in resolved_url, f"Asset did not resolve into subpath: {resolved_url}"
                with urllib.request.urlopen(urllib.request.Request(resolved_url), timeout=3) as ares:
                    assert ares.status == 200, f"Failed to load {resolved_url}"
                    assert len(ares.read()) > 0

            # 3. Extract all data JSON fetch URLs from JS modules and verify they resolve to HTTP 200 under the subpath
            js_files = ["map.js", "commute.js", "weather.js", "forecast.js"]
            for jf in js_files:
                with open(os.path.join(DOCS_DIR, "js", jf), "r", encoding="utf-8") as f:
                    js_code = f.read()
                fetch_calls = re.findall(r'fetch\(["\'](\./[^"\']+)["\']\)', js_code)
                assert len(fetch_calls) > 0, f"No fetch calls found in {jf}"
                for fc in fetch_calls:
                    resolved_data_url = urllib.parse.urljoin(index_url, fc)
                    assert f"{SUBPATH}/data/" in resolved_data_url, f"Data fetch did not resolve into subpath: {resolved_data_url}"
                    with urllib.request.urlopen(urllib.request.Request(resolved_data_url), timeout=3) as dres:
                        assert dres.status == 200, f"Failed to load {resolved_data_url}"
                        raw_json = json.loads(dres.read().decode("utf-8"))
                        assert raw_json is not None

            # 4. Verify that requests outside the subpath (e.g. /data/data_stations.json) return 404
            bad_url = f"http://127.0.0.1:{PORT}/data/data_stations.json"
            try:
                urllib.request.urlopen(urllib.request.Request(bad_url), timeout=2)
                assert False, "Should have failed with 404 outside subpath"
            except urllib.error.HTTPError as e:
                assert e.code == 404, f"Expected 404, got {e.code}"

        finally:
            httpd.shutdown()
            httpd.server_close()
