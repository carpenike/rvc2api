/**
 * Entity Query Hooks
 *
 * Custom React Query hooks for entity management.
 * Provides type-safe, optimized data fetching for all entity types.
 */

import { queryKeys, STALE_TIMES } from '@/lib/query-client';
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

// Extended types for optimistic updates
type OptimisticEntityBase = EntityBase & { _optimistic?: boolean };
type OptimisticLightEntity = LightEntity & { _optimistic?: boolean };

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
          const entity = queryClient.getQueryData<OptimisticEntityBase>(key);
          if (entity && entity.timestamp) {
            // If we have a pending timer and the timestamp is new, clear the timer
            if (
              pendingTimers.current[entityId] &&
              entity.timestamp !== lastConfirmedTimestamps.current[entityId]
            ) {
              clearTimeout(pendingTimers.current[entityId]);
              pendingTimers.current[entityId] = undefined;
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
      void queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(variables.entityId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });
      if (data.entity_type === 'light') {
        void queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
      } else if (data.entity_type === 'lock') {
        void queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
      }
    },

    onMutate: async ({ entityId, command: _command }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.entities.detail(entityId) });
      const previousEntity = queryClient.getQueryData<OptimisticEntityBase>(queryKeys.entities.detail(entityId));
      const previousLights = queryClient.getQueryData<Record<string, OptimisticLightEntity>>(queryKeys.lights.list());

      // Simple optimistic update for visual feedback only - backend handles all business logic
      if (previousEntity) {
        queryClient.setQueryData<OptimisticEntityBase>(
          queryKeys.entities.detail(entityId),
          (old) => {
            if (!old) return old;
            // Simple visual feedback - mark as pending, backend determines final state
            return {
              ...old,
              _optimistic: true, // Visual indicator for pending state
              timestamp: Date.now(),
            };
          }
        );
      }
      // Simple optimistic update for lights list cache - visual feedback only
      if (previousLights && previousLights[entityId]) {
        queryClient.setQueryData<Record<string, OptimisticLightEntity>>(
          queryKeys.lights.list(),
          (old) => {
            if (!old || !old[entityId]) return old;
            return {
              ...old,
              [entityId]: {
                ...old[entityId],
                _optimistic: true, // Visual indicator for pending state
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
        // Revert simple optimistic updates - backend is source of truth
        if (previousEntity) {
          queryClient.setQueryData<OptimisticEntityBase>(
            queryKeys.entities.detail(entityId),
            { ...previousEntity }
          );
        }
        if (previousLights && previousLights[entityId]) {
          queryClient.setQueryData<Record<string, OptimisticLightEntity>>(
            queryKeys.lights.list(),
            { ...previousLights }
          );
        }
        // Show a toast notification
        toast("No confirmation from backend. State reverted.");
        pendingTimers.current[entityId] = undefined;
      }, 2000);
    },

    onError: (_err, variables) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(variables.entityId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
      if (pendingTimers.current[variables.entityId]) {
        clearTimeout(pendingTimers.current[variables.entityId]);
        pendingTimers.current[variables.entityId] = undefined;
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
        controlEntity.mutate({ entityId, command: { command: 'set', state: true } }),
      isPending: controlEntity.isPending,
    },
    turnOff: {
      mutate: ({ entityId }: { entityId: string }) =>
        controlEntity.mutate({ entityId, command: { command: 'set', state: false } }),
      isPending: controlEntity.isPending,
    },
    setBrightness: {
      mutate: ({ entityId, brightness }: { entityId: string; brightness: number }) =>
        controlEntity.mutate({ entityId, command: { command: 'set', state: true, brightness } }),
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
    void queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(entityId) });
    void queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
    void queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });
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
