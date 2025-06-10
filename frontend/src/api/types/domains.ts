/**
 * Domain API Types
 *
 * TypeScript types generated from backend Pydantic schemas with Zod export capability.
 * These types are synchronized with the backend domain models and provide compile-time
 * type safety for the frontend.
 */

//
// ===== ENTITIES DOMAIN TYPES =====
//

/** Supported entity control commands */
export type EntityCommand = 'set' | 'toggle' | 'brightness_up' | 'brightness_down';

/** Entity state values */
export type EntityState = 'on' | 'off' | 'unknown';

/** Operation result status */
export type OperationStatus = 'success' | 'failed' | 'timeout' | 'unauthorized';

/** Server-side entity schema with validation */
export interface EntitySchema {
  /** Unique entity identifier */
  entity_id: string;
  /** Human-readable entity name */
  name: string;
  /** Device type (light, lock, etc.) */
  device_type: string;
  /** Communication protocol (rvc, j1939, etc.) */
  protocol: string;
  /** Current entity state */
  state: Record<string, string | number | boolean>;
  /** Area or zone the entity belongs to */
  area?: string | null;
  /** Last update timestamp */
  last_updated: string;
  /** Entity availability status */
  available: boolean;
}

/** Entity control command schema */
export interface ControlCommandSchema {
  /** Control command to execute */
  command: EntityCommand;
  /** Target state for set commands */
  state?: boolean | null;
  /** Brightness level (0-100) */
  brightness?: number | null;
  /** Additional command parameters */
  parameters?: Record<string, string | number | boolean> | null;
}

/** Bulk entity control request schema */
export interface BulkControlRequestSchema {
  /** List of entity IDs to control */
  entity_ids: string[];
  /** Command to apply to all entities */
  command: ControlCommandSchema;
  /** Continue operation if some entities fail */
  ignore_errors?: boolean;
  /** Operation timeout in seconds */
  timeout_seconds?: number | null;
}

/** Individual operation result schema */
export interface OperationResultSchema {
  /** Entity ID that was operated on */
  entity_id: string;
  /** Operation result status */
  status: OperationStatus;
  /** Error message if operation failed */
  error_message?: string | null;
  /** Error code for programmatic handling */
  error_code?: string | null;
  /** Operation execution time in milliseconds */
  execution_time_ms?: number | null;
}

/** Bulk operation result schema */
export interface BulkOperationResultSchema {
  /** Unique operation identifier */
  operation_id: string;
  /** Total number of entities in the operation */
  total_count: number;
  /** Number of successful operations */
  success_count: number;
  /** Number of failed operations */
  failed_count: number;
  /** Individual operation results */
  results: OperationResultSchema[];
  /** Total operation execution time */
  total_execution_time_ms: number;
}

/** Entity collection with pagination and filtering */
export interface EntityCollectionSchema {
  /** List of entities */
  entities: EntitySchema[];
  /** Total number of entities available */
  total_count: number;
  /** Current page number */
  page: number;
  /** Number of entities per page */
  page_size: number;
  /** Whether there are more pages */
  has_next: boolean;
  /** Applied filters */
  filters_applied: Record<string, string | number | boolean | string[]>;
}

//
// ===== QUERY PARAMETERS =====
//

/** Query parameters for entities endpoints */
export interface EntitiesQueryParams extends Record<string, unknown> {
  /** Filter by device type */
  device_type?: string;
  /** Filter by area */
  area?: string;
  /** Filter by protocol */
  protocol?: string;
  /** Page number */
  page?: number;
  /** Items per page */
  page_size?: number;
  /** Search query */
  search?: string;
}

//
// ===== API RESPONSE HELPERS =====
//

/** Standard API response wrapper */
export interface DomainAPIResponse<T> {
  /** Response data */
  data: T;
  /** Success status */
  success: boolean;
  /** Optional message */
  message?: string;
  /** Response timestamp */
  timestamp: string;
}

/** API error response */
export interface DomainAPIError {
  /** Error detail message */
  detail: string;
  /** HTTP status code */
  status_code: number;
  /** Error timestamp */
  timestamp: string;
  /** Optional error code */
  error_code?: string;
  /** Optional validation errors */
  validation_errors?: Record<string, string[]>;
}

//
// ===== LEGACY COMPATIBILITY TYPES =====
//

/** Legacy entity format for backward compatibility */
export interface LegacyEntity {
  entity_id: string;
  name?: string;
  friendly_name: string | null;
  device_type: string;
  suggested_area: string;
  state: string;
  raw: Record<string, unknown>;
  capabilities: string[];
  timestamp: number;
  value: Record<string, unknown>;
  groups: string[];
  // Legacy fields
  id?: string;
  last_updated?: string;
  source_type?: string;
  entity_type?: string;
  current_state?: string;
}

/** Legacy entity collection format */
export type LegacyEntityCollection = Record<string, LegacyEntity>;

//
// ===== TYPE GUARDS =====
//

