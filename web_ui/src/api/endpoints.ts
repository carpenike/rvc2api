/**
 * API Endpoints for RVC2API Frontend
 *
 * This module provides typed API endpoint functions that match the backend API structure.
 * All functions return Promises with properly typed responses.
 */

import {
  apiGet,
  apiPost,
  buildQueryString,
  logApiRequest,
  logApiResponse
} from './client';

import type {
  AllCANStats,
  CANSendParams,
  ControlCommand,
  ControlEntityResponse,
  EntitiesQueryParams,
  Entity,
  EntityCollection,
  FeatureStatus,
  HealthStatus,
  HistoryEntry,
  HistoryQueryParams,
  MetadataResponse,
  QueueStatus,
  UnknownPGNResponse,
  UnmappedResponse
} from './types';

//
// ===== ENTITIES API (/api/entities) =====
//

/**
 * Fetch all entities with optional filtering
 *
 * @param params - Optional query parameters for filtering
 * @returns Promise resolving to entity collection
 */
export async function fetchEntities(params?: EntitiesQueryParams): Promise<EntityCollection> {
  const queryString = params ? buildQueryString(params) : '';
  const url = queryString ? `/api/entities?${queryString}` : '/api/entities';

  logApiRequest('GET', url, params);
  const result = await apiGet<EntityCollection>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch a specific entity by ID
 *
 * @param entityId - The entity ID to fetch
 * @returns Promise resolving to the entity data
 */
export async function fetchEntity(entityId: string): Promise<Entity> {
  const url = `/api/entities/${entityId}`;

  logApiRequest('GET', url);
  const result = await apiGet<Entity>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Control an entity (turn on/off, set brightness, etc.)
 *
 * @param entityId - The entity ID to control
 * @param command - The control command to execute
 * @returns Promise resolving to the control response
 */
export async function controlEntity(
  entityId: string,
  command: ControlCommand
): Promise<ControlEntityResponse> {
  const url = `/api/entities/${entityId}/control`;

  logApiRequest('POST', url, command);
  const result = await apiPost<ControlEntityResponse>(url, command);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch entity history
 *
 * @param entityId - The entity ID to get history for
 * @param params - Optional query parameters (limit, since)
 * @returns Promise resolving to history entries
 */
export async function fetchEntityHistory(
  entityId: string,
  params?: HistoryQueryParams
): Promise<HistoryEntry[]> {
  const queryString = params ? buildQueryString(params) : '';
  const url = queryString
    ? `/api/entities/${entityId}/history?${queryString}`
    : `/api/entities/${entityId}/history`;

  logApiRequest('GET', url, params);
  const result = await apiGet<HistoryEntry[]>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch unmapped CAN entries
 *
 * @returns Promise resolving to unmapped entries
 */
export async function fetchUnmappedEntries(): Promise<UnmappedResponse> {
  const url = '/api/entities/unmapped';

  logApiRequest('GET', url);
  const result = await apiGet<UnmappedResponse>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch unknown PGN entries
 *
 * @returns Promise resolving to unknown PGN entries
 */
export async function fetchUnknownPGNs(): Promise<UnknownPGNResponse> {
  const url = '/api/entities/unknown-pgns';

  logApiRequest('GET', url);
  const result = await apiGet<UnknownPGNResponse>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get entity metadata (device types, areas, etc.)
 *
 * @returns Promise resolving to metadata response
 */
export async function fetchEntityMetadata(): Promise<MetadataResponse> {
  const url = '/api/entities/metadata';

  logApiRequest('GET', url);
  const result = await apiGet<MetadataResponse>(url);
  logApiResponse(url, result);

  return result;
}

//
// ===== CAN BUS API (/api/can) =====
//

/**
 * Get available CAN interfaces
 *
 * @returns Promise resolving to list of interface names
 */
export async function fetchCANInterfaces(): Promise<string[]> {
  const url = '/api/can/interfaces';

  logApiRequest('GET', url);
  const result = await apiGet<string[]>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get CAN bus statistics for all interfaces
 *
 * @returns Promise resolving to CAN statistics
 */
export async function fetchCANStatistics(): Promise<AllCANStats> {
  const url = '/api/can/statistics';

  logApiRequest('GET', url);
  const result = await apiGet<AllCANStats>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Send a CAN message
 *
 * @param params - CAN message parameters
 * @returns Promise resolving to send confirmation
 */
export async function sendCANMessage(params: CANSendParams): Promise<{ success: boolean; message: string }> {
  const url = '/api/can/send';

  logApiRequest('POST', url, params);
  const result = await apiPost<{ success: boolean; message: string }>(url, params);
  logApiResponse(url, result);

  return result;
}

//
// ===== CONFIGURATION API (/api/config) =====
//

/**
 * Get application health status
 *
 * @returns Promise resolving to health status
 */
export async function fetchHealthStatus(): Promise<HealthStatus> {
  const url = '/api/config/health';

  logApiRequest('GET', url);
  const result = await apiGet<HealthStatus>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get feature status and configuration
 *
 * @returns Promise resolving to feature status list
 */
export async function fetchFeatureStatus(): Promise<FeatureStatus[]> {
  const url = '/api/config/features';

  logApiRequest('GET', url);
  const result = await apiGet<FeatureStatus[]>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get message queue status
 *
 * @returns Promise resolving to queue status
 */
export async function fetchQueueStatus(): Promise<QueueStatus> {
  const url = '/api/config/queue-status';

  logApiRequest('GET', url);
  const result = await apiGet<QueueStatus>(url);
  logApiResponse(url, result);

  return result;
}

//
// ===== CONVENIENCE FUNCTIONS =====
//

/**
 * Fetch only light entities
 * Convenience function that filters entities by device_type=light
 *
 * @returns Promise resolving to light entities only
 */
export async function fetchLights(): Promise<EntityCollection> {
  return fetchEntities({ device_type: 'light' });
}

/**
 * Fetch only lock entities
 * Convenience function that filters entities by device_type=lock
 *
 * @returns Promise resolving to lock entities only
 */
export async function fetchLocks(): Promise<EntityCollection> {
  return fetchEntities({ device_type: 'lock' });
}

/**
 * Fetch only temperature sensor entities
 * Convenience function that filters entities by device_type=temperature_sensor
 *
 * @returns Promise resolving to temperature sensor entities only
 */
export async function fetchTemperatureSensors(): Promise<EntityCollection> {
  return fetchEntities({ device_type: 'temperature_sensor' });
}

/**
 * Fetch only tank sensor entities
 * Convenience function that filters entities by device_type=tank_sensor
 *
 * @returns Promise resolving to tank sensor entities only
 */
export async function fetchTankSensors(): Promise<EntityCollection> {
  return fetchEntities({ device_type: 'tank_sensor' });
}

//
// ===== LIGHT CONTROL CONVENIENCE FUNCTIONS =====
//

/**
 * Turn a light on
 *
 * @param entityId - The light entity ID
 * @returns Promise resolving to control response
 */
export async function turnLightOn(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'set', parameters: { state: true } });
}

/**
 * Turn a light off
 *
 * @param entityId - The light entity ID
 * @returns Promise resolving to control response
 */
export async function turnLightOff(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'set', parameters: { state: false } });
}

/**
 * Toggle a light on/off
 *
 * @param entityId - The light entity ID
 * @returns Promise resolving to control response
 */
export async function toggleLight(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'toggle', parameters: {} });
}

/**
 * Set light brightness
 *
 * @param entityId - The light entity ID
 * @param brightness - Brightness level (0-100)
 * @returns Promise resolving to control response
 */
export async function setLightBrightness(
  entityId: string,
  brightness: number
): Promise<ControlEntityResponse> {
  return controlEntity(entityId, {
    command: 'set',
    parameters: { brightness: Math.max(0, Math.min(100, brightness)) }
  });
}

//
// ===== LOCK CONTROL CONVENIENCE FUNCTIONS =====
//

/**
 * Lock a lock entity
 *
 * @param entityId - The lock entity ID
 * @returns Promise resolving to control response
 */
export async function lockEntity(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'lock', parameters: {} });
}

/**
 * Unlock a lock entity
 *
 * @param entityId - The lock entity ID
 * @returns Promise resolving to control response
 */
export async function unlockEntity(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'unlock', parameters: {} });
}
