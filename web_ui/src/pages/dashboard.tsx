/**
 * Dashboard Page - User-focused overview
 *
 * Provides high-level system overview, device counts, and quick access
 * to main user functions. Technical diagnostics moved to System Status.
 */

import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useEntities } from "@/hooks/useEntities"
import { useHealthStatus } from "@/hooks/useSystem"
import {
    IconActivity,
    IconAlertCircle,
    IconBolt,
    IconCircuitSwitchOpen,
    IconCpu,
    IconCheck,
    IconWifi,
    IconX
} from "@tabler/icons-react"
import { Link } from "react-router-dom"

/**
 * Simplified system status card for dashboard (user-focused)
 */
function SystemStatusOverviewCard() {
  const { data: health, isLoading, error } = useHealthStatus()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconActivity className="size-5" />
            <Skeleton className="h-5 w-32" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-12 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <IconX className="size-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Unable to load system status</p>
        </CardContent>
      </Card>
    )
  }

  const isHealthy = health?.status === "healthy"
  const hasIssues = health?.unhealthy_features && Object.keys(health.unhealthy_features).length > 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="size-5" />
          System Status
        </CardTitle>
        <CardDescription>Current system health overview</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-3">
            {isHealthy ? (
              <IconCheck className="size-6 text-green-500" />
            ) : hasIssues ? (
              <IconX className="size-6 text-red-500" />
            ) : (
              <IconAlertCircle className="size-6 text-amber-500" />
            )}
            <div>
              <div className="font-semibold">
                {isHealthy ? "All Systems Operational" : hasIssues ? "Issues Detected" : "System Status"}
              </div>
              <div className="text-sm text-muted-foreground">
                {hasIssues ? `${Object.keys(health?.unhealthy_features ?? {}).length} component(s) need attention` : "Systems running normally"}
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Badge variant={isHealthy ? "default" : hasIssues ? "destructive" : "secondary"}>
              {health?.status?.toUpperCase() || "UNKNOWN"}
            </Badge>
            <Button asChild variant="outline" size="sm">
              <Link to="/system-status">
                View Details
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


/**
 * Device summary card - simplified for dashboard
 */
function DeviceOverviewCard() {
  const { data: entities, isLoading, error } = useEntities()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconCpu className="size-5" />
            <Skeleton className="h-5 w-32" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-12 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <IconCpu className="size-5" />
            Connected Devices
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Unable to load device information</p>
        </CardContent>
      </Card>
    )
  }

  const entityArray = entities ? Object.values(entities) : []
  const totalEntities = entityArray.length
  const lightCount = entityArray.filter(e => e.device_type === 'light').length
  const sensorCount = entityArray.filter(e =>
    e.device_type === 'tank_sensor' || e.device_type === 'temperature_sensor'
  ).length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconCpu className="size-5" />
          Connected Devices
        </CardTitle>
        <CardDescription>Quick overview of your RV systems</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold">{totalEntities}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold">{lightCount}</div>
            <div className="text-xs text-muted-foreground">Lights</div>
          </div>
          <div className="text-center p-3 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold">{sensorCount}</div>
            <div className="text-xs text-muted-foreground">Sensors</div>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t">
          <Button asChild variant="outline" size="sm" className="w-full">
            <Link to="/lights">
              Manage Devices
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Quick actions card component
 */
function QuickActionsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconBolt className="size-5" />
          Quick Actions
        </CardTitle>
        <CardDescription>Common tasks and shortcuts</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/lights">
            <IconBolt className="mr-2 size-4" />
            Control Lights
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/can-sniffer">
            <IconWifi className="mr-2 size-4" />
            Monitor CAN Bus
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/device-mapping">
            <IconCpu className="mr-2 size-4" />
            Manage Devices
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/unknown-pgns">
            <IconCircuitSwitchOpen className="mr-2 size-4" />
            View Diagnostics
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}

/**
 * Enhanced Dashboard Page Component
 */
export default function Dashboard() {
  return (
    <AppLayout pageTitle="Dashboard">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              System overview and quick access to key functions
            </p>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <SystemStatusOverviewCard />
          </div>
          <div>
            <DeviceOverviewCard />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-6 md:grid-cols-2">
          <QuickActionsCard />
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest system events and updates</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Real-time activity feed will be implemented in a future update.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
