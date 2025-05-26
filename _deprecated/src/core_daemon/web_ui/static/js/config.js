/**
 * config.js - Configuration and constants for rvc2api Web UI
 *
 * Provides theme names, color tokens, refresh intervals, and other app-wide constants.
 *
 * Author: Ryan Holt
 * Last updated: 2025-05-12
 */

// Theme names and keys
export const VALID_THEMES = [
  "default",
  "dark",
  "light",
  "catppuccin-mocha",
  "catppuccin-latte",
  "nord-dark",
  "nord-light",
  "gruvbox-dark",
  "gruvbox-light",
];
export const DEFAULT_THEME = "catppuccin-mocha";
export const SELECTED_THEME_KEY = "selectedTheme";
export const DESKTOP_SIDEBAR_EXPANDED_KEY = "desktopSidebarExpanded";

// Refresh intervals (ms)
export const LOG_WEBSOCKET_RECONNECT_INTERVAL = 5000;
export const CAN_STATUS_REFRESH_INTERVAL = 10000;
export const API_STATUS_REFRESH_INTERVAL = 30000;
export const APP_HEALTH_REFRESH_INTERVAL = 30000;

// Tailwind breakpoints and class names
export const MD_BREAKPOINT_PX = 768;
export const CLASS_HIDDEN = "hidden";
export const CLASS_ACTIVE_NAV = "active-nav";
export const CLASS_LIGHT_ON = "light-on";
export const CLASS_LIGHT_OFF = "light-off";
export const THEME_CLASSES = VALID_THEMES.map((t) => `theme-${t}`);
export const ATTR_DATA_VIEW = "data-view";
export const ARIA_HIDDEN = "aria-hidden";

// WebSocket URLs
export const entitySocketUrl = "/api/ws";

// Sidebar and transition constants
export const SIDEBAR_WIDTH_EXPANDED = "16rem";
export const SIDEBAR_WIDTH_COLLAPSED = "4rem";
export const SIDEBAR_TRANSITION =
  "width 0.3s cubic-bezier(0.4,0,0.2,1), margin-left 0.3s cubic-bezier(0.4,0,0.2,1)";

// Log levels
export const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  CRITICAL: 4,
};
export const LOG_LEVEL_NAMES = Object.keys(LOG_LEVELS);

// Pinned logs drawer
export const PINNED_LOGS_COLLAPSED_HEIGHT_REM = "3rem";
export const PINNED_LOGS_EXPANDED_HEIGHT_REM = "20rem";
export const PINNED_LOGS_EXPANDED_ICON = "mdi mdi-chevron-down text-2xl";
export const PINNED_LOGS_COLLAPSED_ICON = "mdi mdi-chevron-up text-2xl";

// Icon SVGs and color classes
export const ICON_COPY = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 inline-block mr-1"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 4.625a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0z" /></svg>`;
export const ICON_LOADING_SPINNER = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
export const CLASS_TEXT_GREEN_400 = "text-green-400";
export const CLASS_TEXT_RED_400 = "text-red-400";
export const CLASS_TEXT_YELLOW_400 = "text-yellow-400";
export const apiBasePath = "/api";
