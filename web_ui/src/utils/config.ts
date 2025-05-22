// Environment configuration and application-wide settings

// API base URL - handles development vs production environments
type ApiBaseUrl = string;
export const API_BASE_URL: ApiBaseUrl = import.meta.env.PROD
  ? "/api" // In production, use relative path for API (assuming same domain)
  : import.meta.env.VITE_API_URL || "http://localhost:8000/api"; // Dev default

// WebSocket URL helper - builds correct URL for dev and prod
export function getWebSocketUrl(path: string): string {
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}${path}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}

// App version (from env or fallback)
export const APP_VERSION: string = import.meta.env.VITE_APP_VERSION || "0.1.0";

// Feature flags (add new features here as needed)
export interface FeaturesConfig {
  DARK_MODE: boolean;
  CAN_SNIFFER: boolean;
  NETWORK_MAP: boolean;
}
export const FEATURES: FeaturesConfig = {
  DARK_MODE: true,
  CAN_SNIFFER: true,
  NETWORK_MAP: true
};

// Theme-adaptive color variables (semantic roles mapped to CSS variables)
export const THEME_COLORS: Record<string, string> = {
  background: "var(--color-bg)",
  backgroundAlt: "var(--color-bg-alt)",
  surface: "var(--color-surface)",
  surfaceAlt: "var(--color-surface-alt)",
  border: "var(--color-border)",
  text: "var(--color-text)",
  textSecondary: "var(--color-text-secondary)",
  accent: "var(--color-accent)",
  accentAlt: "var(--color-accent-alt)",
  error: "var(--color-error)",
  warning: "var(--color-warning)",
  success: "var(--color-success)",
  info: "var(--color-info)"
};

/**
 * Get a theme-adaptive color by semantic name.
 * @param name Semantic color role (e.g., 'background', 'accent')
 * @returns CSS variable string for use in style or className
 */
export function getThemeColor(name: keyof typeof THEME_COLORS): string {
  return THEME_COLORS[name] || "var(--color-bg)";
}

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

// Date formatting patterns (for use with date-fns or similar)
export const DATE_FORMAT = {
  TIMESTAMP: "yyyy-MM-dd HH:mm:ss",
  DATE_ONLY: "yyyy-MM-dd"
};

// Only log config in development for debugging
if (import.meta.env.DEV) {
  console.log("Environment config:", {
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_WS_URL: import.meta.env.VITE_WS_URL,
    DEV: import.meta.env.DEV,
    PROD: import.meta.env.PROD
  });
  console.log("Using WebSocket URL:", getWebSocketUrl("/api/ws"));
}
