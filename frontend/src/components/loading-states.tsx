/**
 * Standardized Loading States
 *
 * Consistent loading and error components used across the application.
 * Provides unified user experience and reduces code duplication.
 */

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  IconAlertCircle,
  IconRefresh,
  IconWifi,
  IconX,
  IconLoader2
} from "@tabler/icons-react"

// Loading skeleton patterns
export const LoadingPatterns = {
  // Card grid loading (for dashboards, entity lists)
  CardGrid: ({ count = 6, columns = 3 }: { count?: number; columns?: number }) => (
    <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-${columns}`}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-5" />
              <Skeleton className="h-5 w-32" />
            </div>
            <Skeleton className="h-4 w-full" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-4 w-full" />
              <div className="flex gap-2">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-16" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  ),

  // Table rows loading
  TableRows: ({ rows = 8, columns = 5 }: { rows?: number; columns?: number }) => (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  ),

  // List items loading
  ListItems: ({ count = 5 }: { count?: number }) => (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-start gap-3">
          <Skeleton className="h-2 w-2 rounded-full mt-2" />
          <div className="flex-1 space-y-1">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </div>
      ))}
    </div>
  ),

  // Statistics cards loading
  StatsCards: ({ count = 4 }: { count?: number }) => (
    <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-${Math.min(count, 4)}`}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-16 mb-2" />
            <Skeleton className="h-3 w-20" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// Inline loading spinner
export function LoadingSpinner({
  size = "sm",
  className = ""
}: {
  size?: "xs" | "sm" | "md" | "lg"
  className?: string
}) {
  const sizeClasses = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8"
  }

  return (
    <IconLoader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  )
}

// Full page loading
export function PageLoading({
  title = "Loading...",
  description = "Please wait while we load your data"
}: {
  title?: string
  description?: string
}) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}

// Error state types
export interface ErrorInfo {
  title: string
  message: string
  isConnectionError?: boolean
  statusCode?: number
  canRetry?: boolean
  troubleshooting?: string[]
}

// Standardized error component
export function ErrorDisplay({
  error,
  onRetry,
  className = ""
}: {
  error: ErrorInfo
  onRetry?: () => void
  className?: string
}) {
  const getErrorIcon = () => {
    if (error.isConnectionError) return IconWifi
    if (error.statusCode === 404) return IconX
    return IconAlertCircle
  }

  const ErrorIcon = getErrorIcon()

  return (
    <Card className={className}>
      <CardContent className="p-6 text-center">
        <ErrorIcon className="h-12 w-12 mx-auto mb-4 text-destructive" />
        <h3 className="text-lg font-semibold mb-2">{error.title}</h3>
        <p className="text-muted-foreground mb-4">{error.message}</p>

        {error.canRetry && onRetry && (
          <Button onClick={onRetry} variant="outline" className="mb-4">
            <IconRefresh className="mr-2 h-4 w-4" />
            {error.isConnectionError ? "Retry Connection" : "Try Again"}
          </Button>
        )}

        {error.troubleshooting && error.troubleshooting.length > 0 && (
          <Alert className="text-left mt-4">
            <IconAlertCircle className="h-4 w-4" />
            <AlertTitle>Troubleshooting Tips</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside space-y-1 mt-2 text-sm">
                {error.troubleshooting.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}

// Quick error states for common scenarios
export const ErrorStates = {
  // Network/API errors
  NetworkError: ({ onRetry }: { onRetry?: () => void }) => (
    <ErrorDisplay
      error={{
        title: "Connection Error",
        message: "Unable to connect to the server. Please check your network connection.",
        isConnectionError: true,
        canRetry: true,
        troubleshooting: [
          "Check your internet connection",
          "Verify the server is running",
          "Try refreshing the page"
        ]
      }}
      onRetry={onRetry}
    />
  ),

  // Feature disabled errors
  FeatureDisabled: ({ featureName }: { featureName: string }) => (
    <ErrorDisplay
      error={{
        title: "Feature Unavailable",
        message: `The ${featureName} feature is currently disabled or not available.`,
        statusCode: 404,
        canRetry: false,
        troubleshooting: [
          "Contact your system administrator",
          "Check the system configuration",
          "Verify feature requirements are met"
        ]
      }}
    />
  ),

  // No data errors
  NoData: ({
    entityType = "data",
    actionHint
  }: {
    entityType?: string
    actionHint?: string
  }) => (
    <ErrorDisplay
      error={{
        title: `No ${entityType} Found`,
        message: `No ${entityType} is currently available.${actionHint ? ` ${actionHint}` : ''}`,
        canRetry: false
      }}
    />
  ),

  // CAN bus specific errors
  CANError: ({ onRetry }: { onRetry?: () => void }) => (
    <ErrorDisplay
      error={{
        title: "CAN Bus Error",
        message: "Unable to connect to CAN bus interfaces. Check that interfaces are configured and active.",
        isConnectionError: true,
        statusCode: 503,
        canRetry: true,
        troubleshooting: [
          "Ensure CAN interfaces are configured",
          "Check that vCAN interfaces are available (if using virtual CAN)",
          "Verify physical CAN connections and termination",
          "Check interface status with system tools"
        ]
      }}
      onRetry={onRetry}
    />
  )
}

// Loading state wrapper component
export function LoadingWrapper({
  isLoading,
  error,
  onRetry,
  loadingComponent,
  children
}: {
  isLoading: boolean
  error?: Error | null
  onRetry?: () => void
  loadingComponent?: React.ReactNode
  children: React.ReactNode
}) {
  if (isLoading) {
    return loadingComponent || <PageLoading />
  }

  if (error) {
    // Try to extract error information
    const errorInfo: ErrorInfo = {
      title: "Error",
      message: error.message || "An unexpected error occurred",
      canRetry: true
    }

    // Check for specific error types
    if ('statusCode' in error) {
      const statusCode = (error as Error & { statusCode?: number }).statusCode
      errorInfo.statusCode = statusCode

      if (statusCode === 404) {
        errorInfo.title = "Not Found"
        errorInfo.message = "The requested resource was not found"
        errorInfo.canRetry = false
      } else if (statusCode === 503) {
        errorInfo.title = "Service Unavailable"
        errorInfo.message = "The service is temporarily unavailable"
        errorInfo.isConnectionError = true
      }
    }

    return <ErrorDisplay error={errorInfo} onRetry={onRetry} />
  }

  return <>{children}</>
}
