/**
 * CAN Sniffer Page
 *
 * Real-time CAN bus monitoring and packet analysis.
 * Shows live CAN traffic with filtering and analysis capabilities.
 */

import type { CANMessage } from "@/api/types"
import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useCANMessages, useCANMetrics } from "@/hooks/useSystem"
import {
    IconActivity,
    IconAlertTriangle,
    IconFilter,
    IconPlayerPause,
    IconPlayerPlay,
    IconRefresh,
    IconTrash
} from "@tabler/icons-react"
import { useMemo, useState } from "react"

/**
 * CAN message statistics component
 */
function CANStatistics({ messages }: { messages: CANMessage[] }) {
  const stats = useMemo(() => {
    const byPGN = messages.reduce((acc, msg) => {
      acc[msg.pgn] = (acc[msg.pgn] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const byInstance = messages.reduce((acc, msg) => {
      if (msg.instance !== undefined) {
        acc[msg.instance] = (acc[msg.instance] || 0) + 1
      }
      return acc
    }, {} as Record<number, number>)

    const totalMessages = messages.length
    const uniquePGNs = Object.keys(byPGN).length
    const errorMessages = messages.filter(msg => msg.error).length
    const lastMinute = messages.filter(msg =>
      Date.now() - new Date(msg.timestamp).getTime() < 60000
    ).length

    return {
      total: totalMessages,
      uniquePGNs,
      errorMessages,
      lastMinute,
      topPGNs: Object.entries(byPGN)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([pgn, count]) => ({ pgn, count })),
      topInstances: Object.entries(byInstance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([instance, count]) => ({ instance: Number(instance), count }))
    }
  }, [messages])

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
          <IconActivity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total}</div>
          <p className="text-xs text-muted-foreground">
            {stats.lastMinute} in last minute
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Unique PGNs</CardTitle>
          <IconFilter className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.uniquePGNs}</div>
          <p className="text-xs text-muted-foreground">
            Different message types
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Error Messages</CardTitle>
          <IconAlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.errorMessages}</div>
          <p className="text-xs text-muted-foreground">
            {stats.total > 0 ? Math.round((stats.errorMessages / stats.total) * 100) : 0}% error rate
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Message Rate</CardTitle>
          <IconActivity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.lastMinute}</div>
          <p className="text-xs text-muted-foreground">
            messages/minute
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * CAN message table component
 */
