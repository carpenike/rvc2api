/**
 * app.js - Main JavaScript for the rvc2api Web UI
 *
 * Handles:
 * - Theme management and sidebar state
 * - Fetching and rendering API status, health, CAN status, and entity data
 * - WebSocket connections for logs and entity updates
 * - UI event handling for navigation, controls, and user feedback
 * - Utility functions for DOM manipulation and notifications
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-10
 */

// Import configuration and API utilities
import {
  VALID_THEMES,
  DEFAULT_THEME,
  SELECTED_THEME_KEY,
  DESKTOP_SIDEBAR_EXPANDED_KEY,
  CAN_STATUS_REFRESH_INTERVAL,
  API_STATUS_REFRESH_INTERVAL,
  APP_HEALTH_REFRESH_INTERVAL,
  MD_BREAKPOINT_PX,
  CLASS_HIDDEN,
  CLASS_ACTIVE_NAV,
  ATTR_DATA_VIEW,
  ARIA_HIDDEN,
  LOG_LEVELS,
  CLASS_TEXT_GREEN_400,
  CLASS_TEXT_RED_400,
  CLASS_TEXT_YELLOW_400,
  apiBasePath,
  SIDEBAR_WIDTH_EXPANDED,
  SIDEBAR_WIDTH_COLLAPSED,
  SIDEBAR_TRANSITION,
  entitySocketUrl,
} from "./config.js";
import { fetchData } from "./api.js";
import { showToast, copyToClipboard } from "./utils.js";
import {
  handleLightsViewVisibility,
  updateLightsView,
} from "./views/lightsView.js";
import { WebSocketManager } from "./wsManager.js";
import {
  fetchUnmappedEntries,
  renderUnmappedEntries,
} from "./views/unmappedView.js";
import { ICON_COPY } from "./icons.js";
import {
  fetchUnknownPgns,
  renderUnknownPgnsWithToggle,
} from "./views/unknownPgnsView.js";
import { renderHomeView, stopHomePolling } from "./views/homeView.js";
import { fetchSpecView } from "./views/specView.js";
import { renderMappingView } from "./views/mappingView.js";
import {
  renderCanSnifferView,
  cleanupCanSnifferView,
} from "./views/canSnifferView.js";
import {
  renderNetworkMapView,
  cleanupNetworkMapView,
} from "./views/networkMapView.js";
import { initThemeDropdown } from "./themeDropdown.js";

/**
 * @type {string | null} The application version, read from a data attribute on the body.
 */
let APP_VERSION = null; // Will be read from body data attribute

// =====================
// DOM ELEMENT CACHE
// =====================
const appHeader = document.getElementById("appHeader"); // For app version display
const appVersionDisplay = document.getElementById("appVersionDisplay"); // Span to show APP_VERSION

const mainContent = document.getElementById("mainContent");
const sidebar = document.getElementById("sidebar");
const sidebarNavContent = document.getElementById("sidebarNavContent");
const toggleSidebarDesktopButton = document.getElementById(
  "toggleSidebarDesktop"
);
const mobileMenuButton = document.getElementById("mobileMenuButton");
const navLinks = document.querySelectorAll(".nav-link");
const views = document.querySelectorAll(".view-section");
const homeView = document.getElementById("home-view");
const mappingView = document.getElementById("mapping-view");
const mappingContent = document.getElementById("mapping-content");
const specView = document.getElementById("spec-view");
const specContent = document.getElementById("spec-content");
const specMetadataDiv = document.getElementById("spec-metadata");
const unmappedEntriesView = document.getElementById("unmapped-view");
const unmappedEntriesContent = document.getElementById(
  "unmapped-entries-container"
);
const unknownPgnsView = document.getElementById("unknown-pgns-view");
const unknownPgnsContent = document.getElementById("unknown-pgns-container");
const apiStatusContent = document.getElementById("api-status-container");
const appHealthContent = document.getElementById("app-health-container");
const canStatusContent = document.getElementById("can-status-container");
const logStream = document.getElementById("log-stream");
const logLevelSelect = document.getElementById("log-level");
const logSearchInput = document.getElementById("log-search");
const logPauseButton = document.getElementById("log-pause");
const logResumeButton = document.getElementById("log-resume");
const logClearButton = document.getElementById("log-clear");
const pinnedLogsContainer = document.getElementById("pinnedLogsContainer");
const pinnedLogsContent = document.getElementById("pinnedLogsContent");
const pinnedLogsHeader = document.getElementById("pinnedLogsHeader");
const pinnedLogsResizeHandle = document.getElementById(
  "pinnedLogsResizeHandle"
);
const togglePinnedLogsButton = document.getElementById("togglePinnedLogsBtn");
const toastContainer = document.getElementById("toast-container");
const closeSidebarButton = document.getElementById("closeSidebarButton");

let logSocketManager = null;
let currentView = "home"; // Default view
let currentTheme = DEFAULT_THEME;
let pinnedLogMessages = []; // Not currently used, consider for re-filtering if needed
let isPinnedLogsVisible = false; // Consider if this state is needed or derived from DOM
let isResizingPinnedLogs = false; // Already used for resize handle
let originalContainerTransition; // For resize handle
let currentLogLevel = LOG_LEVELS.INFO; // Default log level
let isLogPaused = false;

// Sidebar state: expanded/collapsed (desktop)
let isDesktopSidebarExpanded = true; // Default to expanded; will be set on load

// =====================
// UTILITY FUNCTIONS
// =====================

/**
 * Creates a DOM element with specified options.
 * @param {string} tag - The HTML tag for the element.
 * @param {object} [options={}] - Options for creating the element.
 * @param {string} [options.className] - CSS class name(s).
 * @param {string} [options.id] - Element ID.
 * @param {string} [options.textContent] - Text content.
 * @param {string} [options.innerHTML] - Inner HTML.
 * @param {object} [options.dataset] - Data attributes.
 * @param {object} [options.attributes] - Other HTML attributes.
 * @param {HTMLElement[]} [options.children] - Child elements to append.
 * @returns {HTMLElement} The created DOM element.
 */
function createDomElement(tag, options = {}) {
  const el = document.createElement(tag);
  if (options.className) el.className = options.className;
  if (options.id) el.id = options.id;
  if (options.textContent) el.textContent = options.textContent;
  if (options.innerHTML) el.innerHTML = options.innerHTML;
  if (options.dataset) {
    for (const [k, v] of Object.entries(options.dataset)) {
      el.dataset[k] = v;
    }
  }
  if (options.attributes) {
    for (const [k, v] of Object.entries(options.attributes)) {
      el.setAttribute(k, v);
    }
  }
  if (options.children) {
    options.children.forEach((child) => el.appendChild(child));
  }
  return el;
}

