/**
 * HSL City Bike Project - FMI Daily Weather & Ridership Exploration Module (Phase 4)
 * Analyzes empirical relationships between retrospective FMI ground meteorological
 * observations (Helsinki Kaisaniemi FMISID 100971, Espoo Tapiola FMISID 874863)
 * and daily city-level cycling volume across 856 matched city-days (2024-2025).
 *
 * Methodological Principles:
 * 1. Strictly retrospective ground observations, NOT weather forecasts.
 * 2. Pearson r represents descriptive seasonal co-movement; NON-CAUSAL.
 * 3. Weather features were strictly excluded from 2025 predictive model training.
 * 4. 23,981 unmapped trips (from 7 coordinate-less docks) are fully preserved in daily city totals.
 */

const WeatherModule = (function () {
  "use strict";

  // Data cache
  let weatherData = null; // Loaded from ./data/data_daily_weather.json

  // Chart instances
  let scatterChartInstance = null;
  let timeSeriesChartInstance = null;
  let rainBarsChartInstance = null;

  // Filter state
  const filters = {
    year: "all",      // "all", "2024", "2025"
    city: "all",      // "all" (Both), "Helsinki", "Espoo"
    param: "tday",    // "tday", "tmax", "tmin", "precip", "snow"
    daytype: "all"    // "all", "weekday", "weekend"
  };

  // Weather parameter definitions & units
  const PARAM_CONFIG = {
    tday: {
      name: "Daily Mean Temperature",
      unit: "°C",
      short: "Mean Temp",
      color: "#f97316"
    },
    tmax: {
      name: "Daily Maximum Temperature",
      unit: "°C",
      short: "Max Temp",
      color: "#ef4444"
    },
    tmin: {
      name: "Daily Minimum Temperature",
      unit: "°C",
      short: "Min Temp",
      color: "#06b6d4"
    },
    precip: {
      name: "Daily Precipitation",
      unit: "mm",
      short: "Precipitation",
      color: "#3b82f6"
    },
    snow: {
      name: "Snow Depth",
      unit: "cm",
      short: "Snow Depth",
      color: "#8b5cf6"
    }
  };

  /**
   * Initializes the weather exploration module.
   */
  function init() {
    bindEvents();
    loadWeatherData();
  }

  /**
   * Binds event listeners for weather filters.
   */
  function bindEvents() {
    const yearSelect = document.getElementById("filter-weather-year");
    const citySelect = document.getElementById("filter-weather-city");
    const paramSelect = document.getElementById("filter-weather-param");
    const daytypeSelect = document.getElementById("filter-weather-daytype");

    if (yearSelect) {
      yearSelect.addEventListener("change", (e) => {
        filters.year = e.target.value;
        updateAllVisuals();
      });
    }

    if (citySelect) {
      citySelect.addEventListener("change", (e) => {
        filters.city = e.target.value;
        updateAllVisuals();
      });
    }

    if (paramSelect) {
      paramSelect.addEventListener("change", (e) => {
        filters.param = e.target.value;
        updateAllVisuals();
      });
    }

    if (daytypeSelect) {
      daytypeSelect.addEventListener("change", (e) => {
        filters.daytype = e.target.value;
        updateAllVisuals();
      });
    }
  }

  /**
   * Fetches weather dataset via strictly relative path.
   */
  function loadWeatherData() {
    const loadingElem = document.getElementById("weather-loading-overlay");
    if (loadingElem) loadingElem.style.display = "flex";

    fetch("./data/data_daily_weather.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} loading weather data`);
        return res.json();
      })
      .then((data) => {
        weatherData = data;
        if (loadingElem) loadingElem.style.display = "none";
        updateAllVisuals();
      })
      .catch((err) => {
        if (loadingElem) loadingElem.style.display = "none";
        console.error("WeatherModule load error:", err);
        const errBanner = document.getElementById("weather-error-banner");
        if (errBanner) {
          errBanner.textContent = `Failed to load weather dataset: ${err.message}.`;
          errBanner.style.display = "block";
        }
      });
  }

  /**
   * Filters the raw records according to current UI selections.
   */
  function getFilteredRecords() {
    if (!weatherData || !weatherData.daily_records) return [];

    return weatherData.daily_records.filter((rec) => {
      // Year filter
      if (filters.year !== "all" && String(rec.year) !== filters.year) return false;
      // City filter
      if (filters.city !== "all" && rec.city !== filters.city) return false;
      // Daytype filter
      if (filters.daytype === "weekday" && rec.is_weekend === 1) return false;
      if (filters.daytype === "weekend" && rec.is_weekend === 0) return false;
      return true;
    });
  }

  /**
   * Computes sample size n, Pearson correlation r, and OLS linear regression (slope, intercept).
   * Note: Strictly descriptive co-movement calculation; no hypothesis tests or inferential significance.
   */
  function calculateStatistics(records, paramKey) {
    const n = records.length;
    if (n < 2) {
      return { n, r: 0, slope: 0, intercept: 0, meanParam: 0, meanDep: 0, minX: 0, maxX: 0 };
    }

    let sumX = 0;
    let sumY = 0;
    records.forEach((r) => {
      sumX += r[paramKey];
      sumY += r.dep;
    });
    const meanX = sumX / n;
    const meanY = sumY / n;

    let numer = 0;
    let denomX = 0;
    let denomY = 0;
    let minX = Infinity;
    let maxX = -Infinity;

    records.forEach((r) => {
      const x = r[paramKey];
      const y = r.dep;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      const dx = x - meanX;
      const dy = y - meanY;
      numer += dx * dy;
      denomX += dx * dx;
      denomY += dy * dy;
    });

    const denom = Math.sqrt(denomX * denomY);
    const r = denom > 0 ? numer / denom : 0;
    const slope = denomX > 0 ? numer / denomX : 0;
    const intercept = meanY - slope * meanX;

    return {
      n,
      r,
      slope,
      intercept,
      meanParam: meanX,
      meanDep: meanY,
      minX,
      maxX
    };
  }

  /**
   * Updates KPI summary cards based on filtered data and computed metrics.
   */
  function updateKPICards(records, stats) {
    const kpiSamples = document.getElementById("kpi-weather-samples");
    const kpiCorr = document.getElementById("kpi-weather-corr");
    const kpiCorrSub = document.getElementById("kpi-weather-corr-sub");
    const kpiSlope = document.getElementById("kpi-weather-slope");
    const kpiSlopeSub = document.getElementById("kpi-weather-slope-sub");
    const kpiRainyDays = document.getElementById("kpi-weather-rainydays");
    const kpiRainyDaysSub = document.getElementById("kpi-weather-rainydays-sub");
    const kpiUnmapped = document.getElementById("kpi-weather-unmapped");

    const cfg = PARAM_CONFIG[filters.param];

    if (kpiSamples) {
      kpiSamples.textContent = stats.n.toLocaleString();
    }

    if (kpiCorr) {
      const sign = stats.r > 0 ? "+" : "";
      kpiCorr.textContent = `${sign}${stats.r.toFixed(3)}`;
    }
    if (kpiCorrSub) {
      if (filters.city === "all") {
        kpiCorrSub.textContent = `Descriptive r for ${cfg.short} (Helsinki alone: +0.780; Espoo alone: +0.734)`;
      } else {
        kpiCorrSub.textContent = `Descriptive Pearson r for ${cfg.short} in ${filters.city} (non-causal)`;
      }
    }

    if (kpiSlope) {
      const sign = stats.slope > 0 ? "+" : "";
      kpiSlope.textContent = `${sign}${stats.slope.toFixed(1)} trips / ${cfg.unit}`;
    }
    if (kpiSlopeSub) {
      kpiSlopeSub.textContent = `Descriptive OLS slope (baseline intercept: ${Math.round(stats.intercept).toLocaleString()})`;
    }

    if (kpiRainyDays && records.length > 0) {
      const rainyCount = records.filter((r) => r.precip > 0).length;
      const pct = ((rainyCount / records.length) * 100).toFixed(1);
      kpiRainyDays.textContent = `${rainyCount} / ${records.length} days`;
      if (kpiRainyDaysSub) {
        kpiRainyDaysSub.textContent = `${pct}% of days recorded measurable precipitation (>0.0 mm)`;
      }
    }

    if (kpiUnmapped && weatherData && weatherData.meta && weatherData.meta.unmapped_trips_audit) {
      const audit = weatherData.meta.unmapped_trips_audit;
      kpiUnmapped.textContent = `${audit.total_departures.toLocaleString()} dep`;
    }
  }

  /**
   * Refreshes all charts and metric cards.
   */
  function updateAllVisuals() {
    const records = getFilteredRecords();
    const stats = calculateStatistics(records, filters.param);

    updateKPICards(records, stats);
    renderScatterChart(records, stats);
    renderTimeSeriesChart(records);
    renderRainImpactChart(records);
  }

  /**
   * Renders the Ridership vs. Weather Scatter Plot with OLS regression trendline.
   */
  function renderScatterChart(records, stats) {
    const canvas = document.getElementById("chart-weather-scatter");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (scatterChartInstance) {
      scatterChartInstance.destroy();
      scatterChartInstance = null;
    }

    const cfg = PARAM_CONFIG[filters.param];

    // Build scatter datasets
    const datasets = [];

    if (filters.city === "all") {
      // Split into Helsinki and Espoo points
      const helsinkiPoints = records
        .filter((r) => r.city === "Helsinki")
        .map((r) => ({
          x: r[filters.param],
          y: r.dep,
          date: r.date,
          day: r.day_name,
          city: "Helsinki"
        }));

      const espooPoints = records
        .filter((r) => r.city === "Espoo")
        .map((r) => ({
          x: r[filters.param],
          y: r.dep,
          date: r.date,
          day: r.day_name,
          city: "Espoo"
        }));

      datasets.push({
        label: "Helsinki (FMISID 100971 Kaisaniemi)",
        data: helsinkiPoints,
        backgroundColor: "rgba(37, 99, 235, 0.65)",
        borderColor: "#2563eb",
        borderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6
      });

      datasets.push({
        label: "Espoo (FMISID 874863 Tapiola)",
        data: espooPoints,
        backgroundColor: "rgba(245, 158, 11, 0.65)",
        borderColor: "#d97706",
        borderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6
      });
    } else {
      const cityColor = filters.city === "Helsinki" ? "rgba(37, 99, 235, 0.65)" : "rgba(245, 158, 11, 0.65)";
      const cityBorder = filters.city === "Helsinki" ? "#2563eb" : "#d97706";

      const points = records.map((r) => ({
        x: r[filters.param],
        y: r.dep,
        date: r.date,
        day: r.day_name,
        city: r.city
      }));

      datasets.push({
        label: `${filters.city} Daily Volume`,
        data: points,
        backgroundColor: cityColor,
        borderColor: cityBorder,
        borderWidth: 1,
        pointRadius: 4.5,
        pointHoverRadius: 6.5
      });
    }

    // Add OLS Linear Regression Trendline dataset
    if (stats.n >= 2 && stats.minX !== stats.maxX) {
      const trendPoints = [
        { x: stats.minX, y: Math.max(0, stats.slope * stats.minX + stats.intercept) },
        { x: stats.maxX, y: Math.max(0, stats.slope * stats.maxX + stats.intercept) }
      ];

      const sign = stats.r > 0 ? "+" : "";
      datasets.push({
        type: "line",
        label: `Descriptive OLS Fit (r = ${sign}${stats.r.toFixed(3)}, slope = ${stats.slope.toFixed(1)})`,
        data: trendPoints,
        borderColor: "#dc2626",
        borderWidth: 2,
        borderDash: [6, 4],
        fill: false,
        pointRadius: 0,
        tension: 0
      });
    }

    scatterChartInstance = new Chart(ctx, {
      type: "scatter",
      data: { datasets },
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
                const pt = ctx.raw;
                if (ctx.dataset.type === "line") {
                  return ctx.dataset.label;
                }
                return `${pt.date} (${pt.day}, ${pt.city}): ${pt.y.toLocaleString()} trips @ ${pt.x} ${cfg.unit}`;
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
              text: `${cfg.name} (${cfg.unit})`,
              font: { size: 12, weight: "bold" }
            },
            grid: { color: "#f1f5f9" }
          },
          y: {
            type: "linear",
            title: {
              display: true,
              text: "Daily Departures (Trips / Day)",
              font: { size: 12, weight: "bold" }
            },
            grid: { color: "#f1f5f9" },
            beginAtZero: true
          }
        }
      }
    });
  }

  /**
   * Renders the Chronological Time Series with strictly separate dual Y-axes.
   * Left axis: Departures (Trips); Right axis: Weather Metric (with physical units).
   */
  function renderTimeSeriesChart(records) {
    const canvas = document.getElementById("chart-weather-timeseries");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (timeSeriesChartInstance) {
      timeSeriesChartInstance.destroy();
      timeSeriesChartInstance = null;
    }

    const cfg = PARAM_CONFIG[filters.param];

    // Aggregate records by calendar date (if Both cities selected, sum trips and average weather)
    const dateMap = new Map();
    records.forEach((r) => {
      if (!dateMap.has(r.date)) {
        dateMap.set(r.date, {
          date: r.date,
          year: r.year,
          dep: 0,
          weatherVals: [],
          day: r.day_name
        });
      }
      const entry = dateMap.get(r.date);
      entry.dep += r.dep;
      entry.weatherVals.push(r[filters.param]);
    });

    const sortedDates = Array.from(dateMap.keys()).sort();
    const labels = sortedDates;
    const tripsData = [];
    const weatherDataArr = [];

    sortedDates.forEach((d) => {
      const item = dateMap.get(d);
      tripsData.push(item.dep);
      const avgW = item.weatherVals.reduce((a, b) => a + b, 0) / item.weatherVals.length;
      weatherDataArr.push(Number(avgW.toFixed(1)));
    });

    timeSeriesChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: filters.city === "all" ? "Combined City Departures (Trips)" : `${filters.city} Departures (Trips)`,
            data: tripsData,
            borderColor: "#0284c7",
            backgroundColor: "rgba(2, 132, 199, 0.12)",
            borderWidth: 2,
            pointRadius: 1,
            pointHoverRadius: 5,
            fill: true,
            yAxisID: "y",
            tension: 0.15
          },
          {
            label: `${cfg.name} (${cfg.unit})`,
            data: weatherDataArr,
            borderColor: cfg.color,
            backgroundColor: "transparent",
            borderWidth: 1.8,
            borderDash: filters.param === "precip" ? [] : [4, 2],
            pointRadius: 0,
            pointHoverRadius: 4,
            fill: false,
            yAxisID: "y1",
            tension: 0.2
          }
        ]
      },
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
              font: { size: 11, weight: "bold" }
            }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                if (ctx.dataset.yAxisID === "y") {
                  return `Trips: ${ctx.parsed.y.toLocaleString()} journeys`;
                } else {
                  return `${cfg.short}: ${ctx.parsed.y} ${cfg.unit}`;
                }
              }
            }
          }
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 14,
              font: { size: 10 }
            },
            grid: { color: "#f8fafc" }
          },
          // Left Y-Axis: Trip volume
          y: {
            type: "linear",
            position: "left",
            title: {
              display: true,
              text: "Daily Departures (Trips)",
              color: "#0284c7",
              font: { size: 11, weight: "bold" }
            },
            grid: { color: "#f1f5f9" },
            beginAtZero: true
          },
          // Right Y-Axis: Weather parameter (separate scale)
          y1: {
            type: "linear",
            position: "right",
            title: {
              display: true,
              text: `${cfg.name} (${cfg.unit})`,
              color: cfg.color,
              font: { size: 11, weight: "bold" }
            },
            grid: { drawOnChartArea: false }, // Prevent overlapping grid lines
            beginAtZero: filters.param === "precip" || filters.param === "snow"
          }
        }
      }
    });
  }

  /**
   * Renders Precipitation Impact Breakdown comparing average daily volume across rainfall intensity tiers.
   */
  function renderRainImpactChart(records) {
    const canvas = document.getElementById("chart-weather-rain-bars");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (rainBarsChartInstance) {
      rainBarsChartInstance.destroy();
      rainBarsChartInstance = null;
    }

    const bins = [
      { label: "Dry (0.0 mm)", filter: (r) => r.precip === 0, color: "#10b981" },
      { label: "Trace (0.1–2.0 mm)", filter: (r) => r.precip > 0 && r.precip <= 2.0, color: "#38bdf8" },
      { label: "Moderate (2.1–10.0 mm)", filter: (r) => r.precip > 2.0 && r.precip <= 10.0, color: "#3b82f6" },
      { label: "Heavy (>10.0 mm)", filter: (r) => r.precip > 10.0, color: "#1d4ed8" }
    ];

    const binLabels = [];
    const binMeans = [];
    const binCounts = [];
    const bgColors = [];

    bins.forEach((b) => {
      const matching = records.filter(b.filter);
      const count = matching.length;
      const sum = matching.reduce((acc, r) => acc + r.dep, 0);
      const mean = count > 0 ? Math.round(sum / count) : 0;

      binLabels.push(`${b.label} [${count} d]`);
      binMeans.push(mean);
      binCounts.push(count);
      bgColors.push(b.color);
    });

    rainBarsChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: binLabels,
        datasets: [
          {
            label: "Mean Daily Departures (Trips / Day)",
            data: binMeans,
            backgroundColor: bgColors,
            borderColor: bgColors,
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function (ctx) {
                const count = binCounts[ctx.dataIndex];
                const pct = records.length > 0 ? ((count / records.length) * 100).toFixed(1) : 0;
                return `Frequency: ${count} days (${pct}% of period)`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 10, weight: "600" } }
          },
          y: {
            title: {
              display: true,
              text: "Average Daily Departures (Trips)",
              font: { size: 11, weight: "bold" }
            },
            grid: { color: "#f1f5f9" },
            beginAtZero: true
          }
        }
      }
    });
  }

  return {
    init: init,
    updateAllVisuals: updateAllVisuals
  };
})();
