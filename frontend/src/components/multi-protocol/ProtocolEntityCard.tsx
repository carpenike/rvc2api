/**
 * Protocol-Aware Entity Card Component
 *
 * Enhanced entity card that displays protocol-specific information and controls
 * for J1939, Firefly, Spartan K2, and RV-C entities.
 */

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Checkbox } from "@/components/ui/checkbox"
import type { Entity, J1939Entity, FireflyEntity, SpartanK2Entity } from "@/api/types"
import { useOptimisticLightControl } from "@/hooks/useOptimisticMutations"
import {
  IconBulb,
  IconCpu,
  IconEngine,
  IconTruck,
  IconDroplet,
  IconTemperature,
  IconLock,
  IconLockOpen,
  IconToggleLeft,
  IconToggleRight,
  IconSettings,
  IconAlertTriangle,
  IconShield,
  IconActivity
} from "@tabler/icons-react"
import { Link } from "react-router-dom"

interface ProtocolEntityCardProps {
  entity: Entity
  isSelected?: boolean
  onSelectChange?: (selected: boolean) => void
  showProtocolInfo?: boolean
}

/**
 * Get protocol-specific icon and styling
 */
function getProtocolInfo(entity: Entity) {
  // Check if entity has protocol field (for multi-protocol entities)
  const protocol = (entity as Entity & { protocol?: string }).protocol || "rvc"

  const protocolConfig = {
    rvc: {
      color: "text-blue-600",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
      name: "RV-C"
    },
    j1939: {
      color: "text-green-600",
      bgColor: "bg-green-100 dark:bg-green-900/20",
      name: "J1939"
    },
    firefly: {
      color: "text-yellow-600",
      bgColor: "bg-yellow-100 dark:bg-yellow-900/20",
      name: "Firefly"
    },
    spartan_k2: {
      color: "text-red-600",
      bgColor: "bg-red-100 dark:bg-red-900/20",
      name: "Spartan K2"
    }
  }

  return protocolConfig[protocol as keyof typeof protocolConfig] || protocolConfig.rvc
}

/**
 * Get device type icon
 */
