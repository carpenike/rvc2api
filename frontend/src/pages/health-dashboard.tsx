import { useState } from 'react';
import { AppLayout } from '@/components/app-layout';
import { useSystemHealthStatus, useHealthMonitoring, useReadinessCheck } from '@/hooks/useHealthStatus';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, CheckCircle, XCircle, Activity, Server, Cpu, Network } from 'lucide-react';
import type { HealthCheck } from '@/types/health';

/**
 * Formats a component name for display
 */
function formatComponentName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Gets the appropriate icon for a component
 */
function getComponentIcon(name: string) {
  if (name.includes('server') || name.includes('core')) return Server;
  if (name.includes('hardware') || name.includes('can')) return Cpu;
  if (name.includes('network') || name.includes('websocket')) return Network;
  return Activity;
}

/**
 * Gets a descriptive message for a component's status
 */
function getComponentMessage(name: string, status: string): string {
  const messages: Record<string, Record<string, string>> = {
    hardware_initialization: {
      pass: 'CAN transceivers initialized successfully',
      fail: 'Waiting for CAN transceiver initialization',
    },
    core_services: {
      pass: 'All core services operational',
      fail: 'Core services not fully initialized',
    },
    entity_discovery: {
      pass: 'Entities discovered and ready',
      fail: 'No entities discovered yet',
      warn: 'Limited entities discovered',
    },
    protocol_systems: {
      pass: 'Protocol handlers operational',
      fail: 'Protocol systems not ready',
    },
    safety_systems: {
      pass: 'Safety monitoring active',
      fail: 'Safety systems offline',
    },
    api_systems: {
      pass: 'API endpoints ready',
      fail: 'API systems not available',
    },
  };

  return messages[name]?.[status] || `${formatComponentName(name)} - ${status}`;
}

export default function HealthDashboard() {
  const [technicianMode, setTechnicianMode] = useState(false);
  const { data: health, isLoading } = useSystemHealthStatus();
  const { data: readiness } = useReadinessCheck(technicianMode);
  const { data: monitoring } = useHealthMonitoring(technicianMode);

  if (isLoading) {
    return (
      <AppLayout pageTitle="System Health">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      </AppLayout>
    );
  }

  // Transform health checks into components array
  const components = Object.entries(health?.checks || {}).map(([name, check]) => {
    const isCritical = health?.issues?.critical?.failed?.includes(name) ||
                      health?.issues?.critical?.degraded?.includes(name);
    const isWarning = health?.issues?.warning?.failed?.includes(name) ||
                     health?.issues?.warning?.degraded?.includes(name);

    return {
      name,
      status: check.status === 'fail' ? 'critical' :
              check.status === 'warn' ? 'warning' : 'ok',
      isCritical,
      isWarning,
      message: getComponentMessage(name, check.status),
      check,
    };
  });

  // Sort: critical first, then warnings, then ok
  const sortedComponents = components.sort((a, b) => {
    const statusOrder = { critical: 0, warning: 1, ok: 2 };
    return statusOrder[a.status as keyof typeof statusOrder] - statusOrder[b.status as keyof typeof statusOrder];
  });

  return (
    <AppLayout pageTitle="System Health">
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">System Health Dashboard</h2>
            <p className="text-muted-foreground">
              Monitor system components and health status
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="technician-mode" className="text-sm font-medium">
              Technician Mode
            </Label>
            <Switch
              id="technician-mode"
              checked={technicianMode}
              onCheckedChange={setTechnicianMode}
            />
          </div>
        </div>

        {/* Overall Status Alert */}
        {health && (
          <Alert variant={health.status === 'pass' ? 'default' : 'destructive'}>
            {health.status === 'pass' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertTitle>
              {health.status === 'pass' ? 'System Healthy' : 'System Issues Detected'}
            </AlertTitle>
            <AlertDescription>
              {health.description}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="status" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="status">System Status</TabsTrigger>
            <TabsTrigger value="components">Components</TabsTrigger>
            {technicianMode && (
              <TabsTrigger value="monitoring">Performance</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="status" className="space-y-4">
            {/* Service Information */}
            <Card>
              <CardHeader>
                <CardTitle>Service Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-muted-foreground">Service Name</dt>
                    <dd className="font-medium">{health?.service?.name}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Version</dt>
                    <dd className="font-medium">{health?.service?.version}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Environment</dt>
                    <dd className="font-medium">{health?.service?.environment}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Response Time</dt>
                    <dd className="font-medium">{health?.response_time_ms}ms</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Entity Count
                  </CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {readiness?.data?.metrics?.entity_count || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Enabled Features
                  </CardTitle>
                  <Server className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {readiness?.data?.metrics?.enabled_features || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Critical Systems
                  </CardTitle>
                  {readiness?.data?.metrics?.critical_systems_healthy ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-destructive" />
                  )}
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {readiness?.data?.metrics?.critical_systems_healthy ? 'Healthy' : 'Issues'}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Warning Systems
                  </CardTitle>
                  {readiness?.data?.metrics?.warning_systems_healthy ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                  )}
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {readiness?.data?.metrics?.warning_systems_healthy ? 'Healthy' : 'Warnings'}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="components" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {sortedComponents.map((component) => {
                const Icon = getComponentIcon(component.name);
                const statusConfig = {
                  ok: { color: 'text-green-600', bg: 'bg-green-100', badge: 'default' as const },
                  warning: { color: 'text-yellow-600', bg: 'bg-yellow-100', badge: 'secondary' as const },
                  critical: { color: 'text-red-600', bg: 'bg-red-100', badge: 'destructive' as const },
                };
                const config = statusConfig[component.status as keyof typeof statusConfig];

                return (
                  <Card key={component.name} className={component.status === 'critical' ? 'ring-2 ring-destructive' : ''}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Icon className={`h-5 w-5 ${config.color}`} />
                          {formatComponentName(component.name)}
                        </CardTitle>
                        {component.isCritical && (
                          <Badge variant="destructive" className="text-xs">
                            Safety Critical
                          </Badge>
                        )}
                      </div>
                      <CardDescription>{component.message}</CardDescription>
                    </CardHeader>
                    {technicianMode && readiness?.data?.detailed_checks?.[component.name] && (
                      <CardContent>
                        <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                          {JSON.stringify(readiness?.data?.detailed_checks?.[component.name]?.details, null, 2)}
                        </pre>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {technicianMode && monitoring && (
            <TabsContent value="monitoring" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Health Endpoint Performance</CardTitle>
                  <CardDescription>
                    Response times and success rates for health monitoring endpoints
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {monitoring && Object.entries(monitoring.endpoints).map(([endpoint, metrics]) => (
                      <div key={endpoint} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{endpoint}</span>
                          <Badge variant={metrics.health_status === 'ok' ? 'default' : 'destructive'}>
                            {metrics.health_status}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Avg Response:</span> {metrics.avg_response_time_ms.toFixed(2)}ms
                          </div>
                          <div>
                            <span className="text-muted-foreground">Success Rate:</span> {(metrics.success_rate * 100).toFixed(1)}%
                          </div>
                          <div>
                            <span className="text-muted-foreground">Failures:</span> {metrics.consecutive_failures}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {monitoring.alerts.length > 0 && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Active Alerts</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1">
                      {monitoring.alerts.map((alert, i) => (
                        <li key={i}>{alert}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>
          )}
        </Tabs>
      </div>
    </AppLayout>
  );
}
