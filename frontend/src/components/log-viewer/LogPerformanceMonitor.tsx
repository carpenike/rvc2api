import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Activity, BarChart3 } from "lucide-react";
import { useEffect, useState } from "react";
import { useLogViewer } from "./useLogViewer";

interface PerformanceMetrics {
  totalLogs: number;
  logsPerSecond: number;
  memoryUsage: number;
  filteredLogs: number;
  connectionUptime: number;
  messagesReceived: number;
}

export function LogPerformanceMonitor() {
  const { logs, rawLogs, connectionStatus } = useLogViewer();
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    totalLogs: 0,
    logsPerSecond: 0,
    memoryUsage: 0,
    filteredLogs: 0,
    connectionUptime: 0,
    messagesReceived: 0,
  });
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const uptimeSeconds = (now - startTime) / 1000;

      // Calculate approximate memory usage (rough estimate)
      const avgLogSize = 200; // bytes per log entry
      const memoryUsageBytes = rawLogs.length * avgLogSize;
      const memoryUsageMB = memoryUsageBytes / (1024 * 1024);

      // Calculate logs per second
      const logsPerSecond = rawLogs.length / Math.max(uptimeSeconds, 1);

      setMetrics({
        totalLogs: rawLogs.length,
        logsPerSecond: Math.round(logsPerSecond * 100) / 100,
        memoryUsage: Math.round(memoryUsageMB * 100) / 100,
        filteredLogs: logs.length,
        connectionUptime: Math.round(uptimeSeconds),
        messagesReceived: rawLogs.length,
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [rawLogs.length, logs.length, startTime]);

  const getConnectionBadge = () => {
    switch (connectionStatus) {
      case "connected":
        return <Badge variant="secondary" className="text-green-600">Connected</Badge>;
      case "connecting":
        return <Badge variant="outline" className="text-yellow-600">Connecting</Badge>;
      case "disconnected":
        return <Badge variant="outline" className="text-gray-600">Disconnected</Badge>;
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          aria-label="View performance metrics"
        >
          <Activity className="h-4 w-4" />
          <span className="hidden sm:inline">Metrics</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Performance Metrics
            </CardTitle>
            <CardDescription>
              Real-time log processing statistics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Status</span>
              {getConnectionBadge()}
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm">Total Logs</span>
              <span className="font-mono">{metrics.totalLogs.toLocaleString()}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm">Filtered Logs</span>
              <span className="font-mono">{metrics.filteredLogs.toLocaleString()}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm">Rate</span>
              <span className="font-mono">{metrics.logsPerSecond}/sec</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm">Memory Usage</span>
              <span className="font-mono">{metrics.memoryUsage} MB</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm">Uptime</span>
              <span className="font-mono text-xs">{formatUptime(metrics.connectionUptime)}</span>
            </div>

            {metrics.memoryUsage > 50 && (
              <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                ⚠️ High memory usage detected. Consider clearing logs or reducing buffer size.
              </div>
            )}
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  );
}
