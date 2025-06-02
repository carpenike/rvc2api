/**
 * Enhanced Dashboard Page
 *
 * Provides system overview with health status, CAN bus monitoring,
 * quick actions, real-time updates, and RV-specific control cards.
 */

import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useEntities } from "@/hooks/useEntities"
import { useCANStatistics, useHealthStatus } from "@/hooks/useSystem"
import {
  IconActivity,
  IconAlertCircle,
  IconBolt,
  IconCheck,
  IconCircuitSwitchOpen,
  IconCpu,
  IconHelp,
  IconWifi,
  IconX
} from "@tabler/icons-react"
import { Link } from "react-router-dom"

/**
 * System health status card component with enhanced visual design
 */
function SystemHealthCard() {
  const { data: health, isLoading, error } = useHealthStatus()

  // Helper function to get status icon and color
  const getStatusIndicator = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'ok':
        return { icon: IconCheck, color: 'text-green-500', bgColor: 'bg-green-50', borderColor: 'border-green-200' }
      case 'error':
      case 'failed':
        return { icon: IconX, color: 'text-red-500', bgColor: 'bg-red-50', borderColor: 'border-red-200' }
      case 'degraded':
      case 'warning':
        return { icon: IconAlertCircle, color: 'text-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200' }
      case 'unknown':
      default:
        return { icon: IconHelp, color: 'text-gray-500', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' }
    }
  }

  // Helper function to format feature names
  const formatFeatureName = (feature: string) => {
    return feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
  }

  // Helper function to parse and format status messages
  const parseStatusMessage = (status: string) => {
    // Extract entity count if present (e.g., "healthy (28 entities)")
    const entityMatch = status.match(/(.+?)\s*\((\d+)\s+entities?\)/)
    if (entityMatch) {
      return {
        status: entityMatch[1].trim(),
        entityCount: parseInt(entityMatch[2]),
        hasEntities: true
      }
    }
    return {
      status: status.trim(),
      entityCount: null,
      hasEntities: false
    }
  }

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
          <Skeleton className="h-4 w-full mb-3" />
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
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
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
            <IconAlertCircle className="size-4 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-700">
              Unable to load system health status
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const overallIndicator = getStatusIndicator(health?.status || 'unknown')
  const OverallIcon = overallIndicator.icon

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="size-5" />
          System Health
        </CardTitle>
        <CardDescription>Current system status and diagnostics</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall Status - Prominent Display */}
          <div className={`p-3 rounded-lg border ${overallIndicator.bgColor} ${overallIndicator.borderColor}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <OverallIcon className={`size-5 ${overallIndicator.color}`} />
                <span className="font-semibold text-gray-900">Overall Status</span>
              </div>
              <Badge
                variant={health?.status === "ok" ? "default" : "destructive"}
                className="capitalize"
              >
                {health?.status || "unknown"}
              </Badge>
            </div>
          </div>

          {/* Feature Status List */}
          {health?.features && Object.keys(health.features).length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-gray-700 border-b pb-1">
                Feature Status
              </h4>
              {Object.entries(health.features).map(([feature, status]) => {
                const parsedStatus = parseStatusMessage(status)
                const indicator = getStatusIndicator(parsedStatus.status)
                const StatusIcon = indicator.icon

                return (
                  <div key={feature} className="flex items-center justify-between p-2 rounded-md bg-gray-50 border border-gray-100">
                    <div className="flex items-center gap-2">
                      <StatusIcon className={`size-4 ${indicator.color} flex-shrink-0`} />
                      <span className="text-sm font-medium text-gray-700">
                        {formatFeatureName(feature)}
                      </span>
                      {parsedStatus.hasEntities && (
                        <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                          {parsedStatus.entityCount} entities
                        </span>
                      )}
                    </div>
                    <Badge
                      variant={parsedStatus.status === "healthy" ? "default" :
                               parsedStatus.status === "unknown" ? "secondary" : "destructive"}
                      className="text-xs"
                    >
                      {parsedStatus.status}
                    </Badge>
                  </div>
                )
              })}
            </div>
          )}

          {/* Unhealthy Features - Enhanced Error Display */}
          {health?.unhealthy_features && Object.keys(health.unhealthy_features).length > 0 && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <IconAlertCircle className="size-5 text-red-500" />
                <h4 className="text-sm font-semibold text-red-800">
                  Issues Detected ({Object.keys(health.unhealthy_features).length})
                </h4>
              </div>
              <div className="space-y-2">
                {Object.entries(health.unhealthy_features).map(([feature, status]) => {
                  const parsedStatus = parseStatusMessage(status)

                  return (
                    <div key={feature} className="bg-white p-2 rounded-md border border-red-100">
                      <div className="flex items-start gap-2">
                        <IconX className="size-4 text-red-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-red-800">
                              {formatFeatureName(feature)}
                            </span>
                            <Badge variant="destructive" className="text-xs">
                              {parsedStatus.status}
                            </Badge>
                          </div>
                          {parsedStatus.hasEntities && (
                            <p className="text-xs text-red-600">
                              Affects {parsedStatus.entityCount} entities
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* No Features Message */}
          {(!health?.features || Object.keys(health.features).length === 0) &&
           (!health?.unhealthy_features || Object.keys(health.unhealthy_features).length === 0) && (
            <div className="text-center py-4">
              <IconHelp className="size-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No feature status information available</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * CAN bus status card component
 */
function CANBusStatusCard() {
  const { data: canStats, isLoading, error } = useCANStatistics()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconWifi className="size-5" />
            <Skeleton className="h-5 w-32" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <IconWifi className="size-5" />
            CAN Bus Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Unable to load CAN bus statistics
          </p>
        </CardContent>
      </Card>
    )
  }

  const totalMessages = canStats?.total_messages || 0
  const totalErrors = canStats?.total_errors || 0
  const interfaceCount = canStats?.interfaces ? Object.keys(canStats.interfaces).length : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconWifi className="size-5" />
          CAN Bus Status
        </CardTitle>
        <CardDescription>Real-time CAN network monitoring</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{totalMessages.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">Total Messages</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-destructive">{totalErrors}</div>
              <div className="text-xs text-muted-foreground">Errors</div>
            </div>
          </div>
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Interfaces</span>
              <Badge variant="outline">{interfaceCount} active</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Entity summary card component
 */
function EntitySummaryCard() {
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
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
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
            Devices Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Unable to load device information
          </p>
        </CardContent>
      </Card>
    )
  }

  const entityArray = entities ? Object.values(entities) : []
  const totalEntities = entityArray.length
  const lightCount = entityArray.filter(e => e.device_type === 'light').length
  const lockCount = entityArray.filter(e => e.device_type === 'lock').length
  const sensorCount = entityArray.filter(e =>
    e.device_type === 'tank_sensor' || e.device_type === 'temperature_sensor'
  ).length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconCpu className="size-5" />
          Devices Overview
        </CardTitle>
        <CardDescription>Connected entities and sensors</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="text-center">
            <div className="text-3xl font-bold">{totalEntities}</div>
            <div className="text-xs text-muted-foreground">Total Devices</div>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-2 border-t">
            <div className="text-center">
              <div className="text-lg font-semibold">{lightCount}</div>
              <div className="text-xs text-muted-foreground">Lights</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{lockCount}</div>
              <div className="text-xs text-muted-foreground">Locks</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{sensorCount}</div>
              <div className="text-xs text-muted-foreground">Sensors</div>
            </div>
          </div>
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
 * RV Power Management card component
 */
function RVPowerManagementCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconBolt className="size-5" />
          Power Management
        </CardTitle>
        <CardDescription>Monitor and control power systems</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="w-full justify-start">
            <IconBolt className="mr-2 size-4" />
            Battery Status
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconBolt className="mr-2 size-4" />
            Inverter Control
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconBolt className="mr-2 size-4" />
            Shore Power
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * RV Climate Control card component
 */
function RVClimateControlCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconWifi className="size-5" />
          Climate Control
        </CardTitle>
        <CardDescription>Temperature and ventilation control</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="w-full justify-start">
            <IconWifi className="mr-2 size-4" />
            Air Conditioning
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconWifi className="mr-2 size-4" />
            Heating
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconWifi className="mr-2 size-4" />
            Ventilation
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * RV Water System card component
 */
function RVWaterSystemCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconCpu className="size-5" />
          Water System
        </CardTitle>
        <CardDescription>Fresh water and waste management</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="w-full justify-start">
            <IconCpu className="mr-2 size-4" />
            Fresh Water
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconCpu className="mr-2 size-4" />
            Gray Water
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconCpu className="mr-2 size-4" />
            Black Water
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * RV Slide Outs card component
 */
function RVSlideOutsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="size-5" />
          Slide Outs
        </CardTitle>
        <CardDescription>Extend and retract slide out rooms</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="w-full justify-start">
            <IconActivity className="mr-2 size-4" />
            Main Slide
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconActivity className="mr-2 size-4" />
            Bedroom Slide
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconActivity className="mr-2 size-4" />
            Kitchen Slide
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * RV Awnings & Steps card component
 */
function RVAwningsStepsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconCheck className="size-5" />
          Awnings & Steps
        </CardTitle>
        <CardDescription>Deploy awnings and entry steps</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Button variant="outline" className="w-full justify-start">
            <IconCheck className="mr-2 size-4" />
            Main Awning
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconCheck className="mr-2 size-4" />
            Door Awning
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <IconCheck className="mr-2 size-4" />
            Entry Steps
          </Button>
        </div>
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

        {/* Dashboard Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <SystemHealthCard />
          </div>
          <div>
            <CANBusStatusCard />
          </div>
          <div>
            <EntitySummaryCard />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <QuickActionsCard />
          </div>
          <div className="md:col-span-2">
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

        {/* RV Control Systems */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">RV Control Systems</h2>
              <p className="text-muted-foreground">
                Monitor and control key RV systems and components
              </p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <RVPowerManagementCard />
            <RVClimateControlCard />
            <RVWaterSystemCard />
            <RVSlideOutsCard />
            <RVAwningsStepsCard />
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
