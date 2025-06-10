/**
 * Device Discovery Hooks
 *
 * React hooks for enhanced device discovery, profiling, and setup
 */

import { API_BASE } from "@/api/client"
import type {
    DeviceProfile,
    EnhancedNetworkMap,
    NetworkTopology,
    SetupRecommendations
} from "@/api/types"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
// Temporarily commented out unused imports - may be needed for future device setup features:
// DeviceInfo, DiscoveredDevice, AutoDiscoveryRequest, DeviceSetupRequest

const DEVICE_DISCOVERY_KEYS = {
  all: ["device-discovery"] as const,
  status: () => [...DEVICE_DISCOVERY_KEYS.all, "status"] as const,
  topology: () => [...DEVICE_DISCOVERY_KEYS.all, "topology"] as const,
  availability: () => [...DEVICE_DISCOVERY_KEYS.all, "availability"] as const,
  networkMap: (includeOffline?: boolean, groupByProtocol?: boolean) => [
    ...DEVICE_DISCOVERY_KEYS.all,
    "network-map",
    includeOffline,
    groupByProtocol
  ] as const,
  protocols: () => [...DEVICE_DISCOVERY_KEYS.all, "protocols"] as const,
  deviceProfile: (deviceAddress: number, protocol?: string) => [
    ...DEVICE_DISCOVERY_KEYS.all,
    "device-profile",
    deviceAddress,
    protocol
  ] as const,
  recommendations: (includeConfigured?: boolean) => [
    ...DEVICE_DISCOVERY_KEYS.all,
    "recommendations",
    includeConfigured
  ] as const,
}

/**
 * Get discovery service status
 */
