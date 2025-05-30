import { useContext, useEffect, useState } from "react";
import { ThemeProviderContext, type ThemeCtx } from "@/contexts/theme-context";

type Font = "default" | "scaled" | "mono";

export const useTheme = (): ThemeCtx & {
  font: Font;
  setFont: (f: Font) => void;
} => {
  const ctx = useContext(ThemeProviderContext);
  if (ctx === null) throw new Error("useTheme must be used within a ThemeProvider");

  const [font, setFont] = useState<Font>("default");

  useEffect(() => {
    document.documentElement.dataset.font = font; // e.g. <html data-font="mono">
  }, [font]);

  useEffect(() => {
    document.documentElement.dataset.accent = ctx.accent; // e.g. <html data-accent="green">
  }, [ctx.accent]);

  return { ...ctx, font, setFont };
};
