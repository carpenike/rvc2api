/**
 * Enhanced WebSocket Status Indicator
 *
 * Provides comprehensive visual feedback for WebSocket connection status
 * with user-friendly actions and detailed status information.
 */

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { useWebSocketContext } from "@/contexts/use-websocket-context";
import { cn } from "@/lib/utils";
import { IconAlertCircle, IconRefresh, IconWifi, IconWifiOff } from "@tabler/icons-react";
import { useState } from "react";

export function WebSocketStatusIndicator({ className }: { className?: string }) {
  const { isConnected, hasError, connectAll, disconnectAll, metrics } = useWebSocketContext();
  const [showDetails, setShowDetails] = useState(false);

  const getStatusConfig = () => {
    if (hasError) {
      return {
        icon: IconAlertCircle,
        label: "Error",
        variant: "destructive" as const,
        color: "text-red-500",
      };
    }
    if (isConnected) {
      return {
        icon: IconWifi,
        label: "Connected",
        variant: "secondary" as const,
        color: "text-green-500",
      };
    }
    return {
      icon: IconWifiOff,
      label: "Disconnected",
      variant: "outline" as const,
      color: "text-gray-500",
    };
  };

  const status = getStatusConfig();
  const StatusIcon = status.icon;

  const formatUptime = () => {
    if (!metrics.connectedAt) return "—";
    const uptime = Date.now() - metrics.connectedAt.getTime();
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const handleReconnect = () => {
    // Reconnection attempts are tracked by the WebSocket provider
    connectAll();
  };

  return (
    <Popover open={showDetails} onOpenChange={setShowDetails}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn("gap-2 px-2", className)}
        >
          <StatusIcon className={cn("size-4", status.color)} />
          <Badge variant={status.variant} className="hidden sm:inline-flex">
            {status.label}
          </Badge>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <StatusIcon className={cn("size-4", status.color)} />
              WebSocket Connection
            </CardTitle>
            <CardDescription>
              Real-time data connection status
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium">Status</div>
                <div className={status.color}>{status.label}</div>
              </div>
              <div>
                <div className="font-medium">Uptime</div>
                <div>{formatUptime()}</div>
              </div>
              <div>
                <div className="font-medium">Messages</div>
                <div>{metrics.messageCount.toLocaleString()}</div>
              </div>
              <div>
                <div className="font-medium">Reconnects</div>
                <div>{metrics.reconnectAttempts}</div>
              </div>
            </div>

            {metrics.lastMessage && (
              <>
                <Separator />
                <div className="text-sm">
                  <div className="font-medium mb-1">Last Message</div>
                  <div className="text-muted-foreground">
                    {metrics.lastMessage.toLocaleTimeString()}
                  </div>
                </div>
              </>
            )}

            <Separator />
            <div className="flex gap-2">
              {!isConnected && (
                <Button
                  size="sm"
                  onClick={handleReconnect}
                  className="flex-1"
                >
                  <IconRefresh className="size-3 mr-1" />
                  Reconnect
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={isConnected ? disconnectAll : connectAll}
                className="flex-1"
              >
                {isConnected ? "Disconnect" : "Connect"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  );
}
