/**
 * HSL City Bike Project - Interactive Station Map Module (Phase 2)
 * Renders 454 mapped stations using Leaflet.js with zero-centered net flow colors,
 * interactive filtering (Year, Month, City, Metric), popups, search, and ranking table.
 * Preserves 7 unmapped stations in a dedicated audit drawer without fake coordinates.
 */

const MapModule = (function () {
  "use strict";

  // State Management
  let mapInstance = null;
  let markersLayer = null;
  let rawStationData = null; // Loaded from ./data/data_stations.json
  let activeMarkersMap = new Map(); // station_id -> L.circleMarker
  let currentFilteredList = [];
  let selectedStationId = null;

  // Filter State
  const filters = {
    year: "all",     // "all", "2024", "2025"
    month: "all",    // "all", "04", "05", ..., "10", "Q2", "Q3"
    city: "all",     // "all", "Helsinki", "Espoo"
    metric: "net_flow" // "net_flow", "departures", "returns", "total_trips"
  };

  // Table Sorting State
  const tableSort = {
    column: "metric", // "rank", "name", "city", "capacity", "departures", "returns", "net_flow"
    direction: "desc" // "asc" or "desc"
  };

  // Search Filter
  let searchQuery = "";

  /**
   * Initializes the Leaflet map and loads station data.
   */
  function init() {
    initLeaflet();
    bindEvents();
    loadStationData();
  }

  /**
   * Creates the Leaflet map centered on Helsinki & Espoo metropolitan region.
   */
  function initLeaflet() {
    // Default center on Helsinki-Espoo border (approx 60.18, 24.88)
    mapInstance = L.map("map-container", {
      center: [60.182, 24.890],
      zoom: 12,
      minZoom: 10,
      maxZoom: 18,
      zoomControl: true
    });

    // Standard OpenStreetMap tiles (free, public, no API key required)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(mapInstance);

    markersLayer = L.layerGroup().addTo(mapInstance);
  }

  /**
   * Binds UI control events (dropdowns, metric buttons, search, modal).
   */
  function bindEvents() {
    // Filter dropdowns
    const yearSelect = document.getElementById("filter-year");
    const monthSelect = document.getElementById("filter-month");
    const citySelect = document.getElementById("filter-city");
    const searchInput = document.getElementById("station-search");
    const btnResetView = document.getElementById("btn-reset-view");
    const btnExportCsv = document.getElementById("btn-export-csv");
    const btnUnmapped = document.getElementById("btn-unmapped-audit");
    const modalClose = document.getElementById("modal-close-btn");
    const modalBackdrop = document.getElementById("unmapped-modal");

    if (yearSelect) {
      yearSelect.addEventListener("change", (e) => {
        filters.year = e.target.value;
        applyFiltersAndRender();
      });
    }

    if (monthSelect) {
      monthSelect.addEventListener("change", (e) => {
        filters.month = e.target.value;
        applyFiltersAndRender();
      });
    }

    if (citySelect) {
      citySelect.addEventListener("change", (e) => {
        filters.city = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Metric selector buttons
    const metricButtons = document.querySelectorAll(".btn-metric");
    metricButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        metricButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        filters.metric = btn.dataset.metric;
        // Default sort by chosen metric
        tableSort.column = "metric";
        tableSort.direction = (filters.metric === "net_flow") ? "asc" : "desc";
        applyFiltersAndRender();
      });
    });

    // Search bar
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.trim().toLowerCase();
        renderTableAndMarkersVisibility();
      });
    }

    // Reset view
    if (btnResetView) {
      btnResetView.addEventListener("click", () => {
        mapInstance.setView([60.182, 24.890], 12);
      });
    }

    // Export CSV
    if (btnExportCsv) {
      btnExportCsv.addEventListener("click", exportCurrentTableCsv);
    }

    // Unmapped modal toggles
    if (btnUnmapped && modalBackdrop) {
      btnUnmapped.addEventListener("click", () => {
        modalBackdrop.classList.add("show");
      });
    }

    if (modalClose && modalBackdrop) {
      modalClose.addEventListener("click", () => {
        modalBackdrop.classList.remove("show");
      });
      modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) {
          modalBackdrop.classList.remove("show");
        }
      });
    }

    // Table header sort clicks
    const tableHeaders = document.querySelectorAll("#station-ranking-table th[data-sort]");
    tableHeaders.forEach((th) => {
      th.addEventListener("click", () => {
        const col = th.dataset.sort;
        if (tableSort.column === col) {
          tableSort.direction = (tableSort.direction === "asc") ? "desc" : "asc";
        } else {
          tableSort.column = col;
          tableSort.direction = (col === "name" || col === "city") ? "asc" : "desc";
        }
        updateSortHeaderClasses();
        renderTableOnly();
      });
    });
  }

  /**
   * Fetches data_stations.json using a strictly relative path.
   */
  function loadStationData() {
    showLoading(true);
    fetch("./data/data_stations.json")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data) => {
        rawStationData = data;
        showLoading(false);
        renderUnmappedModalContent(data.unmapped);
        applyFiltersAndRender();
      })
      .catch((err) => {
        showLoading(false);
        showErrorBanner(`Failed to load station data: ${err.message}. Please verify ./data/data_stations.json exists.`);
        console.error("MapModule loadStationData error:", err);
      });
  }

  /**
   * Computes the aggregated metrics (departures, returns, net_flow) for a station
   * according to the current Year and Month/Season filters.
   */
  function computeStationMetrics(station) {
    let dep = 0;
    let ret = 0;

    const targetYears = (filters.year === "all") ? ["2024", "2025"] : [filters.year];

    // Determine target months
    let targetMonths = [];
    if (filters.month === "all") {
      targetMonths = ["04", "05", "06", "07", "08", "09", "10"];
    } else if (filters.month === "Q2") {
      targetMonths = ["04", "05", "06"];
    } else if (filters.month === "Q3") {
      targetMonths = ["07", "08", "09"];
    } else {
      targetMonths = [filters.month];
    }

    // If viewing all season and all years, fast-path from totals
    if (filters.year === "all" && filters.month === "all") {
      dep = station.totals.all.dep;
      ret = station.totals.all.ret;
    } else if (filters.month === "all") {
      const yr = filters.year;
      if (station.totals[yr]) {
        dep = station.totals[yr].dep;
        ret = station.totals[yr].ret;
      }
    } else {
      // Sum across matching target year_months
      for (const y of targetYears) {
        for (const m of targetMonths) {
          const ym = `${y}-${m}`;
          if (station.months[ym]) {
            dep += station.months[ym][0];
            ret += station.months[ym][1];
          }
        }
      }
    }

    const net = ret - dep;
    const total = dep + ret;

    return {
      departures: dep,
      returns: ret,
      net_flow: net,
      total_trips: total
    };
  }

  /**
   * Filters stations, recalculates metrics, and updates map markers and table.
   */
  function applyFiltersAndRender() {
    if (!rawStationData || !rawStationData.stations) return;

    // Filter by city
    let list = rawStationData.stations;
    if (filters.city !== "all") {
      list = list.filter((s) => s.city.toLowerCase() === filters.city.toLowerCase());
    }

    // Compute metrics for each station
    currentFilteredList = list.map((s) => {
      const m = computeStationMetrics(s);
      return {
        id: s.id,
        name: s.name,
        city: s.city,
        lat: s.lat,
        lon: s.lon,
        capacity: s.cap,
        departures: m.departures,
        returns: m.returns,
        net_flow: m.net_flow,
        total_trips: m.total_trips
      };
    });

    updateSummaryKPIs(currentFilteredList);
    renderMapMarkers();
    renderTableOnly();
  }

  /**
   * Updates sidebar KPI counters based on filtered station aggregate metrics.
   */
  function updateSummaryKPIs(stations) {
    let totDep = 0;
    let totRet = 0;
    let totCap = 0;

    stations.forEach((s) => {
      totDep += s.departures;
      totRet += s.returns;
      if (s.capacity) totCap += s.capacity;
    });

    const netFlow = totRet - totDep;

    document.getElementById("kpi-active-stations").textContent = stations.length.toLocaleString();
    document.getElementById("kpi-total-departures").textContent = totDep.toLocaleString();
    document.getElementById("kpi-total-returns").textContent = totRet.toLocaleString();

    const kpiNet = document.getElementById("kpi-net-flow");
    kpiNet.textContent = (netFlow > 0 ? "+" : "") + netFlow.toLocaleString();
    kpiNet.className = "kpi-value " + (netFlow < 0 ? "val-deficit" : netFlow > 0 ? "val-surplus" : "");

    // Header badge
    document.getElementById("visible-station-count").textContent = `${stations.length} Active Stations`;
  }

  /**
   * Renders circle markers onto the Leaflet map with appropriate color encoding.
   */
  function renderMapMarkers() {
    markersLayer.clearLayers();
    activeMarkersMap.clear();

    if (currentFilteredList.length === 0) {
      updateMapLegend(0, 0);
      return;
    }

    // Calculate dynamic metric domain for color scaling
    const metricValues = currentFilteredList.map((s) => s[filters.metric]);
    let minVal = Math.min(...metricValues);
    let maxVal = Math.max(...metricValues);

    // For net_flow, ensure symmetric domain around 0
    if (filters.metric === "net_flow") {
      const absMax = Math.max(Math.abs(minVal), Math.abs(maxVal), 50);
      minVal = -absMax;
      maxVal = absMax;
    }

    // Maximum trip volume for radius scaling
    const maxVolume = Math.max(...currentFilteredList.map((s) => s.total_trips), 100);

    currentFilteredList.forEach((station) => {
      const val = station[filters.metric];
      const color = getMetricColor(val, minVal, maxVal, filters.metric);

      // Radius scaled with total trips between 5px and 15px
      const radius = 5 + Math.sqrt(station.total_trips / maxVolume) * 10;

      const marker = L.circleMarker([station.lat, station.lon], {
        radius: radius,
        fillColor: color,
        color: "#ffffff",
        weight: 1.5,
        opacity: 0.95,
        fillOpacity: 0.85
      });

      // Bind rich popup
      marker.bindPopup(buildPopupHtml(station));

      // Click listener
      marker.on("click", () => {
        selectStationRow(station.id);
      });

      markersLayer.addLayer(marker);
      activeMarkersMap.set(station.id, marker);
    });

    updateMapLegend(minVal, maxVal);
  }

  /**
   * Generates color for a given value based on metric type.
   * Uses a diverging color scale centered at 0 for net_flow.
   */
  function getMetricColor(val, minVal, maxVal, metricType) {
    if (metricType === "net_flow") {
      // Diverging scale: Negative = Red/Coral (Deficit), 0 = Grey, Positive = Teal/Blue (Surplus)
      if (val < 0) {
        // Ratio between 0 and 1
        const ratio = Math.min(Math.abs(val) / (Math.abs(minVal) || 1), 1.0);
        return interpolateColor("#adb5bd", "#d45c39", ratio);
      } else if (val > 0) {
        const ratio = Math.min(val / (maxVal || 1), 1.0);
        return interpolateColor("#adb5bd", "#2b5c8f", ratio);
      } else {
        return "#adb5bd";
      }
    } else {
      // Sequential scale (light to deep teal)
      const range = maxVal - minVal || 1;
      const ratio = Math.max(0, Math.min(1, (val - minVal) / range));
      return interpolateColor("#e0f2f1", "#004d40", ratio);
    }
  }

  /**
   * Simple linear RGB interpolation between two hex colors.
   */
  function interpolateColor(color1, color2, factor) {
    const c1 = hexToRgb(color1);
    const c2 = hexToRgb(color2);
    const r = Math.round(c1.r + factor * (c2.r - c1.r));
    const g = Math.round(c1.g + factor * (c2.g - c1.g));
    const b = Math.round(c1.b + factor * (c2.b - c1.b));
    return `rgb(${r}, ${g}, ${b})`;
  }

  function hexToRgb(hex) {
    let clean = hex.replace("#", "");
    if (clean.length === 3) {
      clean = clean.split("").map(c => c + c).join("");
    }
    const num = parseInt(clean, 16);
    return {
      r: (num >> 16) & 255,
      g: (num >> 8) & 255,
      b: num & 255
    };
  }

  /**
   * Constructs the HTML popup for a clicked station.
   */
  function buildPopupHtml(station) {
    const cityClass = station.city.toLowerCase() === "helsinki" ? "badge-city-helsinki" : "badge-city-espoo";
    const netClass = station.net_flow < 0 ? "val-deficit" : station.net_flow > 0 ? "val-surplus" : "";
    const netPrefix = station.net_flow > 0 ? "+" : "";

    return `
      <div class="popup-station-card">
        <div class="popup-station-header">
          <div class="popup-station-name">${escapeHtml(station.name)}</div>
          <div class="popup-station-sub">
            <span class="badge-city ${cityClass}">${station.city}</span>
            <span>ID #${station.id}</span>
            <span>· ${station.capacity || "N/A"} Docks</span>
          </div>
        </div>
        <div class="popup-metrics-grid">
          <div class="popup-metric-item">
            <div class="popup-metric-label">Departures</div>
            <div class="popup-metric-val">${station.departures.toLocaleString()}</div>
          </div>
          <div class="popup-metric-item">
            <div class="popup-metric-label">Returns</div>
            <div class="popup-metric-val">${station.returns.toLocaleString()}</div>
          </div>
          <div class="popup-metric-item" style="grid-column: span 2;">
            <div class="popup-metric-label">Net Flow (Returns - Departures)</div>
            <div class="popup-metric-val ${netClass}">${netPrefix}${station.net_flow.toLocaleString()} trips</div>
          </div>
        </div>
        <div style="font-size: 0.68rem; color: #64748b; line-height: 1.2;">
          *Macro passenger flow drift; not physical dock inventory.
        </div>
      </div>
    `;
  }

  /**
   * Updates map legend based on active metric and value range.
   */
  function updateMapLegend(minVal, maxVal) {
    let legendContainer = document.getElementById("map-legend-control");
    if (!legendContainer) {
      legendContainer = L.DomUtil.create("div", "map-legend", mapInstance.getContainer());
      legendContainer.id = "map-legend-control";
      L.DomEvent.disableClickPropagation(legendContainer);
      L.DomEvent.disableScrollPropagation(legendContainer);
      const legendCorner = mapInstance._controlCorners.bottomright;
      legendCorner.appendChild(legendContainer);
    }

    if (filters.metric === "net_flow") {
      const absVal = Math.round(Math.max(Math.abs(minVal), Math.abs(maxVal)));
      legendContainer.innerHTML = `
        <div class="legend-title">Net Flow (Returns - Departures)</div>
        <div class="legend-bar" style="background: linear-gradient(to right, #d45c39 0%, #adb5bd 50%, #2b5c8f 100%);"></div>
        <div class="legend-labels">
          <span style="color: #d45c39; font-weight:700;">-${absVal.toLocaleString()} (Deficit)</span>
          <span>0 (Balanced)</span>
          <span style="color: #2b5c8f; font-weight:700;">+${absVal.toLocaleString()} (Surplus)</span>
        </div>
        <div class="legend-note">
          *Net flow measures 30-day directional passenger drift, NOT real-time dock stock or required truck rebalancing volume.
        </div>
      `;
    } else {
      const metricLabel = filters.metric.replace("_", " ").toUpperCase();
      legendContainer.innerHTML = `
        <div class="legend-title">${metricLabel}</div>
        <div class="legend-bar" style="background: linear-gradient(to right, #e0f2f1 0%, #004d40 100%);"></div>
        <div class="legend-labels">
          <span>${Math.round(minVal).toLocaleString()}</span>
          <span>${Math.round(maxVal).toLocaleString()} trips</span>
        </div>
        <div class="legend-note">
          *Radius scales dynamically with total trip volume.
        </div>
      `;
    }
  }

  /**
   * Renders the station ranking table according to search query and sort column.
   */
  function renderTableOnly() {
    const tbody = document.getElementById("station-table-body");
    const emptyState = document.getElementById("table-empty-state");
    if (!tbody) return;

    let displayList = currentFilteredList;

    // Apply text search
    if (searchQuery) {
      displayList = displayList.filter((s) => {
        return (
          s.name.toLowerCase().includes(searchQuery) ||
          s.id.toString().includes(searchQuery) ||
          s.city.toLowerCase().includes(searchQuery)
        );
      });
    }

    if (displayList.length === 0) {
      tbody.innerHTML = "";
      if (emptyState) emptyState.style.display = "block";
      return;
    } else {
      if (emptyState) emptyState.style.display = "none";
    }

    // Sort display list
    displayList.sort((a, b) => {
      let vA, vB;
      switch (tableSort.column) {
        case "name":
          vA = a.name.toLowerCase();
          vB = b.name.toLowerCase();
          return (tableSort.direction === "asc") ? vA.localeCompare(vB) : vB.localeCompare(vA);
        case "city":
          vA = a.city.toLowerCase();
          vB = b.city.toLowerCase();
          return (tableSort.direction === "asc") ? vA.localeCompare(vB) : vB.localeCompare(vA);
        case "capacity":
          vA = a.capacity || 0;
          vB = b.capacity || 0;
          break;
        case "departures":
          vA = a.departures;
          vB = b.departures;
          break;
        case "returns":
          vA = a.returns;
          vB = b.returns;
          break;
        case "net_flow":
          vA = a.net_flow;
          vB = b.net_flow;
          break;
        case "metric":
        default:
          vA = a[filters.metric];
          vB = b[filters.metric];
          break;
      }
      return (tableSort.direction === "asc") ? (vA - vB) : (vB - vA);
    });

    // Build rows
    const rowsHtml = displayList.map((s, idx) => {
      const cityClass = s.city.toLowerCase() === "helsinki" ? "badge-city-helsinki" : "badge-city-espoo";
      const netClass = s.net_flow < 0 ? "val-deficit" : s.net_flow > 0 ? "val-surplus" : "";
      const netPrefix = s.net_flow > 0 ? "+" : "";
      const isSelected = (s.id === selectedStationId) ? "selected-row" : "";

      return `
        <tr class="${isSelected}" data-station-id="${s.id}">
          <td class="text-center" style="color: #64748b; font-weight:600;">#${idx + 1}</td>
          <td style="font-weight:600; color: #12313a;">${escapeHtml(s.name)}</td>
          <td><span class="badge-city ${cityClass}">${s.city}</span></td>
          <td class="text-right">${s.capacity || "—"}</td>
          <td class="text-right">${s.departures.toLocaleString()}</td>
          <td class="text-right">${s.returns.toLocaleString()}</td>
          <td class="text-right ${netClass}" style="font-weight:700;">${netPrefix}${s.net_flow.toLocaleString()}</td>
        </tr>
      `;
    }).join("");

    tbody.innerHTML = rowsHtml;

    // Attach row click listeners to highlight marker and pan map
    tbody.querySelectorAll("tr").forEach((tr) => {
      tr.addEventListener("click", () => {
        const sid = parseInt(tr.dataset.stationId, 10);
        focusStationOnMap(sid);
      });
    });
  }

  /**
   * Centers the map on the given station, highlights it, and triggers its popup.
   */
  function focusStationOnMap(stationId) {
    selectedStationId = stationId;
    selectStationRow(stationId);

    const marker = activeMarkersMap.get(stationId);
    if (marker) {
      const latlng = marker.getLatLng();
      mapInstance.setView(latlng, Math.max(mapInstance.getZoom(), 14), { animate: true });
      marker.openPopup();
    }
  }

  /**
   * Selects and highlights a table row by station id.
   */
  function selectStationRow(stationId) {
    selectedStationId = stationId;
    const tbody = document.getElementById("station-table-body");
    if (!tbody) return;

    tbody.querySelectorAll("tr").forEach((tr) => {
      if (parseInt(tr.dataset.stationId, 10) === stationId) {
        tr.classList.add("selected-row");
        tr.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else {
        tr.classList.remove("selected-row");
      }
    });
  }

  /**
   * Updates table sort arrow headers.
   */
  function updateSortHeaderClasses() {
    const tableHeaders = document.querySelectorAll("#station-ranking-table th[data-sort]");
    tableHeaders.forEach((th) => {
      th.classList.remove("sort-asc", "sort-desc");
      if (th.dataset.sort === tableSort.column) {
        th.classList.add(tableSort.direction === "asc" ? "sort-asc" : "sort-desc");
      }
    });
  }

  /**
   * Filters map markers visibility according to search query.
   */
  function renderTableAndMarkersVisibility() {
    renderTableOnly();

    if (!searchQuery) {
      activeMarkersMap.forEach((m) => m.setStyle({ opacity: 0.95, fillOpacity: 0.85 }));
      return;
    }

    activeMarkersMap.forEach((marker, sid) => {
      const s = currentFilteredList.find(item => item.id === sid);
      if (s) {
        const matches = (
          s.name.toLowerCase().includes(searchQuery) ||
          s.id.toString().includes(searchQuery) ||
          s.city.toLowerCase().includes(searchQuery)
        );
        if (matches) {
          marker.setStyle({ opacity: 1.0, fillOpacity: 0.95 });
        } else {
          marker.setStyle({ opacity: 0.15, fillOpacity: 0.1 });
        }
      }
    });
  }

  /**
   * Populates the Unmapped Stations Audit Modal.
   */
  function renderUnmappedModalContent(unmappedList) {
    const tbody = document.getElementById("unmapped-table-body");
    if (!tbody || !unmappedList) return;

    const rowsHtml = unmappedList.map((u) => {
      const totalDep = u.totals.all.dep.toLocaleString();
      const totalRet = u.totals.all.ret.toLocaleString();
      const net = u.totals.all.net;
      const netStr = (net > 0 ? "+" : "") + net.toLocaleString();

      return `
        <tr>
          <td style="font-weight:700;">#${u.id}</td>
          <td>${escapeHtml(u.name)}</td>
          <td>${u.city}</td>
          <td class="text-right">${totalDep}</td>
          <td class="text-right">${totalRet}</td>
          <td class="text-right" style="font-weight:700;">${netStr}</td>
          <td style="font-size:0.75rem; color:#64748b;">${escapeHtml(u.audit_note)}</td>
        </tr>
      `;
    }).join("");

    tbody.innerHTML = rowsHtml;
  }

  /**
   * Exports the currently displayed table rows as a CSV file.
   */
  function exportCurrentTableCsv() {
    if (!currentFilteredList || currentFilteredList.length === 0) {
      alert("No data available to export.");
      return;
    }

    let csvContent = "Station_ID,Station_Name,City,Capacity,Departures,Returns,Net_Flow,Total_Trips\n";
    currentFilteredList.forEach((s) => {
      const nameEscaped = `"${s.name.replace(/"/g, '""')}"`;
      csvContent += `${s.id},${nameEscaped},${s.city},${s.capacity || ""},${s.departures},${s.returns},${s.net_flow},${s.total_trips}\n`;
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const filename = `hsl_station_ranking_${filters.year}_${filters.month}_${filters.metric}.csv`;
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function showLoading(show) {
    const overlay = document.getElementById("map-loading-overlay");
    if (overlay) overlay.style.display = show ? "flex" : "none";
  }

  function showErrorBanner(msg) {
    const banner = document.getElementById("error-banner");
    if (banner) {
      banner.textContent = msg;
      banner.style.display = "block";
    }
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
    applyFiltersAndRender: applyFiltersAndRender
  };
})();
