/**
 * Entity Query Hooks
 *
 * Custom React Query hooks for entity management.
 * Provides type-safe, optimized data fetching for all entity types.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import {
  controlEntity,
  fetchEntities,
  fetchEntity,
  fetchEntityHistory,
  fetchEntityMetadata,
  fetchLights,
  fetchLocks,
  fetchTankSensors,
  fetchTemperatureSensors,
  lockEntity,
  unlockEntity,
} from '../api';
import type {
  ControlCommand,
  ControlEntityResponse,
  EntitiesQueryParams,
  EntityBase,
  LightEntity,
  LockEntity,
  TankSensorEntity,
  TemperatureSensorEntity
} from '../api/types';
import { queryKeys, STALE_TIMES } from '../lib/query-client';

/**
 * Hook to fetch all entities
 */
export function useEntities(params?: EntitiesQueryParams) {
  return useQuery({
    queryKey: queryKeys.entities.list(params),
    queryFn: () => fetchEntities(params),
    staleTime: STALE_TIMES.ENTITIES,
  });
}

/**
 * Hook to fetch a specific entity by ID
 */
export function useEntity(entityId: string) {
  return useQuery({
    queryKey: queryKeys.entities.detail(entityId),
    queryFn: () => fetchEntity(entityId),
    staleTime: STALE_TIMES.ENTITIES,
    enabled: !!entityId,
  });
}

/**
 * Hook to fetch entity metadata
 */
export function useEntityMetadata(entityId: string) {
  return useQuery({
    queryKey: queryKeys.entities.metadata(entityId),
    queryFn: () => fetchEntityMetadata(),
    staleTime: STALE_TIMES.ENTITY_METADATA,
    enabled: !!entityId,
  });
}

/**
 * Hook to fetch entity history
 */
export function useEntityHistory(
  entityId: string,
  options?: { limit?: number; offset?: number; start_time?: string; end_time?: string }
) {
  return useQuery({
    queryKey: queryKeys.entities.history(entityId, options),
    queryFn: () => fetchEntityHistory(entityId, options),
    staleTime: STALE_TIMES.ENTITY_METADATA,
    enabled: !!entityId,
  });
}

/**
 * Hook to fetch all light entities
 */
export function useLights() {
  return useQuery({
    queryKey: queryKeys.lights.list(),
    queryFn: fetchLights,
    staleTime: STALE_TIMES.ENTITIES,
  });
}

/**
 * Hook to fetch all lock entities
 */
export function useLocks() {
  return useQuery({
    queryKey: queryKeys.locks.list(),
    queryFn: fetchLocks,
    staleTime: STALE_TIMES.ENTITIES,
  });
}

/**
 * Hook to fetch all tank sensor entities
 */
export function useTankSensors() {
  return useQuery({
    queryKey: queryKeys.tankSensors.list(),
    queryFn: fetchTankSensors,
    staleTime: STALE_TIMES.ENTITIES,
  });
}

/**
 * Hook to fetch all temperature sensor entities
 */
export function useTemperatureSensors() {
  return useQuery({
    queryKey: queryKeys.temperatureSensors.list(),
    queryFn: fetchTemperatureSensors,
    staleTime: STALE_TIMES.ENTITIES,
  });
}

/**
 * Hook for generic entity control commands
 */
