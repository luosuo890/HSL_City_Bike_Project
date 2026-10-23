"""
Build Technical Report PDF for HSL City Bike Project.
Generates an executive, publication-quality 5-page PDF technical report
at reports/HSL_City_Bike_Technical_Report.pdf based strictly on reports/findings.md.
"""

import os
import sys
import pymupdf

# Colors
C_NAVY = (0.063, 0.169, 0.306)       # #102B4E - Primary Brand
C_BLUE = (0.0, 0.478, 0.788)         # #007AC9 - HSL Blue Accent
C_SLATE = (0.290, 0.333, 0.408)      # #4A5568 - Body text / Muted
C_LIGHT_BG = (0.965, 0.976, 0.988)   # #F6F8FB - Card background
C_BLUE_BG = (0.937, 0.965, 0.992)    # #EFF6FC - Accent card background
C_BORDER = (0.850, 0.880, 0.920)     # #D9E0EB - Card border
C_DARK = (0.12, 0.14, 0.17)          # #1F242B - Headings / Dark text
C_WHITE = (1.0, 1.0, 1.0)
C_RED = (0.78, 0.15, 0.15)           # Deficit
C_GREEN = (0.12, 0.55, 0.28)         # Surplus

PAGE_W = 595.3   # A4 width (pt)
PAGE_H = 841.9   # A4 height (pt)
MARGIN_L = 40.0
MARGIN_R = 555.3
USABLE_W = MARGIN_R - MARGIN_L       # 515.3 pt


def draw_header_footer(page, page_num, total_pages=5):
    """Draw consistent running header and footer on each page."""
    # Running Header
    page.insert_text(
        pymupdf.Point(MARGIN_L, 27),
        "HSL CITY BIKE ALLOCATION | TECHNICAL EVALUATION REPORT",
        fontname="hebo",
        fontsize=7.5,
        color=C_NAVY
    )
    page.insert_text(
        pymupdf.Point(MARGIN_R - 150, 27),
        "HELSINKI & ESPOO (2024-2025)",
        fontname="helv",
        fontsize=7.5,
        color=C_SLATE
    )
    page.draw_line(
        pymupdf.Point(MARGIN_L, 32),
        pymupdf.Point(MARGIN_R, 32),
        color=C_BORDER,
        width=0.75
    )

    # Running Footer
    page.draw_line(
        pymupdf.Point(MARGIN_L, PAGE_H - 28),
        pymupdf.Point(MARGIN_R, PAGE_H - 28),
        color=C_BORDER,
        width=0.75
    )
    page.insert_text(
        pymupdf.Point(MARGIN_L, PAGE_H - 18),
        "Canvas Workshop 3 | Chenyu Wu, Jizhou Wang, Jussi Honkio | Data: HSL & FMI Open Data (CC BY 4.0)",
        fontname="helv",
        fontsize=7.2,
        color=C_SLATE
    )
    page_str = f"Page {page_num} of {total_pages}"
    page.insert_text(
        pymupdf.Point(MARGIN_R - 55, PAGE_H - 18),
        page_str,
        fontname="hebo",
        fontsize=7.5,
        color=C_NAVY
    )


def draw_section_bar(page, y, title, subtitle=None):
    """Draw a styled section header with accent bar."""
    bar_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + 3.5, y + 14)
    page.draw_rect(bar_rect, color=C_BLUE, fill=C_BLUE)

    page.insert_text(
        pymupdf.Point(MARGIN_L + 8, y + 11),
        title.upper(),
        fontname="hebo",
        fontsize=9.5,
        color=C_NAVY
    )

    if subtitle:
        sw = pymupdf.get_text_length(title.upper(), fontname="hebo", fontsize=9.5)
        page.insert_text(
            pymupdf.Point(MARGIN_L + 16 + sw, y + 11),
            f"|  {subtitle}",
            fontname="helv",
            fontsize=7.8,
            color=C_SLATE
        )

    page.draw_line(
        pymupdf.Point(MARGIN_L, y + 17),
        pymupdf.Point(MARGIN_R, y + 17),
        color=C_BORDER,
        width=0.5
    )
    return y + 24


def draw_card(page, rect, fill=C_LIGHT_BG, border=C_BORDER, border_width=0.5):
    """Draw a styled background card."""
    page.draw_rect(rect, color=border, fill=fill, width=border_width)


def draw_table(page, rect, headers, rows, col_widths, align_rights=None, row_height=15.0):
    """Draw a clean, professional data table."""
    if align_rights is None:
        align_rights = set()

    x0 = rect.x0
    y0 = rect.y0
    table_w = rect.width

    # Header Row
    hdr_h = 16.0
    hdr_rect = pymupdf.Rect(x0, y0, x0 + table_w, y0 + hdr_h)
    page.draw_rect(hdr_rect, color=C_NAVY, fill=C_NAVY)

    cx = x0
    for i, h in enumerate(headers):
        cw = col_widths[i]
        align_mode = pymupdf.TEXT_ALIGN_RIGHT if i in align_rights else pymupdf.TEXT_ALIGN_LEFT
        cell_rect = pymupdf.Rect(cx + 2.5, y0 + 1.5, cx + cw - 2.5, y0 + hdr_h - 1.5)
        rc = page.insert_textbox(cell_rect, h, fontname="hebo", fontsize=6.7, color=C_WHITE, align=align_mode)
        assert rc >= 0, f"Table header {h} overflow: {rc}"
        cx += cw

    # Data Rows
    cy = y0 + hdr_h
    for r_idx, row in enumerate(rows):
        row_bg = C_WHITE if r_idx % 2 == 0 else C_LIGHT_BG
        r_rect = pymupdf.Rect(x0, cy, x0 + table_w, cy + row_height)
        page.draw_rect(r_rect, color=C_BORDER, fill=row_bg, width=0.4)

        cx = x0
        for i, val in enumerate(row):
            cw = col_widths[i]
            align_mode = pymupdf.TEXT_ALIGN_RIGHT if i in align_rights else pymupdf.TEXT_ALIGN_LEFT
            cell_rect = pymupdf.Rect(cx + 3, cy + 2, cx + cw - 3, cy + row_height - 1)

            text_color = C_DARK
            font_choice = "helv"
            val_str = str(val)
            if "trips" in val_str and "-" in val_str:
                text_color = C_RED
                font_choice = "hebo"
            elif "trips" in val_str and "+" in val_str:
                text_color = C_GREEN
                font_choice = "hebo"
            elif i == 0 or (len(row) > 1 and i == 1 and "station" in headers[1].lower()):
                font_choice = "hebo" if i == 0 else "helv"

            rc = page.insert_textbox(cell_rect, val_str, fontname=font_choice, fontsize=6.8, color=text_color, align=align_mode)
            assert rc >= 0, f"Table cell ({r_idx}, {i}) '{val_str}' overflow: {rc}"
            cx += cw
        cy += row_height

    return cy


