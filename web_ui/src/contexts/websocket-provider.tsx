/**
 * WebSocket Provider Component
 *
 * Provides global WebSocket connections for real-time updates.
 * Manages entity updates, system status, and other real-time data streams.
 */

import { useWebSocketManager } from '@/hooks/useWebSocket';
import React, { useEffect, useState } from 'react';
import { WebSocketContext, type ConnectionMetrics, type WebSocketContextType } from './websocket-context';

interface WebSocketProviderProps {
  children: React.ReactNode;
  enableEntityUpdates?: boolean;
  enableSystemStatus?: boolean;
  enableCANScan?: boolean;
}

/**
 * Provides global WebSocket connections to the application
 */
export function WebSocketProvider({
  children,
  enableEntityUpdates = true,
  enableSystemStatus = true,
  enableCANScan = false
}: WebSocketProviderProps) {
  const webSocketManager = useWebSocketManager({
    enableEntityUpdates,
    enableSystemStatus,
    enableCANScan,
  });

  const [metrics, setMetrics] = useState<ConnectionMetrics>({
    messageCount: 0,
    reconnectAttempts: 0,
  });

  // Track connection metrics
  useEffect(() => {
    if (webSocketManager.isAnyConnected && !metrics.connectedAt) {
      setMetrics(prev => ({
        ...prev,
        connectedAt: new Date(),
      }));
    } else if (!webSocketManager.isAnyConnected) {
      setMetrics(prev => ({
        ...prev,
        connectedAt: undefined,
      }));
    }
  }, [webSocketManager.isAnyConnected, metrics.connectedAt]);

  // Update message count metrics
  useEffect(() => {
    const interval = setInterval(() => {
      if (webSocketManager.isAnyConnected) {
        setMetrics(prev => ({
          ...prev,
          lastMessage: new Date(),
          messageCount: prev.messageCount + 1,
        }));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [webSocketManager.isAnyConnected]);

  const contextValue: WebSocketContextType = {
    isConnected: webSocketManager.isAnyConnected,
    hasError: Boolean(webSocketManager.hasAnyError),
    connectAll: webSocketManager.connectAll,
    disconnectAll: webSocketManager.disconnectAll,
    metrics,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}
