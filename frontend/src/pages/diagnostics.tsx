/**
 * Advanced Diagnostics Page
 *
 * Comprehensive diagnostic dashboard showing DTCs, system health,
 * fault correlations, and maintenance predictions in a user-friendly format.
 *
 * Implements Gemini's Tier 1 recommendations:
 * - Human-readable diagnostic messages
 * - Clear system health indicators
 * - Mobile-friendly interface
 * - Peace of mind focus
 */

import { useState } from "react"
import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useDiagnosticsState, useResolveDTC } from "@/hooks/useDiagnostics"
import SmartManualCard from "@/components/diagnostics/SmartManualCard"
import type { DiagnosticTroubleCode, DTCFilters } from "@/api/types"
import {
  IconActivity,
  IconAlertCircle,
  IconAlertTriangle,
  IconBook,
  IconCheck,
  IconClock,
  IconInfoCircle,
  IconRefresh,
  IconShield,
  IconTool,
  IconTrendingUp,
  IconX,
  IconXboxX
} from "@tabler/icons-react"

/**
 * Helper function to convert technical DTCs to human-readable messages
 */
function getHumanReadableMessage(dtc: DiagnosticTroubleCode): string {
  const system = dtc.system_type.toLowerCase()
  const code = dtc.code.toLowerCase()

  // Create human-readable messages based on system and common fault patterns
  if (system.includes('engine')) {
    if (code.includes('temp') || dtc.description.toLowerCase().includes('temperature')) {
      return "Engine Temperature Issue: Engine running too hot. Check coolant level and radiator."
    }
    if (code.includes('oil') || dtc.description.toLowerCase().includes('pressure')) {
      return "Engine Oil Pressure: Low oil pressure detected. Check oil level and pump."
    }
    return `Engine Issue: ${dtc.description || 'Engine system requires attention'}`
  }

  if (system.includes('power') || system.includes('electrical')) {
    if (code.includes('volt') || dtc.description.toLowerCase().includes('voltage')) {
      return "Electrical System: Voltage issue detected. Check battery and charging system."
    }
    return `Power System: ${dtc.description || 'Electrical system requires attention'}`
  }

  if (system.includes('climate') || system.includes('hvac')) {
    return `Climate Control: ${dtc.description || 'HVAC system requires attention'}`
  }

  if (system.includes('lighting')) {
    return `Lighting System: ${dtc.description || 'Light circuit issue detected'}`
  }

  if (system.includes('tank') || system.includes('water')) {
    return `Water System: ${dtc.description || 'Water or tank system issue detected'}`
  }

  // Default fallback with system name
  return `${system.charAt(0).toUpperCase() + system.slice(1)} System: ${dtc.description || 'System requires attention'}`
}

/**
 * DTC Severity Badge Component
 */
function DTCSeverityBadge({ severity }: { severity: string }) {
  const variants = {
    critical: { variant: "destructive" as const, icon: IconAlertCircle, label: "Critical" },
    high: { variant: "destructive" as const, icon: IconAlertTriangle, label: "High" },
    medium: { variant: "secondary" as const, icon: IconClock, label: "Medium" },
    low: { variant: "outline" as const, icon: IconInfoCircle, label: "Low" },
    info: { variant: "outline" as const, icon: IconInfoCircle, label: "Info" },
  }

  const config = variants[severity as keyof typeof variants] || variants.info
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}

/**
 * System Health Overview Card - Peace of Mind Focus
 */