def build_page_1(doc):
    """Build Page 1: Title, Executive Summary, Research Questions, Data Pipeline & Hygiene Filters."""
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header_footer(page, 1)

    # 1. Main Title Banner Block
    banner_rect = pymupdf.Rect(MARGIN_L, 40, MARGIN_R, 124)
    draw_card(page, banner_rect, fill=C_BLUE_BG, border=C_BLUE, border_width=1.0)

    accent_bar = pymupdf.Rect(MARGIN_L, 40, MARGIN_L + 5, 124)
    page.draw_rect(accent_bar, color=C_BLUE, fill=C_BLUE)

    title_text = "Seasonal and Weather-Based HSL City Bike Allocation"
    page.insert_text(pymupdf.Point(MARGIN_L + 14, 58), title_text, fontname="hebo", fontsize=14.5, color=C_NAVY)

    subtitle_text = "Comprehensive Empirical Findings, Leakage-Free Predictive Benchmarking & Rebalancing Triage"
    page.insert_text(pymupdf.Point(MARGIN_L + 14, 72), subtitle_text, fontname="helv", fontsize=8.8, color=C_SLATE)

    meta_box = pymupdf.Rect(MARGIN_L + 14, 79, MARGIN_R - 14, 120)
    meta_str = (
        "Course Project: Canvas Workshop 3 (Machine Learning in Operations)   |   Target: City-Bike Operators & HSL Transport Planners\n"
        "Authors: Chenyu Wu, Jizhou Wang, Jussi Honkio   |   System Scope: Helsinki & Espoo Municipalities (457 Stations)\n"
        "Temporal Coverage: 2 Full Cycling Seasons (2024 & 2025; April 1 – October 31 each; 14 Operating Months Total; 4,951,245 Valid Trips)\n"
        "Artifacts: Production Data Pipeline, Leakage-Free Models, GIS Triage Gallery & Interactive GitHub Pages Planning Platform"
    )
    rc_meta = page.insert_textbox(meta_box, meta_str, fontname="helv", fontsize=7.0, color=C_NAVY)
    assert rc_meta >= 0, f"Page 1 metadata overflow: {rc_meta}"

    y = 132

    # 2. Section 1: Executive Summary & Operational Motivation
    y = draw_section_bar(page, y, "1. Executive Summary & Canvas Problem Definition", "Operational Fleet Management Context")

    sum_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 125)
    draw_card(page, sum_rect, fill=C_LIGHT_BG, border=C_BORDER)
    sum_text = (
        "Efficient urban bike-sharing in northern climates is governed by seasonal swings, subarctic weather transitions, and diurnal commuter tides. "
        "Grounded in the HSL City Bike Project Canvas, this study evaluates two full cycling seasons (2024–2025; 14 operating months) across Helsinki and Espoo "
        "to resolve fundamental fleet allocation challenges: where should bikes be concentrated, how reliably can station demand be forecast without "
        "data leakage, and which stations suffer from chronic stockouts or dock congestion.\n\n"
        "Core Empirical Conclusions: (1) Out of 5.10M raw trips, 4,951,245 clean journeys (97.04% retention) were synthesized with official ArcGIS station "
        "coordinates and FMI ground-truth weather. (2) Daily ridership exhibits a sharp unimodal summer envelope and strong temperature correlation "
        "(r = +0.74), but temperature co-moves with daylight and holiday schedules, establishing descriptive rather than causal links. (3) Weekday demand "
        "features an evening rush surge (+70% to +105% over morning) and commuter tidal reversals between residential and business hubs. (4) An out-of-time "
        "predictive benchmark proves that a historical same-month baseline achieves lowest volume error (17.58% WAPE), while causal Ridge regression "
        "excels at early-season deficit rank ordering (up to 80% Top-20 match). (5) A zero-dependency GitHub Pages planning platform is deployed."
    )
    rc_sum = page.insert_textbox(sum_rect + (8, 6, -8, -6), sum_text, fontname="helv", fontsize=7.1, color=C_DARK)
    assert rc_sum >= 0, f"Page 1 exec summary overflow: {rc_sum}"
    y += 133

    # 3. Section 2: Core Research Questions
    y = draw_section_bar(page, y, "2. Core Research Questions", "Investigative Framework")

    rq_box = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 122)
    draw_card(page, rq_box, fill=C_WHITE, border=C_BORDER)
    rq_text = (
        "Q1. Seasonal & Climatological Trajectories: How does station-level and municipal demand evolve across the 7-month operating window "
        "(April–October), and how strongly does daily trip volume co-move with ground-truth temperature and precipitation observations?\n\n"
        "Q2. Intraday & Weekday/Weekend Regimes: How does demand diverge between workdays and weekends? To what extent do morning (07:00–09:00) "
        "and evening (16:00–18:00) peak rush hours exhibit directional volume asymmetries that monthly aggregates obscure?\n\n"
        "Q3. Out-of-Time Demand Predictability: Can a historical same-month baseline (2024 -> 2025) reliably forecast departures and returns? "
        "How does it compare against causal, leakage-free Ridge regression and decision trees when strictly restricted to preceding-month lags?\n\n"
        "Q4. Rebalancing Triage & Network Bottlenecks: Which stations exhibit persistent, severe directional flow imbalances (net_flow = returns - departures), "
        "and how should transport planners prioritize stations facing chronic bicycle depletion (sinks) versus dock saturation (sources)?"
    )
    rc_rq = page.insert_textbox(rq_box + (8, 6, -8, -6), rq_text, fontname="helv", fontsize=7.0, color=C_DARK)
    assert rc_rq >= 0, f"Page 1 RQ overflow: {rc_rq}"
    y += 130

    # 4. Section 3: Data Ingestion, Hygiene Filters & Metadata Mapping
    y = draw_section_bar(page, y, "3. Data Ingestion, Hygiene Filters & Unmapped Docks", "Data Governance & Traceability")

    col_w = (USABLE_W - 10) / 2
    left_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + col_w, y + 190)
    draw_card(page, left_rect, fill=C_LIGHT_BG, border=C_BORDER)

    left_text = (
        "HSL Origin-Destination (OD) Journey Records:\n"
        "• Raw Ingested Trips: 5,102,233 records across 14 monthly CSVs from official HSL Open Data (2,585,668 in 2024; 2,516,565 in 2025).\n"
        "• Valid Clean Records Retained: 4,951,245 trips (2,507,175 in 2024, 96.96% retention; 2,444,070 in 2025, 97.12% retention; Overall: 97.04%).\n\n"
        "Strict 4-Part Data Hygiene Filtering Rules:\n"
        "1. Trip Duration: 10s <= t <= 86,400s (24h). Discards accidental instant checkouts and unreturned/lost bicycles.\n"
        "2. Trip Distance: Covered distance >= 10m. Eliminates stationary dock sensor testing and immediate re-docking.\n"
        "3. Speed Boundary: Mean velocity <= 10.0 m/s (~36 km/h). Filters motorized transit boardings and GPS teleportation glitches.\n"
        "4. Chronological Integrity: Return timestamp >= Departure timestamp.\n"
        "• Midnight Crossing Attribution: 21,532 trips (0.86%) in 2024 and 19,957 trips (0.82%) in 2025 crossed midnight; departures are attributed to day D1 at origin, returns to D2 at destination."
    )
    rc_l = page.insert_textbox(left_rect + (6, 6, -6, -6), left_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_l >= 0, f"Page 1 left col overflow: {rc_l}"

    right_rect = pymupdf.Rect(MARGIN_L + col_w + 10, y, MARGIN_R, y + 190)
    draw_card(page, right_rect, fill=C_LIGHT_BG, border=C_BORDER)

    right_text = (
        "Station GIS Metadata & Coordinate Alignment:\n"
        "• Ingested from official HSL ArcGIS REST feature service covering 457 active stations with English/Finnish/Swedish names, capacity, and WGS84 coordinates.\n"
        "• 454 stations have verified geographic coordinates and are mapped.\n\n"
        "Audited Unmapped Stations (Zero Silent Imputation):\n"
        "• 4 stations in 2024 (IDs 710, 768, 997, 999; 26 rows) and 7 in 2025 (IDs 626, 710, 716, 754, 768, 997, 999; 45 rows) represent maintenance workshops or pop-up test racks absent from the ArcGIS layer.\n"
        "• Preserved as NaN for coordinates/municipality to avoid synthetic GIS distortion. Retained in system trip totals (23,981 departures in 2025).\n\n"
        "FMI Retrospective Ground-Truth Weather Observations:\n"
        "• Downloaded via FMI WFS API for Helsinki Kaisaniemi (FMISID 100971) and Espoo Tapiola (FMISID 874863). 428 calendar days per station across both seasons; 100% complete across mean, min, max temperature, precipitation, and snow depth. FMI '-1.0' code converted to 0.0 mm."
    )
    rc_r = page.insert_textbox(right_rect + (6, 6, -6, -6), right_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_r >= 0, f"Page 1 right col overflow: {rc_r}"
    y += 198

    # Bottom Callout: Calendar & Operating Days Normalization
    call_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 46)
    draw_card(page, call_rect, fill=C_BLUE_BG, border=C_BLUE)
    call_text = (
        "Operating-Day Calendar Normalization Standard: Each 214-day cycling season consists of exactly 154 weekdays and 60 weekend days. "
        "To eliminate calendar-composition bias (e.g., months with 5 weekends vs. 4), all intraday and peak-hour metrics throughout this report and "
        "interactive tools are reported as Operating-Day Normalized Daily Averages (trips / operating days), never as raw sum comparisons."
    )
    rc_call = page.insert_textbox(call_rect + (8, 6, -8, -6), call_text, fontname="hebo", fontsize=7.0, color=C_NAVY)
    assert rc_call >= 0, f"Page 1 bottom callout overflow: {rc_call}"


def build_page_2(doc):
    """Build Page 2: Empirical Findings: Seasonal Trajectory, FMI Weather & Commuter Asymmetries."""
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header_footer(page, 2)

    y = 38

    # 1. Section 4: Seasonal Dynamics & Municipal Breakdown
    y = draw_section_bar(page, y, "4. Seasonal Ridership Trajectory & Municipal Divergence", "Macro Demand Patterns")

    kpi_h = 38
    kpi_w = (USABLE_W - 16) / 3

    # KPI 1
    kpi1_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + kpi_w, y + kpi_h)
    draw_card(page, kpi1_rect, fill=C_LIGHT_BG, border=C_BORDER)
    page.insert_text(pymupdf.Point(MARGIN_L + 8, y + 12), "TOTAL VALID RIDERSHIP", fontname="hebo", fontsize=6.2, color=C_SLATE)
    page.insert_text(pymupdf.Point(MARGIN_L + 8, y + 24), "4,951,245 Trips", fontname="hebo", fontsize=11.0, color=C_NAVY)
    page.insert_text(pymupdf.Point(MARGIN_L + 8, y + 33), "2024: 2.51M | 2025: 2.44M (-2.5% YoY)", fontname="helv", fontsize=6.2, color=C_DARK)

    # KPI 2
    kpi2_rect = pymupdf.Rect(MARGIN_L + kpi_w + 8, y, MARGIN_L + 2 * kpi_w + 8, y + kpi_h)
    draw_card(page, kpi2_rect, fill=C_LIGHT_BG, border=C_BORDER)
    page.insert_text(pymupdf.Point(MARGIN_L + kpi_w + 16, y + 12), "HELSINKI METROPOLITAN SHARE", fontname="hebo", fontsize=6.2, color=C_SLATE)
    page.insert_text(pymupdf.Point(MARGIN_L + kpi_w + 16, y + 24), "88.8% Regional Share", fontname="hebo", fontsize=11.0, color=C_BLUE)
    page.insert_text(pymupdf.Point(MARGIN_L + kpi_w + 16, y + 33), "2.20M (2024) | 2.17M (2025) Trips", fontname="helv", fontsize=6.2, color=C_DARK)

    # KPI 3
    kpi3_rect = pymupdf.Rect(MARGIN_L + 2 * kpi_w + 16, y, MARGIN_R, y + kpi_h)
    draw_card(page, kpi3_rect, fill=C_LIGHT_BG, border=C_BORDER)
    page.insert_text(pymupdf.Point(MARGIN_L + 2 * kpi_w + 24, y + 12), "ESPOO SUBURBAN SHARE", fontname="hebo", fontsize=6.2, color=C_SLATE)
    page.insert_text(pymupdf.Point(MARGIN_L + 2 * kpi_w + 24, y + 24), "11.2% Regional Share", fontname="hebo", fontsize=11.0, color=C_NAVY)
    page.insert_text(pymupdf.Point(MARGIN_L + 2 * kpi_w + 24, y + 33), "294k (2024) | 260k (2025) Trips", fontname="helv", fontsize=6.2, color=C_DARK)

    y += kpi_h + 8

    # Seasonal narrative
    seas_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 80)
    draw_card(page, seas_rect, fill=C_WHITE, border=C_BORDER)
    seas_text = (
        "• Unimodal Seasonal Envelope: Demand traces a pronounced summer unimodal bell curve governed by high-latitude Nordic daylight and climate. "
        "System ridership peaks in July and August (450,000–492,000 trips/month) and contracts steeply during the spring and autumn shoulder months "
        "(April: 162,000–243,000 trips; October: 198,000–207,000 trips).\n"
        "• Municipal Structural Disparity: Helsinki commands nearly 90% of regional activity, supported by dense inner-city cycling grids, "
        "intermodal train hubs (Central Station, Pasila), and high docking density. Espoo commands 11.2%, anchored by West Metro feeder hubs (Matinkylä, "
        "Niittykumpu) and the Aalto University Otaniemi campus. Espoo trips exhibit higher leisure elasticity and lower absolute shoulder resilience."
    )
    rc_seas = page.insert_textbox(seas_rect + (8, 6, -8, -6), seas_text, fontname="helv", fontsize=7.0, color=C_DARK)
    assert rc_seas >= 0, f"Page 2 seasonal narrative overflow: {rc_seas}"
    y += 88

    # 2. Section 5: Descriptive Weather Associations & Climatological Confounders
    y = draw_section_bar(page, y, "5. FMI Weather Observations & Confounder Disclaimers", "Retrospective Climatological Correlations")

    weath_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 96)
    draw_card(page, weath_rect, fill=C_LIGHT_BG, border=C_BORDER)
    weath_text = (
        "Empirical Ground-Truth Correlation Analysis (214 daily observations in 2025 across Helsinki & Espoo):\n"
        "• Temperature Sensitivity: Daily trips exhibit strong positive linear correlation with mean daily temperature (r = +0.737 in Helsinki, r = +0.665 in Espoo) "
        "and maximum daily temperature (r = +0.788 in Helsinki, r = +0.751 in Espoo). Ridership rises continuously from 5°C to 25°C.\n"
        "• Precipitation Impact: Daily volume displays a moderate negative correlation with rainfall (r = -0.251 in Helsinki, r = -0.289 in Espoo). "
        "Rainfall exceeding 5.0 mm suppresses weekday ridership by 20%–35% relative to seasonal baselines.\n"
        "• CRITICAL METHODOLOGICAL DISCLAIMER (Correlation != Causation): While warm, sunny days record high bike usage, Nordic summer temperature "
        "is strongly collinear with astronomical daylight (19 hours in June vs. 9 hours in October), university exam terms, and institutional summer "
        "shutdowns (July vacation). These empirical figures represent descriptive seasonal co-movements, not isolated causal elasticity."
    )
    rc_weath = page.insert_textbox(weath_rect + (8, 6, -8, -6), weath_text, fontname="helv", fontsize=7.0, color=C_DARK)
    assert rc_weath >= 0, f"Page 2 weather text overflow: {rc_weath}"
    y += 104

    # 3. Section 6: Diurnal Dynamics & Peak Hour Commuter Asymmetry
    y = draw_section_bar(page, y, "6. Diurnal Profiles & The Commuter Evening Rush Surge", "Operating-Day Normalized Intraday Regimes")

    diurn_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 114)
    draw_card(page, diurn_rect, fill=C_WHITE, border=C_BORDER)
    diurn_text = (
        "Operating-Day Normalized Departure Dynamics (154 Weekdays vs. 60 Weekend Days per 214-day Season):\n"
        "• Workday vs. Weekend Totals: Weekday volume exceeds weekend volume by +23.4% to +28.8% across both seasons. "
        "Helsinki: Weekday 10,708–10,985 trips/day vs. Weekend 8,530–8,679 trips/day; Espoo: Weekday 1,287–1,460 trips/day vs. Weekend 1,030–1,149 trips/day.\n"
        "• Morphological Divergence: Weekdays follow a bimodal distribution with a sharp morning commute peak at 08:00 (~643–790 trips/hr in Helsinki) "
        "and an elongated evening commute plateau from 16:00 to 18:00 (~1,112–1,136 trips/hr). Weekends exhibit a smooth unimodal leisure curve (12:00–17:00).\n"
        "• The Marked Evening Peak Surge (+70% to +105% Higher than Morning Peak):\n"
        "  - Helsinki: Morning (07:00–09:00) 1,208–1,287 trips/day vs. Evening (16:00–18:00) 2,154–2,194 trips/day (+70.5% in 2024; +78.4% in 2025).\n"
        "  - Espoo: Morning 141–150 trips/day vs. Evening 276–308 trips/day (+105.4% in 2024; +95.9% in 2025).\n"
        "  - Behavioral Driver: Morning trips are concentrated, direct home-to-work utilitarian journeys. Evening trips combine homeward commutes with dining, "
        "errands, waterfront leisure, and social trips, creating an expanded, dispersed travel peak."
    )
    rc_diurn = page.insert_textbox(diurn_rect + (8, 6, -8, -6), diurn_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_diurn >= 0, f"Page 2 diurnal text overflow: {rc_diurn}"
    y += 122

    # Embedded Figure 5 (Hourly Departure Curves)
    fig5_path = "reports/figures/fig5_hourly_departure_curves_weekday_weekend.png"
    if os.path.exists(fig5_path):
        img_h = 190
        img_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + img_h)
        page.insert_image(img_rect, filename=fig5_path, keep_proportion=True)
        y += img_h + 4

        cap_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 24)
        cap_text = (
            "Figure 5: Operating-day normalized hourly departures (0-23h) across Helsinki (left) and Espoo (right). "
            "Contrasts bimodal weekday curves against unimodal weekend plateaus, highlighting the 70%-105% evening surge over morning rush."
        )
        rc_cap = page.insert_textbox(cap_rect, cap_text, fontname="hebi", fontsize=6.8, color=C_SLATE, align=pymupdf.TEXT_ALIGN_CENTER)
        assert rc_cap >= 0, f"Page 2 caption overflow: {rc_cap}"


