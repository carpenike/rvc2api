export type ThemeType = "default" | "dark" | "light" | "custom" | "system";

export interface ThemeContextProps {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  resolvedTheme: "light" | "dark"; // The actually applied theme
}
