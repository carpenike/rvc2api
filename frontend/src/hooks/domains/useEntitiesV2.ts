/**
 * Entities Domain Hooks
 *
 * React hooks for the entities domain API with optimistic updates,
 * bulk operations, and enhanced error handling.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import type {
  BulkControlRequestSchema,
  ControlCommandSchema,
  EntitiesQueryParams,
  EntityCollectionSchema,
  EntitySchema,
} from '../../api/types/domains';
import {
  bulkControlEntitiesV2,
  controlEntityV2,
  fetchEntitiesV2,
  fetchEntityV2,
  fetchSchemasV2,
} from '../../api/domains/entities';

//
// ===== QUERY KEYS =====
//

export const entitiesV2QueryKeys = {
  all: ['entities-v2'] as const,
  collections: () => [...entitiesV2QueryKeys.all, 'collections'] as const,
  collection: (params?: EntitiesQueryParams) =>
    [...entitiesV2QueryKeys.collections(), params] as const,
  entities: () => [...entitiesV2QueryKeys.all, 'entity'] as const,
  entity: (id: string) => [...entitiesV2QueryKeys.entities(), id] as const,
  schemas: () => [...entitiesV2QueryKeys.all, 'schemas'] as const,
};

//
// ===== COLLECTION HOOKS =====
//

/**
 * Hook to fetch entities collection with pagination and filtering
 *
 * @param params - Query parameters for filtering and pagination
 * @returns Query result with entities collection
 */
export function useEntitiesV2(
  params?: EntitiesQueryParams
): UseQueryResult<EntityCollectionSchema, Error> {
  return useQuery({
    queryKey: entitiesV2QueryKeys.collection(params),
    queryFn: () => fetchEntitiesV2(params),
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch a single entity by ID
 *
 * @param entityId - Entity ID to fetch
 * @param enabled - Whether the query should run
 * @returns Query result with entity data
 */
export function useEntityV2(
  entityId: string,
  enabled = true
): UseQueryResult<EntitySchema, Error> {
  return useQuery({
    queryKey: entitiesV2QueryKeys.entity(entityId),
    queryFn: () => fetchEntityV2(entityId),
    enabled: enabled && !!entityId,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook to fetch API schemas for validation
 *
 * @returns Query result with schema definitions
 */
export function useEntitiesSchemasV2(): UseQueryResult<Record<string, unknown>, Error> {
  return useQuery({
    queryKey: entitiesV2QueryKeys.schemas(),
    queryFn: fetchSchemasV2,
    staleTime: 300000, // Schemas change rarely, cache for 5 minutes
    refetchOnWindowFocus: false,
  });
}

//
// ===== MUTATION HOOKS =====
//

/**
 * Hook for controlling a single entity with optimistic updates
 *
 * @returns Mutation object for entity control
 */
export function useControlEntityV2() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      entityId,
      command,
    }: {
      entityId: string;
      command: ControlCommandSchema;
    }) => controlEntityV2(entityId, command),
    onMutate: async ({ entityId, command }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: entitiesV2QueryKeys.entity(entityId),
      });

      // Snapshot the previous value
      const previousEntity = queryClient.getQueryData<EntitySchema>(
        entitiesV2QueryKeys.entity(entityId)
      );

      // Optimistically update the entity state
      if (previousEntity) {
        const optimisticState = { ...previousEntity.state };

        // Apply optimistic updates based on command
        if (command.command === 'set') {
          if (command.state !== undefined && command.state !== null) {
            optimisticState.state = command.state ? 'on' : 'off';
          }
          if (command.brightness !== undefined && command.brightness !== null) {
            optimisticState.brightness = command.brightness;
          }
        } else if (command.command === 'toggle') {
          optimisticState.state = optimisticState.state === 'on' ? 'off' : 'on';
        } else if (command.command === 'brightness_up') {
          const currentBrightness = typeof optimisticState.brightness === 'number' ? optimisticState.brightness : 0;
          optimisticState.brightness = Math.min(100, currentBrightness + 10);
        } else if (command.command === 'brightness_down') {
          const currentBrightness = typeof optimisticState.brightness === 'number' ? optimisticState.brightness : 0;
          optimisticState.brightness = Math.max(0, currentBrightness - 10);
        }

        queryClient.setQueryData<EntitySchema>(
          entitiesV2QueryKeys.entity(entityId),
          {
            ...previousEntity,
            state: optimisticState,
            last_updated: new Date().toISOString(),
          }
        );
      }

      return { previousEntity };
    },
    onError: (error, { entityId }, context) => {
      // Rollback optimistic update on error
      if (context?.previousEntity) {
        queryClient.setQueryData(
          entitiesV2QueryKeys.entity(entityId),
          context.previousEntity
        );
      }
    },
    onSettled: (data, error, { entityId }) => {
      // Refetch entity data to ensure consistency
      void queryClient.invalidateQueries({
        queryKey: entitiesV2QueryKeys.entity(entityId),
      });

      // Also invalidate collections that might contain this entity
      void queryClient.invalidateQueries({
        queryKey: entitiesV2QueryKeys.collections(),
      });
    },
  });
}

