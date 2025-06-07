/**
 * WebSocket Context Hook
 *
 * Custom hook for consuming WebSocket context.
 */

import { useContext } from 'react';
import { WebSocketContext, type WebSocketContextType } from './websocket-context';

/**
 * Hook to access WebSocket context
 * @throws Error if used outside WebSocketProvider
 */
export function useWebSocketContext(): WebSocketContextType {
  const context = useContext(WebSocketContext);

  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }

  return context;
}