/** Type guard to check if an object is an EntitySchema */
export function isEntitySchema(obj: unknown): obj is EntitySchema {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'entity_id' in obj &&
    'name' in obj &&
    'device_type' in obj &&
    'protocol' in obj &&
    'state' in obj &&
    'last_updated' in obj &&
    'available' in obj &&
    typeof (obj as EntitySchema).entity_id === 'string' &&
    typeof (obj as EntitySchema).name === 'string' &&
    typeof (obj as EntitySchema).device_type === 'string' &&
    typeof (obj as EntitySchema).protocol === 'string' &&
    typeof (obj as EntitySchema).state === 'object' &&
    typeof (obj as EntitySchema).last_updated === 'string' &&
    typeof (obj as EntitySchema).available === 'boolean'
  );
}

/** Type guard to check if an object is a BulkOperationResultSchema */
export function isBulkOperationResult(obj: unknown): obj is BulkOperationResultSchema {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'operation_id' in obj &&
    'total_count' in obj &&
    'success_count' in obj &&
    'failed_count' in obj &&
    'results' in obj &&
    'total_execution_time_ms' in obj &&
    typeof (obj as BulkOperationResultSchema).operation_id === 'string' &&
    typeof (obj as BulkOperationResultSchema).total_count === 'number' &&
    typeof (obj as BulkOperationResultSchema).success_count === 'number' &&
    typeof (obj as BulkOperationResultSchema).failed_count === 'number' &&
    Array.isArray((obj as BulkOperationResultSchema).results) &&
    typeof (obj as BulkOperationResultSchema).total_execution_time_ms === 'number'
  );
}

/** Type guard to check if an object is an EntityCollectionSchema */
export function isEntityCollection(obj: unknown): obj is EntityCollectionSchema {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    'entities' in obj &&
    'total_count' in obj &&
    'page' in obj &&
    'page_size' in obj &&
    'has_next' in obj &&
    'filters_applied' in obj &&
    Array.isArray((obj as EntityCollectionSchema).entities) &&
    typeof (obj as EntityCollectionSchema).total_count === 'number' &&
    typeof (obj as EntityCollectionSchema).page === 'number' &&
    typeof (obj as EntityCollectionSchema).page_size === 'number' &&
    typeof (obj as EntityCollectionSchema).has_next === 'boolean' &&
    typeof (obj as EntityCollectionSchema).filters_applied === 'object'
  );
}

//
// ===== UTILITY TYPES =====
//

/** Extract entity IDs from various entity containers */
export type EntityId<T> = T extends EntitySchema
  ? T['entity_id']
  : T extends LegacyEntity
  ? T['entity_id']
  : never;

/** Extract entity state from various entity containers */
export type EntityStateType<T> = T extends EntitySchema
  ? T['state']
  : T extends LegacyEntity
  ? T['raw']
  : never;

/** Utility type for entity filtering */
export type EntityFilter<T extends EntitySchema = EntitySchema> = {
  [K in keyof T]?: T[K] extends string
    ? string | string[]
    : T[K] extends number
    ? number | [number, number]
    : T[K] extends boolean
    ? boolean
    : unknown;
};

/** Utility type for bulk operation targeting */
export interface BulkOperationTarget {
  /** Entity IDs to target */
  entity_ids: string[];
  /** Optional filter to validate entities */
  filter?: EntityFilter;
  /** Maximum entities per operation */
  max_batch_size?: number;
}

//
// ===== VALIDATION SCHEMAS =====
//

/** Runtime validation helper for ControlCommandSchema */
export function validateControlCommand(command: unknown): command is ControlCommandSchema {
  if (!command || typeof command !== 'object') {
    return false;
  }

  const cmd = command as Record<string, unknown>;
  const validCommands: EntityCommand[] = ['set', 'toggle', 'brightness_up', 'brightness_down'];

  if (!('command' in cmd) || !validCommands.includes(cmd.command as EntityCommand)) {
    return false;
  }

  if ('brightness' in cmd && cmd.brightness !== undefined && cmd.brightness !== null) {
    if (typeof cmd.brightness !== 'number' || cmd.brightness < 0 || cmd.brightness > 100) {
      return false;
    }
  }

  if ('state' in cmd && cmd.state !== undefined && cmd.state !== null) {
    if (typeof cmd.state !== 'boolean') {
      return false;
    }
  }

  return true;
}

/** Runtime validation helper for BulkControlRequestSchema */
export function validateBulkControlRequest(request: unknown): request is BulkControlRequestSchema {
  if (!request || typeof request !== 'object') {
    return false;
  }

  const req = request as Record<string, unknown>;

  if (!('entity_ids' in req) || !Array.isArray(req.entity_ids) || req.entity_ids.length === 0) {
    return false;
  }

  if (!req.entity_ids.every((id: unknown) => typeof id === 'string')) {
    return false;
  }

  if (!('command' in req) || !validateControlCommand(req.command)) {
    return false;
  }

  if ('ignore_errors' in req && req.ignore_errors !== undefined && typeof req.ignore_errors !== 'boolean') {
    return false;
  }

  if ('timeout_seconds' in req && req.timeout_seconds !== undefined && req.timeout_seconds !== null) {
    if (typeof req.timeout_seconds !== 'number' || req.timeout_seconds <= 0) {
      return false;
    }
  }

  return true;
}

