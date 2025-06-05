/**
 * API Types for RVC2API Frontend
 *
 * TypeScript interfaces that match the backend API models.
 * These types ensure type safety when working with API responses.
 */

// Base Entity Interface
export interface EntityBase {
  entity_id: string;
  name?: string;  // Made optional since backend may not always include this
  friendly_name: string | null;
  device_type: string;
  suggested_area: string;
  state: string;
  raw: Record<string, unknown>;
  capabilities: string[];
  timestamp: number;  // Backend returns timestamp, not last_updated
  value: Record<string, unknown>;  // Backend includes value field
  groups: string[];  // Backend includes groups field
  // Legacy fields for backward compatibility
  id?: string;
  last_updated?: string;
  source_type?: string;
  entity_type?: string;
  current_state?: string;
}

// Light-specific interface extending base entity
export interface LightEntity extends EntityBase {
  device_type: "light";
  brightness?: number;
}

// Lock-specific interface extending base entity
export interface LockEntity extends EntityBase {
  device_type: "lock";
}

// Temperature sensor interface extending base entity
export interface TemperatureEntity extends EntityBase {
  device_type: "temperature";
  temperature?: number;
  units?: string;
}

// Tank sensor interface extending base entity
export interface TankEntity extends EntityBase {
  device_type: "tank";
  level?: number;
  capacity?: number;
  tank_type?: string;
}

// Aliases for backward compatibility
export type TankSensorEntity = TankEntity;
export type TemperatureSensorEntity = TemperatureEntity;
export type EntityData = Entity;

// Union type for all entity types
export type Entity = LightEntity | LockEntity | TemperatureEntity | TankEntity | EntityBase;

// Entity collections (API responses return dictionaries keyed by entity ID)
export type EntityCollection = Record<string, Entity>;

// Control Command Structure (matches backend ControlCommand model)
export interface ControlCommand {
  command: string;
  command_type?: string;
  parameters?: Record<string, unknown>;
  state?: string | null;
  brightness?: number;
  level?: number;
  temperature?: number;
}

// Control Response Structure (matches backend ControlEntityResponse model)
export interface ControlEntityResponse {
  success: boolean;
  message: string;
  entity_id: string;
  entity_type?: string;
  command: ControlCommand;
  timestamp: string;
  execution_time_ms?: number;
}

// Entity Mapping Creation Request (matches backend CreateEntityMappingRequest model)
export interface CreateEntityMappingRequest {
  // Source unmapped entry information
  pgn_hex: string;
  instance: string;

  // Entity configuration
  entity_id: string;
  friendly_name: string;
  device_type: string;
  suggested_area?: string;
  capabilities?: string[];
  notes?: string;
}

// Entity Mapping Creation Response (matches backend CreateEntityMappingResponse model)
export interface CreateEntityMappingResponse {
  status: "success" | "error";
  entity_id: string;
  message: string;
  entity_data: Record<string, unknown> | null;
}

// Entity History Entry
export interface HistoryEntry {
  timestamp: string;
  state: string;
  raw: Record<string, unknown>;
  source: string;
}

// CAN Interface Stats (matches backend CANInterfaceStats model)
export interface CANInterfaceStats {
  name: string;
  state: string | null;
  restart_ms: number | null;
  bitrate: number | null;
  sample_point: number | null;
  tx_count: number | null;
  rx_count: number | null;
  error_count: number | null;
  parentdev: string | null;
  error_warning: number | null;
  error_passive: number | null;
  bus_off: number | null;
  raw_details: string | null;
}

// All CAN Stats (matches backend AllCANStats model)
export interface AllCANStats {
  interfaces: Record<string, CANInterfaceStats>;
  total_messages?: number;
  total_errors?: number;
}

// CAN Message Structure
export interface CANMessage {
  timestamp: string;
  pgn: string;
  instance?: number;
  source: number;
  data: number[];
  error?: boolean;
}

// CAN Metrics (for bus health monitoring)
export interface CANMetrics {
  messageRate: number;
  totalMessages: number;
  errorCount: number;
  uptime: number;
}

