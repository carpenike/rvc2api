/**
 * Network Map Page
 *
 * Canvas-based visualization of the RV-C network topology.
 * Shows real-time device connections and status.
 */

import type { EntityData } from "@/api/types"
import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useEntities } from "@/hooks/useEntities"
import {
  IconAlertTriangle,
  IconInfoCircle,
  IconMapPin,
  IconRefresh,
  IconZoomIn,
  IconZoomOut
} from "@tabler/icons-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

/**
 * Network node interface for canvas rendering
 */
interface NetworkNode {
  id: string
  name: string
  type: string
  x: number
  y: number
  radius: number
  color: string
  status: "online" | "offline" | "error"
  connections: string[]
}

/**
 * Network topology canvas component
 */
function NetworkCanvas({ entities }: { entities: EntityData[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })

  // Convert entities to network nodes
  const nodes = useMemo(() => {
    const canvasWidth = 800
    const canvasHeight = 600
    const padding = 100

    return entities.map((entity, index) => {
      // Simple circular layout algorithm
      const angle = (index / entities.length) * 2 * Math.PI
      const radius = Math.min(canvasWidth, canvasHeight) / 2 - padding
      const centerX = canvasWidth / 2
      const centerY = canvasHeight / 2

      const deviceTypeColors: Record<string, string> = {
        light: "#10B981", // emerald-500
        lock: "#F59E0B", // amber-500
        tank: "#3B82F6", // blue-500
        temperature: "#EF4444", // red-500
        default: "#6B7280", // gray-500
      }

      return {
        id: entity.id,
        name: entity.name,
        type: entity.device_type,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        radius: 20,
        color: deviceTypeColors[entity.device_type] || deviceTypeColors.default,
        status: entity.state === "on" || entity.state === "online" ? "online" :
                entity.state === "error" ? "error" : "offline",
        connections: [], // TODO: Determine connections from entity data
      } as NetworkNode
    })
  }, [entities])

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
 * Main Network Map page component
 */
export default function NetworkMap() {
  const { data: entities, isLoading, error, refetch } = useEntities()

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

        <div className="grid gap-8 lg:grid-cols-4">
          {/* Network Canvas - Takes 3/4 width */}
          <div className="lg:col-span-3">
            <NetworkCanvas entities={entitiesArray} />
          </div>

          {/* Network Stats Sidebar - Takes 1/4 width */}
          <div>
            <NetworkStatsSidebar entities={entitiesArray} />
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
