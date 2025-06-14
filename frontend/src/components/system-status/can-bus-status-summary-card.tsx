import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useCANStatistics, useQueueStatus } from '@/hooks/useSystem';
import { IconWifi, IconAlertCircle, IconRefresh, IconChevronRight } from '@tabler/icons-react';
import { CheckCircleIcon, AlertTriangleIcon, XCircleIcon, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';

/**
 * CAN Bus Status Summary Card - Level 2 of the Information Pyramid
 * Shows high-level CAN bus health with drill-down capability.
 */
export function CANBusStatusSummaryCard() {
  const { data: canStats, isLoading, error, refetch } = useCANStatistics();
  const { data: queueStatus } = useQueueStatus();
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Calculate summary metrics
  const totalMessages = canStats?.total_messages || 0;
  const totalErrors = canStats?.total_errors || 0;
  const interfaces = canStats?.interfaces || {};
  const interfaceCount = Object.keys(interfaces).length;
  const errorRate = totalMessages > 0 ? (totalErrors / totalMessages) * 100 : 0;

  // Determine overall CAN status
  const getCANStatus = () => {
    if (error || !canStats) return 'critical';
    if (interfaceCount === 0) return 'critical';
    if (errorRate > 5) return 'warning';
    if (errorRate > 0) return 'warning';
    return 'healthy';
  };

  const canStatus = getCANStatus();

  const getStatusIcon = () => {
    switch (canStatus) {
      case 'critical':
        return <XCircleIcon className="h-4 w-4 text-destructive" />;
      case 'warning':
        return <AlertTriangleIcon className="h-4 w-4 text-yellow-600" />;
      default:
        return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    }
  };

  const getStatusLabel = () => {
    switch (canStatus) {
      case 'critical':
        return 'Critical';
      case 'warning':
        return 'Warning';
      default:
        return 'Healthy';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <IconWifi className="h-5 w-5" />
            <span>CAN Bus</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            <div className="h-8 bg-muted rounded" />
            <div className="h-4 bg-muted rounded w-3/4" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card
        className="cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => setIsPanelOpen(true)}
      >
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <IconWifi className="h-5 w-5" />
              <span>CAN Bus</span>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="text-lg font-semibold">{getStatusLabel()}</span>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium">{interfaceCount} Active</div>
              <div className="text-xs text-muted-foreground">Interfaces</div>
            </div>
          </div>
          {errorRate > 0 && (
            <div className="mt-2">
              <Badge variant={errorRate > 5 ? 'destructive' : 'secondary'} className="text-xs">
                {errorRate.toFixed(2)}% Error Rate
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      <Sheet open={isPanelOpen} onOpenChange={setIsPanelOpen}>
        <SheetContent className="w-[500px] sm:w-[600px] sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>CAN Bus Detailed Status</SheetTitle>
            <SheetDescription>
              Comprehensive CAN network monitoring and statistics
            </SheetDescription>
          </SheetHeader>

          <ScrollArea className="h-[calc(100vh-10rem)] mt-6">
            <div className="space-y-6 pr-4">
              {error ? (
                <Alert variant="destructive">
                  <IconAlertCircle className="h-4 w-4" />
                  <AlertTitle>CAN Bus Unavailable</AlertTitle>
                  <AlertDescription>
                    Unable to connect to CAN bus interface. Check that CAN interfaces are configured and active.
                  </AlertDescription>
                </Alert>
              ) : (
                <>
                  {/* Summary Statistics */}
                  <div>
                    <h3 className="font-semibold mb-3">Overview</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-muted/50 rounded-lg">
                        <div className="text-2xl font-bold">{totalMessages.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Total Messages</div>
                      </div>
                      <div className="text-center p-3 bg-muted/50 rounded-lg">
                        <div className="text-2xl font-bold">{interfaceCount}</div>
                        <div className="text-xs text-muted-foreground">Active Interfaces</div>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Interface Details */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold">Interface Status</h3>
                      <Button asChild variant="outline" size="sm">
                        <Link to="/can-sniffer">
                          Monitor Traffic
                          <IconChevronRight className="ml-1 h-3 w-3" />
                        </Link>
                      </Button>
                    </div>
                    <div className="space-y-3">
                      {Object.entries(interfaces).map(([name, stats]: [string, any]) => {
                        // Calculate messages as sum of tx and rx packets
                        const totalMessages = (stats.tx_packets || 0) + (stats.rx_packets || 0);
                        const totalErrors = (stats.tx_errors || 0) + (stats.rx_errors || 0) + (stats.bus_errors || 0);
                        const interfaceErrorRate = totalMessages > 0 ? (totalErrors / totalMessages) * 100 : 0;
                        const isHealthy = interfaceErrorRate < 1 && stats.state !== 'error';

                        return (
                          <div key={name} className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <IconWifi className={cn(
                                  "h-4 w-4",
                                  isHealthy ? "text-green-600" : "text-yellow-600"
                                )} />
                                <span className="font-medium">{name}</span>
                              </div>
                              <Badge variant={isHealthy ? "default" : "secondary"}>
                                {isHealthy ? "Healthy" : "Warning"}
                              </Badge>
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-sm">
                              <div>
                                <span className="text-muted-foreground">Messages:</span>
                                <span className="ml-1 font-medium">{totalMessages.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Errors:</span>
                                <span className="ml-1 font-medium">{totalErrors}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">State:</span>
                                <span className="ml-1 font-medium">{stats.state || 'Unknown'}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <Separator />

                  {/* Error Metrics */}
                  <div>
                    <h3 className="font-semibold mb-3">Error Analysis</h3>
                    <div className="space-y-3">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">Overall Error Rate</span>
                          <span className="text-sm font-medium">{errorRate.toFixed(2)}%</span>
                        </div>
                        <Progress
                          value={Math.min(errorRate, 100)}
                          className={cn(
                            "h-2",
                            errorRate > 5 && "[&>div]:bg-destructive",
                            errorRate > 0 && errorRate <= 5 && "[&>div]:bg-yellow-600"
                          )}
                        />
                      </div>
                      {totalErrors > 0 && (
                        <Alert>
                          <AlertTriangleIcon className="h-4 w-4" />
                          <AlertDescription>
                            {totalErrors} total errors detected across all interfaces.
                            {errorRate > 5 && " High error rate may indicate network issues."}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>

                  {/* Queue Status */}
                  {queueStatus && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="font-semibold mb-3">Message Queue</h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <span className="text-sm text-muted-foreground">Queue Length</span>
                            <div className="text-lg font-medium">{queueStatus.length || 0}</div>
                          </div>
                          <div className="space-y-1">
                            <span className="text-sm text-muted-foreground">Max Size</span>
                            <div className="text-lg font-medium">{queueStatus.maxsize === "unbounded" ? "∞" : queueStatus.maxsize}</div>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => void refetch()}
                  disabled={isLoading}
                >
                  <IconRefresh className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                <Button asChild variant="default">
                  <Link to="/can-sniffer">
                    Open CAN Monitor
                  </Link>
                </Button>
              </div>
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </>
  );
}
