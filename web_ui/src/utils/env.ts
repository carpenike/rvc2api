/**
 * Environment variable utilities that work in both Vite (browser) and Jest (Node) contexts.
 *
 * This abstraction avoids TypeScript compilation errors with import.meta.env in Jest
 * by using process.env when running in test environments.
 */

interface Environment {
  VITE_API_BASE_URL?: string;
  VITE_WS_URL?: string;
  VITE_APP_VERSION?: string;
  MODE?: string;
  PROD?: boolean;
  DEV?: boolean;
  SSR?: boolean;
}

/**
 * Get environment variables with proper fallbacks for test and runtime contexts.
 *
 * @returns Environment object with consistent interface across contexts
 */
export const getEnv = (): Environment => {
  // Use process.env in test environment (Jest) or when process is available
  if (typeof process !== "undefined" && (process.env.JEST_WORKER_ID || process.env.NODE_ENV === "test")) {
    return {
      VITE_API_BASE_URL: process.env.VITE_API_BASE_URL,
      VITE_WS_URL: process.env.VITE_WS_URL,
      VITE_APP_VERSION: process.env.VITE_APP_VERSION,
      MODE: process.env.NODE_ENV || "test",
      PROD: process.env.NODE_ENV === "production",
      DEV: process.env.NODE_ENV === "development",
      SSR: false
    };
  }

  // In browser environments, try to access Vite environment variables
  // This uses runtime detection to avoid TypeScript compilation issues
  try {
    // Check if we're in a Vite environment by looking for known globals
    const globalEnv = (globalThis as { __VITE_ENV__?: Environment }).__VITE_ENV__;
    if (globalEnv) {
      return globalEnv;
    }

    // Fallback for runtime Vite environment access
    // These will be replaced by Vite's define plugin in production builds
    const windowGlobal = typeof window !== "undefined" ? window : globalThis;
    const viteEnv = windowGlobal as {
      VITE_API_BASE_URL?: string;
      VITE_WS_URL?: string;
      VITE_APP_VERSION?: string;
      MODE?: string;
      PROD?: boolean;
      DEV?: boolean;
    };

    if (viteEnv.VITE_API_BASE_URL !== undefined || viteEnv.MODE !== undefined) {
      return {
        VITE_API_BASE_URL: viteEnv.VITE_API_BASE_URL,
        VITE_WS_URL: viteEnv.VITE_WS_URL,
        VITE_APP_VERSION: viteEnv.VITE_APP_VERSION,
        MODE: viteEnv.MODE || "development",
        PROD: viteEnv.PROD || false,
        DEV: viteEnv.DEV !== false,
        SSR: false
      };
    }
  } catch {
    // Ignore errors accessing environment in Jest
  }

  // Fallback for edge cases
  return {
    VITE_API_BASE_URL: undefined,
    VITE_WS_URL: undefined,
    VITE_APP_VERSION: undefined,
    MODE: "development",
    PROD: false,
    DEV: true,
    SSR: false
  };
};

/**
 * Get API base URL with proper fallbacks
 */
export const getApiBaseUrl = (): string => {
  const env = getEnv();

  // In test environment, use empty string so /api/entities becomes /api/entities
  if (isTest()) {
    return "";
  }

  // In production, use relative path
  if (isProduction()) {
    return "/api";
  }

  // In development, use full URL or fallback
  return env.VITE_API_BASE_URL || "http://localhost:8000";
};

/**
 * Check if running in development mode
 */
export const isDevelopment = (): boolean => {
  const env = getEnv();
  return env.DEV === true || env.MODE === "development";
};

/**
 * Check if running in production mode
 */
export const isProduction = (): boolean => {
  const env = getEnv();
  return env.PROD === true || env.MODE === "production";
};

/**
 * Check if running in test mode
 */
export const isTest = (): boolean => {
  return typeof process !== "undefined" && process.env.JEST_WORKER_ID !== undefined;
};
