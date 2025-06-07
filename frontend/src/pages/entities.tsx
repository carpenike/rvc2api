/**
 * Entities Management Page
 *
 * Consolidated view of all entities in the system with filtering,
 * search, and device-specific management capabilities.
 * Supports current CAN bus devices and future integrations like
 * Victron power management, Shelly ESP devices, etc.
 */

import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { LightEntity } from "@/api/types"
import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import { useEntities } from "@/hooks/useEntities"
import { useOptimisticLightControl, useOptimisticBulkControl } from "@/hooks/useOptimisticMutations"
import type { Entity, TankEntity, TemperatureEntity } from "@/api/types"
import {
    IconBulb,
    IconCpu,
    IconDroplet,
    IconLock,
    IconLockOpen,
    IconSearch,
    IconSettings,
    IconTemperature,
    IconToggleLeft,
    IconToggleRight,
    IconTrendingUp,
    IconX
} from "@tabler/icons-react"
import { useState, useMemo } from "react"
import { Link } from "react-router-dom"

/**
 * Entity status indicator component
 */
function EntityStatusIndicator({ entity }: { entity: Entity }) {
  const isOnline = entity.timestamp && (Date.now() - entity.timestamp) < 300000 // 5 minutes
  const isActive = entity.state === 'on' || entity.state === 'unlocked' || entity.state === 'active'

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-xs text-muted-foreground">
        {isOnline ? 'Online' : 'Offline'}
      </span>
      {isActive && (
        <Badge variant="default">Active</Badge>
      )}
    </div>
  )
}

/**
 * Device type icon helper
 */
function getDeviceIcon(deviceType: string) {
  switch (deviceType) {
    case 'light':
      return IconBulb
    case 'lock':
      return IconLock
    case 'tank':
    case 'tank_sensor':
      return IconDroplet
    case 'temperature':
    case 'temperature_sensor':
      return IconTemperature
    default:
      return IconCpu
  }
}

/**
 * Device type badge color helper
 */
function getDeviceTypeBadgeVariant(deviceType: string): "default" | "secondary" | "destructive" | "outline" {
  switch (deviceType) {
    case 'light':
      return 'default'
    case 'lock':
      return 'secondary'
    case 'tank':
    case 'tank_sensor':
      return 'outline'
    case 'temperature':
    case 'temperature_sensor':
      return 'outline'
    default:
      return 'secondary'
  }
}

/**
 * Entity quick actions component
 */
