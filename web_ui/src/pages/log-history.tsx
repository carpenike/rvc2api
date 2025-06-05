import { API_BASE } from "@/api/client";
import { AppLayout } from "@/components/app-layout";
import { LogViewer } from "@/components/log-viewer/LogViewer";

export default function LogHistoryPage() {
  return (
    <AppLayout pageTitle="Log History">
      <div className="p-6">
        <LogViewer
          variant="full-page"
          websocketUrl="/ws/logs"
          apiEndpoint={`${API_BASE}/logs`}
          initialFilters={{}}
          useVirtualization={true}
        />
      </div>
    </AppLayout>
  );
}
