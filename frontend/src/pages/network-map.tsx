/**
 * Network Map Page
 *
 * Canvas-based visualization of the RV-C network topology.
 * Shows real-time device connections and status.
 */

import type { EntityData, ProtocolBridgeStatus, SpartanK2Entity } from "@/api/types"
import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { useEntities } from "@/hooks/useEntities"
import { useQuery } from "@tanstack/react-query"
import {
  fetchProtocolBridgeStatus,
  fetchJ1939Entities,
  fetchFireflyEntities,
  fetchSpartanK2Entities,
  fetchProtocolThroughput
} from "@/api/endpoints"
import {
  IconAlertTriangle,
  IconInfoCircle,
  IconMapPin,
  IconRefresh,
  IconZoomIn,
  IconZoomOut,
  IconNetwork,
  IconGitBranch,
  IconActivity
} from "@tabler/icons-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

/**
 * Network node interface for canvas rendering
 */
interface NetworkNode {
  id: string
  name: string
  type: string
  protocol: "rvc" | "j1939" | "firefly" | "spartan_k2"
  x: number
  y: number
  radius: number
  color: string
  protocolColor: string
  status: "online" | "offline" | "error"
  connections: string[]
  throughput?: number
  safety_status?: "safe" | "warning" | "critical"
}


/**
 * Enhanced multi-protocol network topology canvas component
 */