def build_page_3(doc):
    """Build Page 3: Predictive Modeling & Baseline Results."""
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header_footer(page, 3)

    y = 38

    # 1. Section 7: Formulation of Causal, Leakage-Free Predictive Models
    y = draw_section_bar(page, y, "7. Causal Within-Season Machine Learning Formulation", "Solution B Operational Architecture")

    ml_form_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 84)
    draw_card(page, ml_form_rect, fill=C_BLUE_BG, border=C_BLUE)
    ml_form_text = (
        "• Operational Decision Epoch: At the beginning of month m (May through October), fleet operators observe completed trip volume through "
        "month m-1. The task is to forecast completed monthly departures and returns for each station in month m to guide monthly rebalancing.\n"
        "• Zero Lookahead Weather Guarantee: 2025 ground-truth weather was strictly excluded from predictive models. In subarctic Finland, long-range "
        "numerical weather predictions weeks in advance exhibit zero practical skill, and using actual historical weather would introduce fatal data leakage.\n"
        "• Causal Feature Space (10 dimensions): Prior-month lag volume (lag_departures or lag_returns), station docking capacity, latitude, "
        "longitude, municipality indicator (is_helsinki), and month indicators (m_6 to m_10) to capture system-wide seasonal trajectory."
    )
    rc_ml = page.insert_textbox(ml_form_rect + (8, 6, -8, -6), ml_form_text, fontname="helv", fontsize=7.0, color=C_NAVY)
    assert rc_ml >= 0, f"Page 3 ML form overflow: {rc_ml}"
    y += 92

    # 2. Section 8: Unified Multi-Model Benchmark (Table)
    y = draw_section_bar(page, y, "8. Multi-Model Benchmark on Unified Test Cohort", "May–October 2025 (Identical N = 2,718 Station-Months)")

    tbl_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 136)
    headers = [
        "Evaluation Dimension / Target Metric",
        "1. Same-Month Baseline (2024)",
        "2. Ridge Regression (α=10)",
        "3. Decision Tree (depth=6)"
    ]
    rows = [
        ["Departures MAE (trips / station-month)", "141.88 trips", "226.01 trips", "199.53 trips"],
        ["Departures WAPE (%) - Volume Error", "17.58%", "28.00%", "24.72%"],
        ["Returns MAE (trips / station-month)", "139.73 trips", "226.52 trips", "195.63 trips"],
        ["Returns WAPE (%) - Volume Error", "17.31%", "28.06%", "24.23%"],
        ["Low-Demand Stations WAPE (Q1 <= 198 trips; N=681)", "33.83% (MAE: 41.92)", "124.07% (MAE: 153.74)", "55.98% (MAE: 69.37)"],
        ["Top-20 Net Deficit Overlap Range (Rank Order)", "40% – 75% (Avg: 60.8%)", "60% – 80% (Avg: 69.2%)", "25% – 40% (Avg: 31.7%)"],
        ["Top-20 Net Surplus Overlap Range (Rank Order)", "35% – 75% (Avg: 53.3%)", "60% – 75% (Avg: 65.8%)", "25% – 35% (Avg: 30.8%)"],
        ["Spearman Net Flow Rank Correlation (ρ) Range", "0.483 – 0.663 (Avg: 0.582)", "0.455 – 0.761 (Avg: 0.650)", "0.123 – 0.358 (Avg: 0.242)"]
    ]
    col_w = [185.3, 110.0, 110.0, 110.0]
    aligns = {1, 2, 3}
    y_after_tbl = draw_table(page, tbl_rect, headers, rows, col_w, align_rights=aligns, row_height=15.0)
    y = y_after_tbl + 8

    # Full-Season Reference Callout
    ref_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 42)
    draw_card(page, ref_rect, fill=C_LIGHT_BG, border=C_BORDER)
    ref_text = (
        "Full-Season Baseline Reference Cohort (April–October 2025, N = 3,170 test station-months across all 7 months):\n"
        "Departures MAE = 147.60 trips/month | WAPE = 19.23% | RMSE = 270.87 trips | Median Absolute Error = 73.0 trips | Pearson r = 0.959.\n"
        "Returns MAE = 145.99 trips/month | WAPE = 19.02% | RMSE = 272.08 trips | Median Absolute Error = 71.0 trips | Pearson r = 0.959."
    )
    rc_ref = page.insert_textbox(ref_rect + (6, 4, -6, -4), ref_text, fontname="hebo", fontsize=6.8, color=C_DARK)
    assert rc_ref >= 0, f"Page 3 ref callout overflow: {rc_ref}"
    y += 48

    # Model Comparison Insights
    ins_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 112)
    draw_card(page, ins_rect, fill=C_WHITE, border=C_BORDER)
    ins_text = (
        "1. For Absolute Demand Volume: Historical Same-Month Baseline Achieves Lowest Error (17.58% vs. 28.00% Ridge vs. 24.72% Tree):\n"
        "   In Helsinki's subarctic climate, month-to-month transitions involve sharp seasonal step-changes (April thaw -> May warmup; August warmth -> "
        "   September chill). Preceding-month lag models suffer from inherent transitional delay, whereas the prior year's same calendar month naturally "
        "   aligns with solar irradiance, school term starts, and summer holiday schedules.\n"
        "2. Severe Failure of Linear Models on Low-Demand Stations (Ridge WAPE = 124.07% on Q1 Docks):\n"
        "   On the quietest 25% of stations (Q1 <= 198 trips/month, N = 681), Ridge incurs a 124% WAPE error. Global month indicator coefficients "
        "   apply rigid additive shifts across all stations, causing massive relative overprediction at peripheral docks. Baseline preserves localized scale (33.8% WAPE).\n"
        "3. For Commuter Deficit Priority Screening: Ridge Regression Excels in Early/Mid-Season (Up to 80% Top-20 Overlap):\n"
        "   In May through August, Ridge achieves 60%–80% overlap on Top-20 deficit stations (Spearman ρ up to 0.761). Its monotonic linear slope "
        "   effectively magnifies heavy commuter sinks (e.g. Pasila). Planners should use Baseline for fleet sizing and Ridge for priority sink screening."
    )
    rc_ins = page.insert_textbox(ins_rect + (8, 6, -8, -6), ins_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_ins >= 0, f"Page 3 insights overflow: {rc_ins}"
    y += 120

    # Embedded Figure 7 (Forecast Evaluation Actual vs Baseline)
    fig7_path = "reports/figures/fig7_forecast_evaluation_actual_vs_baseline_2025.png"
    if os.path.exists(fig7_path):
        img_h = 180
        img_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + img_h)
        page.insert_image(img_rect, filename=fig7_path, keep_proportion=True)
        y += img_h + 4

        cap_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 24)
        cap_text = (
            "Figure 7: Out-of-time demand evaluation (2025 actual vs. same-month baseline). Left: Scatter against 1:1 diagonal (N=3,170, r=0.959). "
            "Right: Monthly MAE and WAPE progression showing spring transition variability and high autumn stability (September WAPE 12.61%)."
        )
        rc_cap = page.insert_textbox(cap_rect, cap_text, fontname="hebi", fontsize=6.8, color=C_SLATE, align=pymupdf.TEXT_ALIGN_CENTER)
        assert rc_cap >= 0, f"Page 3 caption overflow: {rc_cap}"


