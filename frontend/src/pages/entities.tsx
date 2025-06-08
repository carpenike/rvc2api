/**
 * Entities Management Page
 *
 * Multi-protocol entity management with support for RV-C, J1939, Firefly,
 * and Spartan K2 protocols. Provides filtering, search, and protocol-specific
 * controls following professional diagnostic tool patterns.
 */

import { AppLayout } from "@/components/app-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { MultiProtocolSelector, ProtocolEntityCard, type ProtocolType } from "@/components/multi-protocol"
import { useEntities } from "@/hooks/useEntities"
import { useOptimisticBulkControl } from "@/hooks/useOptimisticMutations"
import type { Entity } from "@/api/types"
import { fetchJ1939Entities, fetchFireflyEntities, fetchSpartanK2Entities, fetchProtocolBridgeStatus } from "@/api/endpoints"
import {
    IconBulb,
    IconCpu,
    IconDroplet,
    IconLock,
    IconSearch,
    IconSettings,
    IconTemperature,
    IconTrendingUp,
    IconAlertTriangle
} from "@tabler/icons-react"
import { useState, useMemo } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"



/**
 * Enhanced entity statistics component
 */
function EntityStatistics({ entities }: { entities: Entity[] }) {
  const deviceCounts = useMemo(() => {
    return entities.reduce((acc, entity) => {
      acc[entity.device_type] = (acc[entity.device_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
  }, [entities])

  const onlineCount = entities.filter(entity =>
    entity.timestamp && (Date.now() - entity.timestamp) < 300000
  ).length

  const activeCount = entities.filter(entity =>
    entity.state === 'on' || entity.state === 'unlocked' || entity.state === 'active'
  ).length

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-2 md:grid-cols-4 gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs">
      <Card className="@container/card">
        <CardContent className="p-4 text-center">
          <div className="text-2xl font-semibold tabular-nums @[150px]/card:text-3xl">{entities.length}</div>
          <div className="text-xs text-muted-foreground">Total Entities</div>
        </CardContent>
      </Card>
      <Card className="@container/card">
        <CardContent className="p-4 text-center">
          <div className="text-2xl font-semibold tabular-nums @[150px]/card:text-3xl text-green-600">{onlineCount}</div>
          <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
            <IconTrendingUp className="h-3 w-3" />
            Online
          </div>
        </CardContent>
      </Card>
      <Card className="@container/card">
        <CardContent className="p-4 text-center">
          <div className="text-2xl font-semibold tabular-nums @[150px]/card:text-3xl text-blue-600">{activeCount}</div>
          <div className="text-xs text-muted-foreground">Active</div>
        </CardContent>
      </Card>
      {Object.entries(deviceCounts).slice(0, 1).map(([type, count]) => (
        <Card key={type} className="@container/card">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold tabular-nums @[150px]/card:text-3xl">{count}</div>
            <div className="text-xs text-muted-foreground capitalize">
              {type.replace('_', ' ')}s
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

/**
 * Device management shortcuts component
 */
function DeviceManagementShortcuts({ deviceTypes }: { deviceTypes: string[] }) {
  const shortcuts = [
    { type: 'light', label: 'Control Lights', icon: IconBulb, path: '/lights' },
    { type: 'lock', label: 'Device Mapping', icon: IconLock, path: '/device-mapping' },
    { type: 'tank', label: 'Device Mapping', icon: IconDroplet, path: '/device-mapping' },
    { type: 'temperature', label: 'Device Mapping', icon: IconTemperature, path: '/device-mapping' },
  ]

  const availableShortcuts = shortcuts.filter(shortcut =>
    deviceTypes.some(type => type.includes(shortcut.type))
  )

  if (availableShortcuts.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconSettings className="size-5" />
          Device Management
        </CardTitle>
        <CardDescription>Quick access to device-specific controls</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {availableShortcuts.map(({ type, label, icon: Icon, path }) => (
            <Button key={type} asChild variant="outline" className="h-auto p-4 flex-col">
              <Link to={path}>
                <Icon className="h-6 w-6 mb-2" />
                <span className="text-xs text-center">{label}</span>
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Bulk control actions component
 */
function BulkControlActions({
  selectedEntities,
  onClearSelection
}: {
  selectedEntities: string[]
  onClearSelection: () => void
}) {
  const optimisticBulkControl = useOptimisticBulkControl()

  const handleBulkAction = async (command: string, parameters: Record<string, unknown> = {}) => {
    if (selectedEntities.length === 0) return

    await optimisticBulkControl.mutateAsync({
      entity_ids: selectedEntities,
      command,
      parameters,
      ignore_errors: true
    })

    onClearSelection()
  }

  if (selectedEntities.length === 0) {
    return null
  }

  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="font-medium">{selectedEntities.length}</span> entities selected
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => handleBulkAction('on')}
                size="sm"
                variant="outline"
                disabled={optimisticBulkControl.isPending}
              >
                Turn On
              </Button>
              <Button
                onClick={() => handleBulkAction('off')}
                size="sm"
                variant="outline"
                disabled={optimisticBulkControl.isPending}
              >
                Turn Off
              </Button>
              <Button
                onClick={() => handleBulkAction('toggle')}
                size="sm"
                variant="outline"
                disabled={optimisticBulkControl.isPending}
              >
                Toggle
              </Button>
            </div>
          </div>
          <Button
            onClick={onClearSelection}
            size="sm"
            variant="ghost"
            disabled={optimisticBulkControl.isPending}
          >
            Clear Selection
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Hook to fetch multi-protocol entities
 */
function useMultiProtocolEntities(selectedProtocol: ProtocolType) {
  const { data: rvcEntities, isLoading: rvcLoading } = useEntities()

  const { data: j1939Entities, isLoading: j1939Loading } = useQuery({
    queryKey: ['entities', 'j1939'],
    queryFn: fetchJ1939Entities,
    enabled: selectedProtocol === 'all' || selectedProtocol === 'j1939',
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  const { data: fireflyEntities, isLoading: fireflyLoading } = useQuery({
    queryKey: ['entities', 'firefly'],
    queryFn: fetchFireflyEntities,
    enabled: selectedProtocol === 'all' || selectedProtocol === 'firefly',
    refetchInterval: 30000
  })

  const { data: spartanEntities, isLoading: spartanLoading } = useQuery({
    queryKey: ['entities', 'spartan_k2'],
    queryFn: fetchSpartanK2Entities,
    enabled: selectedProtocol === 'all' || selectedProtocol === 'spartan_k2',
    refetchInterval: 30000
  })

  const { data: bridgeStatus } = useQuery({
    queryKey: ['protocol-bridge-status'],
    queryFn: fetchProtocolBridgeStatus,
    refetchInterval: 15000 // Bridge status refreshes more frequently
  })

  // Combine entities based on selected protocol
  const combinedEntities = useMemo(() => {
    const entities: Entity[] = []

    if (selectedProtocol === 'all' || selectedProtocol === 'rvc') {
      if (rvcEntities) {
        entities.push(...Object.values(rvcEntities))
      }
    }

    if (selectedProtocol === 'all' || selectedProtocol === 'j1939') {
      if (j1939Entities) {
        entities.push(...Object.values(j1939Entities))
      }
    }

    if (selectedProtocol === 'all' || selectedProtocol === 'firefly') {
      if (fireflyEntities) {
        entities.push(...Object.values(fireflyEntities))
      }
    }

    if (selectedProtocol === 'all' || selectedProtocol === 'spartan_k2') {
      if (spartanEntities) {
        entities.push(...Object.values(spartanEntities))
      }
    }

    return entities
  }, [selectedProtocol, rvcEntities, j1939Entities, fireflyEntities, spartanEntities])

  // Calculate protocol stats for selector
  const protocolStats = useMemo(() => {
    const stats: Record<string, { count: number; health: number; status: string }> = {
      all: { count: combinedEntities.length, health: 0.95, status: 'active' },
      rvc: { count: rvcEntities ? Object.keys(rvcEntities).length : 0, health: 0.98, status: 'active' },
      j1939: { count: j1939Entities ? Object.keys(j1939Entities).length : 0, health: 0.92, status: 'active' },
      firefly: { count: fireflyEntities ? Object.keys(fireflyEntities).length : 0, health: 0.89, status: 'warning' },
      spartan_k2: { count: spartanEntities ? Object.keys(spartanEntities).length : 0, health: 0.96, status: 'active' }
    }

    // Update health scores based on bridge status if available
    if (bridgeStatus) {
      stats.all.health = bridgeStatus.health_score
      if (bridgeStatus.error_rate > 0.1) {
        stats.all.status = 'warning'
      }
    }

    return stats
  }, [combinedEntities.length, rvcEntities, j1939Entities, fireflyEntities, spartanEntities, bridgeStatus])

  const isLoading = rvcLoading ||
    (selectedProtocol === 'j1939' && j1939Loading) ||
    (selectedProtocol === 'firefly' && fireflyLoading) ||
    (selectedProtocol === 'spartan_k2' && spartanLoading)

  return {
    entities: combinedEntities,
    protocolStats,
    bridgeStatus,
    isLoading
  }
}

/**
 * Main Entities Page Component
 */
export default function EntitiesPage() {
  const [selectedProtocol, setSelectedProtocol] = useState<ProtocolType>("all")
  const [searchTerm, setSearchTerm] = useState("")
  const [deviceTypeFilter, setDeviceTypeFilter] = useState<string>("all")
  const [areaFilter, setAreaFilter] = useState<string>("all")
  const [selectedEntities, setSelectedEntities] = useState<string[]>([])
  const [showBulkActions, setShowBulkActions] = useState(false)

  const { entities, protocolStats, bridgeStatus, isLoading } = useMultiProtocolEntities(selectedProtocol)

  // Get unique device types and areas for filters
  const { deviceTypes, areas } = useMemo(() => {
    const types = [...new Set(entities.map(e => e.device_type))].sort()
    const areaList = [...new Set(entities.map(e => e.suggested_area).filter(Boolean))].sort()
    return { deviceTypes: types, areas: areaList }
  }, [entities])

  // Filter entities based on search and filters
  const filteredEntities = useMemo(() => {
    return entities.filter(entity => {
      const matchesSearch = !searchTerm ||
        entity.friendly_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entity.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entity.entity_id.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesDeviceType = deviceTypeFilter === "all" || entity.device_type === deviceTypeFilter
      const matchesArea = areaFilter === "all" || entity.suggested_area === areaFilter

      return matchesSearch && matchesDeviceType && matchesArea
    })
  }, [entities, searchTerm, deviceTypeFilter, areaFilter])

  // Selection handlers
  const handleEntitySelect = (entityId: string, selected: boolean) => {
    setSelectedEntities(prev =>
      selected
        ? [...prev, entityId]
        : prev.filter(id => id !== entityId)
    )
  }

  const handleSelectAll = () => {
    const allFilteredIds = filteredEntities.map(entity => entity.entity_id)
    setSelectedEntities(allFilteredIds)
  }

  const handleClearSelection = () => {
    setSelectedEntities([])
  }

  const toggleBulkMode = () => {
    setShowBulkActions(!showBulkActions)
    if (showBulkActions) {
      setSelectedEntities([])
    }
  }

  if (isLoading) {
    return (
      <AppLayout pageTitle="Entities">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Multi-Protocol Entities</h1>
            <p className="text-muted-foreground">Manage all your RV devices and sensors across protocols</p>
          </div>

          {/* Protocol Selector Loading */}
          <Card>
            <CardContent className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout pageTitle="Entities">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Multi-Protocol Entities</h1>
            <p className="text-muted-foreground">
              Manage all your RV devices and sensors across protocols
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={toggleBulkMode}
              variant={showBulkActions ? "default" : "outline"}
              className="gap-2"
            >
              <IconSettings className="h-4 w-4" />
              {showBulkActions ? "Exit Bulk Mode" : "Bulk Actions"}
            </Button>
            {showBulkActions && filteredEntities.length > 0 && (
              <Button
                onClick={handleSelectAll}
                variant="outline"
                size="sm"
                className="gap-2"
              >
                Select All ({filteredEntities.length})
              </Button>
            )}
          </div>
        </div>

        {/* Protocol Selector */}
        <MultiProtocolSelector
          selectedProtocol={selectedProtocol}
          onProtocolChange={setSelectedProtocol}
          protocolStats={protocolStats}
          isLoading={isLoading}
        />

        {/* Bridge Status Alert */}
        {bridgeStatus && bridgeStatus.error_rate > 0.1 && (
          <Alert>
            <IconAlertTriangle className="h-4 w-4" />
            <AlertTitle>Protocol Bridge Warning</AlertTitle>
            <AlertDescription>
              Protocol translation error rate is {Math.round(bridgeStatus.error_rate * 100)}%.
              Some cross-protocol communications may be affected.
            </AlertDescription>
          </Alert>
        )}

        {/* Statistics */}
        <EntityStatistics entities={entities} />

        {/* Search and Filters */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <IconSearch className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search entities..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={deviceTypeFilter} onValueChange={setDeviceTypeFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Device Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {deviceTypes.map(type => (
                    <SelectItem key={type} value={type}>
                      {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={areaFilter} onValueChange={setAreaFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Area" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Areas</SelectItem>
                  {areas.map(area => (
                    <SelectItem key={area} value={area}>
                      {area}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Bulk Control Actions */}
        {showBulkActions && (
          <BulkControlActions
            selectedEntities={selectedEntities}
            onClearSelection={handleClearSelection}
          />
        )}

        {/* Device Management Shortcuts */}
        <DeviceManagementShortcuts deviceTypes={deviceTypes} />

        {/* Entities Grid */}
        {filteredEntities.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredEntities.map(entity => (
              <ProtocolEntityCard
                key={entity.entity_id}
                entity={entity}
                isSelected={selectedEntities.includes(entity.entity_id)}
                onSelectChange={showBulkActions ? (selected) => handleEntitySelect(entity.entity_id, selected) : undefined}
                showProtocolInfo={selectedProtocol === "all"}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <IconCpu className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Entities Found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm || deviceTypeFilter !== "all" || areaFilter !== "all"
                  ? "No entities match your current filters."
                  : "No entities have been discovered yet."}
              </p>
              {(searchTerm || deviceTypeFilter !== "all" || areaFilter !== "all") && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchTerm("")
                    setDeviceTypeFilter("all")
                    setAreaFilter("all")
                  }}
                >
                  Clear Filters
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  )
}
