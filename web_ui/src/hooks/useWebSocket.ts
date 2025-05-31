/**
 * WebSocket Query Hooks
 *
 * Custom React hooks for WebSocket connections with React Query integration.
 * Provides real-time data updates with automatic cache invalidation.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import {
  RVCWebSocketClient,
  createCANScanWebSocket,
  createEntityWebSocket,
  createSystemStatusWebSocket,
  isWebSocketSupported
} from '../api';
import type {
  CANMessage,
  EntityBase,
  SystemStatusMessage,
  WebSocketHandlers,
} from '../api/types';
import { queryKeys } from '../lib/query-client';

/**
 * Hook for entity updates via WebSocket
 */
export function useEntityWebSocket(options?: { autoConnect?: boolean }) {
  const queryClient = useQueryClient();
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const { autoConnect = true } = options || {};

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onEntityUpdate: (entity: EntityBase) => {
        // Update the specific entity in the cache
        queryClient.setQueryData(
          queryKeys.entities.detail(entity.entity_id),
          entity
        );

        // Invalidate entity lists to trigger re-render
        queryClient.invalidateQueries({ queryKey: queryKeys.entities.lists() });

        // Update type-specific lists
        if (entity.entity_type === 'light') {
          queryClient.invalidateQueries({ queryKey: queryKeys.lights.list() });
        } else if (entity.entity_type === 'lock') {
          queryClient.invalidateQueries({ queryKey: queryKeys.locks.list() });
        } else if (entity.entity_type === 'tank_sensor') {
          queryClient.invalidateQueries({ queryKey: queryKeys.tankSensors.list() });
        } else if (entity.entity_type === 'temperature_sensor') {
          queryClient.invalidateQueries({ queryKey: queryKeys.temperatureSensors.list() });
        }
      },

      onConnect: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to entity updates');
      },

      onDisconnect: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from entity updates');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected()) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: string) => {
        setError(error);
        console.error('[WebSocket] Entity updates error:', error);
      },
    };

    const wsClient = createEntityWebSocket(handlers);
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect, queryClient]);

  const connect = () => client?.connect();
  const disconnect = () => client?.disconnect();

  return {
    client,
    isConnected,
    error,
    connect,
    disconnect,
    isSupported: isWebSocketSupported(),
  };
}

/**
 * Hook for CAN message scanning via WebSocket
 */
export function useCANScanWebSocket(options?: {
  autoConnect?: boolean;
  onMessage?: (message: CANMessage) => void;
}) {
  const queryClient = useQueryClient();
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const { autoConnect = false, onMessage } = options || {};

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onCANMessage: (message: CANMessage) => {
        setMessageCount(prev => prev + 1);
        onMessage?.(message);

        // Periodically invalidate CAN statistics
        if (messageCount % 100 === 0) {
          queryClient.invalidateQueries({ queryKey: queryKeys.can.statistics() });
        }
      },

      onConnect: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to CAN scan');
      },

      onDisconnect: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from CAN scan');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected()) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: string) => {
        setError(error);
        console.error('[WebSocket] CAN scan error:', error);
      },
    };

    const wsClient = createCANScanWebSocket(handlers);
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect, queryClient, messageCount, onMessage]);

  const connect = () => client?.connect();
  const disconnect = () => client?.disconnect();
  const clearMessageCount = () => setMessageCount(0);

  return {
    client,
    isConnected,
    error,
    messageCount,
    connect,
    disconnect,
    clearMessageCount,
    isSupported: isWebSocketSupported(),
  };
}

/**
 * Hook for system status updates via WebSocket
 */
export function useSystemStatusWebSocket(options?: { autoConnect?: boolean }) {
  const queryClient = useQueryClient();
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const { autoConnect = true } = options || {};

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onSystemStatus: (status: SystemStatusMessage) => {
        // Update system queries based on status type
        if (status.type === 'health') {
          queryClient.invalidateQueries({ queryKey: queryKeys.system.health() });
        } else if (status.type === 'queue') {
          queryClient.invalidateQueries({ queryKey: queryKeys.system.queueStatus() });
        } else if (status.type === 'can') {
          queryClient.invalidateQueries({ queryKey: queryKeys.can.statistics() });
        }
      },

      onConnect: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to system status');
      },

      onDisconnect: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from system status');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected()) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: string) => {
        setError(error);
        console.error('[WebSocket] System status error:', error);
      },
    };

    const wsClient = createSystemStatusWebSocket(handlers);
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect, queryClient]);

  const connect = () => client?.connect();
  const disconnect = () => client?.disconnect();

  return {
    client,
    isConnected,
    error,
    connect,
    disconnect,
    isSupported: isWebSocketSupported(),
  };
}

/**
 * Hook for managing all WebSocket connections
 */
export function useWebSocketManager(options?: {
  enableEntityUpdates?: boolean;
  enableSystemStatus?: boolean;
  enableCANScan?: boolean;
}) {
  const {
    enableEntityUpdates = true,
    enableSystemStatus = true,
    enableCANScan = false,
  } = options || {};

  const entityWS = useEntityWebSocket({ autoConnect: enableEntityUpdates });
  const systemWS = useSystemStatusWebSocket({ autoConnect: enableSystemStatus });
  const canWS = useCANScanWebSocket({ autoConnect: enableCANScan });

  const connectAll = () => {
    if (enableEntityUpdates) entityWS.connect();
    if (enableSystemStatus) systemWS.connect();
    if (enableCANScan) canWS.connect();
  };

  const disconnectAll = () => {
    entityWS.disconnect();
    systemWS.disconnect();
    canWS.disconnect();
  };

  const isAnyConnected = entityWS.isConnected || systemWS.isConnected || canWS.isConnected;
  const hasAnyError = entityWS.error || systemWS.error || canWS.error;

  return {
    entity: entityWS,
    system: systemWS,
    can: canWS,
    connectAll,
    disconnectAll,
    isAnyConnected,
    hasAnyError,
    isSupported: isWebSocketSupported(),
  };
}
