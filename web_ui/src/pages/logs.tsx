import { API_BASE } from "@/api/client";
import { AppLayout } from "@/components/app-layout";
import { LogViewer } from "@/components/log-viewer/LogViewer";

export default function LogsPage() {
  return (
    <AppLayout pageTitle="System Logs">
      <div className="flex flex-col h-full p-6">
        <LogViewer
          variant="full-page"
          websocketUrl="/ws/logs"
          apiEndpoint={`${API_BASE}/logs`}
          initialFilters={{}}
          useVirtualization={false}
        />
      </div>
    </AppLayout>
  );
}
