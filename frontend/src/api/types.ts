/**
 * API Types for CoachIQ Frontend
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

// Health Status Response (matches backend /healthz)
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
  onDiagnosticUpdate?: (data: DiagnosticUpdateMessage['data']) => void;
  onPerformanceUpdate?: (data: PerformanceUpdateMessage['data']) => void;
  onMultiProtocolUpdate?: (data: MultiProtocolUpdateMessage['data']) => void;
  onMessage?: (message: ExtendedWebSocketMessageType) => void;
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

// Dashboard aggregation types
export interface EntitySummary {
  total_entities: number;
  online_entities: number;
  active_entities: number;
  device_type_counts: Record<string, number>;
  area_counts: Record<string, number>;
  health_score: number;
}

export interface SystemMetrics {
  uptime_seconds: number;
  message_rate: number;
  error_rate: number;
  memory_usage_mb: number;
  cpu_usage_percent: number;
  websocket_connections: number;
}

export interface CANBusSummary {
  interfaces_count: number;
  total_messages: number;
  messages_per_minute: number;
  error_count: number;
  queue_length: number;
  bus_load_percent: number;
}

export interface ActivityEntry {
  id: string;
  timestamp: string;
  event_type: string;
  entity_id?: string;
  title: string;
  description: string;
  severity: string;
  metadata: Record<string, unknown>;
}

export interface ActivityFeed {
  entries: ActivityEntry[];
  total_count: number;
  has_more: boolean;
}

export interface DashboardSummary {
  timestamp: string;
  entities: EntitySummary;
  system: SystemMetrics;
  can_bus: CANBusSummary;
  activity: ActivityFeed;
  alerts: string[];
  quick_stats: Record<string, unknown>;
}

export interface BulkControlRequest {
  entity_ids: string[];
  command: string;
  parameters: Record<string, unknown>;
  ignore_errors: boolean;
}

export interface BulkControlResult {
  entity_id: string;
  success: boolean;
  message: string;
  error?: string;
}

export interface BulkControlResponse {
  total_requested: number;
  successful: number;
  failed: number;
  results: BulkControlResult[];
  summary: string;
}

export interface AlertDefinition {
  id: string;
  name: string;
  description: string;
  condition: string;
  severity: string;
  enabled: boolean;
  threshold?: number;
}

export interface ActiveAlert {
  alert_id: string;
  triggered_at: string;
  current_value: number;
  threshold: number;
  message: string;
  severity: string;
  acknowledged: boolean;
}

export interface SystemAnalytics {
  alerts: ActiveAlert[];
  performance_trends: Record<string, number[]>;
  health_checks: Record<string, boolean>;
  recommendations: string[];
}

//
// ===== ADVANCED DIAGNOSTICS TYPES =====
//

// System Health Response (matches backend SystemHealthResponse)
export interface SystemHealthResponse {
  overall_health: number; // 0.0-1.0
  system_scores: Record<string, number>;
  status: "healthy" | "warning" | "critical";
  recommendations: string[];
  last_assessment: number;
  active_dtcs: number;
}

// DTC Filters for API queries
export interface DTCFilters {
  system_type?: string;
  severity?: string;
  protocol?: string;
}

// Diagnostic Trouble Code (matches backend DTC models)
export interface DiagnosticTroubleCode {
  id: string;
  code: string;
  protocol: "rvc" | "j1939" | "firefly" | "spartan_k2";
  system_type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  first_seen: string;
  last_seen: string;
  count: number;
  resolved: boolean;
  source_address: number;
  pgn?: number;
  dgn?: number;
  metadata: Record<string, unknown>;
}

// DTC Collection Response
export interface DTCCollection {
  dtcs: DiagnosticTroubleCode[];
  total_count: number;
  active_count: number;
  by_severity: Record<string, number>;
  by_protocol: Record<string, number>;
}

// DTC Resolution Response
export interface DTCResolutionResponse {
  resolved: boolean;
  dtc_id: string;
  message: string;
  timestamp: string;
}

// Fault Correlation
export interface FaultCorrelation {
  primary_dtc: string;
  related_dtcs: string[];
  confidence: number; // 0.0-1.0
  temporal_relationship: "simultaneous" | "sequential" | "intermittent";
  suggested_cause: string;
  correlation_id: string;
  detected_at: string;
  pattern_type: string;
}

// Maintenance Prediction
export interface MaintenancePrediction {
  component_name: string;
  system_type: string;
  failure_probability: number; // 0.0-1.0
  predicted_failure_date: string;
  confidence: number; // 0.0-1.0
  recommended_action: string;
  urgency: "low" | "medium" | "high" | "critical";
  estimated_cost: number;
  historical_patterns: string[];
}

// Maintenance Alert
export interface MaintenanceAlert {
  alert_id: string;
  component_name: string;
  prediction_id: string;
  urgency: "low" | "medium" | "high" | "critical";
  message: string;
  recommended_action: string;
  deadline: string;
  estimated_cost: number;
  acknowledged: boolean;
}

// Diagnostic Statistics
export interface DiagnosticStats {
  total_dtcs: number;
  active_dtcs: number;
  resolved_dtcs: number;
  processing_rate: number;
  correlation_accuracy: number;
  prediction_accuracy: number;
  system_health_trend: "improving" | "stable" | "degrading";
  last_updated: string;
}

//
// ===== PERFORMANCE ANALYTICS TYPES =====
//

// Performance Metrics
export interface PerformanceMetrics {
  protocol_performance: Record<string, ProtocolPerformance>;
  api_performance: APIPerformance;
  websocket_performance: WebSocketPerformance;
  overall_health: number; // 0.0-1.0
  last_updated: string;
}

// Protocol Performance
export interface ProtocolPerformance {
  message_rate: number;
  decode_rate: number;
  error_rate: number;
  latency_ms: number;
  throughput_mbps: number;
  efficiency: number; // 0.0-1.0
}

// API Performance
export interface APIPerformance {
  average_response_time: number;
  requests_per_second: number;
  error_rate: number;
  success_rate: number; // 0.0-1.0
  slow_queries: number;
}

// WebSocket Performance
export interface WebSocketPerformance {
  message_rate: number;
  latency_ms: number;
  connection_stability: number; // 0.0-1.0
  active_connections: number;
  dropped_messages: number;
}

// Resource Usage
export interface ResourceUsage {
  cpu_usage: number; // 0.0-1.0
  memory_usage: number; // 0.0-1.0
  disk_usage: number; // 0.0-1.0
  network_usage: number; // bytes/sec
  can_interface_usage: Record<string, number>; // 0.0-1.0 per interface
  queue_lengths: Record<string, number>;
}

// Trend Data
export interface TrendData {
  metric_name: string;
  time_series: TimeSeriesPoint[];
  trend_direction: "up" | "down" | "stable";
  trend_strength: number; // 0.0-1.0
  prediction_confidence: number; // 0.0-1.0
}

// Time Series Point
export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  baseline_deviation: number;
}

// Optimization Suggestion
export interface OptimizationSuggestion {
  suggestion_id: string;
  category: "performance" | "reliability" | "efficiency" | "cost";
  title: string;
  description: string;
  impact_score: number; // 0.0-1.0
  implementation_effort: "low" | "medium" | "high";
  estimated_improvement: string;
  implementation_steps: string[];
  priority: "low" | "medium" | "high" | "critical";
}

// Baseline Deviation
export interface BaselineDeviation {
  metric_name: string;
  current_value: number;
  baseline_value: number;
  deviation_percent: number;
  severity: "low" | "medium" | "high" | "critical";
  threshold_breached: boolean;
  detected_at: string;
  trend: "improving" | "stable" | "degrading";
}

// Performance Analytics Statistics
export interface PerformanceAnalyticsStats {
  feature: Record<string, unknown>;
  telemetry: Record<string, unknown>;
  benchmarking: Record<string, unknown>;
  trends: Record<string, unknown>;
  optimization: Record<string, unknown>;
}

// Performance Report
export interface PerformanceReport {
  report_id: string;
  generated_at: string;
  time_window_seconds: number;
  summary: {
    overall_performance: number; // 0.0-1.0
    key_insights: string[];
    critical_issues: number;
    improvement_opportunities: number;
  };
  metrics: PerformanceMetrics;
  trends: TrendData[];
  baseline_deviations: BaselineDeviation[];
  optimization_recommendations: OptimizationSuggestion[];
  resource_utilization: ResourceUsage;
  protocol_throughput: Record<string, number>;
}

//
// ===== MULTI-PROTOCOL ENTITY TYPES =====
//

// J1939 Entity
export interface J1939Entity extends EntityBase {
  protocol: "j1939";
  system_type: "engine" | "transmission" | "chassis";
  manufacturer?: "cummins" | "allison" | "generic";
  engine_data?: {
    rpm?: number;
    coolant_temp?: number;
    oil_pressure?: number;
    fuel_rate?: number;
  };
}

// Firefly Entity
export interface FireflyEntity extends EntityBase {
  protocol: "firefly";
  multiplexed: boolean;
  safety_interlocks?: string[];
  zone_controls?: {
    scene_id?: string;
    fade_time?: number;
    zone_priority?: number;
  };
}

// Spartan K2 Entity
export interface SpartanK2Entity extends EntityBase {
  protocol: "spartan_k2";
  system_type: "brake" | "suspension" | "steering" | "electrical";
  safety_status: "safe" | "warning" | "critical";
  chassis_data?: {
    brake_pressure?: number;
    suspension_level?: number;
    steering_angle?: number;
  };
}

// Protocol Bridge Status
export interface ProtocolBridgeStatus {
  bridges_active: number;
  total_bridges: number;
  translation_rate: number;
  error_rate: number;
  health_score: number; // 0.0-1.0
  bridge_statuses: Record<string, BridgeStatus>;
}

// Individual Bridge Status
export interface BridgeStatus {
  from_protocol: string;
  to_protocol: string;
  active: boolean;
  translation_count: number;
  error_count: number;
  last_activity: string;
}

//
// ===== ENHANCED WEBSOCKET TYPES =====
//

// Diagnostic Update Message
export interface DiagnosticUpdateMessage extends WebSocketMessage {
  type: "diagnostic_update";
  data: {
    dtc_id?: string;
    health_score_change?: number;
    new_correlation?: FaultCorrelation;
    maintenance_alert?: MaintenanceAlert;
    system_health?: SystemHealthResponse;
  };
}

// Performance Update Message
export interface PerformanceUpdateMessage extends WebSocketMessage {
  type: "performance_update";
  data: {
    metric_name: string;
    current_value: number;
    baseline_deviation: number;
    trend: "improving" | "stable" | "degrading";
    resource_usage?: ResourceUsage;
  };
}

// Multi-Protocol Update Message
export interface MultiProtocolUpdateMessage extends WebSocketMessage {
  type: "multi_protocol_update";
  data: {
    protocol: string;
    entity_updates: EntityCollection;
    bridge_status?: ProtocolBridgeStatus;
    performance_metrics?: ProtocolPerformance;
  };
}

// Extended WebSocket Message Types
export type ExtendedWebSocketMessageType =
  | EntityUpdateMessage
  | CANMessageUpdate
  | SystemStatusMessage
  | DiagnosticUpdateMessage
  | PerformanceUpdateMessage
  | MultiProtocolUpdateMessage
  | WebSocketMessage;

//
// ===== CONFIGURATION MANAGEMENT TYPES =====
//

// System Settings Overview
export interface SystemSettings {
  server: ServerSettings;
  can: CANSettings;
  cors: CORSSettings;
  security: SecuritySettings;
  logging: LoggingSettings;
  rvc: RVCSettings;
  j1939: J1939Settings;
  firefly: FireflySettings;
  spartan_k2: SpartanK2Settings;
  multi_network: MultiNetworkSettings;
  persistence: PersistenceSettings;
  advanced_diagnostics: AdvancedDiagnosticsSettings;
  performance_analytics: PerformanceAnalyticsSettings;
  environment_variables: Record<string, string>;
  config_sources: Record<string, string>;
}

// Server Configuration
export interface ServerSettings {
  host: string;
  port: number;
  ssl_enabled: boolean;
  ssl_cert_path?: string;
  ssl_key_path?: string;
  workers: number;
  max_connections: number;
  keepalive_timeout: number;
  debug_mode: boolean;
}

// CAN Bus Configuration
export interface CANSettings {
  interfaces: Record<string, string>; // logical_name -> physical_interface
  default_bitrate: number;
  buffer_size: number;
  receive_timeout: number;
  error_handling: "strict" | "lenient" | "ignore";
  interface_validation: boolean;
}

// CORS Configuration
export interface CORSSettings {
  allow_origins: string[];
  allow_methods: string[];
  allow_headers: string[];
  allow_credentials: boolean;
  max_age: number;
}

// Security Configuration
export interface SecuritySettings {
  api_key_required: boolean;
  api_keys: string[];
  rate_limiting_enabled: boolean;
  rate_limit_requests_per_minute: number;
  allowed_ips: string[];
  require_https: boolean;
}

// Logging Configuration
export interface LoggingSettings {
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  format: string;
  file_enabled: boolean;
  file_path?: string;
  file_rotation: boolean;
  file_max_size_mb: number;
  file_backup_count: number;
  console_enabled: boolean;
  structured_logging: boolean;
}

// RV-C Protocol Configuration
export interface RVCSettings {
  spec_file_path: string;
  coach_mapping_file: string;
  coach_model_detection: boolean;
  custom_dgn_ranges: number[][];
  performance_tuning: {
    decode_timeout_ms: number;
    cache_size: number;
    parallel_processing: boolean;
  };
}

// J1939 Protocol Configuration
export interface J1939Settings {
  enabled: boolean;
  manufacturer_extensions: {
    cummins_enabled: boolean;
    allison_enabled: boolean;
  };
  chassis_support: {
    spartan_k2_enabled: boolean;
  };
  address_range: {
    min: number;
    max: number;
  };
  priority_pgns: number[];
}

// Firefly Configuration
export interface FireflySettings {
  enabled: boolean;
  zone_controls_enabled: boolean;
  scene_management: boolean;
  safety_interlocks: boolean;
  multiplexing_support: boolean;
  fade_time_default_ms: number;
}

// Spartan K2 Configuration
export interface SpartanK2Settings {
  enabled: boolean;
  safety_validation: boolean;
  brake_system_monitoring: boolean;
  suspension_control: boolean;
  steering_monitoring: boolean;
  safety_thresholds: {
    brake_pressure_min: number;
    brake_pressure_max: number;
    steering_angle_max: number;
  };
}

// Multi-Network Configuration
export interface MultiNetworkSettings {
  enabled: boolean;
  bridge_protocols: string[];
  isolation_enabled: boolean;
  fault_containment: boolean;
  health_monitoring_interval_ms: number;
  bridge_timeout_ms: number;
}

// Persistence Configuration
export interface PersistenceSettings {
  enabled: boolean;
  backend_type: "memory" | "sqlite" | "postgresql";
  backup_enabled: boolean;
  backup_interval_hours: number;
  retention_days: number;
  compression_enabled: boolean;
}

// Advanced Diagnostics Configuration
export interface AdvancedDiagnosticsSettings {
  enabled: boolean;
  health_score_calculation: boolean;
  fault_correlation: boolean;
  predictive_maintenance: boolean;
  correlation_confidence_threshold: number;
  health_update_interval_ms: number;
  maintenance_prediction_horizon_days: number;
}

// Performance Analytics Configuration
export interface PerformanceAnalyticsSettings {
  enabled: boolean;
  metrics_collection: boolean;
  baseline_calculation: boolean;
  optimization_recommendations: boolean;
  telemetry_interval_ms: number;
  baseline_window_hours: number;
  deviation_threshold_percent: number;
}

// Feature Flag with Dependencies
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description: string;
  dependencies: string[];
  dependent_features: string[];
  category: "core" | "protocol" | "advanced" | "experimental";
  stability: "stable" | "beta" | "alpha";
  environment_restrictions?: string[];
}

// Feature Management Response
export interface FeatureManagementResponse {
  features: Record<string, FeatureFlag>;
  dependency_graph: Record<string, string[]>;
  conflict_resolution: Record<string, string>;
  validation_errors: string[];
}

// CAN Interface Mapping
export interface CANInterfaceMapping {
  logical_name: string;
  physical_interface: string;
  bitrate: number;
  is_active: boolean;
  last_activity?: string;
  message_count: number;
  error_count: number;
  validation_status: "valid" | "invalid" | "warning";
  validation_message?: string;
}

// Coach Configuration Metadata
export interface CoachConfiguration {
  model: string;
  year: number;
  manufacturer: string;
  config_file: string;
  interface_requirements: string[];
  device_mappings: Record<string, unknown>;
  validation_status: "valid" | "invalid" | "warning";
  last_validated: string;
}

// Configuration Validation Result
export interface ConfigurationValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  affected_features: string[];
}

// Configuration Update Request
export interface ConfigurationUpdateRequest {
  section: string;
  key: string;
  value: unknown;
  persist: boolean;
  validate_before_apply: boolean;
}

// Configuration Update Response
export interface ConfigurationUpdateResponse {
  success: boolean;
  message: string;
  previous_value?: unknown;
  validation_result?: ConfigurationValidation;
  restart_required: boolean;
  affected_services: string[];
}

// System Status for Configuration
export interface ConfigurationSystemStatus {
  server_status: "running" | "starting" | "stopping" | "error";
  can_interfaces_status: Record<string, "active" | "inactive" | "error">;
  feature_status: Record<string, "enabled" | "disabled" | "error">;
  protocol_status: Record<string, "active" | "inactive" | "error">;
  validation_status: "valid" | "invalid" | "warning";
  last_config_change: string;
  pending_restarts: string[];
}

// Performance Analytics Types (missing from previous implementations)
export interface BaselineDeviation {
  metric_name: string;
  current_value: number;
  baseline_value: number;
  deviation_percent: number;
  trend: "improving" | "stable" | "degrading";
  severity: "low" | "medium" | "high" | "critical";
  timestamp: string;
}


export interface PerformanceAnalyticsStats {
  total_metrics_collected: number;
  active_monitoring_interval_ms: number;
  baseline_calculation_status: "active" | "inactive" | "error";
  last_optimization_run: string;
  metrics_retention_days: number;
  telemetry_endpoints_active: number;
}
