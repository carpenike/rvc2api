import { useContext } from "react";
import { ThemeContext } from "./ThemeContext";
import type { ThemeContextProps } from "./ThemeUtils";

/**
 * Custom React hook to access the theme context.
 * Throws if used outside a ThemeProvider.
 */
export const useTheme = (): ThemeContextProps => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
