/**
 * Multi-Protocol Selector Component
 *
 * Allows users to switch between different protocol views (RV-C, J1939, Firefly, Spartan K2)
 * Shows protocol health status and provides filtering capabilities.
 */

import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
    IconActivity,
    IconAlertTriangle,
    IconBulb,
    IconCpu,
    IconEngine,
    IconNetwork,
    IconTruck
} from "@tabler/icons-react"
import { useMemo } from "react"

export type ProtocolType = "all" | "rvc" | "j1939" | "firefly" | "spartan_k2"

export interface ProtocolInfo {
  id: ProtocolType
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  bgColor: string
  entities?: number
  health?: number // 0.0-1.0
  status?: "active" | "warning" | "error" | "offline"
}

interface MultiProtocolSelectorProps {
  selectedProtocol: ProtocolType
  onProtocolChange: (protocol: ProtocolType) => void
  protocolStats?: Record<string, { count: number; health: number; status: string }>
  isLoading?: boolean
  showCompact?: boolean
  className?: string
}

/**
 * Protocol configuration with icons and styling
 */
const PROTOCOL_CONFIG: Record<ProtocolType, ProtocolInfo> = {
  all: {
    id: "all",
    name: "All Protocols",
    description: "View all entities across all protocols",
    icon: IconNetwork,
    color: "text-primary",
    bgColor: "bg-primary/10"
  },
  rvc: {
    id: "rvc",
    name: "RV-C",
    description: "Recreational Vehicle Controller Area Network",
    icon: IconCpu,
    color: "text-blue-600",
    bgColor: "bg-blue-100 dark:bg-blue-900/20"
  },
  j1939: {
    id: "j1939",
    name: "J1939",
    description: "Commercial vehicle network (engine, transmission)",
    icon: IconEngine,
    color: "text-green-600",
    bgColor: "bg-green-100 dark:bg-green-900/20"
  },
  firefly: {
    id: "firefly",
    name: "Firefly",
    description: "Advanced lighting and zone control system",
    icon: IconBulb,
    color: "text-yellow-600",
    bgColor: "bg-yellow-100 dark:bg-yellow-900/20"
  },
  spartan_k2: {
    id: "spartan_k2",
    name: "Spartan K2",
    description: "Chassis systems (brakes, suspension, steering)",
    icon: IconTruck,
    color: "text-red-600",
    bgColor: "bg-red-100 dark:bg-red-900/20"
  }
}

/**
 * Protocol health indicator component
 */
function ProtocolHealthIndicator({ health, status }: { health?: number; status?: string }) {
  if (health === undefined && !status) return null

  const getHealthColor = (health: number) => {
    if (health >= 0.8) return "text-green-600"
    if (health >= 0.6) return "text-yellow-600"
    return "text-red-600"
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <IconActivity className="h-3 w-3 text-green-600" />
      case "warning":
        return <IconAlertTriangle className="h-3 w-3 text-yellow-600" />
      case "error":
        return <IconAlertTriangle className="h-3 w-3 text-red-600" />
      default:
        return <div className="h-2 w-2 rounded-full bg-gray-400" />
    }
  }

  return (
    <div className="flex items-center gap-1">
      {status && getStatusIcon(status)}
      {health !== undefined && (
        <span className={`text-xs font-medium ${getHealthColor(health)}`}>
          {Math.round(health * 100)}%
        </span>
      )}
    </div>
  )
}

/**
 * Protocol card component for grid view
 */