def build_page_4(doc):
    """Build Page 4: Station Triage, Macro Flow Imbalances & Diurnal Tidal Reversals."""
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header_footer(page, 4)

    y = 38

    # 1. Section 9: Macro Flow Imbalances & Spatial Polarization
    y = draw_section_bar(page, y, "9. Spatial Polarization of Cumulative Net Flow", "Directional Imbalance Across 454 Mapped Stations")

    macro_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 68)
    draw_card(page, macro_rect, fill=C_LIGHT_BG, border=C_BORDER)
    macro_text = (
        "• Macro Net Flow Metric: net_flow = returns - departures calculated over all 14 operating months across 454 stations with coordinates.\n"
        "• Systemic Deficit Sinks (Red, Bike Depletion Vulnerability): Concentrated around major rail interchanges and radial transit arterials "
        "where commuters arrive by train or bus and depart on city bikes, causing chronic docking shortages and bike depletion.\n"
        "• Systemic Surplus Sources (Blue, Dock Congestion Vulnerability): Concentrated along scenic waterfronts, central commercial plazas, and "
        "dense residential docks where riders dock bikes upon arriving home or at leisure destinations, threatening return blocking."
    )
    rc_macro = page.insert_textbox(macro_rect + (8, 6, -8, -6), macro_text, fontname="helv", fontsize=7.0, color=C_DARK)
    assert rc_macro >= 0, f"Page 4 macro text overflow: {rc_macro}"
    y += 76

    # 2. Section 10: Station Triage Allocation Priority Review Lists (Side-by-Side Tables)
    y = draw_section_bar(page, y, "10. Station Triage Rebalancing Priority Lists", "Top 5 Chronic Deficit Sinks vs. Top 5 Chronic Surplus Sources")

    col_w = (USABLE_W - 12) / 2

    def_headers = ["ID", "Deficit Station (Depletion Sink)", "City", "Cap", "Net Flow"]
    def_rows = [
        ["113", "Pasila railway station", "Helsinki", "40", "-11,014 trips"],
        ["120", "Mäkelänkatu", "Helsinki", "28", "-5,275 trips"],
        ["203", "Opastinsilta", "Helsinki", "40", "-5,049 trips"],
        ["043", "Karhupuisto", "Helsinki", "24", "-4,421 trips"],
        ["162", "Leppäsuonaukio", "Helsinki", "28", "-3,750 trips"]
    ]
    def_w = [20, 118, 36, 22, 55.65]
    def_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + col_w, y + 91)
    draw_table(page, def_rect, def_headers, def_rows, def_w, align_rights={0, 3, 4}, row_height=15.0)

    sur_headers = ["ID", "Surplus Station (Dock Saturation)", "City", "Cap", "Net Flow"]
    sur_rows = [
        ["011", "Unioninkatu", "Helsinki", "22", "+3,474 trips"],
        ["012", "Kanavaranta", "Helsinki", "34", "+3,081 trips"],
        ["125", "Arielinkatu", "Helsinki", "16", "+3,027 trips"],
        ["404", "Sompasaari", "Helsinki", "14", "+2,900 trips"],
        ["065", "Hernesaarenranta", "Helsinki", "40", "+2,572 trips"]
    ]
    sur_w = [20, 118, 36, 22, 55.65]
    sur_rect = pymupdf.Rect(MARGIN_L + col_w + 12, y, MARGIN_R, y + 91)
    draw_table(page, sur_rect, sur_headers, sur_rows, sur_w, align_rights={0, 3, 4}, row_height=15.0)

    y += 98

    # 3. Section 11: Weekday Peak-Hour Commuter Tidal Reversal
    y = draw_section_bar(page, y, "11. Diurnal Commuter Tidal Reversal", "Peak Hour Asymmetry: Morning (07:00–09:00) vs. Evening (16:00–18:00)")

    tide_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 142)
    draw_card(page, tide_rect, fill=C_WHITE, border=C_BORDER)
    tide_text = (
        "Station Net Flow Reversal Across Standardized 2-Hour Weekday Peak Windows:\n"
        "• Quadrant II: Residential Feeder Docks (Morning Deficit -> Evening Surplus):\n"
        "  Sompasaari (Station 404, Cap 14): In the morning rush, residents depart for work generating net flow of -7,973 trips (8,787 departures vs. 814 returns). "
        "  In the evening rush, commuters return home, generating net flow of +2,808 trips. Total Diurnal Tidal Swing: 10,781 trips.\n"
        "• Quadrant IV: Employment & Commercial Hub Docks (Morning Surplus -> Evening Deficit):\n"
        "  Salmisaarenranta (Station 059, Cap 28): In the morning rush, inbound workers dock bikes resulting in net flow of +7,343 trips (7,543 returns vs. 200 departures). "
        "  In the evening rush, workers unlock bikes to leave offices, generating net flow of -5,244 trips. Total Diurnal Tidal Swing: 12,587 trips (#1 Tidal Hub).\n"
        "  Itämerentori (Station 030, Cap 40): Morning surplus +6,838 trips -> Evening deficit -5,022 trips (Total Diurnal Tidal Swing: 11,860 trips, #2 Tidal Hub).\n"
        "• Quadrant III: Persistent Structural Sinks (All-Day Deficit):\n"
        "  Pasila railway station (Station 113, Cap 40): Remains in heavy deficit during both morning (-2,618) and evening (-2,607) peaks, acting as an all-day transit dispersal node.\n"
        "• Pre-Staging Operational Hypothesis: Because departures surge sharply between 16:00 and 18:00, planners could explore an operational hypothesis "
        "of pre-staging bicycle redistribution prior to the afternoon peak (e.g., before 15:30); verifying this strategy requires real-time dock inventory data."
    )
    rc_tide = page.insert_textbox(tide_rect + (8, 6, -8, -6), tide_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_tide >= 0, f"Page 4 tide text overflow: {rc_tide}"
    y += 150

    # Embedded Figure 6 (Morning vs Evening Peak Comparison)
    fig6_path = "reports/figures/fig6_morning_vs_evening_peak_station_comparison.png"
    if os.path.exists(fig6_path):
        img_h = 185
        img_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + img_h)
        page.insert_image(img_rect, filename=fig6_path, keep_proportion=True)
        y += img_h + 4

        cap_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 24)
        cap_text = (
            "Figure 6: Station-level net flow during morning rush (07:00-09:00, x-axis) vs. evening rush (16:00-18:00, y-axis). "
            "Highlights diurnal tidal reversal: Residential feeders (Quadrant II), Commercial/employment hubs (Quadrant IV), and Structural sinks (Quadrant III)."
        )
        rc_cap = page.insert_textbox(cap_rect, cap_text, fontname="hebi", fontsize=6.8, color=C_SLATE, align=pymupdf.TEXT_ALIGN_CENTER)
        assert rc_cap >= 0, f"Page 4 caption overflow: {rc_cap}"


