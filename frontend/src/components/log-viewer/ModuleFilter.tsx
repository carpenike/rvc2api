import type { LogEntry, LogFilters } from "./log-viewer-context";
import { useLogViewer } from "./useLogViewer";

export function ModuleFilter() {
  const { rawLogs, filters, updateFilters } = useLogViewer();
  // Get unique logger/module names from raw logs (not filtered logs)
  const modules = Array.from(new Set(rawLogs.map((l: LogEntry) => l.logger).filter(Boolean)));
  return (
    <select
      className="border rounded px-2 py-1 text-sm bg-background"
      value={filters.module || ""}
      onChange={e => {
        const filters: Partial<LogFilters> = {};
        if (e.target.value) {
          filters.module = e.target.value;
        }
        updateFilters(filters);
      }}
      aria-label="Filter by module"
    >
      <option value="">All Modules</option>
      {modules.map((m: unknown) => (
        <option key={m as string} value={m as string}>{m as string}</option>
      ))}
    </select>
  );
}
