/**
 * Entities Domain API Client
 *
 * This module provides typed API client functions for the entities domain,
 * leveraging the new /api/v2/entities endpoints with enhanced bulk operations
 * and optimistic update support.
 */

import { apiGet, apiPost, buildQueryString, logApiRequest, logApiResponse } from '../client';

//
// ===== TYPES FROM BACKEND SCHEMAS =====
//

export interface EntitySchema {
  entity_id: string;
  name: string;
  device_type: string;
  protocol: string;
  state: Record<string, string | number | boolean>;
  area?: string | null;
  last_updated: string;
  available: boolean;
}

export interface ControlCommandSchema {
  command: 'set' | 'toggle' | 'brightness_up' | 'brightness_down';
  state?: boolean | null;
  brightness?: number | null;
  parameters?: Record<string, string | number | boolean> | null;
}

export interface BulkControlRequestSchema {
  entity_ids: string[];
  command: ControlCommandSchema;
  ignore_errors?: boolean;
  timeout_seconds?: number | null;
}

export interface OperationResultSchema {
  entity_id: string;
  status: 'success' | 'failed' | 'timeout' | 'unauthorized';
  error_message?: string | null;
  error_code?: string | null;
  execution_time_ms?: number | null;
}

export interface BulkOperationResultSchema {
  operation_id: string;
  total_count: number;
  success_count: number;
  failed_count: number;
  results: OperationResultSchema[];
  total_execution_time_ms: number;
}

