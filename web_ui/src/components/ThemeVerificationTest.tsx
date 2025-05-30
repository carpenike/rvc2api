import React from "react";
import { useTheme } from "../contexts/useTheme";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

export const ThemeVerificationTest: React.FC = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Theme Verification Test</CardTitle>
          <CardDescription>
            Testing shadcn/ui theming system functionality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Theme Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold text-sm">Selected Theme</h3>
              <p className="text-lg font-mono">{theme}</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold text-sm">Resolved Theme</h3>
              <p className="text-lg font-mono">{resolvedTheme}</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold text-sm">HTML Classes</h3>
              <p className="text-sm font-mono">
                {typeof document !== "undefined"
                  ? Array.from(document.documentElement.classList).join(" ") || "none"
                  : "Loading..."}
              </p>
            </div>
          </div>

          {/* Theme Controls */}
          <div className="flex gap-2 flex-wrap">
            <Button onClick={toggleTheme} variant="default">
              Cycle Theme ({theme} → {theme === "light" ? "dark" : theme === "dark" ? "system" : "light"})
            </Button>
            <Button onClick={() => setTheme("light")} variant="outline">
              Force Light
            </Button>
            <Button onClick={() => setTheme("dark")} variant="outline">
              Force Dark
            </Button>
            <Button onClick={() => setTheme("system")} variant="outline">
              System
            </Button>
          </div>

          {/* Color Swatches */}
          <div>
            <h3 className="font-semibold mb-3">Color Variables Test</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { name: "Background", var: "--background", class: "bg-background text-foreground" },
                { name: "Card", var: "--card", class: "bg-card text-card-foreground" },
                { name: "Primary", var: "--primary", class: "bg-primary text-primary-foreground" },
                { name: "Secondary", var: "--secondary", class: "bg-secondary text-secondary-foreground" },
                { name: "Muted", var: "--muted", class: "bg-muted text-muted-foreground" },
                { name: "Accent", var: "--accent", class: "bg-accent text-accent-foreground" },
                { name: "Destructive", var: "--destructive", class: "bg-destructive text-destructive-foreground" },
                { name: "Border", var: "--border", class: "bg-background border-2 border-border text-foreground" }
              ].map((color) => (
                <div
                  key={color.name}
                  className={`${color.class} p-3 rounded-md text-center text-sm`}
                >
                  <div className="font-semibold">{color.name}</div>
                  <div className="font-mono text-xs opacity-80">{color.var}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Component Tests */}
          <div>
            <h3 className="font-semibold mb-3">Component Tests</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Nested Card</CardTitle>
                  <CardDescription>This card should inherit theme colors</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Card content with muted text color.
                  </p>
                  <div className="mt-2 flex gap-2">
                    <Button size="sm" variant="default">Default</Button>
                    <Button size="sm" variant="outline">Outline</Button>
                    <Button size="sm" variant="destructive">Destructive</Button>
                  </div>
                </CardContent>
              </Card>

              <div className="p-4 border border-border rounded-lg bg-card">
                <h4 className="font-semibold mb-2">Manual Card</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  This demonstrates manual theming using Tailwind classes.
                </p>
                <div className="space-y-2">
                  <div className="w-full h-2 bg-primary rounded"></div>
                  <div className="w-3/4 h-2 bg-secondary rounded"></div>
                  <div className="w-1/2 h-2 bg-accent rounded"></div>
                </div>
              </div>
            </div>
          </div>

          {/* CSS Variables Debug */}
          <details className="border border-border rounded-lg">
            <summary className="p-3 cursor-pointer font-semibold">
              CSS Variables Debug Info (Click to expand)
            </summary>
            <div className="p-3 pt-0">
              <div className="bg-muted rounded-md p-3 font-mono text-xs space-y-1">
                {[
                  "--background", "--foreground", "--card", "--card-foreground",
                  "--primary", "--primary-foreground", "--secondary", "--secondary-foreground",
                  "--muted", "--muted-foreground", "--accent", "--accent-foreground",
                  "--destructive", "--destructive-foreground", "--border", "--input", "--ring"
                ].map((varName) => (
                  <div key={varName} className="flex justify-between">
                    <span>{varName}:</span>
                    <span>
                      {typeof document !== "undefined"
                        ? getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || "undefined"
                        : "Loading..."}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </details>
        </CardContent>
      </Card>
    </div>
  );
};
