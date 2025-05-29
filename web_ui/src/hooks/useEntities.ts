import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import toast from "react-hot-toast";
import { getApiBaseUrl } from "../utils/env";
import type { EntityControlCommand } from "../utils/validation";

// API configuration
const API_BASE = getApiBaseUrl();

// Types based on the backend API schema
export interface Entity {
  entity_id: string;
  state: string;
  device_type: string;
  suggested_area: string;
  friendly_name: string;
  capabilities: string[];
  groups: string[];
  brightness?: number;
  last_updated: string;
  raw?: Record<string, unknown>;
}

export interface EntitiesResponse {
  [entityId: string]: Entity;
}

export interface EntityControlResponse {
  status: string;
  entity_id: string;
  command: string;
  state: string;
  brightness: number;
  action: string;
}

export interface EntityHistoryEntry {
  entity_id: string;
  timestamp: number;
  state: string;
  brightness?: number;
  raw?: Record<string, unknown>;
}

// API Functions
export const fetchEntities = async (params?: {
  device_type?: string;
  area?: string;
}): Promise<EntitiesResponse> => {
  const searchParams = new URLSearchParams();
  if (params?.device_type) searchParams.append("device_type", params.device_type);
  if (params?.area) searchParams.append("area", params.area);

  const url = `${API_BASE}/api/entities${searchParams.toString() ? `?${searchParams}` : ""}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch entities: ${response.statusText}`);
  }

  return response.json();
};

export const fetchEntity = async (entityId: string): Promise<Entity> => {
  const response = await fetch(`${API_BASE}/api/entities/${entityId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Entity '${entityId}' not found`);
    }
    throw new Error(`Failed to fetch entity: ${response.statusText}`);
  }

  return response.json();
};

export const controlEntity = async (
  entityId: string,
  command: EntityControlCommand
): Promise<EntityControlResponse> => {
  const response = await fetch(`${API_BASE}/api/entities/${entityId}/control`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(command)
  });

  if (!response.ok) {
    throw new Error(`Failed to control entity: ${response.statusText}`);
  }

  return response.json();
};

export const fetchEntityHistory = async (
  entityId: string,
  params?: { since?: number; limit?: number }
): Promise<EntityHistoryEntry[]> => {
  const searchParams = new URLSearchParams();
  if (params?.since) searchParams.append("since", params.since.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());

  const url = `${API_BASE}/api/entities/${entityId}/history${searchParams.toString() ? `?${searchParams}` : ""}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch entity history: ${response.statusText}`);
  }

  return response.json();
};

// React Query Hooks

/**
 * Hook to fetch all entities with optional filtering
 */
export const useEntities = (filters?: { device_type?: string; area?: string }) => {
  return useQuery({
    queryKey: ["entities", filters],
    queryFn: () => fetchEntities(filters),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000 // Refetch every minute
  });
};

/**
 * Hook to fetch a specific entity
 */
export const useEntity = (entityId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ["entity", entityId],
    queryFn: () => fetchEntity(entityId),
    enabled: enabled && !!entityId,
    staleTime: 30000
  });
};

/**
 * Hook to fetch entity history
 */
export const useEntityHistory = (
  entityId: string,
  params?: { since?: number; limit?: number },
  enabled: boolean = true
) => {
  return useQuery({
    queryKey: ["entityHistory", entityId, params],
    queryFn: () => fetchEntityHistory(entityId, params),
    enabled: enabled && !!entityId,
    staleTime: 60000 // History data is less frequently updated
  });
};

/**
 * Hook for entity control with optimistic updates
 */
