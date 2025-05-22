// filepath: /workspace/web_ui/src/contexts/ThemeContext.tsx
import React, { createContext, useEffect, useState, type ReactNode } from "react";
import type { ThemeType } from "./ThemeUtils";

interface ThemeProviderProps {
  children: ReactNode;
}

interface ThemeContextValue {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  resolvedTheme: "light" | "dark";
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // SSR-safe check
  const isBrowser = typeof window !== "undefined" && typeof document !== "undefined";

  // Initialize theme from localStorage or default to 'system'
  const getInitialTheme = (): ThemeType => {
    if (!isBrowser) return "system";
    const stored = localStorage.getItem("rv-theme");
    if (stored === "light" || stored === "dark" || stored === "system") {
      return stored;
    }
    // Remove legacy/invalid values
    localStorage.removeItem("rv-theme");
    return "system";
  };

  const [theme, setThemeState] = useState<ThemeType>(() => getInitialTheme());
  const getSystemTheme = (): "dark" | "light" => {
    if (!isBrowser || !window.matchMedia) return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  };
  const [systemTheme, setSystemTheme] = useState<"dark" | "light">(() => getSystemTheme());

  // Calculate the resolved theme (the actual theme to apply)
  // Only allow 'light' or 'dark' as resolvedTheme
  const resolvedTheme: "light" | "dark" = theme === "system"
    ? systemTheme
    : theme === "dark"
      ? "dark"
      : "light";

  // Update theme and persist to localStorage
  const setTheme = (newTheme: ThemeType) => {
    setThemeState(newTheme);
    if (isBrowser) {
      localStorage.setItem("rv-theme", newTheme);
    }
  };

  // Listen for system theme changes
  useEffect(() => {
    if (!isBrowser || !window.matchMedia) return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => setSystemTheme(media.matches ? "dark" : "light");
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, [isBrowser]);

  // Effect: update <html> class when resolvedTheme changes
  useEffect(() => {
    if (!isBrowser) return;
    const root = document.documentElement;
    // Remove all known theme classes
    root.classList.remove(
      "theme-light",
      "theme-dark",
      "theme-default",
      "theme-catppuccin-mocha",
      "theme-catppuccin-latte",
      "theme-nord-dark",
      "theme-nord-light",
      "theme-gruvbox-dark",
      "theme-gruvbox-light"
    );
    let classToAdd = "";
    if (theme === "system") {
      classToAdd = `theme-${resolvedTheme}`;
    } else {
      classToAdd = `theme-${theme}`;
    }
    root.classList.add(classToAdd);
  }, [theme, resolvedTheme, isBrowser]);

  const value: ThemeContextValue = {
    theme,
    setTheme,
    resolvedTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export { ThemeContext };
