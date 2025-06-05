/**
 * Enhanced WebSocket Hook with Performance Optimizations
 *
 * Adds advanced features like message batching, throttling, and
 * selective subscriptions for better performance.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { RVCWebSocketClient, type WebSocketHandlers } from '../api';
import type { EntityUpdateMessage } from '../api/types';
import { queryKeys } from '../lib/query-client';

interface UseOptimizedWebSocketOptions {
  autoConnect?: boolean;
  batchUpdates?: boolean;
  batchDelay?: number;
  throttleDelay?: number;
  maxBatchSize?: number;
  selectiveSubscription?: string[];
}

interface BatchedUpdate {
  entityId: string;
  data: EntityUpdateMessage['data'];
  timestamp: number;
}

export function useOptimizedEntityWebSocket(options: UseOptimizedWebSocketOptions = {}) {
  const {
    autoConnect = true,
    batchUpdates = true,
    batchDelay = 100,
    throttleDelay = 50,
    maxBatchSize = 10,
    selectiveSubscription,
  } = options;

  const queryClient = useQueryClient();
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const [lastMessageTime, setLastMessageTime] = useState<Date | null>(null);

  // Batching and throttling refs
  const batchRef = useRef<BatchedUpdate[]>([]);
  const batchTimerRef = useRef<NodeJS.Timeout | null>(null);
  const throttleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Performance metrics
  const [metrics, setMetrics] = useState({
    messagesPerSecond: 0,
    averageLatency: 0,
    totalMessages: 0,
    connectionStartTime: null as Date | null,
  });

  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Use ref to store the throttledUpdate function and break circular dependency
  const throttledUpdateRef = useRef<((updates: BatchedUpdate[]) => void) | null>(null);

  // Throttled update function
  const throttledUpdate = useCallback((updates: BatchedUpdate[]) => {
    if (throttleTimerRef.current) return;

    throttleTimerRef.current = setTimeout(() => {
      // Process batched updates
      const entityGroups = new Map<string, BatchedUpdate>();

      // Keep only the latest update for each entity
      updates.forEach(update => {
        const existing = entityGroups.get(update.entityId);
        if (!existing || update.timestamp > existing.timestamp) {
          entityGroups.set(update.entityId, update);
        }
      });

      // Apply updates to React Query cache
      entityGroups.forEach((update) => {
        // Skip if selective subscription is enabled and entity is not included
        if (selectiveSubscription && !selectiveSubscription.includes(update.entityId)) {
          return;
        }

        queryClient.setQueryData(
          queryKeys.entities.detail(update.entityId),
          update.data.entity_data
        );

        // Update type-specific lists based on entity type
        const entityType = update.data.entity_data.entity_type;
        if (entityType === 'light') {
          queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
        } else if (entityType === 'lock') {
          queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
        } else if (entityType === 'tank_sensor') {
          queryClient.invalidateQueries({ queryKey: queryKeys.tankSensors.list() });
        } else if (entityType === 'temperature_sensor') {
          queryClient.invalidateQueries({ queryKey: queryKeys.temperatureSensors.list() });
        }
      });

      // Invalidate entity lists once for all updates
      queryClient.invalidateQueries({ queryKey: queryKeys.entities.lists() });

      throttleTimerRef.current = null;
    }, throttleDelay);
  }, [queryClient, selectiveSubscription, throttleDelay]);

  // Update the ref whenever throttledUpdate changes
  throttledUpdateRef.current = throttledUpdate;

  // Flush batched updates
  const flushBatch = useCallback(() => {
    if (batchRef.current.length === 0) return;

    // Use ref to access throttledUpdate and break circular dependency
    if (throttledUpdateRef.current) {
      throttledUpdateRef.current([...batchRef.current]);
    }
    batchRef.current = [];

    if (batchTimerRef.current) {
      clearTimeout(batchTimerRef.current);
      batchTimerRef.current = null;
    }
  }, []); // No dependencies - using ref to break circular dependency

  // Store function refs to break circular dependencies
  const addToBatchRef = useRef<((entityId: string, data: EntityUpdateMessage['data']) => void) | null>(null);
  const updateMetricsRef = useRef<(() => void) | null>(null);
  const flushBatchRef = useRef<(() => void) | null>(null);
  const clientRef = useRef<RVCWebSocketClient | null>(null);

  // Add update to batch
  const addToBatch = useCallback((entityId: string, data: EntityUpdateMessage['data']) => {
    const update: BatchedUpdate = {
      entityId,
      data,
      timestamp: Date.now(),
    };

    batchRef.current.push(update);

    if (!batchUpdates || batchRef.current.length >= maxBatchSize) {
      // Flush immediately if batching is disabled or batch is full
      flushBatch();
    } else {
      // Schedule batch flush
      if (batchTimerRef.current) {
        clearTimeout(batchTimerRef.current);
      }
      batchTimerRef.current = setTimeout(flushBatch, batchDelay);
    }
  }, [batchUpdates, maxBatchSize, batchDelay, flushBatch]);

  // Update refs whenever functions change
  addToBatchRef.current = addToBatch;

  // Update performance metrics
  const updateMetrics = useCallback(() => {
    setMetrics(prev => {
      const now = Date.now();
      const timeSinceStart = prev.connectionStartTime
        ? (now - prev.connectionStartTime.getTime()) / 1000
        : 1;

      return {
        ...prev,
        messagesPerSecond: prev.totalMessages / timeSinceStart,
      };
    });
  }, []);

  // Update refs whenever functions change
  updateMetricsRef.current = updateMetrics;
  flushBatchRef.current = flushBatch;
  clientRef.current = client;

  useEffect(() => {
    if (!autoConnect) return;

    const handlers: WebSocketHandlers = {
      onEntityUpdate: (data: EntityUpdateMessage['data']) => {
        const now = new Date();
        setLastMessageTime(now);
        setMessageCount(prev => prev + 1);
        setMetrics(prev => ({
          ...prev,
          totalMessages: prev.totalMessages + 1
        }));

        // Use ref to avoid dependency issues
        if (addToBatchRef.current) {
          addToBatchRef.current(data.entity_id, data);
        }
      },

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        setMetrics(prev => ({
          ...prev,
          connectionStartTime: new Date(),
          totalMessages: 0,
        }));
        // Connected to entity updates WebSocket
      },

      onClose: () => {
        setIsConnected(false);
        // Disconnected from entity updates WebSocket

        // Clear metrics interval
        if (metricsIntervalRef.current) {
          clearInterval(metricsIntervalRef.current);
          metricsIntervalRef.current = null;
        }

        // Attempt to reconnect after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (client && !client.isConnected) {
            // Attempting to reconnect WebSocket
            client.connect();
          }
        }, 5000);
      },

      onError: (error: Event) => {
        setError(error.type || 'WebSocket error');
        console.error('[WebSocket] Entity updates error:', error);
      },
    };

    // Import the creation function dynamically to avoid circular dependencies
    import('../api').then(({ createEntityWebSocket }) => {
      const wsClient = createEntityWebSocket(handlers, {
        autoReconnect: true,
        reconnectDelay: 3000,
        maxReconnectAttempts: 0,
        heartbeatInterval: 30000,
      });

      setClient(wsClient);
      wsClient.connect();

      // Start metrics collection using ref
      metricsIntervalRef.current = setInterval(() => {
        if (updateMetricsRef.current) {
          updateMetricsRef.current();
        }
      }, 1000);
    });

    return () => {
      // Cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (batchTimerRef.current) {
        clearTimeout(batchTimerRef.current);
      }
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
      }
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current);
      }

      // Flush any remaining batched updates using ref
      if (flushBatchRef.current) {
        flushBatchRef.current();
      }

      // Use ref to disconnect client
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, [autoConnect]); // Removed dependencies to prevent infinite loop

  const connect = () => clientRef.current?.connect();
  const disconnect = () => clientRef.current?.disconnect();

  return {
    client,
    isConnected,
    error,
    messageCount,
    lastMessageTime,
    metrics,
    connect,
    disconnect,
    flushPendingUpdates: flushBatch,
  };
}
