/**
 * HSL City Bike Project - Main Application Controller (Phase 2)
 * Coordinates top navigation tabs, global error logging, and module initializations.
 */

document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  console.log("Initializing HSL City Bike Dashboard (Phase 2)...");

  // Tab Switching Logic
  const tabButtons = document.querySelectorAll(".nav-tabs .tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.dataset.tab;
      if (!targetTabId) return;

      // Update active tab buttons
      tabButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      // Update active tab pane
      tabPanes.forEach((pane) => {
        if (pane.id === targetTabId) {
          pane.classList.add("active");
        } else {
          pane.classList.remove("active");
        }
      });

      // If switching to station map tab, trigger Leaflet invalidation to ensure proper rendering
      if (targetTabId === "tab-station-map") {
        setTimeout(() => {
          if (window.mapInstance) {
            window.mapInstance.invalidateSize();
          }
        }, 100);
      }
    });
  });

  // Banner close button
  const alertClose = document.getElementById("alert-banner-close");
  const alertBanner = document.getElementById("alert-banner");
  if (alertClose && alertBanner) {
    alertClose.addEventListener("click", () => {
      alertBanner.style.display = "none";
    });
  }

  // Initialize Modules
  if (typeof MapModule !== "undefined") {
    MapModule.init();
  }
  if (typeof CommuteModule !== "undefined") {
    CommuteModule.init();
  }
  if (typeof WeatherModule !== "undefined") {
    WeatherModule.init();
  }
  if (typeof ForecastModule !== "undefined") {
    ForecastModule.init();
  }
});
