/**
 * HSL City Bike Project - Commute Dynamics & Peak Hours Module (Phase 3)
 * Renders 24-hour diurnal profiles and morning vs. evening commute tidal reversals
 * using Chart.js, powered by data_hourly_city.json and data_commute_peaks.json.
 */

const CommuteModule = (function () {
  "use strict";

  // Data cache
  let hourlyData = null;  // Loaded from ./data/data_hourly_city.json
  let peaksData = null;   // Loaded from ./data/data_commute_peaks.json

  // Chart instances
  let hourlyChartInstance = null;
  let tidalChartInstance = null;
  let quadrantChartInstance = null;

  // Filter state for diurnal curve
  const hourlyFilters = {
    city: "All",           // "All", "Helsinki", "Espoo"
    timeframe: "overall_all", // "overall_all", "overall_2024", "overall_2025", "2024-04", ...
    mode: "weekday_vs_weekend" // "weekday_vs_weekend", "weekday_dep_ret", "weekend_dep_ret", "net_flow"
  };

  /**
   * Initializes the commute dynamics module.
   */
  function init() {
    bindEvents();
    loadCommuteData();
  }

  /**
   * Binds event listeners for diurnal curve filters.
   */
  function bindEvents() {
    const citySelect = document.getElementById("commute-filter-city");
    const timeSelect = document.getElementById("commute-filter-timeframe");
    const modeSelect = document.getElementById("commute-filter-mode");

    if (citySelect) {
      citySelect.addEventListener("change", (e) => {
        hourlyFilters.city = e.target.value;
        updateHourlyChart();
      });
    }

    if (timeSelect) {
      timeSelect.addEventListener("change", (e) => {
        hourlyFilters.timeframe = e.target.value;
        updateHourlyChart();
      });
    }

    if (modeSelect) {
      modeSelect.addEventListener("change", (e) => {
        hourlyFilters.mode = e.target.value;
        updateHourlyChart();
      });
    }
  }

  /**
   * Fetches required JSON data via strictly relative paths.
   */
  function loadCommuteData() {
    const loadingElem = document.getElementById("commute-loading-overlay");
    if (loadingElem) loadingElem.style.display = "flex";

    Promise.all([
      fetch("./data/data_hourly_city.json").then((r) => {
        if (!r.ok) throw new Error(`Hourly data HTTP ${r.status}`);
        return r.json();
      }),
      fetch("./data/data_commute_peaks.json").then((r) => {
        if (!r.ok) throw new Error(`Peaks data HTTP ${r.status}`);
        return r.json();
      })
    ])
      .then(([hourly, peaks]) => {
        hourlyData = hourly;
        peaksData = peaks;

        if (loadingElem) loadingElem.style.display = "none";

        populateTimeframeDropdown(hourly.meta.months);
        updateAuditMetricsCard(peaks.audit);
        renderHourlyChart();
        renderTidalSwingChart();
        renderQuadrantChart();
        renderCommuterTable();
      })
      .catch((err) => {
        if (loadingElem) loadingElem.style.display = "none";
        console.error("CommuteModule load error:", err);
        const errBanner = document.getElementById("commute-error-banner");
        if (errBanner) {
          errBanner.textContent = `Failed to load commute datasets: ${err.message}.`;
          errBanner.style.display = "block";
        }
      });
  }

  /**
   * Dynamically populates the timeframe selector options.
   */
  function populateTimeframeDropdown(months) {
    const select = document.getElementById("commute-filter-timeframe");
    if (!select || !months) return;

    // Clear existing dynamic month options while keeping overall options
    select.innerHTML = `
      <option value="overall_all" selected>All Seasons (2024 &amp; 2025 Combined)</option>
      <option value="overall_2025">2025 Full Season Only</option>
      <option value="overall_2024">2024 Full Season Only</option>
      <optgroup label="Individual Months (2025)">
        <option value="2025-04">April 2025</option>
        <option value="2025-05">May 2025</option>
        <option value="2025-06">June 2025</option>
        <option value="2025-07">July 2025 (Midsummer Peak)</option>
        <option value="2025-08">August 2025</option>
        <option value="2025-09">September 2025</option>
        <option value="2025-10">October 2025</option>
      </optgroup>
      <optgroup label="Individual Months (2024)">
        <option value="2024-04">April 2024</option>
        <option value="2024-05">May 2024</option>
        <option value="2024-06">June 2024</option>
        <option value="2024-07">July 2024 (Midsummer Peak)</option>
        <option value="2024-08">August 2024</option>
        <option value="2024-09">September 2024</option>
        <option value="2024-10">October 2024</option>
      </optgroup>
    `;
  }

  /**
   * Updates data quality audit badges.
   */
  function updateAuditMetricsCard(audit) {
    if (!audit) return;
    const mid24 = document.getElementById("audit-midnight-2024");
    const mid25 = document.getElementById("audit-midnight-2025");
    const clean24 = document.getElementById("audit-clean-2024");
    const clean25 = document.getElementById("audit-clean-2025");

    if (mid24 && audit["2024"]) mid24.textContent = audit["2024"].midnight_crossings.toLocaleString();
    if (mid25 && audit["2025"]) mid25.textContent = audit["2025"].midnight_crossings.toLocaleString();
    if (clean24 && audit["2024"]) clean24.textContent = (audit["2024"].clean_trips / 1000000).toFixed(2) + "M";
    if (clean25 && audit["2025"]) clean25.textContent = (audit["2025"].clean_trips / 1000000).toFixed(2) + "M";
  }

  /**
   * Prepares datasets and options for the 24-hour diurnal profile line chart.
   */
  function buildHourlyChartConfig() {
    const city = hourlyFilters.city;
    const tf = hourlyFilters.timeframe;
    const mode = hourlyFilters.mode;

    const cityData = hourlyData.profiles[city];
    if (!cityData) return null;

    const weekdayPoints = cityData.weekday[tf] || cityData.weekday["overall_all"];
    const weekendPoints = cityData.weekend[tf] || cityData.weekend["overall_all"];

    const labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`);

    let datasets = [];

    if (mode === "weekday_vs_weekend") {
      datasets = [
        {
          label: "Weekday (Mon–Fri) Departures",
          data: weekdayPoints.map((p) => p.avg_dep),
          borderColor: "#007e87",
          backgroundColor: "rgba(0, 126, 135, 0.12)",
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.3
        },
        {
          label: "Weekend (Sat–Sun) Departures",
          data: weekendPoints.map((p) => p.avg_dep),
          borderColor: "#d45c39",
          backgroundColor: "rgba(212, 92, 57, 0.10)",
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.3
        }
      ];
    } else if (mode === "weekday_dep_ret") {
      datasets = [
        {
          label: "Weekday (Mon–Fri) Departures",
          data: weekdayPoints.map((p) => p.avg_dep),
          borderColor: "#007e87",
          backgroundColor: "rgba(0, 126, 135, 0.12)",
          borderWidth: 2.5,
          pointRadius: 3,
          fill: true,
          tension: 0.3
        },
        {
          label: "Weekday (Mon–Fri) Returns",
          data: weekdayPoints.map((p) => p.avg_ret),
          borderColor: "#2b5c8f",
          backgroundColor: "rgba(43, 92, 143, 0.10)",
          borderWidth: 2.5,
          pointRadius: 3,
          fill: true,
          tension: 0.3
        }
      ];
    } else if (mode === "weekend_dep_ret") {
      datasets = [
        {
          label: "Weekend (Sat–Sun) Departures",
          data: weekendPoints.map((p) => p.avg_dep),
          borderColor: "#d45c39",
          backgroundColor: "rgba(212, 92, 57, 0.12)",
          borderWidth: 2.5,
          pointRadius: 3,
          fill: true,
          tension: 0.3
        },
        {
          label: "Weekend (Sat–Sun) Returns",
          data: weekendPoints.map((p) => p.avg_ret),
          borderColor: "#f77f00",
          backgroundColor: "rgba(247, 127, 0, 0.10)",
          borderWidth: 2.5,
          pointRadius: 3,
          fill: true,
          tension: 0.3
        }
      ];
    } else if (mode === "net_flow") {
      datasets = [
        {
          label: "Weekday (Mon–Fri) Net Flow (Returns - Departures)",
          data: weekdayPoints.map((p) => p.net_flow),
          borderColor: "#2b5c8f",
          backgroundColor: "rgba(43, 92, 143, 0.12)",
          borderWidth: 2.2,
          pointRadius: 3,
          fill: false,
          tension: 0.3
        },
        {
          label: "Weekend (Sat–Sun) Net Flow (Returns - Departures)",
          data: weekendPoints.map((p) => p.net_flow),
          borderColor: "#64748b",
          backgroundColor: "rgba(100, 116, 139, 0.10)",
          borderWidth: 2.2,
          borderDash: [5, 4],
          pointRadius: 3,
          fill: false,
          tension: 0.3
        }
      ];
    }

    return {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              boxWidth: 14,
              font: { size: 12, family: "-apple-system, Segoe UI, sans-serif", weight: "600" }
            }
          },
          tooltip: {
            backgroundColor: "#12313a",
            titleFont: { size: 13, weight: "bold" },
            bodyFont: { size: 12 },
            padding: 10,
            callbacks: {
              label: function (context) {
                const val = context.raw;
                const unit = mode === "net_flow" ? "trips total" : "trips / day";
                return ` ${context.dataset.label}: ${val.toLocaleString()} ${unit}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: "#f1f5f9" },
            ticks: {
              font: { size: 11 },
              maxRotation: 0,
              callback: function (val, idx) {
                // Label every 2 hours for readability
                return idx % 2 === 0 ? labels[idx] : "";
              }
            },
            title: {
              display: true,
              text: "Hour of Day (Europe/Helsinki Local Time)",
              font: { size: 11, weight: "600" },
              color: "#64748b"
            }
          },
          y: {
            grid: { color: "#e2e8f0" },
            ticks: {
              font: { size: 11 },
              callback: function (val) {
                return val.toLocaleString();
              }
            },
            title: {
              display: true,
              text: mode === "net_flow" ? "Cumulative Net Flow (Trips)" : "Average Trips / Operating Day",
              font: { size: 11, weight: "600" },
              color: "#64748b"
            }
          }
        }
      }
    };
  }

  /**
   * Renders the 24-hour diurnal profile line chart.
   */
  function renderHourlyChart() {
    const canvas = document.getElementById("chart-hourly-profile");
    if (!canvas || !hourlyData) return;

    const config = buildHourlyChartConfig();
    if (!config) return;

    if (hourlyChartInstance) {
      hourlyChartInstance.destroy();
    }

    hourlyChartInstance = new Chart(canvas, config);
  }

  /**
   * Updates existing diurnal curve when filters change.
   */
  function updateHourlyChart() {
    if (!hourlyChartInstance || !hourlyData) {
      renderHourlyChart();
      return;
    }
    const config = buildHourlyChartConfig();
    if (!config) return;

    hourlyChartInstance.data = config.data;
    hourlyChartInstance.options = config.options;
    hourlyChartInstance.update();
  }

  /**
   * Renders the Horizontal Bar Chart for Top 10 Tidal Swing Commuter Hubs.
   * Matches verified ranking order:
   * 1. Salmisaarenranta (12,587), 2. Itämerentori (11,860), 3. Sompasaari (10,781), ...
   */
  function renderTidalSwingChart() {
    const canvas = document.getElementById("chart-tidal-swing");
    if (!canvas || !peaksData || !peaksData.top_tidal_swing) return;

    // Display Top 10 sorted ascending for horizontal bar (Rank 1 at the top of the chart)
    const hubs = [...peaksData.top_tidal_swing].reverse();

    const labels = hubs.map((h, i) => `${peaksData.top_tidal_swing.length - i}. ${h.station_name} (${h.city})`);
    const morningData = hubs.map((h) => h.morn_net);
    const eveningData = hubs.map((h) => h.eve_net);

    if (tidalChartInstance) {
      tidalChartInstance.destroy();
    }

    tidalChartInstance = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Morning Peak Net Flow (07:00–09:00)",
            data: morningData,
            backgroundColor: "rgba(247, 127, 0, 0.85)",
            borderColor: "#d97706",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Evening Peak Net Flow (16:00–18:00)",
            data: eveningData,
            backgroundColor: "rgba(43, 92, 143, 0.85)",
            borderColor: "#1e3a8a",
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              boxWidth: 14,
              font: { size: 11.5, weight: "600" }
            }
          },
          tooltip: {
            backgroundColor: "#12313a",
            callbacks: {
              label: function (context) {
                const val = context.raw;
                const sign = val > 0 ? "+" : "";
                const tag = val < 0 ? "Deficit" : "Surplus";
                return ` ${context.dataset.label}: ${sign}${val.toLocaleString()} trips (${tag})`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: "#e2e8f0" },
            title: {
              display: true,
              text: "Net Flow = Returns - Departures (Cumulative Weekday Trips 2024–2025)",
              font: { size: 11, weight: "600" },
              color: "#64748b"
            },
            ticks: {
              callback: function (val) {
                return (val > 0 ? "+" : "") + val.toLocaleString();
              }
            }
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { size: 11, weight: "500" }
            }
          }
        }
      }
    });
  }

  /**
   * Renders the Commute Quadrant Scatter Chart across 120 Busiest Commuter Hubs.
   * X-axis: Morning Peak Net Flow (07:00-09:00)
   * Y-axis: Evening Peak Net Flow (16:00-18:00)
   */
  function renderQuadrantChart() {
    const canvas = document.getElementById("chart-commute-quadrant");
    if (!canvas || !peaksData || !peaksData.commuter_hubs) return;

    const hubs = peaksData.commuter_hubs;

    // Segment stations by commute archetype
    const quad2_residential = []; // Morn Net < 0 & Eve Net > 0
    const quad4_workplace = [];   // Morn Net > 0 & Eve Net < 0
    const quad3_deficit_sink = []; // Morn Net < 0 & Eve Net < 0
    const quad1_surplus_sink = []; // Morn Net > 0 & Eve Net > 0

    hubs.forEach((h) => {
      const point = {
        x: h.morn_net,
        y: h.eve_net,
        name: h.station_name,
        city: h.city,
        total: h.total_peak_trips,
        swing: h.tidal_swing
      };

      if (h.morn_net <= 0 && h.eve_net >= 0) {
        quad2_residential.push(point);
      } else if (h.morn_net >= 0 && h.eve_net <= 0) {
        quad4_workplace.push(point);
      } else if (h.morn_net < 0 && h.eve_net < 0) {
        quad3_deficit_sink.push(point);
      } else {
        quad1_surplus_sink.push(point);
      }
    });

    if (quadrantChartInstance) {
      quadrantChartInstance.destroy();
    }

    quadrantChartInstance = new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Residential Feeder (Morn Deficit → Eve Surplus; e.g. Sompasaari)",
            data: quad2_residential,
            backgroundColor: "rgba(212, 92, 57, 0.8)",
            borderColor: "#d45c39",
            pointRadius: 6,
            pointHoverRadius: 9
          },
          {
            label: "Workplace Center (Morn Surplus → Eve Deficit; e.g. Salmisaarenranta)",
            data: quad4_workplace,
            backgroundColor: "rgba(43, 92, 143, 0.8)",
            borderColor: "#2b5c8f",
            pointRadius: 6,
            pointHoverRadius: 9
          },
          {
            label: "Continuous Deficit Sink (All-Day Net Outflow; e.g. Pasila rail hub)",
            data: quad3_deficit_sink,
            backgroundColor: "rgba(185, 28, 28, 0.85)",
            borderColor: "#991b1b",
            pointRadius: 6,
            pointHoverRadius: 9
          },
          {
            label: "Continuous Accumulator (All-Day Net Inflow; e.g. Waterfront dining)",
            data: quad1_surplus_sink,
            backgroundColor: "rgba(5, 150, 105, 0.8)",
            borderColor: "#047857",
            pointRadius: 5,
            pointHoverRadius: 8
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
              boxWidth: 12,
              font: { size: 11, weight: "600" }
            }
          },
          tooltip: {
            backgroundColor: "#12313a",
            padding: 10,
            callbacks: {
              title: function (items) {
                if (!items.length) return "";
                const pt = items[0].raw;
                return `${pt.name} (${pt.city})`;
              },
              label: function (context) {
                const pt = context.raw;
                return [
                  `Morning Net (07–09): ${pt.x > 0 ? "+" : ""}${pt.x.toLocaleString()} trips`,
                  `Evening Net (16–18): ${pt.y > 0 ? "+" : ""}${pt.y.toLocaleString()} trips`,
                  `Tidal Swing: ${pt.swing.toLocaleString()} trips`,
                  `Total Peak Volume: ${pt.total.toLocaleString()} trips`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: "#e2e8f0" },
            title: {
              display: true,
              text: "Morning Peak Net Flow: 07:00–09:00 (Returns - Departures)",
              font: { size: 11, weight: "600" },
              color: "#64748b"
            },
            ticks: {
              callback: function (val) {
                return (val > 0 ? "+" : "") + val.toLocaleString();
              }
            }
          },
          y: {
            grid: { color: "#e2e8f0" },
            title: {
              display: true,
              text: "Evening Peak Net Flow: 16:00–18:00 (Returns - Departures)",
              font: { size: 11, weight: "600" },
              color: "#64748b"
            },
            ticks: {
              callback: function (val) {
                return (val > 0 ? "+" : "") + val.toLocaleString();
              }
            }
          }
        }
      }
    });
  }

  /**
   * Populates the Top Commuter Hubs reference table.
   */
  function renderCommuterTable() {
    const tbody = document.getElementById("commuter-table-body");
    if (!tbody || !peaksData || !peaksData.commuter_hubs) return;

    // Take top 25 busiest hubs for reference table
    const topHubs = peaksData.commuter_hubs.slice(0, 25);

    const rowsHtml = topHubs.map((h, idx) => {
      let badgeClass = "badge-commute-sink";
      let archetype = "Deficit Sink";
      if (h.morn_net <= 0 && h.eve_net >= 0) {
        badgeClass = "badge-commute-res";
        archetype = "Residential Feeder";
      } else if (h.morn_net >= 0 && h.eve_net <= 0) {
        badgeClass = "badge-commute-work";
        archetype = "Workplace Center";
      } else if (h.morn_net >= 0 && h.eve_net >= 0) {
        badgeClass = "badge-commute-surp";
        archetype = "Accumulator";
      }

      const mornClass = h.morn_net < 0 ? "val-deficit" : "val-surplus";
      const eveClass = h.eve_net < 0 ? "val-deficit" : "val-surplus";
      const cityBadge = h.city.toLowerCase() === "helsinki" ? "badge-city-helsinki" : "badge-city-espoo";

      return `
        <tr>
          <td class="text-center" style="font-weight:600; color:#64748b;">#${idx + 1}</td>
          <td style="font-weight:700; color:#12313a;">${escapeHtml(h.station_name)}</td>
          <td><span class="badge-city ${cityBadge}">${h.city}</span></td>
          <td class="text-center"><span class="badge-archetype ${badgeClass}">${archetype}</span></td>
          <td class="text-right ${mornClass}" style="font-weight:600;">${h.morn_net > 0 ? "+" : ""}${h.morn_net.toLocaleString()}</td>
          <td class="text-right ${eveClass}" style="font-weight:600;">${h.eve_net > 0 ? "+" : ""}${h.eve_net.toLocaleString()}</td>
          <td class="text-right" style="font-weight:700; color:#12313a;">${h.tidal_swing.toLocaleString()}</td>
          <td class="text-right">${h.total_peak_trips.toLocaleString()}</td>
        </tr>
      `;
    }).join("");

    tbody.innerHTML = rowsHtml;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  return {
    init: init,
    updateHourlyChart: updateHourlyChart
  };
})();
