import { useLogViewer } from "./useLogViewer";

export function LogTabs() {
  const { mode, setMode } = useLogViewer();
  return (
    <div className="flex gap-2 px-4 py-2 border-b bg-muted/10">
      <button
        className={`px-3 py-1 rounded-md text-sm font-medium focus:outline-none ${
          mode === "live"
            ? "bg-primary text-primary-foreground"
            : "bg-background text-foreground border"
        }`}
        aria-pressed={mode === "live"}
        onClick={() => setMode("live")}
      >
        Live Stream
      </button>
      <button
        className={`px-3 py-1 rounded-md text-sm font-medium focus:outline-none ${
          mode === "history"
            ? "bg-primary text-primary-foreground"
            : "bg-background text-foreground border"
        }`}
        aria-pressed={mode === "history"}
        onClick={() => setMode("history")}
      >
        History
      </button>
    </div>
  );
}
