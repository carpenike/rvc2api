/**
 * Dashboard Page - User-focused overview
 *
 * Provides high-level system overview, device counts, and quick access
 * to main user functions. Technical diagnostics moved to System Status.
 */

import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useEntities } from "@/hooks/useEntities"
import { useHealthStatus } from "@/hooks/useSystem"
import { useDashboardState, useActivityFeed } from "@/hooks/useDashboard"
import {
    IconActivity,
    IconAlertCircle,
    IconBolt,
    IconCpu,
    IconCheck,
    IconHelp,
    IconTrendingUp,
    IconX
} from "@tabler/icons-react"
import { Link } from "react-router-dom"

/**
 * Simple system health indicator for dashboard
 */
function SystemHealthCard() {
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
          <Skeleton className="h-16 w-full" />
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
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Unable to check system health</p>
        </CardContent>
      </Card>
    )
  }

  const isHealthy = health?.status === "healthy"

  return (
    <Card className="@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs">
      <CardHeader>
        <CardTitle className="@[250px]/card:text-lg flex items-center gap-2">
          <IconActivity className="size-5" />
          System Health
        </CardTitle>
        <CardDescription>Overall system status</CardDescription>
        <CardAction>
          <Badge variant={isHealthy ? "default" : "destructive"}>
            {isHealthy ? "Operational" : "Issues"}
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center p-6">
          <div className="text-center">
            {isHealthy ? (
              <IconCheck className="size-12 text-green-500 mx-auto mb-2" />
            ) : (
              <IconAlertCircle className="size-12 text-amber-500 mx-auto mb-2" />
            )}
            <div className="font-semibold text-lg">
              {isHealthy ? "System Healthy" : "Attention Needed"}
            </div>
            <Button asChild variant="ghost" size="sm" className="mt-2">
              <Link to="/system-status">
                View Details →
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


/**
 * Enhanced device summary card with trends
 */
function DeviceOverviewCard() {
  const { data: entities, isLoading, error } = useEntities()

  if (isLoading) {
    return (
      <Card className="@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs">
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
      <Card className="@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs">
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
    e.device_type === 'tank_sensor' || e.device_type === 'temperature_sensor' ||
    e.device_type === 'tank' || e.device_type === 'temperature'
  ).length

  // Calculate online devices (devices seen in last 5 minutes)
  const onlineDevices = entityArray.filter(e =>
    e.timestamp && (Date.now() - e.timestamp) < 300000
  ).length

  // Mock trend calculation (in real app, compare with previous data)
  const deviceTrend: 'up' | 'down' | 'neutral' = totalEntities > 0 ? 'up' : 'neutral'

  return (
    <Card className="@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs">
      <CardHeader>
        <CardTitle className="@[250px]/card:text-lg flex items-center gap-2">
          <IconCpu className="size-5" />
          Connected Devices
        </CardTitle>
        <CardDescription>Quick overview of your RV systems</CardDescription>
        <CardAction>
          <Badge variant="outline">
            {deviceTrend === 'up' && <IconTrendingUp className="mr-1 h-3 w-3" />}
            {onlineDevices}/{totalEntities} Online
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">{totalEntities}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">{lightCount}</div>
            <div className="text-xs text-muted-foreground">Lights</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">{sensorCount}</div>
            <div className="text-xs text-muted-foreground">Sensors</div>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t">
          <Button asChild variant="outline" size="sm" className="w-full">
            <Link to="/entities">
              Manage Devices
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * User-focused quick actions card
 */
function QuickActionsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconBolt className="size-5" />
          Quick Actions
        </CardTitle>
        <CardDescription>Control your RV systems</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/lights">
            <IconBolt className="mr-2 size-4" />
            Control Lights
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/entities">
            <IconCpu className="mr-2 size-4" />
            Manage Devices
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/system-status">
            <IconActivity className="mr-2 size-4" />
            System Status
          </Link>
        </Button>
        <Button asChild className="w-full justify-start" variant="outline">
          <Link to="/documentation">
            <IconHelp className="mr-2 size-4" />
            Documentation
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}

/**
 * Activity feed card component
 */
function ActivityFeedCard() {
  const { data: activityFeed, isLoading, error } = useActivityFeed({ limit: 10 })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events and updates</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3">
              <Skeleton className="h-2 w-2 rounded-full mt-2" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error || !activityFeed) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events and updates</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Unable to load activity feed at this time.
          </p>
        </CardContent>
      </Card>
    )
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'text-red-500'
      case 'warning': return 'text-yellow-500'
      case 'info': return 'text-blue-500'
      default: return 'text-muted-foreground'
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`

    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`

    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="size-5" />
          Recent Activity
        </CardTitle>
        <CardDescription>Latest system events and updates</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activityFeed.entries.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No recent activity to display
            </p>
          ) : (
            activityFeed.entries.map((entry) => (
              <div key={entry.id} className="flex items-start gap-3 pb-3 last:pb-0 border-b last:border-0">
                <div className={`w-2 h-2 rounded-full mt-2 ${getSeverityColor(entry.severity).replace('text-', 'bg-')}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{entry.title}</p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {entry.description}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground flex-shrink-0">
                      {formatTimeAgo(entry.timestamp)}
                    </span>
                  </div>
                  {entry.entity_id && (
                    <div className="mt-2">
                      <Badge variant="outline" className="text-xs">
                        {entry.entity_id}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {activityFeed.has_more && (
            <Button asChild variant="ghost" size="sm" className="w-full">
              <Link to="/logs">
                View All Activity
                <IconActivity className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Enhanced Dashboard Page Component
 */
export default function Dashboard() {
  const { summary, isLoading, error, refresh } = useDashboardState()

  if (error) {
    return (
      <AppLayout pageTitle="Dashboard">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
              <p className="text-muted-foreground">
                System overview and quick access to key functions
              </p>
            </div>
            <Button onClick={refresh} variant="outline" className="gap-2">
              <IconActivity className="h-4 w-4" />
              Retry
            </Button>
          </div>

          <Card>
            <CardContent className="p-6 text-center">
              <IconX className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Unable to Load Dashboard</h3>
              <p className="text-muted-foreground">
                There was an error loading your dashboard data. Please check your connection and try again.
              </p>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    )
  }

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
          <Button onClick={refresh} variant="outline" className="gap-2" disabled={isLoading}>
            <IconActivity className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* System Alerts */}
        {summary?.alerts && summary.alerts.length > 0 && (
          <div className="grid gap-2">
            {summary.alerts.map((alert, index) => (
              <Alert key={index} variant="destructive">
                <IconAlertCircle className="h-4 w-4" />
                <AlertTitle>System Alert</AlertTitle>
                <AlertDescription>{alert}</AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {/* Overview Cards - Enhanced with summary data */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <DeviceOverviewCard />
          </div>
          <div>
            <SystemHealthCard />
          </div>
        </div>

        {/* Quick Actions and Activity Feed */}
        <div className="grid gap-6 md:grid-cols-2">
          <QuickActionsCard />
          <ActivityFeedCard />
        </div>
      </div>
    </AppLayout>
  )
}
