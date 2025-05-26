/**
 * unmappedView.js - Handles the Unmapped Entries view logic for the rvc2api Web UI
 *
 * Responsibilities:
 * - Fetching and rendering unmapped CAN entries
 * - Providing YAML suggestions and copy-to-clipboard functionality
 * - UI feedback (toasts, error messages)
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */
import { fetchData } from "../api.js";
import { showToast, copyToClipboard } from "../utils.js";
import { apiBasePath } from "../config.js";

const unmappedEntriesView = document.getElementById("unmapped-view");
const unmappedEntriesContent = document.getElementById(
  "unmapped-entries-container"
);

function generateYamlSuggestion(entry) {
  // Generate a detailed YAML suggestion with comments, as in the original UI
  const dgnKey = entry.dgn_hex;
  const instanceKey = String(entry.instance);
  const dgnForId = dgnKey.toLowerCase();
  const instanceForId = instanceKey.toLowerCase().replace(/[^a-z0-9_]/g, "");
  let suggestedEntityId = `unmapped_${dgnForId}_inst${instanceForId}`;
  let yaml = `# Suggested entry for DGN: ${dgnKey}${
    entry.dgn_name ? " (" + entry.dgn_name + ")" : ""
  }, Instance: ${instanceKey}\n`;
  if (entry.pgn_hex && entry.pgn_hex !== entry.dgn_hex) {
    yaml += `# Original PGN from Arbitration ID: ${entry.pgn_hex}${
      entry.pgn_name ? " (" + entry.pgn_name + ")" : ""
    }\n`;
  }
  yaml += `# First seen: ${new Date(
    entry.first_seen_timestamp * 1000
  ).toLocaleString()}\n`;
  yaml += `# Last seen: ${new Date(
    entry.last_seen_timestamp * 1000
  ).toLocaleString()}\n`;
  yaml += `# Count: ${entry.count}\n`;
  yaml += `# Last Data: ${entry.last_data_hex}\n`;
  if (entry.decoded_signals && Object.keys(entry.decoded_signals).length > 0) {
    yaml += `# Decoded Signals (from PGN ${entry.pgn_hex}):\n`;
    for (const [key, value] of Object.entries(entry.decoded_signals)) {
      yaml += `#   ${key}: ${value}\n`;
    }
  }
  if (entry.spec_entry && entry.spec_entry.name) {
    yaml += `# Matched Spec Entry Name (for DGN): ${entry.spec_entry.name}\n`;
  }
  yaml += `\n`;
  yaml += `${dgnKey}:\n`;
  yaml += `  ${instanceKey}:\n`;
  yaml += `    - entity_id: "${suggestedEntityId}" # TODO: MUST be unique. Change to a descriptive name (e.g., 'living_room_thermostat')\n`;
  yaml += `      friendly_name: "Unmapped ${
    entry.dgn_name || dgnKey
  } Inst ${instanceKey}" # TODO: Set a user-friendly name (e.g., 'Living Room Thermostat')\n`;
  yaml += `      suggested_area: "Unknown Area" # TODO: Assign an area (e.g., 'Living Room', 'Bedroom')\n`;
  yaml += `      device_type: "unknown" # TODO: Specify type (e.g., light, sensor, hvac, lock, switch, tank)\n`;
  yaml += `      capabilities: [] # TODO: Define capabilities (e.g., [on_off], [on_off, brightness], [lock_unlock], [temperature])\n`;
  yaml += `      # --- Optional fields based on device_type and system needs ---\n`;
  yaml += `      # interface: canX # TODO: Specify CAN interface if known (e.g., can0, can1)\n`;
  yaml += `      # status_dgn: '${dgnKey}' # Status DGN is typically this DGN key\n`;
  yaml += `      # command_pgn: 'YYYYY' # TODO: If controllable and different from status DGN, specify command PGN\n`;
  yaml += `      # group_mask: '0xXX' # TODO: If part of a command/status group\n`;
  yaml += `      # --- Example for using a YAML template (if defined in your mapping file) ---\n`;
  yaml += `      # <<: *switchable_light  # For on/off lights, if &switchable_light template exists\n`;
  yaml += `      # <<: *dimmable_light   # For dimmable lights, if &dimmable_light template exists\n`;
  return yaml;
}

