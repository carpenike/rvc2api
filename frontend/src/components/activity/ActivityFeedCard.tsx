/**
 * Enhanced Activity Feed Card
 *
 * Tier 1 Activity & Alert System implementation with:
 * - Human-readable activity messages
 * - Alert acknowledgment capabilities
 * - Mobile-friendly interface
 * - Real-time updates
 */

import type { ActivityEntry } from "@/api/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useAcknowledgeAlert, useActivityFeed } from "@/hooks/useDashboard"
import {
    IconActivity,
    IconAlertCircle,
    IconAlertTriangle,
    IconCheck,
    IconClock,
    IconInfoCircle,
    IconX
} from "@tabler/icons-react"
import { Link } from "react-router-dom"

/**
 * Convert technical activity messages to human-readable format
 */
function getHumanReadableActivity(entry: ActivityEntry): string {
  const { event_type, title, description, entity_id } = entry

  // System alerts and diagnostics
  if (event_type === "system_alert") {
    if (title.toLowerCase().includes("temperature")) {
      return "System Alert: Temperature monitoring detected an issue"
    }
    if (title.toLowerCase().includes("voltage") || title.toLowerCase().includes("battery")) {
      return "Power Alert: Battery or charging system needs attention"
    }
    if (title.toLowerCase().includes("engine")) {
      return "Engine Alert: Engine system requires attention"
    }
    return `System Alert: ${description || title}`
  }

  // Entity changes (device controls)
  if (event_type === "entity_change") {
    if (entity_id) {
      const deviceName = entity_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      if (description.toLowerCase().includes("turned on") || description.toLowerCase().includes("on")) {
        return `${deviceName} turned on`
      }
      if (description.toLowerCase().includes("turned off") || description.toLowerCase().includes("off")) {
        return `${deviceName} turned off`
      }
      if (description.toLowerCase().includes("brightness")) {
        return `${deviceName} brightness adjusted`
      }
      return `${deviceName}: ${description}`
    }
  }

  // Bulk operations
  if (event_type === "bulk_control") {
    const metadata = entry.metadata as Record<string, string | number>
    const command = metadata?.command || "controlled"
    const successful = metadata?.successful || 0
    const failed = metadata?.failed || 0

    if (failed === 0) {
      return `Bulk operation successful: ${successful} devices ${command}`
    } else {
      return `Bulk operation completed: ${successful} successful, ${failed} failed`
    }
  }

  // System events
  if (event_type === "system_startup") {
    return "System started successfully"
  }

  if (event_type === "system_shutdown") {
    return "System shutdown initiated"
  }

  // Connection events
  if (event_type === "can_interface") {
    if (description.toLowerCase().includes("connected")) {
      return "CAN network connected"
    }
    if (description.toLowerCase().includes("disconnected")) {
      return "CAN network disconnected"
    }
    return `Network: ${description}`
  }

  // Default fallback with improved formatting
  return description || title || "System activity"
}

/**
 * Get severity icon and styling
 */
function getSeverityIndicator(severity: string) {
  switch (severity) {
    case 'error':
      return {
        icon: IconAlertCircle,
        color: 'text-red-500',
        bgColor: 'bg-red-500',
        label: 'Error'
      }
    case 'warning':
      return {
        icon: IconAlertTriangle,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500',
        label: 'Warning'
      }
    case 'info':
      return {
        icon: IconInfoCircle,
        color: 'text-blue-500',
        bgColor: 'bg-blue-500',
        label: 'Info'
      }
    default:
      return {
        icon: IconClock,
        color: 'text-muted-foreground',
        bgColor: 'bg-muted',
        label: 'Event'
      }
  }
}

/**
 * Format timestamp for human readability
 */
function formatTimeAgo(timestamp: string | number): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString()
}

/**
 * Individual Activity Entry Component
 */
function ActivityEntryItem({ entry }: { entry: ActivityEntry }) {
  const acknowledgeAlert = useAcknowledgeAlert()
  const severity = getSeverityIndicator(entry.severity)
  const SeverityIcon = severity.icon

  const isAlert = entry.event_type === "system_alert" && entry.severity !== "info"
  const canAcknowledge = isAlert && !entry.metadata?.acknowledged

  const handleAcknowledge = () => {
    if (entry.id) {
      acknowledgeAlert.mutate(entry.id)
    }
  }

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border bg-card">
      <div className={`w-2 h-2 rounded-full mt-2 ${severity.bgColor}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">
              {getHumanReadableActivity(entry)}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-muted-foreground">
                {formatTimeAgo(entry.timestamp)}
              </span>
              {isAlert && (
                <Badge variant="outline" className="text-xs gap-1">
                  <SeverityIcon className="h-3 w-3" />
                  {severity.label}
                </Badge>
              )}
            </div>
          </div>

          {canAcknowledge && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAcknowledge}
              disabled={acknowledgeAlert.isPending}
              className="gap-1 h-6 px-2 text-xs"
            >
              <IconCheck className="h-3 w-3" />
              Acknowledge
            </Button>
          )}
        </div>

        {entry.entity_id && (
          <div className="mt-2">
            <Badge variant="outline" className="text-xs">
              {entry.entity_id.replace(/_/g, ' ')}
            </Badge>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Main Activity Feed Card Component
 */
export default function ActivityFeedCard() {
  const { data: activityFeed, isLoading, error } = useActivityFeed({ limit: 8 })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconActivity className="size-5" />
            Recent Activity
          </CardTitle>
          <CardDescription>What's happening with your RV</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg border">
              <Skeleton className="h-2 w-2 rounded-full mt-2" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-1/2" />
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
          <CardTitle className="flex items-center gap-2 text-destructive">
            <IconX className="size-5" />
            Recent Activity
          </CardTitle>
          <CardDescription>What's happening with your RV</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            Unable to load activity feed at this time.
          </p>
        </CardContent>
      </Card>
    )
  }

  const hasUnacknowledgedAlerts = activityFeed.entries.some(
    entry => entry.event_type === "system_alert" &&
             entry.severity !== "info" &&
             !entry.metadata?.acknowledged
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <IconActivity className="size-5" />
            Recent Activity
          </div>
          {hasUnacknowledgedAlerts && (
            <Badge variant="destructive" className="gap-1">
              <IconAlertTriangle className="h-3 w-3" />
              Alerts
            </Badge>
          )}
        </CardTitle>
        <CardDescription>What's happening with your RV</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activityFeed.entries.length === 0 ? (
            <div className="text-center py-6">
              <IconCheck className="h-8 w-8 mx-auto mb-2 text-green-500" />
              <p className="text-sm font-medium">All quiet!</p>
              <p className="text-xs text-muted-foreground">No recent activity to show</p>
            </div>
          ) : (
            activityFeed.entries.map((entry) => (
              <ActivityEntryItem key={entry.id} entry={entry} />
            ))
          )}

          {activityFeed.has_more && (
            <Button asChild variant="ghost" size="sm" className="w-full mt-4">
              <Link to="/logs" className="gap-2">
                View All Activity
                <IconActivity className="h-4 w-4" />
              </Link>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