function EntityQuickActions({ entity }: { entity: Entity }) {
  const optimisticLightControl = useOptimisticLightControl()

  if (entity.device_type === 'light') {
    const lightEntity = entity as LightEntity
    const isOn = lightEntity.state === 'on'

    return (
      <div className="flex gap-1">
        <Button
          size="sm"
          variant="outline"
          onClick={() => optimisticLightControl.toggle.mutate({ entityId: entity.entity_id })}
          disabled={optimisticLightControl.toggle.isPending}
        >
          {isOn ? <IconToggleRight className="h-4 w-4" /> : <IconToggleLeft className="h-4 w-4" />}
        </Button>
        <Button asChild size="sm" variant="ghost">
          <Link to={`/lights`}>
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  if (entity.device_type === 'lock') {
    return (
      <div className="flex gap-1">
        <Button size="sm" variant="outline">
          {entity.state === 'locked' ?
            <IconLockOpen className="h-4 w-4" /> :
            <IconLock className="h-4 w-4" />
          }
        </Button>
        <Button asChild size="sm" variant="ghost">
          <Link to={`/device-mapping`}>
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  // Default actions for other entity types
  return (
    <Button asChild size="sm" variant="ghost">
      <Link to="/device-mapping">
        <IconSettings className="h-4 w-4" />
      </Link>
    </Button>
  )
}

/**
 * Entity details display
 */
function EntityDetails({ entity }: { entity: Entity }) {
  if (entity.device_type === 'light') {
    const lightEntity = entity as LightEntity
    return (
      <div className="text-xs text-muted-foreground">
        {lightEntity.brightness !== undefined && (
          <span>Brightness: {lightEntity.brightness}%</span>
        )}
      </div>
    )
  }

  if (entity.device_type === 'tank' || entity.device_type === 'tank_sensor') {
    const tankEntity = entity as TankEntity
    return (
      <div className="text-xs text-muted-foreground">
        {tankEntity.level !== undefined && (
          <span>Level: {tankEntity.level}%</span>
        )}
        {tankEntity.tank_type && (
          <span className="ml-2">Type: {tankEntity.tank_type}</span>
        )}
      </div>
    )
  }

  if (entity.device_type === 'temperature' || entity.device_type === 'temperature_sensor') {
    const tempEntity = entity as TemperatureEntity
    return (
      <div className="text-xs text-muted-foreground">
        {tempEntity.temperature !== undefined && (
          <span>{tempEntity.temperature}°{tempEntity.units || 'F'}</span>
        )}
      </div>
    )
  }

  return null
}

/**
 * Individual entity card component with enhanced design
 */
function EntityCard({
  entity,
  isSelected = false,
  onSelectChange
}: {
  entity: Entity
  isSelected?: boolean
  onSelectChange?: (selected: boolean) => void
}) {
  const DeviceIcon = getDeviceIcon(entity.device_type)
  const isOnline = entity.timestamp && (Date.now() - entity.timestamp) < 300000
  const isActive = entity.state === 'on' || entity.state === 'unlocked' || entity.state === 'active'

  return (
    <Card className={`@container/card from-primary/5 to-card bg-gradient-to-t shadow-xs hover:shadow-md transition-all duration-200 hover:scale-[1.02] ${isSelected ? 'ring-2 ring-primary' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {onSelectChange && (
            <div className="mr-3 pt-2">
              <Checkbox
                checked={isSelected}
                onCheckedChange={onSelectChange}
                aria-label={`Select ${entity.friendly_name || entity.name || entity.entity_id}`}
              />
            </div>
          )}
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg transition-colors ${isOnline ? 'bg-primary/10' : 'bg-muted'}`}>
              <DeviceIcon className={`h-5 w-5 ${isOnline ? 'text-primary' : 'text-muted-foreground'}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium truncate @[200px]/card:text-base">
                  {entity.friendly_name || entity.name || entity.entity_id}
                </h3>
                <Badge
                  variant={getDeviceTypeBadgeVariant(entity.device_type)}
                  className="text-xs"
                >
                  {entity.device_type}
                </Badge>
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                {entity.suggested_area && (
                  <span className="inline-block bg-background/50 px-2 py-1 rounded text-xs mr-2">
                    {entity.suggested_area}
                  </span>
                )}
                <span className="text-xs">ID: {entity.entity_id}</span>
              </div>
              <EntityDetails entity={entity} />
              <div className="mt-2 flex items-center justify-between">
                <EntityStatusIndicator entity={entity} />
                {isActive && (
                  <Badge variant="default" className="text-xs">
                    <IconTrendingUp className="mr-1 h-3 w-3" />
                    Active
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <div className="ml-2">
            <EntityQuickActions entity={entity} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

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
 * Main Entities Page Component
 */
export default function EntitiesPage() {
  const { data: entitiesData, isLoading, error } = useEntities()
  const [searchTerm, setSearchTerm] = useState("")
  const [deviceTypeFilter, setDeviceTypeFilter] = useState<string>("all")
  const [areaFilter, setAreaFilter] = useState<string>("all")
  const [selectedEntities, setSelectedEntities] = useState<string[]>([])
  const [showBulkActions, setShowBulkActions] = useState(false)

  // Convert entities object to array
  const entities = useMemo(() => {
    return entitiesData ? Object.values(entitiesData) : []
  }, [entitiesData])

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
            <h1 className="text-3xl font-bold tracking-tight">Entities</h1>
            <p className="text-muted-foreground">Manage all your RV devices and sensors</p>
          </div>

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

  if (error) {
    return (
      <AppLayout pageTitle="Entities">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Entities</h1>
            <p className="text-muted-foreground">Manage all your RV devices and sensors</p>
          </div>

          <Card>
            <CardContent className="p-6 text-center">
              <IconX className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Unable to Load Entities</h3>
              <p className="text-muted-foreground">
                There was an error loading your entities. Please check your connection and try again.
              </p>
            </CardContent>
          </Card>
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
            <h1 className="text-3xl font-bold tracking-tight">Entities</h1>
            <p className="text-muted-foreground">
              Manage all your RV devices and sensors in one place
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
              <EntityCard
                key={entity.entity_id}
                entity={entity}
                isSelected={selectedEntities.includes(entity.entity_id)}
                onSelectChange={showBulkActions ? (selected) => handleEntitySelect(entity.entity_id, selected) : undefined}
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
