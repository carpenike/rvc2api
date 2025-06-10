/**
 * Predictive Maintenance Hooks
 *
 * React hooks for predictive maintenance data fetching and operations
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/api/client"
import type {
  ComponentHealth,
  MaintenanceRecommendation,
  RVHealthOverview,
  MaintenanceHistory
} from "@/api/types"

interface PredictiveMaintenanceFilters {
  systemType?: string
  status?: string
  recommendationLevel?: string
  componentId?: string
  acknowledged?: boolean
  days?: number
}

const PREDICTIVE_MAINTENANCE_KEYS = {
  all: ["predictive-maintenance"] as const,
  healthOverview: () => [...PREDICTIVE_MAINTENANCE_KEYS.all, "health-overview"] as const,
  componentHealth: (filters?: PredictiveMaintenanceFilters) => [
    ...PREDICTIVE_MAINTENANCE_KEYS.all,
    "component-health",
    filters
  ] as const,
  componentDetail: (componentId: string) => [
    ...PREDICTIVE_MAINTENANCE_KEYS.all,
    "component-detail",
    componentId
  ] as const,
  recommendations: (filters?: PredictiveMaintenanceFilters) => [
    ...PREDICTIVE_MAINTENANCE_KEYS.all,
    "recommendations",
    filters
  ] as const,
  trends: (componentId: string, metric?: string, days?: number) => [
    ...PREDICTIVE_MAINTENANCE_KEYS.all,
    "trends",
    componentId,
    metric,
    days
  ] as const,
  maintenanceHistory: (filters?: PredictiveMaintenanceFilters) => [
    ...PREDICTIVE_MAINTENANCE_KEYS.all,
    "maintenance-history",
    filters
  ] as const,
}

/**
 * Fetch RV health overview
 */
export function useHealthOverview() {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.healthOverview(),
    queryFn: async (): Promise<RVHealthOverview> => {
      return await apiGet("/api/predictive-maintenance/health/overview")
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  })
}

/**
 * Fetch component health data
 */
export function useComponentHealth(filters?: PredictiveMaintenanceFilters) {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.componentHealth(filters),
    queryFn: async (): Promise<ComponentHealth[]> => {
      const params = new URLSearchParams()
      if (filters?.systemType) params.append("system_type", filters.systemType)
      if (filters?.status) params.append("status", filters.status)

      const url = `/api/predictive-maintenance/health/components${params.toString() ? `?${params.toString()}` : ""}`
      return await apiGet(url)
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Fetch detailed component health
 */
export function useComponentHealthDetail(componentId: string) {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.componentDetail(componentId),
    queryFn: async (): Promise<ComponentHealth> => {
      return await apiGet(`/api/predictive-maintenance/health/components/${componentId}`)
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!componentId,
  })
}

/**
 * Fetch maintenance recommendations
 */
export function useMaintenanceRecommendations(filters?: PredictiveMaintenanceFilters) {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.recommendations(filters),
    queryFn: async (): Promise<MaintenanceRecommendation[]> => {
      const params = new URLSearchParams()
      if (filters?.recommendationLevel) params.append("level", filters.recommendationLevel)
      if (filters?.componentId) params.append("component_id", filters.componentId)
      if (filters?.acknowledged !== undefined) params.append("acknowledged", filters.acknowledged.toString())

      const url = `/api/predictive-maintenance/recommendations${params.toString() ? `?${params.toString()}` : ""}`
      return await apiGet(url)
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Acknowledge maintenance recommendation
 */
export function useAcknowledgeRecommendation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (recommendationId: string): Promise<{ message: string }> => {
      return await apiPost(
        `/api/predictive-maintenance/recommendations/${recommendationId}/acknowledge`
      )
    },
    onSuccess: () => {
      // Invalidate and refetch recommendations
      void queryClient.invalidateQueries({
        queryKey: PREDICTIVE_MAINTENANCE_KEYS.all,
      })
    },
  })
}

/**
 * Fetch component trend data
 */
export function useComponentTrends(
  componentId: string,
  metric?: string,
  days: number = 30
) {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.trends(componentId, metric, days),
    queryFn: async () => {
      const params = new URLSearchParams()
      if (metric) params.append("metric", metric)
      params.append("days", days.toString())

      const url = `/api/predictive-maintenance/trends/${componentId}${params.toString() ? `?${params.toString()}` : ""}`
      return await apiGet(url)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!componentId,
  })
}

/**
 * Fetch maintenance history
 */
export function useMaintenanceHistory(filters?: PredictiveMaintenanceFilters) {
  return useQuery({
    queryKey: PREDICTIVE_MAINTENANCE_KEYS.maintenanceHistory(filters),
    queryFn: async (): Promise<MaintenanceHistory[]> => {
      const params = new URLSearchParams()
      if (filters?.componentId) params.append("component_id", filters.componentId)
      if (filters?.days) params.append("days", filters.days.toString())

      const url = `/api/predictive-maintenance/maintenance/history${params.toString() ? `?${params.toString()}` : ""}`
      return await apiGet(url)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Main predictive maintenance hook
 *
 * Combines multiple data sources for a comprehensive maintenance view
 */
export function usePredictiveMaintenance(filters?: PredictiveMaintenanceFilters) {
  const queryClient = useQueryClient()

  const healthOverview = useHealthOverview()
  const componentHealth = useComponentHealth(filters)
  const recommendations = useMaintenanceRecommendations(filters)
  const acknowledgeRecommendation = useAcknowledgeRecommendation()

  const refresh = () => {
    void queryClient.invalidateQueries({
      queryKey: PREDICTIVE_MAINTENANCE_KEYS.all,
    })
  }

  const isLoading = healthOverview.isLoading || componentHealth.isLoading || recommendations.isLoading
  const error = healthOverview.error || componentHealth.error || recommendations.error

  return {
    // Data
    healthOverview: healthOverview.data,
    componentHealth: componentHealth.data,
    recommendations: recommendations.data,

    // Loading states
    isLoading,
    error,

    // Actions
    acknowledgeRecommendation,
    refresh,

    // Individual query states
    healthOverviewQuery: healthOverview,
    componentHealthQuery: componentHealth,
    recommendationsQuery: recommendations,
  }
}

/**
 * Hook for predictive maintenance statistics
 */
export function usePredictiveMaintenanceStats() {
  const { healthOverview, componentHealth, recommendations } = usePredictiveMaintenance()

  if (!healthOverview || !componentHealth || !recommendations) {
    return null
  }

  const criticalComponents = componentHealth.filter(c => c.status === "alert").length
  const watchComponents = componentHealth.filter(c => c.status === "watch").length
  const healthyComponents = componentHealth.filter(c => c.status === "healthy").length

  const urgentRecommendations = recommendations.filter(r => r.priority <= 2 && !r.acknowledged_at).length
  const totalCost = recommendations
    .filter(r => !r.acknowledged_at && r.estimated_cost)
    .reduce((sum, r) => sum + (r.estimated_cost || 0), 0)

  return {
    overallHealth: healthOverview.overall_health_score,
    criticalComponents,
    watchComponents,
    healthyComponents,
    totalComponents: componentHealth.length,
    urgentRecommendations,
    totalRecommendations: recommendations.length,
    estimatedMaintenanceCost: totalCost,
    lastUpdated: healthOverview.last_updated,
  }
}
