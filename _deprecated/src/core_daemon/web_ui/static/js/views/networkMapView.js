/**
 * networkMapView.js - Displays a network map of observed CAN source addresses and basic info.
 *
 * - Fetches observed source addresses from the backend
 * - Renders a table or grid of all observed source addresses
 * - Optionally shows which address is 'self' (our node)
 * - Can be extended to show more info (device names, traffic counts, etc.)
 */
import { fetchData } from "../api.js";
import { showToast } from "../utils.js";
import { WebSocketManager } from "../wsManager.js";

let networkMapSocketManager = null;
let networkMapData = {};

// Track expanded rows for decoded/raw by address value and type
const expandedNetworkMapRows = new Set();

// DGNs to track for scan responses
const SCAN_DGNS = [0xee00, 0xfefa, 0xfefc];

// Map: addr.value -> { dgns: { [dgn]: { received: true, iface: string, decoded: object } }, ...other addr fields }
let scanStatusByAddr = {};

function prettyPrintJSON(obj) {
  if (!obj) return "";
  let jsonString = "";
  try {
    jsonString = JSON.stringify(obj, null, 2);
  } catch (e) {
    return String(obj);
  }
  return `<pre class="themed-json pretty-json">${escapeHTML(jsonString)}</pre>`;
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</ / g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function makeExpandButton(rowKey, type) {
  const btn = document.createElement("button");
  btn.className = "expand-json-btn themed-table-btn";
  btn.title = `Show full ${type} JSON`;
  btn.innerHTML = '<span class="mdi mdi-chevron-down"></span>';
  btn.setAttribute(
    "aria-expanded",
    expandedNetworkMapRows.has(`${rowKey}_${type}`)
  );
  btn.onclick = function (e) {
    e.stopPropagation();
    toggleExpandRow(rowKey, btn, type);
  };
  return btn;
}

function toggleExpandRow(rowKey, btn, type) {
  const tr = document.getElementById(rowKey);
  if (!tr) return;
  const expandedKey = `${rowKey}_${type}`;
  const expanded = expandedNetworkMapRows.has(expandedKey);
  if (expanded) {
    const next = tr.nextSibling;
    if (next && next.classList.contains("expanded-json-row")) {
      next.remove();
    }
    expandedNetworkMapRows.delete(expandedKey);
    btn.setAttribute("aria-expanded", false);
    btn.innerHTML = '<span class="mdi mdi-chevron-down"></span>';
  } else {
    const jsonData = tr.getAttribute(`data-${type}-json`);
    const colCount = tr.children.length;
    const expandedTr = document.createElement("tr");
    expandedTr.className = "expanded-json-row themed-table-expanded";
    const td = document.createElement("td");
    td.colSpan = colCount;
    td.innerHTML = jsonData;
    expandedTr.appendChild(td);
    tr.parentNode.insertBefore(expandedTr, tr.nextSibling);
    expandedNetworkMapRows.add(expandedKey);
    btn.setAttribute("aria-expanded", true);
    btn.innerHTML = '<span class="mdi mdi-chevron-up"></span>';
  }
}

function connectNetworkMapSocket() {
  if (!networkMapSocketManager) {
    networkMapSocketManager = new WebSocketManager(
      "/api/ws/network-map",
      (eventData) => {
        const data = JSON.parse(eventData);
        updateNetworkMapTable(data);
      },
      {
        onOpen: () => {
          document
            .getElementById("network-map-loading")
            ?.classList.add("hidden");
        },
        onClose: () => {},
        onError: () => {},
        autoReconnect: true,
        reconnectInterval: 5000,
      }
    );
  }
}

function disconnectNetworkMapSocket() {
  if (networkMapSocketManager) {
    networkMapSocketManager.close();
    networkMapSocketManager = null;
  }
}

function updateNetworkMapTable(data) {
  const tbody = document.getElementById("network-map-table-body");
  if (!tbody) return;
  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="13" class="text-center themed-table-muted">No addresses observed yet.</td></tr>';
    networkMapData = {};
    scanStatusByAddr = {};
    return;
  }
  tbody.innerHTML = "";
  networkMapData = {};
  data.forEach((addr) => {
    networkMapData[addr.value] = addr;
    const isSelf = addr.is_self;
    const rowKey = `networkmap_${addr.value}`;
    const tr = document.createElement("tr");
    if (isSelf) tr.className = "themed-table-note";
    tr.id = rowKey;
    // Store pretty JSON as attribute for expansion
    tr.setAttribute("data-decoded-json", prettyPrintJSON(addr.decoded));
    tr.setAttribute("data-raw-json", prettyPrintJSON(addr.raw));
    // DGN status summary cell
    let dgnSummary = "";
    if (scanStatusByAddr[addr.value]) {
      dgnSummary = SCAN_DGNS.map((dgn) => {
        const dgnHex = dgn.toString(16).toUpperCase();
        const status = scanStatusByAddr[addr.value].dgns?.[dgnHex];
        if (status) {
          return `<span title="DGN 0x${dgnHex} via ${status.iface}" style="color:green;">&#x2714;</span>`;
        } else {
          return `<span title="DGN 0x${dgnHex} missing" style="color:gray;">&#x2718;</span>`;
        }
      }).join(" ");
    }
    tr.innerHTML = `
      <td class="font-mono">${addr.value}</td>
      <td class="font-mono">0x${Number(addr.value)
        .toString(16)
        .toUpperCase()}</td>
      <td class="font-mono">${addr.dgn || ""}</td>
      <td class="font-mono">${addr.instance || ""}</td>
      <td>${addr.device_type || ""}</td>
      <td>${addr.friendly_name || ""}</td>
      <td>${addr.area || ""}</td>
      <td>${addr.notes || ""}</td>
      <td>${addr.decoded ? `<span class='json-summary'>{...}</span>` : ""}</td>
      <td>${addr.raw ? `<span class='json-summary'>{...}</span>` : ""}</td>
      <td>${dgnSummary}</td>
    `;
    // Add expand buttons if decoded/raw exist
    if (addr.decoded) {
      const btn = makeExpandButton(rowKey, "decoded");
      const td = tr.querySelector("td:nth-child(9)");
      td.insertBefore(btn, td.firstChild);
    }
    if (addr.raw) {
      const btn = makeExpandButton(rowKey, "raw");
      const td = tr.querySelector("td:nth-child(10)");
      td.insertBefore(btn, td.firstChild);
    }
    tbody.appendChild(tr);
  });
}

