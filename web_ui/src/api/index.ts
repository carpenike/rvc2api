/**
 * API Module Index
 *
 * Central export point for all API-related functionality.
 * Provides clean imports for components and other modules.
 */

// Export all types
export type * from './types';

// Export client utilities
export {
  API_BASE, APIClientError, apiDelete, apiGet,
  apiPost,
  apiPut, apiRequest, buildQueryString, env, handleApiResponse, logApiRequest,
  logApiResponse, WS_BASE
} from './client';

// Export all endpoint functions
export {
  controlEntity,
  // CAN bus endpoints
  fetchCANInterfaces,
  fetchCANStatistics,
  // Entity endpoints
  fetchEntities,
  fetchEntity, fetchEntityHistory, fetchEntityMetadata, fetchFeatureStatus,
  // Configuration endpoints
  fetchHealthStatus,
  // Convenience functions
  fetchLights,
  fetchLocks, fetchQueueStatus, fetchTankSensors, fetchTemperatureSensors, fetchUnknownPGNs, fetchUnmappedEntries,
  // Lock control convenience functions
  lockEntity, sendCANMessage, setLightBrightness, toggleLight, turnLightOff,
  // Light control convenience functions
  turnLightOn, unlockEntity
} from './endpoints';

// Export WebSocket functionality
export {
  createCANScanWebSocket, createEntityWebSocket, createSystemStatusWebSocket, getWebSocketStateString, isWebSocketSupported, RVCWebSocketClient
} from './websocket';

export type {
  WebSocketConfig, WebSocketHandlers, WebSocketState
} from './websocket';

// Re-export types that are commonly used
export type {
  AllCANStats, APIError, CANMessage, CANMessageUpdate, CANSendParams, ControlCommand,
  ControlEntityResponse, EntitiesQueryParams, Entity,
  EntityCollection, EntityUpdateMessage, FeatureStatus, HealthStatus, HistoryEntry, HistoryQueryParams, LightEntity,
  LockEntity, MetadataResponse, SystemStatusMessage, TankEntity, TemperatureEntity, UnknownPGNEntry, UnmappedEntry, WebSocketMessage
} from './types';