function CANMessageTable({
  messages,
  isPaused
}: {
  messages: CANMessage[]
  isPaused: boolean
}) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const timeStr = date.toLocaleTimeString([], {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
    const ms = date.getMilliseconds().toString().padStart(3, '0')
    return `${timeStr}.${ms}`
  }

  const formatData = (data: number[]) => {
    return data.map(byte => byte.toString(16).padStart(2, '0').toUpperCase()).join(' ')
  }

  const getPGNDescription = (pgn: string) => {
    // This would normally come from the RV-C spec database
    const knownPGNs: Record<string, string> = {
      '1FFFF': 'Device Control',
      '1FFF0': 'Light Control',
      '1FFE0': 'Tank Status',
      '1FFD0': 'Temperature',
      // Add more as needed
    }
    return knownPGNs[pgn] || 'Unknown'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="h-5 w-5" />
          Live CAN Messages
          {isPaused && <Badge variant="secondary">Paused</Badge>}
        </CardTitle>
        <CardDescription>
          Real-time CAN bus traffic monitoring
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <div className="max-h-96 overflow-auto">
            <Table>
              <TableHeader className="sticky top-0 bg-background">
                <TableRow>
                  <TableHead className="w-24">Time</TableHead>
                  <TableHead className="w-20">PGN</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-16">Inst</TableHead>
                  <TableHead className="w-16">Src</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead className="w-16">Len</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {messages.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      {isPaused ? "Message capture paused" : "No messages received"}
                    </TableCell>
                  </TableRow>
                ) : (
                  messages.map((message, index) => (
                    <TableRow
                      key={`${message.timestamp}-${index}`}
                      className={message.error ? "bg-destructive/10" : undefined}
                    >
                      <TableCell className="font-mono text-xs">
                        {formatTimestamp(message.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {message.pgn}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {getPGNDescription(message.pgn)}
                      </TableCell>
                      <TableCell className="text-center">
                        {message.instance !== undefined ? (
                          <Badge variant="secondary" className="text-xs">
                            {message.instance}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="text-xs">
                          {message.source}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {formatData(message.data)}
                      </TableCell>
                      <TableCell className="text-center text-xs">
                        {message.data.length}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * CAN bus health component
 */
function CANBusHealth() {
  const { data: metrics, isLoading } = useCANMetrics()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (!metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">CAN Bus Health</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Health metrics unavailable
          </p>
        </CardContent>
      </Card>
    )
  }

  const busLoadPercentage = Math.round((metrics.messageRate / 1000) * 100) // Assuming 1000 msg/s max
  const errorRatePercentage = metrics.totalMessages > 0
    ? Math.round((metrics.errorCount / metrics.totalMessages) * 100)
    : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">CAN Bus Health</CardTitle>
        <CardDescription>Real-time bus performance metrics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Bus Load</span>
            <span>{busLoadPercentage}%</span>
          </div>
          <Progress value={busLoadPercentage} />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Error Rate</span>
            <span>{errorRatePercentage}%</span>
          </div>
          <Progress
            value={errorRatePercentage}
            className={errorRatePercentage > 5 ? "text-destructive" : ""}
          />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Messages/sec</div>
            <div className="font-medium">{metrics.messageRate.toFixed(1)}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Uptime</div>
            <div className="font-medium">{Math.round(metrics.uptime / 60)}m</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Main CAN Sniffer page component
 */
export default function CANSniffer() {
  const [isPaused, setIsPaused] = useState(false)
  const [maxMessages] = useState(1000)

  const { data: messages, isLoading, error, refetch } = useCANMessages({
    enabled: !isPaused,
    maxMessages
  })

  const messageArray = messages || []

  const handleClearMessages = () => {
    // This would normally call an API to clear the message buffer
    refetch()
  }

  if (isLoading && !messages) {
    return (
      <AppLayout>
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex justify-between items-center">
            <div>
              <Skeleton className="h-8 w-48 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-24" />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16 mb-1" />
                  <Skeleton className="h-3 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    // Extract error details for better user messaging
    const getErrorDetails = () => {
      if (error instanceof Error) {
        // Check for specific API error types
        if ('statusCode' in error && typeof (error as { statusCode?: number }).statusCode === 'number') {
          const statusCode = (error as { statusCode: number }).statusCode;

          switch (statusCode) {
            case 404:
              return {
                title: "CAN Feature Disabled",
                message: "The CAN interface feature is currently disabled in the system configuration.",
                isConnectionError: false,
                showRetry: false,
                troubleshooting: [
                  "Contact your system administrator to enable the CAN interface feature",
                  "Check the system configuration settings"
                ]
              };
            case 503:
              return {
                title: "CAN Bus Connection Error",
                message: "Failed to connect to CAN bus interface. No interfaces are available or connected.",
                isConnectionError: true,
                showRetry: true,
                troubleshooting: [
                  "Ensure CAN interfaces are configured and connected",
                  "Check that vCAN interfaces are available (if using virtual CAN)",
                  "Verify physical CAN connections and termination",
                  "Check interface status with 'ip link show' or 'ifconfig'"
                ]
              };
            default:
              return {
                title: "API Error",
                message: error.message || "An unexpected error occurred while communicating with the server.",
                isConnectionError: false,
                showRetry: true,
                troubleshooting: ["Try refreshing the page", "Check your network connection"]
              };
          }
        }

        // Generic error handling
        return {
          title: "Connection Error",
          message: error.message || "An error occurred while loading CAN data.",
          isConnectionError: true,
          showRetry: true,
          troubleshooting: ["Try refreshing the page", "Check your network connection"]
        };
      }

      // Fallback for unknown error types
      return {
        title: "Unknown Error",
        message: "An unexpected error occurred.",
        isConnectionError: false,
        showRetry: true,
        troubleshooting: ["Try refreshing the page"]
      };
    };

    const errorDetails = getErrorDetails();

    return (
      <AppLayout>
        <div className="flex-1 space-y-6 p-4 pt-6">
          <Alert variant="destructive">
            <IconAlertTriangle className="h-4 w-4" />
            <AlertTitle>{errorDetails.title}</AlertTitle>
            <AlertDescription className="space-y-3">
              <p>{errorDetails.message}</p>

              {errorDetails.showRetry && (
                <div className="flex gap-2">
                  <Button onClick={() => refetch()} variant="outline" size="sm">
                    <IconRefresh className="h-4 w-4 mr-2" />
                    {errorDetails.isConnectionError ? "Retry Connection" : "Retry"}
                  </Button>
                </div>
              )}

              {errorDetails.troubleshooting.length > 0 && (
                <div className="text-sm text-muted-foreground">
                  <p><strong>Troubleshooting tips:</strong></p>
                  <ul className="list-disc list-inside space-y-1 mt-2">
                    {errorDetails.troubleshooting.map((tip, index) => (
                      <li key={index}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </AlertDescription>
          </Alert>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">CAN Sniffer</h1>
            <p className="text-muted-foreground">
              Real-time CAN bus monitoring and message analysis
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setIsPaused(!isPaused)}
              variant={isPaused ? "default" : "secondary"}
              className="gap-2"
            >
              {isPaused ? (
                <>
                  <IconPlayerPlay className="h-4 w-4" />
                  Resume
                </>
              ) : (
                <>
                  <IconPlayerPause className="h-4 w-4" />
                  Pause
                </>
              )}
            </Button>
            <Button onClick={handleClearMessages} variant="outline" className="gap-2">
              <IconTrash className="h-4 w-4" />
              Clear
            </Button>
            <Button onClick={() => refetch()} variant="outline" className="gap-2">
              <IconRefresh className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <CANStatistics messages={messageArray} />

        <div className="grid gap-8 lg:grid-cols-4">
          {/* Message Table - Takes 3/4 width */}
          <div className="lg:col-span-3">
            <CANMessageTable messages={messageArray} isPaused={isPaused} />
          </div>

          {/* Sidebar - Takes 1/4 width */}
          <div className="space-y-6">
            <CANBusHealth />

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Message Buffer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Buffer Size</span>
                    <span>{messageArray.length}/{maxMessages}</span>
                  </div>
                  <Progress value={(messageArray.length / maxMessages) * 100} />
                </div>
                <p className="text-xs text-muted-foreground">
                  Messages are automatically trimmed when buffer is full
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
