import { useHealth } from '@/contexts/health-context';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle, XCircle, WifiOff } from 'lucide-react';

/**
 * Global system status banner that displays at the top of the application.
 * Shows real-time health status with appropriate visual indicators.
 */
export const SystemStatusBanner = () => {
  const { isHealthy, connectionStatus, systemHealth } = useHealth();

  // Don't show banner if everything is healthy and connected
  if (connectionStatus === 'connected' && isHealthy && !systemHealth?.issues?.warning?.failed?.length) {
    return null;
  }

  if (connectionStatus === 'disconnected') {
    return (
      <div className="bg-gray-600 text-white px-4 py-2 flex items-center justify-center animate-pulse">
        <WifiOff className="w-5 h-5 mr-2" />
        <span className="font-medium">Status Unknown: Connection to vehicle lost</span>
      </div>
    );
  }

  if (connectionStatus === 'unknown') {
    return (
      <div className="bg-blue-600 text-white px-4 py-2 flex items-center justify-center">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
        <span className="font-medium">Connecting to vehicle systems...</span>
      </div>
    );
  }

  const hasCritical = (systemHealth?.issues?.critical?.failed?.length ?? 0) > 0;
  const hasWarning = (systemHealth?.issues?.warning?.failed?.length ?? 0) > 0 ||
                     (systemHealth?.issues?.warning?.degraded?.length ?? 0) > 0;

  if (!isHealthy && hasCritical) {
    return (
      <div className="bg-red-600 text-white px-4 py-2 flex items-center justify-center">
        <XCircle className="w-5 h-5 mr-2" />
        <span className="font-medium">
          Critical Failure: {systemHealth?.description || 'System not operational'}
        </span>
      </div>
    );
  }

  if (hasWarning) {
    return (
      <div className="bg-yellow-500 text-black px-4 py-2 flex items-center justify-center animate-pulse">
        <AlertCircle className="w-5 h-5 mr-2" />
        <span className="font-medium">
          System Degraded: {systemHealth?.description || 'Reduced functionality'}
        </span>
      </div>
    );
  }

  // This shouldn't normally be reached if the first condition works correctly
  return (
    <div className="bg-green-600 text-white px-4 py-2 flex items-center justify-center">
      <CheckCircle className="w-5 h-5 mr-2" />
      <span className="font-medium">All Systems Operational</span>
    </div>
  );
};

/**
 * Compact version of the status banner for mobile or limited space.
 * Shows only an icon with tooltip.
 */
export const SystemStatusBannerCompact = () => {
  const { isHealthy, connectionStatus, systemHealth } = useHealth();

  const hasCritical = (systemHealth?.issues?.critical?.failed?.length ?? 0) > 0;
  const hasWarning = (systemHealth?.issues?.warning?.failed?.length ?? 0) > 0 ||
                     (systemHealth?.issues?.warning?.degraded?.length ?? 0) > 0;

  let icon: React.ReactNode;
  let className: string;
  let title: string;

  if (connectionStatus === 'disconnected') {
    icon = <WifiOff className="w-5 h-5" />;
    className = "bg-gray-600 text-white";
    title = "Connection lost";
  } else if (connectionStatus === 'unknown') {
    icon = <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />;
    className = "bg-blue-600 text-white";
    title = "Connecting...";
  } else if (!isHealthy && hasCritical) {
    icon = <XCircle className="w-5 h-5" />;
    className = "bg-red-600 text-white";
    title = "Critical system failure";
  } else if (hasWarning) {
    icon = <AlertCircle className="w-5 h-5" />;
    className = "bg-yellow-500 text-black animate-pulse";
    title = "System degraded";
  } else {
    icon = <CheckCircle className="w-5 h-5" />;
    className = "bg-green-600 text-white";
    title = "All systems operational";
  }

  return (
    <div className={cn("p-2 rounded-full", className)} title={title}>
      {icon}
    </div>
  );
};
