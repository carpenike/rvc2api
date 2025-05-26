/**
 * @file canSnifferView.js
 * @module canSnifferView
 * @description
 *   Modularized CAN Sniffer view logic for the rvc2api Web UI frontend.
 *   Handles all UI, WebSocket, and rendering logic for the CAN Sniffer view.
 *   - Connects to the /api/ws/can-sniffer WebSocket endpoint for real-time updates
 *   - Renders command/response groupings in the CAN sniffer table
 *   - Provides cleanup and initialization for navigation
 *   - Exports renderCanSnifferView and cleanupCanSnifferView for use by app.js
 *
 *   This file should not contain any global app state or navigation logic.
 *   All DOM queries are scoped to the CAN Sniffer view elements.
 *
 *   Usage:
 *     import { renderCanSnifferView, cleanupCanSnifferView } from './views/canSnifferView.js';
 *     // Call renderCanSnifferView() when entering the view, cleanupCanSnifferView() when leaving.
 */

// canSnifferView.js - Modularized CAN Sniffer view logic for rvc2api Web UI
// Handles WebSocket connection, table rendering, and cleanup for CAN Sniffer

import { WebSocketManager } from "../wsManager.js";
import { showToast } from "../utils.js";
import { fetchData } from "../api.js";

let canSnifferSocketManager = null;

// Add a toggle for sniffer mode
let snifferMode = "all"; // "all" or "control"

function renderSnifferModeToggle() {
  const container = document.getElementById("can-sniffer-toggle-container");
  if (!container) return;
  container.innerHTML = `
    <div class="sniffer-toggle flex gap-2 mb-2">
      <button id="sniffer-mode-all" type="button" class="themed-table-btn${
        snifferMode === "all" ? " active" : ""
      }">All CAN Messages</button>
      <button id="sniffer-mode-control" type="button" class="themed-table-btn${
        snifferMode === "control" ? " active" : ""
      }">Command/Control Grouped</button>
    </div>
  `;
  document.getElementById("sniffer-mode-all").onclick = () => {
    snifferMode = "all";
    renderCanSnifferView();
  };
  document.getElementById("sniffer-mode-control").onclick = () => {
    snifferMode = "control";
    renderCanSnifferView();
  };
}

function clearCanSnifferTable() {
  const canSnifferTable = document.getElementById("can-sniffer-table");
  if (canSnifferTable) {
    const tbody = canSnifferTable.querySelector("tbody");
    if (tbody) tbody.innerHTML = "";
  }
}

// Helper: Pretty-print JSON with syntax highlighting and theme support
function prettyPrintJSON(obj) {
  if (!obj) return "";
  let jsonString = "";
  try {
    jsonString = JSON.stringify(obj, null, 2);
  } catch (e) {
    return String(obj);
  }
  // Wrap in <pre> and add a class for theming
  return `<pre class="themed-json pretty-json">${escapeHTML(jsonString)}</pre>`;
}

// Helper: Escape HTML for safe rendering
function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Track expanded rows by a unique key (timestamp+dir+arb id)
const expandedRows = new Set();

function makeExpandButton(rowKey) {
  const btn = document.createElement("button");
  btn.className = "expand-json-btn themed-table-btn";
  btn.title = "Show full decoded JSON";
  btn.innerHTML = '<span class="mdi mdi-chevron-down"></span>';
  btn.setAttribute("aria-expanded", expandedRows.has(rowKey));
  btn.onclick = function (e) {
    e.stopPropagation();
    toggleExpandRow(rowKey, btn);
  };
  return btn;
}

