/**
 * WebSocket Context
 *
 * React context for global WebSocket state management.
 */

import { createContext } from 'react';

export interface ConnectionMetrics {
  messageCount: number;
  reconnectAttempts: number;
  connectedAt?: Date;
  lastMessage?: Date;
  messagesPerSecond?: number;
}

export interface WebSocketContextType {
  isConnected: boolean;
  hasError: boolean;
  connectAll: () => void;
  disconnectAll: () => void;
  metrics: ConnectionMetrics;
}

export const WebSocketContext = createContext<WebSocketContextType | null>(null);