// Unmapped Entry Model (matches backend UnmappedEntryModel)
export interface UnmappedEntry {
  pgn_hex: string;
  pgn_name: string;
  dgn_hex: string;
  dgn_name: string;
  instance: string;
  last_data_hex: string;
  decoded_signals: Record<string, unknown>;
  first_seen_timestamp: number;
  last_seen_timestamp: number;
  count: number;
  suggestions: string[];
  spec_entry: Record<string, unknown>;
}

// Unknown PGN Entry (matches backend UnknownPGNEntry)
export interface UnknownPGNEntry {
  pgn_hex: string;
  pgn_name: string;
  arbitration_id_hex?: string;
  first_seen_timestamp: number;
  last_seen_timestamp: number;
  count: number;
  example_data: string;
  last_data_hex?: string;
  source_addresses: string[];
}

// API Response Collections
export interface UnmappedResponse {
  unmapped_entries: Record<string, UnmappedEntry>;
}

export interface UnknownPGNResponse {
  unknown_pgns: Record<string, UnknownPGNEntry>;
}

// Metadata Response Structure
export interface MetadataResponse {
  device_types: string[];
  areas: string[];
  capabilities: string[];
  states: string[];
}

// Health Status Response (matches backend /api/healthz)
export interface HealthStatus {
  status: "healthy" | "degraded" | "failed";
  features: Record<string, string>;
  unhealthy_features?: Record<string, string>;
  all_features?: Record<string, string>;
}

// Feature Status from /api/status/features
export interface FeatureInfo {
  enabled: boolean;
  core: boolean;
  health: string;
  type: string;
}

export interface FeatureStatusResponse {
  total_features: number;
  enabled_count: number;
  core_count: number;
  optional_count: number;
  features: Record<string, FeatureInfo>;
}

// Legacy FeatureStatus (for backward compatibility)
export interface FeatureStatus {
  name: string;
  enabled: boolean;
  core: boolean;
  depends_on: string[];
  description: string;
}

// Queue Status Response (matches backend CAN service response)
export interface QueueStatus {
  length: number;
  maxsize: number | "unbounded";
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

export interface EntityUpdateMessage extends WebSocketMessage {
  type: "entity_update";
  data: {
    entity_id: string;
    entity_data: Entity;
  };
}

export interface CANMessageUpdate extends WebSocketMessage {
  type: "can_message";
  data: CANMessage;
}

export interface SystemStatusMessage extends WebSocketMessage {
  type: "system_status";
  data: {
    connected_clients: number;
    can_interfaces: string[];
    last_message_time: string;
  };
}

// Union type for all WebSocket message types
export type WebSocketMessageType = EntityUpdateMessage | CANMessageUpdate | SystemStatusMessage | WebSocketMessage;

// WebSocket Handlers Interface
export interface WebSocketHandlers {
  onEntityUpdate?: (data: EntityUpdateMessage['data']) => void;
  onCANMessage?: (data: CANMessage) => void;
  onSystemStatus?: (data: SystemStatusMessage['data']) => void;
  onMessage?: (message: WebSocketMessageType) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
}

// API Error Response
export interface APIError {
  detail: string;
  status_code: number;
  timestamp: string;
}

// Generic API Response Wrapper
export interface APIResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

// Query Parameters for API endpoints
export interface EntitiesQueryParams extends Record<string, unknown> {
  device_type?: string;
  area?: string;
}

export interface HistoryQueryParams extends Record<string, unknown> {
  limit?: number;
  since?: number;
}

export interface CANSendParams {
  arbitration_id: number;
  data: string;
  interface: string;
}

// Light Control Helpers (common commands)
export interface LightControlCommands {
  turnOn: () => ControlCommand;
  turnOff: () => ControlCommand;
  toggle: () => ControlCommand;
  setBrightness: (brightness: number) => ControlCommand;
  brightnessUp: () => ControlCommand;
  brightnessDown: () => ControlCommand;
}
