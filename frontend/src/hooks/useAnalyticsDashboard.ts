/**
 * Analytics Dashboard Hooks
 *
 * React hooks for advanced analytics dashboard functionality including
 * performance trends, system insights, historical analysis, and metrics aggregation.
 */

import { apiGet, apiPost } from "@/api/client"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

interface AnalyticsDashboardOptions {
  timeWindowHours?: number
  resolution?: string
  metrics?: string[]
  categories?: string[]
  minSeverity?: string
  analysisType?: string
  includePredictions?: boolean
  aggregationWindows?: string[]
  metricGroups?: string[]
}

const ANALYTICS_KEYS = {
  all: ["analytics"] as const,
  trends: (timeWindow?: number, resolution?: string, metrics?: string[]) => [
    ...ANALYTICS_KEYS.all,
    "trends",
    timeWindow,
    resolution,
    metrics?.join(",")
  ] as const,
  insights: (categories?: string[], minSeverity?: string, limit?: number) => [
    ...ANALYTICS_KEYS.all,
    "insights",
    categories?.join(","),
    minSeverity,
    limit
  ] as const,
  historical: (analysisType?: string, timeWindow?: number, predictions?: boolean) => [
    ...ANALYTICS_KEYS.all,
    "historical",
    analysisType,
    timeWindow,
    predictions
  ] as const,
  aggregation: (windows?: string[], groups?: string[]) => [
    ...ANALYTICS_KEYS.all,
    "aggregation",
    windows?.join(","),
    groups?.join(",")
  ] as const,
  status: () => [...ANALYTICS_KEYS.all, "status"] as const,
  health: () => [...ANALYTICS_KEYS.all, "health"] as const,
}

/**
 * Get performance trends
 */
export function usePerformanceTrends(
  timeWindowHours: number = 24,
  resolution: string = "1h",
  metrics?: string[]
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.trends(timeWindowHours, resolution, metrics),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("time_window_hours", timeWindowHours.toString())
      params.append("resolution", resolution)
      if (metrics && metrics.length > 0) {
        params.append("metrics", metrics.join(","))
      }

      const response = await apiGet<unknown>(`/api/analytics/trends?${params.toString()}`)
      return response
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  })
}

/**
 * Get system insights
 */
export function useSystemInsights(
  categories?: string[],
  minSeverity: string = "low",
  limit: number = 50
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.insights(categories, minSeverity, limit),
    queryFn: async () => {
      const params = new URLSearchParams()
      if (categories && categories.length > 0) {
        params.append("categories", categories.join(","))
      }
      params.append("min_severity", minSeverity)
      params.append("limit", limit.toString())

      const response = await apiGet<unknown>(`/api/analytics/insights?${params.toString()}`)
      return response
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Auto-refresh every 10 minutes
  })
}

/**
 * Get historical analysis
 */
export function useHistoricalAnalysis(
  analysisType: string = "pattern_detection",
  timeWindowHours: number = 168,
  includePredictions: boolean = true
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.historical(analysisType, timeWindowHours, includePredictions),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("analysis_type", analysisType)
      params.append("time_window_hours", timeWindowHours.toString())
      params.append("include_predictions", includePredictions.toString())

      const response = await apiGet<unknown>(`/api/analytics/historical?${params.toString()}`)
      return response
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 30 * 60 * 1000, // Auto-refresh every 30 minutes
  })
}

/**
 * Get metrics aggregation
 */
export function useMetricsAggregation(
  aggregationWindows?: string[],
  metricGroups?: string[]
) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.aggregation(aggregationWindows, metricGroups),
    queryFn: async () => {
      const params = new URLSearchParams()
      if (aggregationWindows && aggregationWindows.length > 0) {
        params.append("aggregation_windows", aggregationWindows.join(","))
      }
      if (metricGroups && metricGroups.length > 0) {
        params.append("metric_groups", metricGroups.join(","))
      }

      const response = await apiGet<unknown>(`/api/analytics/aggregation?${params.toString()}`)
      return response
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 15 * 60 * 1000, // Auto-refresh every 15 minutes
  })
}

/**
 * Get analytics service status
 */
export function useAnalyticsStatus() {
  return useQuery({
    queryKey: ANALYTICS_KEYS.status(),
    queryFn: async () => {
      const response = await apiGet<unknown>("/api/analytics/status")
      return response
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  })
}

/**
 * Get analytics health status
 */
export function useAnalyticsHealth() {
  return useQuery({
    queryKey: ANALYTICS_KEYS.health(),
    queryFn: async () => {
      const response = await apiGet<unknown>("/api/analytics/health")
      return response
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  })
}

/**
 * Record custom metric
 */
export function useRecordCustomMetric() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      metric_name: string
      value: number
      metadata?: Record<string, unknown>
    }) => {
      const response = await apiPost<unknown>("/api/analytics/metrics", data)
      return response
    },
    onSuccess: () => {
      // Invalidate analytics data to reflect new metric
      queryClient.invalidateQueries({
        queryKey: ANALYTICS_KEYS.all,
      })
    },
  })
}

/**
 * Main analytics dashboard hook
 *
 * Combines multiple analytics data sources for comprehensive dashboard management
 */
