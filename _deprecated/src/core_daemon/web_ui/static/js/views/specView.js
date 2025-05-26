/**
 * specView.js - Handles the RVC Specification view logic for the rvc2api Web UI
 *
 * Responsibilities:
 * - Fetching and rendering the RVC specification text and metadata
 * - UI feedback (toasts, error messages)
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

import { fetchData } from "../api.js";
import { showToast } from "../utils.js";
import { apiBasePath } from "../config.js";

const specContent = document.getElementById("spec-content");
const specMetadataDiv = document.getElementById("spec-metadata");

function updateSpecTextView(textData) {
  try {
    if (specContent) {
      // Try to pretty-print JSON if possible, else show as plain text
      let pretty = null;
      let parsed = null;
      try {
        parsed = JSON.parse(textData);
        pretty = JSON.stringify(parsed, null, 2);
      } catch {
        // Not JSON, show as-is
      }
      specContent.textContent = pretty || textData;
      // Add toggle and filter UI if JSON
      if (pretty && parsed && typeof parsed === "object") {
        // Toggle button
        let toggleBtn = document.getElementById("spec-toggle-btn");
        if (!toggleBtn) {
          toggleBtn = document.createElement("button");
          toggleBtn.id = "spec-toggle-btn";
          toggleBtn.className =
            "mt-2 mb-2 bg-blue-600 hover:bg-blue-500 text-white py-1 px-3 rounded text-xs";
          toggleBtn.textContent = "Show Raw";
          specContent.parentElement.insertBefore(toggleBtn, specContent);
        }
        let showingPretty = true;
        toggleBtn.onclick = () => {
          showingPretty = !showingPretty;
          specContent.textContent = showingPretty ? pretty : textData;
          toggleBtn.textContent = showingPretty ? "Show Raw" : "Show Pretty";
          // Hide filter UI if not pretty
          if (filterContainer)
            filterContainer.style.display = showingPretty ? "block" : "none";
        };
        // Filtering UI
        let filterContainer = document.getElementById("spec-filter-container");
        if (!filterContainer) {
          filterContainer = document.createElement("div");
          filterContainer.id = "spec-filter-container";
          filterContainer.className = "mb-2 flex flex-wrap gap-2 items-center";
          specContent.parentElement.insertBefore(filterContainer, toggleBtn);
        }
        filterContainer.innerHTML = `
          <input id="spec-filter-input" type="text" placeholder="Filter by key or value..." class="px-2 py-1 rounded border border-gray-400 text-xs w-64" />
          <button id="spec-filter-clear" class="ml-2 px-2 py-1 rounded bg-gray-600 text-white text-xs">Clear</button>
        `;
        filterContainer.style.display = "block";
        const filterInput = filterContainer.querySelector("#spec-filter-input");
        const filterClear = filterContainer.querySelector("#spec-filter-clear");
        function renderFiltered(filter) {
          if (!filter) {
            specContent.textContent = pretty;
            return;
          }
          // Simple recursive filter: show only matching keys/values
          function filterObj(obj) {
            if (typeof obj !== "object" || obj === null) return obj;
            if (Array.isArray(obj)) {
              return obj
                .map(filterObj)
                .filter((item) =>
                  JSON.stringify(item).toLowerCase().includes(filter)
                );
            }
            const result = {};
            for (const [k, v] of Object.entries(obj)) {
              if (
                k.toLowerCase().includes(filter) ||
                (typeof v === "string" && v.toLowerCase().includes(filter))
              ) {
                result[k] = v;
              } else if (typeof v === "object" && v !== null) {
                const sub = filterObj(v);
                if (
                  sub &&
                  (typeof sub === "object" ? Object.keys(sub).length : sub)
                ) {
                  result[k] = sub;
                }
              }
            }
            return result;
          }
          const filtered = filterObj(parsed);
          specContent.textContent = JSON.stringify(filtered, null, 2);
        }
        filterInput.addEventListener("input", (e) => {
          const val = e.target.value.trim().toLowerCase();
          renderFiltered(val);
        });
        filterClear.addEventListener("click", () => {
          filterInput.value = "";
          specContent.textContent = pretty;
        });
      } else {
        // Remove toggle and filter UI if not JSON
        const oldBtn = document.getElementById("spec-toggle-btn");
        if (oldBtn) oldBtn.remove();
        const oldFilter = document.getElementById("spec-filter-container");
        if (oldFilter) oldFilter.remove();
      }
    }
  } catch (err) {
    console.error("Error in updateSpecTextView:", err);
    if (specContent) specContent.textContent = "Error rendering spec content.";
  }
}

function updateSpecMetadataView(metadata) {
  try {
    if (specMetadataDiv) {
      if (
        metadata &&
        (metadata.version || metadata.source || metadata.spec_document)
      ) {
        specMetadataDiv.innerHTML = `
          Version: ${metadata.version || "N/A"}<br>
          Source: ${metadata.spec_document || metadata.source || "N/A"}
        `;
      } else {
        specMetadataDiv.textContent = "Specification metadata not available.";
      }
    }
  } catch (err) {
    console.error("Error in updateSpecMetadataView:", err);
    if (specMetadataDiv)
      specMetadataDiv.textContent = "Error rendering spec metadata.";
  }
}

export function fetchSpecView() {
  // Fetch Spec Content (Text)
  fetchData(`${apiBasePath}/config/rvc_spec`, {
    responseType: "text",
    successCallback: updateSpecTextView,
    errorCallback: (error) => {
      console.error("Failed to fetch spec content:", error);
      if (specContent)
        specContent.textContent = `Error loading RVC spec content: ${error.message}`;
      showToast("Failed to load RVC specification content.", "error");
    },
    loadingElement: specContent,
  });

  // Fetch Spec Metadata (JSON)
  fetchData(`${apiBasePath}/config/rvc_spec_metadata`, {
    responseType: "json",
    successCallback: updateSpecMetadataView,
    errorCallback: (error) => {
      console.error("Failed to fetch spec metadata:", error);
      if (specMetadataDiv)
        specMetadataDiv.textContent = "Error loading RVC spec metadata.";
    },
  });
}
