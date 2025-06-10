/**
 * WebSocket Query Hooks
 *
 * Custom React hooks for WebSocket connections with React Query integration.
 * Provides real-time data updates with automatic cache invalidation.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import type {
    RVCWebSocketClient} from '../api';
import {
    createCANScanWebSocket,
    createEntityWebSocket,
    createLogWebSocket,
    createSystemStatusWebSocket,
    isWebSocketSupported
} from '../api';
import type {
    CANMessage,
    EntityUpdateMessage,
    WebSocketHandlers,
} from '../api/types';
import { queryKeys } from '@/lib/query-client';

/**
 * Hook for entity updates via WebSocket
 */
export function useEntityWebSocket(options?: { autoConnect?: boolean }) {
  const queryClient = useQueryClient();
  const queryClientRef = useRef(queryClient);
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const clientRef = useRef<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { autoConnect = true } = options || {};

  // Update queryClient ref when it changes
  queryClientRef.current = queryClient;

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onEntityUpdate: (data: EntityUpdateMessage['data']) => {
        // Update the specific entity in the cache using ref
        queryClientRef.current.setQueryData(
          queryKeys.entities.detail(data.entity_id),
          data.entity_data
        );

        // Invalidate entity lists to trigger re-render
        void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.entities.lists() });

        // Update type-specific lists
        if (data.entity_data.entity_type === 'light') {
          void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.lights.list() });
        } else if (data.entity_data.entity_type === 'lock') {
          void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.locks.list() });
        } else if (data.entity_data.entity_type === 'tank_sensor') {
          void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.tankSensors.list() });
        } else if (data.entity_data.entity_type === 'temperature_sensor') {
          void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.temperatureSensors.list() });
        }
      },

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to entity updates');
      },

      onClose: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from entity updates');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: Event) => {
        setError(error.type || 'WebSocket error');
        console.error('[WebSocket] Entity updates error:', error);
      },
    };

    const wsClient = createEntityWebSocket(handlers);
    clientRef.current = wsClient;
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect]);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

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
  const queryClientRef = useRef(queryClient);
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const clientRef = useRef<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { autoConnect = false } = options || {};
  const onMessageRef = useRef(options?.onMessage);

  // Update refs when they change
  queryClientRef.current = queryClient;
  onMessageRef.current = options?.onMessage;

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onCANMessage: (message: CANMessage) => {
        setMessageCount(prev => prev + 1);
        onMessageRef.current?.(message);

        // Periodically invalidate CAN statistics
        if (messageCount % 100 === 0) {
          void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.can.statistics() });
        }
      },

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to CAN scan');
      },

      onClose: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from CAN scan');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: Event) => {
        setError(error.type || 'WebSocket error');
        console.error('[WebSocket] CAN scan error:', error);
      },
    };

    const wsClient = createCANScanWebSocket(handlers);
    clientRef.current = wsClient;
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect, messageCount]);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);
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
  const queryClientRef = useRef(queryClient);
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const clientRef = useRef<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { autoConnect = true } = options || {};

  // Update queryClient ref when it changes
  queryClientRef.current = queryClient;

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onSystemStatus: () => {
        // Update system queries - we just invalidate all relevant queries
        // since we only get the data portion, not the message type
        void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.system.health() });
        void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.system.queueStatus() });
        void queryClientRef.current.invalidateQueries({ queryKey: queryKeys.can.statistics() });
      },

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to system status');
      },

      onClose: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from system status');

        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: Event) => {
        setError(error.type || 'WebSocket error');
        console.error('[WebSocket] System status error:', error);
      },
    };

    const wsClient = createSystemStatusWebSocket(handlers);
    clientRef.current = wsClient;
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect]);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

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
 * Hook for log streaming via WebSocket
 */
export function useLogWebSocket(options?: {
  autoConnect?: boolean;
  onLog?: (log: unknown) => void;
}) {
  const [client, setClient] = useState<RVCWebSocketClient | null>(null);
  const clientRef = useRef<RVCWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const onLogRef = useRef(options?.onLog);

  const { autoConnect = false } = options || {};

  // Update onLog ref when it changes
  onLogRef.current = options?.onLog;

  useEffect(() => {
    if (!autoConnect || !isWebSocketSupported()) {
      return;
    }

    const handlers: WebSocketHandlers = {
      onMessage: (message) => {
        // Accept log messages with or without a type field, as long as they have standard log fields
        if (
          message && typeof message === 'object' &&
          'timestamp' in message && 'level' in message && 'message' in message
        ) {
          onLogRef.current?.(message);
        } else if (typeof message === 'string') {
          // Try to parse as JSON, fallback to raw string
          try {
            const parsed = JSON.parse(message);
            if (
              parsed && typeof parsed === 'object' &&
              'timestamp' in parsed && 'level' in parsed && 'message' in parsed
            ) {
              onLogRef.current?.(parsed);
              return;
            }
          } catch {
            // Not JSON, pass as raw string
          }
          onLogRef.current?.(message);
        } else {
          // Fallback: pass any message
          onLogRef.current?.(message);
        }
      },

      onOpen: () => {
        setIsConnected(true);
        setError(null);
        console.log('[WebSocket] Connected to logs');
      },

      onClose: () => {
        setIsConnected(false);
        console.log('[WebSocket] Disconnected from logs');
        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsClient && !wsClient.isConnected) {
            console.log('[WebSocket] Attempting to reconnect...');
            wsClient.connect();
          }
        }, 5000);
      },

      onError: (error: Event) => {
        setError(error.type || 'WebSocket error');
        console.error('[WebSocket] Log error:', error);
      },
    };

    const wsClient = createLogWebSocket(handlers);
    clientRef.current = wsClient;
    setClient(wsClient);
    wsClient.connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsClient.disconnect();
    };
  }, [autoConnect]);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

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
