export const THEMES = ["light", "dark", "system"] as const;
export type ThemeType = typeof THEMES[number];

export interface ThemeConfig {
  name: ThemeType;
  displayName: string;
  cssClass: string;
  icon: string;
  description: string;
}

export const themeConfigs: Record<ThemeType, ThemeConfig> = {
  light: {
    name: "light",
    displayName: "Light",
    cssClass: "light",
    icon: "☀️",
    description: "Clean and bright interface"
  },
  dark: {
    name: "dark",
    displayName: "Dark",
    cssClass: "dark",
    icon: "🌙",
    description: "Easy on the eyes"
  },
  system: {
    name: "system",
    displayName: "System",
    cssClass: "system",
    icon: "💻",
    description: "Follows your system preference"
  }
};

// Utility function to get system theme preference
export const getSystemTheme = (): "light" | "dark" => {
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
};

// Utility function to resolve effective theme
export const resolveTheme = (theme: ThemeType): "light" | "dark" => {
  return theme === "system" ? getSystemTheme() : theme;
};

export interface ThemeContextProps {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  resolvedTheme: "light" | "dark"; // The actually applied theme
}