export const useEntityControl = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entityId, command }: { entityId: string; command: EntityControlCommand }) =>
      controlEntity(entityId, command),

    onMutate: async ({ entityId, command }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["entities"] });
      await queryClient.cancelQueries({ queryKey: ["entity", entityId] });

      // Snapshot the previous values
      const previousEntities = queryClient.getQueryData<EntitiesResponse>(["entities"]);
      const previousEntity = queryClient.getQueryData<Entity>(["entity", entityId]);

      // Optimistically update entity state
      if (previousEntities && previousEntities[entityId]) {
        const optimisticUpdate = getOptimisticUpdate(previousEntities[entityId], command);

        // Update entities list
        queryClient.setQueryData<EntitiesResponse>(["entities"], (old) => {
          if (!old) return old;
          return {
            ...old,
            [entityId]: optimisticUpdate
          };
        });

        // Update individual entity
        queryClient.setQueryData<Entity>(["entity", entityId], optimisticUpdate);
      }

      return { previousEntities, previousEntity };
    },

    onError: (error, { entityId }, context) => {
      // Revert optimistic updates on error
      if (context?.previousEntities) {
        queryClient.setQueryData(["entities"], context.previousEntities);
      }
      if (context?.previousEntity) {
        queryClient.setQueryData(["entity", entityId], context.previousEntity);
      }

      toast.error(`Failed to control entity: ${error.message}`);
    },

    onSuccess: (data, { entityId }) => {
      // Update with server response
      queryClient.setQueryData<EntitiesResponse>(["entities"], (old) => {
        if (!old) return old;
        return {
          ...old,
          [entityId]: {
            ...old[entityId],
            state: data.state,
            brightness: data.brightness,
            last_updated: new Date().toISOString()
          }
        };
      });

      queryClient.setQueryData<Entity>(["entity", entityId], (old) => {
        if (!old) return old;
        return {
          ...old,
          state: data.state,
          brightness: data.brightness,
          last_updated: new Date().toISOString()
        };
      });

      toast.success(data.action || "Entity control successful");
    },

    onSettled: (_data, _error, { entityId }) => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ["entities"] });
      queryClient.invalidateQueries({ queryKey: ["entity", entityId] });
    }
  });
};

/**
 * Helper function to create optimistic updates
 */
function getOptimisticUpdate(entity: Entity, command: EntityControlCommand): Entity {
  const now = new Date().toISOString();

  // Handle different command types
  switch (command.command) {
    case "set":
      return {
        ...entity,
        state: command.state ? String(command.state) : entity.state,
        brightness: command.brightness ?? entity.brightness,
        last_updated: now
      };

    case "toggle":
      return {
        ...entity,
        state: entity.state === "on" ? "off" : "on",
        brightness: entity.state === "on" ? 0 : (entity.brightness || 100),
        last_updated: now
      };

    case "brightness_up":
      return {
        ...entity,
        brightness: Math.min((entity.brightness || 0) + 10, 100),
        state: "on",
        last_updated: now
      };

    case "brightness_down": {
      const newBrightness = Math.max((entity.brightness || 0) - 10, 0);
      return {
        ...entity,
        brightness: newBrightness,
        state: newBrightness > 0 ? "on" : "off",
        last_updated: now
      };
    }

    default:
      return {
        ...entity,
        last_updated: now
      };
  }
}

/**
 * Convenience hook for lights specifically
 */
export const useLights = (area?: string) => {
  return useEntities({ device_type: "light", area });
};

/**
 * Convenience hook for light control
 */
export const useLightControl = () => {
  const entityControl = useEntityControl();

  const turnOn = useCallback((entityId: string, brightness?: number) => {
    return entityControl.mutate({
      entityId,
      command: { command: "set", state: "on", brightness }
    });
  }, [entityControl]);

  const turnOff = useCallback((entityId: string) => {
    return entityControl.mutate({
      entityId,
      command: { command: "set", state: "off" }
    });
  }, [entityControl]);

  const toggle = useCallback((entityId: string) => {
    return entityControl.mutate({
      entityId,
      command: { command: "toggle" }
    });
  }, [entityControl]);

  const setBrightness = useCallback((entityId: string, brightness: number) => {
    return entityControl.mutate({
      entityId,
      command: { command: "set", state: "on", brightness }
    });
  }, [entityControl]);

  const brightnessUp = useCallback((entityId: string) => {
    return entityControl.mutate({
      entityId,
      command: { command: "brightness_up" }
    });
  }, [entityControl]);

  const brightnessDown = useCallback((entityId: string) => {
    return entityControl.mutate({
      entityId,
      command: { command: "brightness_down" }
    });
  }, [entityControl]);

  return useMemo(() => ({
    ...entityControl,
    turnOn,
    turnOff,
    toggle,
    setBrightness,
    brightnessUp,
    brightnessDown
  }), [entityControl, turnOn, turnOff, toggle, setBrightness, brightnessUp, brightnessDown]);
};
