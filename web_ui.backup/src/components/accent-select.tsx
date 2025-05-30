import { useTheme } from "@/hooks/useTheme";
import { useAvailableAccents } from "@/hooks/useAvailableAccents";
import { useEffect, useState } from "react";

import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator
} from "@/components/ui/select";
import { PaintBucket } from "lucide-react";

type Font = "default" | "scaled" | "mono";

export function AccentSelect() {
  const { accent, setAccent, font, setFont } = useTheme();
  const accents = useAvailableAccents();

  const fontOptions: ReadonlyArray<{ label: string; value: Font }> = [
    { label: "Default", value: "default" },
    { label: "Scaled", value: "scaled" },
    { label: "Mono", value: "mono" }
  ];

  // last-clicked item controls <Select>
  const [selected, setSelected] = useState<string>(`font:${font}`);

  /* keep local state in sync when context updates elsewhere */
  useEffect(() => {
    setSelected((prev) =>
      prev.startsWith("font:")
        ? `font:${font}`
        : `accent:${accent}`
    );
  }, [font, accent]);

  const handleChange = (val: string) => {
    setSelected(val);
    const [kind, payload] = val.split(":") as ["font" | "accent", string];
    if (kind === "font") setFont(payload as Font);
    else setAccent(payload as Accent);
  };

  return (
    <Select value={selected} onValueChange={handleChange}>
      <SelectTrigger className="w-32 rounded-md p-2 hover:bg-muted/50">
        <PaintBucket className="h-4 w-4" />
        <SelectValue placeholder="Theme" />
      </SelectTrigger>

      <SelectContent className="max-h-60 overflow-y-auto">
        {/* Fonts */}
        <SelectGroup>
          <SelectLabel>Theme</SelectLabel>
          {fontOptions.map(({ label, value }) => (
            <SelectItem key={value} value={`font:${value}`}>
              {label}
            </SelectItem>
          ))}
        </SelectGroup>

        <SelectSeparator />

        {/* Colours */}
        <SelectGroup>
          <SelectLabel>Colors</SelectLabel>
          {accents.map((a) => (
            <SelectItem key={a} value={`accent:${a}`}>
              {a.charAt(0).toUpperCase() + a.slice(1)}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
