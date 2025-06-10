import { createContext } from "react"

export type Theme = "dark" | "light" | "system"

export interface ThemeProviderState {
  theme: Theme
  setTheme: (theme: Theme) => void
  systemTheme: "dark" | "light"
  resolvedTheme: "dark" | "light"
}

export const initialState: ThemeProviderState = {
  theme: "system",
  setTheme: () => null,
  systemTheme: "light",
  resolvedTheme: "light",
}

export const ThemeProviderContext = createContext<ThemeProviderState>(initialState)