export function useControlEntity() {
  const queryClient = useQueryClient();
  // Track pending optimistic updates per entity
  const pendingTimers = useRef<Record<string, NodeJS.Timeout>>({});
  const lastConfirmedTimestamps = useRef<Record<string, number>>({});

  // Listen for WebSocket entity updates to clear pending timers
  useEffect(() => {
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'updated' && event.query.queryKey && Array.isArray(event.query.queryKey)) {
        const key = event.query.queryKey;
        // Only care about entity detail updates
        if (key[0] === 'entity' && typeof key[1] === 'string') {
          const entityId = key[1];
          const entity = queryClient.getQueryData<EntityBase>(key);
          if (entity && entity.timestamp) {
            // If we have a pending timer and the timestamp is new, clear the timer
            if (
              pendingTimers.current[entityId] &&
              entity.timestamp !== lastConfirmedTimestamps.current[entityId]
            ) {
              clearTimeout(pendingTimers.current[entityId]);
              delete pendingTimers.current[entityId];
              lastConfirmedTimestamps.current[entityId] = entity.timestamp;
            }
          }
        }
      }
    });
    return () => unsubscribe();
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ entityId, command }: { entityId: string; command: ControlCommand }) =>
      controlEntity(entityId, command),

    onSuccess: (data: ControlEntityResponse, variables) => {
      // Invalidate the specific entity and related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(variables.entityId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });
      if (data.entity_type === 'light') {
        queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
      } else if (data.entity_type === 'lock') {
        queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
      }
    },

    onMutate: async ({ entityId, command }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.entities.detail(entityId) });
      const previousEntity = queryClient.getQueryData<EntityBase>(queryKeys.entities.detail(entityId));
      const previousLights = queryClient.getQueryData<Record<string, LightEntity>>(queryKeys.lights.list());
      // Optimistically update the entity detail
      if (previousEntity) {
        queryClient.setQueryData<EntityBase>(
          queryKeys.entities.detail(entityId),
          (old) => {
            if (!old) return old;
            if (old.entity_type === 'light') {
              const light = old as LightEntity;
              let newState = light.state;
              if (command.command === 'set' && command.state) {
                newState = command.state;
              } else if (command.command === 'toggle') {
                newState = light.state === 'on' ? 'off' : 'on';
              } else if (
                command.command === 'brightness_up' ||
                command.command === 'brightness_down'
              ) {
                newState = light.state === 'off' ? 'on' : light.state;
              }
              return {
                ...light,
                state: newState,
                ...(command.brightness !== undefined ? { brightness: command.brightness } : {}),
                ...((command.command === 'brightness_up' && command.brightness === undefined)
                  ? { brightness: typeof light.brightness === 'number' ? Math.min(light.brightness + 10, 100) : 10 }
                  : {}),
                ...((command.command === 'brightness_down' && command.brightness === undefined)
                  ? { brightness: typeof light.brightness === 'number' ? Math.max(light.brightness - 10, 0) : 0 }
                  : {}),
                timestamp: Date.now(),
              };
            }
            // For other entity types, just return old
            return old;
          }
        );
      }
      // Optimistically update the lights list cache
      if (previousLights) {
        queryClient.setQueryData<Record<string, LightEntity>>(
          queryKeys.lights.list(),
          (old) => {
            if (!old) return old;
            const light =
              old[entityId] ||
              (previousEntity && previousEntity.entity_type === 'light'
                ? (previousEntity as LightEntity)
                : undefined);
            if (!light) return old;
            let newState = light.state;
            let newBrightness = light.brightness;
            if (command.command === 'set' && command.state) {
              newState = command.state;
              if (command.brightness !== undefined) {
                newBrightness = command.brightness;
              }
            } else if (command.command === 'toggle') {
              newState = light.state === 'on' ? 'off' : 'on';
              // If toggling on, set brightness to last known or default (10)
              if (newState === 'on') {
                newBrightness = typeof light.brightness === 'number' ? light.brightness : 10;
              }
            } else if (command.command === 'brightness_up' && command.brightness === undefined) {
              // If light is off, turn it on and bump brightness
              newState = light.state === 'off' ? 'on' : light.state;
              newBrightness = typeof light.brightness === 'number' ? Math.min(light.brightness + 10, 100) : 10;
            } else if (command.command === 'brightness_down' && command.brightness === undefined) {
              // If light is off, turn it on and lower brightness
              newState = light.state === 'off' ? 'on' : light.state;
              newBrightness = typeof light.brightness === 'number' ? Math.max(light.brightness - 10, 0) : 0;
            } else if (command.brightness !== undefined) {
              newBrightness = command.brightness;
            }
            return {
              ...old,
              [entityId]: {
                ...light,
                state: newState,
                brightness: newBrightness,
                timestamp: Date.now(),
              },
            };
          }
        );
      } else if (previousEntity && previousEntity.entity_type === 'light') {
        // If lights list cache is missing, but we have the entity, create a new cache entry
        queryClient.setQueryData<Record<string, LightEntity>>(
          queryKeys.lights.list(),
          (old) => {
            const prev = previousEntity as LightEntity;
            let newState = prev.state;
            let newBrightness = prev.brightness;
            if (command.command === 'set' && command.state) {
              newState = command.state;
              if (command.brightness !== undefined) {
                newBrightness = command.brightness;
              }
            } else if (command.command === 'toggle') {
              newState = prev.state === 'on' ? 'off' : 'on';
              if (newState === 'on') {
                newBrightness = typeof prev.brightness === 'number' ? prev.brightness : 10;
              }
            } else if (command.command === 'brightness_up' && command.brightness === undefined) {
              // If light is off, turn it on and bump brightness
              newState = prev.state === 'off' ? 'on' : prev.state;
              newBrightness = typeof prev.brightness === 'number' ? Math.min(prev.brightness + 10, 100) : 10;
            } else if (command.command === 'brightness_down' && command.brightness === undefined) {
              // If light is off, turn it on and lower brightness
              newState = prev.state === 'off' ? 'on' : prev.state;
              newBrightness = typeof prev.brightness === 'number' ? Math.max(prev.brightness - 10, 0) : 0;
            } else if (command.brightness !== undefined) {
              newBrightness = command.brightness;
            }
            return {
              ...(old || {}),
              [entityId]: {
                ...prev,
                state: newState,
                brightness: newBrightness,
                timestamp: Date.now(),
              },
            };
          }
        );
      }
      // Start a timer to revert the optimistic update if no confirmation is received
      if (pendingTimers.current[entityId]) {
        clearTimeout(pendingTimers.current[entityId]);
      }
      pendingTimers.current[entityId] = setTimeout(() => {
        // Revert entity detail
        if (previousEntity) {
          // Always create a new object to ensure re-render
          queryClient.setQueryData<EntityBase>(
            queryKeys.entities.detail(entityId),
            { ...previousEntity }
          );
        }
        // Revert lights list
        if (previousLights) {
          // Always create a new object to ensure re-render
          queryClient.setQueryData<Record<string, LightEntity>>(
            queryKeys.lights.list(),
            { ...previousLights }
          );
        } else {
          // If there was no previous lights list, remove the entity from the list
          queryClient.setQueryData<Record<string, LightEntity>>(
            queryKeys.lights.list(),
            (old) => {
              if (!old) return old;
              // Remove the entity from the list without unused variable warning
              const rest = Object.fromEntries(
                Object.entries(old).filter(([key]) => key !== entityId)
              );
              return { ...rest };
            }
          );
        }
        // Show a toast notification
        toast("No confirmation from backend. State reverted.");
        delete pendingTimers.current[entityId];
      }, 2000);
    },

    onError: (_err, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(variables.entityId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
      if (pendingTimers.current[variables.entityId]) {
        clearTimeout(pendingTimers.current[variables.entityId]);
        delete pendingTimers.current[variables.entityId];
      }
    },
  });
}

