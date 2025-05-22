import clsx from "clsx";
import React from "react";
import type { ThemeType } from "../contexts/ThemeUtils";
import { useTheme } from "../contexts/useTheme";

interface ThemeOption {
  id: string;
  label: string;
  value: ThemeType;
}

const themeOptions: ThemeOption[] = [
  { id: "theme-system", label: "System", value: "system" },
  { id: "theme-default", label: "Default", value: "default" },
  { id: "theme-dark", label: "Dark", value: "dark" },
  { id: "theme-light", label: "Light", value: "light" }
];

export const ThemeSelector: React.FC = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <fieldset
      className="flex items-center border-0 p-0 m-0"
      aria-label="Theme selection"
      data-testid="theme-selector-fieldset"
    >
      <legend className="sr-only">Theme selection</legend>
      <label
        htmlFor="theme-select"
        className="mr-2 text-rv-text text-sm font-medium"
        id="theme-select-label"
      >
        Theme:
      </label>
      <select
        id="theme-select"
        value={theme}
        onChange={(e) => {
          const newTheme = e.target.value as ThemeType;
          setTheme(newTheme);
        }}
        className={clsx(
          "bg-rv-surface text-rv-text border border-rv-border rounded-md px-2 py-1 text-sm",
          "focus:outline-none focus:ring-2 focus:ring-rv-primary transition-colors"
        )}
        aria-label="Select theme"
        aria-describedby="theme-select-label"
        data-testid="theme-selector-select"
      >
        {themeOptions.map((option) => (
          <option key={option.id} value={option.value} data-testid={`theme-option-${option.value}`}>
            {option.label}
            {option.value === "system" && resolvedTheme ?
              ` (${resolvedTheme.charAt(0).toUpperCase() + resolvedTheme.slice(1)})` : ""}
          </option>
        ))}
      </select>
    </fieldset>
  );
};
