/**
 * Entity Status Component
 *
 * Demonstrates the new state management system by showing real entity data.
 * This component serves as an example of how to use the new React Query hooks.
 */

import type { LightEntity } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useEntities, useHealthStatus, useLightControl, useLights } from "@/hooks";

/**
 * Simple loading skeleton for entity cards
 */
function EntityCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-3 w-32" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Light Control Component
 * Demonstrates entity control with optimistic updates
 */
function LightControlCard() {
  const { data: lightsData, isLoading, error } = useLights();
  const lightControl = useLightControl();

  // Convert EntityCollection to array
  const lights = lightsData ? Object.values(lightsData) as LightEntity[] : [];

  if (isLoading) {
    return <EntityCardSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Lighting System</CardTitle>
          <CardDescription>Control RV interior and exterior lights</CardDescription>
        </CardHeader>
        <CardContent>
          <Badge variant="destructive">Error loading lights</Badge>
        </CardContent>
      </Card>
    );
  }

  const handleLightToggle = (light: LightEntity) => {
    lightControl.toggle.mutate(light.id, {
      onError: (error) => {
        console.error('Failed to toggle light:', error);
      },
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lighting System</CardTitle>
        <CardDescription>
          Control RV interior and exterior lights ({lights?.length || 0} lights found)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          {lights && lights.length > 0 ? (
            lights.slice(0, 3).map((light) => (
              <Button
                key={light.id}
                variant={light.state === 'on' ? 'default' : 'outline'}
                onClick={() => handleLightToggle(light)}
                disabled={lightControl.toggle.isPending}
                className="justify-between"
              >
                <span>{light.name || light.id}</span>
                <Badge variant={light.state === 'on' ? 'default' : 'secondary'}>
                  {light.state}
                </Badge>
              </Button>
            ))
          ) : (
            <Badge variant="secondary">No lights available</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * System Status Component
 * Shows system health and CAN bus status
 */
function SystemStatusCard() {
  const { data: health, isLoading, error } = useHealthStatus();

  if (isLoading) {
    return <EntityCardSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
          <CardDescription>Monitor system health and connectivity</CardDescription>
        </CardHeader>
        <CardContent>
          <Badge variant="destructive">Error loading status</Badge>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
        <CardDescription>Monitor system health and connectivity</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span>Overall Status</span>
            <Badge variant={health?.status === 'healthy' ? 'default' : 'destructive'}>
              {health?.status || 'Unknown'}
            </Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Database</span>
            <Badge variant={health?.features?.database ? 'default' : 'destructive'}>
              {health?.features?.database ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>CAN Bus</span>
            <Badge variant={health?.features?.can_interface ? 'default' : 'destructive'}>
              {health?.features?.can_interface ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>WebSocket</span>
            <Badge variant={health?.features?.websocket ? 'default' : 'destructive'}>
              {health?.features?.websocket ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Entity Overview Component
 * Shows total entity counts and types
 */
function EntityOverviewCard() {
  const { data: entitiesData, isLoading, error } = useEntities();

  // Convert EntityCollection to array
  const entities = entitiesData ? Object.values(entitiesData) : [];

  if (isLoading) {
    return <EntityCardSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Entity Overview</CardTitle>
          <CardDescription>Connected devices and sensors</CardDescription>
        </CardHeader>
        <CardContent>
          <Badge variant="destructive">Error loading entities</Badge>
        </CardContent>
      </Card>
    );
  }

  // Count entities by type
  const entityCounts = entities.reduce((acc, entity) => {
    acc[entity.device_type] = (acc[entity.device_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Entity Overview</CardTitle>
        <CardDescription>
          Connected devices and sensors ({entities.length} total)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-2">
          {Object.entries(entityCounts).map(([type, count]) => (
            <div key={type} className="flex justify-between items-center">
              <span className="capitalize">{type.replace('_', ' ')}</span>
              <Badge variant="secondary">{count as number}</Badge>
            </div>
          ))}
          {Object.keys(entityCounts).length === 0 && (
            <Badge variant="secondary">No entities found</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Main component export
 */
export {
  EntityCardSkeleton, EntityOverviewCard, LightControlCard,
  SystemStatusCard
};
