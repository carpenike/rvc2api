/**
 * Centralized exports for application contexts
 *
 * This file provides a single import point for all global contexts and providers.
 * Use this for cleaner imports throughout the application.
 */

// Theme Context
export { ThemeProvider, useTheme } from '../hooks/use-theme.tsx';

// WebSocket Context
export { useWebSocketContext } from './use-websocket-context';
export { WebSocketContext, type ConnectionMetrics, type WebSocketContextType } from './websocket-context';
export { WebSocketProvider } from './websocket-provider';

// Query Provider
export { QueryProvider } from './query-provider';