export function renderNetworkMapView() {
  const view = document.getElementById("network-map-view");
  if (!view) return;
  // DGN labels for table header
  const DGN_LABELS = {
    EE00: "Address Claimed",
    FEFA: "Product ID",
    FEFC: "Software Version",
  };
  // New table for DGN responses per address
  view.innerHTML = `<h1 class="text-3xl font-bold mb-6">CAN Network Map (DGN Responses)</h1>
    <div class="mb-4 flex items-center gap-4">
      <p class="themed-table-muted flex-1">For each source address, see the decoded response to each scanned DGN.</p>
      <button id="btn-canbus-scan" class="themed-table-btn bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded shadow flex items-center gap-2">
        <i class="mdi mdi-radar" aria-hidden="true"></i>Scan CANbus
      </button>
    </div>
    <div id="network-map-loading" class="mb-4">Loading network map...</div>
    <table class="themed-table">
      <thead><tr><th>Source Address</th><th>DGN 0xEE00<br><span class='text-xs themed-table-muted'>${DGN_LABELS.EE00}</span></th><th>DGN 0xFEFA<br><span class='text-xs themed-table-muted'>${DGN_LABELS.FEFA}</span></th><th>DGN 0xFEFC<br><span class='text-xs themed-table-muted'>${DGN_LABELS.FEFC}</span></th></tr></thead>
      <tbody id="network-map-table-body"></tbody>
    </table>`;
  // Fetch initial data via HTTP (not used for this table, but keep for scan button)
  fetchData("/api/network-map", {
    successCallback: () => {
      document.getElementById("network-map-loading")?.classList.add("hidden");
    },
    errorCallback: () => {
      document.getElementById("network-map-loading").textContent =
        "Failed to load network map.";
    },
  });
  // Add CANbus Scan button handler
  const scanBtn = document.getElementById("btn-canbus-scan");
  if (scanBtn) {
    scanBtn.onclick = () => {
      fetchData("/api/canbus-scan", {
        method: "POST",
        successCallback: () =>
          showToast(
            "CANbus scan started. Results will appear below as devices respond."
          ),
        errorCallback: () => showToast("Failed to start CANbus scan.", "error"),
      });
    };
  }
  // Render table rows as scan results come in
  function renderDgnTable() {
    const tbody = document.getElementById("network-map-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";
    // Get all addresses seen in scanStatusByAddr
    const addresses = Object.keys(scanStatusByAddr).sort(
      (a, b) => Number(a) - Number(b)
    );
    addresses.forEach((addr) => {
      const dgns = scanStatusByAddr[addr].dgns || {};
      const tr = document.createElement("tr");
      tr.id = `networkmap_${addr}`;
      // Helper to render a cell for a DGN
      function dgnCell(dgnHex) {
        const dgnInfo = dgns[dgnHex];
        if (dgnInfo && dgnInfo.decoded) {
          const cellId = `cell_${addr}_${dgnHex}`;
          // Try to get friendly name from decoded JSON (common keys: friendly_name, name, product_name, etc.)
          let friendly = "";
          const decoded = dgnInfo.decoded;
          if (decoded.friendly_name) friendly = decoded.friendly_name;
          else if (decoded.name) friendly = decoded.name;
          else if (decoded.product_name) friendly = decoded.product_name;
          else if (decoded.device_name) friendly = decoded.device_name;
          else if (decoded.Model) friendly = decoded.Model;
          else if (decoded.Manufacturer) friendly = decoded.Manufacturer;
          // Show TI if present
          let tiLine = "";
          if (typeof dgnInfo.ti !== "undefined") {
            tiLine = `<div class='text-xs themed-table-muted'>TI: ${escapeHTML(
              String(dgnInfo.ti)
            )}</div>`;
          }
          // Show friendly name above expand button if found
          return `<div>${
            friendly
              ? `<div class='font-semibold mb-1'>${escapeHTML(friendly)}</div>`
              : ""
          }
          ${tiLine}
            <button class='expand-json-btn themed-table-btn' onclick="window.toggleDgnJson('${cellId}')">&#x1F50D;</button>
            <span id='${cellId}' class='hidden'>${prettyPrintJSON(
            decoded
          )}</span></div>`;
        } else {
          return '<span class="themed-table-muted">No response</span>';
        }
      }
      tr.innerHTML = `
        <td class="font-mono">${addr}</td>
        <td>${dgnCell("EE00")}</td>
        <td>${dgnCell("FEFA")}</td>
        <td>${dgnCell("FEFC")}</td>
      `;
      tbody.appendChild(tr);
    });
  }
  // Expose a global for expand/collapse (quick hack)
  window.toggleDgnJson = function (cellId) {
    const el = document.getElementById(cellId);
    if (el) el.classList.toggle("hidden");
  };
  // Patch mergeScanResult to store decoded per DGN
  function mergeScanResult(result) {
    if (!result || typeof result.value === "undefined") return;
    const addr = result.value;
    if (!scanStatusByAddr[addr]) scanStatusByAddr[addr] = { dgns: {} };
    const dgnHex = (result.dgn || result.dgn_hex || "")
      .toString()
      .toUpperCase();
    console.log(
      "mergeScanResult: addr",
      addr,
      "dgnHex",
      dgnHex,
      "result",
      result
    ); // Debug log
    if (SCAN_DGNS.map((d) => d.toString(16).toUpperCase()).includes(dgnHex)) {
      scanStatusByAddr[addr].dgns[dgnHex] = {
        received: true,
        iface: result.iface,
        decoded: result.decoded || null,
        ti: typeof result.ti !== "undefined" ? result.ti : undefined,
      };
    }
    renderDgnTable();
  }
  // WebSocket for scan results
  let ws;
  function connectScanWebSocket() {
    ws = new WebSocket(
      (window.location.protocol === "https:" ? "wss://" : "ws://") +
        window.location.host +
        "/api/ws/canbus-scan"
    );
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Scan WS received:", data); // Debug log
        mergeScanResult(data);
      } catch (e) {
        console.error("WS parse error", e, event.data); // Debug log
      }
    };
    ws.onopen = () => {};
    ws.onclose = () => {};
    ws.onerror = () => {};
  }
  connectScanWebSocket();
}

export function cleanupNetworkMapView() {
  disconnectNetworkMapSocket();
  const view = document.getElementById("network-map-view");
  if (view) view.innerHTML = "";
}