/**
 * Hook for bulk entity control operations
 *
 * @returns Mutation object for bulk operations
 */
export function useBulkControlEntitiesV2() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BulkControlRequestSchema) => bulkControlEntitiesV2(request),
    onMutate: async (request) => {
      // Cancel outgoing refetches for affected entities
      const cancelPromises = request.entity_ids.map((entityId) =>
        queryClient.cancelQueries({
          queryKey: entitiesV2QueryKeys.entity(entityId),
        })
      );
      await Promise.all(cancelPromises);

      // Snapshot previous values
      const previousEntities = request.entity_ids.map((entityId) => ({
        entityId,
        data: queryClient.getQueryData<EntitySchema>(
          entitiesV2QueryKeys.entity(entityId)
        ),
      }));

      // Apply optimistic updates to all entities
      request.entity_ids.forEach((entityId) => {
        const previousEntity = queryClient.getQueryData<EntitySchema>(
          entitiesV2QueryKeys.entity(entityId)
        );

        if (previousEntity) {
          const optimisticState = { ...previousEntity.state };

          // Apply the same optimistic logic as single entity control
          if (request.command.command === 'set') {
            if (request.command.state !== undefined && request.command.state !== null) {
              optimisticState.state = request.command.state ? 'on' : 'off';
            }
            if (request.command.brightness !== undefined && request.command.brightness !== null) {
              optimisticState.brightness = request.command.brightness;
            }
          } else if (request.command.command === 'toggle') {
            optimisticState.state = optimisticState.state === 'on' ? 'off' : 'on';
          }

          queryClient.setQueryData<EntitySchema>(
            entitiesV2QueryKeys.entity(entityId),
            {
              ...previousEntity,
              state: optimisticState,
              last_updated: new Date().toISOString(),
            }
          );
        }
      });

      return { previousEntities };
    },
    onError: (error, request, context) => {
      // Rollback optimistic updates on error
      if (context?.previousEntities) {
        context.previousEntities.forEach(({ entityId, data }) => {
          if (data) {
            queryClient.setQueryData(
              entitiesV2QueryKeys.entity(entityId),
              data
            );
          }
        });
      }
    },
    onSuccess: (result, _request) => {
      // Handle partial success scenarios
      result.results.forEach((operationResult) => {
        if (operationResult.status !== 'success') {
          // Rollback optimistic update for failed entities
          void queryClient.invalidateQueries({
            queryKey: entitiesV2QueryKeys.entity(operationResult.entity_id),
          });
        }
      });
    },
    onSettled: (data, error, request) => {
      // Refetch all affected entities and collections
      request.entity_ids.forEach((entityId) => {
        void queryClient.invalidateQueries({
          queryKey: entitiesV2QueryKeys.entity(entityId),
        });
      });

      void queryClient.invalidateQueries({
        queryKey: entitiesV2QueryKeys.collections(),
      });
    },
  });
}

