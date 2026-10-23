# HSL City Bike Project: 3-Minute Spotlight Presentation Script

> **Target Audience:** City-bike operators and HSL transport planners
> **Occasion:** University of Helsinki — Introduction to Data Science (Course Mini-Project Spotlight Session)
> **Presentation Deck:** [`HSL_Bike_Heatmap_Presentation_Spotlight.pptx`](file:///c:/Users/luosuo/Desktop/HSL_City_Bike_Project/HSL_Bike_Heatmap_Presentation_Spotlight.pptx)
> **Strict Duration:** 3 minutes 00 seconds (180 seconds)
> **Total Spoken Word Count:** 353 words (Target constraint: 330–360 words)
> **Average Delivery Pace:** 117.7 words / minute (Target: 110–120 wpm)

---

## Executive Timing & Pacing Summary

| Slide # | Slide Category & Headline | On-Screen Visual Asset | Time Window | Duration | Word Count | Delivery Pace |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **01** | **Operational Challenge**<br>Anticipating Urban Bike Depletion & Dock Congestion | Dark Slate Hero Layout + 3 Scope Cards | 0:00–0:20 | 20 sec | 44 words | 132 wpm |
| **02** | **Seasonal Concentration**<br>Summer Peaks at Nearly 500k Monthly Trips | `fig2_station_month_demand_heatmap.png` | 0:20–0:55 | 35 sec | 73 words | 125 wpm |
| **03** | **Intraday Commute Dynamics**<br>Weekday Evening Demand Surges +78%, Reversing Net Flows | `fig6_morning_vs_evening_peak_station_comparison.png` | 0:55–1:30 | 35 sec | 76 words | 130 wpm |
| **04** | **Rebalancing Triage**<br>Directional Net Flow Pinpoints Systemic Rebalancing Bottlenecks | `fig3_station_net_flow_map.png` | 1:30–2:05 | 35 sec | 59 words | 101 wpm |
| **05** | **Demand Forecasting**<br>Previous-Year Same-Month Baseline Minimizes Demand Forecast Error | `fig7_forecast_evaluation_actual_vs_baseline_2025.png` | 2:05–2:35 | 30 sec | 54 words | 108 wpm |
| **06** | **Operational Conclusions**<br>Actionable Guidelines & Methodological Guardrails | 3 Action Pillar Cards + Guardrails Banner | 2:35–3:00 | 25 sec | 47 words | 113 wpm |
| **TOTAL** | **Full Spotlight Presentation** | **6 Slides Total** | **0:00–3:00** | **180 sec** | **353 words** | **117.7 wpm** |

---

## Verbatim Slide-by-Slide Spoken Script & Delivery Guide

### Slide 01 | The Operational Challenge
- **Category:** `01 | OPERATIONAL CHALLENGE`
- **Headline:** *Anticipating Urban Bike Depletion & Dock Congestion*
- **Sub-headline:** *HSL City-Bike Rebalancing Insights Across 457 Stations & 4.98 Million Trips (2024–2025)*
- **Visual On Screen:** Dark slate-teal canvas (`#12313A`) with a bold central inquiry card and three structured problem domains: *Macro Seasonality*, *Commuter Tidal Swings*, and *Operational Triage*.
- **Time Window:** `0:00 – 0:20` (20 seconds)
- **Spoken Word Count:** 44 words (~132 wpm)

#### Verbatim Oral Script:
> "Good morning. City-bike operators in Helsinki face a daily rebalancing headache: docks run empty during morning commutes and overflow by evening. Across nearly five million cleaned trips in 2024 and 2025, our goal is helping HSL planners triage critical stations before service disruptions occur."

#### Presenter Cues & Gestures:
- *[0:00]* Stand upright, make direct eye contact with the audience, and deliver the opening greeting with confident, warm energy.
- *[0:05]* Stress the operational contrast: *"docks run empty"* (slight upward hand gesture) vs. *"overflow by evening"* (downward sweeping hand).
- *[0:15]* Point to the center card showing 4.98M trips, framing the talk as practical triage for operators rather than academic theory.

---

### Slide 02 | Seasonal Demand Concentration
- **Category:** `02 | SEASONAL CONCENTRATION`
- **Headline:** *Summer Peaks at Nearly 500k Monthly Trips, Anchored by Major Rail Hubs*
- **Sub-headline:** *Station-Month Departures Across Two Full Seasons (April–October, 2024 & 2025)*
- **Visual On Screen:** Top-30 station departure heatmap across all 14 operating months ([`fig2_station_month_demand_heatmap.png`](file:///c:/Users/luosuo/Desktop/HSL_City_Bike_Project/reports/figures/fig2_station_month_demand_heatmap.png)) alongside two key callout cards: *Sharp Unimodal Summer Envelope* and *Transit Hub Sinks & Weather Context*.
- **Time Window:** `0:20 – 0:55` (35 seconds)
- **Spoken Word Count:** 73 words (~125 wpm)

#### Verbatim Oral Script:
> "Looking at the thirty busiest stations across fourteen operating months, ridership follows a steep summer peak in July and August, contracting by more than half in shoulder months. Helsinki accounts for eighty-nine percent of volume, anchored by major rail hubs like Pasila and Central Railway Station. Daily trips correlate with warm summer days, but this reflects holiday schedules and long Nordic daylight rather than direct causation. This volume profile informs seasonal fleet sizing."

#### Presenter Cues & Gestures:
- *[0:22]* Point left toward the heatmap visual, tracing your hand across the bright yellow bands in July and August.
- *[0:32]* Point to the top rows of the heatmap, emphasizing the dense departure blocks at Pasila and Rautatieasema.
- *[0:42]* Modulate tone to sound measured when referencing weather: clarify that positive temperature correlation (+0.74) is descriptive co-movement with 19-hour Nordic daylight and holidays, not a causal forecast.
- *[0:50]* Conclude this slide by emphasizing the takeaway: seasonal macro contracts and depot allocations.

---

### Slide 03 | Intraday Commute Dynamics
- **Category:** `03 | INTRADAY COMMUTE DYNAMICS`
- **Headline:** *Weekday Evening Demand Surges +78%, Reversing Station Net Flows*
- **Sub-headline:** *Standardized Peak Windows (07:00–09:00 vs. 16:00–18:00) Reveal Polarized Commuter Swings*
- **Visual On Screen:** Paired bar chart contrasting morning vs. evening departures across top commuter hubs ([`fig6_morning_vs_evening_peak_station_comparison.png`](file:///c:/Users/luosuo/Desktop/HSL_City_Bike_Project/reports/figures/fig6_morning_vs_evening_peak_station_comparison.png)) paired with callouts for *Evening Rush Surge (+78% to +96%)* and *Diurnal Commuter Tidal Reversals*.
- **Time Window:** `0:55 – 1:30` (35 seconds)
- **Spoken Word Count:** 76 words (~130 wpm)

#### Verbatim Oral Script:
> "Intraday patterns show that weekday evening peaks generate seventy-eight to ninety-six percent more trips than morning peaks. Simultaneously, stations undergo sharp tidal reversals. Residential docks like Sompasaari experience severe morning deficits as commuters leave, but accumulate heavy surpluses by evening. Conversely, workplace centers like Salmisaarenranta fill up in the morning and empty out after work. Meanwhile, Pasila rail station operates in continuous deficit throughout the entire day. These commuter swings dictate where rebalancing vans should stage."

#### Presenter Cues & Gestures:
- *[0:58]* Point to the dramatic contrast between the morning (coral) and evening (blue) bars on the chart.
- *[1:08]* Use two hand motions to demonstrate tidal opposition: left hand forward for morning outflow, right hand return for evening inflow.
- *[1:18]* Highlight Sompasaari (residential deficit turning into surplus) versus Salmisaarenranta (office surplus turning into deficit).
- *[1:24]* Emphasize Pasila as an exception that remains in structural deficit all day long. Pause briefly before moving to the geographic map.

---

### Slide 04 | Spatial Rebalancing Triage
- **Category:** `04 | REBALANCING TRIAGE`
- **Headline:** *Directional Net Flow Pinpoints Systemic Rebalancing Bottlenecks*
- **Sub-headline:** *Cumulative Net Flow (Returns - Departures) Across 454 Coordinate Stations (2024–2025)*
- **Visual On Screen:** Diverging zero-centered geospatial net flow map ([`fig3_station_net_flow_map.png`](file:///c:/Users/luosuo/Desktop/HSL_City_Bike_Project/reports/figures/fig3_station_net_flow_map.png)) displaying red deficit sinks and blue surplus sources across Helsinki and Espoo.
- **Time Window:** `1:30 – 2:05` (35 seconds)
- **Spoken Word Count:** 59 words (~101 wpm)

#### Verbatim Oral Script:
> "Mapping cumulative net flow across the network highlights structural rebalancing sinks in red and surplus sources in blue. Pasila railway station is the primary deficit bottleneck, accumulating an eleven-thousand trip deficit over two seasons. While this macro drift identifies priority candidates for rebalancing attention, it reflects passenger flow rather than exact physical bike inventory or rigid truck dispatch orders."

#### Presenter Cues & Gestures:
- *[1:32]* Adopt a slower, deliberate cadence (101 wpm) as operators absorb the map layout.
- *[1:36]* Point to the pronounced red node at Pasila rail junction in central northern Helsinki.
- *[1:46]* Direct attention to coastal and recreational blue nodes (Unioninkatu, Kanavaranta, Kalasatama).
- *[1:55]* Emphasize the methodological boundary: net flow is cumulative trip drift, not real-time dock stock or deterministic van routing.

---

### Slide 05 | Demand Forecasting Benchmarks
- **Category:** `05 | DEMAND FORECASTING`
- **Headline:** *Previous-Year Same-Month Baseline Minimizes Demand Forecast Error*
- **Sub-headline:** *2025 Out-of-Time Backtest (N=2,718 Matched Station-Months; Unit: Trips / Station-Month)*
- **Visual On Screen:** Dual-panel model evaluation chart ([`fig7_forecast_evaluation_actual_vs_baseline_2025.png`](file:///c:/Users/luosuo/Desktop/HSL_City_Bike_Project/reports/figures/fig7_forecast_evaluation_actual_vs_baseline_2025.png)): actual vs. baseline scatter with 45-degree reference line, and model performance metrics (MAE / WAPE).
- **Time Window:** `2:05 – 2:35` (30 seconds)
- **Spoken Word Count:** 54 words (~108 wpm)

#### Verbatim Oral Script:
> "When forecasting 2025 monthly demand, using the previous year's same month achieved the lowest volume error at 17.6% WAPE. The baseline naturally absorbs Nordic seasonal shifts without transitional delay. Meanwhile, Ridge regression helps screen high-deficit stations. This single-season test provides an empirical benchmark for fleet sizing, measured in monthly trip events, not missing bicycles."

#### Presenter Cues & Gestures:
- *[2:07]* Gesture to the scatter plot: highlight how tightly the data points cluster along the diagonal dashed line.
- *[2:15]* Explain simply why the baseline excels: it avoids lag penalties when spring ramps up into summer and summer cools down into autumn.
- *[2:23]* Point out Ridge regression's value in ranking deficit stations (Spearman ρ = 0.76).
- *[2:29]* Clarify clearly that MAE measures completed trip departures per station-month, not physical bicycles.

---

### Slide 06 | Operational Guidelines & Boundaries
- **Category:** `06 | OPERATIONAL CONCLUSIONS`
- **Headline:** *Actionable Guidelines & Methodological Guardrails for Operators*
- **Sub-headline:** *Empirical Recommendations for Seasonal Fleet Sizing, Triage & Future Telemetry*
- **Visual On Screen:** Three clean operational pillar cards:
  1. *Seasonal Fleet Sizing (Baseline for Contracts)*
  2. *Rebalancing Route Triage (Pre-Stage Prior to 16:00 Rush)*
  3. *Connect Live Telemetry (Integrate Real-Time Dock Sensors)*
  Followed by a dark guardrails card explicitly stating methodological boundaries.
- **Time Window:** `2:35 – 3:00` (25 seconds)
- **Spoken Word Count:** 47 words (~113 wpm)

#### Verbatim Oral Script:
> "To conclude, operators should use the historical baseline for seasonal fleet sizing and net-flow rankings to prioritize rebalancing routes, such as pre-staging before the 16:00 evening surge. Connecting real-time dock telemetry is the essential next step before dispatching redistribution vans. Thank you, and we welcome your questions."

#### Presenter Cues & Gestures:
- *[2:36]* Sweep your hand across the three top action cards in sequence: Sizing → Triage → Telemetry.
- *[2:44]* Emphasize the practical recommendation: pre-staging bikes ahead of the afternoon rush (before 16:00) to absorb the +78% surge.
- *[2:52]* Glaze over the bottom guardrails card to reassure planners that the team understands the boundaries between retrospective trip data and live operations.
- *[2:58]* Conclude with a warm smile and thank the audience: *"Thank you, and we welcome your questions."*

---

## Methodological Boundaries & Guardrails Summary

To ensure academic rigor and prevent operational misinterpretation, both the slides and oral script adhere strictly to the following principles:

1. **Retrospective Weather vs. Weather Forecasts:**
   Weather data consists of retrospective FMI observations from Kumpula and Kaisaniemi stations. Weather variables were **strictly excluded** from 2025 demand prediction models. Weather correlations (e.g., $r = +0.74$ with temperature) reflect macro seasonal co-movement with Nordic daylight and vacation calendars, not direct causality.
2. **Trip Demand vs. Bicycle Stock:**
   Prediction errors ($\text{MAE} = 141.9$ trips/month) measure completed trip counts per station-month, **never missing physical bicycles**. A single bicycle circulates across multiple trips every day.
3. **Net Flow Drift vs. Van Dispatch Workloads:**
   Station net flow ($\text{Returns} - \text{Departures}$) measures 30-day directional passenger drift. It does not reflect real-time dock emptiness or physical van capacity requirements, especially given that diurnal morning/evening reversals partially self-rebalance docks.
4. **Out-of-Time Backtest vs. Statistical Proof:**
   The 2025 backtest across $N=2,718$ station-months represents an empirical out-of-time benchmark across a single test season. It does not establish statistical significance or prove long-term model superiority.
5. **Screening Lists vs. Deterministic Routing:**
   High-deficit station rankings are triage screening tools to help operators identify candidate areas for investigation, not automated dispatch orders. Live 15-minute dock occupancy feeds are required prior to physical vehicle routing.


Good morning. City-bike operators in Helsinki face a daily rebalancing headache: docks run empty during morning commutes and overflow by evening. Across nearly five million cleaned trips in 2024 and 2025, our goal is helping HSL planners triage critical stations before service disruptions occur."

"Looking at the thirty busiest stations across fourteen operating months, ridership follows a steep summer peak in July and August, contracting by more than half in shoulder months. Helsinki accounts for eighty-nine percent of volume, anchored by major rail hubs like Pasila and Central Railway Station. Daily trips correlate with warm summer days, but this reflects holiday schedules and long Nordic daylight rather than direct causation. This volume profile informs seasonal fleet sizing."

"Intraday patterns show that weekday evening peaks generate seventy-eight to ninety-six percent more trips than morning peaks. Simultaneously, stations undergo sharp tidal reversals. Residential docks like Sompasaari experience severe morning deficits as commuters leave, but accumulate heavy surpluses by evening. Conversely, workplace centers like Salmisaarenranta fill up in the morning and empty out after work. Meanwhile, Pasila rail station operates in continuous deficit throughout the entire day. These commuter swings dictate where rebalancing vans should stage."

"Mapping cumulative net flow across the network highlights structural rebalancing sinks in red and surplus sources in blue. Pasila railway station is the primary deficit bottleneck, accumulating an eleven-thousand trip deficit over two seasons. While this macro drift identifies priority candidates for rebalancing attention, it reflects passenger flow rather than exact physical bike inventory or rigid truck dispatch orders."

"When forecasting 2025 monthly demand, using the previous year's same month achieved the lowest volume error at 17.6% WAPE. The baseline naturally absorbs Nordic seasonal shifts without transitional delay. Meanwhile, Ridge regression helps screen high-deficit stations. This single-season test provides an empirical benchmark for fleet sizing, measured in monthly trip events, not missing bicycles."

"To conclude, operators should use the historical baseline for seasonal fleet sizing and net-flow rankings to prioritize rebalancing routes, such as pre-staging before the 16:00 evening surge. Connecting real-time dock telemetry is the essential next step before dispatching redistribution vans. Thank you, and we welcome your questions."