//
// ===== ANALYTICS DASHBOARD TYPES =====
//

/** Analytics metrics data structure */
export interface AnalyticsMetricData {
  /** Current value of the metric */
  current_value: number;
  /** Historical data points */
  data_points: { timestamp: string; value: number }[];
  /** Trend direction */
  trend_direction: 'up' | 'down' | 'stable';
  /** Percentage change */
  change_percent: number;
  /** Number of anomalies detected */
  anomaly_count: number;
  /** Data quality indicator */
  data_quality: 'good' | 'fair' | 'poor';
}

/** Performance trends summary */
export interface PerformanceTrendsSummary {
  /** Number of metrics trending upward */
  trending_up: number;
  /** Number of metrics trending downward */
  trending_down: number;
  /** Number of stable metrics */
  stable: number;
  /** Total number of anomalies */
  total_anomalies: number;
  /** Key insights from analysis */
  key_insights: string[];
}

/** Performance alert */
export interface PerformanceAlert {
  /** Alert type */
  type: string;
  /** Alert severity */
  severity: 'low' | 'medium' | 'high' | 'critical';
  /** Alert message */
  message: string;
  /** Recommendation for addressing the alert */
  recommendation?: string;
}

/** Performance trends response */
export interface PerformanceTrendsResponse {
  /** Summary statistics */
  summary: PerformanceTrendsSummary;
  /** Detailed metrics data */
  metrics: Record<string, AnalyticsMetricData>;
  /** Performance alerts */
  alerts: PerformanceAlert[];
  /** Time window for the analysis */
  time_window_hours: number;
  /** Data resolution */
  resolution: string;
}

/** System insight */
export interface SystemInsight {
  /** Unique insight identifier */
  insight_id: string;
  /** Insight title */
  title: string;
  /** Detailed description */
  description: string;
  /** Insight category */
  category: string;
  /** Severity level */
  severity: 'low' | 'medium' | 'high' | 'critical';
  /** Confidence score (0-1) */
  confidence: number;
  /** Impact score (0-1) */
  impact_score: number;
  /** List of recommendations */
  recommendations: string[];
  /** Creation timestamp */
  created_at: number;
}

/** System insights summary */
export interface SystemInsightsSummary {
  /** Total number of insights */
  total_count: number;
  /** Average confidence score */
  avg_confidence: number;
  /** Average impact score */
  avg_impact: number;
}

/** System insights response */
export interface SystemInsightsResponse {
  /** List of insights */
  insights: SystemInsight[];
  /** Summary statistics */
  summary: SystemInsightsSummary;
  /** Distribution by severity */
  severity_distribution: Record<string, number>;
}

/** Historical pattern */
export interface HistoricalPattern {
  /** Pattern identifier */
  pattern_id: string;
  /** Pattern description */
  description: string;
  /** Pattern type */
  pattern_type: string;
  /** Confidence level (0-1) */
  confidence: number;
  /** Pattern frequency */
  frequency?: string;
  /** Correlation factors */
  correlation_factors: string[];
}

/** Historical analysis summary */
export interface HistoricalAnalysisSummary {
  /** Number of patterns found */
  patterns_found: number;
  /** Number of anomalies detected */
  anomalies_detected: number;
  /** Number of correlations found */
  correlations_found: number;
  /** Number of predictions generated */
  predictions_generated: number;
}

/** Historical analysis response */
export interface HistoricalAnalysisResponse {
  /** Detected patterns */
  patterns: HistoricalPattern[];
  /** Detected anomalies */
  anomalies: unknown[]; // To be expanded when anomaly structure is defined
  /** Found correlations */
  correlations: unknown[]; // To be expanded when correlation structure is defined
  /** Generated predictions */
  predictions: unknown[]; // To be expanded when prediction structure is defined
  /** Analysis summary */
  summary: HistoricalAnalysisSummary;
}

/** Metrics aggregation response */
export interface MetricsAggregationResponse {
  /** Aggregation time windows */
  windows: Record<string, unknown>; // To be expanded when window structure is defined
  /** Key performance indicators */
  kpis: Record<string, number | string>;
  /** Optimization recommendations */
  recommendations: unknown[]; // To be expanded when recommendation structure is defined
}

/** Analytics service status */
export interface AnalyticsServiceStatus {
  /** Service operational status */
  service_status: 'operational' | 'degraded' | 'down';
  /** Number of metrics being tracked */
  metrics_tracked: number;
  /** Number of cached insights */
  insights_cached: number;
  /** Number of patterns detected */
  patterns_detected: number;
}
