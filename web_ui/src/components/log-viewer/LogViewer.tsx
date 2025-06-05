import { LogViewerProvider } from "./log-viewer-context";
import { LogList } from "./LogList";
import { LogTabs } from "./LogTabs";
import { LogToolbar } from "./LogToolbar";
import { VirtualizedLogList } from "./VirtualizedLogList";

export interface LogViewerProps {
  variant: "drawer" | "full-page";
  websocketUrl: string;
  apiEndpoint: string;
  initialFilters?: Record<string, unknown>;
  useVirtualization?: boolean;
}

export function LogViewer({
  // variant is not used yet, so prefix with _ to avoid lint error
  variant: _variant,
  websocketUrl,
  apiEndpoint,
  initialFilters,
  useVirtualization = false,
}: LogViewerProps) {
  return (
    <LogViewerProvider
      websocketUrl={websocketUrl}
      apiEndpoint={apiEndpoint}
      initialFilters={initialFilters}
    >
      <div className="flex flex-col h-full">
        <LogToolbar />
        <LogTabs />
        {useVirtualization ? <VirtualizedLogList /> : <LogList />}
      </div>
    </LogViewerProvider>
  );
}