function ProtocolCard({
  protocol,
  isSelected,
  onClick,
  stats
}: {
  protocol: ProtocolInfo
  isSelected: boolean
  onClick: () => void
  stats?: { count: number; health: number; status: string }
}) {
  const Icon = protocol.icon

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            className={`cursor-pointer transition-all duration-200 hover:scale-105 ${
              isSelected
                ? "ring-2 ring-primary shadow-md"
                : "hover:shadow-md"
            }`}
            onClick={onClick}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${protocol.bgColor}`}>
                  <Icon className={`h-5 w-5 ${protocol.color}`} />
                </div>
                {stats && (
                  <ProtocolHealthIndicator health={stats.health} status={stats.status} />
                )}
              </div>
              <div className="space-y-1">
                <h3 className="font-medium text-sm">{protocol.name}</h3>
                {stats && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {stats.count} entities
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {stats.status || "active"}
                    </Badge>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-medium">{protocol.name}</p>
          <p className="text-xs text-muted-foreground">{protocol.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Compact protocol selector for toolbar use
 */
function CompactProtocolSelector({
  selectedProtocol,
  onProtocolChange,
  protocolStats
}: {
  selectedProtocol: ProtocolType
  onProtocolChange: (protocol: ProtocolType) => void
  protocolStats?: Record<string, { count: number; health: number; status: string }>
}) {
  const selectedConfig = PROTOCOL_CONFIG[selectedProtocol]
  const SelectedIcon = selectedConfig.icon

  return (
    <div className="flex items-center gap-2">
      <div className={`p-2 rounded-lg ${selectedConfig.bgColor}`}>
        <SelectedIcon className={`h-4 w-4 ${selectedConfig.color}`} />
      </div>
      <Select value={selectedProtocol} onValueChange={(value) => onProtocolChange(value as ProtocolType)}>
        <SelectTrigger className="w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {Object.values(PROTOCOL_CONFIG).map((protocol) => {
            const stats = protocolStats?.[protocol.id]
            const Icon = protocol.icon

            return (
              <SelectItem key={protocol.id} value={protocol.id}>
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${protocol.color}`} />
                  <span>{protocol.name}</span>
                  {stats && (
                    <Badge variant="outline" className="ml-auto text-xs">
                      {stats.count}
                    </Badge>
                  )}
                </div>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}

/**
 * Main MultiProtocolSelector component
 */
export function MultiProtocolSelector({
  selectedProtocol,
  onProtocolChange,
  protocolStats,
  isLoading = false,
  showCompact = false,
  className = ""
}: MultiProtocolSelectorProps) {
  // Generate protocol info with stats
  const protocolsWithStats = useMemo(() => {
    return Object.values(PROTOCOL_CONFIG).map(protocol => {
      const stats = protocolStats?.[protocol.id]
      return {
        ...protocol,
        entities: stats?.count,
        health: stats?.health,
        status: (stats?.status === "active" || stats?.status === "warning" || stats?.status === "error" || stats?.status === "offline")
          ? stats.status
          : undefined
      } as ProtocolInfo
    })
  }, [protocolStats])

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className="h-8 w-48" />
        </div>
        {!showCompact && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        )}
      </div>
    )
  }

  if (showCompact) {
    const compactProps: {
      selectedProtocol: ProtocolType;
      onProtocolChange: (protocol: ProtocolType) => void;
      protocolStats?: Record<string, { count: number; health: number; status: string; }>;
    } = {
      selectedProtocol,
      onProtocolChange,
    };
    if (protocolStats) {
      compactProps.protocolStats = protocolStats;
    }

    return (
      <div className={className}>
        <CompactProtocolSelector {...compactProps} />
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Protocol Selection</h3>
          <p className="text-sm text-muted-foreground">
            Choose a protocol to view specific entities and controls
          </p>
        </div>
        {protocolStats && (
          <Badge variant="outline">
            {Object.values(protocolStats).reduce((sum, stats) => sum + stats.count, 0)} total entities
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {protocolsWithStats.map((protocol) => {
          const cardProps: {
            protocol: ProtocolInfo;
            isSelected: boolean;
            onClick: () => void;
            stats?: { count: number; health: number; status: string; };
          } = {
            protocol,
            isSelected: selectedProtocol === protocol.id,
            onClick: () => onProtocolChange(protocol.id),
          };

          const stats = protocolStats?.[protocol.id];
          if (stats) {
            cardProps.stats = stats;
          }

          return (
            <ProtocolCard
              key={protocol.id}
              {...cardProps}
            />
          );
        })}
      </div>

      {selectedProtocol !== "all" && (
        <div className="p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            {(() => {
              const SelectedIcon = PROTOCOL_CONFIG[selectedProtocol].icon
              return <SelectedIcon className={`h-5 w-5 ${PROTOCOL_CONFIG[selectedProtocol].color}`} />
            })()}
            <span className="font-medium">{PROTOCOL_CONFIG[selectedProtocol].name}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {PROTOCOL_CONFIG[selectedProtocol].description}
          </p>
        </div>
      )}
    </div>
  )
}

export default MultiProtocolSelector