/**
 * Hook for light control commands
 * Exposes only mutate and isPending for each action.
 */
export function useLightControl() {
  const controlEntity = useControlEntity();

  return {
    toggle: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'toggle' } }),
      isPending: controlEntity.isPending,
    },
    turnOn: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'set', state: 'on' } }),
      isPending: controlEntity.isPending,
    },
    turnOff: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'set', state: 'off' } }),
      isPending: controlEntity.isPending,
    },
    setBrightness: {
      mutate: ({ entityId, brightness }: { entityId: string; brightness: number }) =>
        controlEntity.mutate({ entityId, command: { command: 'set', state: 'on', brightness } }),
      isPending: controlEntity.isPending,
    },
    brightnessUp: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'brightness_up' } }),
      isPending: controlEntity.isPending,
    },
    brightnessDown: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'brightness_down' } }),
      isPending: controlEntity.isPending,
    },
  };
}

/**
 * Hook for lock control commands
 */
export function useLockControl() {
  const queryClient = useQueryClient();

  const invalidateLock = (entityId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(entityId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
    queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });
  };

  return {
    lock: useMutation({
      mutationFn: lockEntity,
      onSuccess: (_, entityId) => invalidateLock(entityId),
    }),

    unlock: useMutation({
      mutationFn: unlockEntity,
      onSuccess: (_, entityId) => invalidateLock(entityId),
    }),
  };
}

/**
 * Hook to get a light entity with type safety
 */
export function useLight(entityId: string) {
  const { data, ...rest } = useEntity(entityId);

  return {
    data: data as LightEntity | undefined,
    ...rest,
  };
}

/**
 * Hook to get a lock entity with type safety
 */
export function useLock(entityId: string) {
  const { data, ...rest } = useEntity(entityId);

  return {
    data: data as LockEntity | undefined,
    ...rest,
  };
}

/**
 * Hook to get a tank sensor entity with type safety
 */
export function useTankSensor(entityId: string) {
  const { data, ...rest } = useEntity(entityId);

  return {
    data: data as TankSensorEntity | undefined,
    ...rest,
  };
}

/**
 * Hook to get a temperature sensor entity with type safety
 */
export function useTemperatureSensor(entityId: string) {
  const { data, ...rest } = useEntity(entityId);

  return {
    data: data as TemperatureSensorEntity | undefined,
    ...rest,
  };
}
