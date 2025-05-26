/**
 * api.js - API utility functions for rvc2api Web UI
 *
 * Provides:
 * - fetchData: Universal fetch utility for API calls with flexible options and error handling.
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

/**
 * Universal fetch utility for API calls with flexible options and error handling.
 *
 * @param {string} url - The endpoint URL to fetch.
 * @param {object} [options={}] - Options for the fetch request.
 * @param {'GET'|'POST'|'PUT'|'DELETE'} [options.method='GET'] - HTTP method.
 * @param {object} [options.headers] - Request headers (default: JSON for POST/PUT, none for GET).
 * @param {object|string|null} [options.body=null] - Request body (object will be JSON.stringified).
 * @param {'json'|'text'} [options.responseType='json'] - Expected response type.
 * @param {function} [options.successCallback] - Called with response data on success.
 * @param {function} [options.errorCallback] - Called with error object on failure.
 * @param {HTMLElement|null} [options.loadingElement=null] - Element to show loading/error message.
 * @param {boolean} [options.showToastOnError=true] - Show toast on error.
 */
export function fetchData(url, options = {}) {
  const {
    method = "GET",
    headers = method === "GET" ? {} : { "Content-Type": "application/json" },
    body = null,
    responseType = "json",
    successCallback = () => {},
    errorCallback = null,
    loadingElement = null,
    showToastOnError = true,
  } = options;

  if (loadingElement) {
    loadingElement.textContent = "Loading...";
    loadingElement.classList.remove("text-red-500");
    loadingElement.classList.add("text-gray-400");
  }

  fetch(url, {
    method,
    headers,
    body:
      body && method !== "GET"
        ? typeof body === "string"
          ? body
          : JSON.stringify(body)
        : undefined,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return responseType === "text" ? response.text() : response.json();
    })
    .then((data) => {
      if (loadingElement) loadingElement.textContent = "";
      successCallback(data);
    })
    .catch((error) => {
      if (loadingElement) {
        loadingElement.textContent = "Error loading data.";
        loadingElement.classList.remove("text-gray-400");
        loadingElement.classList.add("text-red-500");
      }
      if (showToastOnError && typeof window.showToast === "function") {
        window.showToast(error.message || "API error", "error");
      }
      if (typeof errorCallback === "function") errorCallback(error);
    });
}

/**
 * Calls a light service (toggle, set_brightness, etc.) for a given entity.
 * @param {string} entityId - The entity_id of the light.
 * @param {string} command - The command to send (e.g., 'toggle', 'set_brightness').
 * @param {object} [params={}] - Additional parameters for the command.
 * @returns {Promise<any>} Resolves with the response or false on error.
 */
export function callLightService(entityId, command, params = {}) {
  return fetch(`/api/entities/${entityId}/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, ...params }),
  })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .catch((err) => {
      console.error("callLightService error:", err);
      return false;
    });
}