function toggleExpandRow(rowKey, btn) {
  const tr = document.getElementById(rowKey);
  if (!tr) return;
  const expanded = expandedRows.has(rowKey);
  if (expanded) {
    // Collapse: remove next sibling if it's an expanded row
    const next = tr.nextSibling;
    if (next && next.classList.contains("expanded-json-row")) {
      next.remove();
    }
    expandedRows.delete(rowKey);
    btn.setAttribute("aria-expanded", false);
    btn.innerHTML = '<span class="mdi mdi-chevron-down"></span>';
  } else {
    // Expand: insert a new row below
    const decodedData = tr.getAttribute("data-decoded-json");
    const colCount = tr.children.length;
    const expandedTr = document.createElement("tr");
    expandedTr.className = "expanded-json-row themed-table-expanded";
    const td = document.createElement("td");
    td.colSpan = colCount;
    td.innerHTML = decodedData;
    expandedTr.appendChild(td);
    tr.parentNode.insertBefore(expandedTr, tr.nextSibling);
    expandedRows.add(rowKey);
    btn.setAttribute("aria-expanded", true);
    btn.innerHTML = '<span class="mdi mdi-chevron-up"></span>';
  }
}

function addCanSnifferGroupRow(group) {
  const canSnifferTable = document.getElementById("can-sniffer-table");
  if (!canSnifferTable) return;
  const tbody = canSnifferTable.querySelector("tbody");
  if (!tbody) return;
  const { command, response, confidence } = group;
  let rowClass = "";
  let icon = "";
  if (confidence === "high") {
    rowClass = "themed-table-note";
    icon =
      '<span title="Mapped grouping" class="mdi mdi-link-variant themed-table-note mr-1"></span>';
  } else if (confidence === "low") {
    rowClass = "themed-table-muted";
    icon =
      '<span title="Heuristic grouping" class="mdi mdi-help-circle-outline themed-table-muted mr-1"></span>';
  }
  // Helper to build a row (TX or RX)
  function buildRow(entry, dir) {
    const rowKey = `${entry.timestamp}_${dir}_${entry.arbitration_id}`;
    const tr = document.createElement("tr");
    tr.className = rowClass;
    tr.id = rowKey;
    // Store pretty JSON as attribute for expansion
    tr.setAttribute("data-decoded-json", prettyPrintJSON(entry.decoded));
    tr.innerHTML = `
      <td class="px-2 py-1 font-mono">${new Date(
        entry.timestamp * 1000
      ).toLocaleTimeString()}</td>
      <td class="px-2 py-1">${dir}</td>
      <td class="px-2 py-1 font-mono">${entry.pgn || ""}</td>
      <td class="px-2 py-1 font-mono">${entry.dgn_hex || ""}</td>
      <td class="px-2 py-1">${icon}${entry.name || ""}</td>
      <td class="px-2 py-1 font-mono">$${
        entry.arbitration_id
          ? "0x" + entry.arbitration_id.toString(16).toUpperCase()
          : ""
      }</td>
      <td class="px-2 py-1 font-mono">${entry.data || ""}</td>
      <td class="px-2 py-1 font-mono">${
        entry.decoded ? `<span class="json-summary">{...}</span>` : ""
      }</td>
    `;
    // Add expand button if decoded JSON exists
    if (entry.decoded) {
      const btn = makeExpandButton(rowKey);
      const td = tr.querySelector("td:last-child");
      td.insertBefore(btn, td.firstChild);
    }
    return tr;
  }
  // Command row
  const trCmd = buildRow(command, "TX");
  tbody.appendChild(trCmd);
  // Response row
  const trResp = buildRow(response, "RX");
  tbody.appendChild(trResp);
}

function addCanSnifferRow(entry) {
  const canSnifferTable = document.getElementById("can-sniffer-table");
  if (!canSnifferTable) return;
  const tbody = canSnifferTable.querySelector("tbody");
  if (!tbody) return;
  const dir = entry.direction ? entry.direction.toUpperCase() : "";
  const rowKey = `${entry.timestamp}_${dir}_${entry.arbitration_id}`;
  const tr = document.createElement("tr");
  tr.className = "";
  tr.id = rowKey;
  tr.setAttribute("data-decoded-json", prettyPrintJSON(entry.decoded));
  tr.innerHTML = `
    <td class="px-2 py-1 font-mono">${new Date(
      entry.timestamp * 1000
    ).toLocaleTimeString()}</td>
    <td class="px-2 py-1">${dir}</td>
    <td class="px-2 py-1 font-mono">${entry.pgn || ""}</td>
    <td class="px-2 py-1 font-mono">${entry.dgn_hex || ""}</td>
    <td class="px-2 py-1">${entry.name || ""}</td>
    <td class="px-2 py-1 font-mono">${
      entry.arbitration_id
        ? "0x" + entry.arbitration_id.toString(16).toUpperCase()
        : ""
    }</td>
    <td class="px-2 py-1 font-mono">${entry.data || ""}</td>
    <td class="px-2 py-1 font-mono">${
      entry.decoded ? `<span class="json-summary">{...}</span>` : ""
    }</td>
  `;
  if (entry.decoded) {
    const btn = makeExpandButton(rowKey);
    const td = tr.querySelector("td:last-child");
    td.insertBefore(btn, td.firstChild);
  }
  tbody.appendChild(tr);
}

