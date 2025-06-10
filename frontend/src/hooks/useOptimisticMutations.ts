/**
 * Optimistic Mutations Hook
 *
 * Provides optimistic UI updates for better user experience.
 * Updates the UI immediately while the API call is in progress.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { controlEntity, toggleLight, setLightBrightness, brightnessUp, brightnessDown } from '@/api/endpoints'
import type { ControlCommand, ControlEntityResponse, Entity, LightEntity } from '@/api/types'

/**
 * Hook for optimistic entity control with immediate UI updates
 */
export function useOptimisticEntityControl() {
  const queryClient = useQueryClient()

  return useMutation<
    ControlEntityResponse,
    Error,
    { entityId: string; command: ControlCommand },
    { previousEntities?: unknown; previousDashboard?: unknown }
  >({
    mutationFn: async ({ entityId, command }) => {
      return await controlEntity(entityId, command)
    },

    onMutate: async ({ entityId, command }) => {
      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: ['entities'] })
      await queryClient.cancelQueries({ queryKey: ['dashboard', 'summary'] })

      // Snapshot the previous value
      const previousEntities = queryClient.getQueryData(['entities'])
      const previousDashboard = queryClient.getQueryData(['dashboard', 'summary'])

      // Optimistically update the entity state
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[entityId]) return old

        const entity = { ...old[entityId] }

        // Update entity based on command
        if (command.command === 'toggle') {
          entity.state = entity.state === 'on' ? 'off' : 'on'
        } else if (command.command === 'on' || command.command === 'set') {
          if (command.parameters?.state !== undefined) {
            entity.state = command.parameters.state ? 'on' : 'off'
          } else {
            entity.state = 'on'
          }

          // Update brightness for lights
          if (command.parameters?.brightness !== undefined && 'brightness' in entity) {
            (entity as LightEntity).brightness = command.parameters.brightness as number
          }
        } else if (command.command === 'off') {
          entity.state = 'off'
        }

        // Update timestamp
        entity.timestamp = Date.now()

        return {
          ...old,
          [entityId]: entity
        }
      })

      // Return context object with the previous state
      return { previousEntities, previousDashboard }
    },

    onError: (_err, variables, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      if (context?.previousDashboard) {
        queryClient.setQueryData(['dashboard', 'summary'], context.previousDashboard)
      }

      toast.error('Control Failed', {
        description: `Failed to control ${variables.entityId}: ${_err instanceof Error ? _err.message : 'Unknown error'}`,
      })
    },

    onSuccess: (data, variables) => {
      // Update with actual server response
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[variables.entityId]) return old

        return {
          ...old,
          [variables.entityId]: {
            ...old[variables.entityId],
            timestamp: Date.now()
          }
        }
      })

      toast.success('Control Successful', {
        description: data.message,
      })
    },

    onSettled: () => {
      // Always refetch after error or success to ensure we have the latest data
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
    },
  })
}

/**
 * Hook for optimistic light control with immediate brightness updates
 */
