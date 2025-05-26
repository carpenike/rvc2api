/**
 * lightsView.js - Handles the Lights view logic for the rvc2api Web UI
 *
 * Responsibilities:
 * - Fetching and rendering light entities
 * - Managing area filter and grouped rendering
 * - Handling real-time updates via WebSocketManager
 * - Providing UI feedback (toasts, error messages)
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */
import { fetchData, callLightService } from "../api.js";
import { showToast } from "../utils.js";
import {
  apiBasePath,
  CLASS_HIDDEN,
  entitySocketUrl,
  CLASS_LIGHT_ON,
  CLASS_LIGHT_OFF,
} from "../config.js";
import { WebSocketManager } from "../wsManager.js";

export const lightsElements = {
  view: document.getElementById("lights-view"),
  content: document.getElementById("lightsContent"),
  loadingMessage: document.getElementById("lights-loading-message"),
  areaFilter: document.getElementById("area-filter"),
};

export const currentLightStates = {};

let entitySocketManager = null;

function handleEntitySocketMessage(data) {
  try {
    const updatedEntity = JSON.parse(data);
    if (
      updatedEntity &&
      updatedEntity.entity_id &&
      typeof updatedEntity.state === "string"
    ) {
      const entityId = updatedEntity.entity_id;
      currentLightStates[entityId] = {
        ...(currentLightStates[entityId] || {}),
        ...updatedEntity,
      };
      if (!lightsElements.view.classList.contains(CLASS_HIDDEN)) {
        updateOrInsertLightCard(entityId);
      }
    }
  } catch (error) {
    console.error(
      "[ENTITY_WS] Error processing entity WebSocket message:",
      error,
      "Raw data:",
      data
    );
  }
}

/**
 * Updates or inserts a single light card in the DOM for the given entityId.
 * Only updates the card if it is currently visible in the filtered area.
 */
function updateOrInsertLightCard(entityId) {
  const { content, areaFilter } = lightsElements;
  if (!content || !areaFilter) return;
  const entity = currentLightStates[entityId];
  if (!entity || entity.device_type !== "light") return;
  const selectedArea = areaFilter.value;
  const entityArea = entity.suggested_area || "Unknown Area";
  if (selectedArea !== "All" && selectedArea !== entityArea) {
    // If the card is present but now filtered out, remove it
    const card = content.querySelector(
      `.entity-card[data-entity-id='${entityId}']`
    );
    if (card) card.remove();
    return;
  }
  // Find the section for this area
  let section = content.querySelector(
    `.lights-area-section[data-area='${entityArea}']`
  );
  if (!section) {
    // If not present, create a new section for this area
    section = document.createElement("div");
    section.className = "mb-8 lights-area-section";
    section.dataset.area = entityArea;
    const header = document.createElement("h2");
    header.className = "text-2xl font-semibold mb-4 pb-2";
    header.style.borderBottom = `2px solid var(--color-border-primary)`;
    header.textContent = entityArea;
    section.appendChild(header);
    const grid = document.createElement("div");
    grid.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6";
    section.appendChild(grid);
    // Insert in sorted order
    const allSections = Array.from(
      content.querySelectorAll(".lights-area-section")
    );
    let inserted = false;
    for (let i = 0; i < allSections.length; i++) {
      if (allSections[i].dataset.area > entityArea) {
        content.insertBefore(section, allSections[i]);
        inserted = true;
        break;
      }
    }
    if (!inserted) content.appendChild(section);
  }
  const grid = section.querySelector(".grid");
  if (!grid) return;
  // Remove old card if present
  const oldCard = grid.querySelector(
    `.entity-card[data-entity-id='${entityId}']`
  );
  if (oldCard) oldCard.remove();
  // Insert new/updated card
  const newCard = renderLightCard(entity);
  grid.appendChild(newCard);

  // --- Stable sort: ensure all cards are sorted after update ---
  // Gather all entities for this area
  const areaEntities = Object.values(currentLightStates).filter(
    (e) =>
      e.device_type === "light" &&
      (e.suggested_area || "Unknown Area") === entityArea
  );
  areaEntities.sort((a, b) => {
    const nameA = a.friendly_name || a.entity_id;
    const nameB = b.friendly_name || b.entity_id;
    if (nameA === nameB) {
      return a.entity_id.localeCompare(b.entity_id);
    }
    return nameA.localeCompare(nameB);
  });
  // Remove all cards, then re-append in sorted order
  const cards = Array.from(grid.querySelectorAll(".entity-card"));
  cards.forEach((card) => card.remove());
  areaEntities.forEach((e) => {
    grid.appendChild(e.entity_id === entityId ? newCard : renderLightCard(e));
  });
}