export function useDiscoveryStatus() {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.status(),
    queryFn: async () => {
      const response = await fetch("/api/discovery/status")
      if (!response.ok) {
        throw new Error(`Failed to fetch discovery status: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Get network topology
 */
export function useNetworkTopology() {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.topology(),
    queryFn: async (): Promise<NetworkTopology> => {
      const response = await fetch("/api/discovery/topology")
      if (!response.ok) {
        throw new Error(`Failed to fetch network topology: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
  })
}

/**
 * Get device availability
 */
export function useDeviceAvailability() {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.availability(),
    queryFn: async () => {
      const response = await fetch("/api/discovery/availability")
      if (!response.ok) {
        throw new Error(`Failed to fetch device availability: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

/**
 * Get enhanced network map
 */
export function useEnhancedNetworkMap(
  includeOffline: boolean = true,
  groupByProtocol: boolean = true
) {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.networkMap(includeOffline, groupByProtocol),
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("include_offline", includeOffline.toString())
      params.append("group_by_protocol", groupByProtocol.toString())

      const response = await fetch(`${API_BASE}/api/discovery/network-map?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch network map: ${response.statusText}`)
      }
      return response.json() as Promise<EnhancedNetworkMap>
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Get supported protocols
 */
export function useSupportedProtocols() {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.protocols(),
    queryFn: async () => {
      const response = await fetch("/api/discovery/protocols")
      if (!response.ok) {
        throw new Error(`Failed to fetch protocols: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 10 * 60 * 1000, // 10 minutes (protocols don't change often)
  })
}

/**
 * Get device profile
 */
export function useDeviceProfile(deviceAddress: number, protocol: string = "rvc") {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.deviceProfile(deviceAddress, protocol),
    queryFn: async (): Promise<DeviceProfile> => {
      const params = new URLSearchParams()
      params.append("protocol", protocol)

      const response = await fetch(`${API_BASE}/api/discovery/wizard/device-profile/${deviceAddress}?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch device profile: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!deviceAddress,
  })
}

/**
 * Get setup recommendations
 */
export function useSetupRecommendations(includeConfigured: boolean = false) {
  return useQuery({
    queryKey: DEVICE_DISCOVERY_KEYS.recommendations(includeConfigured),
    queryFn: async (): Promise<SetupRecommendations> => {
      const params = new URLSearchParams()
      params.append("include_configured", includeConfigured.toString())

      const response = await fetch(`${API_BASE}/api/discovery/wizard/setup-recommendations?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch setup recommendations: ${response.statusText}`)
      }
      return response.json()
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Discover devices for a protocol
 */
export function useDiscoverDevices() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (protocol: string = "rvc") => {
      const response = await fetch("/api/discovery/discover", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ protocol }),
      })
      if (!response.ok) {
        throw new Error(`Failed to discover devices: ${response.statusText}`)
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate and refetch discovery data
      void queryClient.invalidateQueries({
        queryKey: DEVICE_DISCOVERY_KEYS.all,
      })
    },
  })
}

/**
 * Poll a specific device
 */
export function usePollDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: {
      source_address: number
      pgn: number
      protocol?: string
      instance?: number
    }) => {
      const response = await fetch("/api/discovery/poll", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_address: request.source_address,
          pgn: request.pgn,
          protocol: request.protocol || "rvc",
          instance: request.instance,
        }),
      })
      if (!response.ok) {
        throw new Error(`Failed to poll device: ${response.statusText}`)
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate topology and availability data
      void queryClient.invalidateQueries({
        queryKey: DEVICE_DISCOVERY_KEYS.topology(),
      })
      void queryClient.invalidateQueries({
        queryKey: DEVICE_DISCOVERY_KEYS.availability(),
      })
    },
  })
}

/**
 * Start auto-discovery wizard
 */
export function useStartAutoDiscovery() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: {
      protocols: string[]
      scan_duration_seconds: number
      deep_scan: boolean
      save_results: boolean
    }) => {
      const response = await fetch("/api/discovery/wizard/auto-discover", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })
      if (!response.ok) {
        throw new Error(`Failed to start auto-discovery: ${response.statusText}`)
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate all discovery data after auto-discovery
      void queryClient.invalidateQueries({
        queryKey: DEVICE_DISCOVERY_KEYS.all,
      })
    },
  })
}

/**
 * Setup a discovered device
 */
export function useSetupDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: {
      device_address: number
      device_name: string
      device_type: string
      area: string
      capabilities: string[]
      configuration: Record<string, string | number | boolean>
    }) => {
      const response = await fetch("/api/discovery/wizard/setup-device", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })
      if (!response.ok) {
        throw new Error(`Failed to setup device: ${response.statusText}`)
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate discovery data and entity data after device setup
      void queryClient.invalidateQueries({
        queryKey: DEVICE_DISCOVERY_KEYS.all,
      })
      // Also invalidate entities since we may have created new ones
      void queryClient.invalidateQueries({
        queryKey: ["entities"],
      })
    },
  })
}

/**
 * Main device discovery hook
 *
 * Combines multiple data sources for comprehensive discovery management
 */
export function useDeviceDiscovery() {
  const queryClient = useQueryClient()

  const status = useDiscoveryStatus()
  const topology = useNetworkTopology()
  const availability = useDeviceAvailability()
  const networkMap = useEnhancedNetworkMap()
  const protocols = useSupportedProtocols()
  const recommendations = useSetupRecommendations()

  const discoverDevices = useDiscoverDevices()
  const pollDevice = usePollDevice()
  const startAutoDiscovery = useStartAutoDiscovery()
  const setupDevice = useSetupDevice()

  const refresh = () => {
    void queryClient.invalidateQueries({
      queryKey: DEVICE_DISCOVERY_KEYS.all,
    })
  }

  const isLoading = status.isLoading || topology.isLoading || availability.isLoading
  const error = status.error || topology.error || availability.error

  return {
    // Data
    status: status.data,
    topology: topology.data,
    availability: availability.data,
    networkMap: networkMap.data,
    protocols: protocols.data,
    recommendations: recommendations.data,

    // Loading states
    isLoading,
    error,

    // Actions
    discoverDevices,
    pollDevice,
    startAutoDiscovery,
    setupDevice,
    refresh,

    // Individual query states
    statusQuery: status,
    topologyQuery: topology,
    availabilityQuery: availability,
    networkMapQuery: networkMap,
    protocolsQuery: protocols,
    recommendationsQuery: recommendations,
  }
}

/**
 * Hook for device discovery statistics
 */
export function useDeviceDiscoveryStats() {
  const { topology, availability, networkMap, status } = useDeviceDiscovery()

  if (!topology || !availability || !networkMap || !status) {
    return null
  }

  const totalDevices = topology.total_devices || 0
  const onlineDevices = networkMap.online_devices || 0
  const offlineDevices = networkMap.offline_devices || 0
  const protocolCount = Object.keys(networkMap.protocol_distribution || {}).length
  const discoveryActive = status.health?.metrics?.discovery_active || false

  return {
    totalDevices,
    onlineDevices,
    offlineDevices,
    protocolCount,
    discoveryActive,
    healthScore: networkMap.network_health?.score || 0,
    healthStatus: networkMap.network_health?.status || "unknown",
    lastDiscovery: topology.last_discovery || 0,
    deviceTypes: Object.keys(networkMap.device_groups || {}),
  }
}

/**
 * Hook for getting device by address
 */
export function useDeviceByAddress(address: number, protocol: string = "rvc") {
  const { topology } = useDeviceDiscovery()

  if (!topology?.devices) {
    return null
  }

  // Find device in the topology
  const protocolDevices = topology.devices[protocol] || []
  return protocolDevices.find(device => device.source_address === address) || null
}
