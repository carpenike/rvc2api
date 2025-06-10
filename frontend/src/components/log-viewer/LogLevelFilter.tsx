import type { LogFilters } from "./log-viewer-context";
import { useLogViewer } from "./useLogViewer";

const LEVELS = [
  { value: "0", label: "Emerg" },
  { value: "1", label: "Alert" },
  { value: "2", label: "Crit" },
  { value: "3", label: "Error" },
  { value: "4", label: "Warn" },
  { value: "5", label: "Notice" },
  { value: "6", label: "Info" },
  { value: "7", label: "Debug" },
];

export function LogLevelFilter() {
  const { filters, updateFilters } = useLogViewer();
  return (
    <select
      className="border rounded px-2 py-1 text-sm bg-background"
      value={filters.level || ""}
      onChange={e => {
        const filters: Partial<LogFilters> = {};
        if (e.target.value) {
          filters.level = e.target.value;
        }
        updateFilters(filters);
      }}
      aria-label="Filter by log level"
    >
      <option value="">All Levels</option>
      {LEVELS.map(l => (
        <option key={l.value} value={l.value}>{l.label}</option>
      ))}
    </select>
  );
}
