/**
 * Entity Query Hooks
 *
 * Custom React Query hooks for entity management.
 * Provides type-safe, optimized data fetching for all entity types.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
  setLightBrightness,
  toggleLight,
  turnLightOff,
  turnLightOn,
  unlockEntity,
} from '../api';
import type {
  ControlCommand,
  ControlEntityResponse,
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
export function useEntities() {
  return useQuery({
    queryKey: queryKeys.entities.list(),
    queryFn: fetchEntities,
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
    queryFn: () => fetchEntityMetadata(entityId),
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

  return useMutation({
    mutationFn: ({ entityId, command }: { entityId: string; command: ControlCommand }) =>
      controlEntity(entityId, command),

    onSuccess: (data: ControlEntityResponse, variables) => {
      // Invalidate the specific entity and related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(variables.entityId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });

      // Also invalidate type-specific queries if applicable
      if (data.entity_type === 'light') {
        queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
      } else if (data.entity_type === 'lock') {
        queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
      }
    },

    // Optimistically update the entity state
    onMutate: async ({ entityId, command }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.entities.detail(entityId) });

      // Snapshot the previous value
      const previousEntity = queryClient.getQueryData<EntityBase>(
        queryKeys.entities.detail(entityId)
      );

      // Optimistically update the entity
      if (previousEntity) {
        queryClient.setQueryData<EntityBase>(
          queryKeys.entities.detail(entityId),
          (old) => {
            if (!old) return old;

            // Update the entity based on the command
            const updated = { ...old };

            // Handle different command types
            if (command.command_type === 'set_state' && command.parameters?.state !== undefined) {
              updated.current_state = command.parameters.state;
            }

            if (command.command_type === 'set_brightness' && command.parameters?.brightness !== undefined) {
              (updated as LightEntity).brightness = command.parameters.brightness;
            }

            return updated;
          }
        );
      }

      return { previousEntity };
    },

    // Revert on error
    onError: (err, variables, context) => {
      if (context?.previousEntity) {
        queryClient.setQueryData(
          queryKeys.entities.detail(variables.entityId),
          context.previousEntity
        );
      }
    },
  });
}

/**
 * Hook for light control commands
 */
export function useLightControl() {
  const queryClient = useQueryClient();

  const invalidateLight = (entityId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.entities.detail(entityId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
    queryClient.invalidateQueries({ queryKey: queryKeys.entities.list() });
  };

  return {
    toggle: useMutation({
      mutationFn: toggleLight,
      onSuccess: (_, entityId) => invalidateLight(entityId),
    }),

    turnOn: useMutation({
      mutationFn: turnLightOn,
      onSuccess: (_, entityId) => invalidateLight(entityId),
    }),

    turnOff: useMutation({
      mutationFn: turnLightOff,
      onSuccess: (_, entityId) => invalidateLight(entityId),
    }),

    setBrightness: useMutation({
      mutationFn: ({ entityId, brightness }: { entityId: string; brightness: number }) =>
        setLightBrightness(entityId, brightness),
      onSuccess: (_, { entityId }) => invalidateLight(entityId),
    }),
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