function getDeviceIcon(deviceType: string, protocol?: string) {
  if (protocol === "j1939") {
    return IconEngine
  }
  if (protocol === "firefly") {
    return IconBulb
  }
  if (protocol === "spartan_k2") {
    return IconTruck
  }

  // Standard RV-C device icons
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
 * Protocol-specific entity details
 */
function ProtocolEntityDetails({ entity }: { entity: Entity }) {
  const protocol = (entity as Entity & { protocol?: string }).protocol

  // J1939 specific details
  if (protocol === "j1939") {
    const j1939Entity = entity as J1939Entity
    return (
      <div className="space-y-1 text-xs text-muted-foreground">
        {j1939Entity.system_type && (
          <div>System: <span className="font-medium">{j1939Entity.system_type}</span></div>
        )}
        {j1939Entity.manufacturer && (
          <div>Mfg: <span className="font-medium">{j1939Entity.manufacturer}</span></div>
        )}
        {j1939Entity.engine_data && (
          <div className="space-y-1">
            {j1939Entity.engine_data.rpm && (
              <div>RPM: <span className="font-medium">{j1939Entity.engine_data.rpm}</span></div>
            )}
            {j1939Entity.engine_data.coolant_temp && (
              <div>Coolant: <span className="font-medium">{j1939Entity.engine_data.coolant_temp}°F</span></div>
            )}
            {j1939Entity.engine_data.oil_pressure && (
              <div>Oil: <span className="font-medium">{j1939Entity.engine_data.oil_pressure} PSI</span></div>
            )}
          </div>
        )}
      </div>
    )
  }

  // Firefly specific details
  if (protocol === "firefly") {
    const fireflyEntity = entity as FireflyEntity
    return (
      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span>Multiplexed:</span>
          <Badge variant={fireflyEntity.multiplexed ? "default" : "outline"} className="text-xs">
            {fireflyEntity.multiplexed ? "Yes" : "No"}
          </Badge>
        </div>
        {fireflyEntity.safety_interlocks && fireflyEntity.safety_interlocks.length > 0 && (
          <div className="flex items-center gap-1">
            <IconShield className="h-3 w-3" />
            <span>{fireflyEntity.safety_interlocks.length} interlocks</span>
          </div>
        )}
        {fireflyEntity.zone_controls?.scene_id && (
          <div>Scene: <span className="font-medium">{fireflyEntity.zone_controls.scene_id}</span></div>
        )}
      </div>
    )
  }

  // Spartan K2 specific details
  if (protocol === "spartan_k2") {
    const spartanEntity = entity as SpartanK2Entity
    return (
      <div className="space-y-1 text-xs text-muted-foreground">
        {spartanEntity.system_type && (
          <div>System: <span className="font-medium">{spartanEntity.system_type}</span></div>
        )}
        <div className="flex items-center gap-2">
          <span>Safety:</span>
          <Badge
            variant={spartanEntity.safety_status === "safe" ? "default" : "destructive"}
            className="text-xs"
          >
            {spartanEntity.safety_status}
          </Badge>
        </div>
        {spartanEntity.chassis_data && (
          <div className="space-y-1">
            {spartanEntity.chassis_data.brake_pressure && (
              <div>Brake: <span className="font-medium">{spartanEntity.chassis_data.brake_pressure} PSI</span></div>
            )}
            {spartanEntity.chassis_data.suspension_level && (
              <div>Susp: <span className="font-medium">{spartanEntity.chassis_data.suspension_level}%</span></div>
            )}
            {spartanEntity.chassis_data.steering_angle && (
              <div>Steer: <span className="font-medium">{spartanEntity.chassis_data.steering_angle}°</span></div>
            )}
          </div>
        )}
      </div>
    )
  }

  // Standard RV-C entity details (existing logic)
  if (entity.device_type === 'light') {
    const lightEntity = entity as Entity & { brightness?: number }
    return (
      <div className="text-xs text-muted-foreground">
        {lightEntity.brightness !== undefined && (
          <div className="space-y-1">
            <span>Brightness: {lightEntity.brightness}%</span>
            <Progress value={lightEntity.brightness} className="h-1" />
          </div>
        )}
      </div>
    )
  }

  if (entity.device_type === 'tank' || entity.device_type === 'tank_sensor') {
    const tankEntity = entity as Entity & { level?: number; tank_type?: string }
    return (
      <div className="text-xs text-muted-foreground">
        {tankEntity.level !== undefined && (
          <div className="space-y-1">
            <span>Level: {tankEntity.level}%</span>
            <Progress value={tankEntity.level} className="h-1" />
          </div>
        )}
        {tankEntity.tank_type && (
          <span className="block">Type: {tankEntity.tank_type}</span>
        )}
      </div>
    )
  }

  if (entity.device_type === 'temperature' || entity.device_type === 'temperature_sensor') {
    const tempEntity = entity as Entity & { temperature?: number; units?: string }
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
 * Protocol-specific quick actions
 */
function ProtocolEntityActions({ entity }: { entity: Entity }) {
  const optimisticLightControl = useOptimisticLightControl()
  const protocol = (entity as Entity & { protocol?: string }).protocol

  // J1939 actions
  if (protocol === "j1939") {
    return (
      <div className="flex gap-1">
        <Button size="sm" variant="outline" disabled>
          <IconActivity className="h-4 w-4" />
        </Button>
        <Button asChild size="sm" variant="ghost">
          <Link to="/diagnostics">
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  // Firefly actions
  if (protocol === "firefly") {
    const fireflyEntity = entity as FireflyEntity
    return (
      <div className="flex gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="outline" disabled={fireflyEntity.safety_interlocks?.length ? true : false}>
                <IconBulb className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {fireflyEntity.safety_interlocks?.length
                ? "Scene control locked by safety interlocks"
                : "Control lighting scene"}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button asChild size="sm" variant="ghost">
          <Link to="/lights">
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  // Spartan K2 actions
  if (protocol === "spartan_k2") {
    const spartanEntity = entity as SpartanK2Entity
    const isSafe = spartanEntity.safety_status === "safe"

    return (
      <div className="flex gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="sm"
                variant={isSafe ? "outline" : "destructive"}
                disabled={!isSafe}
              >
                {isSafe ? <IconShield className="h-4 w-4" /> : <IconAlertTriangle className="h-4 w-4" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {isSafe ? "System is safe" : "Safety issue detected"}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button asChild size="sm" variant="ghost">
          <Link to="/diagnostics">
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  // Standard RV-C actions (existing logic)
  if (entity.device_type === 'light') {
    const isOn = entity.state === 'on'
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
          <Link to="/lights">
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  if (entity.device_type === 'lock') {
    return (
      <div className="flex gap-1">
        <Button size="sm" variant="outline" disabled>
          {entity.state === 'locked' ?
            <IconLockOpen className="h-4 w-4" /> :
            <IconLock className="h-4 w-4" />
          }
        </Button>
        <Button asChild size="sm" variant="ghost">
          <Link to="/device-mapping">
            <IconSettings className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    )
  }

  // Default actions
  return (
    <Button asChild size="sm" variant="ghost">
      <Link to="/device-mapping">
        <IconSettings className="h-4 w-4" />
      </Link>
    </Button>
  )
}

/**
 * Enhanced entity status indicator with protocol awareness
 */
function ProtocolEntityStatus({ entity }: { entity: Entity }) {
  const isOnline = entity.timestamp && (Date.now() - entity.timestamp) < 300000 // 5 minutes
  const isActive = entity.state === 'on' || entity.state === 'unlocked' || entity.state === 'active'
  const protocol = (entity as Entity & { protocol?: string }).protocol

  // Safety status for Spartan K2
  if (protocol === "spartan_k2") {
    const spartanEntity = entity as SpartanK2Entity
    const isSafetyIssue = spartanEntity.safety_status !== "safe"

    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-xs text-muted-foreground">
          {isOnline ? 'Online' : 'Offline'}
        </span>
        {isSafetyIssue && (
          <Badge variant="destructive" className="text-xs">
            <IconAlertTriangle className="h-3 w-3 mr-1" />
            Safety
          </Badge>
        )}
        {isActive && (
          <Badge variant="default" className="text-xs">Active</Badge>
        )}
      </div>
    )
  }

  // Standard status display
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-xs text-muted-foreground">
        {isOnline ? 'Online' : 'Offline'}
      </span>
      {isActive && (
        <Badge variant="default" className="text-xs">Active</Badge>
      )}
    </div>
  )
}

/**
 * Main ProtocolEntityCard component
 */
export function ProtocolEntityCard({
  entity,
  isSelected = false,
  onSelectChange,
  showProtocolInfo = true
}: ProtocolEntityCardProps) {
  const protocol = (entity as Entity & { protocol?: string }).protocol || "rvc"
  const protocolInfo = getProtocolInfo(entity)
  const DeviceIcon = getDeviceIcon(entity.device_type, protocol)
  const isOnline = entity.timestamp && (Date.now() - entity.timestamp) < 300000

  return (
    <Card className={`@container/card transition-all duration-200 hover:shadow-md hover:scale-[1.02] ${
      isSelected ? 'ring-2 ring-primary' : ''
    }`}>
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
            <div className={`p-2 rounded-lg transition-colors ${
              isOnline ? protocolInfo.bgColor : 'bg-muted'
            }`}>
              <DeviceIcon className={`h-5 w-5 ${
                isOnline ? protocolInfo.color : 'text-muted-foreground'
              }`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium truncate @[200px]/card:text-base">
                  {entity.friendly_name || entity.name || entity.entity_id}
                </h3>
                <Badge variant="outline" className="text-xs">
                  {entity.device_type}
                </Badge>
                {showProtocolInfo && protocol !== "rvc" && (
                  <Badge variant="secondary" className="text-xs">
                    {protocolInfo.name}
                  </Badge>
                )}
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                {entity.suggested_area && (
                  <span className="inline-block bg-background/50 px-2 py-1 rounded text-xs mr-2">
                    {entity.suggested_area}
                  </span>
                )}
                <span className="text-xs">ID: {entity.entity_id}</span>
              </div>
              <ProtocolEntityDetails entity={entity} />
              <div className="mt-2">
                <ProtocolEntityStatus entity={entity} />
              </div>
            </div>
          </div>
          <div className="ml-2">
            <ProtocolEntityActions entity={entity} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default ProtocolEntityCard