/**
 * Utility to debounce a function call.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The debounce interval in ms.
 * @returns {Function} Debounced function.
 */
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Helper to get a value from localStorage with a fallback.
 * @param {string} key
 * @param {any} fallback
 * @returns {any}
 */
function getLocalStorage(key, fallback) {
  const value = localStorage.getItem(key);
  return value !== null ? value : fallback;
}

/**
 * Helper to DRY out fetchers.
 * @param {string} path - API path (e.g. '/status/server')
 * @param {function} onSuccess - Success callback
 * @param {HTMLElement} container - Loading element
 * @param {object} [opts] - Additional fetchData options
 * @returns {function} Fetcher function
 */
function makeFetcher(path, onSuccess, container, opts = {}) {
  return () =>
    fetchData(`${apiBasePath}${path}`, {
      successCallback: onSuccess,
      loadingElement: container,
      ...opts,
    });
}

// =====================
// API FETCH & RENDERING
// =====================
/**
 * Updates the API server status view in-place (no full redraw).
 * Only updates changed values.
 * @param {object} data - Data from the API.
 */
function updateApiServerView(data) {
  if (!apiStatusContent) return;
  // Try to find or create the status and version spans
  let statusSpan = apiStatusContent.querySelector(".api-status-value");
  let versionSpan = apiStatusContent.querySelector(".api-version-value");
  let messageDiv = apiStatusContent.querySelector(".api-status-message");
  if (!statusSpan || !versionSpan || !messageDiv) {
    // Initial render or structure changed, re-create
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
  const status = data.status || "unknown";
  const message = data.message || "";
  const version = data.version || APP_VERSION || "";
  const statusColor =
    status === "ok"
      ? CLASS_TEXT_GREEN_400
      : status === "error"
      ? CLASS_TEXT_RED_400
      : CLASS_TEXT_YELLOW_400;
  statusSpan.textContent = status;
  statusSpan.className = `api-status-value ${statusColor}`;
  versionSpan.textContent = version;
  messageDiv.textContent = message;
}

/**
 * Updates the application health view.
 * Fetches from /api/status/application and displays key health metrics.
 * @param {object} data - Health data with keys as metric names and values as status/counts.
 */
function updateApplicationHealthView(data) {
  try {
    if (!appHealthContent) return;
    appHealthContent.innerHTML = "";
    if (!data || typeof data !== "object") {
      appHealthContent.textContent = "No health data available.";
      return;
    }
    const entries = Object.entries(data).map(([key, value]) => {
      return `<div><span class="font-semibold">${key}:</span> <span>${value}</span></div>`;
    });
    appHealthContent.innerHTML = entries.join("");
  } catch (err) {
    console.error("Error in updateApplicationHealthView:", err);
    if (appHealthContent)
      appHealthContent.textContent = "Error rendering application health.";
  }
}

/**
 * Updates the CAN status view in-place (no full redraw).
 * Only updates changed interface rows.
 * @param {object} data - CAN status data, expected to have an 'interfaces' object.
 */
function updateCanStatusView(data) {
  if (!canStatusContent) return;
  if (!data || !data.interfaces || Object.keys(data.interfaces).length === 0) {
    canStatusContent.textContent = "No CAN interfaces found.";
    return;
  }
  // Use a table for stable row updates
  let table = canStatusContent.querySelector("table.can-status-table");
  if (!table) {
    table = document.createElement("table");
    table.className =
      "can-status-table min-w-full bg-gray-800 rounded-lg shadow text-sm";
    table.innerHTML = `
      <thead>
        <tr class="text-gray-300 border-b border-gray-700">
          <th class="px-4 py-2 text-left">Interface</th>
          <th class="px-4 py-2 text-left">State</th>
          <th class="px-4 py-2 text-left">RX</th>
          <th class="px-4 py-2 text-left">TX</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    canStatusContent.innerHTML = "";
    canStatusContent.appendChild(table);
  }
  const tbody = table.querySelector("tbody");
  const interfaces = data.interfaces;
  // Update or insert rows for each interface
  Object.entries(interfaces).forEach(([iface, stats]) => {
    let row = tbody.querySelector(`tr[data-iface='${iface}']`);
    if (!row) {
      row = document.createElement("tr");
      row.dataset.iface = iface;
      row.className = "border-b border-gray-700";
      row.innerHTML = `
        <td class="px-4 py-2 font-semibold">${iface}</td>
        <td class="px-4 py-2 can-state"></td>
        <td class="px-4 py-2 can-rx"></td>
        <td class="px-4 py-2 can-tx"></td>
      `;
      tbody.appendChild(row);
    }
    row.querySelector(".can-state").textContent = stats.state || "unknown";
    row.querySelector(".can-rx").textContent = stats.rx_packets || 0;
    row.querySelector(".can-tx").textContent = stats.tx_packets || 0;
  });
  // Remove rows for interfaces no longer present
  Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
    if (!(row.dataset.iface in interfaces)) row.remove();
  });
}

/**
 * Updates the specification text view.
 * @param {string} textData - The RVC specification text (JSON string).
 */
function updateSpecTextView(textData) {
  try {
    if (specContent) {
      specContent.textContent = textData;
    }
  } catch (err) {
    console.error("Error in updateSpecTextView:", err);
    if (specContent) specContent.textContent = "Error rendering spec content.";
  }
}

/**
 * Updates the specification metadata view.
 * @param {object} metadata - The RVC specification metadata.
 * @param {string} [metadata.version] - Specification version.
 * @param {string} [metadata.source] - Specification source/document URL.
 */
function updateSpecMetadataView(metadata) {
  try {
    if (specMetadataDiv) {
      if (
        metadata &&
        (metadata.version || metadata.source || metadata.spec_document)
      ) {
        // Check spec_document too
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

/**
 * Fetches and updates the API server status.
 */
const fetchApiStatus = makeFetcher(
  "/status/server",
  updateApiServerView,
  apiStatusContent,
  {
    errorCallback: (error) => {
      if (apiStatusContent)
        apiStatusContent.textContent = `Error loading API status: ${error.message}`;
    },
    showToastOnError: false,
  }
);

/**
 * Fetches and updates the application health status.
 */
const fetchAppHealth = makeFetcher(
  "/status/application",
  updateApplicationHealthView,
  appHealthContent,
  {
    errorCallback: (error) => {
      if (appHealthContent)
        appHealthContent.textContent = `Error loading app health: ${error.message}`;
    },
    showToastOnError: false,
  }
);

/**
 * Fetches and updates the CAN interface status.
 */
const fetchCanStatus = makeFetcher(
  "/can/status",
  updateCanStatusView,
  canStatusContent,
  {
    errorCallback: (error) => {
      if (canStatusContent)
        canStatusContent.textContent = `Error loading CAN status: ${error.message}`;
    },
    showToastOnError: false,
  }
);

/**
 * Fetches and displays the rvc.json specification content and metadata.
 * Fetches content from /api/config/rvc_spec (text)
 * Fetches metadata from /api/config/rvc_spec_metadata (JSON)
 */
function fetchSpecContent() {
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
    loadingElement: specContent, // Use specContent for its loading message
  });

  // Fetch Spec Metadata (JSON)
  fetchData(`${apiBasePath}/config/rvc_spec_metadata`, {
    responseType: "json",
    successCallback: updateSpecMetadataView,
    errorCallback: (error) => {
      console.error("Failed to fetch spec metadata:", error);
      if (specMetadataDiv)
        specMetadataDiv.textContent = "Error loading RVC spec metadata.";
      // Do not show a toast for metadata if the primary content toast is already shown
      // showToast("Failed to load RVC specification metadata.", "error");
    },
    // No separate loading element for metadata, or use specMetadataDiv if it has one
  });
}

// =====================
// WEBSOCKET HANDLERS
// =====================
/**
 * Appends a log message to the log stream.
 * @param {string} message - The raw log message string.
 */
function appendLogMessage(message) {
  if (!logStream || isLogPaused) return;

  const currentFilterLevel = logLevelSelect.value.toUpperCase();
  const searchTerm = logSearchInput.value.toLowerCase();

  // Updated regex for log format: 2025-05-10 23:49:28,569 DEBUG core_daemon.can_processing: ...
  const parts = message.match(
    /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (\w+) ([^:]+): (.*)/
  );
  let timestamp = "",
    level = "UNKNOWN",
    msgContent = message;

  if (parts) {
    timestamp = parts[1];
    level = parts[2].toUpperCase();
    msgContent = parts[4];
  }

  if (LOG_LEVELS[level] < LOG_LEVELS[currentFilterLevel]) {
    return;
  }
  if (searchTerm && !message.toLowerCase().includes(searchTerm)) {
    return;
  }

  const lineDiv = createDomElement("div", { className: "log-line" });
  const timeSpan = createDomElement("span", {
    className: "log-timestamp",
    textContent: timestamp,
  });
  const levelSpan = createDomElement("span", {
    className: `log-level-tag log-level-${level.toLowerCase()}`,
    textContent: level,
  });
  const msgSpan = createDomElement("span", {
    className: "log-message",
    textContent: msgContent,
  });

  // Add copy icon/button for the message
  const copyButton = createDomElement("button", {
    className: "log-copy-btn ml-2 text-gray-500 hover:text-gray-300",
    innerHTML: ICON_COPY + "Copy",
    attributes: { title: "Copy log message" },
  });
  copyButton.addEventListener("click", () => {
    copyToClipboard(message)
      .then(() => showToast("Log message copied!", "success", 1500))
      .catch((err) => {
        console.error("Failed to copy log message:", err);
        showToast("Failed to copy log message.", "error", 1500);
      });
  });

  lineDiv.appendChild(timeSpan);
  lineDiv.appendChild(levelSpan);
  lineDiv.appendChild(msgSpan);
  lineDiv.appendChild(copyButton);
  logStream.appendChild(lineDiv);

  // Auto-scroll if near the bottom
  if (
    logStream.scrollHeight - logStream.scrollTop - logStream.clientHeight <
    100
  ) {
    logStream.scrollTop = logStream.scrollHeight;
  }

  setLogsWaitingMessage(false); // Hide waiting message on new log
}

/**
 * Connects to the log WebSocket.
 */
function connectLogSocket() {
  if (!logSocketManager) {
    logSocketManager = new WebSocketManager(
      "/api/ws/logs",
      (data) => appendLogMessage(data),
      {
        onOpen: () => showToast("Log stream connected.", "info", 2000),
        onClose: () => showToast("Log stream disconnected.", "warning"),
        onError: () => showToast("Log stream error.", "error"),
        autoReconnect: true,
        reconnectInterval: 5000,
      }
    );
  }
}

/**
 * Disconnects the log WebSocket.
 */
function disconnectLogSocket() {
  if (logSocketManager) {
    logSocketManager.close();
    logSocketManager = null;
  }
}

// =====================
// UI EVENT HANDLERS & INIT
// =====================
/**
 * Navigates to the specified view.
 * @param {string} viewName - The name of the view to navigate to (e.g., "home", "lights").
 * @param {boolean} [isInitial=false] - True if this is the initial page load.
 */
function navigateToView(viewName, isInitial = false) {
  views.forEach((v) => v.classList.add(CLASS_HIDDEN));
  const targetView = document.getElementById(`${viewName}-view`);

  if (currentView === "lights") {
    handleLightsViewVisibility(false);
  }
  if (currentView === "home") {
    if (typeof cleanupHomeView === "function") cleanupHomeView();
  }
  // Clean up CAN Sniffer view when leaving it
  if (currentView === "can-sniffer") {
    if (typeof cleanupCanSnifferView === "function") cleanupCanSnifferView();
  }
  // Add cleanup for network map
  if (currentView === "network-map-view") cleanupNetworkMapView();

  if (targetView) {
    targetView.classList.remove(CLASS_HIDDEN);
    currentView = viewName;
    const mainHeading = targetView.querySelector("h1");
    if (mainHeading) {
      mainHeading.setAttribute("tabindex", "-1");
      mainHeading.focus();
    }
  } else {
    console.warn(`View "${viewName}" not found, defaulting to home.`);
    homeView?.classList.remove(CLASS_HIDDEN);
    currentView = "home";
  }

  navLinks.forEach((link) => {
    if (link.getAttribute(ATTR_DATA_VIEW) === currentView) {
      link.classList.add(CLASS_ACTIVE_NAV);
      link.setAttribute("aria-current", "page");
    } else {
      link.classList.remove(CLASS_ACTIVE_NAV);
      link.removeAttribute("aria-current");
    }
  });

  // Fetch data for the current view
  console.log(`Navigating to view: ${currentView}, initial: ${isInitial}`);
  switch (currentView) {
    case "home":
      if (typeof renderHomeView === "function") renderHomeView();
      break;
    case "lights":
      updateLightsView();
      handleLightsViewVisibility(true);
      break;
    case "mapping":
      renderMappingView();
      break;
    case "spec":
      fetchSpecView();
      break;
    case "unmapped":
      fetchUnmappedEntries();
      break;
    case "unknown-pgns":
      fetchUnknownPgns();
      break;
    case "can-sniffer":
      if (typeof renderCanSnifferView === "function") renderCanSnifferView();
      break;
    case "network-map":
      renderNetworkMapView();
      break;
    default:
      handleLightsViewVisibility(false);
      if (typeof cleanupCanSnifferView === "function") cleanupCanSnifferView();
      break;
  }
  // Close mobile sidebar if open
  if (
    window.innerWidth < MD_BREAKPOINT_PX &&
    sidebar &&
    !sidebar.classList.contains("-translate-x-full")
  ) {
    sidebar.classList.add("-translate-x-full");
  }
}

/**
 * Utility to toggle open/collapsed state for a panel (sidebar or drawer).
 * @param {Object} opts
 * @param {HTMLElement} opts.panel - The panel element (sidebar or drawer)
 * @param {HTMLElement} opts.content - The content element to show/hide (optional)
 * @param {HTMLElement} opts.mainContent - The main content element (for margin adjustment, optional)
 * @param {HTMLElement} opts.toggleButton - The button to update icon/text (optional)
 * @param {boolean} opts.expanded - True to expand, false to collapse
 * @param {Object} opts.styles - { expanded: {width, marginLeft, height, paddingBottom}, collapsed: {...} }
 * @param {Function} [opts.onExpand] - Callback after expand
 * @param {Function} [opts.onCollapse] - Callback after collapse
 * @param {HTMLElement} [opts.pinnedLogsContainer] - The pinned logs container element (optional)
 * @param {Object} [opts.pinnedLogsStyles] - Styles for pinned logs container (optional)
 */
function setPanelExpanded({
  panel,
  content,
  mainContent,
  toggleButton,
  expanded,
  styles,
  onExpand,
  onCollapse,
  pinnedLogsContainer,
  pinnedLogsStyles,
}) {
  if (!panel) return;

  panel.style.transition = "";
  if (mainContent) mainContent.style.transition = "";
  if (pinnedLogsContainer) pinnedLogsContainer.style.transition = "";

  if (styles.transition) {
    const _ = panel.offsetHeight;
    panel.style.transition = styles.transition;
    if (mainContent) {
      const __ = mainContent.offsetHeight;
      mainContent.style.transition = styles.transition;
    }
    if (
      pinnedLogsContainer &&
      pinnedLogsStyles &&
      pinnedLogsStyles.transition
    ) {
      const ___ = pinnedLogsContainer.offsetHeight;
      pinnedLogsContainer.style.transition = pinnedLogsStyles.transition;
    }
  }

  if (expanded) {
    if (styles.expanded.width) {
      panel.style.setProperty("width", styles.expanded.width, "important");
    }
    if (mainContent && styles.expanded.marginLeft) {
      mainContent.style.setProperty(
        "margin-left",
        styles.expanded.marginLeft,
        "important"
      );
    }
    if (
      pinnedLogsContainer &&
      pinnedLogsStyles &&
      pinnedLogsStyles.expanded &&
      pinnedLogsStyles.expanded.left
    ) {
      pinnedLogsContainer.style.left = pinnedLogsStyles.expanded.left;
    }
    if (panel && styles.expanded.height) {
      panel.style.height = styles.expanded.height;
    }
    if (mainContent && styles.expanded.paddingBottom) {
      mainContent.style.paddingBottom = styles.expanded.paddingBottom;
    }
    if (content) content.classList.remove(CLASS_HIDDEN);
    if (toggleButton && toggleButton.querySelector("i")) {
      toggleButton.querySelector("i").className =
        styles.expanded.iconClass || "";
    }
    if (toggleButton && toggleButton.querySelector("span")) {
      toggleButton.querySelector("span").textContent =
        styles.expanded.label || "";
    }
    if (toggleButton) toggleButton.setAttribute("aria-expanded", "true");
    if (onExpand) onExpand();
  } else {
    if (styles.collapsed.width) {
      panel.style.setProperty("width", styles.collapsed.width, "important");
    }
    if (mainContent && styles.collapsed.marginLeft) {
      mainContent.style.setProperty(
        "margin-left",
        styles.collapsed.marginLeft,
        "important"
      );
    }
    if (
      pinnedLogsContainer &&
      pinnedLogsStyles &&
      pinnedLogsStyles.collapsed &&
      pinnedLogsStyles.collapsed.left
    ) {
      pinnedLogsContainer.style.left = pinnedLogsStyles.collapsed.left;
    }
    if (panel && styles.collapsed.height) {
      panel.style.height = styles.collapsed.height;
    }
    if (mainContent && styles.collapsed.paddingBottom) {
      mainContent.style.paddingBottom = styles.collapsed.paddingBottom;
    }
    if (content) content.classList.add(CLASS_HIDDEN);
    if (toggleButton && toggleButton.querySelector("i")) {
      toggleButton.querySelector("i").className =
        styles.collapsed.iconClass || "";
    }
    if (toggleButton && toggleButton.querySelector("span")) {
      toggleButton.querySelector("span").textContent =
        styles.collapsed.label || "";
    }
    if (toggleButton) toggleButton.setAttribute("aria-expanded", "false");
    if (onCollapse) onCollapse();
  }
}

/**
 * Sets the visibility and state of the desktop sidebar.
 * Also adjusts the pinned logs container's left margin to align with the sidebar.
 * @param {boolean} expanded - True to expand the sidebar, false to collapse.
 */
function setDesktopSidebarVisible(expanded) {
  console.log(
    "[DEBUG] setDesktopSidebarVisible called with:",
    expanded,
    "Current isDesktopSidebarExpanded before change:",
    isDesktopSidebarExpanded
  );
  isDesktopSidebarExpanded = expanded;
  localStorage.setItem(DESKTOP_SIDEBAR_EXPANDED_KEY, expanded);

  if (
    !sidebar ||
    !mainContent ||
    !toggleSidebarDesktopButton ||
    !sidebarNavContent ||
    !pinnedLogsContainer
  ) {
    console.warn(
      "[SIDEBAR/LOGS] Missing one or more critical elements for setDesktopSidebarVisible or adjustPinnedLogsLayout"
    );
    return;
  }

  sidebar.setAttribute("aria-expanded", expanded.toString());
  toggleSidebarDesktopButton.setAttribute("aria-expanded", expanded.toString());

  const sidebarStyles = {
    transition: SIDEBAR_TRANSITION,
    expanded: {
      width: SIDEBAR_WIDTH_EXPANDED,
      marginLeft: SIDEBAR_WIDTH_EXPANDED,
      iconClass: "mdi mdi-chevron-left text-xl",
      label: "Collapse",
    },
    collapsed: {
      width: SIDEBAR_WIDTH_COLLAPSED,
      marginLeft: SIDEBAR_WIDTH_COLLAPSED,
      iconClass: "mdi mdi-chevron-right text-xl",
      label: "",
    },
  };

  let finalMainContentMarginLeftExpanded = sidebarStyles.expanded.marginLeft;
  let finalMainContentMarginLeftCollapsed = sidebarStyles.collapsed.marginLeft;

  if (window.innerWidth < MD_BREAKPOINT_PX) {
    finalMainContentMarginLeftExpanded = "0px";
    finalMainContentMarginLeftCollapsed = "0px";
  }

  const effectivePanelStyles = {
    transition: sidebarStyles.transition,
    expanded: {
      ...sidebarStyles.expanded,
      marginLeft: finalMainContentMarginLeftExpanded,
    },
    collapsed: {
      ...sidebarStyles.collapsed,
      marginLeft: finalMainContentMarginLeftCollapsed,
    },
  };

  const pinnedLogsStylesDef = {
    transition: "left 0.3s cubic-bezier(0.4,0,0.2,1)",
    expanded: {
      left: SIDEBAR_WIDTH_EXPANDED,
    },
    collapsed: {
      left: SIDEBAR_WIDTH_COLLAPSED,
    },
  };

  setPanelExpanded({
    panel: sidebar,
    content: sidebarNavContent,
    mainContent,
    toggleButton: toggleSidebarDesktopButton,
    expanded,
    styles: effectivePanelStyles,
    pinnedLogsContainer,
    pinnedLogsStyles: pinnedLogsStylesDef,
    onExpand: () => {
      toggleSidebarDesktopButton.innerHTML = `<span class="mdi ${sidebarStyles.expanded.iconClass} mr-0"></span><span class="ml-2">${sidebarStyles.expanded.label}</span>`;
      sidebar.classList.remove("sidebar-collapsed-hoverable");
      sidebarNavContent.classList.remove(CLASS_HIDDEN);
      sidebar
        .querySelectorAll(".nav-link span")
        .forEach((span) => span.classList.remove(CLASS_HIDDEN));
      sidebar
        .querySelectorAll(".nav-link i")
        .forEach((icon) => icon.classList.add("mr-2"));
      adjustPinnedLogsLayout();
    },
    onCollapse: () => {
      toggleSidebarDesktopButton.innerHTML = `<span class="mdi ${sidebarStyles.collapsed.iconClass}"></span><span class="ml-2">${sidebarStyles.collapsed.label}</span>`;
      sidebar.classList.add("sidebar-collapsed-hoverable");
      sidebarNavContent.classList.add(CLASS_HIDDEN);
      sidebar
        .querySelectorAll(".nav-link span")
        .forEach((span) => span.classList.add(CLASS_HIDDEN));
      sidebar
        .querySelectorAll(".nav-link i")
        .forEach((icon) => icon.classList.remove("mr-2"));
      adjustPinnedLogsLayout();
    },
  });
  adjustPinnedLogsLayout();
}

/**
 * Enhances sidebar collapse/expand/hover behavior.
 * - Click-to-expand on collapsed sidebar (desktop)
 * - Robust state save/restore in localStorage
 * - Maintains ARIA and accessibility
 */
function setupSidebarCollapseExpand() {
  if (
    !sidebar ||
    !mainContent ||
    !toggleSidebarDesktopButton ||
    !sidebarNavContent
  ) {
    console.warn(
      "[SIDEBAR_SETUP] Missing critical elements for setupSidebarCollapseExpand. Listeners not attached."
    );
    return;
  }

  sidebar.style.overflowX = "hidden";

  sidebar.addEventListener("click", (e) => {
    console.log(
      "[SIDEBAR_SETUP] Sidebar area clicked. isDesktopSidebarExpanded:",
      isDesktopSidebarExpanded,
      "e.target:",
      e.target,
      "sidebar element:",
      sidebar
    );
    if (
      window.innerWidth >= MD_BREAKPOINT_PX &&
      !isDesktopSidebarExpanded &&
      e.target === sidebar
    ) {
      console.log("[SIDEBAR_SETUP] Expanding sidebar via area click.");
      setDesktopSidebarVisible(true);
    } else {
      console.log(
        "[SIDEBAR_SETUP] Sidebar area click - conditions for expansion NOT MET or click was on a child. Conditions:",
        {
          isDesktop: window.innerWidth >= MD_BREAKPOINT_PX,
          isCollapsed: !isDesktopSidebarExpanded,
          targetIsSidebarItself: e.target === sidebar,
        }
      );
    }
  });

  toggleSidebarDesktopButton.addEventListener("click", (e) => {
    console.log(
      "[SIDEBAR_SETUP] Toggle button clicked. Current isDesktopSidebarExpanded:",
      isDesktopSidebarExpanded,
      "e.target:",
      e.target
    );
    e.stopPropagation();
    setDesktopSidebarVisible(!isDesktopSidebarExpanded);
  });

  if (closeSidebarButton) {
    closeSidebarButton.addEventListener("click", (e) => {
      if (sidebar) {
        console.log("[SIDEBAR_SETUP] Mobile close button clicked.");
        e.stopPropagation();
        sidebar.classList.add("-translate-x-full");
        sidebar.setAttribute(ARIA_HIDDEN, "true");
      }
    });
  }
}

/**
 * Adjusts the pinned logs drawer position so it does not cover the sidebar.
 * Sets the left offset to match the sidebar width (expanded/collapsed) on desktop.
 * On mobile, sets left to 0.
 * Should be called on sidebar expand/collapse, window resize, and after toggling logs.
 */
function adjustPinnedLogsLayout() {
  if (!pinnedLogsContainer || !sidebar || !mainContent) {
    console.warn(
      "[LOGS] Missing elements for adjustPinnedLogsLayout. Cannot adjust layout."
    );
    return;
  }

  const logsHeaderHeight = pinnedLogsHeader ? pinnedLogsHeader.offsetHeight : 0;
  const currentPinnedLogsHeight = pinnedLogsContainer.offsetHeight;

  if (window.innerWidth < MD_BREAKPOINT_PX) {
    pinnedLogsContainer.style.left = "0px";
    pinnedLogsContainer.style.right = "0px";
    mainContent.style.paddingBottom = `${currentPinnedLogsHeight}px`;
  } else {
    pinnedLogsContainer.style.right = "0px";
    mainContent.style.paddingBottom = `${currentPinnedLogsHeight}px`;
  }

  if (pinnedLogsContent) {
    pinnedLogsContent.style.height = `calc(100% - ${logsHeaderHeight}px)`;
  }
}

/**
 * Applies the selected theme to the body.
 * @param {string} themeName - The name of the theme to apply.
 */
function applyTheme(themeName) {
  if (!VALID_THEMES.includes(themeName)) {
    console.warn(
      `Invalid theme: ${themeName}. Defaulting to ${DEFAULT_THEME}.`
    );
    themeName = DEFAULT_THEME;
  }
  document.body.className = document.body.className.replace(/theme-\S+/g, ""); // Remove old theme
  document.body.classList.add(`theme-${themeName}`);
  localStorage.setItem(SELECTED_THEME_KEY, themeName);
  currentTheme = themeName;
  console.log(`Theme applied: ${themeName}`);
}

/**
 * Sets up event listeners for bulk light control buttons (All/Interior/Exterior On/Off).
 * Each button fetches all lights, filters by group/area, and sends control commands to each.
 */
function setupBulkLightControlButtons() {
  const controls = [
    {
      id: "btn-all-on",
      name: "All Lights On",
      filter: () => true,
      command: { command: "set", state: "on" },
    },
    {
      id: "btn-all-off",
      name: "All Lights Off",
      filter: () => true,
      command: { command: "set", state: "off" },
    },
    {
      id: "btn-interior-on",
      name: "Interior Lights On",
      filter: (entity) => (entity.groups || []).includes("interior"),
      command: { command: "set", state: "on" },
    },
    {
      id: "btn-interior-off",
      name: "Interior Lights Off",
      filter: (entity) => (entity.groups || []).includes("interior"),
      command: { command: "set", state: "off" },
    },
    {
      id: "btn-exterior-on",
      name: "Exterior Lights On",
      filter: (entity) => (entity.groups || []).includes("exterior"),
      command: { command: "set", state: "on" },
    },
    {
      id: "btn-exterior-off",
      name: "Exterior Lights Off",
      filter: (entity) => (entity.groups || []).includes("exterior"),
      command: { command: "set", state: "off" },
    },
  ];
  controls.forEach((control) => {
    const button = document.getElementById(control.id);
    if (!button) return;
    button.addEventListener("click", async () => {
      const originalHTML = button.innerHTML;
      button.disabled = true;
      button.innerHTML =
        '<i class="mdi mdi-loading mdi-spin mr-2"></i>Processing...';
      try {
        let lights = null;
        await new Promise((resolve) => {
          fetchData(`${apiBasePath}/entities?device_type=light`, {
            successCallback: (resp) => {
              lights = resp;
              resolve();
            },
            errorCallback: (err) => {
              showToast("Failed to fetch lights", "error");
              resolve();
            },
            showToastOnError: false,
          });
        });
        if (!lights) return;
        const entities = Object.values(lights).filter(
          (entity) => entity.device_type === "light" && control.filter(entity)
        );
        if (entities.length === 0) {
          showToast(`No lights found for ${control.name}.`, "warning");
          return;
        }
        let successCount = 0;
        let errorCount = 0;
        for (const entity of entities) {
          const res = await callLightService(
            entity.entity_id,
            control.command.command,
            control.command
          );
          if (res) successCount++;
          else errorCount++;
        }
        if (errorCount > 0) {
          showToast(
            `${control.name}: ${successCount} succeeded, ${errorCount} failed.`,
            errorCount === entities.length ? "error" : "warning"
          );
        } else {
          showToast(
            `${control.name}: ${successCount} lights commanded.`,
            "success"
          );
        }
      } catch (error) {
        showToast(
          `Failed to execute ${control.name}. Error: ${error.message}`,
          "error"
        );
        console.error(`Command ${control.name} failed:`, error);
      } finally {
        button.disabled = false;
        button.innerHTML = originalHTML;
      }
    });
  });
}

/**
 * Enables drag-to-resize for the pinned logs panel, with persistent height in localStorage.
 * Restores height and open/closed state on load, and clamps to min/max values.
 * Adds comprehensive comments and JSDoc.
 */
function setupPinnedLogsResizablePanel() {
  const PINNED_LOGS_OPEN_KEY = "pinnedLogsOpen";
  const PINNED_LOGS_HEIGHT_KEY = "pinnedLogsHeight";
  const COLLAPSED_LOGS_HEIGHT = "3rem";
  const DEFAULT_EXPANDED_LOGS_HEIGHT_VH = 30;
  const MIN_LOGS_PANEL_HEIGHT_PX = 80;
  const MAX_LOGS_PANEL_HEIGHT_VH_PERCENT = 80;
  let currentExpandedLogsHeight = `${DEFAULT_EXPANDED_LOGS_HEIGHT_VH}vh`;
  let isResizingLogs = false;
  let resizeRafId = null;
  let pendingResizeHeightPx = 0;
  let originalContainerTransition = "";

  if (
    !pinnedLogsContainer ||
    !pinnedLogsResizeHandle ||
    !pinnedLogsContent ||
    !mainContent
  )
    return;

  const savedIsOpen = localStorage.getItem(PINNED_LOGS_OPEN_KEY) === "true";
  const savedHeight = localStorage.getItem(PINNED_LOGS_HEIGHT_KEY);
  if (savedHeight) {
    let heightNum = parseFloat(savedHeight);
    const unit = savedHeight.replace(/[\d.-]/g, "");
    if (unit === "px") {
      heightNum = Math.max(
        MIN_LOGS_PANEL_HEIGHT_PX,
        Math.min(
          heightNum,
          window.innerHeight * (MAX_LOGS_PANEL_HEIGHT_VH_PERCENT / 100)
        )
      );
      currentExpandedLogsHeight = `${heightNum}px`;
    } else if (unit === "vh") {
      heightNum = Math.max(
        (MIN_LOGS_PANEL_HEIGHT_PX / window.innerHeight) * 100,
        Math.min(heightNum, MAX_LOGS_PANEL_HEIGHT_VH_PERCENT)
      );
      currentExpandedLogsHeight = `${heightNum}vh`;
    } else {
      currentExpandedLogsHeight = `${DEFAULT_EXPANDED_LOGS_HEIGHT_VH}vh`;
    }
  }

  const originalTransition = pinnedLogsContainer.style.transition;
  pinnedLogsContainer.style.transition = "none";
  setPinnedLogsState(savedIsOpen, currentExpandedLogsHeight);
  setTimeout(() => {
    pinnedLogsContainer.style.transition =
      originalTransition || "height 0.3s ease-in-out";
  }, 50);

  function setPinnedLogsState(isOpen, height) {
    localStorage.setItem("pinnedLogsOpen", isOpen);
    if (isOpen && height) {
      localStorage.setItem("pinnedLogsHeight", height);
      currentExpandedLogsHeight = height;
    }
    setPanelExpanded({
      panel: pinnedLogsContainer,
      content: pinnedLogsContent,
      mainContent,
      toggleButton: togglePinnedLogsButton,
      expanded: isOpen,
      styles: {
        transition:
          "height 0.3s cubic-bezier(0.4,0,0.2,1), padding-bottom 0.3s cubic-bezier(0.4,0,0.2,1)",
        expanded: {
          height: currentExpandedLogsHeight,
          paddingBottom: currentExpandedLogsHeight,
          iconClass: "mdi mdi-chevron-down text-2xl",
          label: "",
        },
        collapsed: {
          height: "3rem",
          paddingBottom: "3rem",
          iconClass: "mdi mdi-chevron-up text-2xl",
          label: "",
        },
      },
      onExpand: () => {
        connectLogSocket();
      },
      onCollapse: () => {
        disconnectLogSocket();
      },
    });
    adjustPinnedLogsLayout();
  }

  pinnedLogsResizeHandle.addEventListener("mousedown", (e) => {
    if (pinnedLogsContent.classList.contains(CLASS_HIDDEN)) return;
    e.preventDefault();
    isResizingLogs = true;
    const startY = e.clientY;
    const startHeight = pinnedLogsContainer.offsetHeight;
    originalContainerTransition = pinnedLogsContainer.style.transition;
    pinnedLogsContainer.style.transition = "none";
    document.body.style.userSelect = "none";
    document.body.style.cursor = "ns-resize";
    const onMouseMove = (moveEvent) => {
      if (!isResizingLogs) return;
      const dy = startY - moveEvent.clientY;
      let newHeightPx = startHeight + dy;
      const maxHeightPx =
        window.innerHeight * (MAX_LOGS_PANEL_HEIGHT_VH_PERCENT / 100);
      newHeightPx = Math.max(
        MIN_LOGS_PANEL_HEIGHT_PX,
        Math.min(newHeightPx, maxHeightPx)
      );
      pendingResizeHeightPx = newHeightPx;
      if (resizeRafId === null) {
        resizeRafId = requestAnimationFrame(() => {
          currentExpandedLogsHeight = `${pendingResizeHeightPx}px`;
          pinnedLogsContainer.style.height = currentExpandedLogsHeight;
          pinnedLogsContent.style.height = `calc(${currentExpandedLogsHeight} - ${COLLAPSED_LOGS_HEIGHT})`;
          mainContent.style.paddingBottom = currentExpandedLogsHeight;
          resizeRafId = null;
        });
      }
    };
    const onMouseUp = () => {
      if (isResizingLogs) {
        isResizingLogs = false;
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        if (resizeRafId !== null) {
          cancelAnimationFrame(resizeRafId);
          resizeRafId = null;
        }
        currentExpandedLogsHeight = `${pendingResizeHeightPx}px`;
        pinnedLogsContainer.style.height = currentExpandedLogsHeight;
        pinnedLogsContent.style.height = `calc(${currentExpandedLogsHeight} - ${COLLAPSED_LOGS_HEIGHT})`;
        mainContent.style.paddingBottom = currentExpandedLogsHeight;
        localStorage.setItem(PINNED_LOGS_HEIGHT_KEY, currentExpandedLogsHeight);
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
        pinnedLogsContainer.style.transition =
          originalContainerTransition || "height 0.3s ease-in-out";
      }
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });

  if (togglePinnedLogsButton && pinnedLogsHeader) {
    togglePinnedLogsButton.addEventListener("click", () => {
      const isOpen = !pinnedLogsContent.classList.contains(CLASS_HIDDEN);
      setPinnedLogsState(!isOpen, currentExpandedLogsHeight);
    });
    pinnedLogsHeader.addEventListener("click", (e) => {
      if (
        e.target === pinnedLogsHeader ||
        (pinnedLogsHeader.contains(e.target) && e.target.tagName !== "BUTTON")
      ) {
        const isOpen = !pinnedLogsContent.classList.contains(CLASS_HIDDEN);
        setPinnedLogsState(!isOpen, currentExpandedLogsHeight);
      }
    });
  }

  window.addEventListener("resize", () => {
    const maxHeightPx =
      window.innerHeight * (MAX_LOGS_PANEL_HEIGHT_VH_PERCENT / 100);
    let heightNum = parseFloat(currentExpandedLogsHeight);
    if (currentExpandedLogsHeight.endsWith("px")) {
      heightNum = Math.max(
        MIN_LOGS_PANEL_HEIGHT_PX,
        Math.min(heightNum, maxHeightPx)
      );
      currentExpandedLogsHeight = `${heightNum}px`;
    } else if (currentExpandedLogsHeight.endsWith("vh")) {
      heightNum = Math.max(
        (MIN_LOGS_PANEL_HEIGHT_PX / window.innerHeight) * 100,
        Math.min(heightNum, MAX_LOGS_PANEL_HEIGHT_VH_PERCENT)
      );
      currentExpandedLogsHeight = `${heightNum}vh`;
    }
    if (!pinnedLogsContent.classList.contains(CLASS_HIDDEN)) {
      pinnedLogsContainer.style.height = currentExpandedLogsHeight;
      pinnedLogsContent.style.height = `calc(${currentExpandedLogsHeight} - ${COLLAPSED_LOGS_HEIGHT})`;
      mainContent.style.paddingBottom = currentExpandedLogsHeight;
    }
    adjustPinnedLogsLayout();
  });
}

/**
 * Shows or hides the "Waiting for logs..." message in the pinned logs panel.
 * @param {boolean} show - Whether to show the waiting message.
 */
function setLogsWaitingMessage(show) {
  const logsWaitingMessage = document.getElementById("logs-waiting-message");
  if (!logsWaitingMessage) return;
  if (show) {
    logsWaitingMessage.classList.remove(CLASS_HIDDEN);
    if (logLevelSelect) logLevelSelect.disabled = false;
    if (logSearchInput) logSearchInput.disabled = false;
    if (logPauseButton) logPauseButton.disabled = false;
    if (logClearButton) logClearButton.disabled = false;
  } else {
    logsWaitingMessage.classList.add(CLASS_HIDDEN);
  }
}

if (logClearButton)
  logClearButton.addEventListener("click", () => {
    if (logStream) logStream.innerHTML = "";
    if (
      logSocketManager &&
      logSocketManager.readyState === WebSocket.OPEN &&
      pinnedLogsContent &&
      !pinnedLogsContent.classList.contains(CLASS_HIDDEN)
    ) {
      setLogsWaitingMessage(true);
    }
  });
if (logLevelSelect)
  logLevelSelect.addEventListener("change", () => {
    if (logStream) logStream.innerHTML = "";
    if (
      logSocketManager &&
      logSocketManager.readyState === WebSocket.OPEN &&
      pinnedLogsContent &&
      !pinnedLogsContent.classList.contains(CLASS_HIDDEN)
    ) {
      setLogsWaitingMessage(true);
    }
  });
if (logSearchInput)
  logSearchInput.addEventListener(
    "input",
    debounce(() => {
      if (logStream) logStream.innerHTML = "";
      if (
        logSocketManager &&
        logSocketManager.readyState === WebSocket.OPEN &&
        pinnedLogsContent &&
        !pinnedLogsContent.classList.contains(CLASS_HIDDEN)
      ) {
        setLogsWaitingMessage(true);
      }
    }, 300)
  );

// =====================
// FOOTER STATUS RENDERING
// =====================

const footerApiServer = document.getElementById("footerApiServer");
const footerHealthStatus = document.getElementById("footerHealthStatus");
const footerAppVersion = document.getElementById("footerAppVersion");
const footerVersionStatus = document.getElementById("footerVersionStatus");

// Fetch the latest version from the backend API instead of GitHub directly
async function fetchLatestVersion() {
  try {
    const resp = await fetch(`${apiBasePath}/status/latest_release`);
    if (!resp.ok) throw new Error("Failed to fetch latest version");
    const data = await resp.json();
    return data.latest_version || null;
  } catch (e) {
    return null;
  }
}

function updateFooterStatus({ version, status, message }) {
  if (footerApiServer) {
    footerApiServer.textContent = `API: ${window.location.origin}`;
  }
  if (footerHealthStatus) {
    let icon = status === "ok" ? "🟢" : status === "error" ? "🔴" : "🟡";
    let label = status || "unknown";
    let msg = status !== "ok" && message ? ` | ${message}` : "";
    footerHealthStatus.innerHTML = `<span>${icon} ${label}${msg}</span>`;
    footerHealthStatus.title = status !== "ok" && message ? message : "";
  }
  if (footerAppVersion) {
    footerAppVersion.textContent = version
      ? `v${version}`
      : APP_VERSION
      ? `v${APP_VERSION}`
      : "";
  }
}

async function updateFooterVersionStatus(currentVersion) {
  if (!footerVersionStatus) return;
  const latest = await fetchLatestVersion();
  if (!latest) {
    footerVersionStatus.textContent = "";
    return;
  }
  if (currentVersion === latest) {
    footerVersionStatus.innerHTML =
      '<span class="text-green-400">(Up to date)</span>';
  } else {
    const changelogUrl = `https://github.com/holtrop/rvc2api/blob/v${latest}/CHANGELOG.md`;
    footerVersionStatus.innerHTML = `(<a href="${changelogUrl}" target="_blank" class="text-yellow-400 underline hover:text-yellow-300">v${latest} Available</a>)`;
  }
}

async function fetchAndUpdateFooterStatus() {
  try {
    const resp = await fetch(`${apiBasePath}/status/server`);
    if (!resp.ok) throw new Error("API error");
    const data = await resp.json();
    updateFooterStatus(data);
    await updateFooterVersionStatus(data.version || APP_VERSION);
  } catch (err) {
    updateFooterStatus({ status: "error", message: "API unreachable" });
    if (footerVersionStatus) footerVersionStatus.textContent = "";
  }
}

// Check for updates every hour instead of every 10 seconds to avoid rate limiting
setInterval(fetchAndUpdateFooterStatus, 3600000);
document.addEventListener("DOMContentLoaded", fetchAndUpdateFooterStatus);

// =====================
// APP INITIALIZATION
// =====================
/**
 * Initializes the application.
 * Sets up event listeners, loads initial state, and fetches data for the default view.
 */
function initializeApp() {
  APP_VERSION = document.body.dataset.appVersion || null;
  if (appVersionDisplay) {
    if (APP_VERSION && APP_VERSION !== "N/A") {
      appVersionDisplay.textContent = `v${APP_VERSION}`;
      appVersionDisplay.style.display = "inline";
    } else {
      appVersionDisplay.textContent = "";
      appVersionDisplay.style.display = "none";
    }
  }

  const savedTheme = localStorage.getItem(SELECTED_THEME_KEY);
  applyTheme(savedTheme || DEFAULT_THEME);

  const savedSidebarState = localStorage.getItem(DESKTOP_SIDEBAR_EXPANDED_KEY);
  setDesktopSidebarVisible(
    savedSidebarState === null ? true : savedSidebarState === "true"
  );

  if (mobileMenuButton && sidebar) {
    mobileMenuButton.addEventListener("click", () => {
      sidebar.classList.remove("-translate-x-full");
      sidebar.setAttribute(ARIA_HIDDEN, "false");
    });
  }

  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const viewName = link.getAttribute(ATTR_DATA_VIEW);
      if (viewName) {
        navigateToView(viewName);
      }
    });
  });

  let initialView = "home";
  navigateToView(initialView, true);

  if (logPauseButton) {
    logPauseButton.addEventListener("click", () => {
      isLogPaused = true;
      logPauseButton.disabled = true;
      if (logResumeButton) logResumeButton.disabled = false;
      showToast("Log stream paused.", "info", 1500);
    });
  }
  if (logResumeButton) {
    logResumeButton.disabled = true;
    logResumeButton.addEventListener("click", () => {
      isLogPaused = false;
      if (logPauseButton) logPauseButton.disabled = false;
      logResumeButton.disabled = true;
      if (logStream) logStream.scrollTop = logStream.scrollHeight;
      showToast("Log stream resumed.", "info", 1500);
    });
  }

  setupBulkLightControlButtons();
  setupPinnedLogsResizablePanel();
  setupSidebarCollapseExpand();

  window.addEventListener(
    "resize",
    debounce(() => {
      if (typeof isDesktopSidebarExpanded === "boolean") {
        setDesktopSidebarVisible(isDesktopSidebarExpanded);
      }
    }, 100)
  );

  console.log(`rvc2api UI Initialized. Version: ${APP_VERSION}`);
}

// Initialize custom theme dropdown
let patchedApplyTheme = null;
if (typeof initThemeDropdown === "function") {
  patchedApplyTheme = initThemeDropdown(applyTheme, window.SELECTED_THEME_KEY);
  if (patchedApplyTheme) {
    window.applyTheme = patchedApplyTheme;
  }
}

// On page load, after applying the saved theme, also update the dropdown label and highlight
if (typeof window.applyTheme === "function") {
  window.applyTheme(localStorage.getItem(SELECTED_THEME_KEY) || DEFAULT_THEME);
}

document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
});
