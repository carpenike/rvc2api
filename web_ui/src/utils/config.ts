// Environment configuration and application-wide settings

// API base URL - this will automatically handle development vs production environments
export const API_BASE_URL = import.meta.env.PROD
  ? "/api" // In production, use relative path for API (assuming same domain)
  : import.meta.env.VITE_API_URL || "http://localhost:8000/api"; // Dev default

// WebSocket URL
export const WS_URL = import.meta.env.PROD
  ? "/api/ws" // In production, use relative path for WebSocket
  : import.meta.env.VITE_WS_URL || "ws://localhost:8000/api/ws"; // Dev default

// App version
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || "0.1.0";

// Feature flags
export const FEATURES = {
  DARK_MODE: true,
  CAN_SNIFFER: true,
  NETWORK_MAP: true
};

// Theme settings
export const DEFAULT_THEME = "dark";

// Polling intervals (in milliseconds)
export const POLLING_INTERVALS = {
  HEALTH_CHECK: 60000, // 1 minute
  CAN_STATUS: 10000 // 10 seconds
};

// Pagination defaults
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20
};

// Local storage keys
export const STORAGE_KEYS = {
  THEME: "rvc2api-theme",
  USER_SETTINGS: "rvc2api-user-settings"
};

// Date formatting
export const DATE_FORMAT = {
  TIMESTAMP: "yyyy-MM-dd HH:mm:ss",
  DATE_ONLY: "yyyy-MM-dd"
};
