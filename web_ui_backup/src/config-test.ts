/**
 * This file is used to test if the TypeScript configuration is working correctly.
 */

// Dummy config value for testing
const WS_URL = "ws://localhost:8000/api/ws";

// Example: Theme-adaptive config value using a CSS variable
export const THEME_TEST_COLOR = "var(--color-accent, #646cff)";

/**
 * Get a theme color from CSS variables (for theme-adaptive UI)
 * @param name The CSS variable name (e.g., '--color-accent')
 * @returns The computed color value or fallback
 */
export function getThemeColor(name: string): string {
  if (typeof window === "undefined" || !window.getComputedStyle) return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name) || "";
}

// Note: For real theme integration, use THEME_COLORS from config.ts

// Define a simple test function
export function testConfiguration(): string {
  return `Configuration test is working. WS_URL: ${WS_URL}`;
}

// Define a simple interface to test TypeScript
export interface TestConfig {
  name: string;
  value: number;
  optional?: boolean;
}

// Create an object with the interface type
const config: TestConfig = {
  name: "test",
  value: 123
};

// Test theme color getter (will only work in browser)
if (typeof window !== "undefined") {
  const accent = getThemeColor("--color-accent");
  console.info("Theme accent color:", accent);
}

console.info(config);
