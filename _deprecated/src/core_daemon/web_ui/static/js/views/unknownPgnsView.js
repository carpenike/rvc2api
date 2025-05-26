/**
 * unknownPgnsView.js - Handles the Unknown PGNs view logic for the rvc2api Web UI
 *
 * Responsibilities:
 * - Fetching and rendering unknown Parameter Group Numbers (PGNs)
 * - Providing detailed table and card views for each PGN, with as much data as possible
 * - UI feedback (toasts, error messages)
 * - Toggle between table and card view
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

import { fetchData } from "../api.js";
import { showToast, copyToClipboard } from "../utils.js";
import { apiBasePath } from "../config.js";

const unknownPgnsView = document.getElementById("unknown-pgns-view");
const unknownPgnsContent = document.getElementById("unknown-pgns-container");

function renderUnknownPgnsTable(data) {
  if (!unknownPgnsContent) return;
  unknownPgnsContent.innerHTML = "";
  if (Object.keys(data).length === 0) {
    unknownPgnsContent.innerHTML = "<p>No unknown PGNs found.</p>";
    return;
  }
  const table = document.createElement("table");
  table.className = "themed-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>PGN</th>
        <th>Count</th>
        <th>First Seen</th>
        <th>Last Seen</th>
        <th>Last Data</th>
      </tr>
    </thead>
    <tbody>
      ${Object.entries(data)
        .map(
          ([pgn, item]) => `
            <tr>
              <td class="font-mono themed-table-note">${pgn}</td>
              <td class="font-bold themed-table-note">${
                item.count?.toLocaleString?.() ?? ""
              }</td>
              <td class="themed-table-muted">${
                item.first_seen_timestamp
                  ? new Date(item.first_seen_timestamp * 1000).toLocaleString()
                  : ""
              }</td>
              <td class="themed-table-muted">${
                item.last_seen_timestamp
                  ? new Date(item.last_seen_timestamp * 1000).toLocaleString()
                  : ""
              }</td>
              <td class="font-mono themed-table-note">${
                item.last_data_hex || ""
              }</td>
            </tr>
          `
        )
        .join("")}
    </tbody>
  `;
  unknownPgnsContent.appendChild(table);
}

function renderUnknownPgnsCards(data) {
  if (!unknownPgnsContent) return;
  unknownPgnsContent.innerHTML = "";
  if (Object.keys(data).length === 0) {
    unknownPgnsContent.innerHTML = "<p>No unknown PGNs found.</p>";
    return;
  }
  const container = document.createElement("div");
  container.className = "space-y-4";
  Object.entries(data).forEach(([pgn, item]) => {
    const card = document.createElement("div");
    card.className = "bg-[var(--color-bg-tertiary)] rounded-lg shadow p-4 mb-4";
    card.innerHTML = `
      <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-2">
        <span class="font-mono themed-table-note text-lg font-semibold">PGN: ${pgn}</span>
        <span class="inline-block themed-table-note text-xs font-bold px-2 py-1 rounded mt-2 md:mt-0">Count: ${
          item.count?.toLocaleString?.() ?? ""
        }</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm mb-2">
        <div><strong>First Seen:</strong> <span class="themed-table-muted">${
          item.first_seen_timestamp
            ? new Date(item.first_seen_timestamp * 1000).toLocaleString()
            : ""
        }</span></div>
        <div><strong>Last Seen:</strong> <span class="themed-table-muted">${
          item.last_seen_timestamp
            ? new Date(item.last_seen_timestamp * 1000).toLocaleString()
            : ""
        }</span></div>
        <div class="md:col-span-2"><strong>Last Data Hex:</strong> <code class="font-mono themed-table-note">${
          item.last_data_hex || ""
        }</code></div>
      </div>
      <button class="mt-2 bg-blue-600 hover:bg-blue-500 text-white py-1 px-3 rounded text-xs copy-hex-btn">Copy Hex</button>
    `;
    container.appendChild(card);
  });
  unknownPgnsContent.appendChild(container);
  // Event delegation for copy buttons
  if (!container.hasAttribute("data-copy-bound")) {
    container.setAttribute("data-copy-bound", "");
    container.addEventListener("click", (event) => {
      const btn = event.target.closest(".copy-hex-btn");
      if (!btn) return;
      const code = btn.parentElement.querySelector("code");
      if (!code) return;
      const hexText = code.innerText;
      btn.textContent = "Copying...";
      copyToClipboard(hexText)
        .then(() => {
          btn.textContent = "Copied!";
          showToast("Hex copied to clipboard!", "success");
          setTimeout(() => {
            btn.textContent = "Copy Hex";
          }, 2000);
        })
        .catch(() => {
          showToast("Failed to copy Hex.", "error");
          btn.textContent = "Failed to copy";
          setTimeout(() => {
            btn.textContent = "Copy Hex";
          }, 2000);
        });
    });
  }
}

export function renderUnknownPgnsWithToggle(data) {
  if (!unknownPgnsContent) return;
  unknownPgnsContent.innerHTML = "";
  // Add toggle buttons
  const toggleContainer = document.createElement("div");
  toggleContainer.className = "mb-4 flex gap-2 items-center";
  const tableBtn = document.createElement("button");
  tableBtn.textContent = "Table View";
  tableBtn.className =
    "px-3 py-1 rounded bg-gray-700 text-gray-200 hover:bg-gray-600 focus:outline-none";
  const cardBtn = document.createElement("button");
  cardBtn.textContent = "Card View";
  cardBtn.className =
    "px-3 py-1 rounded bg-gray-700 text-gray-200 hover:bg-gray-600 focus:outline-none";
  toggleContainer.appendChild(tableBtn);
  toggleContainer.appendChild(cardBtn);
  unknownPgnsContent.appendChild(toggleContainer);
  // Render default (table)
  let currentView = "table";
  function render() {
    if (currentView === "table") {
      renderUnknownPgnsTable(data);
    } else {
      renderUnknownPgnsCards(data);
    }
  }
  render();
  tableBtn.addEventListener("click", () => {
    currentView = "table";
    render();
  });
  cardBtn.addEventListener("click", () => {
    currentView = "card";
    render();
  });
}

export function fetchUnknownPgns() {
  fetchData(`${apiBasePath}/unknown_pgns`, {
    successCallback: renderUnknownPgnsWithToggle,
    errorCallback: (error) => {
      if (unknownPgnsContent)
        unknownPgnsContent.textContent = `Error loading unknown PGNs: ${error.message}`;
      showToast("Failed to load unknown PGNs.", "error");
    },
    loadingElement:
      unknownPgnsContent?.querySelector("#unknown-pgns-loading-message") ||
      unknownPgnsContent,
  });
}
