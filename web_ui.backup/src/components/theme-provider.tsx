import { useEffect, useState } from "react";
import { type Accent, type Theme, ALL_ACCENTS } from "@/lib/constants";
import { ThemeProviderContext } from "@/contexts/theme-context";

/* ── Provider ───────────────────────────────────── */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  /* read saved or system prefs */
  const [theme, setTheme] = useState<Theme>(() =>
    (localStorage.getItem("theme") as Theme) ??
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );

  const [accent, setAccent] = useState<Accent>(() =>
    (localStorage.getItem("accent") as Accent) ?? "slate"
  );

  /* apply classes + persist */
  useEffect(() => {
    const root = document.documentElement;

    /* theme */
    root.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);

    /* accent switch */
    const accentClasses = ALL_ACCENTS
      .filter(a => a !== "slate")
      .map(a => `accent-${a}`);
    accentClasses.forEach(c => root.classList.remove(c));
    if (accent !== "slate") root.classList.add(`accent-${accent}`);
    localStorage.setItem("accent", accent);
  }, [theme, accent]);

  return (
    <ThemeProviderContext.Provider value={{ theme, accent, setTheme, setAccent }}>
      {children}
    </ThemeProviderContext.Provider>
  );
}