export function handleLightsViewVisibility(isVisible) {
  if (isVisible) {
    if (!entitySocketManager) {
      entitySocketManager = new WebSocketManager(
        entitySocketUrl,
        handleEntitySocketMessage,
        {
          onOpen: () => showToast("Real-time updates connected.", "info", 2000),
          onError: () =>
            showToast("Real-time updates connection error.", "error"),
          onClose: () =>
            showToast("Real-time updates disconnected.", "warning"),
          autoReconnect: true,
          reconnectInterval: 5000,
        }
      );
    }
  } else {
    if (entitySocketManager) {
      entitySocketManager.close();
      entitySocketManager = null;
    }
  }
}

export function updateLightsView() {
  const { view, content, loadingMessage, areaFilter } = lightsElements;
  if (!view || !content) return;
  if (!view.classList.contains(CLASS_HIDDEN)) {
    if (loadingMessage) loadingMessage.classList.remove(CLASS_HIDDEN);
    content.innerHTML = "";
    fetchData(`${apiBasePath}/entities?device_type=light`, {
      successCallback: (lightsData) => {
        Object.keys(currentLightStates).forEach(
          (key) => delete currentLightStates[key]
        );
        Object.values(lightsData).forEach((light) => {
          currentLightStates[light.entity_id] = light;
        });
        if (loadingMessage) loadingMessage.classList.add(CLASS_HIDDEN);
        updateAreaFilterForLights(currentLightStates);
        renderGroupedLights();
      },
      errorCallback: (error) => {
        if (loadingMessage) {
          loadingMessage.textContent =
            "Error loading lights. Please check console.";
          loadingMessage.classList.remove(CLASS_HIDDEN);
        }
        if (content)
          content.innerHTML =
            '<p class="text-red-500">Error loading lights data.</p>';
      },
      loadingElement: loadingMessage,
    });
  }
}

export function updateAreaFilterForLights(lights) {
  const { areaFilter } = lightsElements;
  if (!areaFilter) return;
  const currentSelectedValue =
    localStorage.getItem("lightsAreaFilter") || "All";
  const areas = new Set(["All"]);
  Object.values(lights).forEach((entity) => {
    if (entity.device_type === "light" && entity.suggested_area) {
      areas.add(entity.suggested_area);
    }
  });
  areaFilter.innerHTML = "";
  Array.from(areas)
    .sort()
    .forEach((area) => {
      const option = document.createElement("option");
      option.value = area;
      option.textContent = area;
      areaFilter.appendChild(option);
    });
  if (areas.has(currentSelectedValue)) {
    areaFilter.value = currentSelectedValue;
  } else {
    areaFilter.value = "All";
    localStorage.setItem("lightsAreaFilter", "All");
  }
  areaFilter.disabled = areas.size <= 1;
}