def build_page_5(doc):
    """Build Page 5: Canvas Plan vs. Actual Work Reflection, Methodological Limitations, Lessons & Future Work."""
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    draw_header_footer(page, 5)

    y = 38

    # 1. Section 12: Reflection: Canvas Plan vs. Actual Completed Work
    y = draw_section_bar(page, y, "12. Reflection: Canvas Plan vs. Actual Completed Work", "Methodological Evolution & Refinement")

    refl_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 150)
    draw_card(page, refl_rect, fill=C_BLUE_BG, border=C_BLUE)
    refl_text = (
        "• Evolution of Weather Features (Decoupling Lookahead Bias): The Canvas Workshop 3 proposal initially contemplated using weather and local weather "
        "forecasts as direct regression features. However, during pipeline development, methodological auditing revealed that using ground-truth retrospective "
        "weather in an out-of-time forecasting benchmark creates fatal lookahead bias (future weather is unknown at decision time), while commercial numerical "
        "weather forecasts weeks/months in advance have zero skill in subarctic Finland. We correctly decoupled weather into retrospective descriptive EDA "
        "(identifying strong seasonal temperature correlation r ~ 0.74 alongside daylight/holiday confounders) and restricted predictive ML to causal lag-1 signals.\n\n"
        "• Temporal Granularity & Operational Hierarchy: The Canvas proposed multi-scale regressions from hour to month. Modeling full-network hourly "
        "demands across 457 stations yields sparse, zero-inflated counts that obscure seasonal macro trends and require dock sensor telemetry. We structured "
        "a clean two-tier operational framework: (1) Monthly macro demand forecasting (Baseline vs. Ridge vs. Trees) for seasonal fleet sizing, and "
        "(2) Operating-day normalized diurnal curves (0-23h) and peak-hour net flow reversal for day-to-day dispatch planning.\n\n"
        "• Metric & Task Differentiation: The Canvas envisioned general allocation; our empirical evaluation proved that volume sizing (MAE/WAPE) and "
        "rebalancing triage (Spearman rank correlation) require different tools: Historical Baseline for sizing vs. Ridge for early-season deficit screening."
    )
    rc_refl = page.insert_textbox(refl_rect + (8, 6, -8, -6), refl_text, fontname="helv", fontsize=6.8, color=C_NAVY)
    assert rc_refl >= 0, f"Page 5 reflection overflow: {rc_refl}"
    y += 158

    # 2. Section 13: Limitations & Methodological Constraints
    y = draw_section_bar(page, y, "13. Methodological Constraints & Physical Reality Boundaries", "Analytical Disclaimers")

    col_w = (USABLE_W - 10) / 2

    disc_l_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + col_w, y + 115)
    draw_card(page, disc_l_rect, fill=C_LIGHT_BG, border=C_BORDER)
    disc_l_text = (
        "1. Historical Weather != Weather Forecasts:\n"
        "   FMI weather records represent retrospective ground-truth observations, strictly excluded from predictive models to eliminate data leakage.\n"
        "2. Descriptive Correlation != Causation:\n"
        "   Daily trip correlations (r ~ +0.74 with temp) reflect seasonal co-movement. Astronomical daylight (19h June vs. 9h Oct), school calendars, "
        "   and summer holidays are heavily collinear with temperature.\n"
        "3. Forecast Error Unit (MAE) != Physical Bicycles:\n"
        "   MAE is measured in trips per station-month (e.g. 147.60 trips/mo). It does not represent physical bicycle shortages; one bicycle serves multiple trips daily."
    )
    rc_dl = page.insert_textbox(disc_l_rect + (6, 5, -6, -5), disc_l_text, fontname="helv", fontsize=6.7, color=C_DARK)
    assert rc_dl >= 0, f"Page 5 disc left overflow: {rc_dl}"

    disc_r_rect = pymupdf.Rect(MARGIN_L + col_w + 10, y, MARGIN_R, y + 115)
    draw_card(page, disc_r_rect, fill=C_LIGHT_BG, border=C_BORDER)
    disc_r_text = (
        "4. Monthly Net Flow != Real-Time Van Dispatch Workload:\n"
        "   Cumulative monthly net_flow = returns - departures reflects 30-day passenger drift, not immediate truck dispatch needs. "
        "   Diurnal tidal reversals partially offset daytime imbalances; truck dispatch requires 15-minute dock occupancy sensor telemetry.\n"
        "5. Single Out-of-Time Test Cycle (2025 Season):\n"
        "   Evaluating on 2025 provides an exploratory out-of-time backtest, not multi-year statistical significance.\n"
        "6. Partial Q4 Operating Window:\n"
        "   The HSL season closes October 31; Q4 contains only October (1 operating month)."
    )
    rc_dr = page.insert_textbox(disc_r_rect + (6, 5, -6, -5), disc_r_text, fontname="helv", fontsize=6.7, color=C_DARK)
    assert rc_dr >= 0, f"Page 5 disc right overflow: {rc_dr}"
    y += 123

    # 3. Section 14: Data Privacy, Ethical Governance & Licensing
    y = draw_section_bar(page, y, "14. Data Privacy, Ethical Governance & Licensing", "Compliance Framework")

    priv_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 54)
    draw_card(page, priv_rect, fill=C_WHITE, border=C_BORDER)
    priv_text = (
        "• Data Privacy Protection: In strict compliance with European GDPR and ethical research standards, all analytical tables and published "
        "web deliverables aggregate trips at station-month or hourly municipal scales. Zero individual rider identifiers, trajectory coordinates, or personal "
        "smart-card tokens exist in raw or derived data.\n"
        "• Attribution & Open Data Licensing: Ingested journey records and ArcGIS station metadata are published by City Bike Finland and HSL under "
        "Creative Commons Attribution 4.0 International (CC BY 4.0). Weather observations are provided by the Finnish Meteorological Institute (FMI) under CC BY 4.0."
    )
    rc_priv = page.insert_textbox(priv_rect + (8, 5, -8, -5), priv_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_priv >= 0, f"Page 5 privacy overflow: {rc_priv}"
    y += 62

    # 4. Section 15: Learning Takeaways & Future Engineering Roadmap
    y = draw_section_bar(page, y, "15. Key Learning Takeaways & Future Improvements", "Engineering Synthesis")

    col_w2 = (USABLE_W - 10) / 2

    lrn_rect = pymupdf.Rect(MARGIN_L, y, MARGIN_L + col_w2, y + 100)
    draw_card(page, lrn_rect, fill=C_LIGHT_BG, border=C_BORDER)
    lrn_text = (
        "Key Project Learning Takeaways:\n"
        "1. Domain Physics Beat Algorithmic Complexity: In subarctic shared mobility, seasonal calendar alignment (same-month baseline) outperforms "
        "   complex feature regressions that suffer from transitional lag across Nordic seasons.\n"
        "2. Strict Leakage Auditing is Paramount: Decoupling weather lookahead prevented deceptive model performance and yielded realistic operational benchmarks.\n"
        "3. Multi-Metric Evaluation: Single-metric optimization (e.g. global MAE) hides severe localized failure modes, such as Ridge's 124% WAPE on quiet stations."
    )
    rc_lrn = page.insert_textbox(lrn_rect + (6, 5, -6, -5), lrn_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_lrn >= 0, f"Page 5 learning overflow: {rc_lrn}"

    fut_rect = pymupdf.Rect(MARGIN_L + col_w2 + 10, y, MARGIN_R, y + 100)
    draw_card(page, fut_rect, fill=C_LIGHT_BG, border=C_BORDER)
    fut_text = (
        "Future Operational Improvements:\n"
        "1. 15-Minute Sensor Telemetry: Ingest real-time dock occupancy GBFS feeds to transition from macro seasonal triage to dynamic rebalancing truck routing.\n"
        "2. Same-Day Weather Adjustment Heuristics: Develop day-of-forecast multiplier adjustments based on short-range 24h FMI precipitation forecasts.\n"
        "3. User Crowdsourced Rebalancing Incentives: Model dynamic reverse-pricing or bonus credits for users riding from surplus docks to deficit sinks."
    )
    rc_fut = page.insert_textbox(fut_rect + (6, 5, -6, -5), fut_text, fontname="helv", fontsize=6.8, color=C_DARK)
    assert rc_fut >= 0, f"Page 5 future overflow: {rc_fut}"
    y += 108

    # 5. Section 16: Interactive Web Platform Deliverable Banner
    web_banner = pymupdf.Rect(MARGIN_L, y, MARGIN_R, y + 64)
    draw_card(page, web_banner, fill=C_BLUE_BG, border=C_BLUE, border_width=1.0)
    web_text = (
        "Interactive Planning Web Application (GitHub Pages Platform):\n"
        "Delivered as a zero-dependency static web platform hosted under docs/ (published to GitHub Pages at https://luosuo890.github.io/HSL_City_Bike_Project/). "
        "Features 4 interactive modules: (1) Leaflet Station Map with net flow & capacity layers; (2) Intraday Commute & Tidal Peaks; "
        "(3) FMI Daily Weather Correlation Explorer; (4) Model Comparison & 2025 Test Predictions Scatter. 22 automated test suites passing."
    )
    rc_web = page.insert_textbox(web_banner + (8, 5, -8, -5), web_text, fontname="hebo", fontsize=6.9, color=C_NAVY)
    assert rc_web >= 0, f"Page 5 web banner overflow: {rc_web}"


def generate_report():
    """Generate the full 5-page report PDF."""
    os.makedirs("reports", exist_ok=True)
    out_pdf = os.path.join("reports", "HSL_City_Bike_Technical_Report.pdf")

    doc = pymupdf.open()
    build_page_1(doc)
    build_page_2(doc)
    build_page_3(doc)
    build_page_4(doc)
    build_page_5(doc)

    assert len(doc) == 5, f"Expected exactly 5 pages, got {len(doc)}"
    doc.save(out_pdf, garbage=4, deflate=True, clean=True)
    pdf_size_mb = os.path.getsize(out_pdf) / (1024 * 1024)
    print(f"Technical Report PDF successfully generated: {out_pdf}")
    print(f"Total Page Count: {len(doc)} pages (Budget: maximum 5 pages)")
    print(f"File Size: {pdf_size_mb:.2f} MB")
    return out_pdf, len(doc)


if __name__ == "__main__":
    generate_report()
