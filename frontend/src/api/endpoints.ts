/**
 * API Endpoints for CoachIQ Frontend
 *
 * This module provides typed API endpoint functions that match the backend API structure.
 * All functions return Promises with properly typed responses.
 */

import {
    APIClientError,
    API_BASE,
    apiGet,
    apiPost,
    buildQueryString,
    logApiRequest,
    logApiResponse
} from './client';

import type {
    AllCANStats,
    CANMessage,
    CANMetrics,
    CANSendParams,
    ControlCommand,
    ControlEntityResponse,
    CreateEntityMappingRequest,
    CreateEntityMappingResponse,
    EntitiesQueryParams,
    Entity,
    EntityCollection,
    FeatureStatusResponse,
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
  const url = '/api/unmapped';

  logApiRequest('GET', url);
  const result = await apiGet<UnmappedResponse>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Create entity mapping from unmapped entry
 *
 * @param request - Entity mapping configuration details
 * @returns Promise resolving to mapping creation response
 */
export async function createEntityMapping(
  request: CreateEntityMappingRequest
): Promise<CreateEntityMappingResponse> {
  const url = '/api/entities/mappings';

  logApiRequest('POST', url, request);
  const result = await apiPost<CreateEntityMappingResponse>(url, request);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch unknown PGN entries
 *
 * @returns Promise resolving to unknown PGN entries
 */
export async function fetchUnknownPGNs(): Promise<UnknownPGNResponse> {
  const url = '/api/unknown-pgns';

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
  const url = '/api/metadata';

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

/**
 * Fetch recent CAN messages
 *
 * @param params - Optional query parameters (limit)
 * @returns Promise resolving to CAN messages
 */
export async function fetchCANMessages(params?: { limit?: number }): Promise<CANMessage[]> {
  const queryString = params ? buildQueryString(params) : '';
  const url = queryString ? `/api/can/recent?${queryString}` : '/api/can/recent';

  logApiRequest('GET', url, params);
  const result = await apiGet<CANMessage[]>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get CAN bus metrics and health information
 *
 * Note: Using statistics endpoint as metrics source
 * @returns Promise resolving to CAN metrics derived from statistics
 */
export async function fetchCANMetrics(): Promise<CANMetrics> {
  const url = '/api/can/statistics';

  logApiRequest('GET', url);
  const statsResult = await apiGet<Record<string, unknown>>(url);
  logApiResponse(url, statsResult);

  // Transform statistics to metrics format
  const summary = statsResult.summary as Record<string, unknown> || {};
  const metrics: CANMetrics = {
    messageRate: (summary.message_rate as number) || 0,
    totalMessages: (summary.total_messages as number) || 0,
    errorCount: (summary.total_errors as number) || 0,
    uptime: (summary.uptime as number) || 0
  };

  return metrics;
}

//
// ===== CONFIGURATION API (/api/config) =====
//

/**
 * Get application health status
 *
 * Special handling for health endpoint: accepts both 200 (healthy) and 503 (degraded) as valid responses
 *
 * @returns Promise resolving to health status
 */
export async function fetchHealthStatus(): Promise<HealthStatus> {
  const url = '/healthz';

  logApiRequest('GET', url);

  try {
    const result = await apiGet<HealthStatus>(url);
    logApiResponse(url, result);
    return result;
  } catch (error) {
    // For health endpoint, 503 responses contain valid degraded status data
    if (error instanceof APIClientError && error.statusCode === 503) {
      try {
        // Re-fetch to get the 503 response data directly
        const fullUrl = url.startsWith('/api') ? url : `${API_BASE}${url}`;
        const response = await fetch(fullUrl, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

        if (response.status === 503) {
          const degradedData = await response.json() as HealthStatus;
          logApiResponse(url, degradedData);
          return degradedData;
        }
      } catch (fetchError) {
        console.warn('Failed to parse 503 health response:', fetchError);
      }
    }

    // Re-throw other errors
    throw error;
  }
}

/**
 * Get feature status and configuration
 *
 * @returns Promise resolving to feature status response
 */
export async function fetchFeatureStatus(): Promise<FeatureStatusResponse> {
  const url = '/api/status/features';

  logApiRequest('GET', url);
  const result = await apiGet<FeatureStatusResponse>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get message queue status
 *
 * @returns Promise resolving to queue status
 */
export async function fetchQueueStatus(): Promise<QueueStatus> {
  const url = '/api/can/queue/status';

  logApiRequest('GET', url);
  const result = await apiGet<QueueStatus>(url);
  logApiResponse(url, result);

  return result;
}

//
// ===== DASHBOARD AGGREGATION API (/api/dashboard) =====
//

/**
 * Get complete dashboard summary data
 *
 * Optimized endpoint that returns all dashboard data in a single request
 * @returns Promise resolving to complete dashboard summary
 */
export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const url = '/api/dashboard/summary';

  logApiRequest('GET', url);
  const result = await apiGet<DashboardSummary>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get entity summary statistics
 *
 * @returns Promise resolving to aggregated entity statistics
 */
export async function fetchEntitySummary(): Promise<EntitySummary> {
  const url = '/api/dashboard/entities';

  logApiRequest('GET', url);
  const result = await apiGet<EntitySummary>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get system performance metrics
 *
 * @returns Promise resolving to system metrics
 */
export async function fetchSystemMetrics(): Promise<SystemMetrics> {
  const url = '/api/dashboard/system';

  logApiRequest('GET', url);
  const result = await apiGet<SystemMetrics>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get CAN bus summary
 *
 * @returns Promise resolving to CAN bus summary
 */
export async function fetchCANBusSummary(): Promise<CANBusSummary> {
  const url = '/api/dashboard/can-bus';

  logApiRequest('GET', url);
  const result = await apiGet<CANBusSummary>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Get activity feed
 *
 * @param params - Optional query parameters (limit, since)
 * @returns Promise resolving to activity feed
 */
export async function fetchActivityFeed(params?: { limit?: number; since?: string }): Promise<ActivityFeed> {
  const queryString = params ? buildQueryString(params) : '';
  const url = queryString ? `/api/dashboard/activity?${queryString}` : '/api/dashboard/activity';

  logApiRequest('GET', url, params);
  const result = await apiGet<ActivityFeed>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Perform bulk control operations on multiple entities
 *
 * @param request - Bulk control request with entity IDs and command
 * @returns Promise resolving to bulk control response
 */
export async function bulkControlEntities(request: BulkControlRequest): Promise<BulkControlResponse> {
  const url = '/api/dashboard/bulk-control';

  logApiRequest('POST', url, request);
  const result = await apiPost<BulkControlResponse>(url, request);
  logApiResponse(url, result);

  return result;
}

/**
 * Get system analytics and monitoring data
 *
 * @returns Promise resolving to system analytics
 */
export async function fetchSystemAnalytics(): Promise<SystemAnalytics> {
  const url = '/api/dashboard/analytics';

  logApiRequest('GET', url);
  const result = await apiGet<SystemAnalytics>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Acknowledge a system alert
 *
 * @param alertId - ID of the alert to acknowledge
 * @returns Promise resolving to acknowledgment response
 */
export async function acknowledgeAlert(alertId: string): Promise<{ success: boolean; message: string }> {
  const url = `/api/dashboard/alerts/${alertId}/acknowledge`;

  logApiRequest('POST', url);
  const result = await apiPost<{ success: boolean; message: string }>(url, {});
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

/**
 * Increase light brightness by 10%
 *
 * @param entityId - The light entity ID
 * @returns Promise resolving to control response
 */
export async function brightnessUp(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'brightness_up', parameters: {} });
}

/**
 * Decrease light brightness by 10%
 *
 * @param entityId - The light entity ID
 * @returns Promise resolving to control response
 */
export async function brightnessDown(entityId: string): Promise<ControlEntityResponse> {
  return controlEntity(entityId, { command: 'brightness_down', parameters: {} });
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
