/**
 * homeView.js - Handles the Home/Dashboard view logic for the rvc2api Web UI
 *
 * Responsibilities:
 * - Fetching and rendering API status, CAN status, and application health
 * - Handling quick light controls (all/interior/exterior on/off)
 * - Providing UI feedback (toasts, error messages)
 * - Modularizing dashboard widgets for maintainability
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

import { fetchData, callLightService } from "../api.js";
import { showToast } from "../utils.js";
import { apiBasePath } from "../config.js";
import { WebSocketManager } from "../wsManager.js";
import {
  API_STATUS_REFRESH_INTERVAL,
  APP_HEALTH_REFRESH_INTERVAL,
  CAN_STATUS_REFRESH_INTERVAL,
} from "../config.js";

const homeView = document.getElementById("home-view");
const apiStatusContent = document.getElementById("api-status-container");
const appHealthContent = document.getElementById("app-health-container");
const canStatusContent = document.getElementById("can-status-container");

// Quick Light Control Buttons
const quickLightButtons = [
  { id: "btn-all-on", name: "All Lights On", endpoint: "/lights/all/on" },
  { id: "btn-all-off", name: "All Lights Off", endpoint: "/lights/all/off" },
  {
    id: "btn-interior-on",
    name: "Interior Lights On",
    endpoint: "/lights/interior/on",
  },
  {
    id: "btn-interior-off",
    name: "Interior Lights Off",
    endpoint: "/lights/interior/off",
  },
  {
    id: "btn-exterior-on",
    name: "Exterior Lights On",
    endpoint: "/lights/exterior/on",
  },
  {
    id: "btn-exterior-off",
    name: "Exterior Lights Off",
    endpoint: "/lights/exterior/off",
  },
];

export function setupQuickLightControls() {
  quickLightButtons.forEach(({ id, name, endpoint }) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener("click", () => {
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML =
        '<i class="mdi mdi-loading mdi-spin mr-2"></i>Processing...';
      fetchData(`${apiBasePath}${endpoint}`, {
        method: "POST",
        successCallback: (data) => {
          showToast(
            `${name}: ${data.lights_commanded ?? "Commanded"}`,
            "success"
          );
        },
        errorCallback: (err) => {
          showToast(`Failed to execute ${name}: ${err.message}`, "error");
        },
        finallyCallback: () => {
          btn.disabled = false;
          btn.innerHTML = originalText;
        },
      });
    });
  });
}

export function fetchAndRenderApiStatus() {
  fetchData(`${apiBasePath}/status/server`, {
    successCallback: (data) => {
      if (!apiStatusContent) return;
      let statusSpan = apiStatusContent.querySelector(".api-status-value");
      let versionSpan = apiStatusContent.querySelector(".api-version-value");
      let messageDiv = apiStatusContent.querySelector(".api-status-message");
      if (!statusSpan || !versionSpan || !messageDiv) {
        apiStatusContent.innerHTML = `
          <div class="flex items-center space-x-2">
            <span class="font-semibold">Status:</span>
            <span class="api-status-value"></span>
            <span class="ml-4 font-semibold">Version:</span>
            <span class="api-version-value"></span>
          </div>
          <div class="mt-2 text-sm text-gray-400 api-status-message"></div>
        `;
        statusSpan = apiStatusContent.querySelector(".api-status-value");
        versionSpan = apiStatusContent.querySelector(".api-version-value");
        messageDiv = apiStatusContent.querySelector(".api-status-message");
      }
      statusSpan.textContent = data.status || "unknown";
      versionSpan.textContent = data.version || "";
      messageDiv.textContent = data.message || "";
    },
    errorCallback: (err) => {
      if (apiStatusContent)
        apiStatusContent.textContent = `Error loading API status: ${err.message}`;
    },
    loadingElement: apiStatusContent,
  });
}

export function fetchAndRenderAppHealth() {
  fetchData(`${apiBasePath}/status/application`, {
    successCallback: (data) => {
      if (!appHealthContent) return;
      appHealthContent.innerHTML = "";
      if (!data || typeof data !== "object") {
        appHealthContent.textContent = "No health data available.";
        return;
      }
      const entries = Object.entries(data).map(
        ([key, value]) =>
          `<div><span class="font-semibold">${key}:</span> <span>${value}</span></div>`
      );
      appHealthContent.innerHTML = entries.join("");
    },
    errorCallback: (err) => {
      if (appHealthContent)
        appHealthContent.textContent = `Error loading app health: ${err.message}`;
    },
    loadingElement: appHealthContent,
  });
}

export function fetchAndRenderCanStatus() {
  fetchData(`${apiBasePath}/can/status`, {
    successCallback: (data) => {
      if (!canStatusContent) return;
      if (
        !data ||
        !data.interfaces ||
        Object.keys(data.interfaces).length === 0
      ) {
        canStatusContent.textContent = "No CAN interfaces found.";
        return;
      }
      let table = canStatusContent.querySelector("table.can-status-table");
      if (!table) {
        table = document.createElement("table");
        table.className = "can-status-table themed-table";
        table.innerHTML = `
          <thead>
            <tr>
              <th>Interface</th>
              <th>State</th>
              <th>RX</th>
              <th>TX</th>
            </tr>
          </thead>
          <tbody></tbody>
        `;
        canStatusContent.innerHTML = "";
        canStatusContent.appendChild(table);
      }
      const tbody = table.querySelector("tbody");
      const interfaces = data.interfaces;
      Object.entries(interfaces).forEach(([iface, stats]) => {
        let row = tbody.querySelector(`tr[data-iface='${iface}']`);
        if (!row) {
          row = document.createElement("tr");
          row.dataset.iface = iface;
          row.innerHTML = `
            <td class="font-semibold">${iface}</td>
            <td class="can-state"></td>
            <td class="can-rx"></td>
            <td class="can-tx"></td>
          `;
          tbody.appendChild(row);
        }
        row.querySelector(".can-state").textContent = stats.state || "unknown";
        row.querySelector(".can-rx").textContent = stats.rx_packets || 0;
        row.querySelector(".can-tx").textContent = stats.tx_packets || 0;
      });
      Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
        if (!(row.dataset.iface in interfaces)) row.remove();
      });
    },
    errorCallback: (err) => {
      if (canStatusContent)
        canStatusContent.textContent = `Error loading CAN status: ${err.message}`;
    },
    loadingElement: canStatusContent,
  });
}

// =====================
// HOME VIEW POLLING (moved from app.js)
// =====================
let homePollingIntervals = [];
let statusWsManager = null;
let wsActive = false;

function handleStatusWsMessage(data) {
  try {
    const parsed = JSON.parse(data);
    if (parsed.server) renderApiStatus(parsed.server);
    if (parsed.application) renderAppHealth(parsed.application);
    if (parsed.can_status) renderCanStatus(parsed.can_status);
  } catch (e) {
    // fallback: ignore or show error
  }
}

function startStatusWebSocket() {
  if (statusWsManager) return;
  statusWsManager = new WebSocketManager(
    "/api/ws/status",
    handleStatusWsMessage,
    {
      onOpen: () => {
        wsActive = true;
        stopHomePolling();
      },
      onClose: () => {
        wsActive = false;
        statusWsManager = null;
        startHomePolling();
      },
      onError: () => {
        wsActive = false;
      },
      autoReconnect: true,
      reconnectInterval: 5000,
    }
  );
}

function stopStatusWebSocket() {
  if (statusWsManager) {
    statusWsManager.close();
    statusWsManager = null;
    wsActive = false;
  }
}

// Widget renderers for WebSocket
function renderApiStatus(data) {
  if (!apiStatusContent) return;
  let statusSpan = apiStatusContent.querySelector(".api-status-value");
  let versionSpan = apiStatusContent.querySelector(".api-version-value");
  let messageDiv = apiStatusContent.querySelector(".api-status-message");
  if (!statusSpan || !versionSpan || !messageDiv) {
    apiStatusContent.innerHTML = `
      <div class="flex items-center space-x-2">
        <span class="font-semibold">Status:</span>
        <span class="api-status-value"></span>
        <span class="ml-4 font-semibold">Version:</span>
        <span class="api-version-value"></span>
      </div>
      <div class="mt-2 text-sm text-gray-400 api-status-message"></div>
    `;
    statusSpan = apiStatusContent.querySelector(".api-status-value");
    versionSpan = apiStatusContent.querySelector(".api-version-value");
    messageDiv = apiStatusContent.querySelector(".api-status-message");
  }
  statusSpan.textContent = data.status || "unknown";
  versionSpan.textContent = data.version || "";
  messageDiv.textContent = data.message || "";
}

function renderAppHealth(data) {
  if (!appHealthContent) return;
  appHealthContent.innerHTML = "";
  if (!data || typeof data !== "object") {
    appHealthContent.textContent = "No health data available.";
    return;
  }
  const entries = Object.entries(data).map(
    ([key, value]) =>
      `<div><span class="font-semibold">${key}:</span> <span>${value}</span></div>`
  );
  appHealthContent.innerHTML = entries.join("");
}

function renderCanStatus(data) {
  if (!canStatusContent) return;
  if (!data || !data.interfaces || Object.keys(data.interfaces).length === 0) {
    canStatusContent.textContent = "No CAN interfaces found.";
    return;
  }
  let table = canStatusContent.querySelector("table.can-status-table");
  if (!table) {
    table = document.createElement("table");
    table.className = "can-status-table themed-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Interface</th>
          <th>State</th>
          <th>RX</th>
          <th>TX</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    canStatusContent.innerHTML = "";
    canStatusContent.appendChild(table);
  }
  const tbody = table.querySelector("tbody");
  const interfaces = data.interfaces;
  Object.entries(interfaces).forEach(([iface, stats]) => {
    let row = tbody.querySelector(`tr[data-iface='${iface}']`);
    if (!row) {
      row = document.createElement("tr");
      row.dataset.iface = iface;
      row.innerHTML = `
        <td class="font-semibold">${iface}</td>
        <td class="can-state"></td>
        <td class="can-rx"></td>
        <td class="can-tx"></td>
      `;
      tbody.appendChild(row);
    }
    row.querySelector(".can-state").textContent = stats.state || "unknown";
    row.querySelector(".can-rx").textContent = stats.rx_packets || 0;
    row.querySelector(".can-tx").textContent = stats.tx_packets || 0;
  });
  Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
    if (!(row.dataset.iface in interfaces)) row.remove();
  });
}

export function startHomePolling() {
  if (wsActive) return; // Don't poll if WebSocket is active
  stopHomePolling(); // Defensive: clear any existing intervals
  homePollingIntervals.push(
    setInterval(fetchAndRenderApiStatus, API_STATUS_REFRESH_INTERVAL),
    setInterval(fetchAndRenderAppHealth, APP_HEALTH_REFRESH_INTERVAL),
    setInterval(fetchAndRenderCanStatus, CAN_STATUS_REFRESH_INTERVAL)
  );
}

export function stopHomePolling() {
  homePollingIntervals.forEach((id) => clearInterval(id));
  homePollingIntervals = [];
}

export function renderHomeView() {
  fetchAndRenderApiStatus();
  fetchAndRenderAppHealth();
  fetchAndRenderCanStatus();
  setupQuickLightControls();
  startStatusWebSocket();
  if (!wsActive) startHomePolling();
}

export function cleanupHomeView() {
  stopHomePolling();
  stopStatusWebSocket && stopStatusWebSocket();
}