export interface EntityCollectionSchema {
  entities: EntitySchema[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  filters_applied: Record<string, string | number | boolean | string[]>;
}

//
// ===== QUERY PARAMETERS =====
//

export interface EntitiesQueryParams {
  device_type?: string;
  area?: string;
  protocol?: string;
  page?: number;
  page_size?: number;
}

//
// ===== API CLIENT FUNCTIONS =====
//

/**
 * Fetch entities using the new domain API with filtering and pagination
 *
 * @param params - Optional query parameters for filtering and pagination
 * @returns Promise resolving to paginated entity collection
 */
export async function fetchEntitiesV2(params?: EntitiesQueryParams): Promise<EntityCollectionSchema> {
  const queryString = params ? buildQueryString(params as Record<string, unknown>) : '';
  const url = queryString ? `/api/v2/entities?${queryString}` : '/api/v2/entities';

  logApiRequest('GET', url, params);
  const result = await apiGet<EntityCollectionSchema>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Fetch a specific entity by ID using the new domain API
 *
 * @param entityId - The entity ID to fetch
 * @returns Promise resolving to the entity data
 */
export async function fetchEntityV2(entityId: string): Promise<EntitySchema> {
  const url = `/api/v2/entities/${entityId}`;

  logApiRequest('GET', url);
  const result = await apiGet<EntitySchema>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Control a single entity using the new domain API
 *
 * @param entityId - The entity ID to control
 * @param command - The control command to execute
 * @returns Promise resolving to the operation result
 */
export async function controlEntityV2(
  entityId: string,
  command: ControlCommandSchema
): Promise<OperationResultSchema> {
  const url = `/api/v2/entities/${entityId}/control`;

  logApiRequest('POST', url, command);
  const result = await apiPost<OperationResultSchema>(url, command);
  logApiResponse(url, result);

  return result;
}

/**
 * Execute bulk control operations on multiple entities
 *
 * This is the primary enhancement of the domain API, supporting:
 * - Concurrent entity control with proper timeout handling
 * - Detailed per-entity operation results
 * - Multi-status HTTP responses (200, 207, 400)
 * - Optimistic update patterns
 *
 * @param request - Bulk control request with entity IDs and command
 * @returns Promise resolving to bulk operation results
 */
export async function bulkControlEntitiesV2(
  request: BulkControlRequestSchema
): Promise<BulkOperationResultSchema> {
  const url = '/api/v2/entities/bulk-control';

  logApiRequest('POST', url, request);
  const result = await apiPost<BulkOperationResultSchema>(url, request);
  logApiResponse(url, result);

  return result;
}

/**
 * Get Zod-compatible schemas for frontend validation
 *
 * @returns Promise resolving to schema definitions
 */
export async function fetchSchemasV2(): Promise<Record<string, unknown>> {
  const url = '/api/v2/entities/schemas';

  logApiRequest('GET', url);
  const result = await apiGet<Record<string, unknown>>(url);
  logApiResponse(url, result);

  return result;
}

/**
 * Health check for entities domain API
 *
 * @returns Promise resolving to health status
 */
export async function fetchEntitiesHealthV2(): Promise<Record<string, unknown>> {
  const url = '/api/v2/entities/health';

  logApiRequest('GET', url);
  const result = await apiGet<Record<string, unknown>>(url);
  logApiResponse(url, result);

  return result;
}

//
// ===== CONVENIENCE FUNCTIONS =====
//

/**
 * Turn multiple lights on using bulk operations
 *
 * @param entityIds - Array of light entity IDs
 * @param ignoreErrors - Whether to continue if some operations fail
 * @returns Promise resolving to bulk operation results
 */
export async function bulkTurnLightsOn(
  entityIds: string[],
  ignoreErrors = true
): Promise<BulkOperationResultSchema> {
  return bulkControlEntitiesV2({
    entity_ids: entityIds,
    command: {
      command: 'set',
      state: true,
    },
    ignore_errors: ignoreErrors,
  });
}

/**
 * Turn multiple lights off using bulk operations
 *
 * @param entityIds - Array of light entity IDs
 * @param ignoreErrors - Whether to continue if some operations fail
 * @returns Promise resolving to bulk operation results
 */
export async function bulkTurnLightsOff(
  entityIds: string[],
  ignoreErrors = true
): Promise<BulkOperationResultSchema> {
  return bulkControlEntitiesV2({
    entity_ids: entityIds,
    command: {
      command: 'set',
      state: false,
    },
    ignore_errors: ignoreErrors,
  });
}

/**
 * Set brightness for multiple lights using bulk operations
 *
 * @param entityIds - Array of light entity IDs
 * @param brightness - Brightness level (0-100)
 * @param ignoreErrors - Whether to continue if some operations fail
 * @returns Promise resolving to bulk operation results
 */
export async function bulkSetLightBrightness(
  entityIds: string[],
  brightness: number,
  ignoreErrors = true
): Promise<BulkOperationResultSchema> {
  return bulkControlEntitiesV2({
    entity_ids: entityIds,
    command: {
      command: 'set',
      brightness: Math.max(0, Math.min(100, brightness)),
    },
    ignore_errors: ignoreErrors,
  });
}

/**
 * Toggle multiple entities using bulk operations
 *
 * @param entityIds - Array of entity IDs
 * @param ignoreErrors - Whether to continue if some operations fail
 * @returns Promise resolving to bulk operation results
 */
export async function bulkToggleEntities(
  entityIds: string[],
  ignoreErrors = true
): Promise<BulkOperationResultSchema> {
  return bulkControlEntitiesV2({
    entity_ids: entityIds,
    command: {
      command: 'toggle',
    },
    ignore_errors: ignoreErrors,
  });
}

//
// ===== LEGACY COMPATIBILITY =====
//

/**
 * Convert new EntitySchema to legacy Entity format for backward compatibility
 *
 * @param entity - New EntitySchema from domain API
 * @returns Legacy Entity format
 */
export function convertEntitySchemaToLegacy(entity: EntitySchema): Record<string, unknown> {
  return {
    entity_id: entity.entity_id,
    name: entity.name,
    friendly_name: entity.name,
    device_type: entity.device_type,
    suggested_area: entity.area || '',
    state: entity.state?.state || 'unknown',
    raw: entity.state || {},
    capabilities: [], // Could be extracted from state if needed
    timestamp: new Date(entity.last_updated).getTime(),
    value: entity.state || {},
    groups: [],
    // Legacy fields
    id: entity.entity_id,
    last_updated: entity.last_updated,
    current_state: entity.state?.state || 'unknown',
  };
}

/**
 * Convert legacy EntityCollection to new EntityCollectionSchema format
 *
 * @param legacyCollection - Legacy entity collection (Record<string, Entity>)
 * @returns New EntityCollectionSchema format
 */
export function convertLegacyEntityCollection(legacyCollection: Record<string, unknown>): EntityCollectionSchema {
  const entities: EntitySchema[] = Object.entries(legacyCollection).map(([id, entity]) => {
    // Type guard for entity object
    const entityObj = entity && typeof entity === 'object' ? entity as Record<string, unknown> : {};

    // Safe state extraction with type assertion
    const extractState = (): Record<string, string | number | boolean> => {
      const rawState = entityObj.raw || entityObj.value;
      if (rawState && typeof rawState === 'object' && rawState !== null) {
        return rawState as Record<string, string | number | boolean>;
      }
      return {};
    };

    return {
      entity_id: id,
      name: (typeof entityObj.friendly_name === 'string' ? entityObj.friendly_name :
             typeof entityObj.name === 'string' ? entityObj.name : id),
      device_type: typeof entityObj.device_type === 'string' ? entityObj.device_type : 'unknown',
      protocol: typeof entityObj.protocol === 'string' ? entityObj.protocol : 'rvc',
      state: extractState(),
      area: typeof entityObj.suggested_area === 'string' ? entityObj.suggested_area : null,
      last_updated: typeof entityObj.last_updated === 'string' ? entityObj.last_updated : new Date().toISOString(),
      available: entityObj.available !== false,
    };
  });

  return {
    entities,
    total_count: entities.length,
    page: 1,
    page_size: entities.length,
    has_next: false,
    filters_applied: {},
  };
}