export function useOptimisticLightControl() {
  const queryClient = useQueryClient()

  const toggle = useMutation<
    ControlEntityResponse,
    Error,
    { entityId: string },
    { previousEntities?: unknown }
  >({
    mutationFn: async ({ entityId }) => {
      return await toggleLight(entityId)
    },

    onMutate: async ({ entityId }) => {
      await queryClient.cancelQueries({ queryKey: ['entities'] })

      const previousEntities = queryClient.getQueryData(['entities'])

      // Optimistically toggle the light
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[entityId]) return old

        const entity = { ...old[entityId] }
        entity.state = entity.state === 'on' ? 'off' : 'on'
        entity.timestamp = Date.now()

        return {
          ...old,
          [entityId]: entity
        }
      })

      return { previousEntities }
    },

    onError: (_err, variables, context) => {
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      toast.error('Toggle Failed', {
        description: `Failed to toggle ${variables.entityId}`,
      })
    },

    onSuccess: (data) => {
      toast.success('Light Toggled', {
        description: data.message,
      })
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
    },
  })

  const setBrightness = useMutation<
    ControlEntityResponse,
    Error,
    { entityId: string; brightness: number },
    { previousEntities?: unknown }
  >({
    mutationFn: async ({ entityId, brightness }) => {
      return await setLightBrightness(entityId, brightness)
    },

    onMutate: async ({ entityId, brightness }) => {
      await queryClient.cancelQueries({ queryKey: ['entities'] })

      const previousEntities = queryClient.getQueryData(['entities'])

      // Optimistically update brightness
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[entityId]) return old

        const entity = { ...old[entityId] } as LightEntity
        entity.brightness = brightness
        entity.state = brightness > 0 ? 'on' : 'off'
        entity.timestamp = Date.now()

        return {
          ...old,
          [entityId]: entity
        }
      })

      return { previousEntities }
    },

    onError: (_err, variables, context) => {
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      toast.error('Brightness Update Failed', {
        description: `Failed to set brightness for ${variables.entityId}`,
      })
    },

    onSuccess: (data) => {
      toast.success('Brightness Updated', {
        description: data.message,
      })
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
    },
  })

  const brightnessUpMutation = useMutation<
    ControlEntityResponse,
    Error,
    { entityId: string },
    { previousEntities?: unknown }
  >({
    mutationFn: async ({ entityId }) => {
      return await brightnessUp(entityId)
    },

    onMutate: async ({ entityId }) => {
      await queryClient.cancelQueries({ queryKey: ['entities'] })

      const previousEntities = queryClient.getQueryData(['entities'])

      // Optimistically increase brightness by 10%
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[entityId]) return old

        const entity = { ...old[entityId] } as LightEntity
        const currentBrightness = entity.brightness || 0
        entity.brightness = Math.min(100, currentBrightness + 10)
        entity.state = entity.brightness > 0 ? 'on' : 'off'
        entity.timestamp = Date.now()

        return {
          ...old,
          [entityId]: entity
        }
      })

      return { previousEntities }
    },

    onError: (_err, variables, context) => {
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      toast.error('Brightness Up Failed', {
        description: `Failed to increase brightness for ${variables.entityId}`,
      })
    },

    onSuccess: (data) => {
      toast.success('Brightness Increased', {
        description: data.message,
      })
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
    },
  })

  const brightnessDownMutation = useMutation<
    ControlEntityResponse,
    Error,
    { entityId: string },
    { previousEntities?: unknown }
  >({
    mutationFn: async ({ entityId }) => {
      return await brightnessDown(entityId)
    },

    onMutate: async ({ entityId }) => {
      await queryClient.cancelQueries({ queryKey: ['entities'] })

      const previousEntities = queryClient.getQueryData(['entities'])

      // Optimistically decrease brightness by 10%
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old || !old[entityId]) return old

        const entity = { ...old[entityId] } as LightEntity
        const currentBrightness = entity.brightness || 0
        entity.brightness = Math.max(0, currentBrightness - 10)
        entity.state = entity.brightness > 0 ? 'on' : 'off'
        entity.timestamp = Date.now()

        return {
          ...old,
          [entityId]: entity
        }
      })

      return { previousEntities }
    },

    onError: (_err, variables, context) => {
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      toast.error('Brightness Down Failed', {
        description: `Failed to decrease brightness for ${variables.entityId}`,
      })
    },

    onSuccess: (data) => {
      toast.success('Brightness Decreased', {
        description: data.message,
      })
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
    },
  })

  return { toggle, setBrightness, brightnessUp: brightnessUpMutation, brightnessDown: brightnessDownMutation }
}

/**
 * Hook for optimistic bulk operations
 */