export function renderUnmappedEntries(data) {
  try {
    if (!unmappedEntriesContent) return;
    unmappedEntriesContent.innerHTML = "";
    const loadingMsg = document.getElementById("unmapped-loading-message");
    if (loadingMsg) loadingMsg.classList.add("hidden");
    if (Object.keys(data).length === 0) {
      unmappedEntriesContent.innerHTML =
        '<p class="text-gray-500">No unmapped entries found. Good job!</p>';
      return;
    }
    for (const [key, entry] of Object.entries(data)) {
      const entryDiv = document.createElement("div");
      entryDiv.className = "bg-gray-800 p-4 rounded-lg shadow mb-4";
      let decodedSignalsHtml = "N/A";
      if (
        entry.decoded_signals &&
        Object.keys(entry.decoded_signals).length > 0
      ) {
        decodedSignalsHtml = '<ul class="list-disc list-inside pl-4 text-sm">';
        for (const [sigKey, sigValue] of Object.entries(
          entry.decoded_signals
        )) {
          decodedSignalsHtml += `<li><strong>${sigKey}:</strong> ${sigValue}</li>`;
        }
        decodedSignalsHtml += "</ul>";
      } else if (entry.decoded_signals) {
        decodedSignalsHtml =
          '<span class="text-gray-500">No signals decoded (PGN might be complex or data invalid).</span>';
      }
      let suggestionsHtml = "";
      if (entry.suggestions && entry.suggestions.length > 0) {
        suggestionsHtml =
          '<div class="mt-3"><p class="font-semibold mb-1 text-blue-300">Mapping Suggestions (other instances of this DGN):</p><ul class="list-disc list-inside pl-4 text-sm">';
        entry.suggestions.forEach((sugg) => {
          suggestionsHtml += `<li>Instance <strong>${
            sugg.instance
          }</strong> mapped to: <strong>${sugg.name}</strong> (Area: ${
            sugg.suggested_area || "N/A"
          })</li>`;
        });
        suggestionsHtml += "</ul></div>";
      }
      const yamlSuggestion = generateYamlSuggestion(entry);
      entryDiv.innerHTML = `
        <h3 class="text-xl font-semibold text-yellow-400 mb-2">Unmapped Key: ${key}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm mb-3">
          <p><strong>PGN (from ArbID):</strong> ${entry.pgn_hex} ${
        entry.pgn_name ? `(${entry.pgn_name})` : ""
      }</p>
          <p><strong>DGN (for mapping):</strong> ${entry.dgn_hex} ${
        entry.dgn_name ? `(${entry.dgn_name})` : ""
      }</p>
          <p><strong>Instance:</strong> ${entry.instance}</p>
          <p><strong>Count:</strong> ${entry.count}</p>
          <p><strong>First Seen:</strong> ${new Date(
            entry.first_seen_timestamp * 1000
          ).toLocaleString()}</p>
          <p><strong>Last Seen:</strong> ${new Date(
            entry.last_seen_timestamp * 1000
          ).toLocaleString()}</p>
          <p class="md:col-span-2"><strong>Last Data Hex:</strong> <code class="text-green-400">${
            entry.last_data_hex
          }</code></p>
        </div>
        <div class="mb-3">
          <p class="font-semibold mb-1">Decoded Signals (from PGN ${
            entry.pgn_hex
          }):</p>
          ${decodedSignalsHtml}
        </div>
        ${suggestionsHtml}
        <div>
          <p class="font-semibold mt-3 mb-1">Suggested device_mapping.yml entry:</p>
          <pre class="bg-gray-900 text-green-300 p-3 rounded overflow-auto text-xs whitespace-pre-wrap"><code class="language-yaml">${yamlSuggestion}</code></pre>
          <button class="mt-2 bg-blue-600 hover:bg-blue-500 text-white py-1 px-3 rounded text-xs copy-yaml-btn">Copy YAML</button>
        </div>
      `;
      unmappedEntriesContent.appendChild(entryDiv);
    }
    // Event delegation for copy buttons
    if (!unmappedEntriesContent.hasAttribute("data-copy-bound")) {
      unmappedEntriesContent.setAttribute("data-copy-bound", "");
      unmappedEntriesContent.addEventListener("click", (event) => {
        const btn = event.target.closest(".copy-yaml-btn");
        if (!btn) return;
        const code = btn.previousElementSibling.querySelector("code");
        if (!code) return;
        const yamlText = code.innerText;
        btn.textContent = "Copying...";
        copyToClipboard(yamlText)
          .then(() => {
            btn.textContent = "Copied!";
            showToast("YAML copied to clipboard!", "success");
            setTimeout(() => {
              btn.textContent = "Copy YAML";
            }, 2000);
          })
          .catch((err) => {
            showToast("Failed to copy YAML.", "error");
            btn.textContent = "Failed to copy";
            setTimeout(() => {
              btn.textContent = "Copy YAML";
            }, 2000);
          });
      });
    }
  } catch (err) {
    console.error("Error in renderUnmappedEntries:", err);
    if (unmappedEntriesContent)
      unmappedEntriesContent.textContent = "Error rendering unmapped entries.";
  }
}

export function fetchUnmappedEntries() {
  fetchData(`${apiBasePath}/unmapped_entries`, {
    successCallback: renderUnmappedEntries,
    errorCallback: (error) => {
      if (unmappedEntriesContent)
        unmappedEntriesContent.textContent = `Error loading unmapped entries: ${error.message}`;
      showToast("Failed to load unmapped entries.", "error");
    },
    loadingElement:
      unmappedEntriesContent?.querySelector("#unmapped-loading-message") ||
      unmappedEntriesContent,
  });
}