function SystemHealthCard() {
  const { stats, isLoading, error } = useDiagnosticsState()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconShield className="size-5" />
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

  const isHealthy = (stats?.active_dtcs || 0) === 0
  const healthTrend = stats?.system_health_trend || 'stable'

  const trendIcons = {
    improving: { icon: IconTrendingUp, color: "text-green-500" },
    stable: { icon: IconActivity, color: "text-blue-500" },
    degrading: { icon: IconAlertTriangle, color: "text-amber-500" },
  }

  const TrendIcon = trendIcons[healthTrend as keyof typeof trendIcons]?.icon || IconActivity
  const trendColor = trendIcons[healthTrend as keyof typeof trendIcons]?.color || "text-blue-500"

  return (
    <Card className="@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs">
      <CardHeader>
        <CardTitle className="@[250px]/card:text-lg flex items-center gap-2">
          <IconShield className="size-5" />
          System Health
        </CardTitle>
        <CardDescription>Overall diagnostic status</CardDescription>
        <CardAction>
          <Badge variant={isHealthy ? "default" : "destructive"}>
            {isHealthy ? "All Systems Normal" : "Issues Detected"}
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
              {isHealthy ? "Everything looks good!" : "Attention needed"}
            </div>
            <div className="text-sm text-muted-foreground mt-1">
              {isHealthy
                ? "All vehicle systems are operating normally"
                : `${stats?.active_dtcs || 0} active diagnostic codes`
              }
            </div>
            <div className="flex items-center justify-center gap-1 mt-2">
              <TrendIcon className={`size-4 ${trendColor}`} />
              <span className="text-sm capitalize">{healthTrend}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Active DTCs List Component - Human-Readable Focus
 */
function ActiveDTCsList({ filters }: { filters?: DTCFilters }) {
  const { dtcs, isLoading, error } = useDiagnosticsState(filters)
  const resolveDTC = useResolveDTC()

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 p-4 border rounded-lg">
            <Skeleton className="h-4 w-4 rounded-full mt-1" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-6 w-16" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <IconAlertCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Issues</AlertTitle>
        <AlertDescription>
          Unable to load diagnostic information. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    )
  }

  if (!dtcs || dtcs.dtcs.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <IconCheck className="h-12 w-12 mx-auto mb-4 text-green-500" />
          <h3 className="text-lg font-semibold mb-2">No Active Issues</h3>
          <p className="text-muted-foreground">
            All systems are operating normally with no diagnostic trouble codes.
          </p>
        </CardContent>
      </Card>
    )
  }

  const handleResolveDTC = (dtc: DiagnosticTroubleCode) => {
    resolveDTC.mutate({
      protocol: dtc.protocol,
      code: typeof dtc.code === 'string' ? parseInt(dtc.code, 16) : dtc.code,
      sourceAddress: dtc.source_address,
    })
  }

  return (
    <div className="space-y-3">
      {dtcs.dtcs.map((dtc) => (
        <Card key={`${dtc.protocol}-${dtc.code}-${dtc.source_address}`}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                <DTCSeverityBadge severity={dtc.severity} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm leading-5 mb-1">
                      {getHumanReadableMessage(dtc)}
                    </h4>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <div>System: {dtc.system_type} • Code: {dtc.code}</div>
                      <div>
                        First seen: {new Date(dtc.first_seen).toLocaleDateString()} •
                        {dtc.count > 1 && ` Occurred ${dtc.count} times`}
                      </div>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleResolveDTC(dtc)}
                      disabled={resolveDTC.isPending || dtc.resolved}
                      className="gap-2"
                    >
                      <IconCheck className="h-3 w-3" />
                      {dtc.resolved ? 'Resolved' : 'Mark Fixed'}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/**
 * DTC Filters Component
 */
function DTCFilters({
  filters,
  onFiltersChange
}: {
  filters: DTCFilters
  onFiltersChange: (filters: DTCFilters) => void
}) {
  return (
    <div className="flex gap-3 flex-wrap">
      <Select
        value={filters.severity || "all"}
        onValueChange={(value) => onFiltersChange({ ...filters, severity: value === "all" ? undefined : value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Severity" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Severities</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
          <SelectItem value="info">Info</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.protocol || "all"}
        onValueChange={(value) => onFiltersChange({ ...filters, protocol: value === "all" ? undefined : value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Protocol" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Protocols</SelectItem>
          <SelectItem value="rvc">RV-C</SelectItem>
          <SelectItem value="j1939">J1939</SelectItem>
          <SelectItem value="firefly">Firefly</SelectItem>
          <SelectItem value="spartan_k2">Spartan K2</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.system_type || "all"}
        onValueChange={(value) => onFiltersChange({ ...filters, system_type: value === "all" ? undefined : value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="System" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Systems</SelectItem>
          <SelectItem value="lighting">Lighting</SelectItem>
          <SelectItem value="climate">Climate</SelectItem>
          <SelectItem value="power">Power</SelectItem>
          <SelectItem value="engine">Engine</SelectItem>
          <SelectItem value="transmission">Transmission</SelectItem>
        </SelectContent>
      </Select>

      {(filters.severity || filters.protocol || filters.system_type) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFiltersChange({})}
          className="gap-2"
        >
          <IconXboxX className="h-3 w-3" />
          Clear Filters
        </Button>
      )}
    </div>
  )
}

/**
 * Diagnostic Statistics Component
 */
function DiagnosticStatsCard() {
  const { stats, isLoading, error } = useDiagnosticsState()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="text-center">
                <Skeleton className="h-8 w-16 mx-auto mb-2" />
                <Skeleton className="h-4 w-20 mx-auto" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center">
            Unable to load system statistics
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="size-5" />
          System Statistics
        </CardTitle>
        <CardDescription>Diagnostic system performance</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums">{stats.total_dtcs}</div>
            <div className="text-xs text-muted-foreground">Total Issues</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums">{stats.resolved_dtcs}</div>
            <div className="text-xs text-muted-foreground">Resolved</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums">{stats.correlation_accuracy.toFixed(1)}%</div>
            <div className="text-xs text-muted-foreground">Accuracy</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold tabular-nums capitalize">{stats.system_health_trend}</div>
            <div className="text-xs text-muted-foreground">Trend</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Main Advanced Diagnostics Page Component
 */
export default function AdvancedDiagnostics() {
  const [filters, setFilters] = useState<DTCFilters>({})
  const { dtcs, isLoading, error, refresh } = useDiagnosticsState(filters)

  if (error) {
    return (
      <AppLayout pageTitle="System Health">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
              <p className="text-muted-foreground">
                Vehicle system monitoring and diagnostic information
              </p>
            </div>
            <Button onClick={refresh} variant="outline" className="gap-2">
              <IconRefresh className="h-4 w-4" />
              Retry
            </Button>
          </div>

          <Card>
            <CardContent className="p-6 text-center">
              <IconX className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Unable to Load System Health</h3>
              <p className="text-muted-foreground">
                There was an error loading diagnostic data. Please check your connection and try again.
              </p>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout pageTitle="System Health">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
            <p className="text-muted-foreground">
              Vehicle system monitoring and diagnostic information
            </p>
          </div>
          <Button onClick={refresh} variant="outline" className="gap-2" disabled={isLoading}>
            <IconRefresh className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Overview Cards */}
        <div className="grid gap-6 md:grid-cols-2">
          <SystemHealthCard />
          <DiagnosticStatsCard />
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="issues" className="space-y-4">
          <TabsList>
            <TabsTrigger value="issues" className="gap-2">
              <IconAlertTriangle className="h-4 w-4" />
              Current Issues
            </TabsTrigger>
            <TabsTrigger value="help" className="gap-2">
              <IconBook className="h-4 w-4" />
              Smart Manual
            </TabsTrigger>
            <TabsTrigger value="maintenance" className="gap-2">
              <IconTool className="h-4 w-4" />
              Maintenance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="issues" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Current System Issues</h2>
              <DTCFilters filters={filters} onFiltersChange={setFilters} />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <ActiveDTCsList filters={filters} />
              </div>
              <div>
                <SmartManualCard
                  activeDTC={dtcs?.dtcs && dtcs.dtcs.length > 0 ? dtcs.dtcs[0] : undefined}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="help" className="space-y-4">
            <h2 className="text-lg font-semibold">Smart Manual & Troubleshooting</h2>
            <SmartManualCard />
          </TabsContent>

          <TabsContent value="maintenance" className="space-y-4">
            <h2 className="text-lg font-semibold">Maintenance Recommendations</h2>
            <Card>
              <CardContent className="p-6 text-center">
                <IconTool className="h-12 w-12 mx-auto mb-4 text-green-500" />
                <h3 className="text-lg font-semibold mb-2">Predictive Maintenance Active</h3>
                <p className="text-muted-foreground mb-4">
                  Visit the <strong>Maintenance</strong> page for detailed component health tracking, trend analysis, and maintenance recommendations.
                </p>
                <Button variant="outline" onClick={() => window.location.href = '/maintenance'} className="gap-2">
                  <IconTool className="h-4 w-4" />
                  View Maintenance Dashboard
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}