export function useAnalyticsDashboard(options: AnalyticsDashboardOptions = {}) {
  const queryClient = useQueryClient()

  const {
    timeWindowHours = 24,
    resolution = "1h",
    metrics,
    categories,
    minSeverity = "low",
    analysisType = "pattern_detection",
    includePredictions = true,
    aggregationWindows,
    metricGroups
  } = options

  // Individual data hooks
  const trends = usePerformanceTrends(timeWindowHours, resolution, metrics)
  const insights = useSystemInsights(categories, minSeverity, 50)
  const historical = useHistoricalAnalysis(analysisType, timeWindowHours, includePredictions)
  const aggregation = useMetricsAggregation(aggregationWindows, metricGroups)
  const status = useAnalyticsStatus()
  const health = useAnalyticsHealth()

  // Mutations
  const recordCustomMetric = useRecordCustomMetric()

  // Refresh functions
  const refreshTrends = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.trends(timeWindowHours, resolution, metrics),
    })
  }

  const refreshInsights = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.insights(categories, minSeverity, 50),
    })
  }

  const refreshHistorical = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.historical(analysisType, timeWindowHours, includePredictions),
    })
  }

  const refreshAggregation = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.aggregation(aggregationWindows, metricGroups),
    })
  }

  const refreshStatus = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.status(),
    })
  }

  const refreshAll = () => {
    queryClient.invalidateQueries({
      queryKey: ANALYTICS_KEYS.all,
    })
  }

  // Loading states
  const isLoadingTrends = trends.isLoading
  const isLoadingInsights = insights.isLoading
  const isLoadingHistorical = historical.isLoading
  const isLoadingAggregation = aggregation.isLoading
  const isLoadingStatus = status.isLoading
  const isLoadingHealth = health.isLoading

  const isLoading = isLoadingTrends || isLoadingInsights || isLoadingHistorical ||
                   isLoadingAggregation || isLoadingStatus

  // Error states
  const error = trends.error || insights.error || historical.error ||
               aggregation.error || status.error || health.error

  return {
    // Data
    trends: trends.data,
    insights: insights.data,
    historical: historical.data,
    aggregation: aggregation.data,
    status: status.data,
    health: health.data,

    // Loading states
    isLoading,
    isLoadingTrends,
    isLoadingInsights,
    isLoadingHistorical,
    isLoadingAggregation,
    isLoadingStatus,
    isLoadingHealth,

    // Error state
    error,

    // Actions
    recordCustomMetric,
    refreshTrends,
    refreshInsights,
    refreshHistorical,
    refreshAggregation,
    refreshStatus,
    refreshAll,

    // Individual query states
    trendsQuery: trends,
    insightsQuery: insights,
    historicalQuery: historical,
    aggregationQuery: aggregation,
    statusQuery: status,
    healthQuery: health,
  }
}

/**
 * Hook for analytics dashboard statistics
 */
export function useAnalyticsDashboardStats() {
  const { trends, insights, historical, aggregation, status } = useAnalyticsDashboard()

  if (!trends || !insights || !historical || !aggregation || !status) {
    return null
  }

  const trendsMetrics = Object.keys((trends as { metrics?: Record<string, unknown> })?.metrics || {}).length
  const totalInsights = (insights as { total_insights?: number })?.total_insights || 0
  const patternsFound = (historical as { summary?: { patterns_found?: number } })?.summary?.patterns_found || 0
  const kpis = Object.keys((aggregation as { kpis?: Record<string, unknown> })?.kpis || {}).length

  return {
    trendsMetrics,
    totalInsights,
    patternsFound,
    kpis,
    serviceHealth: (status as { service_status?: string })?.service_status === "operational",
    dataQuality: trendsMetrics > 0 && totalInsights > 0 ? "good" : "limited",
    lastUpdate: Math.max(
      (trends as { time_window_hours?: number })?.time_window_hours || 0,
      (insights as { summary?: { total_count?: number } })?.summary?.total_count || 0,
      (historical as { summary?: { confidence?: number } })?.summary?.confidence || 0
    )
  }
}

/**
 * Hook for analytics performance summary
 */
export function useAnalyticsPerformanceSummary() {
  const trends = usePerformanceTrends(24, "1h")

  if (!(trends.data as { summary?: unknown })?.summary) {
    return null
  }

  const summary = (trends.data as { summary: {
    trending_up?: number
    trending_down?: number
    stable?: number
    total_anomalies?: number
    key_insights?: string[]
  } }).summary
  // const metrics = trends.data.metrics || {} // Currently unused but may be needed for future enhancements

  // Calculate overall performance score
  const trendingUp = summary.trending_up || 0
  const trendingDown = summary.trending_down || 0
  const stable = summary.stable || 0
  const totalMetrics = trendingUp + trendingDown + stable

  const performanceScore = totalMetrics > 0
    ? ((trendingUp * 1.0 + stable * 0.7) / totalMetrics) * 100
    : 0

  // Get most critical alerts
  const alerts = (trends.data as { alerts?: { severity: string }[] })?.alerts || []
  const criticalAlerts = alerts.filter((alert: { severity: string }) => alert.severity === "high" || alert.severity === "critical")

  return {
    performanceScore: Math.round(performanceScore),
    totalMetrics,
    trendingUp,
    trendingDown,
    stable,
    totalAnomalies: summary.total_anomalies || 0,
    criticalAlerts: criticalAlerts.length,
    keyInsights: summary.key_insights || [],
    hasIssues: criticalAlerts.length > 0 || (summary.total_anomalies || 0) > 5,
    overallTrend: trendingUp > trendingDown ? "improving" :
                  trendingUp < trendingDown ? "declining" : "stable"
  }
}