function connectCanSnifferSocket() {
  if (!canSnifferSocketManager) {
    canSnifferSocketManager = new WebSocketManager(
      "/api/ws/can-sniffer",
      (eventData) => {
        const group = JSON.parse(eventData);
        addCanSnifferGroupRow(group);
      },
      {
        onOpen: () => {
          clearCanSnifferTable();
          const canSnifferLoading = document.getElementById(
            "can-sniffer-loading-message"
          );
          if (canSnifferLoading) canSnifferLoading.classList.add("hidden");
        },
        onClose: () => {},
        onError: () => {},
        autoReconnect: true,
        reconnectInterval: 5000,
      }
    );
  }
}

function disconnectCanSnifferSocket() {
  if (canSnifferSocketManager) {
    canSnifferSocketManager.close();
    canSnifferSocketManager = null;
  }
}

function fetchCanSnifferAll() {
  const canSnifferLoading = document.getElementById(
    "can-sniffer-loading-message"
  );
  const canSnifferTable = document.getElementById("can-sniffer-table");
  if (!canSnifferTable) return;
  const tbody = canSnifferTable.querySelector("tbody");
  if (tbody) tbody.innerHTML = "";
  fetchData("/api/can-sniffer", {
    successCallback: (data) => {
      if (canSnifferLoading) canSnifferLoading.classList.add("hidden");
      if (!Array.isArray(data) || data.length === 0) {
        if (tbody) tbody.innerHTML = "";
        return;
      }
      data
        .slice()
        .reverse()
        .forEach((entry) => {
          addCanSnifferRow(entry);
        });
    },
    errorCallback: (error) => {
      if (canSnifferLoading) canSnifferLoading.classList.add("hidden");
      showToast("Failed to load CAN sniffer log.", "error");
    },
    loadingElement: canSnifferLoading,
  });
}

function fetchCanSnifferControl() {
  const canSnifferLoading = document.getElementById(
    "can-sniffer-loading-message"
  );
  const canSnifferTable = document.getElementById("can-sniffer-table");
  if (!canSnifferTable) return;
  const tbody = canSnifferTable.querySelector("tbody");
  if (tbody) tbody.innerHTML = "";
  fetchData("/api/can-sniffer-control", {
    successCallback: (data) => {
      if (canSnifferLoading) canSnifferLoading.classList.add("hidden");
      if (!Array.isArray(data) || data.length === 0) {
        if (tbody) tbody.innerHTML = "";
        return;
      }
      data
        .slice()
        .reverse()
        .forEach((group) => {
          addCanSnifferGroupRow(group);
        });
    },
    errorCallback: (error) => {
      if (canSnifferLoading) canSnifferLoading.classList.add("hidden");
      showToast("Failed to load CAN sniffer log.", "error");
    },
    loadingElement: canSnifferLoading,
  });
}

export function renderCanSnifferView() {
  clearCanSnifferTable();
  renderSnifferModeToggle();
  if (snifferMode === "all") {
    fetchCanSnifferAll();
  } else {
    fetchCanSnifferControl();
  }
}

export function cleanupCanSnifferView() {
  disconnectCanSnifferSocket();
  clearCanSnifferTable();
}

export {
  connectCanSnifferSocket,
  disconnectCanSnifferSocket,
  clearCanSnifferTable,
  addCanSnifferGroupRow,
};
