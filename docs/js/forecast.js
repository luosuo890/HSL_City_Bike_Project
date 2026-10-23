/**
 * HSL City Bike Project - Demand Forecasting & Model Comparison Module (Phase 5)
 * Visualizes out-of-time demand prediction benchmarks across 2,718 station-month test observations (May–Oct 2025).
 * Compares Same-Month Baseline (2024), Ridge Regression (Lag-1), and Decision Tree (Lag-1).
 *
 * Methodological Principles & Operational Boundaries:
 * 1. Multi-Model Test Cohort (May–Oct 2025, N=2,718): Fair comparison on identical station-months.
 *    (Full-Season Baseline N=3,170 Apr–Oct is displayed strictly as a separate reference).
 * 2. Units: MAE/RMSE measured in completed passenger journeys (trips), NOT physical bicycles.
 * 3. Flow Terminology: "Net outflow / Net inflow" describes directional travel balance, NOT dock stock or truck dispatch commands.
 * 4. Weather Input: Strictly excluded from model feature space (no 2025 weather leakage).
 * 5. Descriptive Benchmark: Single out-of-time test season; no statistical significance claims.
 */

const ForecastModule = (function () {
  "use strict";

  // Data cache
  let summaryData = null;      // Loaded from ./data/data_model_summary.json
  let predictionData = null;   // Loaded from ./data/data_model_predictions_2025.json
  let scenarioData = null;     // Loaded from ./data/data_weather_scenario.json

  // Scenario state (City-Day aggregate what-if analysis)
  const scenarioState = {
    city: "Helsinki",
    month: 6,           // June (integer 4 to 10)
    daytype: "weekday", // "weekday" or "weekend"
    tday: 18.0,         // Mean daily temperature (°C)
    precip: 0.0         // Daily precipitation (mm)
  };

  // Chart instances
  let scatterChartInstance = null;
  let monthlyWapeChartInstance = null;
  let rankingOverlapChartInstance = null;

  // Active filter state
  const filters = {
    month: "all",        // "all", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"
    model: "base",       // "base", "ridge", "dt"
    metric: "dep",       // "dep" (Departures), "ret" (Returns), "net" (Net Flow)
    city: "all",         // "all", "Helsinki", "Espoo"
    segment: "all",      // "all", "q1_low" (Low usage <= 198 trips)
    search: ""           // search query by station name or ID
  };

  const MODEL_META = {
    base: {
      name: "Same-Month Baseline (2024)",
      short: "Baseline",
      color: "#059669",
      borderColor: "#047857",
      bgRgba: "rgba(5, 150, 105, 0.65)"
    },
    ridge: {
      name: "Ridge Regression (Lag-1)",
      short: "Ridge",
      color: "#ea580c",
      borderColor: "#c2410c",
      bgRgba: "rgba(234, 88, 12, 0.65)"
    },
    dt: {
      name: "Decision Tree (max_depth=6)",
      short: "Decision Tree",
      color: "#7c3aed",
      borderColor: "#6d28d9",
      bgRgba: "rgba(124, 58, 237, 0.65)"
    }
  };

  /**
   * Initializes the forecast module.
   */
  function init() {
    bindEvents();
    bindScenarioEvents();
    loadForecastData();
  }

  /**
   * Binds event listeners for model filter controls.
   */
  function bindEvents() {
    const monthSelect = document.getElementById("filter-forecast-month");
    const modelSelect = document.getElementById("filter-forecast-model");
    const metricSelect = document.getElementById("filter-forecast-metric");
    const citySelect = document.getElementById("filter-forecast-city");
    const segmentSelect = document.getElementById("filter-forecast-segment");
    const searchInput = document.getElementById("filter-forecast-search");

    if (monthSelect) {
      monthSelect.addEventListener("change", (e) => {
        filters.month = e.target.value;
        updateDynamicViews();
      });
    }

    if (modelSelect) {
      modelSelect.addEventListener("change", (e) => {
        filters.model = e.target.value;
        updateDynamicViews();
      });
    }

    if (metricSelect) {
      metricSelect.addEventListener("change", (e) => {
        filters.metric = e.target.value;
        updateDynamicViews();
      });
    }

    if (citySelect) {
      citySelect.addEventListener("change", (e) => {
        filters.city = e.target.value;
        updateDynamicViews();
      });
    }

    if (segmentSelect) {
      segmentSelect.addEventListener("change", (e) => {
        filters.segment = e.target.value;
        updateDynamicViews();
      });
    }

    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        filters.search = e.target.value.trim().toLowerCase();
        updateDynamicViews();
      });
    }
  }

  /**
   * Fetches required JSON datasets via strictly relative paths.
   */
  function loadForecastData() {
    const loadingElem = document.getElementById("forecast-loading-overlay");
    if (loadingElem) loadingElem.style.display = "flex";

    Promise.all([
      fetch("./data/data_model_summary.json").then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} loading summary data`);
        return r.json();
      }),
      fetch("./data/data_model_predictions_2025.json").then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} loading predictions data`);
        return r.json();
      }),
      fetch("./data/data_weather_scenario.json").then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} loading weather scenario data`);
        return r.json();
      })
    ])
      .then(([summary, preds, scenario]) => {
        summaryData = summary;
        predictionData = preds;
        scenarioData = scenario;

        if (loadingElem) loadingElem.style.display = "none";

        renderScorecardTable();
        renderMonthlyWapeChart();
        renderRankingOverlapChart();
        updateDynamicViews();
        initWeatherScenario();
      })
      .catch((err) => {
        if (loadingElem) loadingElem.style.display = "none";
        console.error("ForecastModule load error:", err);
        const errBanner = document.getElementById("forecast-error-banner");
        if (errBanner) {
          errBanner.textContent = `Failed to load forecasting datasets: ${err.message}.`;
          errBanner.style.display = "block";
        }
      });
  }

  /**
   * Filters raw 2025 prediction records based on active UI criteria.
   */
  function getFilteredRecords() {
    if (!predictionData || !predictionData.records) return [];

    return predictionData.records.filter((rec) => {
      // Month filter
      if (filters.month !== "all" && rec.ym !== filters.month) return false;
      // City filter
      if (filters.city !== "all" && rec.city !== filters.city) return false;
      // Low usage segment filter (threshold <= 198 trips/month)
      if (filters.segment === "q1_low" && rec.act_dep > 198.0) return false;
      // Search filter
      if (filters.search) {
        const matchesName = rec.name.toLowerCase().includes(filters.search);
        const matchesId = String(rec.sid).includes(filters.search);
        if (!matchesName && !matchesId) return false;
      }
      return true;
    });
  }

  /**
   * Computes error metrics (MAE, WAPE, RMSE) dynamically on any filtered slice.
   */
  function calculateSliceMetrics(records, modelKey, metricType) {
    const n = records.length;
    if (n === 0) return { n: 0, mae: 0, wape: 0, rmse: 0, sumActual: 0 };

    let sumAbsErr = 0;
    let sumSqErr = 0;
    let sumActual = 0;

    const actKey = `act_${metricType}`;
    const predKey = `${modelKey}_${metricType}`;

    records.forEach((r) => {
      const act = r[actKey];
      const pred = r[predKey];
      const diff = pred - act;
      sumAbsErr += Math.abs(diff);
      sumSqErr += diff * diff;
      sumActual += Math.abs(act);
    });

    const mae = sumAbsErr / n;
    const rmse = Math.sqrt(sumSqErr / n);
    const wape = sumActual > 0 ? (sumAbsErr / sumActual) * 100 : 0;

    return {
      n,
      mae,
      wape,
      rmse,
      sumActual
    };
  }

  /**
   * Updates all dynamic views (scatter plot, slice KPI callout, triage table).
   */
  function updateDynamicViews() {
    const records = getFilteredRecords();
    const sliceStats = calculateSliceMetrics(records, filters.model, filters.metric);

    updateSliceMetricsBadge(sliceStats);
    renderScatterChart(records);
    renderTriageTable(records);
  }

  /**
   * Updates the dynamic slice metric callout badge above the scatter plot.
   */
  function updateSliceMetricsBadge(stats) {
    const badgeCount = document.getElementById("slice-sample-count");
    const badgeMae = document.getElementById("slice-mae-val");
    const badgeWape = document.getElementById("slice-wape-val");
    const badgeRmse = document.getElementById("slice-rmse-val");
    const badgeModel = document.getElementById("slice-model-label");

    const mMeta = MODEL_META[filters.model];
    const metricLabel = filters.metric === "dep" ? "Departures" : filters.metric === "ret" ? "Returns" : "Net Flow";

    if (badgeModel) {
      badgeModel.textContent = `${mMeta.name} — ${metricLabel}`;
    }
    if (badgeCount) {
      badgeCount.textContent = `N = ${stats.n.toLocaleString()} station-months`;
    }
    if (badgeMae) {
      badgeMae.textContent = `${stats.mae.toFixed(1)} trips`;
    }
    if (badgeWape) {
      badgeWape.textContent = `${stats.wape.toFixed(2)}%`;
    }
    if (badgeRmse) {
      badgeRmse.textContent = `${stats.rmse.toFixed(1)} trips`;
    }
  }

  /**
   * Renders the Actual vs. Predicted interactive scatter plot with y = x reference diagonal.
   */
  function renderScatterChart(records) {
    const canvas = document.getElementById("chart-forecast-scatter");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (scatterChartInstance) {
      scatterChartInstance.destroy();
      scatterChartInstance = null;
    }

    const mMeta = MODEL_META[filters.model];
    const actKey = `act_${filters.metric}`;
    const predKey = `${filters.model}_${filters.metric}`;

    // Compute range for 45-degree diagonal reference line
    let minVal = Infinity;
    let maxVal = -Infinity;

    const points = records.map((r) => {
      const x = r[actKey];
      const y = r[predKey];
      if (x < minVal) minVal = x;
      if (x > maxVal) maxVal = x;
      if (y < minVal) minVal = y;
      if (y > maxVal) maxVal = y;

      return {
        x: x,
        y: Number(y.toFixed(1)),
        sid: r.sid,
        name: r.name,
        city: r.city,
        ym: r.ym
      };
    });

    if (minVal === Infinity) {
      minVal = 0;
      maxVal = 100;
    }

    // Reference diagonal y = x
    const diagLine = [
      { x: minVal, y: minVal },
      { x: maxVal, y: maxVal }
    ];

    const metricTitle = filters.metric === "dep" ? "Departures" : filters.metric === "ret" ? "Returns" : "Net Flow (Returns - Departures)";

    scatterChartInstance = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: `${mMeta.name} Predictions`,
            data: points,
            backgroundColor: mMeta.bgRgba,
            borderColor: mMeta.borderColor,
            borderWidth: 1,
            pointRadius: 4,
            pointHoverRadius: 6.5
          },
          {
            type: "line",
            label: "Ideal Prediction Reference (y = x)",
            data: diagLine,
            borderColor: "#94a3b8",
            borderWidth: 1.5,
            borderDash: [5, 4],
            fill: false,
            pointRadius: 0,
            tension: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              boxWidth: 14,
              font: { size: 11, weight: "bold" }
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (ctx.dataset.type === "line") return "Ideal Reference: Actual = Predicted";
                const pt = ctx.raw;
                const err = Math.abs(pt.y - pt.x);
                return `${pt.name} (${pt.city}, ${pt.ym}): Act = ${pt.x.toLocaleString()} trips | Pred = ${pt.y.toLocaleString()} trips (Error: ${err.toFixed(1)})`;
              }
            }
          }
        },
        scales: {
          x: {
            type: "linear",
            position: "bottom",
            title: {
              display: true,
              text: `2025 Actual ${metricTitle} (Completed Journeys / Month)`,
              font: { size: 12, weight: "bold" }
            },
            grid: { color: "#f1f5f9" }
          },
          y: {
            type: "linear",
            title: {
              display: true,
              text: `Model Predicted ${metricTitle} (Completed Journeys / Month)`,
              font: { size: 12, weight: "bold" }
            },
            grid: { color: "#f1f5f9" }
          }
        }
      }
    });
  }

  /**
   * Renders the Monthly WAPE Breakdown comparison chart (May to October 2025).
   */
  function renderMonthlyWapeChart() {
    const canvas = document.getElementById("chart-forecast-monthly-wape");
    if (!canvas || !summaryData || !summaryData.monthly_wape_breakdown) return;
    const ctx = canvas.getContext("2d");

    if (monthlyWapeChartInstance) {
      monthlyWapeChartInstance.destroy();
      monthlyWapeChartInstance = null;
    }

    const items = summaryData.monthly_wape_breakdown;
    const labels = items.map((x) => x.month);
    const baseWape = items.map((x) => x.base_wape);
    const ridgeWape = items.map((x) => x.ridge_wape);
    const dtWape = items.map((x) => x.dt_wape);

    monthlyWapeChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Same-Month Baseline",
            data: baseWape,
            backgroundColor: "rgba(5, 150, 105, 0.8)",
            borderColor: "#047857",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Ridge Regression",
            data: ridgeWape,
            backgroundColor: "rgba(234, 88, 12, 0.8)",
            borderColor: "#c2410c",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Decision Tree",
            data: dtWape,
            backgroundColor: "rgba(124, 58, 237, 0.8)",
            borderColor: "#6d28d9",
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { boxWidth: 12, font: { size: 11, weight: "bold" } }
          },
          tooltip: {
            callbacks: {
              afterLabel: function (ctx) {
                if (ctx.label === "2025-06" && ctx.datasetIndex === 1) {
                  return "Ridge outperforms Baseline (15.0% vs 24.7%) during June surge";
                }
                return "";
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 11, weight: "600" } }
          },
          y: {
            title: {
              display: true,
              text: "Departures WAPE (%)",
              font: { size: 11, weight: "bold" }
            },
            grid: { color: "#f1f5f9" },
            beginAtZero: true
          }
        }
      }
    });
  }

  /**
   * Renders the Top-20 Net Outflow Ranking Overlap comparison chart.
   */
  function renderRankingOverlapChart() {
    const canvas = document.getElementById("chart-forecast-ranking-overlap");
    if (!canvas || !summaryData || !summaryData.ranking_overlap_metrics) return;
    const ctx = canvas.getContext("2d");

    if (rankingOverlapChartInstance) {
      rankingOverlapChartInstance.destroy();
      rankingOverlapChartInstance = null;
    }

    const items = summaryData.ranking_overlap_metrics;
    const labels = items.map((x) => x.month);

    // Parse '15/20' into integer 15
    const baseOverlap = items.map((x) => parseInt(x.base_deficit_overlap.split("/")[0], 10));
    const ridgeOverlap = items.map((x) => parseInt(x.ridge_deficit_overlap.split("/")[0], 10));
    const dtOverlap = items.map((x) => parseInt(x.dt_deficit_overlap.split("/")[0], 10));

    rankingOverlapChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Ridge Top-20 Net Outflow Matches",
            data: ridgeOverlap,
            backgroundColor: "rgba(234, 88, 12, 0.85)",
            borderColor: "#c2410c",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Baseline Top-20 Net Outflow Matches",
            data: baseOverlap,
            backgroundColor: "rgba(5, 150, 105, 0.7)",
            borderColor: "#047857",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Decision Tree Matches",
            data: dtOverlap,
            backgroundColor: "rgba(124, 58, 237, 0.5)",
            borderColor: "#6d28d9",
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { boxWidth: 12, font: { size: 11, weight: "bold" } }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const count = ctx.parsed.y;
                const pct = ((count / 20) * 100).toFixed(0);
                return `${ctx.dataset.label}: ${count} / 20 (${pct}% match rate)`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 11, weight: "600" } }
          },
          y: {
            max: 20,
            title: {
              display: true,
              text: "Top-20 Net Outflow Hubs Matched",
              font: { size: 11, weight: "bold" }
            },
            grid: { color: "#f1f5f9" },
            beginAtZero: true
          }
        }
      }
    });
  }

  /**
   * Renders the Benchmarking Scorecard Table comparing Overall, Low-Usage, and Full-Season Reference cohorts.
   */
  function renderScorecardTable() {
    const tbody = document.getElementById("forecast-scorecard-tbody");
    if (!tbody || !summaryData) return;

    let html = "";

    // Header 1: Multi-Model Evaluation Cohort (May-Oct 2025, N=2,718)
    html += `
      <tr class="cohort-header-row">
        <td colspan="8">
          <strong>Fair Multi-Model Comparison Cohort (May–Oct 2025, N = 2,718 station-months)</strong>
          <span style="font-size: 0.76rem; color: #64748b; font-weight: normal; margin-left: 0.5rem;">
            Identical test cohort across all 3 models; April omitted due to 1-month lag requirement.
          </span>
        </td>
      </tr>
    `;

    summaryData.overall_metrics.forEach((m) => {
      const isBase = m.model_id === "base";
      const highlightCls = isBase ? "table-highlight-base" : "";
      html += `
        <tr class="${highlightCls}">
          <td><strong>${m.model_name}</strong></td>
          <td class="text-center"><span class="badge-cohort">N = 2,718</span></td>
          <td class="text-right"><strong>${m.dep_mae.toFixed(1)}</strong></td>
          <td class="text-right"><strong>${m.dep_wape.toFixed(2)}%</strong></td>
          <td class="text-right">${m.dep_rmse.toFixed(1)}</td>
          <td class="text-right">${m.ret_mae.toFixed(1)}</td>
          <td class="text-right">${m.ret_wape.toFixed(2)}%</td>
          <td class="text-right">${m.ret_rmse.toFixed(1)}</td>
        </tr>
      `;
    });

    // Header 2: Low Usage Sensitivity (Q1, Trips <= 198, N=681)
    html += `
      <tr class="cohort-header-row">
        <td colspan="8">
          <strong>Low-Usage Stations Sensitivity (Bottom 25% by Volume, ≤ 198 trips/month, N = 681)</strong>
          <span style="font-size: 0.76rem; color: #64748b; font-weight: normal; margin-left: 0.5rem;">
            Evaluates model shrinkage distortion on peripheral low-demand docks.
          </span>
        </td>
      </tr>
    `;

    summaryData.low_usage_metrics.forEach((m) => {
      const isRidge = m.model_id === "ridge";
      const highlightCls = isRidge ? "table-highlight-warn" : "";
      html += `
        <tr class="${highlightCls}">
          <td>${m.model_name}</td>
          <td class="text-center"><span class="badge-cohort">N = 681 (Q1)</span></td>
          <td class="text-right"><strong>${m.dep_mae.toFixed(1)}</strong></td>
          <td class="text-right"><strong>${m.dep_wape.toFixed(2)}%</strong></td>
          <td class="text-right">${m.dep_rmse.toFixed(1)}</td>
          <td class="text-right">${m.ret_mae.toFixed(1)}</td>
          <td class="text-right">${m.ret_wape.toFixed(2)}%</td>
          <td class="text-right">${m.ret_rmse.toFixed(1)}</td>
        </tr>
      `;
    });

    // Header 3: Full-Season Baseline Reference (Apr–Oct 2025, N=3,170)
    html += `
      <tr class="cohort-header-row reference-cohort-header">
        <td colspan="8">
          <strong>Full-Season Baseline Reference (Apr–Oct 2025, N = 3,170 station-months)</strong>
          <span style="font-size: 0.76rem; color: #b45309; font-weight: 600; margin-left: 0.5rem;">
            ⚠️ Non-overlapping Cohort: Includes April season launch; cannot be directly compared to Lag-1 models.
          </span>
        </td>
      </tr>
      <tr class="table-reference-row">
        <td><em>Same-Month Baseline (Full 2025 Season)</em></td>
        <td class="text-center"><span class="badge-cohort badge-ref">N = 3,170</span></td>
        <td class="text-right"><strong>147.6</strong></td>
        <td class="text-right"><strong>19.23%</strong></td>
        <td class="text-right">270.9</td>
        <td class="text-right">146.0</td>
        <td class="text-right">19.02%</td>
        <td class="text-right">272.1</td>
      </tr>
    `;

    tbody.innerHTML = html;
  }

  /**
   * Renders the Station Net Flow Triage Table for operational planning.
   */
  function renderTriageTable(records) {
    const tbody = document.getElementById("forecast-triage-tbody");
    if (!tbody) return;

    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 1.5rem; color: #94a3b8;">No records match your filter criteria.</td></tr>`;
      return;
    }

    // Sort stations by greatest net outflow (act_net ascending: large negative returns - departures)
    // Or if filtered by returns, by returns
    const sorted = [...records].sort((a, b) => a.act_net - b.act_net);
    const top25 = sorted.slice(0, 25);

    let html = "";
    top25.forEach((r, idx) => {
      const cityBadge = r.city === "Helsinki" ? "badge-city-helsinki" : "badge-city-espoo";
      const flowType = r.act_net < 0 ? "badge-commute-res" : "badge-commute-surp";
      const flowLabel = r.act_net < 0 ? "Net Outflow Hub" : "Net Inflow Hub";

      html += `
        <tr>
          <td class="text-center" style="font-weight: 700; color: #64748b;">${idx + 1}</td>
          <td><strong>${r.name}</strong> <span style="font-size: 0.72rem; color: #94a3b8;">#${r.sid}</span></td>
          <td><span class="badge-city ${cityBadge}">${r.city}</span></td>
          <td class="text-center"><span class="badge-archetype ${flowType}">${flowLabel}</span></td>
          <td class="text-right" style="font-weight: 700; color: ${r.act_net < 0 ? '#b91c1c' : '#047857'}">
            ${r.act_net > 0 ? '+' : ''}${r.act_net.toLocaleString()}
          </td>
          <td class="text-right">${r.base_net > 0 ? '+' : ''}${r.base_net.toLocaleString()}</td>
          <td class="text-right" style="font-weight: 600; color: #ea580c;">
            ${r.ridge_net > 0 ? '+' : ''}${r.ridge_net.toFixed(1)}
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }

  /**
   * Initializes the City-Day Weather Scenario Explorer.
   */
  function initWeatherScenario() {
    if (!scenarioData) return;
    updateScenarioView();
  }

  /**
   * Binds event listeners for the scenario controls.
   */
  function bindScenarioEvents() {
    const citySel = document.getElementById("scenario-city");
    const monthSel = document.getElementById("scenario-month");
    const daytypeSel = document.getElementById("scenario-daytype");
    const tdaySlider = document.getElementById("scenario-tday");
    const precipSlider = document.getElementById("scenario-precip");

    if (citySel) {
      citySel.addEventListener("change", (e) => {
        scenarioState.city = e.target.value;
        updateScenarioView();
      });
    }

    if (monthSel) {
      monthSel.addEventListener("change", (e) => {
        scenarioState.month = parseInt(e.target.value, 10);
        updateScenarioView();
      });
    }

    if (daytypeSel) {
      daytypeSel.addEventListener("change", (e) => {
        scenarioState.daytype = e.target.value;
        updateScenarioView();
      });
    }

    if (tdaySlider) {
      const updateTday = (e) => {
        scenarioState.tday = parseFloat(e.target.value);
        const badge = document.getElementById("scenario-tday-val");
        if (badge) badge.textContent = `${scenarioState.tday.toFixed(1)}°C`;
        updateScenarioView();
      };
      tdaySlider.addEventListener("input", updateTday);
      tdaySlider.addEventListener("change", updateTday);
    }

    if (precipSlider) {
      const updatePrecip = (e) => {
        scenarioState.precip = parseFloat(e.target.value);
        const badge = document.getElementById("scenario-precip-val");
        if (badge) badge.textContent = `${scenarioState.precip.toFixed(1)} mm`;
        updateScenarioView();
      };
      precipSlider.addEventListener("input", updatePrecip);
      precipSlider.addEventListener("change", updatePrecip);
    }
  }

  /**
   * Evaluates the what-if scenario using 2024-trained Ridge regression models.
   * Compares the weather-augmented model with the calendar-only baseline,
   * calculates empirical 2025 test residual bands, verifies empirical bounds,
   * and triggers historical analog day retrieval.
   */
  function updateScenarioView() {
    if (!scenarioData || !scenarioData.models) return;

    const calModel = scenarioData.models.calendar_only;
    const wthModel = scenarioData.models.weather;
    const bounds = scenarioData.meta.empirical_bounds;

    const isHelsinki = scenarioState.city === "Helsinki" ? 1.0 : 0.0;
    const isWeekend = scenarioState.daytype === "weekend" ? 1.0 : 0.0;
    const month = scenarioState.month;
    const tday = scenarioState.tday;
    const precip = scenarioState.precip;

    // Feature indicators (m_5 to m_10; m_4 is reference category)
    const mIndicators = {};
    for (let m = 5; m <= 10; m++) {
      mIndicators[`m_${m}`] = month === m ? 1.0 : 0.0;
    }

    // 1. Calendar-Only Baseline Score
    let calScore = calModel.intercept;
    calScore += (calModel.coefficients.is_helsinki || 0) * isHelsinki;
    calScore += (calModel.coefficients.is_weekend || 0) * isWeekend;
    for (let m = 5; m <= 10; m++) {
      calScore += (calModel.coefficients[`m_${m}`] || 0) * mIndicators[`m_${m}`];
    }
    const calPred = Math.max(0, calScore);

    // 2. Weather-Augmented Model Score
    let wthScore = wthModel.intercept;
    wthScore += (wthModel.coefficients.is_helsinki || 0) * isHelsinki;
    wthScore += (wthModel.coefficients.is_weekend || 0) * isWeekend;
    for (let m = 5; m <= 10; m++) {
      wthScore += (wthModel.coefficients[`m_${m}`] || 0) * mIndicators[`m_${m}`];
    }
    wthScore += (wthModel.coefficients.tday || 0) * tday;
    wthScore += (wthModel.coefficients.precip || 0) * precip;
    const wthPred = Math.max(0, wthScore);

    // 3. Marginal Weather Effect Delta
    const delta = wthPred - calPred;
    const deltaPct = calPred > 0 ? (delta / calPred) * 100 : 0;

    // 4. Empirical Residual Bounds (from 2025 out-of-time test evaluation)
    const cityKey = scenarioState.city.toLowerCase();
    const cityResiduals = (wthModel.empirical_residuals && wthModel.empirical_residuals[cityKey])
      ? wthModel.empirical_residuals[cityKey]
      : { p10: -2000, p90: 2000, mae: 1500 };

    const lowerBand = Math.max(0, Math.round(wthPred + cityResiduals.p10));
    const upperBand = Math.round(wthPred + cityResiduals.p90);
    const maeVal = Math.round(cityResiduals.mae);

    // 5. Check empirical bounds
    const warningBox = document.getElementById("scenario-range-warning");
    const warningText = document.getElementById("scenario-range-warning-text");
    const isTdayOut = bounds && bounds.tday ? (tday < bounds.tday.min || tday > bounds.tday.max) : false;
    const isPrecipOut = bounds && bounds.precip ? (precip < bounds.precip.min || precip > bounds.precip.max) : false;

    if (warningBox && warningText) {
      if (isTdayOut || isPrecipOut) {
        const warnMsgs = [];
        if (isTdayOut) {
          warnMsgs.push(`Selected temperature (${tday.toFixed(1)}°C) falls outside the observed 2024–2025 operating season boundaries (${bounds.tday.min.toFixed(1)}°C to +${bounds.tday.max.toFixed(1)}°C).`);
        }
        if (isPrecipOut) {
          warnMsgs.push(`Selected precipitation (${precip.toFixed(1)} mm) falls outside the observed range (${bounds.precip.min.toFixed(1)} mm to ${bounds.precip.max.toFixed(1)} mm).`);
        }
        warnMsgs.push("Linear projections in this extrapolation regime carry heightened uncertainty and should be evaluated with caution.");
        warningText.textContent = warnMsgs.join(" ");
        warningBox.style.display = "flex";
      } else {
        warningBox.style.display = "none";
      }
    }

    // 6. Update KPI card values
    const estDepElem = document.getElementById("scenario-est-departures");
    const estBandElem = document.getElementById("scenario-est-band");
    const baseDepElem = document.getElementById("scenario-base-departures");
    const weatherDeltaElem = document.getElementById("scenario-weather-delta");
    const weatherDeltaPctElem = document.getElementById("scenario-weather-delta-pct");
    const weatherDeltaCard = weatherDeltaElem ? weatherDeltaElem.closest(".scenario-output-card") : null;
    const accuracyElem = document.getElementById("scenario-accuracy-context");

    if (estDepElem) estDepElem.textContent = `${Math.round(wthPred).toLocaleString()} trips`;
    if (estBandElem) {
      estBandElem.textContent = `Empirical 80% 2025 Test Error Band: [${lowerBand.toLocaleString()} to ${upperBand.toLocaleString()} trips] (MAE: ±${maeVal.toLocaleString()} trips)`;
    }
    if (baseDepElem) baseDepElem.textContent = `${Math.round(calPred).toLocaleString()} trips`;

    if (weatherDeltaElem) {
      weatherDeltaElem.textContent = `${delta >= 0 ? '+' : ''}${Math.round(delta).toLocaleString()} trips`;
    }
    if (weatherDeltaPctElem) {
      weatherDeltaPctElem.textContent = `${delta >= 0 ? '+' : ''}${deltaPct.toFixed(1)}% vs. calendar-only baseline`;
    }
    if (weatherDeltaCard) {
      if (delta < 0) {
        weatherDeltaCard.classList.add("negative-delta");
      } else {
        weatherDeltaCard.classList.remove("negative-delta");
      }
    }

    if (accuracyElem && wthModel.metrics && calModel.metrics) {
      const cityWth = wthModel.metrics[cityKey];
      const cityCal = calModel.metrics[cityKey];
      if (cityWth && cityCal) {
        accuracyElem.innerHTML = `Weather WAPE: <strong>${cityWth.wape.toFixed(2)}%</strong> (MAE ${Math.round(cityWth.mae).toLocaleString()} trips)<br>Calendar Baseline WAPE: <strong>${cityCal.wape.toFixed(2)}%</strong> (MAE ${Math.round(cityCal.mae).toLocaleString()} trips)`;
      }
    }

    // 7. Render 3-5 historical analog days from 2025 test set
    renderAnalogDays();
  }

  /**
   * Renders 3-5 closest 2025 actual operating test days as factual grounding.
   */
  function renderAnalogDays() {
    const tbody = document.getElementById("scenario-analog-tbody");
    if (!tbody || !scenarioData || !scenarioData.test_2025_records) return;

    const city = scenarioState.city;
    const month = scenarioState.month;
    const isWeekend = scenarioState.daytype === "weekend" ? 1 : 0;
    const tday = scenarioState.tday;
    const precip = scenarioState.precip;

    const cityRecords = scenarioData.test_2025_records.filter((r) => r.city === city);

    // Compute standardized distance
    // Weight month difference (x4.0), day-type difference (x5.0), normalized tday diff / 5.5, normalized precip diff / 4.5
    const scored = cityRecords.map((r) => {
      const mDiff = Math.abs(r.month - month);
      const wkDiff = Math.abs(r.is_weekend - isWeekend);
      const tDiff = (r.tday - tday) / 5.5;
      const pDiff = (r.precip - precip) / 4.5;
      const dist = (mDiff * 4.0) + (wkDiff * 5.0) + (tDiff * tDiff + pDiff * pDiff);
      return { record: r, dist: dist };
    });

    scored.sort((a, b) => a.dist - b.dist);
    const topAnalogs = scored.slice(0, 5).map((item) => item.record);

    let html = "";
    topAnalogs.forEach((r, idx) => {
      const residual = r.dep - Math.round(r.wth_pred);
      const resColor = residual >= 0 ? "#047857" : "#b91c1c";
      const resSign = residual >= 0 ? "+" : "";

      html += `
        <tr>
          <td class="text-center" style="font-weight: 700; color: #64748b;">#${idx + 1}</td>
          <td><strong>${r.date}</strong></td>
          <td>${r.day_name}</td>
          <td><span class="badge-city ${r.city === 'Helsinki' ? 'badge-city-helsinki' : 'badge-city-espoo'}">${r.city}</span></td>
          <td class="text-right" style="font-weight: 600;">${r.tday.toFixed(1)}°C</td>
          <td class="text-right">${r.precip.toFixed(1)} mm</td>
          <td class="text-right" style="font-weight: 700; color: var(--primary-dark);">${r.dep.toLocaleString()}</td>
          <td class="text-right" style="color: #64748b;">${Math.round(r.wth_pred).toLocaleString()}</td>
          <td class="text-right" style="font-weight: 600; color: ${resColor};">
            ${resSign}${residual.toLocaleString()}
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }

  return {
    init: init,
    updateDynamicViews: updateDynamicViews,
    updateScenarioView: updateScenarioView
  };
})();
