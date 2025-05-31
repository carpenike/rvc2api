/**
 * Hooks Index
 *
 * Central export point for all custom React hooks.
 * Provides clean imports for components and other modules.
 */

// Entity management hooks
export {
  useControlEntity, useEntities,
  useEntity, useEntityHistory, useEntityMetadata, useLight, useLightControl, useLights, useLock, useLockControl, useLocks, useTankSensor, useTankSensors, useTemperatureSensor, useTemperatureSensors
} from './useEntities';

// System and CAN bus hooks
export {
  useCANInterfaces,
  useCANStatistics, useDataRefresh, useFeatureStatus, useGlobalLoadingState, useHealthStatus, useQueueStatus, useRefreshCANData,
  useRefreshSystemData, useSendCANMessage, useUnknownPGNs,
  useUnmappedEntries
} from './useSystem';

// WebSocket hooks
export {
  useCANScanWebSocket, useEntityWebSocket, useSystemStatusWebSocket,
  useWebSocketManager
} from './useWebSocket';