export function renderGroupedLights() {
  const { content, areaFilter } = lightsElements;
  if (!content) return;
  content.innerHTML = "";
  const selectedArea = areaFilter.value;
  localStorage.setItem("lightsAreaFilter", selectedArea);
  const grouped = {};
  Object.values(currentLightStates).forEach((entity) => {
    if (entity.device_type !== "light") return;
    const area = entity.suggested_area || "Unknown Area";
    if (selectedArea !== "All" && selectedArea !== area) return;
    if (!grouped[area]) grouped[area] = [];
    grouped[area].push(entity);
  });
  if (Object.keys(grouped).length === 0 && selectedArea === "All") {
    content.innerHTML = '<p class="text-gray-400">No lights found.</p>';
    return;
  } else if (Object.keys(grouped).length === 0) {
    content.innerHTML = `<p class="text-gray-400">No lights found in area: ${selectedArea}.</p>`;
    return;
  }
  Object.keys(grouped)
    .sort()
    .forEach((area) => {
      const section = document.createElement("div");
      section.className = "mb-8 lights-area-section";
      section.dataset.area = area;
      const header = document.createElement("h2");
      header.className = "text-2xl font-semibold mb-4 pb-2";
      header.style.borderBottom = `2px solid var(--color-border-primary)`;
      header.textContent = area;
      section.appendChild(header);
      const grid = document.createElement("div");
      grid.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6";
      section.appendChild(grid);
      grouped[area]
        .sort((a, b) =>
          (a.friendly_name || a.entity_id).localeCompare(
            b.friendly_name || b.entity_id
          )
        )
        .forEach((entity) => {
          grid.appendChild(renderLightCard(entity));
        });
      content.appendChild(section);
    });
}

export function renderLightCard(entity) {
  const card = document.createElement("div");
  card.className = `entity-card p-4 rounded-lg shadow-md space-y-3`;
  card.dataset.entityId = entity.entity_id;
  const friendlyName = entity.friendly_name || entity.entity_id;
  const entityState = (entity.state || "unknown").toLowerCase();
  const capabilities = entity.capabilities || [];
  const rawAttrs = entity.raw || {};
  card.classList.toggle(CLASS_LIGHT_ON, entityState === "on");
  card.classList.toggle(CLASS_LIGHT_OFF, entityState !== "on");
  let cardContent = `<h3 class="text-lg font-semibold">${friendlyName}</h3>`;
  const hasBrightness = capabilities.includes("brightness");
  if (hasBrightness) {
    let currentBrightnessPercent = 0;
    if (typeof entity.brightness === "number") {
      currentBrightnessPercent = Math.max(0, Math.min(100, entity.brightness));
    } else if (
      entityState === "on" &&
      rawAttrs.operating_status !== undefined &&
      !isNaN(rawAttrs.operating_status)
    ) {
      // Fallback: convert raw.operating_status (0-200 CAN scale) to 0-100 UI
      currentBrightnessPercent = Math.round(
        Math.max(0, Math.min(100, (rawAttrs.operating_status / 200) * 100))
      );
    }
    cardContent += `
      <div class="brightness-control space-y-1">
        <label for="brightness-${entity.entity_id}" class="block text-sm font-medium">Brightness: <span class="brightness-value">${currentBrightnessPercent}%</span></label>
        <input type="range" id="brightness-${entity.entity_id}" name="brightness"
               min="0" max="100" value="${currentBrightnessPercent}"
               class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer brightness-slider">
      </div>
    `;
  }
  card.innerHTML = cardContent;
  card.addEventListener("click", (e) => {
    if (e.target.closest(".brightness-control")) return;
    callLightService(entity.entity_id, "toggle").then(() => {
      showToast(`Toggled ${friendlyName}`, "info");
    });
  });
  if (hasBrightness) {
    const slider = card.querySelector(".brightness-slider");
    const brightnessValueDisplay = card.querySelector(".brightness-value");
    if (slider && brightnessValueDisplay) {
      slider.addEventListener("input", (e) => {
        brightnessValueDisplay.textContent = `${slider.value}%`;
      });
      slider.addEventListener("change", (e) => {
        callLightService(entity.entity_id, "set", {
          state: "on",
          brightness: Number(slider.value),
        }).then(() => {
          showToast(
            `Set brightness for ${friendlyName} to ${slider.value}%`,
            "success"
          );
        });
      });
    }
  }
  return card;
}

// Wire up areaFilter change handler
lightsElements.areaFilter?.addEventListener("change", renderGroupedLights);
