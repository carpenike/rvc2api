import { Badge, type badgeVariants } from "@/components/ui/badge";
import { type VariantProps } from "class-variance-authority";
import {
  AlertCircle,
  AlertTriangle,
  Bell,
  Bug,
  Info,
  Zap
} from "lucide-react";
import { InfiniteLogLoader } from "./InfiniteLogLoader";
import type { LogEntry } from "./log-viewer-context";
import { useLogViewer } from "./useLogViewer";

type LogBadgeVariant = VariantProps<typeof badgeVariants>["variant"];

// Log level icon mapping for accessibility
function getLogIcon(level?: string) {
  switch (level) {
    case "error":
    case "3":
      return AlertCircle;
    case "warn":
    case "warning":
    case "4":
      return AlertTriangle;
    case "info":
    case "6":
      return Info;
    case "debug":
    case "7":
      return Bug;
    case "critical":
    case "2":
      return Zap;
    case "notice":
    case "5":
      return Bell;
    default:
      return Info;
  }
}

// Log level badge variant mapping
function getLogVariant(level?: string): LogBadgeVariant {
  switch (level) {
    case "error":
    case "3":
      return "log-error";
    case "warn":
    case "warning":
    case "4":
      return "log-warning";
    case "info":
    case "6":
      return "log-info";
    case "debug":
    case "7":
      return "log-debug";
    case "critical":
    case "2":
      return "log-critical";
    case "notice":
    case "5":
      return "log-notice";
    default:
      return "outline";
  }
}

// Row background for subtle visual grouping
function getLogRowBg(level?: string) {
  switch (level) {
    case "error":
    case "3":
      return "bg-log-error-bg border-l-2 border-log-error";
    case "warn":
    case "warning":
    case "4":
      return "bg-log-warning-bg border-l-2 border-log-warning";
    case "info":
    case "6":
      return "bg-log-info-bg border-l-2 border-log-info/50";
    case "debug":
    case "7":
      return "bg-log-debug-bg border-l-2 border-log-debug/50";
    case "critical":
    case "2":
      return "bg-log-critical-bg border-l-2 border-log-critical animate-pulse";
    case "notice":
    case "5":
      return "bg-log-notice-bg border-l-2 border-log-notice/50";
    default:
      return "";
  }
}

export function LogList() {
  const { logs, loading, error, clearError } = useLogViewer();

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-40 p-4 text-center">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-left">
              <h3 className="text-sm font-medium text-yellow-800 mb-1">
                History Not Available
              </h3>
              <p className="text-sm text-yellow-700">
                {error}
              </p>
              <button
                onClick={clearError}
                className="mt-2 text-xs text-yellow-800 underline hover:text-yellow-900"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-muted-foreground">
        Loading logs...
      </div>
    );
  }

  if (!logs.length) {
    return (
      <div className="flex items-center justify-center h-40 text-muted-foreground">
        No logs to display.
      </div>
    );
  }

  return (
    <div className="overflow-y-auto flex-1 bg-background font-mono text-sm">
      {logs.map((log: LogEntry, i: number) => {
        const IconComponent = getLogIcon(log.level);
        const variant = getLogVariant(log.level);
        const isCritical = log.level === "critical" || log.level === "2";

        // Apply text color based on log level for improved readability
        const textColor = isCritical ? "text-log-critical" :
                          log.level === "error" || log.level === "3" ? "text-log-error" : "";

        return (
          <div
            key={i}
            className={`px-4 py-2 border-b flex items-start gap-2 transition-colors hover:bg-muted/50 ${getLogRowBg(log.level)} ${
              isCritical ? "animate-pulse" : ""
            }`}
          >
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {log.timestamp}
            </span>
            <Badge variant={variant} className="shrink-0 flex items-center gap-1">
              <IconComponent className="w-3 h-3" aria-hidden="true" />
              <span>{log.level}</span>
            </Badge>
            {log.logger && (
              <span className="text-xs bg-muted/50 rounded px-1 py-0.5">{log.logger}</span>
            )}
            <span className={`flex-1 ${isCritical ? "font-medium" : ""} ${textColor}`}>
              {log.message}
            </span>
          </div>
        );
      })}
      <InfiniteLogLoader />
    </div>
  );
}