//
// ===== COMPOSITE HOOKS =====
//

/**
 * Hook for managing entity selection and bulk operations
 *
 * @returns Selection state and bulk operation utilities
 */
export function useEntitySelection() {
  const [selectedEntityIds, setSelectedEntityIds] = useState<string[]>([]);
  const bulkControlMutation = useBulkControlEntitiesV2();

  const selectEntity = useCallback((entityId: string) => {
    setSelectedEntityIds((prev) =>
      prev.includes(entityId) ? prev : [...prev, entityId]
    );
  }, []);

  const deselectEntity = useCallback((entityId: string) => {
    setSelectedEntityIds((prev) => prev.filter((id) => id !== entityId));
  }, []);

  const toggleEntitySelection = useCallback((entityId: string) => {
    setSelectedEntityIds((prev) =>
      prev.includes(entityId)
        ? prev.filter((id) => id !== entityId)
        : [...prev, entityId]
    );
  }, []);

  const selectAll = useCallback((entityIds: string[]) => {
    setSelectedEntityIds(entityIds);
  }, []);

  const deselectAll = useCallback(() => {
    setSelectedEntityIds([]);
  }, []);

  const executeBulkOperation = useCallback(
    (command: ControlCommandSchema, options?: { ignoreErrors?: boolean; timeout?: number }) => {
      if (selectedEntityIds.length === 0) {
        throw new Error('No entities selected for bulk operation');
      }

      return bulkControlMutation.mutate({
        entity_ids: selectedEntityIds,
        command,
        ignore_errors: options?.ignoreErrors ?? true,
        timeout_seconds: options?.timeout,
      });
    },
    [selectedEntityIds, bulkControlMutation]
  );

  return {
    selectedEntityIds,
    selectedCount: selectedEntityIds.length,
    selectEntity,
    deselectEntity,
    toggleEntitySelection,
    selectAll,
    deselectAll,
    executeBulkOperation,
    bulkOperationState: {
      isLoading: bulkControlMutation.isPending,
      error: bulkControlMutation.error,
      data: bulkControlMutation.data,
      reset: bulkControlMutation.reset,
    },
  };
}

//
// ===== UTILITY HOOKS =====
//

/**
 * Hook for managing pagination state
 *
 * @param initialPageSize - Initial page size (default: 50)
 * @returns Pagination state and utilities
 */
export function useEntityPagination(initialPageSize = 50) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const nextPage = useCallback(() => setPage((prev) => prev + 1), []);
  const prevPage = useCallback(() => setPage((prev) => Math.max(1, prev - 1)), []);
  const goToPage = useCallback((newPage: number) => setPage(Math.max(1, newPage)), []);
  const resetPagination = useCallback(() => setPage(1), []);

  return {
    page,
    pageSize,
    setPageSize,
    nextPage,
    prevPage,
    goToPage,
    resetPagination,
    paginationParams: { page, page_size: pageSize },
  };
}

/**
 * Hook for managing entity filtering
 *
 * @returns Filter state and utilities
 */
export function useEntityFilters() {
  const [filters, setFilters] = useState<Partial<EntitiesQueryParams>>({});

  const setFilter = useCallback(
    <K extends keyof EntitiesQueryParams>(key: K, value: EntitiesQueryParams[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const removeFilter = useCallback((key: keyof EntitiesQueryParams) => {
    setFilters((prev) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { [key]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  const clearFilters = useCallback(() => setFilters({}), []);

  const hasActiveFilters = Object.keys(filters).length > 0;

  return {
    filters,
    setFilter,
    removeFilter,
    clearFilters,
    hasActiveFilters,
  };
}
