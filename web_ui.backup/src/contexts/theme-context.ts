import { createContext } from "react";
import { type Accent, type Theme } from "@/lib/constants";

/* ── Context shape ──────────────────────────────── */
export interface ThemeCtx {
  theme: Theme;
  accent: Accent;
  setTheme:  (t: Theme)  => void;
  setAccent: (a: Accent) => void;
}

export const ThemeProviderContext = createContext<ThemeCtx | null>(null);
