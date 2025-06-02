/**
 * Lights Management Page
 *
 * Provides entity-based light control using /api/entities endpoint.
 * Features group-based organization, individual controls, and real-time updates.
 */

import type { EntityData, LightEntity } from "@/api/types"
import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useLightControl, useLights } from "@/hooks/useEntities"
import { cn } from "@/lib/utils"
import { IconBulb, IconBulbOff, IconMinus, IconPlus } from "@tabler/icons-react"

/**
 * Individual light control component
 */
interface LightControlProps {
  light: EntityData
}

function LightControl({ light }: LightControlProps) {
  const { toggle, setBrightness } = useLightControl()

  const isOn = light.state === "on" || light.state === "true"
  const lightEntity = light as LightEntity
  const brightness = lightEntity.brightness || 0
  const hasBrightnessControl = light.capabilities?.includes("brightness")

  const handleBrightnessAdjust = (delta: number) => {
    const newBrightness = Math.max(0, Math.min(100, brightness + delta))
    setBrightness.mutate({ entityId: light.id, brightness: newBrightness })
  }

  return (
    <Card className={cn(
      "transition-all duration-200",
      isOn && "ring-2 ring-primary/20 bg-primary/5"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isOn ? (
              <IconBulb className="size-5 text-yellow-500" />
            ) : (
              <IconBulbOff className="size-5 text-muted-foreground" />
            )}
            <CardTitle className="text-base">
              {light.name}
            </CardTitle>
          </div>
          <Badge variant={isOn ? "default" : "secondary"}>
            {isOn ? "ON" : "OFF"}
          </Badge>
        </div>
        {light.suggested_area && (
          <CardDescription>{light.suggested_area}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Main Controls */}
        <div className="flex gap-2">
          <Button
            onClick={() => toggle.mutate(light.id)}
            disabled={toggle.isPending || setBrightness.isPending}
            className="flex-1"
            variant={isOn ? "default" : "outline"}
          >
            {isOn ? "Turn Off" : "Turn On"}
          </Button>
        </div>

        {/* Brightness Control */}
        {hasBrightnessControl && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Brightness</span>
              <span className="text-sm text-muted-foreground">{brightness}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBrightnessAdjust(-10)}
                disabled={toggle.isPending || setBrightness.isPending || brightness <= 0}
              >
                <IconMinus className="size-4" />
              </Button>
              <div className="flex-1 bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-200"
                  style={{ width: `${brightness}%` }}
                />
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBrightnessAdjust(10)}
                disabled={toggle.isPending || setBrightness.isPending || brightness >= 100}
              >
                <IconPlus className="size-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Capabilities */}
        {light.capabilities && light.capabilities.length > 0 && (
          <div className="pt-2 border-t">
            <div className="text-xs text-muted-foreground mb-1">Capabilities</div>
            <div className="flex flex-wrap gap-1">
              {light.capabilities.map((capability, index) => (
                <Badge key={`${light.id}-capability-${index}`} variant="outline" className="text-xs">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Last Updated */}
        {light.last_updated && (
          <div className="text-xs text-muted-foreground">
            Last updated: {new Date(light.last_updated).toLocaleString()}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Loading skeleton for light controls
 */
function LightControlSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="size-5" />
            <Skeleton className="h-5 w-24" />
          </div>
          <Skeleton className="h-5 w-12" />
        </div>
        <Skeleton className="h-4 w-16" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-8" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-8" />
            <Skeleton className="h-2 flex-1" />
            <Skeleton className="h-8 w-8" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Group-based light organization
 */
interface LightGroupProps {
  title: string
  lights: EntityData[]
}

function LightGroup({ title, lights }: LightGroupProps) {
  if (lights.length === 0) return null

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {lights.map((light) => (
          <LightControl key={light.id || light.entity_id} light={light} />
        ))}
      </div>
    </div>
  )
}

/**
 * Lights Management Page Component
 */
export default function Lights() {
  const { data: lights, isLoading, error } = useLights()

  if (isLoading) {
    return (
      <AppLayout pageTitle="Lights">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Lights</h1>
              <p className="text-muted-foreground">
                Control and monitor all lighting systems
              </p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <LightControlSkeleton key={index} />
            ))}
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout pageTitle="Lights">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Lights</h1>
              <p className="text-muted-foreground">
                Control and monitor all lighting systems
              </p>
            </div>
          </div>
          <Card>
            <CardHeader>
              <CardTitle className="text-destructive">Error Loading Lights</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Unable to load light information. Please check your connection and try again.
              </p>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    )
  }

  const lightArray = lights ? Object.values(lights) : []

  if (lightArray.length === 0) {
    return (
      <AppLayout pageTitle="Lights">
        <div className="flex-1 space-y-6 p-4 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Lights</h1>
              <p className="text-muted-foreground">
                Control and monitor all lighting systems
              </p>
            </div>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>No Lights Found</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                No light entities are currently detected. Check your RV-C network connection
                and ensure light devices are properly configured.
              </p>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    )
  }

  // Group lights by area
  const groupedLights = lightArray.reduce((groups, light) => {
    const area = light.suggested_area || "Other"
    if (!groups[area]) {
      groups[area] = []
    }
    groups[area].push(light)
    return groups
  }, {} as Record<string, EntityData[]>)

  const sortedGroups = Object.entries(groupedLights).sort(([a], [b]) => {
    // Put "Other" group last
    if (a === "Other") return 1
    if (b === "Other") return -1
    return a.localeCompare(b)
  })

  return (
    <AppLayout pageTitle="Lights">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Lights</h1>
            <p className="text-muted-foreground">
              Control and monitor all lighting systems
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {lightArray.length} devices
            </Badge>
            <Badge variant="outline">
              {lightArray.filter(light => light.state === "on" || light.state === "true").length} active
            </Badge>
          </div>
        </div>

        {/* Light Groups */}
        <div className="space-y-8">
          {sortedGroups.map(([groupName, groupLights]) => (
            <LightGroup
              key={groupName}
              title={groupName}
              lights={groupLights}
            />
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
