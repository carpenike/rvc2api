import React, { useEffect, useState } from "react";
import { themeConfigs } from "../../contexts/ThemeUtils";
import { useTheme } from "../../contexts/useTheme";

interface CSSVariableInfo {
  name: string;
  value: string;
  category: string;
}

export const ThemeDebugger: React.FC = () => {
  const { theme, resolvedTheme } = useTheme();
  const [isVisible, setIsVisible] = useState(false);
  const [cssVariables, setCssVariables] = useState<CSSVariableInfo[]>([]);

  useEffect(() => {
    const extractCSSVariables = () => {
      const styles = getComputedStyle(document.documentElement);
      const variables: CSSVariableInfo[] = [];

      // Extract theme-related CSS variables
      const themeVars = [
        "--background",
        "--foreground",
        "--primary",
        "--primary-foreground",
        "--secondary",
        "--secondary-foreground",
        "--muted",
        "--muted-foreground",
        "--accent",
        "--accent-foreground",
        "--destructive",
        "--destructive-foreground",
        "--border",
        "--input",
        "--ring",
        "--card",
        "--card-foreground",
        "--popover",
        "--popover-foreground"
      ];

      themeVars.forEach(varName => {
        const value = styles.getPropertyValue(varName).trim();
        if (value) {
          variables.push({
            name: varName,
            value,
            category: "theme"
          });
        }
      });

      setCssVariables(variables);
    };

    if (isVisible) {
      extractCSSVariables();
    }
  }, [isVisible, resolvedTheme]);

  // Only show in development
  if (process.env.NODE_ENV !== "development") {
    return null;
  }

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-3 py-2 rounded-md text-sm shadow-lg hover:bg-primary/90 transition-colors"
        title="Open Theme Debugger"
      >
        🎨 Debug
      </button>
    );
  }

  const currentThemeConfig = themeConfigs[theme];

  return (
    <div className="fixed bottom-4 right-4 bg-card border border-border rounded-lg shadow-xl max-w-md max-h-96 overflow-auto z-50">
      <div className="sticky top-0 bg-card border-b border-border p-3 flex items-center justify-between">
        <h3 className="font-semibold text-card-foreground">Theme Debugger</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-muted-foreground hover:text-foreground transition-colors"
          title="Close"
        >
          ✕
        </button>
      </div>

      <div className="p-3 space-y-4">
        {/* Current Theme Info */}
        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-2">Current Theme</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Selected:</span>
              <div className="font-mono">
                {currentThemeConfig.icon} {currentThemeConfig.displayName}
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">Resolved:</span>
              <div className="font-mono capitalize">{resolvedTheme}</div>
            </div>
          </div>
        </div>

        {/* CSS Classes */}
        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-2">HTML Classes</h4>
          <div className="font-mono text-xs bg-muted p-2 rounded">
            {Array.from(document.documentElement.classList).join(" ") || "none"}
          </div>
        </div>

        {/* CSS Variables */}
        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-2">CSS Variables</h4>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {cssVariables.map((variable) => (
              <div key={variable.name} className="flex items-center justify-between text-xs">
                <code className="text-muted-foreground">{variable.name}</code>
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 border border-border rounded"
                    style={{
                      backgroundColor: `hsl(${variable.value})`
                    }}
                    title={`hsl(${variable.value})`}
                  />
                  <code className="font-mono text-xs">{variable.value}</code>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Info */}
        <div>
          <h4 className="font-medium text-sm text-muted-foreground mb-2">System</h4>
          <div className="text-xs space-y-1">
            <div>
              <span className="text-muted-foreground">Prefers dark:</span>{" "}
              <code>
                {window.matchMedia("(prefers-color-scheme: dark)").matches ? "yes" : "no"}
              </code>
            </div>
            <div>
              <span className="text-muted-foreground">Reduced motion:</span>{" "}
              <code>
                {window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "yes" : "no"}
              </code>
            </div>
            <div>
              <span className="text-muted-foreground">High contrast:</span>{" "}
              <code>
                {window.matchMedia("(prefers-contrast: high)").matches ? "yes" : "no"}
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