export function useOptimisticBulkControl() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: { entity_ids: string[]; command: string; parameters: Record<string, unknown>; ignore_errors?: boolean }) => {
      const { bulkControlEntities } = await import('@/api/endpoints')
      return await bulkControlEntities({
        entity_ids: request.entity_ids,
        command: request.command,
        parameters: request.parameters,
        ignore_errors: request.ignore_errors ?? true
      })
    },

    onMutate: async ({ entity_ids, command }) => {
      await queryClient.cancelQueries({ queryKey: ['entities'] })

      const previousEntities = queryClient.getQueryData(['entities'])

      // Optimistically update all selected entities
      queryClient.setQueryData(['entities'], (old: Record<string, Entity> | undefined) => {
        if (!old) return old

        const updated = { ...old }

        entity_ids.forEach(entityId => {
          if (updated[entityId]) {
            const entity = { ...updated[entityId] }

            // Apply optimistic updates based on command
            if (command === 'toggle') {
              entity.state = entity.state === 'on' ? 'off' : 'on'
            } else if (command === 'on') {
              entity.state = 'on'
            } else if (command === 'off') {
              entity.state = 'off'
            }

            // Update timestamp
            entity.timestamp = Date.now()

            updated[entityId] = entity
          }
        })

        return updated
      })

      return { previousEntities }
    },

    onError: (err, _variables, context) => {
      if (context?.previousEntities) {
        queryClient.setQueryData(['entities'], context.previousEntities)
      }
      toast.error('Bulk Operation Failed', {
        description: err.message,
      })
    },

    onSuccess: (data) => {
      toast.success('Bulk Operation Complete', {
        description: `${data.successful} successful, ${data.failed} failed`,
      })
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['entities'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] })
    },
  })
}

/**
 * Generic optimistic update helper for any mutation
 */
export function useOptimisticMutation<TData, TError, TVariables>({
  mutationFn,
  onOptimisticUpdate,
  queryKeys = [],
  successMessage,
  errorMessage
}: {
  mutationFn: (variables: TVariables) => Promise<TData>
  onOptimisticUpdate: (variables: TVariables, queryClient: ReturnType<typeof useQueryClient>) => unknown
  queryKeys?: string[][]
  successMessage?: string | ((data: TData, variables: TVariables) => string)
  errorMessage?: string | ((error: TError, variables: TVariables) => string)
}) {
  const queryClient = useQueryClient()

  return useMutation<TData, TError, TVariables, { previousStates?: Record<string, unknown>; rollback?: () => void }>({
    mutationFn,

    onMutate: async (variables) => {
      // Cancel any outgoing refetches
      await Promise.all(
        queryKeys.map(key => queryClient.cancelQueries({ queryKey: key }))
      )

      // Save previous states
      const previousStates = queryKeys.reduce((acc, key) => {
        acc[key.join('.')] = queryClient.getQueryData(key)
        return acc
      }, {} as Record<string, unknown>)

      // Apply optimistic update
      const rollback = onOptimisticUpdate(variables, queryClient) as (() => void) | undefined

      return { previousStates, rollback }
    },

    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousStates) {
        queryKeys.forEach(key => {
          const previousValue = context.previousStates?.[key.join('.')]
          if (previousValue !== undefined) {
            queryClient.setQueryData(key, previousValue)
          }
        })
      }

      if (context?.rollback) {
        context.rollback()
      }

      const message = typeof errorMessage === 'function'
        ? errorMessage(error, variables)
        : errorMessage || 'Operation failed'

      toast.error('Error', { description: message })
    },

    onSuccess: (data, variables) => {
      const message = typeof successMessage === 'function'
        ? successMessage(data, variables)
        : successMessage || 'Operation completed successfully'

      if (message) {
        toast.success('Success', { description: message })
      }
    },

    onSettled: () => {
      // Always refetch to ensure consistency
      queryKeys.forEach(key => {
        void queryClient.invalidateQueries({ queryKey: key })
      })
    },
  })
}