function NetworkCanvas({
  entities,
  throughput
}: {
  entities: EntityData[]
  throughput?: Record<string, number>
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })


  // Convert entities to network nodes with protocol grouping
  const { nodes } = useMemo(() => {
    const canvasWidth = 800
    const canvasHeight = 600

    // Protocol colors
    const protocolColors = {
      rvc: "#2563EB", // blue-600
      j1939: "#059669", // emerald-600
      firefly: "#7C3AED", // violet-600
      spartan_k2: "#DC2626", // red-600
    }

    // Group entities by protocol
    const protocolGroups = entities.reduce((acc, entity) => {
      const protocol = (entity as EntityData & { protocol?: string }).protocol || 'rvc'
      if (!acc[protocol]) acc[protocol] = []
      acc[protocol].push(entity)
      return acc
    }, {} as Record<string, EntityData[]>)

    const protocols = Object.keys(protocolGroups)
    const nodes: NetworkNode[] = []

    // Position nodes in protocol-specific zones
    protocols.forEach((protocol, protocolIndex) => {
      const entitiesInProtocol = protocolGroups[protocol]
      const protocolAngle = (protocolIndex / protocols.length) * 2 * Math.PI
      const protocolRadius = Math.min(canvasWidth, canvasHeight) / 3
      const protocolCenterX = canvasWidth / 2 + Math.cos(protocolAngle) * protocolRadius * 0.5
      const protocolCenterY = canvasHeight / 2 + Math.sin(protocolAngle) * protocolRadius * 0.5

      entitiesInProtocol.forEach((entity, entityIndex) => {
        const angle = (entityIndex / entitiesInProtocol.length) * 2 * Math.PI
        const radius = Math.min(protocolRadius * 0.6, 120)

        const deviceTypeColors: Record<string, string> = {
          light: "#10B981", // emerald-500
          lock: "#F59E0B", // amber-500
          tank: "#3B82F6", // blue-500
          temperature: "#EF4444", // red-500
          engine: "#059669", // emerald-600 (J1939)
          transmission: "#DC2626", // red-600 (J1939)
          brake: "#DC2626", // red-600 (Spartan K2)
          suspension: "#7C2D12", // amber-800 (Spartan K2)
          steering: "#991B1B", // red-800 (Spartan K2)
          default: "#6B7280", // gray-500
        }

        const entityProtocol = (entity as EntityData & { protocol?: string }).protocol || 'rvc'
        const safetyStatus = (entity as SpartanK2Entity)?.safety_status

        nodes.push({
          id: entity.id,
          name: entity.name,
          type: entity.device_type,
          protocol: entityProtocol as "rvc" | "j1939" | "firefly" | "spartan_k2",
          x: protocolCenterX + Math.cos(angle) * radius,
          y: protocolCenterY + Math.sin(angle) * radius,
          radius: 18,
          color: deviceTypeColors[entity.device_type] || deviceTypeColors.default,
          protocolColor: protocolColors[entityProtocol as keyof typeof protocolColors] || protocolColors.rvc,
          status: entity.state === "on" || entity.state === "online" ? "online" :
                  entity.state === "error" ? "error" : "offline",
          connections: [],
          throughput: throughput?.[entityProtocol] || 0,
          safety_status: safetyStatus,
        })
      })
    })

    return { nodes }
  }, [entities, throughput])

  // Draw the network topology
  const drawNetwork = useCallback((ctx: CanvasRenderingContext2D) => {
    const canvas = ctx.canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Apply zoom and pan transformations
    ctx.save()
    ctx.translate(pan.x, pan.y)
    ctx.scale(zoom, zoom)

    // Draw connections first (so they appear behind nodes)
    ctx.strokeStyle = "#E5E7EB" // gray-200
    ctx.lineWidth = 2
    nodes.forEach(node => {
      node.connections.forEach(connectionId => {
        const connectedNode = nodes.find(n => n.id === connectionId)
        if (connectedNode) {
          ctx.beginPath()
          ctx.moveTo(node.x, node.y)
          ctx.lineTo(connectedNode.x, connectedNode.y)
          ctx.stroke()
        }
      })
    })

    // Draw nodes
    nodes.forEach(node => {
      // Node background
      ctx.fillStyle = node.status === "offline" ? "#9CA3AF" : node.color // gray-400 for offline
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI)
      ctx.fill()

      // Node border
      ctx.strokeStyle = selectedNode?.id === node.id ? "#1F2937" : "#FFFFFF" // gray-800 for selected
      ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2
      ctx.stroke()

      // Status indicator
      const statusColors = {
        online: "#10B981", // emerald-500
        offline: "#6B7280", // gray-500
        error: "#EF4444", // red-500
      }
      ctx.fillStyle = statusColors[node.status]
      ctx.beginPath()
      ctx.arc(node.x + node.radius * 0.6, node.y - node.radius * 0.6, 6, 0, 2 * Math.PI)
      ctx.fill()
      ctx.strokeStyle = "#FFFFFF"
      ctx.lineWidth = 2
      ctx.stroke()

      // Node label
      ctx.fillStyle = "#1F2937" // gray-800
      ctx.font = "12px Inter, sans-serif"
      ctx.textAlign = "center"
      ctx.fillText(node.name, node.x, node.y + node.radius + 15)
    })

    ctx.restore()
  }, [nodes, selectedNode, zoom, pan])

  // Handle canvas click events
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left - pan.x) / zoom
    const y = (event.clientY - rect.top - pan.y) / zoom

    // Find clicked node
    const clickedNode = nodes.find(node => {
      const distance = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2)
      return distance <= node.radius
    })

    setSelectedNode(clickedNode || null)
  }, [nodes, zoom, pan])

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const animate = () => {
      drawNetwork(ctx)
      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [drawNetwork])

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.3))
  const handleResetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedNode(null)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="flex items-center gap-2">
              <IconMapPin className="h-5 w-5" />
              Network Topology
            </CardTitle>
            <CardDescription>
              Interactive visualization of RV-C network devices
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleZoomIn}>
              <IconZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleZoomOut}>
              <IconZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleResetView}>
              Reset
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="border rounded-lg cursor-pointer bg-gray-50"
            onClick={handleCanvasClick}
          />

          {/* Selected node info overlay */}
          {selectedNode && (
            <div className="absolute top-4 left-4 bg-background/95 backdrop-blur-sm border rounded-lg p-4 shadow-lg">
              <h4 className="font-semibold mb-2">{selectedNode.name}</h4>
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <span>Type:</span>
                  <Badge variant="outline">{selectedNode.type}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span>Status:</span>
                  <Badge variant={selectedNode.status === "online" ? "default" :
                                selectedNode.status === "error" ? "destructive" : "secondary"}>
                    {selectedNode.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span>ID:</span>
                  <span className="font-mono text-xs">{selectedNode.id}</span>
                </div>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="absolute bottom-4 right-4 bg-background/95 backdrop-blur-sm border rounded-lg p-4 shadow-lg">
            <h5 className="font-semibold text-sm mb-2">Legend</h5>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                <span>Light</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                <span>Lock</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span>Tank Sensor</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>Temperature</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                <span>Other</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Network statistics sidebar component
 */
function NetworkStatsSidebar({ entities }: { entities: EntityData[] }) {
  const stats = useMemo(() => {
    const deviceTypes = entities.reduce((acc, entity) => {
      acc[entity.device_type] = (acc[entity.device_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const statusCounts = entities.reduce((acc, entity) => {
      const status = entity.state === "on" || entity.state === "online" ? "online" :
                   entity.state === "error" ? "error" : "offline"
      acc[status] = (acc[status] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const sourceCounts = entities.reduce((acc, entity) => {
      const sourceType = entity.source_type || entity.device_type || 'unknown'
      acc[sourceType] = (acc[sourceType] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return {
      total: entities.length,
      deviceTypes,
      statusCounts,
      sourceCounts,
      online: statusCounts.online || 0,
      offline: statusCounts.offline || 0,
      errors: statusCounts.error || 0,
    }
  }, [entities])

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Network Overview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-600">{stats.online}</div>
              <div className="text-xs text-muted-foreground">Online</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-500">{stats.offline}</div>
              <div className="text-xs text-muted-foreground">Offline</div>
            </div>
          </div>

          {stats.errors > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
              <div className="text-xs text-muted-foreground">Errors</div>
            </div>
          )}

          <div className="text-center pt-2 border-t">
            <div className="text-xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">Total Devices</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Device Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(stats.deviceTypes).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Source Protocols</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(stats.sourceCounts).map(([source, count]) => (
              <div key={source} className="flex justify-between items-center">
                <span className="text-sm">{source}</span>
                <Badge variant="secondary">{count}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Network Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span>Connectivity</span>
              <Badge variant="default">
                {stats.total > 0 ? Math.round((stats.online / stats.total) * 100) : 0}%
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span>Error Rate</span>
              <Badge variant={stats.errors > 0 ? "destructive" : "outline"}>
                {stats.total > 0 ? Math.round((stats.errors / stats.total) * 100) : 0}%
              </Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span>Last Update</span>
              <Badge variant="outline">
                {new Date().toLocaleTimeString()}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Protocol Bridge Status Component
 */
function ProtocolBridgeStatus() {
  const { data: bridgeStatus, isLoading } = useQuery({
    queryKey: ['protocol-bridge-status'],
    queryFn: fetchProtocolBridgeStatus,
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: throughput = {} } = useQuery({
    queryKey: ['protocol-throughput'],
    queryFn: fetchProtocolThroughput,
    refetchInterval: 15000,
    staleTime: 10000,
  })

  if (isLoading || !bridgeStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Protocol Bridges</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <IconGitBranch className="h-4 w-4" />
          Protocol Bridges
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-blue-600">{bridgeStatus.bridges_active}</div>
            <div className="text-xs text-muted-foreground">Active</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">{bridgeStatus.total_bridges}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Health Score</span>
            <span className="font-medium">{(bridgeStatus.health_score * 100).toFixed(1)}%</span>
          </div>
          <Progress value={bridgeStatus.health_score * 100} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Translation Rate</span>
            <span className="font-medium">{bridgeStatus.translation_rate.toFixed(1)}/sec</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Error Rate</span>
            <Badge variant={bridgeStatus.error_rate > 0.05 ? 'destructive' : 'outline'}>
              {(bridgeStatus.error_rate * 100).toFixed(2)}%
            </Badge>
          </div>
        </div>

        {Object.entries(bridgeStatus.bridge_statuses).length > 0 && (
          <div className="space-y-2">
            <h6 className="text-xs font-semibold text-muted-foreground">Bridge Status</h6>
            {Object.entries(bridgeStatus.bridge_statuses).map(([bridgeId, bridge]) => (
              <div key={bridgeId} className="flex items-center justify-between p-2 border rounded text-xs">
                <div>
                  <div className="font-medium">
                    {bridge.from_protocol.toUpperCase()} → {bridge.to_protocol.toUpperCase()}
                  </div>
                  <div className="text-muted-foreground">
                    {bridge.translation_count} translations
                  </div>
                </div>
                <Badge variant={bridge.active ? 'default' : 'secondary'}>
                  {bridge.active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            ))}
          </div>
        )}

        <div className="space-y-2">
          <h6 className="text-xs font-semibold text-muted-foreground">Protocol Throughput</h6>
          {Object.entries(throughput).map(([protocol, rate]) => (
            <div key={protocol} className="flex justify-between text-xs">
              <span className="capitalize">{protocol}</span>
              <span className="font-medium">{rate.toFixed(1)} msg/sec</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Multi-Protocol Entity Statistics Component
 */
function MultiProtocolStats({ entities }: { entities: EntityData[] }) {
  const stats = useMemo(() => {
    const protocolCounts = entities.reduce((acc, entity) => {
      const protocol = (entity as EntityData & { protocol?: string }).protocol || 'rvc'
      acc[protocol] = (acc[protocol] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const deviceTypes = entities.reduce((acc, entity) => {
      acc[entity.device_type] = (acc[entity.device_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const statusCounts = entities.reduce((acc, entity) => {
      const status = entity.state === "on" || entity.state === "online" ? "online" :
                   entity.state === "error" ? "error" : "offline"
      acc[status] = (acc[status] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const safetyIssues = entities.filter(entity =>
      (entity as SpartanK2Entity)?.safety_status === 'critical' ||
      (entity as SpartanK2Entity)?.safety_status === 'warning'
    ).length

    return {
      total: entities.length,
      protocolCounts,
      deviceTypes,
      statusCounts,
      safetyIssues,
      online: statusCounts.online || 0,
      offline: statusCounts.offline || 0,
      errors: statusCounts.error || 0,
    }
  }, [entities])

  const protocolColors = {
    rvc: "bg-blue-600",
    j1939: "bg-emerald-600",
    firefly: "bg-violet-600",
    spartan_k2: "bg-red-600",
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <IconNetwork className="h-4 w-4" />
            Multi-Protocol Network
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-600">{stats.online}</div>
              <div className="text-xs text-muted-foreground">Online</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-500">{stats.offline}</div>
              <div className="text-xs text-muted-foreground">Offline</div>
            </div>
          </div>

          {stats.errors > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
              <div className="text-xs text-muted-foreground">Errors</div>
            </div>
          )}

          {stats.safetyIssues > 0 && (
            <Alert className="border-red-200 bg-red-50">
              <IconAlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {stats.safetyIssues} safety issue{stats.safetyIssues > 1 ? 's' : ''} detected
              </AlertDescription>
            </Alert>
          )}

          <div className="text-center pt-2 border-t">
            <div className="text-xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">Total Devices</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Protocol Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(stats.protocolCounts).map(([protocol, count]) => (
              <div key={protocol} className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${protocolColors[protocol as keyof typeof protocolColors] || 'bg-gray-500'}`}></div>
                  <span className="text-sm capitalize">{protocol}</span>
                </div>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Device Types</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(stats.deviceTypes).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Main Network Map page component
 */
export default function NetworkMap() {
  const { data: entities, isLoading, error, refetch } = useEntities()

  // Multi-protocol entity queries
  const { data: j1939Entities } = useQuery({
    queryKey: ['j1939-entities'],
    queryFn: fetchJ1939Entities,
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: fireflyEntities } = useQuery({
    queryKey: ['firefly-entities'],
    queryFn: fetchFireflyEntities,
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: spartanK2Entities } = useQuery({
    queryKey: ['spartan-k2-entities'],
    queryFn: fetchSpartanK2Entities,
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: bridgeStatus } = useQuery({
    queryKey: ['protocol-bridge-status'],
    queryFn: fetchProtocolBridgeStatus,
    refetchInterval: 30000,
    staleTime: 15000,
  })

  const { data: throughput } = useQuery({
    queryKey: ['protocol-throughput'],
    queryFn: fetchProtocolThroughput,
    refetchInterval: 15000,
    staleTime: 10000,
  })

  // Combine all entities
  const allEntities = useMemo(() => {
    const rvcEntities = entities ? Object.values(entities) : []
    const j1939Array = j1939Entities?.entities || []
    const fireflyArray = fireflyEntities?.entities || []
    const spartanK2Array = spartanK2Entities?.entities || []

    return [
      ...rvcEntities.map(e => ({ ...e, protocol: 'rvc' })),
      ...j1939Array,
      ...fireflyArray,
      ...spartanK2Array,
    ]
  }, [entities, j1939Entities, fireflyEntities, spartanK2Entities])

  const entitiesArray = entities ? Object.values(entities) : []

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex justify-between items-center">
            <div>
              <Skeleton className="h-8 w-48 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
            <Skeleton className="h-10 w-24" />
          </div>

          <div className="grid gap-8 lg:grid-cols-4">
            <div className="lg:col-span-3">
              <Card>
                <CardHeader>
                  <Skeleton className="h-6 w-48" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-96 w-full" />
                </CardContent>
              </Card>
            </div>
            <div>
              <Skeleton className="h-96 w-full" />
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout>
        <div className="flex-1 space-y-6 p-4 pt-6">
          <Alert variant="destructive">
            <IconAlertTriangle className="h-4 w-4" />
            <AlertTitle>Error Loading Network Map</AlertTitle>
            <AlertDescription>
              Failed to load network topology data. Please try again.
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
            <h1 className="text-3xl font-bold tracking-tight">Network Map</h1>
            <p className="text-muted-foreground">
              Visual representation of RV-C network topology and device status
            </p>
          </div>
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="gap-2"
          >
            <IconRefresh className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Info Alert */}
        <Alert>
          <IconInfoCircle className="h-4 w-4" />
          <AlertTitle>Interactive Network Visualization</AlertTitle>
          <AlertDescription>
            Click on devices to view details. Use zoom controls to navigate the network topology.
            Status indicators show real-time device connectivity.
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="topology" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="topology">Network Topology</TabsTrigger>
            <TabsTrigger value="protocols">Multi-Protocol View</TabsTrigger>
            <TabsTrigger value="performance">Performance View</TabsTrigger>
          </TabsList>

          <TabsContent value="topology" className="space-y-4">
            <div className="grid gap-8 lg:grid-cols-4">
              {/* Network Canvas - Takes 3/4 width */}
              <div className="lg:col-span-3">
                <NetworkCanvas entities={allEntities} throughput={throughput} />
              </div>

              {/* Network Stats Sidebar - Takes 1/4 width */}
              <div>
                <NetworkStatsSidebar entities={entitiesArray} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="protocols" className="space-y-4">
            <div className="grid gap-6 lg:grid-cols-4">
              <div className="lg:col-span-3 space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <IconNetwork className="h-5 w-5" />
                        Protocol Overview
                      </CardTitle>
                      <CardDescription>
                        Cross-protocol communication and bridge status
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {bridgeStatus ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-blue-600">
                                {bridgeStatus.bridges_active}
                              </div>
                              <div className="text-sm text-muted-foreground">Active Bridges</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold">
                                {(bridgeStatus.health_score * 100).toFixed(0)}%
                              </div>
                              <div className="text-sm text-muted-foreground">Bridge Health</div>
                            </div>
                          </div>
                          <Progress value={bridgeStatus.health_score * 100} className="h-3" />
                          <div className="text-center text-sm text-muted-foreground">
                            {bridgeStatus.translation_rate.toFixed(1)} translations/sec
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <IconGitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">No protocol bridges active</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <IconActivity className="h-5 w-5" />
                        Protocol Throughput
                      </CardTitle>
                      <CardDescription>
                        Real-time message rates by protocol
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {throughput && Object.keys(throughput).length > 0 ? (
                        <div className="space-y-3">
                          {Object.entries(throughput).map(([protocol, rate]) => (
                            <div key={protocol}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="capitalize">{protocol}</span>
                                <span className="font-medium">{rate.toFixed(1)} msg/sec</span>
                              </div>
                              <Progress value={Math.min((rate / 100) * 100, 100)} className="h-2" />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <IconActivity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">No throughput data available</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle>Protocol Entity Distribution</CardTitle>
                    <CardDescription>
                      Entity breakdown across all supported protocols
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                      <div className="text-center p-4 border rounded-lg">
                        <div className="w-4 h-4 bg-blue-600 rounded-full mx-auto mb-2"></div>
                        <div className="text-lg font-bold">
                          {allEntities.filter(e => (e as EntityData & { protocol?: string }).protocol === 'rvc').length}
                        </div>
                        <div className="text-sm text-muted-foreground">RV-C</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="w-4 h-4 bg-emerald-600 rounded-full mx-auto mb-2"></div>
                        <div className="text-lg font-bold">
                          {allEntities.filter(e => (e as EntityData & { protocol?: string }).protocol === 'j1939').length}
                        </div>
                        <div className="text-sm text-muted-foreground">J1939</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="w-4 h-4 bg-violet-600 rounded-full mx-auto mb-2"></div>
                        <div className="text-lg font-bold">
                          {allEntities.filter(e => (e as EntityData & { protocol?: string }).protocol === 'firefly').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Firefly</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="w-4 h-4 bg-red-600 rounded-full mx-auto mb-2"></div>
                        <div className="text-lg font-bold">
                          {allEntities.filter(e => (e as EntityData & { protocol?: string }).protocol === 'spartan_k2').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Spartan K2</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <ProtocolBridgeStatus />
                <MultiProtocolStats entities={allEntities} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-4">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Network Performance Overview</CardTitle>
                    <CardDescription>
                      Real-time performance metrics and health indicators
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {Math.round((allEntities.filter(e => e.state === 'on' || e.state === 'online').length / Math.max(allEntities.length, 1)) * 100)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Connectivity</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {Object.values(throughput || {}).reduce((a, b) => a + b, 0).toFixed(1)}
                        </div>
                        <div className="text-sm text-muted-foreground">Total msg/sec</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {bridgeStatus ? (bridgeStatus.health_score * 100).toFixed(0) : 0}%
                        </div>
                        <div className="text-sm text-muted-foreground">Bridge Health</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Alert>
                  <IconInfoCircle className="h-4 w-4" />
                  <AlertTitle>Performance Monitoring</AlertTitle>
                  <AlertDescription>
                    For detailed performance analytics, visit the dedicated{' '}
                    <a href="/performance" className="font-medium underline">Performance Analytics</a> page.
                  </AlertDescription>
                </Alert>
              </div>

              <div>
                <MultiProtocolStats entities={allEntities} />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}
