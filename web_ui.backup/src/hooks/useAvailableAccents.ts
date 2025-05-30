import { useMemo } from "react";
import { ALL_ACCENTS, type Accent } from "@/lib/constants";

/**
 * Detects which `.accent-{name}` blocks actually exist in global.css by
 * checking if they change the `--primary` CSS variable.  Returns only
 * those accents, so the picker shows valid options.
 */
export function useAvailableAccents(): Accent[] {
  return useMemo(() => {
    const root = document.documentElement;
    const original = getComputedStyle(root)
      .getPropertyValue("--primary")
      .trim();

    // spread ⇒ tuple → normal array, so filter() is fine
    return [...ALL_ACCENTS].filter((a): a is Accent => {
      if (a === "slate") return true; // base colours always present

      const cls = `accent-${a}`;
      root.classList.add(cls);
      const changed =
        getComputedStyle(root).getPropertyValue("--primary").trim() !== original;
      root.classList.remove(cls);

      return changed;
    });
  }, []);
}
