// mappingView.js - Handles the Mapping view logic for the rvc2api Web UI
// Responsibilities:
// - Fetching and rendering the device mapping YAML file
// - Providing UI feedback (toasts, error messages)
// - Modularizing mapping view for maintainability

import { fetchData } from "../api.js";
import { showToast } from "../utils.js";
import { apiBasePath } from "../config.js";

const mappingContent = document.getElementById("mapping-content");

export function fetchAndRenderMapping() {
  fetchData(`${apiBasePath}/config/device_mapping`, {
    responseType: "text",
    successCallback: (textData) => {
      if (mappingContent) {
        mappingContent.textContent = textData;
      }
    },
    errorCallback: (error) => {
      if (mappingContent)
        mappingContent.textContent = `Error loading mapping: ${error.message}`;
      showToast("Failed to load device mapping.", "error");
    },
    loadingElement: mappingContent,
  });
}

export function renderMappingView() {
  fetchAndRenderMapping();
}
