/**
 * API Types for RVC2API Frontend
 *
 * TypeScript interfaces that match the backend API models.
 * These types ensure type safety when working with API responses.
 */

// Base Entity Interface
export interface EntityBase {
  id: string;
  name: string;
  device_type: string;
  suggested_area: string;
  state: string;
  raw: Record<string, unknown>;
  capabilities: string[];
  last_updated: string;
  source_type: string;
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

// Union type for all entity types
export type Entity = LightEntity | LockEntity | TemperatureEntity | TankEntity | EntityBase;

// Entity collections (API responses return dictionaries keyed by entity ID)
export type EntityCollection = Record<string, Entity>;

// Control Command Structure (matches backend ControlCommand model)
export interface ControlCommand {
  command: string;
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
  command: ControlCommand;
  timestamp: string;
  execution_time_ms?: number;
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
}

// CAN Message Structure
export interface CANMessage {
  timestamp: string;
  arbitration_id: string;
  data: string;
  interface: string;
  pgn: string;
  source_addr: string;
  priority: string;
  dgn_hex: string;
  name: string;
  decoded: Record<string, unknown>;
  direction: "rx" | "tx";
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
  first_seen_timestamp: number;
  last_seen_timestamp: number;
  count: number;
  example_data: string;
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

// Health Status Response
export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  version: string;
  uptime: number;
  features: Record<string, boolean>;
}

// Feature Status
export interface FeatureStatus {
  name: string;
  enabled: boolean;
  core: boolean;
  depends_on: string[];
  description: string;
}

// Queue Status Response
export interface QueueStatus {
  length: number;
  capacity: number;
  pending_messages: number;
  last_processed: string | null;
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
export interface EntitiesQueryParams {
  device_type?: string;
  area?: string;
}

export interface HistoryQueryParams {
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
